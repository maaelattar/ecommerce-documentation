# Snapshot Mechanism for Order Service

## Overview

The snapshot mechanism in the Order Service is a critical performance optimization that stores the current state of an order at specific points in time. This reduces the need to replay all events from the beginning when reconstructing order state, which is especially important for orders with numerous events over their lifecycle.

## Problem Statement

Orders in e-commerce systems often go through many state changes, each represented by an event. Active customers may have orders with dozens of events (creation, payment, status updates, shipping updates, etc.). Reconstructing these orders by replaying all events becomes increasingly expensive as the number of events grows, leading to performance issues during order lookups and processing.

## Snapshot Architecture

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│   Order       │────▶│   Snapshot    │────▶│   Snapshot    │
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

Snapshots are stored in DynamoDB with the following structure:

```
Table: order_snapshots
- partitionKey: orderId (string) - ID of the order
- sortKey: version (number) - Version number of the snapshot
- state: string (JSON) - Serialized state of the order
- lastEventSequence: number - Sequence number of the last event included
- timestamp: number - Time when snapshot was created
- metadata: string (JSON) - Additional information
```

## Snapshot Service Implementation

```typescript
@Injectable()
export class OrderSnapshotService {
  constructor(
    private readonly dynamoDBClient: DynamoDBClient,
    private readonly orderEventStoreRepository: OrderEventStoreRepository,
    private readonly snapshotStrategyProvider: SnapshotStrategyProvider,
    private readonly config: ConfigService,
    private readonly logger: Logger,
  ) {}

  async createSnapshot(order: Order, lastEventSequence: number): Promise<void> {
    const timestamp = Date.now();
    const version = await this.getNextSnapshotVersion(order.id);
    
    // Serialize order state
    const orderState = this.serializeOrderState(order);
    
    const item = {
      orderId: order.id,
      version,
      state: orderState,
      lastEventSequence,
      timestamp,
      metadata: {
        createdBy: 'system',
        reason: 'threshold-reached',
      },
    };
    
    try {
      await this.dynamoDBClient.send(
        new PutItemCommand({
          TableName: 'order_snapshots',
          Item: marshall(item),
        })
      );
      
      this.logger.debug(`Created snapshot ${version} for order ${order.id}`);
    } catch (error) {
      this.logger.error(`Failed to create snapshot for order ${order.id}`, error);
      throw new SnapshotCreationException(`Failed to create snapshot: ${error.message}`);
    }
  }

  async getLatestSnapshot(orderId: string): Promise<OrderSnapshot | null> {
    try {
      const response = await this.dynamoDBClient.send(
        new QueryCommand({
          TableName: 'order_snapshots',
          KeyConditionExpression: 'orderId = :orderId',
          ExpressionAttributeValues: marshall({
            ':orderId': orderId,
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
        orderId: item.orderId,
        version: item.version,
        state: JSON.parse(item.state),
        lastEventSequence: item.lastEventSequence,
        timestamp: item.timestamp,
        metadata: item.metadata,
      };
    } catch (error) {
      this.logger.error(`Failed to retrieve snapshot for order ${orderId}`, error);
      throw new SnapshotRetrievalException(`Failed to retrieve snapshot: ${error.message}`);
    }
  }

  async getEventsAfterSnapshot(orderId: string, lastEventSequence: number): Promise<OrderDomainEvent[]> {
    return this.orderEventStoreRepository.getEventsForOrder(
      orderId,
      {
        startSequence: lastEventSequence + 1,
      }
    );
  }

  shouldCreateSnapshot(order: Order, eventCount: number): boolean {
    // Use the appropriate strategy for the order
    const strategy = this.snapshotStrategyProvider.getStrategyForOrder(order);
    return strategy.shouldCreateSnapshot(order, eventCount);
  }

  private serializeOrderState(order: Order): string {
    // Remove non-serializable properties and methods
    const orderClone = { ...order };
    delete orderClone._events;
    delete orderClone._uncommittedEvents;
    
    return JSON.stringify(orderClone);
  }

  private async getNextSnapshotVersion(orderId: string): Promise<number> {
    const response = await this.dynamoDBClient.send(
      new QueryCommand({
        TableName: 'order_snapshots',
        KeyConditionExpression: 'orderId = :orderId',
        ExpressionAttributeValues: marshall({
          ':orderId': orderId,
        }),
        ScanIndexForward: false, // descending order
        Limit: 1,
      })
    );

    if (!response.Items || response.Items.length === 0) {
      return 1;
    }

    const highestVersion = unmarshall(response.Items[0]).version;
    return highestVersion + 1;
  }
}
```

## Order Repository with Snapshot Support

The Order Repository uses snapshots to optimize order reconstruction:

```typescript
@Injectable()
export class OrderRepository {
  constructor(
    private readonly orderEventStoreRepository: OrderEventStoreRepository,
    private readonly snapshotService: OrderSnapshotService,
    private readonly orderFactory: OrderFactory,
    private readonly logger: Logger,
  ) {}

  async getOrderById(orderId: string, options?: { skipEvents?: boolean }): Promise<Order | null> {
    // Try to get the latest snapshot
    const snapshot = await this.snapshotService.getLatestSnapshot(orderId);
    
    let order: Order;
    let lastSequence = 0;
    
    if (snapshot) {
      // Create order from snapshot
      order = this.orderFactory.createFromState(snapshot.state);
      lastSequence = snapshot.lastEventSequence;
      
      this.logger.debug(`Loaded order ${orderId} from snapshot version ${snapshot.version}`);
    } else {
      // Check if order exists in event store
      const orderExists = await this.orderEventStoreRepository.orderExists(orderId);
      
      if (!orderExists) {
        return null;
      }
      
      // Create a new empty order
      order = this.orderFactory.createEmpty(orderId);
    }
    
    // If skipEvents is true, return the order from snapshot without applying additional events
    if (options?.skipEvents) {
      return order;
    }
    
    // Get events that occurred after the snapshot
    const events = await this.orderEventStoreRepository.getEventsForOrder(
      orderId,
      { startSequence: lastSequence + 1 }
    );
    
    if (events.length > 0) {
      // Apply events to build current state
      events.forEach(event => order.applyEvent(event));
      
      this.logger.debug(`Applied ${events.length} events to order ${orderId}`);
      
      // Check if we should create a new snapshot
      const totalEvents = lastSequence + events.length;
      if (this.snapshotService.shouldCreateSnapshot(order, totalEvents)) {
        await this.createSnapshot(order, totalEvents);
      }
    }
    
    return order;
  }

  async save(order: Order): Promise<void> {
    // Get uncommitted events from the order
    const uncommittedEvents = order.getUncommittedEvents();
    
    if (uncommittedEvents.length === 0) {
      return; // No changes to persist
    }
    
    // Save events to the event store
    await this.orderEventStoreRepository.saveEvents(
      order.id,
      uncommittedEvents,
      order.version
    );
    
    // Clear uncommitted events after successful save
    order.clearUncommittedEvents();
    
    // Check if we need to create a snapshot
    const eventCount = await this.orderEventStoreRepository.getEventCount(order.id);
    if (this.snapshotService.shouldCreateSnapshot(order, eventCount)) {
      await this.createSnapshot(order, eventCount);
    }
  }

  private async createSnapshot(order: Order, lastEventSequence: number): Promise<void> {
    try {
      await this.snapshotService.createSnapshot(order, lastEventSequence);
    } catch (error) {
      // Log but don't rethrow - snapshot creation is non-critical
      this.logger.warn(
        `Failed to create snapshot for order ${order.id}`,
        error
      );
    }
  }
}
```

## Snapshot Strategies

Different orders may have different snapshotting needs based on order complexity, frequency of access, and other factors. The service implements multiple strategies to address these varying needs.

### Strategy Provider

```typescript
@Injectable()
export class SnapshotStrategyProvider {
  constructor(
    private readonly eventCountStrategy: EventCountSnapshotStrategy,
    private readonly timeBasedStrategy: TimeBasedSnapshotStrategy,
    private readonly hybridStrategy: HybridSnapshotStrategy,
    private readonly configService: ConfigService,
  ) {}

  getStrategyForOrder(order: Order): SnapshotStrategy {
    const defaultStrategy = this.configService.get<string>('DEFAULT_SNAPSHOT_STRATEGY');
    
    // Apply special rules based on order characteristics
    
    // Rule 1: Large orders (many line items) get hybrid strategy
    if (order.items.length > 10) {
      return this.hybridStrategy;
    }
    
    // Rule 2: Orders with high value get more frequent snapshots
    if (order.total > 1000) {
      return this.eventCountStrategy;
    }
    
    // Default based on configuration
    switch (defaultStrategy) {
      case 'EVENT_COUNT':
        return this.eventCountStrategy;
      case 'TIME_BASED':
        return this.timeBasedStrategy;
      case 'HYBRID':
        return this.hybridStrategy;
      default:
        return this.eventCountStrategy;
    }
  }
}
```

### Event Count Based Strategy

```typescript
@Injectable()
export class EventCountSnapshotStrategy implements SnapshotStrategy {
  constructor(
    private readonly configService: ConfigService,
  ) {}

  shouldCreateSnapshot(order: Order, eventCount: number): boolean {
    const threshold = this.configService.get<number>('EVENT_COUNT_SNAPSHOT_THRESHOLD') || 10;
    return eventCount % threshold === 0;
  }
}
```

### Time Based Strategy

```typescript
@Injectable()
export class TimeBasedSnapshotStrategy implements SnapshotStrategy {
  constructor(
    private readonly configService: ConfigService,
  ) {}

  shouldCreateSnapshot(order: Order, eventCount: number, lastSnapshotTime?: number): boolean {
    // If no previous snapshot, use event count fallback
    if (!lastSnapshotTime) {
      return eventCount >= 5;
    }
    
    const intervalHours = this.configService.get<number>('TIME_BASED_SNAPSHOT_INTERVAL_HOURS') || 24;
    const hoursSinceLastSnapshot = (Date.now() - lastSnapshotTime) / (1000 * 60 * 60);
    
    return hoursSinceLastSnapshot >= intervalHours;
  }
}
```

### Hybrid Strategy

```typescript
@Injectable()
export class HybridSnapshotStrategy implements SnapshotStrategy {
  constructor(
    private readonly eventCountStrategy: EventCountSnapshotStrategy,
    private readonly timeBasedStrategy: TimeBasedSnapshotStrategy,
  ) {}

  shouldCreateSnapshot(order: Order, eventCount: number, lastSnapshotTime?: number): boolean {
    return this.eventCountStrategy.shouldCreateSnapshot(order, eventCount) || 
           this.timeBasedStrategy.shouldCreateSnapshot(order, eventCount, lastSnapshotTime);
  }
}
```

## Snapshot Cleanup

To prevent unlimited growth of snapshots, the service implements a cleanup policy:

```typescript
@Injectable()
export class SnapshotCleanupService {
  constructor(
    private readonly dynamoDBClient: DynamoDBClient,
    private readonly configService: ConfigService,
    private readonly logger: Logger,
  ) {}

  @Cron('0 0 * * *') // Run daily at midnight
  async cleanupSnapshots(): Promise<void> {
    this.logger.log('Starting order snapshot cleanup job');
    
    const maxSnapshotsPerOrder = this.configService.get<number>('MAX_SNAPSHOTS_PER_ORDER') || 3;
    const maxSnapshotAge = this.configService.get<number>('MAX_SNAPSHOT_AGE_DAYS') || 90;
    
    try {
      // Get all unique orderIds with snapshots
      const orderIds = await this.getAllOrderIdsWithSnapshots();
      
      for (const orderId of orderIds) {
        await this.cleanupOrderSnapshots(orderId, maxSnapshotsPerOrder, maxSnapshotAge);
      }
      
      this.logger.log(`Snapshot cleanup completed for ${orderIds.length} orders`);
    } catch (error) {
      this.logger.error('Error during snapshot cleanup', error);
    }
  }

  private async cleanupOrderSnapshots(
    orderId: string, 
    maxSnapshots: number, 
    maxAgeDays: number
  ): Promise<void> {
    // Get all snapshots for this order, sorted by version (newest first)
    const snapshots = await this.getSnapshotsForOrder(orderId);
    
    // Keep track of which snapshots to delete
    const snapshotsToDelete: any[] = [];
    
    // Keep the newest maxSnapshots snapshots
    if (snapshots.length > maxSnapshots) {
      snapshotsToDelete.push(...snapshots.slice(maxSnapshots));
    }
    
    // Also delete snapshots older than maxAgeDays
    const cutoffTime = Date.now() - (maxAgeDays * 24 * 60 * 60 * 1000);
    const oldSnapshots = snapshots.filter(snapshot => snapshot.timestamp < cutoffTime);
    
    // Add old snapshots to delete list, avoiding duplicates
    for (const snapshot of oldSnapshots) {
      if (!snapshotsToDelete.some(s => s.version === snapshot.version)) {
        snapshotsToDelete.push(snapshot);
      }
    }
    
    // Delete the snapshots
    for (const snapshot of snapshotsToDelete) {
      await this.deleteSnapshot(orderId, snapshot.version);
    }
    
    if (snapshotsToDelete.length > 0) {
      this.logger.debug(
        `Deleted ${snapshotsToDelete.length} old snapshots for order ${orderId}`
      );
    }
  }

  private async getSnapshotsForOrder(orderId: string): Promise<any[]> {
    const response = await this.dynamoDBClient.send(
      new QueryCommand({
        TableName: 'order_snapshots',
        KeyConditionExpression: 'orderId = :orderId',
        ExpressionAttributeValues: marshall({
          ':orderId': orderId,
        }),
        ScanIndexForward: false, // descending order (newest first)
      })
    );
    
    return response.Items ? response.Items.map(item => unmarshall(item)) : [];
  }

  private async deleteSnapshot(orderId: string, version: number): Promise<void> {
    await this.dynamoDBClient.send(
      new DeleteItemCommand({
        TableName: 'order_snapshots',
        Key: marshall({
          orderId,
          version,
        }),
      })
    );
  }

  private async getAllOrderIdsWithSnapshots(): Promise<string[]> {
    // Use scan with pagination to get all order IDs
    const orderIds = new Set<string>();
    let lastEvaluatedKey: Record<string, any> | undefined;
    
    do {
      const response = await this.dynamoDBClient.send(
        new ScanCommand({
          TableName: 'order_snapshots',
          ProjectionExpression: 'orderId',
          ExclusiveStartKey: lastEvaluatedKey,
        })
      );
      
      if (response.Items) {
        for (const item of response.Items) {
          const { orderId } = unmarshall(item);
          orderIds.add(orderId);
        }
      }
      
      lastEvaluatedKey = response.LastEvaluatedKey;
    } while (lastEvaluatedKey);
    
    return Array.from(orderIds);
  }
}
```

## Snapshot Management API

An administrative API is provided for managing snapshots:

```typescript
@Controller('admin/order-snapshots')
@UseGuards(AdminAuthGuard)
export class OrderSnapshotController {
  constructor(
    private readonly orderSnapshotService: OrderSnapshotService,
    private readonly orderRepository: OrderRepository,
    private readonly snapshotCleanupService: SnapshotCleanupService,
    private readonly logger: Logger,
  ) {}

  @Post('create/:orderId')
  async createSnapshot(
    @Param('orderId') orderId: string,
  ): Promise<{ message: string }> {
    this.logger.log(`Manual snapshot creation requested for order ${orderId}`);
    
    const order = await this.orderRepository.getOrderById(orderId);
    if (!order) {
      throw new NotFoundException(`Order ${orderId} not found`);
    }
    
    const eventCount = await this.orderEventStoreRepository.getEventCount(orderId);
    await this.orderSnapshotService.createSnapshot(order, eventCount);
    
    return { message: `Snapshot created successfully for order ${orderId}` };
  }

  @Get(':orderId')
  async getSnapshots(
    @Param('orderId') orderId: string,
  ): Promise<any[]> {
    return this.orderSnapshotService.getSnapshotsForOrder(orderId);
  }

  @Delete(':orderId/:version')
  async deleteSnapshot(
    @Param('orderId') orderId: string,
    @Param('version') version: number,
  ): Promise<{ message: string }> {
    await this.orderSnapshotService.deleteSnapshot(orderId, version);
    return { message: `Snapshot ${version} deleted for order ${orderId}` };
  }

  @Post('cleanup')
  async triggerCleanup(): Promise<{ message: string }> {
    this.logger.log('Manual snapshot cleanup triggered');
    
    await this.snapshotCleanupService.cleanupSnapshots();
    
    return { message: 'Snapshot cleanup completed successfully' };
  }
}
```

## Performance Benefits

The snapshot mechanism provides significant performance improvements:

1. **Reduced Event Replay**: Loading an order requires replaying only new events since the last snapshot
2. **Faster Order Lookups**: Critical for customer-facing operations like order status checks
3. **Reduced Database Load**: Less strain on the event store for frequently accessed orders
4. **Scalability**: Enables the system to handle orders with hundreds of events efficiently

## Memory Considerations

When working with snapshots, memory usage is an important consideration:

1. **Serialization Format**: JSON is used for simplicity but can be replaced with more efficient formats
2. **Compression**: Large order snapshots can be compressed to reduce storage costs
3. **Selective State**: Only essential state is included in snapshots, excluding derivable data

## Security Considerations

1. **Encryption**: Snapshot data is encrypted at rest using AWS KMS
2. **Access Control**: Management APIs are restricted to admin users only
3. **Audit Logging**: All snapshot operations are logged for audit purposes