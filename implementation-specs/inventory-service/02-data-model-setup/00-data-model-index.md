# Inventory Service Data Model

## Core Entities

The Inventory Service data model consists of the following core entities:

### 1. Inventory Item
The central entity that represents a unique stock keeping unit (SKU) in the system.
- [Inventory Item Entity Definition](./01-inventory-item-entity.md)

### 2. Inventory Allocation
Represents a reservation of inventory for an order.
- [Inventory Allocation Entity Definition](./02-inventory-reservation-entity.md)

### 3. Warehouse
Represents a physical location where inventory is stored.
- [Warehouse Entity Definition](./03-warehouse-entity.md)

### 4. Stock Transaction
Records all movements of inventory (receipts, adjustments, returns, etc.).
- [Stock Transaction Entity Definition](./04-stock-transaction-entity.md)

### 5. Inventory Snapshot
Point-in-time record of inventory levels, used for reporting and reconciliation.
- [Inventory Snapshot Entity Definition](./05-inventory-snapshot-entity.md)

## Entity Relationships

```
┌───────────────┐     ┌───────────────┐
│               │     │               │
│ Inventory Item│◄────┤   Warehouse   │
│               │     │               │
└───────┬───────┘     └───────────────┘
        │
        │
        ▼
┌───────────────┐     ┌───────────────┐
│  Inventory    │     │    Stock      │
│  Allocation   │     │  Transaction  │
│               │     │               │
└───────────────┘     └───────────────┘
```

## Data Access Patterns

### TypeORM Repositories
The Inventory Service uses TypeORM to interact with the PostgreSQL database:

1. **InventoryItemRepository**
   - Primary operations for inventory management

2. **AllocationRepository**
   - Manages inventory allocations and reservations

3. **WarehouseRepository**
   - CRUD operations for warehouse management

4. **StockTransactionRepository**
   - Records all inventory movements

5. **InventorySnapshotRepository**
   - Manages periodic snapshots of inventory state

### Event Sourcing
For event sourcing pattern, the service uses a separate repository interface:

1. **InventoryEventRepository**
   - Stores all inventory-related events
   - Enables event replay and state reconstruction