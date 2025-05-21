# Event Store Implementation

## 1. Overview

The event store is the backbone of our event sourcing implementation, responsible for storing all domain events in a reliable, immutable, and queryable manner. It serves as the source of truth for the entire system, capturing every state change.

## 2. Implementation Technology

We will use Amazon DynamoDB for our event store due to its:
- Scalability and performance
- Durability and reliability
- Seamless integration with AWS infrastructure
- Point-in-time recovery capabilities
- Support for transaction operations

## 3. Schema Design

### 3.1. Primary Event Store Table (ProductEvents)

**Table Name:** `ProductService-Events`

**Key Structure:**
- **Partition Key:** `entityId` (String) - The ID of the aggregate (e.g., productId, categoryId)
- **Sort Key:** `sequenceNumber` (Number) - Auto-incrementing sequence number for ordering events

**Attributes:**
- `eventId` (String) - UUID uniquely identifying the event
- `eventType` (String) - Type of event (e.g., "ProductCreated", "PriceUpdated")
- `eventTime` (String) - ISO 8601 timestamp of when the event occurred
- `eventData` (Map) - JSON serialized event payload
- `version` (String) - Schema version of the event
- `userId` (String) - ID of user or system that triggered the event
- `correlationId` (String) - For tracing related events across services
- `aggregateType` (String) - Type of aggregate (e.g., "Product", "Category")

**GSI 1: EventTypeIndex**
- **Partition Key:** `aggregateType`
- **Sort Key:** `eventTime`
- Enables querying events by aggregate type and time

**GSI 2: UserActionIndex**
- **Partition Key:** `userId`
- **Sort Key:** `eventTime`
- Enables querying events by user for audit purposes

### 3.2. Snapshot Table (ProductSnapshots)

**Table Name:** `ProductService-Snapshots`

**Key Structure:**
- **Partition Key:** `entityId` (String) - The ID of the aggregate
- **Sort Key:** `version` (Number) - Version of the aggregate at snapshot time

**Attributes:**
- `aggregateType` (String) - Type of aggregate (e.g., "Product", "Category")
- `snapshotData` (Map) - JSON serialized aggregate state
- `snapshotTime` (String) - ISO 8601 timestamp of when the snapshot was created
- `eventSequenceNumber` (Number) - The sequence number of the last event included in the snapshot

## 4. Core Functions

### 4.1. Event Storage

```typescript
interface EventStore {
  // Store a new event for an aggregate
  appendEvent<T>(
    aggregateType: string,
    entityId: string,
    eventType: string,
    eventData: T,
    userId: string,
    correlationId: string,
    expectedVersion?: number
  ): Promise<number>;

  // Get events for an aggregate
  getEvents(
    entityId: string,
    fromSequence?: number,
    toSequence?: number
  ): Promise<Event[]>;

  // Get events by type within a time range
  getEventsByType(
    aggregateType: string,
    eventType: string,
    fromTime?: string,
    toTime?: string
  ): Promise<Event[]>;

  // Create a snapshot of an aggregate state
  createSnapshot<T>(
    aggregateType: string,
    entityId: string,
    version: number,
    snapshotData: T,
    eventSequenceNumber: number
  ): Promise<void>;

  // Get the latest snapshot for an aggregate
  getLatestSnapshot<T>(
    entityId: string
  ): Promise<Snapshot<T> | null>;
}
```

### 4.2. Optimistic Concurrency Control

To handle concurrent modifications, each aggregate will maintain a version counter. When storing events:

1. The command handler loads the current version of the aggregate
2. The expected version is specified when appending an event
3. If the current version doesn't match the expected version, a concurrency exception is thrown
4. The client must reload the aggregate and retry the operation

### 4.3. Snapshots

To optimize loading aggregates with many events:

1. Snapshots will be created periodically (e.g., every 100 events)
2. When loading an aggregate, the system first checks for the latest snapshot
3. If a snapshot exists, only events after the snapshot need to be loaded
4. The aggregate state is reconstructed by applying these events

## 5. Implementation Example

```typescript
export class DynamoDBEventStore implements EventStore {
  constructor(
    private readonly dynamoDbClient: DynamoDBClient,
    private readonly eventTableName: string,
    private readonly snapshotTableName: string,
  ) {}

  async appendEvent<T>(
    aggregateType: string,
    entityId: string,
    eventType: string,
    eventData: T,
    userId: string,
    correlationId: string,
    expectedVersion?: number
  ): Promise<number> {
    // Get current highest sequence number
    const currentEvents = await this.getEvents(entityId, undefined, undefined, 1, true);
    const currentSeq = currentEvents.length > 0 
      ? currentEvents[0].sequenceNumber 
      : 0;
    const newSeq = currentSeq + 1;

    // Check version if expectedVersion provided
    if (expectedVersion !== undefined && currentSeq !== expectedVersion) {
      throw new ConcurrencyError(
        `Optimistic concurrency error: expected version ${expectedVersion}, got ${currentSeq}`
      );
    }

    // Prepare event item
    const eventItem = {
      entityId,
      sequenceNumber: newSeq,
      eventId: uuid(),
      aggregateType,
      eventType,
      eventTime: new Date().toISOString(),
      eventData: JSON.stringify(eventData),
      userId,
      correlationId,
      version: '1.0', // Schema version
    };

    // Store event in DynamoDB
    await this.dynamoDbClient.send(
      new PutItemCommand({
        TableName: this.eventTableName,
        Item: marshall(eventItem),
        ConditionExpression: 'attribute_not_exists(sequenceNumber)',
      })
    );

    return newSeq;
  }

  // Other methods implementation...
}
```

## 6. Performance Considerations

1. **Read Optimization**: Use projections for read models to avoid reconstructing state from events for every query
2. **Write Optimization**: Batch writes for high-throughput scenarios
3. **Snapshot Strategy**: Implement intelligent snapshot creation based on:
   - Number of events (e.g., every 100 events)
   - Time elapsed (e.g., daily snapshots)
   - Business significance (e.g., major state changes)
4. **Scaling**: Configure appropriate throughput and consider using on-demand capacity mode for unpredictable workloads
5. **Caching**: Cache frequently accessed aggregates and projections

## 7. References

- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [Event Sourcing Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)
- [CQRS Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)