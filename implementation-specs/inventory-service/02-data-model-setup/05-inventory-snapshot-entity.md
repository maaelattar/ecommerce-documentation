# Inventory Snapshot Entity

## Overview
The Inventory Snapshot entity provides a point-in-time record of inventory levels across all warehouses. These snapshots are used for historical reporting, reconciliation, and trend analysis without the need to replay all transactions.

## Entity Definition

```typescript
@Entity('inventory_snapshots')
export class InventorySnapshot {
  @PrimaryGeneratedColumn('uuid')
  id: string;

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

  @Column({ type: 'date' })
  snapshotDate: Date;

  @Column({ type: 'int' })
  quantityAvailable: number;

  @Column({ type: 'int' })
  quantityReserved: number;

  @Column({ type: 'int' })
  quantityOnOrder: number;

  @Column({ type: 'int' })
  quantitySold: number;

  @Column({ type: 'int' })
  quantityReceived: number;

  @Column({ type: 'int' })
  quantityReturned: number;

  @Column({ type: 'int' })
  quantityDamaged: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  valueAvailable: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  valueSold: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  valueReceived: number;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  createdAt: Date;

  @Column({ type: 'varchar', length: 100 })
  createdBy: string;

  @Column({ type: 'boolean', default: false })
  isReconciled: boolean;

  @Column({ type: 'timestamp', nullable: true })
  reconciledAt: Date;

  @Column({ type: 'varchar', length: 100, nullable: true })
  reconciledBy: string;

  @Column({ type: 'int', nullable: true })
  discrepancy: number;

  @Column({ type: 'varchar', length: 255, nullable: true })
  notes: string;
}
```

## Business Rules

1. **Snapshot Timing**
   - Snapshots are typically taken daily, at the close of business
   - May be taken more frequently for high-velocity items
   - Special snapshots can be taken during inventory reconciliation

2. **Data Included**
   - Current quantities (available, reserved, on order)
   - Daily movement statistics (sold, received, returned, damaged)
   - Valuation data when available
   - Reconciliation status and information

3. **Reconciliation Process**
   - Physical counts are compared to system values
   - Discrepancies are recorded and may trigger adjustments
   - Reconciled snapshots are marked with reconciliation metadata

4. **Data Retention**
   - Snapshots are retained according to data retention policy
   - Typically kept for at least 7 years for financial audit purposes

## Indexing Strategy

```sql
-- Composite index for item and date lookups
CREATE INDEX idx_inventory_snapshots_item_date ON inventory_snapshots(inventory_item_id, snapshot_date);

-- Index for warehouse-based queries
CREATE INDEX idx_inventory_snapshots_warehouse ON inventory_snapshots(warehouse_id);

-- Index for date-based filtering
CREATE INDEX idx_inventory_snapshots_date ON inventory_snapshots(snapshot_date);

-- Index for reconciliation filtering
CREATE INDEX idx_inventory_snapshots_reconciled ON inventory_snapshots(is_reconciled);
```

## Snapshot Generation

The inventory snapshot process follows these steps:

1. **Scheduled Execution**
   - Runs automatically at a configured time (typically end of day)
   - Can be triggered manually if needed

2. **Data Collection**
   - Collects current inventory levels from all inventory items
   - Aggregates transaction data for the snapshot period

3. **Snapshot Creation**
   - Creates snapshot records for all inventory items
   - Calculates derived values (e.g., value based on cost)

4. **Retention Management**
   - Applies data retention policies
   - Archives or aggregates older snapshots based on configuration

## Usage Examples

1. **Historical Reporting**
   ```typescript
   // Get inventory levels for a product over time
   async getInventoryTrend(productId: string, startDate: Date, endDate: Date): Promise<InventorySnapshot[]> {
     return this.inventorySnapshotRepository.find({
       where: {
         inventoryItem: { productId },
         snapshotDate: Between(startDate, endDate)
       },
       order: { snapshotDate: 'ASC' }
     });
   }
   ```

2. **Reconciliation Workflow**
   ```typescript
   // Record physical count and reconcile
   async reconcileInventory(
     inventoryItemId: string, 
     physicalCount: number, 
     userId: string
   ): Promise<void> {
     const snapshot = await this.getLatestSnapshot(inventoryItemId);
     snapshot.discrepancy = physicalCount - snapshot.quantityAvailable;
     snapshot.isReconciled = true;
     snapshot.reconciledAt = new Date();
     snapshot.reconciledBy = userId;
     
     await this.inventorySnapshotRepository.save(snapshot);
     
     // Create adjustment transaction if needed
     if (snapshot.discrepancy !== 0) {
       await this.createAdjustmentTransaction(inventoryItemId, snapshot.discrepancy, 'RECONCILIATION');
     }
   }
   ```