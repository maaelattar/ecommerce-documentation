# Order Service

## 1. Overview

The `OrderService` is the primary business logic component within the Order Service. It encapsulates all core functionality related to order management, including order creation, retrieval, updates, cancellations, and status transitions. This service acts as an orchestrator, coordinating between the repository layer, domain objects, validation services, and integration with other microservices.

## 2. Responsibilities

- Implementing all business logic for order operations
- Enforcing order state transitions and business rules
- Managing order data persistence through the repository layer
- Coordinating with other services (payment, inventory, notification)
- Validating order data integrity and consistency
- Handling order workflows from creation to completion
- Supporting both individual and bulk operations

## 3. Class Definition

```typescript
@Injectable()
export class OrderService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly orderItemRepository: OrderItemRepository,
    private readonly orderStatusRepository: OrderStatusRepository,
    private readonly userService: UserService,
    private readonly inventoryService: InventoryClient,
    private readonly paymentService: PaymentServiceClient,
    private readonly eventPublisher: EventPublisher,
    private readonly logger: Logger
  ) {}

  // Service methods defined below
}
```

## 4. Core Methods

### 4.1. Create Order

```typescript
/**
 * Creates a new order with the provided details
 */
async createOrder(
  createOrderDto: CreateOrderDto,
  userId: string
): Promise<Order> {
  this.logger.log(`Creating new order for user ${userId}`);

  // Validate order data
  await this.validateOrderData(createOrderDto);

  // Check inventory availability
  await this.checkInventoryAvailability(createOrderDto.items);

  // Get initial order status
  const initialStatus = await this.orderStatusRepository.findByName('PENDING_PAYMENT');
  if (!initialStatus) {
    throw new InternalServerErrorException('Initial order status not found');
  }

  try {
    // Start a database transaction
    return await this.orderRepository.manager.transaction(async (manager) => {
      // Create order entity
      const order = new Order();
      order.userId = userId;
      order.orderNumber = this.generateOrderNumber();
      order.status = initialStatus;
      order.statusId = initialStatus.id;
      order.totalAmount = this.calculateOrderTotal(createOrderDto);
      order.subtotal = this.calculateSubtotal(createOrderDto.items);
      order.tax = createOrderDto.tax || 0;
      order.shippingCost = createOrderDto.shippingCost || 0;
      order.discountAmount = createOrderDto.discountAmount || 0;
      order.currency = createOrderDto.currency || 'USD';
      order.promoCode = createOrderDto.promoCode;
      order.notes = createOrderDto.notes;
      order.metadata = createOrderDto.metadata;

      // Save order to get ID
      const savedOrder = await manager.getRepository(Order).save(order);

      // Create and save shipping details
      if (createOrderDto.shippingDetails) {
        const shippingDetails = new OrderShippingDetails();
        shippingDetails.order = savedOrder;
        shippingDetails.orderId = savedOrder.id;
        // Map shipping details from DTO to entity
        Object.assign(shippingDetails, createOrderDto.shippingDetails);

        await manager.getRepository(OrderShippingDetails).save(shippingDetails);
        savedOrder.shippingDetails = shippingDetails;
      }

      // Create and save billing details
      if (createOrderDto.billingDetails) {
        const billingDetails = new OrderBillingDetails();
        billingDetails.order = savedOrder;
        billingDetails.orderId = savedOrder.id;
        // Map billing details from DTO to entity
        Object.assign(billingDetails, createOrderDto.billingDetails);

        await manager.getRepository(OrderBillingDetails).save(billingDetails);
        savedOrder.billingDetails = billingDetails;
      }

      // Create and save order items
      const orderItems: OrderItem[] = [];
      for (const itemDto of createOrderDto.items) {
        const orderItem = new OrderItem();
        orderItem.order = savedOrder;
        orderItem.orderId = savedOrder.id;
        orderItem.productId = itemDto.productId;
        orderItem.variantId = itemDto.variantId;
        orderItem.productName = itemDto.productName;
        orderItem.quantity = itemDto.quantity;
        orderItem.unitPrice = itemDto.unitPrice;
        orderItem.totalPrice = itemDto.unitPrice * itemDto.quantity;
        orderItem.metadata = itemDto.metadata;

        const savedItem = await manager.getRepository(OrderItem).save(orderItem);
        orderItems.push(savedItem);
      }
      savedOrder.items = orderItems;

      // Create order status history entry
      const statusHistory = new OrderStatusHistory();
      statusHistory.order = savedOrder;
      statusHistory.orderId = savedOrder.id;
      statusHistory.status = initialStatus;
      statusHistory.statusId = initialStatus.id;
      statusHistory.changedBy = userId;
      statusHistory.notes = 'Order created';

      await manager.getRepository(OrderStatusHistory).save(statusHistory);

      // Reserve inventory
      await this.inventoryService.reserveInventory(
        savedOrder.id,
        savedOrder.items.map((item) => ({
          productId: item.productId,
          variantId: item.variantId,
          quantity: item.quantity
        }))
      );

      // Return the saved order with all relations
      return savedOrder;
    });
  } catch (error) {
    this.logger.error(`Failed to create order: ${error.message}`, error.stack);

    if (error instanceof QueryFailedError) {
      throw new BadRequestException('Invalid order data');
    }

    if (error instanceof InventoryServiceException) {
      throw new ConflictException('Insufficient inventory for one or more items');
    }

    throw new InternalServerErrorException(`Order creation failed: ${error.message}`);
  }
}
```

### 4.2. Find Order By ID

```typescript
/**
 * Finds an order by its ID with all relations loaded
 */
async findOrderById(orderId: string): Promise<Order> {
  this.logger.log(`Finding order with id ${orderId}`);

  const order = await this.orderRepository.findOne({
    where: { id: orderId },
    relations: [
      'items',
      'shippingDetails',
      'billingDetails',
      'status',
      'statusHistory',
      'statusHistory.status'
    ]
  });

  if (!order) {
    throw new OrderNotFoundException(`Order with id ${orderId} not found`);
  }

  return order;
}
```

### 4.3. Find Orders

```typescript
/**
 * Finds orders with pagination and filtering options
 */
async findOrders(
  queryParams: OrderQueryParamsDto,
  userId?: string
): Promise<[Order[], number]> {
  this.logger.log(`Finding orders with params: ${JSON.stringify(queryParams)}`);

  const { page = 1, limit = 10, status, fromDate, toDate, sortBy, sortOrder } = queryParams;

  const skip = (page - 1) * limit;

  // Build query with QueryBuilder for more complex filtering
  const queryBuilder = this.orderRepository.createQueryBuilder('order')
    .leftJoinAndSelect('order.items', 'items')
    .leftJoinAndSelect('order.shippingDetails', 'shippingDetails')
    .leftJoinAndSelect('order.status', 'status');

  // Apply user filter if provided (for customer access)
  if (userId) {
    queryBuilder.andWhere('order.userId = :userId', { userId });
  }

  // Apply status filter if provided
  if (status) {
    if (Array.isArray(status)) {
      queryBuilder.andWhere('status.name IN (:...statusNames)', { statusNames: status });
    } else {
      queryBuilder.andWhere('status.name = :statusName', { statusName: status });
    }
  }

  // Apply date range filter if provided
  if (fromDate) {
    queryBuilder.andWhere('order.createdAt >= :fromDate', {
      fromDate: new Date(fromDate)
    });
  }

  if (toDate) {
    queryBuilder.andWhere('order.createdAt <= :toDate', {
      toDate: new Date(toDate)
    });
  }

  // Apply sorting
  if (sortBy) {
    const order = sortOrder?.toUpperCase() === 'DESC' ? 'DESC' : 'ASC';

    if (sortBy === 'createdAt' || sortBy === 'updatedAt' || sortBy === 'totalAmount') {
      queryBuilder.orderBy(`order.${sortBy}`, order);
    } else if (sortBy === 'status') {
      queryBuilder.orderBy('status.name', order);
    }
  } else {
    // Default sorting by created date, newest first
    queryBuilder.orderBy('order.createdAt', 'DESC');
  }

  // Apply pagination
  queryBuilder.skip(skip).take(limit);

  // Execute query and return results with total count
  const [orders, totalCount] = await queryBuilder.getManyAndCount();

  return [orders, totalCount];
}
```

### 4.4. Update Order Status

```typescript
/**
 * Updates an order's status with validation of status transitions
 */
async updateOrderStatus(
  orderId: string,
  statusUpdateDto: UpdateOrderStatusDto,
  userId: string
): Promise<Order> {
  this.logger.log(`Updating status for order ${orderId} to ${statusUpdateDto.status}`);

  // Start a database transaction
  return await this.orderRepository.manager.transaction(async (manager) => {
    // Get the order with its current status
    const order = await manager.getRepository(Order).findOne({
      where: { id: orderId },
      relations: ['status', 'items', 'shippingDetails', 'billingDetails'],
    });

    if (!order) {
      throw new OrderNotFoundException(`Order with id ${orderId} not found`);
    }

    // Get the target status
    const newStatus = await manager.getRepository(OrderStatus).findOne({
      where: { name: statusUpdateDto.status },
    });

    if (!newStatus) {
      throw new BadRequestException(`Invalid status: ${statusUpdateDto.status}`);
    }

    // Validate status transition
    await this.validateStatusTransition(order.status.name, newStatus.name);

    // Check if additional required data is present based on the new status
    await this.validateStatusUpdateData(newStatus.name, statusUpdateDto);

    const previousStatus = { ...order.status };

    // Update the order status
    order.status = newStatus;
    order.statusId = newStatus.id;

    // Update status-specific fields based on the new status
    await this.applyStatusSpecificUpdates(order, newStatus.name, statusUpdateDto);

    // Update the order
    await manager.getRepository(Order).save(order);

    // Create status history record
    const statusHistory = new OrderStatusHistory();
    statusHistory.orderId = orderId;
    statusHistory.statusId = newStatus.id;
    statusHistory.status = newStatus;
    statusHistory.changedBy = userId;
    statusHistory.notes = statusUpdateDto.notes || '';
    statusHistory.metadata = statusUpdateDto.metadata;

    await manager.getRepository(OrderStatusHistory).save(statusHistory);

    // Process additional actions based on status transition
    await this.processStatusTransitionActions(
      order,
      previousStatus.name,
      newStatus.name,
      statusUpdateDto
    );

    return order;
  });
}
```

### 4.5. Cancel Order

```typescript
/**
 * Cancels an order and handles refund if necessary
 */
async cancelOrder(
  orderId: string,
  reason: string,
  note: string,
  userId: string
): Promise<Order> {
  this.logger.log(`Cancelling order ${orderId} with reason: ${reason}`);

  // Start a database transaction
  return await this.orderRepository.manager.transaction(async (manager) => {
    // Get the order with its current status
    const order = await manager.getRepository(Order).findOne({
      where: { id: orderId },
      relations: ['status', 'items', 'shippingDetails', 'billingDetails'],
    });

    if (!order) {
      throw new OrderNotFoundException(`Order with id ${orderId} not found`);
    }

    // Check if order can be cancelled
    const cancelableStatuses = [
      'PENDING_PAYMENT',
      'PAYMENT_COMPLETED',
      'PROCESSING',
      'READY_FOR_SHIPPING'
    ];

    if (!cancelableStatuses.includes(order.status.name)) {
      throw new OrderStatusTransitionException(
        `Orders in status ${order.status.name} cannot be cancelled`
      );
    }

    // Get cancelled status
    const cancelledStatus = await manager.getRepository(OrderStatus).findOne({
      where: { name: 'CANCELLED' },
    });

    if (!cancelledStatus) {
      throw new InternalServerErrorException('Cancelled status not found');
    }

    const previousStatus = { ...order.status };

    // Update order status
    order.status = cancelledStatus;
    order.statusId = cancelledStatus.id;

    // Save the updated order
    await manager.getRepository(Order).save(order);

    // Create status history record
    const statusHistory = new OrderStatusHistory();
    statusHistory.orderId = orderId;
    statusHistory.statusId = cancelledStatus.id;
    statusHistory.status = cancelledStatus;
    statusHistory.changedBy = userId;
    statusHistory.notes = `Cancelled: ${reason}. ${note || ''}`;
    statusHistory.metadata = { cancellationReason: reason };

    await manager.getRepository(OrderStatusHistory).save(statusHistory);

    // Process refund if payment was already completed
    if (previousStatus.name === 'PAYMENT_COMPLETED' ||
        previousStatus.name === 'PROCESSING' ||
        previousStatus.name === 'READY_FOR_SHIPPING') {

      try {
        // Initiate refund through payment service
        await this.paymentService.processRefund(
          order.paymentId,
          order.id,
          order.totalAmount,
          reason,
          order.items
        );
      } catch (error) {
        this.logger.error(`Failed to process refund: ${error.message}`, error.stack);
        // Continue with cancellation but log the error
        // Refund will need to be processed manually
      }
    }

    // Release inventory
    await this.inventoryService.releaseInventory(
      order.id,
      order.items.map((item) => ({
        productId: item.productId,
        variantId: item.variantId,
        quantity: item.quantity
      }))
    );

    return order;
  });
}
```

### 4.6. Bulk Operations

```typescript
/**
 * Updates the status of multiple orders in a single batch operation
 */
async bulkStatusUpdate(
  bulkUpdateDto: BulkOrderStatusUpdateDto,
  userId: string,
  batchId: string
): Promise<BulkOrderStatusUpdateResultDto[]> {
  this.logger.log(`Processing bulk status update for ${bulkUpdateDto.orderIds.length} orders`);

  const results: BulkOrderStatusUpdateResultDto[] = [];

  // Process each order individually
  for (const orderId of bulkUpdateDto.orderIds) {
    try {
      // Get the current order to capture previous status
      const currentOrder = await this.findOrderById(orderId);
      const previousStatus = currentOrder.status.name;

      // Prepare status update DTO for this order
      const statusUpdateDto: UpdateOrderStatusDto = {
        status: bulkUpdateDto.newStatus,
        notes: bulkUpdateDto.updateReason,
        metadata: {
          ...bulkUpdateDto.statusMetadata,
          batchId,
          bulkOperation: true
        }
      };

      // Add order-specific metadata if available (like tracking info)
      if (bulkUpdateDto.newStatus === 'SHIPPED' &&
          bulkUpdateDto.statusMetadata?.trackingInfo) {

        const trackingInfo = bulkUpdateDto.statusMetadata.trackingInfo
          .find(info => info.orderId === orderId);

        if (trackingInfo) {
          statusUpdateDto.metadata = {
            ...statusUpdateDto.metadata,
            trackingNumber: trackingInfo.trackingNumber,
            estimatedDeliveryDate: trackingInfo.estimatedDeliveryDate
          };
        }
      }

      // Update the order status
      const updatedOrder = await this.updateOrderStatus(
        orderId,
        statusUpdateDto,
        userId
      );

      // If customer notifications are requested
      if (bulkUpdateDto.notifyCustomers) {
        try {
          await this.eventPublisher.publish(
            `order.${bulkUpdateDto.newStatus.toLowerCase()}`,
            {
              orderId: updatedOrder.id,
              userId: updatedOrder.userId,
              status: updatedOrder.status.name,
              // Include additional event data based on status
              ...this.buildEventDataForStatus(updatedOrder, bulkUpdateDto.newStatus)
            }
          );
        } catch (error) {
          this.logger.warn(
            `Failed to publish event for order ${orderId}: ${error.message}`
          );
          // Continue processing other orders even if notification fails
        }
      }

      // Add successful result
      results.push({
        orderId,
        success: true,
        status: updatedOrder.status.name,
        previousStatus
      });
    } catch (error) {
      this.logger.error(
        `Error updating order ${orderId}: ${error.message}`,
        error.stack
      );

      // Add failed result
      results.push({
        orderId,
        success: false,
        errorMessage: error.message,
        status: error instanceof OrderNotFoundException ? null :
               (await this.findOrderById(orderId).catch(() => null))?.status?.name,
        previousStatus: error instanceof OrderNotFoundException ? null :
                       (await this.findOrderById(orderId).catch(() => null))?.status?.name
      });
    }
  }

  return results;
}
```

## 5. Helper Methods

### 5.1. Data Validation

```typescript
/**
 * Validates order data before creating an order
 */
private async validateOrderData(createOrderDto: CreateOrderDto): Promise<void> {
  // Validate items exist
  if (!createOrderDto.items || createOrderDto.items.length === 0) {
    throw new BadRequestException('Order must contain at least one item');
  }

  // Validate item quantities
  for (const item of createOrderDto.items) {
    if (item.quantity <= 0) {
      throw new BadRequestException('Item quantity must be greater than zero');
    }
  }

  // Validate shipping details if provided
  if (createOrderDto.shippingDetails) {
    const { shippingMethod, recipientName, shippingAddressLine1, shippingCity,
            shippingState, shippingPostalCode, shippingCountry } = createOrderDto.shippingDetails;

    if (!shippingMethod) {
      throw new BadRequestException('Shipping method is required');
    }

    if (!recipientName) {
      throw new BadRequestException('Recipient name is required');
    }

    if (!shippingAddressLine1 || !shippingCity || !shippingState ||
        !shippingPostalCode || !shippingCountry) {
      throw new BadRequestException('Shipping address is incomplete');
    }
  }

  // Validate billing details if provided
  if (createOrderDto.billingDetails) {
    const { paymentMethod, billingName, billingAddressLine1, billingCity,
            billingState, billingPostalCode, billingCountry } = createOrderDto.billingDetails;

    if (!paymentMethod) {
      throw new BadRequestException('Payment method is required');
    }

    if (!billingName) {
      throw new BadRequestException('Billing name is required');
    }

    if (!billingAddressLine1 || !billingCity || !billingState ||
        !billingPostalCode || !billingCountry) {
      throw new BadRequestException('Billing address is incomplete');
    }
  }
}
```

### 5.2. Inventory Availability Check

```typescript
/**
 * Checks inventory availability for all items in the order
 */
private async checkInventoryAvailability(items: CreateOrderItemDto[]): Promise<void> {
  const inventoryCheckResult = await this.inventoryService.checkAvailability(
    items.map(item => ({
      productId: item.productId,
      variantId: item.variantId,
      quantity: item.quantity
    }))
  );

  const unavailableItems = inventoryCheckResult.filter(item => !item.available);

  if (unavailableItems.length > 0) {
    throw new ConflictException({
      message: 'Some items are not available in the requested quantity',
      unavailableItems: unavailableItems.map(item => ({
        productId: item.productId,
        variantId: item.variantId,
        requestedQuantity: item.requestedQuantity,
        availableQuantity: item.availableQuantity
      }))
    });
  }
}
```

### 5.3. Order Number Generation

```typescript
/**
 * Generates a unique order number
 */
private generateOrderNumber(): string {
  const prefix = 'ORD';
  const timestamp = Date.now().toString().slice(-8);
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
  return `${prefix}-${timestamp}${random}`;
}
```

### 5.4. Total Calculation

```typescript
/**
 * Calculates the total amount for an order
 */
private calculateOrderTotal(createOrderDto: CreateOrderDto): number {
  const subtotal = this.calculateSubtotal(createOrderDto.items);
  const tax = createOrderDto.tax || 0;
  const shippingCost = createOrderDto.shippingCost || 0;
  const discountAmount = createOrderDto.discountAmount || 0;

  return +(subtotal + tax + shippingCost - discountAmount).toFixed(2);
}

/**
 * Calculates the subtotal for order items
 */
private calculateSubtotal(items: CreateOrderItemDto[]): number {
  return +(items.reduce(
    (sum, item) => sum + (item.unitPrice * item.quantity),
    0
  )).toFixed(2);
}
```

### 5.5. Status Transition Validation

```typescript
/**
 * Validates if a status transition is allowed
 */
private async validateStatusTransition(
  currentStatus: string,
  newStatus: string
): Promise<void> {
  // Define allowed transitions for each status
  const allowedTransitions = {
    'PENDING_PAYMENT': ['PAYMENT_COMPLETED', 'CANCELLED'],
    'PAYMENT_COMPLETED': ['PROCESSING', 'CANCELLED'],
    'PROCESSING': ['READY_FOR_SHIPPING', 'CANCELLED'],
    'READY_FOR_SHIPPING': ['SHIPPED', 'CANCELLED'],
    'SHIPPED': ['DELIVERED', 'RETURNED'],
    'DELIVERED': ['RETURNED', 'COMPLETED'],
    'RETURNED': ['REFUNDED'],
    'CANCELLED': ['REFUNDED'],
    'REFUNDED': [],
    'COMPLETED': []
  };

  // Check if transition is allowed
  if (!allowedTransitions[currentStatus]?.includes(newStatus)) {
    throw new OrderStatusTransitionException(
      `Cannot transition from ${currentStatus} to ${newStatus}`
    );
  }
}
```

### 5.6. Status-Specific Updates

```typescript
/**
 * Applies status-specific updates to an order
 */
private async applyStatusSpecificUpdates(
  order: Order,
  status: string,
  updateDto: UpdateOrderStatusDto
): Promise<void> {
  switch (status) {
    case 'SHIPPED':
      // Update tracking information
      if (!order.shippingDetails) {
        throw new BadRequestException('Order does not have shipping details');
      }

      if (!updateDto.metadata?.trackingNumber) {
        throw new BadRequestException('Tracking number is required for SHIPPED status');
      }

      order.shippingDetails.trackingNumber = updateDto.metadata.trackingNumber;
      order.shippingDetails.carrier = updateDto.metadata.carrier;
      order.shippingDetails.estimatedDeliveryDate = updateDto.metadata.estimatedDeliveryDate;
      order.shippedAt = new Date();
      break;

    case 'DELIVERED':
      order.deliveredAt = new Date();
      break;

    case 'PAYMENT_COMPLETED':
      order.paymentId = updateDto.metadata?.paymentId;
      order.paidAt = new Date();
      break;

    case 'CANCELLED':
      order.cancelledAt = new Date();
      order.cancellationReason = updateDto.metadata?.cancellationReason || 'Not specified';
      break;

    case 'RETURNED':
      order.returnedAt = new Date();
      order.returnReason = updateDto.metadata?.returnReason || 'Not specified';
      break;

    case 'REFUNDED':
      order.refundedAt = new Date();
      order.refundAmount = updateDto.metadata?.refundAmount || order.totalAmount;
      break;

    case 'COMPLETED':
      order.completedAt = new Date();
      break;
  }
}
```

## 6. Error Handling

The `OrderService` implements several custom exceptions for domain-specific error handling:

```typescript
export class OrderNotFoundException extends NotFoundException {
  constructor(message: string) {
    super(message);
  }
}

export class OrderStatusTransitionException extends BadRequestException {
  constructor(message: string) {
    super(message);
  }
}

export class InventoryUnavailableException extends ConflictException {
  constructor(message: string, public readonly unavailableItems: any[]) {
    super({
      message,
      unavailableItems,
    });
  }
}

export class PaymentProcessingException extends ServiceUnavailableException {
  constructor(message: string) {
    super(message);
  }
}
```

## 7. Performance Considerations

- **Batch Processing**: For bulk operations, the service uses individual transactions per order to prevent complete batch failures
- **Pagination**: All list operations use pagination to limit result sets
- **Eager Loading**: Relations are loaded based on need to minimize database round trips
- **Query Optimization**: Complex queries use TypeORM's QueryBuilder for efficient SQL generation
- **Transaction Management**: ACID transactions are used for multi-step operations to ensure data consistency

## 8. Security Considerations

- **Data Validation**: Strict validation of all input data before processing
- **Resource Access Control**: Orders are accessible only to their owner or authorized staff
- **Status Transition Rules**: Enforcement of valid status transitions to prevent invalid states
- **Audit Logging**: All status changes are recorded with user ID and timestamp
- **Secure Payment Processing**: Payment details are handled through external payment service

## 9. References

- [Order Entity Model](../../02-data-model-setup/01-order-entity.md)
- [Order Status Definitions](../../02-data-model-setup/04-order-status-entity.md)
- [Order Controller](./01-order-controller.md)
- [Payment Service Integration](../06-integration-points/01-payment-service-integration.md)
- [Inventory Service Integration](../06-integration-points/03-inventory-service-integration.md)
- [Event Publishing](../05-event-publishing/00-events-index.md)
