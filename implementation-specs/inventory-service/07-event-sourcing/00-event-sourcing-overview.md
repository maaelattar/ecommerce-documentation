# Event Sourcing Implementation for Inventory Service

## Overview

The Inventory Service implements event sourcing to maintain a complete history of all inventory changes. This approach provides an immutable audit trail, enables system reconstruction, and supports advanced analytics and reporting capabilities.

## Implementation Documentation

The event sourcing implementation is documented in the following sections:

1. [Event Store Implementation](./02-event-store-implementation.md) - Details on the storage and retrieval of events
2. [Event Replay Functionality](./03-event-replay-functionality.md) - Mechanisms for replaying events to rebuild state
3. [Snapshot Mechanism](./04-snapshot-mechanism.md) - Performance optimization through state snapshots
4. [Operational Considerations](./05-operational-considerations.md) - Monitoring, performance, backup, and troubleshooting
5. [Inventory Domain Events](./01-inventory-domain-events.md) - Detailed event definitions

## Event Sourcing Architecture

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│    Command    │────▶│   Aggregate   │────▶│    Event      │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────┬───────┘
                                                    │
                                                    ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│  Projections  │◀────│  Event Store  │◀────│  Event Bus    │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Key Components

1. **Commands**: Represent intentions to change the system state
2. **Aggregates**: Business entities that handle commands and emit events
3. **Events**: Immutable facts representing state changes
4. **Event Store**: DynamoDB-based persistent storage for all events
5. **Event Bus**: RabbitMQ for event distribution. Events stored in the Event Store (or integration events derived from domain events/state changes) are reliably published to this bus, typically using a mechanism like the Transactional Outbox pattern detailed in the service's event publishing documentation (see section `05-event-publishing`).
6. **Projections**: Read models built from event streams

## Event Store Implementation

The event store uses DynamoDB with the following structure:

```
Table: inventory_events
- partitionKey: aggregateId (string) - ID of the aggregate (e.g., inventoryItemId)
- sortKey: sequenceNumber (number) - Ordered sequence for the aggregate
- aggregateType: string - Type of aggregate (e.g., "InventoryItem", "Allocation")
- eventType: string - Type of event (e.g., "StockLevelChanged")
- eventData: JSON - Event payload
- metadata: JSON - Additional information (user, timestamp, correlation ID, etc.)
- timestamp: number - Time of event creation
```

### Benefits of DynamoDB for Event Store

1. **Scalability**: Handles high-volume event storage
2. **Performance**: Low-latency reads and writes
3. **Durability**: High durability guarantees
4. **Cost-effectiveness**: Pay-per-request pricing model
5. **AWS Integration**: Native integration with AWS services

## Domain Events

### Inventory Item Events

1. **InventoryItemCreatedEvent**

   - Emitted when a new inventory item is created
   - Contains item details (SKU, product ID, initial quantity, etc.)

2. **StockLevelChangedEvent**

   - Emitted when stock levels change
   - Contains previous and new quantities, reason for change

3. **LowStockThresholdReachedEvent**

   - Emitted when inventory falls below reorder threshold
   - Contains current quantity, threshold, and suggested reorder quantity

4. **InventoryItemDeactivatedEvent**
   - Emitted when an inventory item is deactivated
   - Contains reason for deactivation

### Allocation Events

1. **AllocationCreatedEvent**

   - Emitted when inventory is allocated to an order
   - Contains allocation details (order ID, item, quantity, etc.)

2. **AllocationConfirmedEvent**

   - Emitted when an allocation is confirmed
   - Contains allocation details and confirmation timestamp

3. **AllocationCancelledEvent**

   - Emitted when an allocation is cancelled
   - Contains allocation details and cancellation reason

4. **AllocationFulfilledEvent**
   - Emitted when an allocation is fulfilled (order shipped)
   - Contains allocation details and fulfillment timestamp

### Warehouse Events

1. **WarehouseCreatedEvent**

   - Emitted when a new warehouse is added
   - Contains warehouse details

2. **WarehouseUpdatedEvent**

   - Emitted when warehouse information changes
   - Contains previous and new details

3. **WarehouseDeactivatedEvent**
   - Emitted when a warehouse is deactivated
   - Contains reason for deactivation

## Event Projections

Projections transform events into read-optimized views:

1. **Current Inventory State**

   - Current quantities of all inventory items
   - Built from InventoryItemCreated and StockLevelChanged events

2. **Allocation Status**

   - Current status of all allocations
   - Built from various allocation events

3. **Inventory History**

   - Historical record of inventory changes over time
   - Useful for trend analysis and reporting

4. **Stock Movement Report**
   - Aggregated view of stock movements by time period
   - Built from various inventory-changing events
