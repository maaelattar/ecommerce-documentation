# Inventory Domain Events

## Overview

This document defines the domain events used in the Inventory Service. These events represent significant state changes in the inventory domain and are used for both event sourcing and integration with other services.

## Event Structure

All inventory domain events follow a common structure:

```typescript
export interface DomainEvent {
  eventId: string;           // Unique identifier for the event
  aggregateId: string;       // ID of the entity this event relates to
  aggregateType: string;     // Type of entity (e.g., "InventoryItem")
  eventType: string;         // Type of event
  timestamp: Date;           // When the event occurred
  version: number;           // Schema version for the event
  metadata: {                // Additional contextual information
    userId: string;          // User who triggered the event
    correlationId: string;   // ID linking related operations
    causationId: string;     // ID of event that caused this event
    source: string;          // Service that generated the event
  };
  data: any;                 // Event-specific payload
}
```

## Inventory Item Events

### InventoryItemCreatedEvent

Emitted when a new inventory item is created.

```typescript
export interface InventoryItemCreatedEvent extends DomainEvent {
  eventType: 'INVENTORY_ITEM_CREATED';
  aggregateType: 'INVENTORY_ITEM';
  data: {
    sku: string;
    productId: string;
    name: string;
    warehouseId: string;
    initialQuantity: number;
    reorderThreshold: number;
    targetStockLevel: number;
    metadata?: Record<string, any>;
  };
}
```

### StockLevelChangedEvent

Emitted when the quantity of an inventory item changes.

```typescript
export interface StockLevelChangedEvent extends DomainEvent {
  eventType: 'STOCK_LEVEL_CHANGED';
  aggregateType: 'INVENTORY_ITEM';
  data: {
    warehouseId: string;
    previousQuantity: number;
    newQuantity: number;
    changeAmount: number;  // Can be positive or negative
    changeReason: string;  // e.g., "RECEIPT", "SALE", "ADJUSTMENT"
    transactionId: string;
    referenceNumber?: string;
    referenceType?: string;
  };
}
```

### LowStockThresholdReachedEvent

Emitted when inventory falls below the reorder threshold.

```typescript
export interface LowStockThresholdReachedEvent extends DomainEvent {
  eventType: 'LOW_STOCK_THRESHOLD_REACHED';
  aggregateType: 'INVENTORY_ITEM';
  data: {
    sku: string;
    warehouseId: string;
    currentQuantity: number;
    reorderThreshold: number;
    targetStockLevel: number;
    suggestedOrderQuantity: number;
  };
}
```

### OutOfStockEvent

Emitted when an inventory item's available quantity reaches zero.

```typescript
export interface OutOfStockEvent extends DomainEvent {
  eventType: 'OUT_OF_STOCK';
  aggregateType: 'INVENTORY_ITEM';
  data: {
    sku: string;
    warehouseId: string;
    productId: string;
    lastTransactionId: string;
  };
}
```

### InventoryItemDeactivatedEvent

Emitted when an inventory item is deactivated.

```typescript
export interface InventoryItemDeactivatedEvent extends DomainEvent {
  eventType: 'INVENTORY_ITEM_DEACTIVATED';
  aggregateType: 'INVENTORY_ITEM';
  data: {
    reason: string;
  };
}
```

## Allocation Events

### AllocationCreatedEvent

Emitted when inventory is allocated to an order.

```typescript
export interface AllocationCreatedEvent extends DomainEvent {
  eventType: 'ALLOCATION_CREATED';
  aggregateType: 'ALLOCATION';
  data: {
    orderId: string;
    orderItemId: string;
    inventoryItemId: string;
    warehouseId: string;
    quantity: number;
    expiresAt?: Date;
  };
}
```

### AllocationConfirmedEvent

Emitted when an allocation is confirmed.

```typescript
export interface AllocationConfirmedEvent extends DomainEvent {
  eventType: 'ALLOCATION_CONFIRMED';
  aggregateType: 'ALLOCATION';
  data: {
    orderId: string;
    inventoryItemId: string;
    warehouseId: string;
    quantity: number;
  };
}
```

### AllocationCancelledEvent

Emitted when an allocation is cancelled.

```typescript
export interface AllocationCancelledEvent extends DomainEvent {
  eventType: 'ALLOCATION_CANCELLED';
  aggregateType: 'ALLOCATION';
  data: {
    orderId: string;
    inventoryItemId: string;
    warehouseId: string;
    quantity: number;
    reason: string;
  };
}
```

### AllocationFulfilledEvent

Emitted when an allocation is fulfilled (order shipped).

```typescript
export interface AllocationFulfilledEvent extends DomainEvent {
  eventType: 'ALLOCATION_FULFILLED';
  aggregateType: 'ALLOCATION';
  data: {
    orderId: string;
    inventoryItemId: string;
    warehouseId: string;
    quantity: number;
    shipmentId?: string;
  };
}
```

## Warehouse Events

### WarehouseCreatedEvent

Emitted when a new warehouse is added.

```typescript
export interface WarehouseCreatedEvent extends DomainEvent {
  eventType: 'WAREHOUSE_CREATED';
  aggregateType: 'WAREHOUSE';
  data: {
    code: string;
    name: string;
    location: {
      addressLine1: string;
      addressLine2?: string;
      city: string;
      state: string;
      postalCode: string;
      country: string;
      latitude?: number;
      longitude?: number;
    };
    isPrimary: boolean;
    isVirtual: boolean;
  };
}
```

### WarehouseDeactivatedEvent

Emitted when a warehouse is deactivated.

```typescript
export interface WarehouseDeactivatedEvent extends DomainEvent {
  eventType: 'WAREHOUSE_DEACTIVATED';
  aggregateType: 'WAREHOUSE';
  data: {
    reason: string;
  };
}
```

## Stock Transaction Events

### StockTransactionCreatedEvent

Emitted when a stock transaction is recorded.

```typescript
export interface StockTransactionCreatedEvent extends DomainEvent {
  eventType: 'STOCK_TRANSACTION_CREATED';
  aggregateType: 'STOCK_TRANSACTION';
  data: {
    inventoryItemId: string;
    warehouseId: string;
    type: string;  // RECEIPT, ADJUSTMENT, etc.
    quantity: number;
    referenceNumber?: string;
    referenceType?: string;
    reason?: string;
    sourceWarehouseId?: string;
    destinationWarehouseId?: string;
    lotNumber?: string;
    expirationDate?: Date;
  };
}
```

### StockTransferredEvent

Emitted when stock is transferred between warehouses.

```typescript
export interface StockTransferredEvent extends DomainEvent {
  eventType: 'STOCK_TRANSFERRED';
  aggregateType: 'INVENTORY_ITEM';
  data: {
    inventoryItemId: string;
    sourceWarehouseId: string;
    destinationWarehouseId: string;
    quantity: number;
    outboundTransactionId: string;
    inboundTransactionId: string;
  };
}
```