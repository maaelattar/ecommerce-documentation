# Snapshot Mechanism

## Overview

The snapshot mechanism is a performance optimization technique that stores the current state of an aggregate at a specific point in time. This reduces the need to replay all events from the beginning when reconstructing aggregate state, significantly improving read performance for aggregates with many events.

## Problem Statement

In event sourcing, as the number of events for an aggregate grows, the time to reconstruct the aggregate by replaying all events becomes increasingly expensive. The Inventory Service stores millions of events, making full event replay impractical for high-frequency operations.

## Snapshot Architecture

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│   Aggregate   │────▶│   Snapshot    │────▶│   Snapshot    │
│   Repository  │     │   Service     │     │   Store       │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
                                                    │
                                                    ▼
┌───────────────┐                          ┌───────────────┐
│               │                          │               │
│   Event Store │◀─────────────────────────│   Snapshot    │
│   Repository  │                          │   Strategy    │
│               │                          │               │
└───────────────┘                          └───────────────┘
```

## Snapshot Storage

Snapshots are stored in DynamoDB with a structure optimized for quick retrieval:

```
Table: inventory_snapshots
- partitionKey: aggregateId (string) - ID of the aggregate
- sortKey: version (number) - Version number of the snapshot
- aggregateType: string - Type of aggregate (e.g., "INVENTORY_ITEM")
- state: JSON - Serialized state of the aggregate
- lastEventSequence: number - Sequence number of the last event included in this snapshot
- timestamp: number - Time when snapshot was created
- metadata: JSON - Additional information (like who created it, etc.)
```

## Snapshot Service Implementation

The SnapshotService handles creation, retrieval, and management of snapshots:

```typescript
@Injectable()
export class SnapshotService {
  constructor(
    private readonly dynamoDBClient: DynamoDBClient,
    private readonly eventStoreRepository: EventStoreRepository,
    private readonly logger: Logger,
  ) {}

  // Create a snapshot for an aggregate
  async createSnapshot(aggregateId: string, aggregateType: string, state: any, lastEventSequence: number): Promise<void> {
    const timestamp = Date.now();
    const version = await this.getNextSnapshotVersion(aggregateId);
    
    const item = {
      aggregateId,
      version,
      aggregateType,
      state: JSON.stringify(state),
      lastEventSequence,
      timestamp,
      metadata: {
        createdBy: 'system',
        reason: 'scheduled',
      },
    };
    
    try {
      await this.dynamoDBClient.send(
        new PutItemCommand({
          TableName: 'inventory_snapshots',
          Item: marshall(item),
        })
      );
      
      this.logger.debug(`Created snapshot ${version} for ${aggregateType}:${aggregateId}`);
    } catch (error) {
      this.logger.error(`Failed to create snapshot for ${aggregateType}:${aggregateId}`, error);
      throw new SnapshotCreationException(`Failed to create snapshot: ${error.message}`);
    }
  }

  // Get the latest snapshot for an aggregate
  async getLatestSnapshot(aggregateId: string): Promise<Snapshot | null> {
    try {
      const response = await this.dynamoDBClient.send(
        new QueryCommand({
          TableName: 'inventory_snapshots',
          KeyConditionExpression: 'aggregateId = :aggregateId',
          ExpressionAttributeValues: marshall({
            ':aggregateId': aggregateId,
          }),
          ScanIndexForward: false, // descending order (newest first)
          Limit: 1,
        })
      );
      
      if (!response.Items || response.Items.length === 0) {
        return null;
      }
      
      const item = unmarshall(response.Items[0]);
      return {
        aggregateId: item.aggregateId,
        aggregateType: item.aggregateType,
        version: item.version,
        state: JSON.parse(item.state),
        lastEventSequence: item.lastEventSequence,
        timestamp: item.timestamp,
        metadata: item.metadata,
      };
    } catch (error) {
      this.logger.error(`Failed to retrieve snapshot for ${aggregateId}`, error);
      throw new SnapshotRetrievalException(`Failed to retrieve snapshot: ${error.message}`);
    }
  }

  // Get events that occurred after the snapshot
  async getEventsAfterSnapshot(aggregateId: string, lastEventSequence: number): Promise<DomainEvent[]> {
    return this.eventStoreRepository.getEventsForAggregate(
      aggregateId,
      {
        startSequence: lastEventSequence + 1,
      }
    );
  }

  // Determine if a snapshot should be created based on event count
  shouldCreateSnapshot(eventCount: number): boolean {
    // Create a snapshot every 100 events
    return eventCount % 100 === 0 && eventCount > 0;
  }

  private async getNextSnapshotVersion(aggregateId: string): Promise<number> {
    // Query for the highest version for this aggregate
    const response = await this.dynamoDBClient.send(
      new QueryCommand({
        TableName: 'inventory_snapshots',
        KeyConditionExpression: 'aggregateId = :aggregateId',
        ExpressionAttributeValues: marshall({
          ':aggregateId': aggregateId,
        }),
        ScanIndexForward: false, // descending order
        Limit: 1,
      })
    );

    // If no snapshots exist for this aggregate, start with version 1
    if (!response.Items || response.Items.length === 0) {
      return 1;
    }

    // Otherwise, increment the highest existing version
    const highestVersion = unmarshall(response.Items[0]).version;
    return highestVersion + 1;
  }
}
```

## Aggregate Repository with Snapshot Support

The AggregateRepository uses snapshots to optimize aggregate reconstruction:

```typescript
@Injectable()
export class AggregateRepository<T extends Aggregate> {
  constructor(
    private readonly eventStoreRepository: EventStoreRepository,
    private readonly snapshotService: SnapshotService,
    private readonly aggregateFactory: AggregateFactory<T>,
    private readonly logger: Logger,
  ) {}

  async getById(aggregateId: string): Promise<T> {
    // Try to get the latest snapshot
    const snapshot = await this.snapshotService.getLatestSnapshot(aggregateId);
    
    let aggregate: T;
    let lastSequence = 0;
    
    if (snapshot) {
      // Create aggregate from snapshot
      aggregate = this.aggregateFactory.createFromSnapshot(snapshot.state);
      lastSequence = snapshot.lastEventSequence;
      
      this.logger.debug(`Loaded ${aggregate.constructor.name}:${aggregateId} from snapshot version ${snapshot.version}`);
    } else {
      // No snapshot, create a new aggregate instance
      aggregate = this.aggregateFactory.create(aggregateId);
    }
    
    // Get events that occurred after the snapshot
    const events = await this.eventStoreRepository.getEventsForAggregate(
      aggregateId,
      { startSequence: lastSequence + 1 }
    );
    
    if (events.length > 0) {
      // Apply events to build current state
      events.forEach(event => aggregate.applyEvent(event));
      
      this.logger.debug(`Applied ${events.length} events to ${aggregate.constructor.name}:${aggregateId}`);
      
      // Check if we should create a new snapshot
      if (this.snapshotService.shouldCreateSnapshot(events.length)) {
        await this.createSnapshot(aggregate, events[events.length - 1].sequenceNumber);
      }
    }
    
    return aggregate;
  }

  async save(aggregate: T): Promise<void> {
    // Get uncommitted events from the aggregate
    const uncommittedEvents = aggregate.getUncommittedEvents();
    
    if (uncommittedEvents.length === 0) {
      return; // No changes to persist
    }
    
    // Save events to the event store
    await this.eventStoreRepository.saveEvents(
      aggregate.id,
      uncommittedEvents,
      aggregate.version
    );
    
    // Clear uncommitted events after successful save
    aggregate.clearUncommittedEvents();
    
    // Check if we need to create a snapshot
    const totalEvents = aggregate.version;
    if (this.snapshotService.shouldCreateSnapshot(totalEvents)) {
      await this.createSnapshot(aggregate, totalEvents);
    }
  }

  private async createSnapshot(aggregate: T, lastEventSequence: number): Promise<void> {
    try {
      await this.snapshotService.createSnapshot(
        aggregate.id,
        aggregate.constructor.name,
        aggregate.getStateForSnapshot(),
        lastEventSequence
      );
    } catch (error) {
      // Log but don't rethrow - snapshot creation is non-critical
      this.logger.warn(
        `Failed to create snapshot for ${aggregate.constructor.name}:${aggregate.id}`,
        error
      );
    }
  }
}
```

## Snapshot Strategies

Different aggregates may have different snapshotting needs. The service implements multiple strategies:

### 1. Event Count Based Strategy

```typescript
@Injectable()
export class EventCountSnapshotStrategy implements SnapshotStrategy {
  constructor(
    @Inject('SNAPSHOT_THRESHOLD') 
    private readonly threshold: number,
  ) {}

  shouldCreateSnapshot(aggregate: Aggregate, eventCount: number): boolean {
    return eventCount >= this.threshold;
  }
}
```

### 2. Time Based Strategy

```typescript
@Injectable()
export class TimeBasedSnapshotStrategy implements SnapshotStrategy {
  constructor(
    @Inject('SNAPSHOT_INTERVAL_HOURS') 
    private readonly intervalHours: number,
  ) {}

  shouldCreateSnapshot(aggregate: Aggregate, eventCount: number, lastSnapshotTime: number): boolean {
    const hoursSinceLastSnapshot = (Date.now() - lastSnapshotTime) / (1000 * 60 * 60);
    return hoursSinceLastSnapshot >= this.intervalHours;
  }
}
```

### 3. Hybrid Strategy

```typescript
@Injectable()
export class HybridSnapshotStrategy implements SnapshotStrategy {
  constructor(
    private readonly eventCountStrategy: EventCountSnapshotStrategy,
    private readonly timeBasedStrategy: TimeBasedSnapshotStrategy,
  ) {}

  shouldCreateSnapshot(aggregate: Aggregate, eventCount: number, lastSnapshotTime: number): boolean {
    return this.eventCountStrategy.shouldCreateSnapshot(aggregate, eventCount) || 
           this.timeBasedStrategy.shouldCreateSnapshot(aggregate, eventCount, lastSnapshotTime);
  }
}
```

## Snapshot Cleanup

To prevent unlimited snapshot growth, the service implements a cleanup policy:

```typescript
@Injectable()
export class SnapshotCleanupService {
  constructor(
    private readonly dynamoDBClient: DynamoDBClient,
    private readonly logger: Logger,
    @Inject('MAX_SNAPSHOTS_PER_AGGREGATE') 
    private readonly maxSnapshots: number,
  ) {}

  @Cron('0 0 * * *') // Run daily at midnight
  async cleanupSnapshots(): Promise<void> {
    this.logger.log('Starting snapshot cleanup job');
    
    try {
      // Get all unique aggregateIds
      const aggregateIds = await this.getAllAggregateIds();
      
      for (const aggregateId of aggregateIds) {
        await this.cleanupAggregateSnapshots(aggregateId);
      }
      
      this.logger.log(`Snapshot cleanup completed for ${aggregateIds.length} aggregates`);
    } catch (error) {
      this.logger.error('Error during snapshot cleanup', error);
    }
  }

  private async cleanupAggregateSnapshots(aggregateId: string): Promise<void> {
    // Get all snapshots for this aggregate, sorted by version (newest first)
    const snapshots = await this.getSnapshotsForAggregate(aggregateId);
    
    // Keep the newest 'maxSnapshots' snapshots, delete the rest
    if (snapshots.length > this.maxSnapshots) {
      const snapshotsToDelete = snapshots.slice(this.maxSnapshots);
      
      for (const snapshot of snapshotsToDelete) {
        await this.deleteSnapshot(aggregateId, snapshot.version);
      }
      
      this.logger.debug(
        `Deleted ${snapshotsToDelete.length} old snapshots for ${aggregateId}`
      );
    }
  }

  private async getSnapshotsForAggregate(aggregateId: string): Promise<any[]> {
    const response = await this.dynamoDBClient.send(
      new QueryCommand({
        TableName: 'inventory_snapshots',
        KeyConditionExpression: 'aggregateId = :aggregateId',
        ExpressionAttributeValues: marshall({
          ':aggregateId': aggregateId,
        }),
        ScanIndexForward: false, // descending order (newest first)
      })
    );
    
    return response.Items ? response.Items.map(item => unmarshall(item)) : [];
  }

  private async deleteSnapshot(aggregateId: string, version: number): Promise<void> {
    await this.dynamoDBClient.send(
      new DeleteItemCommand({
        TableName: 'inventory_snapshots',
        Key: marshall({
          aggregateId,
          version,
        }),
      })
    );
  }

  private async getAllAggregateIds(): Promise<string[]> {
    // Use a scan operation with projection to get distinct aggregateIds
    // Note: For production, this would need pagination for large datasets
    const response = await this.dynamoDBClient.send(
      new ScanCommand({
        TableName: 'inventory_snapshots',
        ProjectionExpression: 'aggregateId',
      })
    );
    
    if (!response.Items || response.Items.length === 0) {
      return [];
    }
    
    // Extract unique aggregateIds
    const uniqueIds = new Set<string>();
    response.Items.forEach(item => {
      const unmarshalled = unmarshall(item);
      uniqueIds.add(unmarshalled.aggregateId);
    });
    
    return Array.from(uniqueIds);
  }
}
```

## Snapshot Management API

```typescript
@Controller('admin/snapshots')
@UseGuards(AdminAuthGuard)
export class SnapshotController {
  constructor(
    private readonly snapshotService: SnapshotService,
    private readonly snapshotCleanupService: SnapshotCleanupService,
    private readonly logger: Logger,
  ) {}

  @Post('create/:aggregateType/:aggregateId')
  async createSnapshot(
    @Param('aggregateType') aggregateType: string,
    @Param('aggregateId') aggregateId: string,
  ): Promise<void> {
    this.logger.log(
      `Manual snapshot creation requested for ${aggregateType}:${aggregateId}`,
    );
    
    // Get the aggregate
    const aggregateRepository = this.getRepositoryForType(aggregateType);
    const aggregate = await aggregateRepository.getById(aggregateId);
    
    // Create snapshot
    await this.snapshotService.createSnapshot(
      aggregateId,
      aggregateType,
      aggregate.getStateForSnapshot(),
      aggregate.version
    );
  }

  @Get(':aggregateId')
  async getSnapshots(
    @Param('aggregateId') aggregateId: string,
  ): Promise<any[]> {
    return this.snapshotService.getSnapshotsForAggregate(aggregateId);
  }

  @Post('cleanup')
  async triggerCleanup(): Promise<{ message: string }> {
    this.logger.log('Manual snapshot cleanup triggered');
    
    await this.snapshotCleanupService.cleanupSnapshots();
    
    return { message: 'Snapshot cleanup completed successfully' };
  }

  private getRepositoryForType(aggregateType: string): any {
    // Resolve the appropriate repository based on aggregate type
    switch (aggregateType) {
      case 'INVENTORY_ITEM':
        return this.inventoryItemRepository;
      case 'WAREHOUSE':
        return this.warehouseRepository;
      // Add other aggregate types as needed
      default:
        throw new Error(`Unsupported aggregate type: ${aggregateType}`);
    }
  }
}
```

## Performance Considerations

1. **Serialization**: Use efficient serialization format (JSON or binary)
2. **Compression**: Compress large snapshot data to reduce storage costs
3. **Indexing**: Maintain appropriate indexes on snapshot table for query performance
4. **Lazy Loading**: Load aggregate state from snapshots only when needed
5. **Asynchronous Creation**: Create snapshots asynchronously to avoid blocking operations

## Security Considerations

1. **Encryption**: Encrypt snapshot data at rest using AWS KMS
2. **Access Control**: Restrict snapshot management APIs to admin users only
3. **Audit Trail**: Log all snapshot-related operations for audit purposes
4. **Validation**: Validate snapshot integrity before applying