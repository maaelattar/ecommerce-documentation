# Event Store Implementation for Order Service

## Overview

The Event Store is the foundational component of our event sourcing architecture for the Order Service. It provides persistent storage for all order domain events, ensuring an immutable record of all changes throughout the order lifecycle. This document details the implementation strategy, technology selection, and operational aspects of the Order Event Store.

## Technology Selection

The Order Service uses Amazon DynamoDB as the primary event store with the following benefits:

1. **Scalability**: Handles high-volume event storage required for orders
2. **Performance**: Low-latency reads and writes for efficient order processing
3. **Reliability**: Provides 99.999% availability for critical order data
4. **Cost-effectiveness**: Pay-per-request pricing model optimizes costs
5. **AWS Integration**: Seamless integration with other AWS services

## Event Store Architecture

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│   Order       │────▶│  Event Store  │────▶│   Amazon SNS  │
│   Service     │     │  (DynamoDB)   │     │   Topic       │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────┬───────┘
                                                    │
                                                    ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Analytics    │     │ Notification  │     │  Other        │
│  Service      │◀────│ Service       │◀────│  Services     │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
```

## DynamoDB Table Design

### Main Events Table

```
Table: order_events
- partitionKey: orderId (string) - ID of the order
- sortKey: sequenceNumber (number) - Ordered sequence for the events
- eventType: string - Type of event (e.g., "ORDER_CREATED")
- eventData: string (JSON) - Event payload
- metadata: string (JSON) - Additional information (user, timestamp, etc.)
- timestamp: number - Time of event creation (epoch milliseconds)
- version: number - Schema version of the event
- correlationId: string - ID for tracking related operations
```

### Global Secondary Indexes

1. **EventTypeIndex**
   - partitionKey: eventType
   - sortKey: timestamp
   - Allows querying for all events of a specific type

2. **TimestampIndex**
   - partitionKey: timestamp (truncated to day)
   - sortKey: orderId
   - Allows time-based querying of events

3. **CorrelationIdIndex**
   - partitionKey: correlationId
   - sortKey: timestamp
   - Allows tracking of related events across services

## Write Operations

### Event Persistence Flow

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│   Command     │────▶│    Order      │────▶│   Domain      │
│   Handler     │     │   Aggregate   │     │   Event       │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────┬───────┘
                                                    │
                                                    ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│ Event Bus     │◀────│  Event Store  │◀────│ Event Store   │
│ (SNS)         │     │ Repository    │     │ Transaction   │
│               │     │               │     │ Manager       │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Event Store Repository Implementation

```typescript
@Injectable()
export class OrderEventStoreRepository {
  constructor(
    private readonly dynamoDBClient: DynamoDBClient,
    private readonly snsClient: SNSClient,
    private readonly configService: ConfigService,
    private readonly logger: Logger,
  ) {}

  async saveEvent(event: OrderDomainEvent): Promise<void> {
    const sequenceNumber = await this.getNextSequenceNumber(event.aggregateId);

    // Prepare DynamoDB item
    const item = {
      orderId: event.aggregateId,
      sequenceNumber,
      eventType: event.eventType,
      eventData: JSON.stringify(event.data),
      metadata: JSON.stringify(event.metadata),
      timestamp: event.timestamp.getTime(),
      version: event.version,
      correlationId: event.metadata.correlationId,
    };

    // Begin transaction
    const transactionItems = [
      {
        Put: {
          TableName: 'order_events',
          Item: marshall(item),
          // Ensure no duplicate sequence numbers
          ConditionExpression: 'attribute_not_exists(orderId) AND attribute_not_exists(sequenceNumber)',
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

      // Publish event to SNS
      await this.publishEventToSNS(event);

      this.logger.debug(`Event ${event.eventId} persisted successfully for order ${event.aggregateId}`);
    } catch (error) {
      this.logger.error(`Failed to persist event ${event.eventId} for order ${event.aggregateId}`, error);
      throw new EventPersistenceException(
        `Failed to persist event: ${error.message}`
      );
    }
  }

  private async getNextSequenceNumber(orderId: string): Promise<number> {
    // Query for the highest sequence number for this order
    const response = await this.dynamoDBClient.send(
      new QueryCommand({
        TableName: 'order_events',
        KeyConditionExpression: 'orderId = :orderId',
        ExpressionAttributeValues: marshall({
          ':orderId': orderId,
        }),
        ScanIndexForward: false, // descending order
        Limit: 1,
      })
    );

    // If no events exist for this order, start with sequence number 1
    if (!response.Items || response.Items.length === 0) {
      return 1;
    }

    // Otherwise, increment the highest existing sequence number
    const highestSeqNum = unmarshall(response.Items[0]).sequenceNumber;
    return highestSeqNum + 1;
  }

  private async publishEventToSNS(event: OrderDomainEvent): Promise<void> {
    const topicArn = this.configService.get<string>('SNS_ORDER_EVENTS_TOPIC_ARN');
    
    try {
      await this.snsClient.send(
        new PublishCommand({
          TopicArn: topicArn,
          Message: JSON.stringify(event),
          MessageAttributes: {
            eventType: {
              DataType: 'String',
              StringValue: event.eventType,
            },
            aggregateId: {
              DataType: 'String',
              StringValue: event.aggregateId,
            },
          },
        })
      );
    } catch (error) {
      this.logger.error(`Failed to publish event to SNS: ${error.message}`, error);
      // We don't throw here to avoid rollback - the event is already stored in DynamoDB
      // An async process can periodically check for unpublished events and retry
    }
  }
}
```

### Optimistic Concurrency Control

To prevent concurrent modifications causing inconsistent order states:

```typescript
async saveEvents(orderId: string, events: OrderDomainEvent[], expectedVersion: number): Promise<void> {
  // Get current version from event store
  const currentVersion = await this.getCurrentOrderVersion(orderId);

  // Check for concurrent modification
  if (currentVersion !== expectedVersion) {
    throw new ConcurrencyException(
      `Order ${orderId} has been modified concurrently. Expected version ${expectedVersion}, but got ${currentVersion}.`
    );
  }

  // Save events in sequence
  for (const event of events) {
    await this.saveEvent(event);
  }
}
```

## Read Operations

### Event Retrieval by Order ID

```typescript
async getEventsForOrder(orderId: string, options?: EventRetrievalOptions): Promise<OrderDomainEvent[]> {
  const params: QueryCommandInput = {
    TableName: 'order_events',
    KeyConditionExpression: 'orderId = :orderId',
    ExpressionAttributeValues: marshall({
      ':orderId': orderId,
    }),
    ScanIndexForward: true, // ascending order by sequence
  };

  // Add optional filtering
  if (options?.startSequence) {
    params.KeyConditionExpression += ' AND sequenceNumber >= :startSeq';
    params.ExpressionAttributeValues = marshall({
      ...unmarshall(params.ExpressionAttributeValues),
      ':startSeq': options.startSequence,
    });
  }

  if (options?.endSequence) {
    params.KeyConditionExpression += ' AND sequenceNumber <= :endSeq';
    params.ExpressionAttributeValues = marshall({
      ...unmarshall(params.ExpressionAttributeValues),
      ':endSeq': options.endSequence,
    });
  }

  if (options?.eventTypes && options.eventTypes.length > 0) {
    params.FilterExpression = 'eventType IN (:eventTypes)';
    params.ExpressionAttributeValues = marshall({
      ...unmarshall(params.ExpressionAttributeValues),
      ':eventTypes': options.eventTypes,
    });
  }

  const response = await this.dynamoDBClient.send(new QueryCommand(params));

  if (!response.Items || response.Items.length === 0) {
    return [];
  }

  return response.Items.map((item) => this.mapToDomainEvent(unmarshall(item)));
}
```

### Event Retrieval by Event Type

```typescript
async getEventsByType(eventType: string, options?: EventTypeQueryOptions): Promise<OrderDomainEvent[]> {
  const params: QueryCommandInput = {
    TableName: 'order_events',
    IndexName: 'EventTypeIndex',
    KeyConditionExpression: 'eventType = :eventType',
    ExpressionAttributeValues: marshall({
      ':eventType': eventType,
    }),
    ScanIndexForward: options?.ascending ?? true,
  };

  if (options?.startTime && options?.endTime) {
    params.KeyConditionExpression += ' AND timestamp BETWEEN :startTime AND :endTime';
    params.ExpressionAttributeValues = marshall({
      ...unmarshall(params.ExpressionAttributeValues),
      ':startTime': options.startTime.getTime(),
      ':endTime': options.endTime.getTime(),
    });
  } else if (options?.startTime) {
    params.KeyConditionExpression += ' AND timestamp >= :startTime';
    params.ExpressionAttributeValues = marshall({
      ...unmarshall(params.ExpressionAttributeValues),
      ':startTime': options.startTime.getTime(),
    });
  } else if (options?.endTime) {
    params.KeyConditionExpression += ' AND timestamp <= :endTime';
    params.ExpressionAttributeValues = marshall({
      ...unmarshall(params.ExpressionAttributeValues),
      ':endTime': options.endTime.getTime(),
    });
  }

  if (options?.limit) {
    params.Limit = options.limit;
  }

  const response = await this.dynamoDBClient.send(new QueryCommand(params));

  if (!response.Items || response.Items.length === 0) {
    return [];
  }

  return response.Items.map((item) => this.mapToDomainEvent(unmarshall(item)));
}
```

## Streaming Events

For continuous event processing, such as analytics or synchronization jobs:

```typescript
async* streamOrderEvents(options?: EventStreamOptions): AsyncGenerator<OrderDomainEvent, void, undefined> {
  let lastEvaluatedKey: Record<string, any> | undefined;
  let count = 0;
  
  do {
    const params: QueryCommandInput = {
      TableName: 'order_events',
      IndexName: 'TimestampIndex',
      KeyConditionExpression: 'dayTimestamp = :day',
      ExpressionAttributeValues: marshall({
        ':day': this.getDayTimestamp(options?.startTime || new Date()),
      }),
      ScanIndexForward: true,
      Limit: options?.batchSize || 100,
      ExclusiveStartKey: lastEvaluatedKey,
    };

    if (options?.startTime) {
      params.KeyConditionExpression += ' AND timestamp >= :startTime';
      params.ExpressionAttributeValues = marshall({
        ...unmarshall(params.ExpressionAttributeValues),
        ':startTime': options.startTime.getTime(),
      });
    }

    if (options?.eventTypes && options.eventTypes.length > 0) {
      params.FilterExpression = 'eventType IN (:eventTypes)';
      params.ExpressionAttributeValues = marshall({
        ...unmarshall(params.ExpressionAttributeValues),
        ':eventTypes': options.eventTypes,
      });
    }

    const response = await this.dynamoDBClient.send(new QueryCommand(params));

    if (response.Items && response.Items.length > 0) {
      for (const item of response.Items) {
        const event = this.mapToDomainEvent(unmarshall(item));
        yield event;
        
        count++;
        if (options?.maxEvents && count >= options.maxEvents) {
          return;
        }
      }
    }

    lastEvaluatedKey = response.LastEvaluatedKey;
  } while (lastEvaluatedKey);
}

private getDayTimestamp(date: Date): string {
  return date.toISOString().substring(0, 10); // YYYY-MM-DD format
}
```

## Performance Optimization

1. **Batch Operations**: Use batch operations for reading/writing multiple events
2. **Caching**: Cache frequently accessed orders for read operations
3. **Read Replicas**: Use DynamoDB global tables for multi-region access
4. **Auto-Scaling**: Configure DynamoDB auto-scaling for variable workloads
5. **On-Demand Capacity**: Use on-demand capacity for unpredictable spikes

## Disaster Recovery

### Backup Strategy

1. **Point-in-Time Recovery**:
   - Enable point-in-time recovery on the order_events table
   - Allows restoration to any point within the last 35 days

2. **Scheduled Backups**:
   - Daily backups with 30-day retention
   - Weekly backups with 90-day retention
   - Monthly backups with 1-year retention

3. **Cross-Region Replication**:
   - Replicate order events to a secondary region
   - Enable automatic failover in case of regional outage

### Recovery Process

1. **Table Restoration**:
   - Restore the order_events table from the latest backup or point-in-time recovery
   - Validate data integrity

2. **Order State Rebuilding**:
   - Rebuild order projections from events
   - Validate order states against business rules

3. **Integration Recovery**:
   - Re-publish critical events to ensure downstream systems are synchronized
   - Validate integration points

## Monitoring and Alerting

### Key Metrics

1. **Event Write Metrics**:
   - Event persistence latency (p50, p95, p99)
   - Failed event persistence count
   - Write throughput (events per second)

2. **Event Read Metrics**:
   - Event retrieval latency (p50, p95, p99)
   - Read throughput (events per second)

3. **DynamoDB Metrics**:
   - Consumed read/write capacity units
   - Throttled requests
   - Table size (number of items and bytes)

4. **SNS Metrics**:
   - Publication success rate
   - Delivery to subscription success rate
   - Message age