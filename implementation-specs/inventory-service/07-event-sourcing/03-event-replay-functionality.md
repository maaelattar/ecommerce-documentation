# Event Replay Functionality

## Overview

Event replay is a critical capability in an event-sourced system that allows for rebuilding state, testing, and recovery. This document details the implementation of event replay functionality in the Inventory Service.

## Core Concepts

1. **Event Replay**: The process of reading events from the event store in chronological order and processing them to rebuild state
2. **Consistent Point-in-Time View**: Ability to reconstruct the state of the system at any historical point
3. **Saga Replay**: Replaying events to recover from failed sagas or long-running processes
4. **Projection Rebuilding**: Recreating read models from events

## Implementation Architecture

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
│   Aggregate   │◀────│  Event        │◀────│  Event        │
│   Repository  │     │  Handler      │     │  Router       │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
```

## Replay Controller Implementation

The ReplayController serves as the entry point for triggering event replay operations.

```typescript
@Controller('admin/replay')
@UseGuards(AdminAuthGuard)
export class ReplayController {
  constructor(
    private readonly replayService: ReplayService,
    private readonly logger: Logger,
  ) {}

  @Post('aggregate/:aggregateType/:aggregateId')
  async replayAggregate(
    @Param('aggregateType') aggregateType: string,
    @Param('aggregateId') aggregateId: string,
    @Body() options: ReplayOptions,
  ): Promise<ReplayResult> {
    this.logger.log(
      `Initiating replay for ${aggregateType} with ID ${aggregateId}`,
    );
    
    return this.replayService.replayAggregate(
      aggregateType,
      aggregateId,
      options,
    );
  }

  @Post('projection/:projectionName')
  async rebuildProjection(
    @Param('projectionName') projectionName: string,
    @Body() options: ReplayOptions,
  ): Promise<ReplayResult> {
    this.logger.log(
      `Initiating rebuild of projection: ${projectionName}`,
    );
    
    return this.replayService.rebuildProjection(
      projectionName,
      options,
    );
  }

  @Post('from-timestamp')
  async replayFromTimestamp(
    @Body() options: TimestampReplayOptions,
  ): Promise<ReplayResult> {
    this.logger.log(
      `Initiating replay from timestamp: ${options.startTimestamp}`,
    );
    
    return this.replayService.replayFromTimestamp(options);
  }
}
```

## Replay Service Implementation

The ReplayService orchestrates the replay process by fetching events and directing them to appropriate handlers.

```typescript
@Injectable()
export class ReplayService {
  constructor(
    private readonly eventStoreRepository: EventStoreRepository,
    private readonly eventBus: EventBus,
    private readonly projectionManager: ProjectionManager,
    private readonly aggregateRepository: AggregateRepository,
    private readonly logger: Logger,
  ) {}

  async replayAggregate(
    aggregateType: string,
    aggregateId: string,
    options: ReplayOptions,
  ): Promise<ReplayResult> {
    const startTime = Date.now();
    let processedCount = 0;
    
    try {
      // Fetch all events for the aggregate
      const events = await this.eventStoreRepository.getEventsForAggregate(
        aggregateId,
        {
          startSequence: options.startSequence || 1,
          endSequence: options.endSequence,
          startTimestamp: options.startTimestamp,
          endTimestamp: options.endTimestamp,
        },
      );
      
      if (events.length === 0) {
        return { 
          success: true, 
          message: 'No events found for replay',
          eventsProcessed: 0,
          timeElapsedMs: Date.now() - startTime
        };
      }
      
      // Clear existing aggregate state if requested
      if (options.resetState) {
        await this.aggregateRepository.deleteAggregate(aggregateType, aggregateId);
      }
      
      // Process events in sequence
      for (const event of events) {
        if (options.dryRun) {
          // Log but don't process in dry run mode
          this.logger.debug(`[DRY RUN] Would process event: ${event.eventType} for ${aggregateId}`);
        } else {
          // Apply event to rebuild aggregate state
          await this.aggregateRepository.applyEvent(event);
          processedCount++;
        }
      }
      
      return {
        success: true,
        message: options.dryRun 
          ? `Dry run completed, would process ${events.length} events` 
          : `Successfully replayed ${processedCount} events`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime
      };
    } catch (error) {
      this.logger.error(
        `Error during replay for ${aggregateType}:${aggregateId}`,
        error,
      );
      
      return {
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
    options: ReplayOptions,
  ): Promise<ReplayResult> {
    const startTime = Date.now();
    let processedCount = 0;
    
    try {
      // Clear existing projection if reset is requested
      if (options.resetState) {
        await this.projectionManager.resetProjection(projectionName);
      }
      
      // Get the projection handler
      const projection = this.projectionManager.getProjection(projectionName);
      if (!projection) {
        throw new Error(`Projection ${projectionName} not found`);
      }
      
      // Get relevant event types for this projection
      const eventTypes = projection.getInterestedEventTypes();
      
      // Stream events for processing
      const eventStream = this.eventStoreRepository.streamEventsByTypes(
        eventTypes,
        {
          startTimestamp: options.startTimestamp,
          endTimestamp: options.endTimestamp,
        },
      );
      
      // Process events
      for await (const event of eventStream) {
        if (options.dryRun) {
          this.logger.debug(`[DRY RUN] Would process event: ${event.eventType} for projection ${projectionName}`);
        } else {
          await projection.handleEvent(event);
          processedCount++;
          
          // Periodic logging for long operations
          if (processedCount % 1000 === 0) {
            this.logger.log(`Projection rebuild progress: ${processedCount} events processed`);
          }
        }
      }
      
      return {
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
      
      return {
        success: false,
        message: `Projection rebuild failed: ${error.message}`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime,
        error: error.message,
      };
    }
  }

  async replayFromTimestamp(
    options: TimestampReplayOptions,
  ): Promise<ReplayResult> {
    const startTime = Date.now();
    let processedCount = 0;
    
    try {
      // Stream all events from the specified timestamp
      const eventStream = this.eventStoreRepository.streamEvents({
        startTimestamp: options.startTimestamp,
        endTimestamp: options.endTimestamp,
        aggregateTypes: options.aggregateTypes,
        eventTypes: options.eventTypes,
      });
      
      // Process events
      for await (const event of eventStream) {
        if (options.dryRun) {
          this.logger.debug(`[DRY RUN] Would process event: ${event.eventType} (${event.aggregateType}:${event.aggregateId})`);
        } else {
          // Republish the event to the event bus for handling
          if (options.republishToEventBus) {
            await this.eventBus.publish(event);
          }
          
          // Apply directly to aggregates or projections
          if (options.updateAggregates) {
            await this.aggregateRepository.applyEvent(event);
          }
          
          if (options.updateProjections) {
            await this.projectionManager.handleEvent(event);
          }
          
          processedCount++;
          
          // Periodic logging for long operations
          if (processedCount % 1000 === 0) {
            this.logger.log(`Replay progress: ${processedCount} events processed`);
          }
        }
      }
      
      return {
        success: true,
        message: options.dryRun 
          ? `Dry run completed for timestamp-based replay` 
          : `Successfully replayed ${processedCount} events from timestamp`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime
      };
    } catch (error) {
      this.logger.error(
        `Error during timestamp-based replay`,
        error,
      );
      
      return {
        success: false,
        message: `Timestamp-based replay failed: ${error.message}`,
        eventsProcessed: processedCount,
        timeElapsedMs: Date.now() - startTime,
        error: error.message,
      };
    }
  }
}
```

## Replay Options

```typescript
export interface ReplayOptions {
  // Starting event sequence number
  startSequence?: number;
  
  // Ending event sequence number
  endSequence?: number;
  
  // Starting timestamp (milliseconds since epoch)
  startTimestamp?: number;
  
  // Ending timestamp (milliseconds since epoch)
  endTimestamp?: number;
  
  // Whether to reset state before replay
  resetState?: boolean;
  
  // Whether to perform a dry run (log but don't apply changes)
  dryRun?: boolean;
}

export interface TimestampReplayOptions extends ReplayOptions {
  // Aggregate types to filter (optional)
  aggregateTypes?: string[];
  
  // Event types to filter (optional)
  eventTypes?: string[];
  
  // Whether to republish events to the event bus
  republishToEventBus?: boolean;
  
  // Whether to update aggregate state
  updateAggregates?: boolean;
  
  // Whether to update projections
  updateProjections?: boolean;
}
```

## Use Cases

### 1. Debugging and Analysis

Replay can be used to investigate issues or analyze past behavior:

```typescript
// Example: Replay all inventory item events to debug an issue
const replayResult = await replayService.replayAggregate(
  'INVENTORY_ITEM',
  'item-123',
  {
    dryRun: true, // Just log, don't modify state
  }
);
```

### 2. Rebuilding Projections

When projection code changes or becomes corrupted:

```typescript
// Example: Rebuild the inventory status projection
const rebuildResult = await replayService.rebuildProjection(
  'inventory-status',
  {
    resetState: true, // Clear existing projection data
  }
);
```

### 3. System Recovery

After data corruption or system failures:

```typescript
// Example: Replay all events after a specific timestamp
const recoveryResult = await replayService.replayFromTimestamp({
  startTimestamp: systemOutageTimestamp,
  updateAggregates: true,
  updateProjections: true,
});
```

### 4. Testing New Features

Test new event handlers with existing event history:

```typescript
// Example: Test a new feature with historical data
const testResult = await replayService.replayFromTimestamp({
  startTimestamp: testStartTimestamp,
  endTimestamp: testEndTimestamp,
  dryRun: true,
  aggregateTypes: ['INVENTORY_ITEM'],
});
```

## Performance Optimization

1. **Batch Processing**: Process events in batches to reduce I/O overhead
2. **Parallel Processing**: Use multi-threading for projections that can be rebuilt independently
3. **Selective Replay**: Only replay relevant event types or aggregates
4. **Progress Tracking**: Maintain progress metadata for long-running replays

## Replay API Security

The replay functionality is protected by:

1. **Admin Authentication**: Only authenticated administrators can trigger replays
2. **Rate Limiting**: Limited to 10 requests per hour to prevent abuse
3. **Audit Logging**: All replay operations are logged with admin identity for audit trails
4. **Resource Limits**: Configurable limits on maximum events per replay operation