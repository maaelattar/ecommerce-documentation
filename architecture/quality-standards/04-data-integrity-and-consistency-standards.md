# Data Integrity and Consistency Standards

## 1. Overview

This document defines the standards and best practices for ensuring data integrity and consistency across the distributed services of our e-commerce platform. Maintaining reliable data across multiple services and databases is critical for business operations and customer trust.

## 2. Core Principles

### 2.1. Data Ownership

- Each domain service owns its core data entities exclusively
- Single source of truth for each data entity
- Clear boundaries for data responsibility
- Explicit ownership documentation for all data entities

### 2.2. Consistency Models

- Understand and choose appropriate consistency models
- Strong consistency for critical operations (payments, inventory)
- Eventual consistency for non-critical operations (analytics, recommendations)
- Document consistency requirements for each data entity

### 2.3. Integrity Guarantees

- Define integrity constraints at both application and database levels
- Implement validation at service boundaries
- Ensure transactional integrity within service boundaries
- Use compensating transactions for cross-service operations

### 2.4. Truth Reconciliation

- Implement reconciliation processes for eventual consistency
- Regular verification of cross-service data consistency
- Automated detection and alerting for data inconsistencies
- Clear procedures for resolving data conflicts

## 3. Data Modeling Principles

### 3.1. Entity Design

- Design entities with clear boundaries and relationships
- Use UUIDs as primary keys for all entities for global uniqueness
- Define immutable properties vs. mutable properties
- Document entity lifecycle and state transitions

### 3.2. Data Duplication Strategy

```
┌────────────────┐         ┌────────────────┐
│                │         │                │
│  Service A     │         │  Service B     │
│  (Owner)       │         │  (Consumer)    │
│                │         │                │
└───────┬────────┘         └────────┬───────┘
        │                           │
        │                           │
        ▼                           ▼
┌───────────────┐          ┌────────────────┐
│               │          │                │
│  Database A   │          │  Database B    │
│  (Primary)    │          │  (Replica)     │
│               │          │                │
└───────────────┘          └────────────────┘
```

- Acceptable duplication scenarios:

  - Read-only projections for query optimization
  - Caching for performance improvements
  - Reference data needed for validation
  - Historical data for audit purposes

- Duplication requirements:
  - Document all duplicated data with:
    - Source of truth identification
    - Update frequency
    - Staleness tolerance
    - Reconciliation mechanism
  - Implement clear update patterns

### 3.3. Schema Design

- Use schema versioning for all data structures
- Implement forward and backward compatible schemas
- Use schema registries for shared data formats
- Include metadata in schemas:
  - Creation timestamp
  - Last modified timestamp
  - Version information
  - Source service identifier

### 3.4. Reference Data Management

- Centralize management of reference data
- Implement versioning for reference data
- Distribute reference data via events or APIs
- Cache reference data with appropriate invalidation strategies

## 4. Transactional Patterns

### 4.1. Local Transactions

- Use ACID transactions within service boundaries
- Implement optimistic concurrency control for high contention data
- Define transactional boundaries in service design
- Document transaction isolation levels

### 4.2. Distributed Transactions

- Avoid two-phase commit (2PC) across services when possible
- Use saga pattern for operations spanning multiple services
- Implement compensation logic for failed operations
- Document transaction flows and rollback procedures

### 4.3. Saga Pattern Implementation

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  Order   │      │ Payment  │      │Inventory │      │ Shipping │
│ Service  │      │ Service  │      │ Service  │      │ Service  │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │                 │
     │ Create Order    │                 │                 │
     │───────────────► │                 │                 │
     │                 │                 │                 │
     │◄ ─ ─ ─ ─ ─ ─ ─ ─│                 │                 │
     │                 │                 │                 │
     │                 │ Process Payment │                 │
     │                 │───────────────► │                 │
     │                 │                 │                 │
     │                 │◄ ─ ─ ─ ─ ─ ─ ─ ─│                 │
     │                 │                 │                 │
     │                 │                 │ Reserve Items   │
     │                 │                 │───────────────► │
     │                 │                 │                 │
     │                 │                 │◄ ─ ─ ─ ─ ─ ─ ─ ─│
     │                 │                 │                 │
     │         If any step fails, execute compensating transactions:
     │                 │                 │                 │
     │◄ ─ ─ ─ ─ ─ ─ ─ ─│                 │                 │
     │                 │                 │                 │
     │ Cancel Order    │                 │                 │
     │───────────────► │                 │                 │
     │                 │                 │                 │
     │                 │ Refund Payment  │                 │
     │                 │───────────────► │                 │
     │                 │                 │                 │
     │                 │                 │ Release Items   │
     │                 │                 │───────────────► │
```

#### 4.3.1. Choreography-Based Sagas

- Services exchange events to progress through saga steps
- Each service listens for events and performs its actions
- Each service publishes events upon successful completion
- Services implement compensation logic for failure scenarios

Example implementation:

```typescript
// Order Service
@EventPattern('payment.completed')
async handlePaymentCompleted(event: PaymentCompletedEvent): Promise<void> {
  const { orderId, paymentId } = event.data;

  try {
    // Update order status
    const order = await this.orderRepository.findById(orderId);
    order.status = OrderStatus.PAYMENT_COMPLETED;
    order.paymentId = paymentId;
    await this.orderRepository.save(order);

    // Publish event for inventory service
    await this.eventBus.publish('order.payment_completed', {
      orderId,
      items: order.items.map(item => ({
        productId: item.productId,
        quantity: item.quantity
      }))
    });
  } catch (error) {
    // Handle failure - initiate compensation
    this.logger.error(`Failed to process payment completion: ${error.message}`);
    await this.eventBus.publish('order.payment_completion_failed', {
      orderId,
      paymentId,
      reason: error.message
    });
  }
}
```

#### 4.3.2. Orchestration-Based Sagas

- Central orchestrator service manages the saga workflow
- Orchestrator tracks saga state and progress
- Orchestrator calls services sequentially or in parallel as needed
- Orchestrator manages compensation logic on failures

Example implementation:

```typescript
// Order Saga Orchestrator
async executeOrderSaga(orderId: string): Promise<void> {
  // Start saga
  const saga = await this.sagaRepository.create({
    type: 'CREATE_ORDER',
    entityId: orderId,
    status: 'STARTED',
    steps: [
      { name: 'PROCESS_PAYMENT', status: 'PENDING' },
      { name: 'RESERVE_INVENTORY', status: 'PENDING' },
      { name: 'SCHEDULE_SHIPPING', status: 'PENDING' }
    ]
  });

  try {
    // Step 1: Process payment
    await this.updateSagaStep(saga.id, 'PROCESS_PAYMENT', 'IN_PROGRESS');
    const paymentResult = await this.paymentService.processPayment(orderId);
    await this.updateSagaStep(saga.id, 'PROCESS_PAYMENT', 'COMPLETED', paymentResult);

    // Step 2: Reserve inventory
    await this.updateSagaStep(saga.id, 'RESERVE_INVENTORY', 'IN_PROGRESS');
    const inventoryResult = await this.inventoryService.reserveItems(orderId);
    await this.updateSagaStep(saga.id, 'RESERVE_INVENTORY', 'COMPLETED', inventoryResult);

    // Step 3: Schedule shipping
    await this.updateSagaStep(saga.id, 'SCHEDULE_SHIPPING', 'IN_PROGRESS');
    const shippingResult = await this.shippingService.scheduleDelivery(orderId);
    await this.updateSagaStep(saga.id, 'SCHEDULE_SHIPPING', 'COMPLETED', shippingResult);

    // Complete saga
    await this.sagaRepository.update(saga.id, { status: 'COMPLETED' });
  } catch (error) {
    // Handle failure - execute compensation
    this.logger.error(`Saga failed for order ${orderId}: ${error.message}`);
    await this.executeCompensation(saga);
  }
}

async executeCompensation(saga: Saga): Promise<void> {
  // Update saga status
  await this.sagaRepository.update(saga.id, { status: 'COMPENSATING' });

  // Execute compensations in reverse order
  const completedSteps = saga.steps.filter(step => step.status === 'COMPLETED');

  for (const step of completedSteps.reverse()) {
    try {
      switch (step.name) {
        case 'SCHEDULE_SHIPPING':
          await this.shippingService.cancelDelivery(saga.entityId);
          break;
        case 'RESERVE_INVENTORY':
          await this.inventoryService.releaseItems(saga.entityId);
          break;
        case 'PROCESS_PAYMENT':
          await this.paymentService.refundPayment(saga.entityId);
          break;
      }

      await this.updateSagaStep(saga.id, step.name, 'COMPENSATED');
    } catch (error) {
      this.logger.error(`Compensation failed for step ${step.name}: ${error.message}`);
      // Mark compensation as failed but continue with other compensations
      await this.updateSagaStep(saga.id, step.name, 'COMPENSATION_FAILED', { error: error.message });
    }
  }

  // Update saga status
  await this.sagaRepository.update(saga.id, { status: 'COMPENSATED' });
}
```

### 4.4. Outbox Pattern

- Use the outbox pattern for reliable event publishing
- Store outgoing events in a local transaction with business data
- Process outbox with a separate background job
- Mark events as published once successfully delivered

```typescript
// Using outbox pattern for reliable event publishing
@Transactional()
async createOrder(orderData: CreateOrderDto): Promise<Order> {
  // Create order entity
  const order = this.orderRepository.create({
    ...orderData,
    status: OrderStatus.CREATED
  });

  // Save order
  const savedOrder = await this.orderRepository.save(order);

  // Create outbox event in same transaction
  await this.outboxRepository.save({
    aggregateType: 'Order',
    aggregateId: savedOrder.id,
    eventType: 'order.created',
    payload: {
      id: savedOrder.id,
      userId: savedOrder.userId,
      items: savedOrder.items,
      totalAmount: savedOrder.totalAmount,
      createdAt: savedOrder.createdAt
    }
  });

  return savedOrder;
}

// Background job to process outbox
@Cron('*/5 * * * * *') // Every 5 seconds
async processOutbox(): Promise<void> {
  // Get unpublished events
  const events = await this.outboxRepository.findUnpublished(10);

  for (const event of events) {
    try {
      // Publish event
      await this.eventBus.publish(event.eventType, event.payload);

      // Mark as published
      await this.outboxRepository.markAsPublished(event.id);
    } catch (error) {
      this.logger.error(`Failed to publish event ${event.id}: ${error.message}`);

      // Increment retry count
      await this.outboxRepository.incrementRetryCount(event.id);
    }
  }
}
```

## 5. Consistency Patterns

### 5.1. Eventual Consistency

- Implement event-based updates for eventual consistency
- Document acceptable staleness windows for each data type
- Use version fields or timestamps for conflict resolution
- Implement idempotent event handlers

### 5.2. Read-Your-Writes Consistency

- Implement techniques to ensure users see their own updates:
  - Session-based routing for API Gateway
  - Client-side caching of writes
  - Versioned responses with client-side validation

### 5.3. Causal Consistency

- Maintain happened-before relationships in distributed operations
- Use version vectors or Lamport timestamps for ordering
- Ensure operations that depend on each other respect causal order
- Document causal dependencies between operations

### 5.4. Strong Consistency for Critical Operations

- Identify truly critical operations requiring strong consistency
- Implement synchronous verification for these operations
- Consider using consensus algorithms for critical coordination
- Design for degraded operation when strong consistency is unavailable

## 6. Data Synchronization Patterns

### 6.1. Event-Based Synchronization

- Publish domain events for all state changes
- Subscribe to relevant events from other services
- Implement idempotent event handlers
- Use event versioning for schema evolution

```typescript
// Product Service publishing a product updated event
@Transactional()
async updateProduct(id: string, data: UpdateProductDto): Promise<Product> {
  // Get existing product
  const product = await this.productRepository.findById(id);
  if (!product) {
    throw new NotFoundException(`Product with ID ${id} not found`);
  }

  // Track changed fields
  const changedFields = [];
  for (const [key, value] of Object.entries(data)) {
    if (product[key] !== value) {
      changedFields.push(key);
    }
  }

  // Update product
  Object.assign(product, data);
  product.updatedAt = new Date();
  const updatedProduct = await this.productRepository.save(product);

  // Publish event with changed fields
  if (changedFields.length > 0) {
    await this.eventPublisher.publish('product.updated', {
      productId: updatedProduct.id,
      changedFields,
      version: updatedProduct.version,
      timestamp: updatedProduct.updatedAt.toISOString()
    });
  }

  return updatedProduct;
}

// Order Service subscribing to product updates
@EventPattern('product.updated')
async handleProductUpdated(event: ProductUpdatedEvent): Promise<void> {
  const { productId, changedFields, version, timestamp } = event;

  // Skip if no relevant fields changed
  const relevantFields = ['name', 'price', 'status'];
  if (!changedFields.some(field => relevantFields.includes(field))) {
    return;
  }

  // Get product from cache or API
  const product = await this.productService.getProductDetails(productId);

  // Update local product cache
  await this.productCacheRepository.upsert(productId, {
    name: product.name,
    price: product.price,
    status: product.status,
    updatedAt: new Date(timestamp),
    version
  });

  // If product is discontinued, flag affected orders
  if (product.status === 'DISCONTINUED') {
    await this.orderService.flagOrdersWithDiscontinuedProduct(productId);
  }
}
```

### 6.2. Batch Synchronization

- Implement periodic reconciliation jobs for data consistency
- Use checksums or version comparisons for efficient detection
- Schedule jobs during off-peak hours for resource-intensive reconciliation
- Maintain detailed logs of reconciliation operations

### 6.3. CDC (Change Data Capture)

- Use database CDC for high-volume data synchronization
- Stream database changes to a message broker
- Transform CDC events into domain events
- Implement consumers for CDC streams

### 6.4. API-Based Synchronization

- Implement polling or webhook mechanisms for external integrations
- Use pagination for large datasets
- Implement delta queries for efficient synchronization
- Document API versioning and backward compatibility

## 7. Data Validation Standards

### 7.1. Input Validation

- Validate all input data against schema definitions
- Implement consistent validation across all services
- Include size limits, format constraints, and business rules
- Return standardized validation error responses

### 7.2. Domain Validation

- Apply business rules validation beyond basic schema validation
- Implement validation at both REST/API and event consumption layers
- Use domain services for complex validation logic
- Document domain constraints and validation rules

### 7.3. Cross-Entity Validation

- Implement explicit validators for relationships between entities
- Use asynchronous validation workflows for cross-service constraints
- Document entity relationships and validation dependencies
- Define clear error handling for constraint violations

### 7.4. Validation Implementation

```typescript
// Example of comprehensive validation in Order Service
@Injectable()
export class OrderValidator {
  constructor(
    private readonly productService: ProductServiceClient,
    private readonly userService: UserServiceClient,
    private readonly inventoryCache: InventoryCacheRepository
  ) {}

  async validateNewOrder(orderData: CreateOrderDto): Promise<ValidationResult> {
    const errors = [];

    // Basic schema validation
    const schemaErrors = this.validateSchema(orderData);
    if (schemaErrors.length > 0) {
      return { valid: false, errors: schemaErrors };
    }

    // User exists and is active
    try {
      const user = await this.userService.getUser(orderData.userId);
      if (user.status !== "ACTIVE") {
        errors.push({ field: "userId", message: "User account is not active" });
      }
    } catch (error) {
      errors.push({ field: "userId", message: "Invalid user ID" });
    }

    // Product validation
    const productIds = orderData.items.map((item) => item.productId);
    const products = await this.productService.getProductsBatch(productIds);

    // Check each item
    for (const item of orderData.items) {
      const product = products.get(item.productId);

      // Product exists and is active
      if (!product) {
        errors.push({
          field: `items[${item.productId}]`,
          message: "Product not found",
        });
        continue;
      }

      if (product.status !== "ACTIVE") {
        errors.push({
          field: `items[${item.productId}]`,
          message: "Product is not available for purchase",
        });
      }

      // Quantity is valid
      if (item.quantity <= 0) {
        errors.push({
          field: `items[${item.productId}].quantity`,
          message: "Quantity must be positive",
        });
      }

      // Check inventory availability (from cache)
      const inventory = await this.inventoryCache.getInventory(item.productId);
      if (inventory && inventory.available < item.quantity) {
        errors.push({
          field: `items[${item.productId}].quantity`,
          message: "Requested quantity exceeds available inventory",
        });
      }
    }

    // Shipping address validation
    if (orderData.shippingAddress) {
      const addressErrors = this.validateAddress(orderData.shippingAddress);
      errors.push(...addressErrors);
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  // Helper methods...
}
```

## 8. Data Consistency Monitoring

### 8.1. Consistency Metrics

- Track and monitor key consistency metrics:
  - Replication lag
  - Event processing delay
  - Reconciliation exceptions
  - Duplicate events detected
  - Conflict resolution events

### 8.2. Data Quality Monitoring

- Implement data quality checks across services
- Schedule regular data integrity scans
- Generate data quality reports
- Alert on data anomalies

### 8.3. Reconciliation Jobs

- Implement automated reconciliation between data sources
- Schedule regular integrity checks
- Document reconciliation procedures and outcomes
- Track and review reconciliation exceptions

Example reconciliation job:

```typescript
@Injectable()
export class OrderProductReconciliationService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly productServiceClient: ProductServiceClient,
    private readonly logger: Logger
  ) {}

  // Run daily at 1:00 AM
  @Cron("0 1 * * *")
  async reconcileOrderProducts(): Promise<ReconciliationReport> {
    this.logger.log("Starting order-product reconciliation job");

    const results = {
      ordersProcessed: 0,
      inconsistenciesFound: 0,
      reconciled: 0,
      failed: 0,
    };

    // Get recent orders in batches
    let page = 1;
    const pageSize = 100;
    let hasMore = true;

    while (hasMore) {
      // Get batch of orders
      const orders = await this.orderRepository.findRecent(page, pageSize);
      hasMore = orders.length === pageSize;
      page++;

      results.ordersProcessed += orders.length;

      // Check each order
      for (const order of orders) {
        try {
          // Get product information from product service
          const productIds = order.items.map((item) => item.productId);
          const products = await this.productServiceClient.getProductsBatch(
            productIds
          );

          // Check for inconsistencies
          const inconsistencies = [];

          for (const item of order.items) {
            const product = products.get(item.productId);

            // Skip if product no longer exists (could be deleted)
            if (!product) continue;

            // Check for name differences
            if (item.productName !== product.name) {
              inconsistencies.push({
                orderId: order.id,
                productId: item.productId,
                field: "name",
                orderValue: item.productName,
                productValue: product.name,
              });
            }

            // Check for significant price differences (> 1%)
            const priceDifference = Math.abs(
              (item.unitPrice - product.price) / product.price
            );
            if (priceDifference > 0.01) {
              inconsistencies.push({
                orderId: order.id,
                productId: item.productId,
                field: "price",
                orderValue: item.unitPrice,
                productValue: product.price,
                difference: priceDifference,
              });
            }
          }

          // Record inconsistencies
          if (inconsistencies.length > 0) {
            results.inconsistenciesFound += inconsistencies.length;

            // Log inconsistencies
            await this.logInconsistencies(order.id, inconsistencies);

            // Update order product data where appropriate
            // (e.g. product names, but not prices for completed orders)
            if (this.shouldReconcile(order)) {
              await this.reconcileOrderProducts(
                order,
                inconsistencies,
                products
              );
              results.reconciled++;
            }
          }
        } catch (error) {
          this.logger.error(
            `Failed to reconcile order ${order.id}: ${error.message}`
          );
          results.failed++;
        }
      }
    }

    this.logger.log(
      `Completed order-product reconciliation: ${JSON.stringify(results)}`
    );
    return results;
  }

  // Helper methods...
}
```

## 9. Error Handling and Recovery

### 9.1. Error Categorization

- Categorize errors by type and severity:
  - Transient vs. persistent
  - Retriable vs. non-retriable
  - Data corruption vs. availability issues
- Implement different handling strategies by category

### 9.2. Recovery Procedures

- Document automated and manual recovery procedures
- Implement recovery workflows for common error scenarios
- Include validation steps after recovery
- Track recovery operations and success rates

### 9.3. Retry Strategies

- Implement exponential backoff with jitter
- Set appropriate retry limits for different operations
- Use dead-letter queues for failed operations
- Implement circuit breakers for failing dependencies

## 10. Data Migration Standards

### 10.1. Schema Evolution

- Implement backward and forward compatible schema changes
- Use schema versioning for all entities
- Support multiple schema versions during transition periods
- Document schema migration paths

### 10.2. Zero-Downtime Migrations

- Implement expansion-contraction pattern for schema changes
  1. Add new fields/columns/tables without removing old ones
  2. Deploy code that writes to both old and new structures
  3. Migrate existing data to new structure
  4. Deploy code that reads from new structure but still writes to both
  5. Verify all system components are using new structure
  6. Deploy code that only uses new structure
  7. Remove old structure

### 10.3. Data Migration Tools

- Develop or adopt standardized migration tools
- Implement validation for all migrations
- Include rollback capability
- Track migration progress and status

### 10.4. Migration Testing

- Test migrations with production-scale data volumes
- Measure performance impact of migrations
- Test rollback procedures
- Simulate failure scenarios during migration

## 11. Implementation Examples

### 11.1. Event-Sourced Entity

```typescript
// Example of an event-sourced entity with proper versioning and consistency
@Injectable()
export class OrderAggregate {
  constructor(
    private readonly eventStore: EventStore,
    private readonly logger: Logger
  ) {}

  async getOrder(orderId: string): Promise<Order> {
    // Retrieve events for this order
    const events = await this.eventStore.getEvents("Order", orderId);

    // Apply events to build current state
    return this.applyEvents(events);
  }

  async createOrder(command: CreateOrderCommand): Promise<Order> {
    // Validate command
    this.validateCreateOrder(command);

    // Create Order Created event
    const event = {
      type: "OrderCreated",
      aggregateId: command.orderId,
      aggregateType: "Order",
      version: 1,
      timestamp: new Date().toISOString(),
      data: {
        userId: command.userId,
        items: command.items,
        shippingAddress: command.shippingAddress,
        totalAmount: this.calculateTotal(command.items),
      },
    };

    // Store event
    await this.eventStore.appendEvent("Order", command.orderId, event);

    // Return new state
    return this.applyEvents([event]);
  }

  async addOrderItem(command: AddOrderItemCommand): Promise<Order> {
    // Get current state
    const order = await this.getOrder(command.orderId);

    // Business rules validation
    if (order.status !== "DRAFT") {
      throw new Error("Cannot add items to non-draft orders");
    }

    // Create event
    const event = {
      type: "OrderItemAdded",
      aggregateId: command.orderId,
      aggregateType: "Order",
      version: order.version + 1,
      timestamp: new Date().toISOString(),
      data: {
        item: command.item,
        newTotalAmount: this.calculateTotal([...order.items, command.item]),
      },
    };

    // Store event with optimistic concurrency check
    await this.eventStore.appendEvent(
      "Order",
      command.orderId,
      event,
      order.version
    );

    // Return updated state
    return this.applyEvents([...order.events, event]);
  }

  private applyEvents(events: Event[]): Order {
    // Initial state
    let order = {
      id: events[0]?.aggregateId,
      version: 0,
      status: "DRAFT",
      items: [],
      totalAmount: 0,
      events: [],
    };

    // Apply each event
    for (const event of events) {
      order = this.applyEvent(order, event);
      order.version = event.version;
      order.events.push(event);
    }

    return order;
  }

  private applyEvent(order: Order, event: Event): Order {
    switch (event.type) {
      case "OrderCreated":
        return {
          ...order,
          status: "DRAFT",
          userId: event.data.userId,
          items: event.data.items,
          shippingAddress: event.data.shippingAddress,
          totalAmount: event.data.totalAmount,
          createdAt: event.timestamp,
        };

      case "OrderItemAdded":
        return {
          ...order,
          items: [...order.items, event.data.item],
          totalAmount: event.data.newTotalAmount,
          updatedAt: event.timestamp,
        };

      // Other event handlers...

      default:
        return order;
    }
  }

  // Other methods...
}
```

### 11.2. Handling Concurrent Updates

```typescript
// Example of handling concurrent updates with optimistic locking
@Injectable()
export class ProductRepository {
  constructor(
    @InjectRepository(Product)
    private readonly repository: Repository<Product>,
    private readonly logger: Logger
  ) {}

  async update(
    id: string,
    data: Partial<Product>,
    version: number
  ): Promise<Product> {
    try {
      // Attempt to update with version check
      const result = await this.repository.update(
        { id, version },
        {
          ...data,
          version: version + 1,
          updatedAt: new Date(),
        }
      );

      // Check if update succeeded
      if (result.affected === 0) {
        // Get current version
        const current = await this.repository.findOne({ where: { id } });

        if (!current) {
          throw new NotFoundException(`Product with ID ${id} not found`);
        }

        if (current.version !== version) {
          throw new ConflictException(
            `Concurrency conflict: Product with ID ${id} has been modified. ` +
              `Current version: ${current.version}, submitted version: ${version}`
          );
        }

        // Something else went wrong
        throw new InternalServerErrorException("Failed to update product");
      }

      // Return updated entity
      return this.repository.findOne({ where: { id } });
    } catch (error) {
      this.logger.error(`Failed to update product ${id}: ${error.message}`);
      throw error;
    }
  }
}

// Using the optimistic concurrency control
@Controller("products")
export class ProductController {
  @Put(":id")
  async updateProduct(
    @Param("id") id: string,
    @Body() data: UpdateProductDto,
    @Headers("If-Match") etag: string
  ): Promise<ProductDto> {
    // Extract version from ETag
    const version = this.extractVersionFromETag(etag);

    try {
      // Update with version check
      const product = await this.productService.update(id, data, version);

      // Set ETag header on response
      return this.mapper.toDto(product);
    } catch (error) {
      if (error instanceof ConflictException) {
        // Return 412 Precondition Failed for version conflicts
        throw new PreconditionFailedException(error.message);
      }
      throw error;
    }
  }

  private extractVersionFromETag(etag: string): number {
    if (!etag) throw new BadRequestException("ETag header is required");

    // Remove quotes and "W/" weak validator prefix if present
    const cleanEtag = etag.replace(/^W\//, "").replace(/"/g, "");
    const version = parseInt(cleanEtag, 10);

    if (isNaN(version)) {
      throw new BadRequestException("Invalid ETag format");
    }

    return version;
  }
}
```

## 12. References

- [Database Per Service Pattern](../patterns/database-per-service.md)
- [Saga Pattern](../patterns/saga-pattern.md)
- [CQRS Pattern](../patterns/cqrs.md)
- [Event Sourcing](../patterns/event-sourcing.md)
- [Outbox Pattern](../patterns/transactional-outbox.md)
- [AWS Architecture Best Practices](../technology-decisions-aws-centeric/data-consistency.md)
