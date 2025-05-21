# Event Replay Functionality for Order Service

## Overview

Event replay is a core capability of the Order Service's event sourcing architecture. It allows for rebuilding order state, debugging issues, recovering from failures, and testing new event handlers against historical data. This document details the design and implementation of event replay functionality in the Order Service.

## Use Cases for Event Replay

1. **Order State Reconstruction**: Rebuild the state of orders from their event history
2. **Projection Rebuilding**: Recreate read models when their structure or logic changes
3. **System Recovery**: Recover from data corruption or system failures
4. **Debugging**: Analyze order issues by replaying events to understand what happened
5. **Testing**: Test new features or event handlers against real historical order data
6. **Auditing**: Reproduce the exact state of orders at specific points in time for compliance

## Architecture

The event replay system follows a modular architecture that separates concerns:

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│   Replay      │────▶│  Event Store  │────▶│  Event Stream │
│   Controller  │     │  Repository   │     │  Processor    │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────┬───────┘
                                                    │
                                                    ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│   Order       │◀────│  Event        │◀────│  Event        │
│   Aggregate   │     │  Handler      │     │  Router       │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
```

## Implementation

### Replay Controller

The `OrderReplayController` provides API endpoints for triggering and monitoring replay operations.

```typescript
@Controller('admin/order-replay')
@UseGuards(AdminAuthGuard)
export class OrderReplayController {
  constructor(
    private readonly orderReplayService: OrderReplayService,
    private readonly logger: Logger,
  ) {}

  @Post('order/:orderId')
  async replayOrder(
    @Param('orderId') orderId: string,
    @Body() options: OrderReplayOptions,
  ): Promise<ReplayResult> {
    this.logger.log(`Initiating replay for order ${orderId}`);
    
    return this.orderReplayService.replayOrder(
      orderId,
      options,
    );
  }

  @Post('projection/:projectionName')
  async rebuildProjection(
    @Param('projectionName') projectionName: string,
    @Body() options: ProjectionRebuildOptions,
  ): Promise<ReplayResult> {
    this.logger.log(`Initiating rebuild of order projection: ${projectionName}`);
    
    return this.orderReplayService.rebuildProjection(
      projectionName,
      options,
    );
  }

  @Post('time-range')
  async replayTimeRange(
    @Body() options: TimeRangeReplayOptions,
  ): Promise<ReplayResult> {
    this.logger.log(
      `Initiating time-range replay from ${options.startTime} to ${options.endTime}`,
    );
    
    return this.orderReplayService.replayTimeRange(options);
  }

  @Get('status/:replayId')
  async getReplayStatus(
    @Param('replayId') replayId: string,
  ): Promise<ReplayStatus> {
    return this.orderReplayService.getReplayStatus(replayId);
  }
}
```

### Replay Service

The `OrderReplayService` orchestrates the replay process.

```typescript
@Injectable()
export class OrderReplayService {
  constructor(
    private readonly orderEventStoreRepository: OrderEventStoreRepository,
    private readonly orderRepository: OrderRepository,
    private readonly orderProjectionManager: OrderProjectionManager,
    private readonly eventBus: EventBus,
    private readonly logger: Logger,
  ) {}

  async replayOrder(
    orderId: string,
    options: OrderReplayOptions,
  ): Promise<ReplayResult> {
    const replayId = this.generateReplayId();
    const startTime = Date.now();
    let processedCount = 0;
    
    try {
      // Record replay start in the replay registry
      await this.recordReplayStart(replayId, 'ORDER', { orderId });
      
      // Fetch all events for the order
      const events = await this.orderEventStoreRepository.getEventsForOrder(
        orderId,
        {
          startSequence: options.startSequence,
          endSequence: options.endSequence,
        },
      );
      
      if (events.length === 0) {
        await this.recordReplayComplete(replayId, 0);
        return { 
          replayId,
          success: true, 
          message: 'No events found for order',
          eventsProcessed: 0,
          timeElapsedMs: Date.now() - startTime
        };
      }
      
      // Reset order state if requested
      if (options.resetState) {
        await this.orderRepository.deleteOrder(orderId);
      }
      
      // Process events in sequence
      for (const event of events) {
        if (options.dryRun) {
          // Log but don't process in dry run mode
          this.logger.debug(`[DRY RUN] Would process event: ${event.eventType} for order ${orderId}`);
        } else {
          // Apply event to rebuild order state
          await this.processEvent(event, options);
          processedCount++;
          
          // Update progress
          await this.updateReplayProgress(replayId, processedCount, events.length);
        }
      }
      
      // Record replay completion
      await this.recordReplayComplete(replayId, processedCount);
      
      return {
        replayId,
        success: true,
        message: options.dryRun 
          ? `Dry run completed, would process ${events.length} events` 
          : `Successfully replayed ${processedCount} events for order ${orderId}`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime
      };
    } catch (error) {
      this.logger.error(
        `Error during replay for order ${orderId}`,
        error,
      );
      
      // Record replay failure
      await this.recordReplayFailure(replayId, error.message);
      
      return {
        replayId,
        success: false,
        message: `Replay failed: ${error.message}`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime,
        error: error.message,
      };
    }
  }

  async rebuildProjection(
    projectionName: string,
    options: ProjectionRebuildOptions,
  ): Promise<ReplayResult> {
    const replayId = this.generateReplayId();
    const startTime = Date.now();
    let processedCount = 0;
    
    try {
      // Record replay start
      await this.recordReplayStart(replayId, 'PROJECTION', { projectionName });
      
      // Get the projection handler
      const projection = this.orderProjectionManager.getProjection(projectionName);
      if (!projection) {
        throw new Error(`Projection ${projectionName} not found`);
      }
      
      // Reset projection if requested
      if (options.resetState) {
        await projection.reset();
      }
      
      // Get relevant event types for this projection
      const eventTypes = projection.getInterestedEventTypes();
      
      // Total count for progress tracking
      let totalCount = 0;
      if (options.estimateTotal) {
        totalCount = await this.orderEventStoreRepository.countEventsByTypes(
          eventTypes,
          {
            startTime: options.startTime,
            endTime: options.endTime,
          }
        );
      }
      
      // Stream events for processing
      const eventStream = this.orderEventStoreRepository.streamOrderEvents({
        startTime: options.startTime,
        endTime: options.endTime,
        eventTypes,
        batchSize: options.batchSize || 100,
      });
      
      // Process events
      for await (const event of eventStream) {
        if (options.dryRun) {
          this.logger.debug(`[DRY RUN] Would process event: ${event.eventType} for projection ${projectionName}`);
        } else {
          await projection.handleEvent(event);
          processedCount++;
          
          // Update progress
          if (processedCount % 100 === 0) {
            await this.updateReplayProgress(
              replayId, 
              processedCount, 
              totalCount > 0 ? totalCount : undefined
            );
            
            // Log progress
            this.logger.log(`Processed ${processedCount} events for projection ${projectionName}`);
          }
        }
      }
      
      // Record replay completion
      await this.recordReplayComplete(replayId, processedCount);
      
      return {
        replayId,
        success: true,
        message: options.dryRun 
          ? `Dry run completed for projection ${projectionName}` 
          : `Successfully rebuilt projection ${projectionName} with ${processedCount} events`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime
      };
    } catch (error) {
      this.logger.error(
        `Error during projection rebuild for ${projectionName}`,
        error,
      );
      
      // Record replay failure
      await this.recordReplayFailure(replayId, error.message);
      
      return {
        replayId,
        success: false,
        message: `Projection rebuild failed: ${error.message}`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime,
        error: error.message,
      };
    }
  }

  async replayTimeRange(
    options: TimeRangeReplayOptions,
  ): Promise<ReplayResult> {
    const replayId = this.generateReplayId();
    const startTime = Date.now();
    let processedCount = 0;
    
    try {
      // Record replay start
      await this.recordReplayStart(replayId, 'TIME_RANGE', {
        startTime: options.startTime,
        endTime: options.endTime,
      });
      
      // Total count for progress tracking
      let totalCount = 0;
      if (options.estimateTotal) {
        totalCount = await this.orderEventStoreRepository.countEventsByTimeRange(
          options.startTime,
          options.endTime,
          options.eventTypes
        );
      }
      
      // Stream events for processing
      const eventStream = this.orderEventStoreRepository.streamOrderEvents({
        startTime: options.startTime,
        endTime: options.endTime,
        eventTypes: options.eventTypes,
        batchSize: options.batchSize || 100,
      });
      
      // Process events
      for await (const event of eventStream) {
        if (options.dryRun) {
          this.logger.debug(`[DRY RUN] Would process event: ${event.eventType} (${event.aggregateId})`);
        } else {
          // Process event based on options
          await this.processEvent(event, options);
          processedCount++;
          
          // Update progress
          if (processedCount % 100 === 0) {
            await this.updateReplayProgress(
              replayId, 
              processedCount, 
              totalCount > 0 ? totalCount : undefined
            );
            
            // Log progress
            this.logger.log(`Processed ${processedCount} events for time range replay`);
          }
        }
      }
      
      // Record replay completion
      await this.recordReplayComplete(replayId, processedCount);
      
      return {
        replayId,
        success: true,
        message: options.dryRun 
          ? `Dry run completed for time range replay` 
          : `Successfully replayed ${processedCount} events from ${options.startTime} to ${options.endTime}`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime
      };
    } catch (error) {
      this.logger.error(
        `Error during time range replay`,
        error,
      );
      
      // Record replay failure
      await this.recordReplayFailure(replayId, error.message);
      
      return {
        replayId,
        success: false,
        message: `Time range replay failed: ${error.message}`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime,
        error: error.message,
      };
    }
  }

  async getReplayStatus(replayId: string): Promise<ReplayStatus> {
    return this.getReplayFromRegistry(replayId);
  }

  private async processEvent(event: OrderDomainEvent, options: ReplayOptions): Promise<void> {
    // Apply to aggregates if needed
    if (options.updateAggregates) {
      const order = await this.orderRepository.getOrderById(event.aggregateId, { skipEvents: true });
      if (order) {
        order.applyEvent(event);
        await this.orderRepository.save(order);
      } else {
        // Create new order from event if it doesn't exist
        const newOrder = new Order();
        newOrder.applyEvent(event);
        await this.orderRepository.save(newOrder);
      }
    }
    
    // Update projections if needed
    if (options.updateProjections) {
      await this.orderProjectionManager.handleEvent(event);
    }
    
    // Republish to event bus if needed
    if (options.republishToEventBus) {
      await this.eventBus.publish(event);
    }
  }

  // Helper methods for tracking replay status
  private generateReplayId(): string {
    return `replay-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private async recordReplayStart(replayId: string, type: string, details: any): Promise<void> {
    // Implementation depends on storage mechanism (DynamoDB, Redis, etc.)
    // This is a simplified example
    const replayRecord = {
      replayId,
      type,
      details,
      status: 'RUNNING',
      startTime: new Date(),
      progress: {
        processed: 0,
        total: 0,
        percentage: 0,
      },
    };
    
    await this.saveReplayToRegistry(replayId, replayRecord);
  }

  private async updateReplayProgress(replayId: string, processed: number, total?: number): Promise<void> {
    const replay = await this.getReplayFromRegistry(replayId);
    if (!replay) return;
    
    replay.progress = {
      processed,
      total: total || 0,
      percentage: total ? Math.floor((processed / total) * 100) : 0,
    };
    
    await this.saveReplayToRegistry(replayId, replay);
  }

  private async recordReplayComplete(replayId: string, processedCount: number): Promise<void> {
    const replay = await this.getReplayFromRegistry(replayId);
    if (!replay) return;
    
    replay.status = 'COMPLETED';
    replay.endTime = new Date();
    replay.progress = {
      processed: processedCount,
      total: processedCount,
      percentage: 100,
    };
    
    await this.saveReplayToRegistry(replayId, replay);
  }

  private async recordReplayFailure(replayId: string, errorMessage: string): Promise<void> {
    const replay = await this.getReplayFromRegistry(replayId);
    if (!replay) return;
    
    replay.status = 'FAILED';
    replay.endTime = new Date();
    replay.error = errorMessage;
    
    await this.saveReplayToRegistry(replayId, replay);
  }

  // Simplified registry interactions (would use a database or cache in production)
  private async saveReplayToRegistry(replayId: string, replay: any): Promise<void> {
    // In a real implementation, save to DynamoDB, Redis, etc.
    // For this example, we'll just log
    this.logger.debug(`Saved replay ${replayId}: ${JSON.stringify(replay)}`);
  }

  private async getReplayFromRegistry(replayId: string): Promise<any> {
    // In a real implementation, retrieve from DynamoDB, Redis, etc.
    // For this example, we'll return a mock
    return {
      replayId,
      status: 'COMPLETED', // Mock status
      startTime: new Date(Date.now() - 60000),
      endTime: new Date(),
      progress: {
        processed: 100,
        total: 100,
        percentage: 100,
      },
    };
  }
}
```

## Replay Options Interfaces

```typescript
export interface ReplayOptions {
  // Whether to perform a dry run (log but don't apply changes)
  dryRun?: boolean;
  
  // Whether to update aggregate state
  updateAggregates?: boolean;
  
  // Whether to update projections
  updateProjections?: boolean;
  
  // Whether to republish events to the event bus
  republishToEventBus?: boolean;
}

export interface OrderReplayOptions extends ReplayOptions {
  // Starting event sequence number
  startSequence?: number;
  
  // Ending event sequence number
  endSequence?: number;
  
  // Whether to reset order state before replay
  resetState?: boolean;
}

export interface ProjectionRebuildOptions extends ReplayOptions {
  // Starting timestamp (milliseconds since epoch)
  startTime?: Date;
  
  // Ending timestamp (milliseconds since epoch)
  endTime?: Date;
  
  // Whether to reset projection state before rebuild
  resetState?: boolean;
  
  // Number of events to process in each batch
  batchSize?: number;
  
  // Whether to estimate total events for progress tracking
  estimateTotal?: boolean;
}

export interface TimeRangeReplayOptions extends ReplayOptions {
  // Starting timestamp (inclusive)
  startTime: Date;
  
  // Ending timestamp (inclusive)
  endTime: Date;
  
  // Event types to filter (optional)
  eventTypes?: string[];
  
  // Number of events to process in each batch
  batchSize?: number;
  
  // Whether to estimate total events for progress tracking
  estimateTotal?: boolean;
}

export interface ReplayResult {
  // Unique ID for tracking this replay operation
  replayId: string;
  
  // Whether the replay was successful
  success: boolean;
  
  // Message describing the result
  message: string;
  
  // Number of events processed
  eventsProcessed: number;
  
  // Time elapsed in milliseconds
  timeElapsedMs: number;
  
  // Error message if replay failed
  error?: string;
}

export interface ReplayStatus {
  // Unique ID for this replay
  replayId: string;
  
  // Status: RUNNING, COMPLETED, FAILED
  status: string;
  
  // When the replay started
  startTime: Date;
  
  // When the replay completed or failed
  endTime?: Date;
  
  // Progress information
  progress: {
    processed: number;
    total: number;
    percentage: number;
  };
  
  // Error message if failed
  error?: string;
  
  // Additional details about the replay
  details?: any;
}
```

## Order State Reconstruction

When replaying events to reconstruct an order, the events are processed in the same way as during normal operation, but with some special considerations:

```typescript
@Injectable()
export class OrderAggregateFactory {
  createFromEvents(orderId: string, events: OrderDomainEvent[]): Order {
    // Create a new empty order
    const order = new Order();
    order.id = orderId;
    
    // Apply all events in sequence
    for (const event of events) {
      order.applyEvent(event, true); // Second parameter indicates replay mode
    }
    
    return order;
  }
}
```

The `Order` class implements event handling with replay awareness:

```typescript
export class Order {
  // Properties
  id: string;
  orderNumber: string;
  status: OrderStatus;
  items: OrderItem[] = [];
  // Other properties...
  
  // Event handling
  applyEvent(event: OrderDomainEvent, isReplay = false): void {
    switch (event.eventType) {
      case 'ORDER_CREATED':
        this.applyOrderCreatedEvent(event, isReplay);
        break;
      case 'ORDER_PAYMENT_COMPLETED':
        this.applyOrderPaymentCompletedEvent(event, isReplay);
        break;
      // Handle other event types...
    }
    
    // If not a replay, record the fact that we've handled this event
    if (!isReplay) {
      this.version++;
    }
  }
  
  private applyOrderCreatedEvent(event: OrderCreatedEvent, isReplay: boolean): void {
    // Extract data from event
    const { customerId, orderNumber, items, billingDetails, shippingDetails, subtotal, tax, shippingCost, discount, total } = event.data;
    
    // Apply to state
    this.orderNumber = orderNumber;
    this.customerId = customerId;
    this.items = items.map(item => new OrderItem(item));
    this.billingDetails = new BillingDetails(billingDetails);
    this.shippingDetails = new ShippingDetails(shippingDetails);
    this.subtotal = subtotal;
    this.tax = tax;
    this.shippingCost = shippingCost;
    this.discount = discount;
    this.total = total;
    this.status = OrderStatus.CREATED;
    
    // If not a replay, might perform additional actions like validation
    if (!isReplay) {
      // E.g., validate that all required fields are present
    }
  }
  
  // Other event application methods...
}
```

## Projection Rebuilding

Projections provide optimized read models. When rebuilt, they process all relevant events:

```typescript
@Injectable()
export class OrderStatusProjection implements OrderProjection {
  constructor(
    private readonly dataSource: DataSource,
    private readonly logger: Logger,
  ) {}
  
  // Define which events this projection cares about
  getInterestedEventTypes(): string[] {
    return [
      'ORDER_CREATED',
      'ORDER_PAYMENT_PENDING',
      'ORDER_PAYMENT_COMPLETED',
      'ORDER_PROCESSING',
      'ORDER_SHIPPED',
      'ORDER_DELIVERED',
      'ORDER_CANCELLED',
    ];
  }
  
  // Reset the projection (used before rebuilding)
  async reset(): Promise<void> {
    await this.dataSource.createQueryBuilder()
      .delete()
      .from('order_status_view')
      .execute();
  }
  
  // Handle an event during normal processing or replay
  async handleEvent(event: OrderDomainEvent): Promise<void> {
    try {
      switch (event.eventType) {
        case 'ORDER_CREATED':
          await this.handleOrderCreated(event);
          break;
        case 'ORDER_PAYMENT_COMPLETED':
          await this.handleOrderPaymentCompleted(event);
          break;
        // Handle other event types...
      }
    } catch (error) {
      this.logger.error(`Error handling event ${event.eventType} in OrderStatusProjection`, error);
      throw error;
    }
  }
  
  private async handleOrderCreated(event: OrderCreatedEvent): Promise<void> {
    const { orderId, orderNumber } = event;
    const { customerId } = event.data;
    
    // Upsert the order status view
    await this.dataSource.createQueryBuilder()
      .insert()
      .into('order_status_view')
      .values({
        order_id: orderId,
        order_number: orderNumber,
        customer_id: customerId,
        status: 'CREATED',
        created_at: new Date(event.timestamp),
        last_updated: new Date(event.timestamp),
      })
      .orUpdate(['status', 'last_updated'], ['order_id'])
      .execute();
  }
  
  // Other event handling methods...
}
```

## Performance Considerations

1. **Batched Processing**: Process events in batches to optimize database operations
2. **Progressive Updates**: Update progress tracking for long-running replays
3. **Parallel Processing**: Use worker queues for projections that can be rebuilt independently
4. **Resource Throttling**: Limit concurrent replay operations to prevent system overload

## Security Considerations

1. **Admin-Only Access**: Restrict replay functionality to administrative users
2. **Audit Logging**: Record all replay operations in audit logs
3. **Rate Limiting**: Limit frequency of replay requests
4. **Process Isolation**: Run replay operations in separate process pools