# Stock Transaction Processor

## Overview

The Stock Transaction Processor is responsible for recording and processing all inventory movements in the system. It ensures that each inventory change is properly documented with an associated transaction record, maintaining a complete audit trail of stock changes.

## Interface Definition

```typescript
export interface IStockTransactionProcessor {
  // Transaction Creation
  recordReceipt(command: RecordReceiptCommand): Promise<StockTransaction>;
  recordAdjustment(command: RecordAdjustmentCommand): Promise<StockTransaction>;
  recordTransfer(command: RecordTransferCommand): Promise<TransferTransactions>;
  recordSale(command: RecordSaleCommand): Promise<StockTransaction>;
  recordReturn(command: RecordReturnCommand): Promise<StockTransaction>;
  recordDamage(command: RecordDamageCommand): Promise<StockTransaction>;
  recordReservation(command: RecordReservationCommand): Promise<StockTransaction>;
  recordRelease(command: RecordReleaseCommand): Promise<StockTransaction>;
  recordCycleCount(command: RecordCycleCountCommand): Promise<StockTransaction>;
  
  // Transaction Queries
  getTransactionById(id: string): Promise<StockTransaction>;
  getTransactionsByInventoryItem(inventoryItemId: string, options?: QueryOptions): Promise<StockTransaction[]>;
  getTransactionsByWarehouse(warehouseId: string, options?: QueryOptions): Promise<StockTransaction[]>;
  getTransactionsByReference(referenceType: string, referenceNumber: string): Promise<StockTransaction[]>;
  getRelatedTransactions(transactionId: string): Promise<StockTransaction[]>;
}
```

## Implementation

```typescript
@Injectable()
export class StockTransactionProcessor implements IStockTransactionProcessor {
  constructor(
    private readonly stockTransactionRepository: IStockTransactionRepository,
    private readonly inventoryItemRepository: IInventoryItemRepository,
    private readonly warehouseRepository: IWarehouseRepository,
    private readonly eventPublisher: IEventPublisher,
    private readonly eventStore: IEventStore,
    private readonly logger: Logger
  ) {}

  // Implementation of interface methods...
}
```

## Transaction Types and Processing Logic

### 1. Receipt Transaction (RECEIPT)

Handles incoming inventory:

```typescript
async recordReceipt(command: RecordReceiptCommand): Promise<StockTransaction> {
  // Validate inventory item and warehouse exist
  const inventoryItem = await this.inventoryItemRepository.findById(command.inventoryItemId);
  if (!inventoryItem) throw new InventoryItemNotFoundException(command.inventoryItemId);
  
  // Create transaction
  const transaction = await this.stockTransactionRepository.create({
    inventoryItemId: command.inventoryItemId,
    warehouseId: command.warehouseId,
    type: 'RECEIPT',
    quantity: command.quantity,
    referenceNumber: command.referenceNumber,
    referenceType: command.referenceType,
    reason: command.reason || 'Stock receipt',
    createdBy: command.userId,
    lotNumber: command.lotNumber,
    expirationDate: command.expirationDate,
    metadata: command.metadata
  });
  
  // Update inventory item quantity
  inventoryItem.quantityAvailable += command.quantity;
  inventoryItem.updatedAt = new Date();
  await this.inventoryItemRepository.save(inventoryItem);
  
  // Publish events
  await this.eventPublisher.publish(new StockLevelChangedEvent({
    inventoryItemId: inventoryItem.id,
    warehouseId: inventoryItem.warehouseId,
    previousQuantity: inventoryItem.quantityAvailable - command.quantity,
    newQuantity: inventoryItem.quantityAvailable,
    changeAmount: command.quantity,
    changeReason: 'RECEIPT',
    transactionId: transaction.id
  }));
  
  return transaction;
}
```

### 2. Transfer Transaction (TRANSFER_OUT/TRANSFER_IN)

Handles stock movement between warehouses:

```typescript
async recordTransfer(command: RecordTransferCommand): Promise<TransferTransactions> {
  // Validate inventory items and warehouses exist
  const sourceItem = await this.inventoryItemRepository.findById(command.inventoryItemId, command.sourceWarehouseId);
  if (!sourceItem) throw new InventoryItemNotFoundException(command.inventoryItemId);
  
  if (sourceItem.quantityAvailable < command.quantity) {
    throw new InsufficientStockException(command.inventoryItemId, command.sourceWarehouseId);
  }
  
  // Create outbound transaction
  const outboundTransaction = await this.stockTransactionRepository.create({
    inventoryItemId: command.inventoryItemId,
    warehouseId: command.sourceWarehouseId,
    type: 'TRANSFER_OUT',
    quantity: command.quantity,
    referenceNumber: command.referenceNumber,
    referenceType: command.referenceType || 'WAREHOUSE_TRANSFER',
    reason: command.reason || 'Stock transfer',
    createdBy: command.userId,
    destinationWarehouseId: command.destinationWarehouseId,
    metadata: command.metadata
  });
  
  // Create inbound transaction
  const inboundTransaction = await this.stockTransactionRepository.create({
    inventoryItemId: command.inventoryItemId,
    warehouseId: command.destinationWarehouseId,
    type: 'TRANSFER_IN',
    quantity: command.quantity,
    referenceNumber: command.referenceNumber,
    referenceType: command.referenceType || 'WAREHOUSE_TRANSFER',
    reason: command.reason || 'Stock transfer',
    createdBy: command.userId,
    sourceWarehouseId: command.sourceWarehouseId,
    relatedTransactionId: outboundTransaction.id,
    metadata: command.metadata
  });
  
  // Update related transaction reference
  outboundTransaction.relatedTransactionId = inboundTransaction.id;
  await this.stockTransactionRepository.save(outboundTransaction);
  
  // Update inventory quantities
  sourceItem.quantityAvailable -= command.quantity;
  await this.inventoryItemRepository.save(sourceItem);
  
  // Get or create destination inventory item
  let destinationItem = await this.inventoryItemRepository.findById(
    command.inventoryItemId, 
    command.destinationWarehouseId
  );
  
  if (!destinationItem) {
    // Create new inventory item in destination warehouse
    destinationItem = await this.inventoryItemRepository.create({
      sku: sourceItem.sku,
      productId: sourceItem.productId,
      name: sourceItem.name,
      quantityAvailable: command.quantity,
      warehouseId: command.destinationWarehouseId,
      reorderThreshold: sourceItem.reorderThreshold,
      targetStockLevel: sourceItem.targetStockLevel
    });
  } else {
    // Update existing inventory item
    destinationItem.quantityAvailable += command.quantity;
    await this.inventoryItemRepository.save(destinationItem);
  }
  
  // Publish events
  await this.eventPublisher.publish(new StockTransferredEvent({
    inventoryItemId: sourceItem.id,
    sourceWarehouseId: command.sourceWarehouseId,
    destinationWarehouseId: command.destinationWarehouseId,
    quantity: command.quantity,
    outboundTransactionId: outboundTransaction.id,
    inboundTransactionId: inboundTransaction.id
  }));
  
  return {
    outboundTransaction,
    inboundTransaction
  };
}
```

## Business Rules

1. **Transaction Atomicity**
   - All inventory updates and transaction records must succeed together or fail together
   - Uses database transactions to ensure consistency

2. **Validation Rules**
   - Inventory item and warehouse must exist and be active
   - Cannot reduce inventory below zero
   - Transfer requires valid source and destination warehouses

3. **Audit Trail Requirements**
   - All transactions record the user who performed the action
   - Transactions include timestamps
   - Reference information links to external systems or documents

4. **Event Publishing**
   - Each transaction type publishes specific domain events
   - Events include before/after quantities and reason for change