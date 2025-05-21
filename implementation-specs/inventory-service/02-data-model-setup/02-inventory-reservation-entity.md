# Inventory Allocation Entity

## Overview
The Inventory Allocation entity represents a reservation of inventory items for a specific order. When a customer places an order, the inventory service allocates (reserves) the requested quantity of each product to ensure it's available when the order is processed.

## Entity Definition

```typescript
@Entity('inventory_allocations')
export class InventoryAllocation {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar', length: 100 })
  orderId: string;

  @Column({ type: 'varchar', length: 100 })
  orderItemId: string;

  @ManyToOne(() => InventoryItem)
  @JoinColumn({ name: 'inventory_item_id' })
  inventoryItem: InventoryItem;

  @Column({ name: 'inventory_item_id' })
  inventoryItemId: string;

  @ManyToOne(() => Warehouse)
  @JoinColumn({ name: 'warehouse_id' })
  warehouse: Warehouse;

  @Column({ name: 'warehouse_id' })
  warehouseId: string;

  @Column({ type: 'int' })
  quantity: number;

  @Column({
    type: 'enum',
    enum: ['PENDING', 'CONFIRMED', 'CANCELLED', 'FULFILLED'],
    default: 'PENDING'
  })
  status: 'PENDING' | 'CONFIRMED' | 'CANCELLED' | 'FULFILLED';

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  createdAt: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updatedAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  expiresAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  confirmedAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  cancelledAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  fulfilledAt: Date;

  @Column({ type: 'varchar', length: 255, nullable: true })
  notes: string;
}
```

## Business Rules

1. **Allocation States**
   - **PENDING**: Initial state when allocation is created but not yet confirmed
   - **CONFIRMED**: Allocation is confirmed and inventory is reserved
   - **CANCELLED**: Allocation was cancelled and inventory returned to available stock
   - **FULFILLED**: Allocation was fulfilled (item shipped) and inventory deducted

2. **Allocation Lifecycle**
   - When an order is placed, a PENDING allocation is created
   - Order confirmation changes allocation to CONFIRMED status
   - Cancellation moves allocation to CANCELLED and releases inventory
   - Order fulfillment moves allocation to FULFILLED and removes inventory

3. **Expiration Logic**
   - Pending allocations can expire if not confirmed within a set timeframe
   - System periodically checks for expired allocations and releases them

4. **Allocation Consistency**
   - Total allocated quantity must not exceed available inventory
   - Inventory service enforces this constraint during allocation creation

## Methods

```typescript
// Confirm the allocation
confirm(): void {
  if (this.status === 'PENDING') {
    this.status = 'CONFIRMED';
    this.confirmedAt = new Date();
  }
}

// Cancel the allocation and release inventory
cancel(reason: string): void {
  if (this.status === 'PENDING' || this.status === 'CONFIRMED') {
    this.status = 'CANCELLED';
    this.cancelledAt = new Date();
    this.notes = reason;
    
    // Logic to release the inventory handled by service
  }
}

// Mark allocation as fulfilled when order ships
fulfill(): void {
  if (this.status === 'CONFIRMED') {
    this.status = 'FULFILLED';
    this.fulfilledAt = new Date();
    
    // Final inventory deduction handled by service
  }
}

// Check if allocation has expired
isExpired(): boolean {
  return this.expiresAt != null && this.expiresAt < new Date();
}
```

## Indexing Strategy

```sql
-- Index for order-based lookups
CREATE INDEX idx_inventory_allocations_order ON inventory_allocations(order_id);

-- Index for inventory item allocations
CREATE INDEX idx_inventory_allocations_item ON inventory_allocations(inventory_item_id);

-- Index for warehouse allocations
CREATE INDEX idx_inventory_allocations_warehouse ON inventory_allocations(warehouse_id);

-- Index for status filtering
CREATE INDEX idx_inventory_allocations_status ON inventory_allocations(status);

-- Index for expiration checks
CREATE INDEX idx_inventory_allocations_expires ON inventory_allocations(expires_at);
```

## Additional Considerations

1. **Partial Allocations**
   If full allocation isn't possible, the system can:
   - Reject the allocation entirely
   - Allow partial allocation with backorder
   - Allocate from multiple warehouses

2. **Allocation Priority**
   When limited stock exists, allocation priority can be determined by:
   - Order creation time (FIFO)
   - Customer tier (e.g., premium customers first)
   - Custom business rules

3. **Bulk Allocation Processing**
   For performance, the system supports bulk allocation operations
   when processing large orders with multiple items.