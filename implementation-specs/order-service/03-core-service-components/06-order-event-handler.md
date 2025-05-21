# Order Event Handler

## 1. Overview

The `OrderEventHandler` is responsible for processing incoming events from other services that affect order state and operations. This component listens to events from the message queue, validates and processes them, and triggers appropriate business logic in the Order Service. It provides asynchronous integration with other microservices like Payment, Inventory, and Shipping services.

## 2. Responsibilities

- Consuming events from the message broker
- Validating event payloads and structure
- Processing events according to their type
- Updating order state based on event data
- Managing idempotency to prevent duplicate processing
- Handling error cases and retries
- Logging event processing for audit and debugging
- Publishing resulting events after successful processing

## 3. Class Definition

```typescript
@Injectable()
export class OrderEventHandler {
  constructor(
    private readonly orderService: OrderService,
    private readonly eventPublisher: EventPublisher,
    private readonly idempotencyService: IdempotencyService,
    private readonly logger: Logger
  ) {
    this.logger.setContext(OrderEventHandler.name);
  }

  // Event handler methods defined below
}
```

## 4. Core Event Handlers

### 4.1. Payment Completed Event Handler

```typescript
/**
 * Handles payment completed events from Payment Service
 */
@EventPattern('payment.completed')
async handlePaymentCompleted(
  @Payload() event: PaymentCompletedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, timestamp, data } = event;
  const { orderId, paymentId, amount, method, status } = data;

  this.logger.log(`Processing payment.completed event ${eventId} for order ${orderId}`);

  try {
    // Check idempotency to prevent duplicate processing
    const processed = await this.idempotencyService.checkProcessed(
      'payment.completed',
      eventId
    );

    if (processed) {
      this.logger.log(`Event ${eventId} already processed, skipping`);
      return;
    }

    // Validate event data
    if (!orderId || !paymentId || !amount || !method || status !== 'COMPLETED') {
      throw new EventValidationError('Invalid payment completed event data');
    }

    // Get current order
    const order = await this.orderService.findOrderById(orderId);

    // Validate payment amount matches order total
    if (Math.abs(order.totalAmount - amount) > 0.01) {
      this.logger.warn(
        `Payment amount (${amount}) does not match order total (${order.totalAmount})`
      );
      // Still proceed but log the discrepancy
    }

    // Update order status with payment information
    await this.orderService.updateOrderStatus(
      orderId,
      {
        status: 'PAYMENT_COMPLETED',
        notes: `Payment processed successfully via ${method}`,
        metadata: {
          paymentId,
          paymentMethod: method,
          paymentTimestamp: timestamp
        }
      },
      'system'
    );

    // Mark event as processed
    await this.idempotencyService.markProcessed(
      'payment.completed',
      eventId,
      { orderId, result: 'status_updated_to_payment_completed' }
    );

    // Publish order payment completed event
    await this.eventPublisher.publish('order.payment_completed', {
      orderId,
      userId: order.userId,
      totalAmount: order.totalAmount,
      currency: order.currency,
      paymentId
    });

    this.logger.log(`Successfully processed payment.completed event for order ${orderId}`);
  } catch (error) {
    this.logger.error(
      `Error processing payment.completed event: ${error.message}`,
      error.stack
    );

    // Handle specific errors
    if (error instanceof OrderNotFoundException) {
      // Ack the message but log the error - order doesn't exist
      await this.idempotencyService.markProcessed(
        'payment.completed',
        eventId,
        { error: 'order_not_found', orderId }
      );
      return;
    }

    // For critical errors that need retry, re-throw to trigger Nats retry mechanism
    context.getMessage().nak();
    throw error;
  }
}
```

### 4.2. Payment Failed Event Handler

```typescript
/**
 * Handles payment failed events from Payment Service
 */
@EventPattern('payment.failed')
async handlePaymentFailed(
  @Payload() event: PaymentFailedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, timestamp, data } = event;
  const { orderId, paymentId, reason, failureCode } = data;

  this.logger.log(`Processing payment.failed event ${eventId} for order ${orderId}`);

  try {
    // Check idempotency to prevent duplicate processing
    const processed = await this.idempotencyService.checkProcessed(
      'payment.failed',
      eventId
    );

    if (processed) {
      this.logger.log(`Event ${eventId} already processed, skipping`);
      return;
    }

    // Validate event data
    if (!orderId || !reason) {
      throw new EventValidationError('Invalid payment failed event data');
    }

    // Get current order
    const order = await this.orderService.findOrderById(orderId);

    // Update order status with payment failure information
    await this.orderService.updateOrderStatus(
      orderId,
      {
        status: 'PAYMENT_FAILED',
        notes: `Payment failed: ${reason}`,
        metadata: {
          paymentId,
          failureCode,
          failureReason: reason,
          failureTimestamp: timestamp
        }
      },
      'system'
    );

    // Mark event as processed
    await this.idempotencyService.markProcessed(
      'payment.failed',
      eventId,
      { orderId, result: 'status_updated_to_payment_failed' }
    );

    // Publish order payment failed event
    await this.eventPublisher.publish('order.payment_failed', {
      orderId,
      userId: order.userId,
      reason,
      failureCode
    });

    this.logger.log(`Successfully processed payment.failed event for order ${orderId}`);
  } catch (error) {
    this.logger.error(
      `Error processing payment.failed event: ${error.message}`,
      error.stack
    );

    // For non-retriable errors, log and acknowledge
    if (error instanceof OrderNotFoundException) {
      await this.idempotencyService.markProcessed(
        'payment.failed',
        eventId,
        { error: 'order_not_found', orderId }
      );
      return;
    }

    // For critical errors that need retry, re-throw
    context.getMessage().nak();
    throw error;
  }
}
```

### 4.3. Inventory Reserved Event Handler

```typescript
/**
 * Handles inventory reserved events from Inventory Service
 */
@EventPattern('inventory.reserved')
async handleInventoryReserved(
  @Payload() event: InventoryReservedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, timestamp, data } = event;
  const { orderId, items, reservationId } = data;

  this.logger.log(`Processing inventory.reserved event ${eventId} for order ${orderId}`);

  try {
    // Check idempotency
    const processed = await this.idempotencyService.checkProcessed(
      'inventory.reserved',
      eventId
    );

    if (processed) {
      this.logger.log(`Event ${eventId} already processed, skipping`);
      return;
    }

    // Validate event data
    if (!orderId || !items || !reservationId) {
      throw new EventValidationError('Invalid inventory reserved event data');
    }

    // Get current order
    const order = await this.orderService.findOrderById(orderId);

    // Update order with inventory reservation information
    await this.orderService.updateInventoryReservation(
      orderId,
      reservationId,
      items,
      timestamp
    );

    // If order is in PAYMENT_COMPLETED status, move to PROCESSING
    if (order.status.name === 'PAYMENT_COMPLETED') {
      await this.orderService.updateOrderStatus(
        orderId,
        {
          status: 'PROCESSING',
          notes: 'Inventory reserved, order is being processed',
          metadata: {
            inventoryReservationId: reservationId,
            reservedAt: timestamp
          }
        },
        'system'
      );

      // Publish order processing event
      await this.eventPublisher.publish('order.processing', {
        orderId,
        userId: order.userId
      });
    }

    // Mark event as processed
    await this.idempotencyService.markProcessed(
      'inventory.reserved',
      eventId,
      { orderId, result: 'inventory_reservation_recorded' }
    );

    this.logger.log(`Successfully processed inventory.reserved event for order ${orderId}`);
  } catch (error) {
    this.logger.error(
      `Error processing inventory.reserved event: ${error.message}`,
      error.stack
    );

    // Re-throw to trigger retry mechanism
    context.getMessage().nak();
    throw error;
  }
}
```

### 4.4. Inventory Reservation Failed Event Handler

```typescript
/**
 * Handles inventory reservation failures from Inventory Service
 */
@EventPattern('inventory.reservation_failed')
async handleInventoryReservationFailed(
  @Payload() event: InventoryReservationFailedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, timestamp, data } = event;
  const { orderId, reason, items } = data;

  this.logger.log(`Processing inventory.reservation_failed event ${eventId} for order ${orderId}`);

  try {
    // Check idempotency
    const processed = await this.idempotencyService.checkProcessed(
      'inventory.reservation_failed',
      eventId
    );

    if (processed) {
      this.logger.log(`Event ${eventId} already processed, skipping`);
      return;
    }

    // Validate event data
    if (!orderId || !reason) {
      throw new EventValidationError('Invalid inventory reservation failed event data');
    }

    // Get current order
    const order = await this.orderService.findOrderById(orderId);

    // Check if order is in a state that can be cancelled
    const cancellableStates = ['PENDING_PAYMENT', 'PAYMENT_COMPLETED', 'PROCESSING'];

    if (cancellableStates.includes(order.status.name)) {
      // Cancel the order due to inventory shortage
      await this.orderService.cancelOrder(
        orderId,
        `Inventory reservation failed: ${reason}`,
        `Failed items: ${JSON.stringify(items)}`,
        'system'
      );

      // If payment was already completed, trigger refund
      if (order.status.name === 'PAYMENT_COMPLETED' || order.paymentId) {
        await this.eventPublisher.publish('order.refund_requested', {
          orderId,
          userId: order.userId,
          paymentId: order.paymentId,
          amount: order.totalAmount,
          reason: `Inventory shortage: ${reason}`
        });
      }

      // Notify customer about cancellation
      await this.eventPublisher.publish('order.cancelled', {
        orderId,
        userId: order.userId,
        reason: `We're sorry, but some items in your order are no longer available: ${reason}`,
        autoRefundInitiated: (order.status.name === 'PAYMENT_COMPLETED')
      });
    } else {
      // Order is in a state that can't be automatically cancelled
      this.logger.warn(
        `Order ${orderId} in status ${order.status.name} cannot be automatically cancelled due to inventory failure`
      );

      // Record inventory failure but don't change order status
      await this.orderService.recordInventoryFailure(
        orderId,
        reason,
        items,
        timestamp
      );
    }

    // Mark event as processed
    await this.idempotencyService.markProcessed(
      'inventory.reservation_failed',
      eventId,
      { orderId, result: 'order_cancelled_due_to_inventory' }
    );

    this.logger.log(`Successfully processed inventory.reservation_failed event for order ${orderId}`);
  } catch (error) {
    this.logger.error(
      `Error processing inventory.reservation_failed event: ${error.message}`,
      error.stack
    );

    // For retriable errors, re-throw
    context.getMessage().nak();
    throw error;
  }
}
```

### 4.5. Shipping Updates Event Handler

```typescript
/**
 * Handles shipping updates from Shipping Service
 */
@EventPattern('shipping.status_updated')
async handleShippingStatusUpdated(
  @Payload() event: ShippingStatusUpdatedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, timestamp, data } = event;
  const { orderId, shippingId, status, carrier, trackingNumber, estimatedDelivery } = data;

  this.logger.log(`Processing shipping.status_updated event ${eventId} for order ${orderId}`);

  try {
    // Check idempotency
    const processed = await this.idempotencyService.checkProcessed(
      'shipping.status_updated',
      eventId
    );

    if (processed) {
      this.logger.log(`Event ${eventId} already processed, skipping`);
      return;
    }

    // Validate event data
    if (!orderId || !status || !shippingId) {
      throw new EventValidationError('Invalid shipping status update event data');
    }

    // Map shipping service status to order status
    let orderStatus: string;
    switch (status) {
      case 'PICKED_UP':
        orderStatus = 'SHIPPED';
        break;
      case 'DELIVERED':
        orderStatus = 'DELIVERED';
        break;
      case 'RETURNED':
        orderStatus = 'RETURNED';
        break;
      case 'FAILED':
        orderStatus = 'DELIVERY_FAILED';
        break;
      default:
        // For other statuses, just update shipping details but not order status
        await this.orderService.updateShippingDetails(
          orderId,
          {
            shippingId,
            carrier,
            trackingNumber,
            estimatedDeliveryDate: estimatedDelivery,
            lastStatus: status,
            lastUpdated: timestamp
          }
        );

        // Mark event as processed
        await this.idempotencyService.markProcessed(
          'shipping.status_updated',
          eventId,
          { orderId, result: 'shipping_details_updated' }
        );

        this.logger.log(`Updated shipping details for order ${orderId} with status ${status}`);
        return;
    }

    // Update order status based on shipping status
    await this.orderService.updateOrderStatus(
      orderId,
      {
        status: orderStatus,
        notes: `Shipping status updated to ${status}`,
        metadata: {
          shippingId,
          carrier,
          trackingNumber,
          estimatedDeliveryDate: estimatedDelivery,
          shippingStatus: status,
          shippingStatusTimestamp: timestamp
        }
      },
      'system'
    );

    // Mark event as processed
    await this.idempotencyService.markProcessed(
      'shipping.status_updated',
      eventId,
      { orderId, result: `order_status_updated_to_${orderStatus}` }
    );

    this.logger.log(`Successfully processed shipping.status_updated event for order ${orderId}`);
  } catch (error) {
    this.logger.error(
      `Error processing shipping.status_updated event: ${error.message}`,
      error.stack
    );

    // For retriable errors, re-throw
    context.getMessage().nak();
    throw error;
  }
}
```

## 5. Helper Methods

### 5.1. Process Failed Events

```typescript
/**
 * Reprocesses failed events for recovery
 */
async processFailedEvents(
  eventType: string,
  limit: number = 100
): Promise<{ processed: number, failed: number }> {
  let processed = 0;
  let failed = 0;

  this.logger.log(`Reprocessing failed ${eventType} events, limit: ${limit}`);

  try {
    // Get failed events from idempotency service
    const failedEvents = await this.idempotencyService.getFailedEvents(
      eventType,
      limit
    );

    if (failedEvents.length === 0) {
      this.logger.log(`No failed ${eventType} events to process`);
      return { processed: 0, failed: 0 };
    }

    // Process each failed event
    for (const event of failedEvents) {
      try {
        // Determine which handler to use based on event type
        switch (eventType) {
          case 'payment.completed':
            await this.handlePaymentCompleted(event.payload, event.context);
            break;
          case 'payment.failed':
            await this.handlePaymentFailed(event.payload, event.context);
            break;
          case 'inventory.reserved':
            await this.handleInventoryReserved(event.payload, event.context);
            break;
          case 'inventory.reservation_failed':
            await this.handleInventoryReservationFailed(event.payload, event.context);
            break;
          case 'shipping.status_updated':
            await this.handleShippingStatusUpdated(event.payload, event.context);
            break;
          default:
            this.logger.warn(`No handler defined for event type: ${eventType}`);
            failed++;
            continue;
        }

        processed++;
      } catch (error) {
        this.logger.error(
          `Error reprocessing failed ${eventType} event ${event.id}: ${error.message}`,
          error.stack
        );
        failed++;
      }
    }

    return { processed, failed };
  } catch (error) {
    this.logger.error(
      `Error retrieving failed ${eventType} events: ${error.message}`,
      error.stack
    );
    return { processed, failed: limit };
  }
}
```

### 5.2. Event Validation

```typescript
/**
 * Validates common event structure
 */
private validateEventStructure(event: any): boolean {
  if (!event || typeof event !== 'object') {
    return false;
  }

  // Check required fields
  if (!event.id || !event.timestamp || !event.data) {
    return false;
  }

  // Validate timestamp is a valid date
  const timestamp = new Date(event.timestamp);
  if (isNaN(timestamp.getTime())) {
    return false;
  }

  return true;
}
```

## 6. Event Schemas

### 6.1. Base Event Schema

```typescript
/**
 * Base event interface for all events
 */
export interface BaseEvent {
  id: string; // Unique event identifier
  type: string; // Event type identifier
  source: string; // Source service
  timestamp: string; // ISO-8601 timestamp
  correlationId?: string; // For tracing related events
  data: Record<string, any>; // Event payload
}
```

### 6.2. Payment Completed Event

```typescript
/**
 * Payment completed event interface
 */
export interface PaymentCompletedEvent extends BaseEvent {
  type: "payment.completed";
  data: {
    orderId: string; // Associated order ID
    paymentId: string; // Unique payment ID
    amount: number; // Payment amount
    currency: string; // Currency code
    method: string; // Payment method used
    status: "COMPLETED"; // Payment status
    transactionId?: string; // External payment provider transaction ID
    metadata?: Record<string, any>; // Additional payment details
  };
}
```

### 6.3. Payment Failed Event

```typescript
/**
 * Payment failed event interface
 */
export interface PaymentFailedEvent extends BaseEvent {
  type: "payment.failed";
  data: {
    orderId: string; // Associated order ID
    paymentId: string; // Unique payment ID
    amount: number; // Failed payment amount
    currency: string; // Currency code
    method: string; // Payment method used
    reason: string; // Failure reason
    failureCode: string; // Standardized failure code
    metadata?: Record<string, any>; // Additional payment details
  };
}
```

## 7. Error Handling

The `OrderEventHandler` implements a robust error handling strategy:

1. **Event Validation Errors**: Invalid events are logged and acknowledged without processing
2. **Business Logic Errors**: Specific business rule violations are handled gracefully
3. **Idempotency Tracking**: Events are tracked to prevent duplicate processing
4. **Retry Management**: Critical errors trigger event redelivery via NATS
5. **Dead Letter Handling**: Permanently failed events are moved to a dead letter queue
6. **Error Monitoring**: All event processing errors are logged with context for monitoring

### Error Types Example:

```typescript
/**
 * Custom error for event validation failures
 */
export class EventValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EventValidationError";
  }
}

/**
 * Custom error for idempotency violations
 */
export class DuplicateEventError extends Error {
  constructor(eventId: string) {
    super(`Event with ID ${eventId} has already been processed`);
    this.name = "DuplicateEventError";
  }
}
```

## 8. Idempotency Management

The `OrderEventHandler` ensures idempotent event processing via the `IdempotencyService`:

```typescript
/**
 * Service responsible for ensuring idempotent event processing
 */
@Injectable()
export class IdempotencyService {
  constructor(
    @InjectRepository(ProcessedEvent)
    private readonly processedEventRepository: Repository<ProcessedEvent>,
    private readonly logger: Logger
  ) {}

  /**
   * Checks if an event has already been processed
   */
  async checkProcessed(eventType: string, eventId: string): Promise<boolean> {
    const processed = await this.processedEventRepository.findOne({
      where: { eventType, eventId },
    });
    return !!processed;
  }

  /**
   * Marks an event as processed
   */
  async markProcessed(
    eventType: string,
    eventId: string,
    result: Record<string, any>
  ): Promise<void> {
    const processedEvent = new ProcessedEvent();
    processedEvent.eventType = eventType;
    processedEvent.eventId = eventId;
    processedEvent.processedAt = new Date();
    processedEvent.result = result;

    await this.processedEventRepository.save(processedEvent);
  }

  /**
   * Gets failed events for reprocessing
   */
  async getFailedEvents(
    eventType: string,
    limit: number
  ): Promise<FailedEvent[]> {
    return this.processedEventRepository.find({
      where: {
        eventType,
        processedAt: IsNull(),
        attemptCount: LessThan(5), // Max retry attempts
      },
      take: limit,
      order: { createdAt: "ASC" },
    });
  }
}
```

## 9. Testing Strategy

The `OrderEventHandler` is tested using a combination of unit and integration tests:

### 9.1. Unit Tests Example

```typescript
describe("OrderEventHandler", () => {
  let handler: OrderEventHandler;
  let orderService: MockType<OrderService>;
  let eventPublisher: MockType<EventPublisher>;
  let idempotencyService: MockType<IdempotencyService>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        OrderEventHandler,
        { provide: OrderService, useFactory: mockOrderService },
        { provide: EventPublisher, useFactory: mockEventPublisher },
        { provide: IdempotencyService, useFactory: mockIdempotencyService },
        Logger,
      ],
    }).compile();

    handler = module.get<OrderEventHandler>(OrderEventHandler);
    orderService = module.get(OrderService);
    eventPublisher = module.get(EventPublisher);
    idempotencyService = module.get(IdempotencyService);
  });

  describe("handlePaymentCompleted", () => {
    it("should update order status to PAYMENT_COMPLETED when valid event received", async () => {
      // Arrange
      const event: PaymentCompletedEvent = {
        id: "evt-123",
        type: "payment.completed",
        source: "payment-service",
        timestamp: new Date().toISOString(),
        data: {
          orderId: "order-123",
          paymentId: "payment-123",
          amount: 99.99,
          currency: "USD",
          method: "CREDIT_CARD",
          status: "COMPLETED",
        },
      };

      const context = {
        getMessage: () => ({
          ack: jest.fn(),
          nak: jest.fn(),
        }),
      } as any;

      idempotencyService.checkProcessed.mockResolvedValue(false);
      orderService.findOrderById.mockResolvedValue({
        id: "order-123",
        userId: "user-123",
        totalAmount: 99.99,
        status: { name: "PENDING_PAYMENT" },
        currency: "USD",
      });

      // Act
      await handler.handlePaymentCompleted(event, context);

      // Assert
      expect(orderService.updateOrderStatus).toHaveBeenCalledWith(
        "order-123",
        expect.objectContaining({
          status: "PAYMENT_COMPLETED",
        }),
        "system"
      );

      expect(idempotencyService.markProcessed).toHaveBeenCalledWith(
        "payment.completed",
        "evt-123",
        expect.any(Object)
      );

      expect(eventPublisher.publish).toHaveBeenCalledWith(
        "order.payment_completed",
        expect.any(Object)
      );
    });

    it("should skip processing if event was already processed", async () => {
      // Arrange
      const event = { id: "evt-123", data: { orderId: "order-123" } } as any;
      const context = { getMessage: () => ({ ack: jest.fn() }) } as any;

      idempotencyService.checkProcessed.mockResolvedValue(true);

      // Act
      await handler.handlePaymentCompleted(event, context);

      // Assert
      expect(orderService.updateOrderStatus).not.toHaveBeenCalled();
      expect(eventPublisher.publish).not.toHaveBeenCalled();
    });

    // Additional test cases...
  });

  // Tests for other event handlers...
});
```

### 9.2. Integration Tests Example

```typescript
describe("OrderEventHandler Integration", () => {
  let app: INestApplication;
  let eventHandler: OrderEventHandler;
  let orderRepository: Repository<Order>;
  let processedEventRepository: Repository<ProcessedEvent>;
  let natsClient: ClientProxy;

  beforeAll(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [
        TypeOrmModule.forRoot({
          type: "sqlite",
          database: ":memory:",
          entities: [Order, OrderItem, OrderStatus, ProcessedEvent],
          synchronize: true,
        }),
        EventEmitterModule.forRoot(),
        // Other required modules
      ],
      providers: [
        OrderEventHandler,
        OrderService,
        EventPublisher,
        IdempotencyService,
        Logger,
        // Other required providers
      ],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();

    eventHandler = moduleFixture.get<OrderEventHandler>(OrderEventHandler);
    orderRepository = moduleFixture.get(getRepositoryToken(Order));
    processedEventRepository = moduleFixture.get(
      getRepositoryToken(ProcessedEvent)
    );
    natsClient = moduleFixture.get<ClientProxy>("NATS_CLIENT");

    // Seed test data
    await seedTestData(moduleFixture);
  });

  afterAll(async () => {
    await app.close();
  });

  it("should process payment completed event and update order status", async () => {
    // Arrange
    const testOrder = await createTestOrder(orderRepository, "PENDING_PAYMENT");

    const event: PaymentCompletedEvent = {
      id: `test-event-${Date.now()}`,
      type: "payment.completed",
      source: "payment-service",
      timestamp: new Date().toISOString(),
      data: {
        orderId: testOrder.id,
        paymentId: "test-payment-id",
        amount: testOrder.totalAmount,
        currency: testOrder.currency,
        method: "CREDIT_CARD",
        status: "COMPLETED",
      },
    };

    const context = createMockNatsContext();

    // Act
    await eventHandler.handlePaymentCompleted(event, context);

    // Assert - Check order was updated
    const updatedOrder = await orderRepository.findOne({
      where: { id: testOrder.id },
      relations: ["status"],
    });

    expect(updatedOrder.status.name).toBe("PAYMENT_COMPLETED");
    expect(updatedOrder.paymentId).toBe("test-payment-id");

    // Check event was marked as processed
    const processedEvent = await processedEventRepository.findOne({
      where: { eventId: event.id },
    });

    expect(processedEvent).toBeDefined();
    expect(processedEvent.processedAt).toBeDefined();
  });

  // Additional integration tests...
});
```

## 10. References

- [Order Service](./02-order-service.md)
- [Order Status Transitions](../02-data-model-setup/04-order-status-entity.md)
- [Message Broker Configuration](../../infrastructure/event-driven-architecture.md)
- [Idempotency Patterns](../../architecture/patterns/idempotent-consumers.md)
- [Event Schema Definitions](../../architecture/api-contracts/event-schemas.md)
- [Payment Service Integration](../06-integration-points/01-payment-service-integration.md)
- [Inventory Service Integration](../06-integration-points/03-inventory-service-integration.md)
