# Event Store Implementation

## Overview

The Event Store is the backbone of our event sourcing architecture, providing persistent storage for all domain events in the Inventory Service. This document details the implementation strategy, technology selection, and operational aspects of the Event Store.

## Event Store Architecture

The Inventory Service uses a dual-storage approach for event persistence:

1. **Primary Storage**: DynamoDB for event data persistence
2. **Secondary Index**: ElasticSearch for advanced querying capabilities

### DynamoDB Table Structure

```
Table: inventory_events
- partitionKey: aggregateId (string) - ID of the aggregate (e.g., inventoryItemId)
- sortKey: sequenceNumber (number) - Ordered sequence number for the aggregate
- aggregateType: string - Type of aggregate (e.g., "INVENTORY_ITEM", "ALLOCATION")
- eventType: string - Type of event (e.g., "STOCK_LEVEL_CHANGED")
- eventData: JSON - Event payload
- metadata: JSON - Additional information (user, timestamp, correlation ID, etc.)
- timestamp: number - Time of event creation
- version: number - Schema version of the event
```

#### Global Secondary Indexes

1. **EventTypeIndex**

   - partitionKey: eventType
   - sortKey: timestamp
   - Allows querying for all events of a specific type

2. **AggregateTypeIndex**

   - partitionKey: aggregateType
   - sortKey: timestamp
   - Allows querying for all events of a specific aggregate type

3. **TimestampIndex**
   - partitionKey: timestamp (using a truncated date value)
   - sortKey: aggregateId
   - Allows time-based querying of events

## Write Operations

### Event Persistence Flow

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│   Command     │────▶│   Aggregate   │────▶│   Domain      │
│   Handler     │     │               │     │   Event       │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────┬───────┘
                                                    │
                                                    ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│ Event Bus     │◀────│  Event Store  │◀────│ Event Store   │
│ (RabbitMQ)    │     │ Repository    │     │ Transaction   │
│               │     │               │     │ Manager       │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Event Store Repository Implementation

```typescript
@Injectable()
export class EventStoreRepository {
  constructor(
    private readonly dynamoDBClient: DynamoDBClient,
    private readonly elasticsearchService: ElasticsearchService,
    private readonly eventBus: EventBus
  ) {}

  async saveEvent(event: DomainEvent): Promise<void> {
    const sequenceNumber = await this.getNextSequenceNumber(
      event.aggregateId,
      event.aggregateType
    );

    // Prepare DynamoDB item
    const item = {
      aggregateId: event.aggregateId,
      sequenceNumber,
      aggregateType: event.aggregateType,
      eventType: event.eventType,
      eventData: event.data,
      metadata: event.metadata,
      timestamp: event.timestamp.getTime(),
      version: event.version,
    };

    // Begin transaction
    const transactionItems = [
      {
        Put: {
          TableName: "inventory_events",
          Item: marshall(item),
          ConditionExpression:
            "attribute_not_exists(aggregateId) AND attribute_not_exists(sequenceNumber)",
        },
      },
    ];

    try {
      // Execute transaction
      await this.dynamoDBClient.send(
        new TransactWriteItemsCommand({
          TransactItems: transactionItems,
        })
      );

      // Index in ElasticSearch for advanced querying
      await this.elasticsearchService.index({
        index: "inventory-events",
        id: event.eventId,
        document: {
          ...item,
          eventData: JSON.stringify(event.data),
          metadata: JSON.stringify(event.metadata),
        },
      });

      // Publish event to event bus
      // This step typically involves reliably scheduling the event for publication
      // using the Transactional Outbox pattern (detailed in '05-event-publishing')
      // to ensure the event is sent to RabbitMQ if and only if the event store transaction commits.
      await this.eventBus.publish(event);

      this.logger.debug(`Event ${event.eventId} persisted successfully`);
    } catch (error) {
      this.logger.error(`Failed to persist event ${event.eventId}`, error);
      throw new EventPersistenceException(
        `Failed to persist event: ${error.message}`
      );
    }
  }

  private async getNextSequenceNumber(
    aggregateId: string,
    aggregateType: string
  ): Promise<number> {
    // Query for the highest sequence number for this aggregate
    const response = await this.dynamoDBClient.send(
      new QueryCommand({
        TableName: "inventory_events",
        KeyConditionExpression: "aggregateId = :aggregateId",
        ExpressionAttributeValues: marshall({
          ":aggregateId": aggregateId,
        }),
        ScanIndexForward: false, // descending order
        Limit: 1,
      })
    );

    // If no events exist for this aggregate, start with sequence number 1
    if (!response.Items || response.Items.length === 0) {
      return 1;
    }

    // Otherwise, increment the highest existing sequence number
    const highestSeqNum = unmarshall(response.Items[0]).sequenceNumber;
    return highestSeqNum + 1;
  }
}
```

### Optimistic Concurrency Control

To prevent concurrent modifications creating inconsistent states:

1. Each aggregate maintains a version counter
2. When saving events, the current version is checked
3. If the version doesn't match expected, a concurrency exception is thrown

```typescript
async saveEvents(aggregateId: string, events: DomainEvent[], expectedVersion: number): Promise<void> {
  // Get current version from event store
  const currentVersion = await this.getCurrentAggregateVersion(aggregateId);

  // Check for concurrent modification
  if (currentVersion !== expectedVersion) {
    throw new ConcurrencyException(
      `Aggregate ${aggregateId} has been modified concurrently. Expected version ${expectedVersion}, but got ${currentVersion}.`
    );
  }

  // Save events...
}
```

## Read Operations

### Event Retrieval by Aggregate

```typescript
async getEventsForAggregate(aggregateId: string): Promise<DomainEvent[]> {
  const response = await this.dynamoDBClient.send(
    new QueryCommand({
      TableName: 'inventory_events',
      KeyConditionExpression: 'aggregateId = :aggregateId',
      ExpressionAttributeValues: marshall({
        ':aggregateId': aggregateId,
      }),
      ScanIndexForward: true, // ascending order
    })
  );

  if (!response.Items || response.Items.length === 0) {
    return [];
  }

  return response.Items.map((item) => this.mapToDomainEvent(unmarshall(item)));
}
```

### Advanced Event Querying

For complex queries, the ElasticSearch index is used:

```typescript
async findEventsByType(eventType: string, fromTimestamp: number, limit: number): Promise<DomainEvent[]> {
  const response = await this.elasticsearchService.search({
    index: 'inventory-events',
    body: {
      query: {
        bool: {
          must: [
            { match: { eventType } },
            { range: { timestamp: { gte: fromTimestamp } } }
          ]
        }
      },
      sort: [{ timestamp: 'asc' }],
      size: limit
    }
  });

  return response.hits.hits.map(hit => this.mapEsHitToDomainEvent(hit));
}
```

## Streaming Events

For continuous event processing, the service implements an event streaming mechanism:

```typescript
async* streamEvents(fromTimestamp: number): AsyncGenerator<DomainEvent, void, undefined> {
  let lastEvaluatedKey: Record<string, any> | undefined;
  let lastTimestamp = fromTimestamp;

  do {
    const response = await this.dynamoDBClient.send(
      new QueryCommand({
        TableName: 'inventory_events',
        IndexName: 'TimestampIndex',
        KeyConditionExpression: 'truncatedDate = :date AND timestamp >= :timestamp',
        ExpressionAttributeValues: marshall({
          ':date': this.getTruncatedDate(new Date(lastTimestamp)),
          ':timestamp': lastTimestamp,
        }),
        ScanIndexForward: true,
        Limit: 100,
        ExclusiveStartKey: lastEvaluatedKey,
      })
    );

    if (response.Items && response.Items.length > 0) {
      for (const item of response.Items) {
        const event = this.mapToDomainEvent(unmarshall(item));
        lastTimestamp = event.timestamp.getTime();
        yield event;
      }
    }

    lastEvaluatedKey = response.LastEvaluatedKey;
  } while (lastEvaluatedKey);
}
```

## Performance Considerations

1. **Batch Operations**: Use batch operations for reading/writing multiple events
2. **Projection Caching**: Cache frequently accessed projection states
3. **Read Replica**: Use DynamoDB read replicas for heavy read workloads
4. **Throttling**: Implement backpressure mechanisms to handle traffic spikes

## Disaster Recovery

1. **Backup Strategy**:

   - Point-in-time recovery enabled on DynamoDB
   - Daily snapshots stored in S3 with 90-day retention

2. **Recovery Process**:
   - Restore from the latest backup
   - Replay missing events from event bus dead-letter queue
   - Verify integrity via aggregate version check

## Monitoring and Alerting

1. **Key Metrics**:

   - Event write latency
   - Event read latency
   - Failed event persistence count
   - DynamoDB throttling events

2. **Alerts**:
   - Alert on persistence failures exceeding threshold
   - Alert on read/write latency exceeding SLA
   - Alert on DynamoDB capacity utilization above 80%
