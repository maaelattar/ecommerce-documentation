# Inventory Item Entity

## Overview
The Inventory Item entity represents a unique stocked product in the inventory system. It tracks quantity, location, and status of products across warehouses.

## Entity Definition

```typescript
@Entity('inventory_items')
export class InventoryItem {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar', length: 100, unique: true })
  sku: string;

  @Column({ type: 'varchar', length: 255 })
  productId: string;

  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'int', default: 0 })
  quantityAvailable: number;

  @Column({ type: 'int', default: 0 })
  quantityReserved: number;

  @Column({ type: 'int', default: 0 })
  quantityOnOrder: number;

  @Column({ type: 'int' })
  reorderThreshold: number;

  @Column({ type: 'int' })
  targetStockLevel: number;

  @Column({ type: 'boolean', default: true })
  active: boolean;

  @ManyToOne(() => Warehouse)
  @JoinColumn({ name: 'warehouse_id' })
  warehouse: Warehouse;

  @Column({ name: 'warehouse_id' })
  warehouseId: string;

  @OneToMany(() => StockTransaction, transaction => transaction.inventoryItem)
  transactions: StockTransaction[];

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  createdAt: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updatedAt: Date;

  @Column({ type: 'varchar', length: 100, nullable: true })
  location: string;

  @Column({ type: 'varchar', length: 100, nullable: true })
  barcode: string;

  @Column({ type: 'jsonb', nullable: true })
  metadata: Record<string, any>;
}
```

## Business Rules

1. **Stock Availability**
   - `quantityAvailable` represents the physical stock that can be sold or allocated
   - `quantityAvailable = totalQuantity - quantityReserved`

2. **Stock Reservations**
   - `quantityReserved` represents inventory allocated to orders but not yet shipped
   - When an order is placed, inventory is moved from available to reserved
   - When an order is shipped, inventory is removed from reserved

3. **Reordering Logic**
   - System triggers reorder alerts when `quantityAvailable <= reorderThreshold`
   - Target stock level is used to determine reorder quantity

4. **Unique Constraints**
   - Each SKU must be unique across the system
   - Product may have multiple inventory items if stored in different warehouses

## Methods

```typescript
// Calculate available inventory that can be allocated
calculateAvailableToAllocate(): number {
  return this.quantityAvailable - this.quantityReserved;
}

// Check if item needs reordering
needsReorder(): boolean {
  return this.quantityAvailable <= this.reorderThreshold;
}

// Calculate recommended reorder quantity
calculateReorderQuantity(): number {
  return this.targetStockLevel - (this.quantityAvailable + this.quantityOnOrder);
}

// Reserve inventory for an order
reserveInventory(quantity: number): boolean {
  if (this.quantityAvailable >= quantity) {
    this.quantityReserved += quantity;
    this.quantityAvailable -= quantity;
    return true;
  }
  return false;
}

// Release previously reserved inventory
releaseReservation(quantity: number): void {
  this.quantityReserved -= quantity;
  this.quantityAvailable += quantity;
}

// Process inventory adjustment
adjustInventory(quantity: number, reason: string): void {
  this.quantityAvailable += quantity;
  // Log adjustment as a transaction
}
```

## Indexing Strategy

```sql
-- Index for fast lookups by SKU
CREATE INDEX idx_inventory_items_sku ON inventory_items(sku);

-- Index for finding products in specific warehouse
CREATE INDEX idx_inventory_items_warehouse ON inventory_items(warehouse_id);

-- Index for filtering active inventory items
CREATE INDEX idx_inventory_items_active ON inventory_items(active);

-- Index for product-based lookups
CREATE INDEX idx_inventory_items_product ON inventory_items(product_id);
```