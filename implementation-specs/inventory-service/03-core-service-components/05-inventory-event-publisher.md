# Inventory Event Publisher

## Overview

The Inventory Event Publisher component is responsible for publishing domain events related to inventory changes to external systems. It ensures that all significant state changes within the inventory system are properly communicated to other microservices through an event-driven architecture, enabling loosely coupled system integration.

## Service Interface

```typescript
export interface IInventoryEventPublisher {
  // Event Publishing Methods
  publishEvent<T extends DomainEvent>(event: T): Promise<void>;
  publishEvents<T extends DomainEvent>(events: T[]): Promise<void>;
  
  // Event Registration Methods
  registerEventHandler<T extends DomainEvent>(
    eventType: string,
    handler: EventHandler<T>
  ): void;
  
  // Replay Capabilities
  replayEvents(options: ReplayOptions): Promise<ReplayResult>;
  
  // Status and Monitoring
  getPublisherStatus(): PublisherStatus;
  getFailedEvents(options?: FailedEventOptions): Promise<FailedEvent[]>;
  retryFailedEvent(eventId: string): Promise<RetryResult>;
}
```

## Implementation

```typescript
@Injectable()
export class InventoryEventPublisher implements IInventoryEventPublisher {
  constructor(
    private readonly eventStoreRepository: IEventStoreRepository,
    private readonly messageBroker: IMessageBroker,
    private readonly failedEventRepository: IFailedEventRepository,
    private readonly configService: ConfigService,
    private readonly logger: Logger
  ) {}

  // Implementation of interface methods...
}
```

## Event Processing Flow

1. **Event Creation**
   - Domain services create events representing state changes
   - Events are validated and enriched with metadata

2. **Event Storage**
   - Events are persisted to the event store for durability
   - This occurs in the same transaction as state changes

3. **Event Publication**
   - Stored events are published to the message broker
   - Events are formatted according to the event schema

4. **Delivery Confirmation**
   - Acknowledgements from the message broker are tracked
   - Failed publications are stored for retry

5. **Retry Mechanism**
   - Failed events are retried based on configurable policies
   - Dead-letter handling for persistently failing events

## Event Types and Structure

### Base Event Structure
```typescript
export interface DomainEvent {
  eventId: string;           // Unique identifier for this event instance
  eventType: string;         // Type name of the event
  aggregateId: string;       // ID of the aggregate that emitted the event
  aggregateType: string;     // Type of the aggregate (e.g., "InventoryItem")
  timestamp: Date;           // When the event occurred
  version: number;           // Event schema version
  metadata?: {
    correlationId?: string;  // To trace related operations
    causationId?: string;    // ID of the event or command that caused this event
    userId?: string;         // User who initiated the action
    source?: string;         // Source system
  };
  payload: any;              // Event-specific data
}
```

### Inventory-Specific Events

The publisher handles various inventory domain events, including:

1. **Item Events**
   - InventoryItemCreatedEvent
   - InventoryItemUpdatedEvent
   - InventoryItemDeactivatedEvent

2. **Stock Events**
   - StockLevelChangedEvent
   - StockTransferredEvent
   - LowStockThresholdReachedEvent
   - StockoutEvent

3. **Allocation Events**
   - AllocationCreatedEvent
   - AllocationConfirmedEvent
   - AllocationCancelledEvent
   - AllocationFulfilledEvent

4. **Warehouse Events**
   - WarehouseCreatedEvent
   - WarehouseUpdatedEvent
   - WarehouseBinCreatedEvent
   - ItemAssignedToLocationEvent

## Message Broker Integration

The event publisher supports integration with multiple message broker technologies:

1. **Amazon SNS/SQS**
   - Topic-based publication
   - Dead-letter queue support
   - FIFO capabilities for ordered events

2. **Apache Kafka**
   - Partitioned topics by aggregate ID
   - Schema registry integration
   - Consumer group support

3. **RabbitMQ**
   - Exchange and queue configuration
   - Message confirmation
   - Dead-letter exchange support

## Event Schema Management

Event schemas are versioned to ensure backward compatibility:

1. **Schema Registry**
   - Central repository for event schemas
   - Versioning support
   - Compatibility checking

2. **Schema Evolution**
   - Adding optional fields is allowed
   - Removing fields requires a new version
   - Field type changes require a new version

3. **Compatibility Modes**
   - BACKWARD: New schema can read old data
   - FORWARD: Old schema can read new data
   - FULL: Both backward and forward compatibility

## Error Handling and Reliability

The publisher implements several reliability mechanisms:

1. **Transactional Outbox Pattern**
   - Events are stored before being published
   - Ensures events are never lost, even during failures
   - Separate process polls outbox to publish events

2. **Retry Policies**
   - Configurable retry intervals
   - Exponential backoff
   - Maximum retry attempts

3. **Dead-Letter Handling**
   - Events that repeatedly fail are moved to dead-letter storage
   - Administrative interface for viewing and handling dead-lettered events
   - Manual retry or resolution capabilities

4. **Circuit Breaker**
   - Prevents cascading failures
   - Temporary suspension of publishing when broker is unavailable
   - Automatic recovery when connectivity is restored

## Monitoring and Observability

The publisher exposes monitoring capabilities:

1. **Metrics**
   - Event publication rates
   - Success/failure counts
   - Latency measurements
   - Retry counts

2. **Health Checks**
   - Broker connection status
   - Outbox processor status
   - Failed event count thresholds

3. **Logging**
   - Structured logging of publication attempts
   - Error details for failed publications
   - Retry attempts and outcomes

## Example Usage

```typescript
// In a domain service
const inventoryService = new InventoryManagementService(
  itemRepository,
  transactionRepository,
  inventoryEventPublisher, // Dependency injected
  logger
);

// Service creates and publishes events
async addStock(command: AddStockCommand): Promise<StockTransaction> {
  // Process business logic...
  
  // Create event
  const event = new StockLevelChangedEvent({
    inventoryItemId: item.id,
    warehouseId: item.warehouseId,
    previousQuantity: previousLevel,
    newQuantity: newLevel,
    changeAmount: command.quantity,
    changeReason: 'MANUAL_ADJUSTMENT',
    transactionId: transaction.id
  });
  
  // Publish event
  await this.eventPublisher.publishEvent(event);
  
  return transaction;
}

// Configuration for publisher
const publisherConfig = {
  broker: {
    type: 'KAFKA',
    bootstrapServers: ['kafka-1:9092', 'kafka-2:9092'],
    clientId: 'inventory-service',
    retryCount: 3,
    retryInterval: 1000
  },
  outbox: {
    pollingInterval: 500,
    batchSize: 50
  },
  topics: {
    inventoryEvents: 'inventory-events',
    deadLetterQueue: 'inventory-events-dlq'
  }
};
```