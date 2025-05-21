# Stock Transaction Entity

## Overview
The Stock Transaction entity records all movements of inventory items in and out of warehouses. This entity provides a complete audit trail of inventory changes, including receipts, adjustments, transfers, returns, and order fulfillment.

## Entity Definition

```typescript
@Entity('stock_transactions')
export class StockTransaction {
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

  @Column({
    type: 'enum',
    enum: ['RECEIPT', 'ADJUSTMENT', 'TRANSFER_IN', 'TRANSFER_OUT', 'SALE', 'RETURN', 'DAMAGE', 'RESERVATION', 'RELEASE', 'CYCLE_COUNT'],
    default: 'ADJUSTMENT'
  })
  type: 'RECEIPT' | 'ADJUSTMENT' | 'TRANSFER_IN' | 'TRANSFER_OUT' | 'SALE' | 'RETURN' | 'DAMAGE' | 'RESERVATION' | 'RELEASE' | 'CYCLE_COUNT';

  @Column({ type: 'int' })
  quantity: number;

  @Column({ type: 'varchar', length: 255, nullable: true })
  referenceNumber: string;

  @Column({ type: 'varchar', length: 100, nullable: true })
  referenceType: string;

  @Column({ type: 'uuid', nullable: true })
  relatedTransactionId: string;

  @Column({ type: 'varchar', length: 255, nullable: true })
  reason: string;

  @Column({ type: 'varchar', length: 100 })
  createdBy: string;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  createdAt: Date;

  @Column({ type: 'jsonb', nullable: true })
  metadata: Record<string, any>;

  @Column({ type: 'varchar', length: 50, nullable: true })
  lotNumber: string;

  @Column({ type: 'timestamp', nullable: true })
  expirationDate: Date;

  @ManyToOne(() => Warehouse, { nullable: true })
  @JoinColumn({ name: 'source_warehouse_id' })
  sourceWarehouse: Warehouse;

  @Column({ name: 'source_warehouse_id', nullable: true })
  sourceWarehouseId: string;

  @ManyToOne(() => Warehouse, { nullable: true })
  @JoinColumn({ name: 'destination_warehouse_id' })
  destinationWarehouse: Warehouse;

  @Column({ name: 'destination_warehouse_id', nullable: true })
  destinationWarehouseId: string;
}
```

## Transaction Types

1. **RECEIPT**
   - Increases inventory when new stock is received
   - Usually associated with purchase orders

2. **ADJUSTMENT**
   - Manual adjustment to inventory quantities
   - May be positive or negative

3. **TRANSFER_IN / TRANSFER_OUT**
   - Records movement between warehouses
   - Paired transactions that should net to zero

4. **SALE**
   - Decreases inventory when orders are fulfilled

5. **RETURN**
   - Increases inventory when customer returns are processed

6. **DAMAGE**
   - Decreases inventory due to damaged or defective items

7. **RESERVATION**
   - Records when inventory is reserved for an order
   - Does not change total inventory, only available vs. reserved

8. **RELEASE**
   - Records when a reservation is released
   - Counterpart to RESERVATION

9. **CYCLE_COUNT**
   - Adjustment based on physical inventory count

## Business Rules

1. **Transaction Integrity**
   - All stock changes must be recorded with a transaction
   - Each transaction must have a type, quantity, and associated inventory item

2. **Reference Data**
   - `referenceNumber` and `referenceType` link to external documents (e.g., PO-12345, ORDER)
   - `relatedTransactionId` links to other transactions (e.g., connecting a transfer in/out)

3. **Audit Requirements**
   - All transactions record the user who created them
   - Timestamps are automatically recorded
   - Reason codes are required for certain transaction types

4. **Transfer Logic**
   - Transfer transactions require both source and destination warehouses
   - Each transfer creates two transactions: TRANSFER_OUT and TRANSFER_IN

## Indexing Strategy

```sql
-- Index for inventory item transactions
CREATE INDEX idx_stock_transactions_item ON stock_transactions(inventory_item_id);

-- Index for warehouse transactions
CREATE INDEX idx_stock_transactions_warehouse ON stock_transactions(warehouse_id);

-- Index for filtering by transaction type
CREATE INDEX idx_stock_transactions_type ON stock_transactions(type);

-- Index for reference lookups
CREATE INDEX idx_stock_transactions_reference ON stock_transactions(reference_type, reference_number);

-- Index for date-based filtering
CREATE INDEX idx_stock_transactions_date ON stock_transactions(created_at);

-- Index for related transaction lookups
CREATE INDEX idx_stock_transactions_related ON stock_transactions(related_transaction_id);
```

## Additional Considerations

1. **Cost Tracking**
   - Future enhancement will include cost information for each transaction
   - Will support average cost, FIFO, and LIFO accounting methods

2. **Lot and Expiration Tracking**
   - Support for lot number and expiration date on transactions
   - Critical for certain product categories (e.g., food, pharmaceuticals)

3. **Bulk Processing**
   - Optimized for bulk transaction processing
   - Transaction batching for high-volume operations