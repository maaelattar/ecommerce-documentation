# Inventory Management Service

## Overview

The Inventory Management Service is responsible for core inventory operations including adding new inventory items, updating stock levels, and handling inventory movements. It enforces business rules related to inventory management and publishes domain events for all significant inventory changes.

## Service Interface

```typescript
export interface IInventoryManagementService {
  // Item Management
  createInventoryItem(command: CreateInventoryItemCommand): Promise<InventoryItem>;
  updateInventoryItem(command: UpdateInventoryItemCommand): Promise<InventoryItem>;
  deactivateInventoryItem(itemId: string, reason: string): Promise<void>;
  
  // Stock Management
  addStock(command: AddStockCommand): Promise<StockTransaction>;
  adjustStock(command: AdjustStockCommand): Promise<StockTransaction>;
  transferStock(command: TransferStockCommand): Promise<TransferResult>;
  
  // Stock Information
  getAvailableStock(itemId: string, warehouseId?: string): Promise<number>;
  getReservedStock(itemId: string, warehouseId?: string): Promise<number>;
  checkLowStockLevels(): Promise<LowStockItem[]>;
  
  // Threshold Management
  updateStockThresholds(command: UpdateThresholdsCommand): Promise<void>;
}
```

## Implementation

```typescript
@Injectable()
export class InventoryManagementService implements IInventoryManagementService {
  constructor(
    private readonly inventoryItemRepository: IInventoryItemRepository,
    private readonly stockTransactionRepository: IStockTransactionRepository,
    private readonly eventPublisher: IEventPublisher,
    private readonly eventStore: IEventStore,
    private readonly logger: Logger
  ) {}

  // Implementation of interface methods...
}
```

## CQRS Commands

### CreateInventoryItemCommand
```typescript
export class CreateInventoryItemCommand {
  readonly sku: string;
  readonly productId: string;
  readonly name: string;
  readonly warehouseId: string;
  readonly initialQuantity: number;
  readonly reorderThreshold: number;
  readonly targetStockLevel: number;
  readonly metadata?: Record<string, any>;
}
```

### AddStockCommand
```typescript
export class AddStockCommand {
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly quantity: number;
  readonly referenceNumber?: string;
  readonly referenceType?: string;
  readonly reason?: string;
  readonly lotNumber?: string;
  readonly expirationDate?: Date;
  readonly metadata?: Record<string, any>;
}
```

### AdjustStockCommand
```typescript
export class AdjustStockCommand {
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly quantity: number; // Positive or negative
  readonly reason: string;
  readonly referenceNumber?: string;
  readonly referenceType?: string;
  readonly metadata?: Record<string, any>;
}
```

### TransferStockCommand
```typescript
export class TransferStockCommand {
  readonly inventoryItemId: string;
  readonly sourceWarehouseId: string;
  readonly destinationWarehouseId: string;
  readonly quantity: number;
  readonly reason?: string;
  readonly referenceNumber?: string;
  readonly metadata?: Record<string, any>;
}
```

## Business Rules

1. **Inventory Creation Rules**
   - SKU must be unique across the system
   - Initial quantity must be non-negative
   - Reorder threshold must be less than target stock level

2. **Stock Addition Rules**
   - Quantity must be positive
   - Inventory item must exist and be active
   - Warehouse must exist and be active

3. **Stock Adjustment Rules**
   - Cannot reduce stock below zero
   - Reason is required for all adjustments
   - Large adjustments may require approval (configurable threshold)

4. **Stock Transfer Rules**
   - Source and destination warehouses must be different
   - Source warehouse must have sufficient stock
   - Both warehouses must be active

## Domain Events

### InventoryItemCreatedEvent
```typescript
export class InventoryItemCreatedEvent {
  readonly inventoryItemId: string;
  readonly sku: string;
  readonly productId: string;
  readonly warehouseId: string;
  readonly initialQuantity: number;
  readonly timestamp: Date;
}
```

### StockLevelChangedEvent
```typescript
export class StockLevelChangedEvent {
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly previousQuantity: number;
  readonly newQuantity: number;
  readonly changeAmount: number;
  readonly changeReason: string;
  readonly transactionId: string;
  readonly timestamp: Date;
}
```

### LowStockThresholdReachedEvent
```typescript
export class LowStockThresholdReachedEvent {
  readonly inventoryItemId: string;
  readonly sku: string;
  readonly warehouseId: string;
  readonly currentQuantity: number;
  readonly reorderThreshold: number;
  readonly targetStockLevel: number;
  readonly suggestedOrderQuantity: number;
  readonly timestamp: Date;
}
```

## Error Handling

The service handles various error scenarios:

1. **Validation Errors**
   - Invalid command parameters
   - Business rule violations

2. **Concurrency Issues**
   - Optimistic concurrency control for inventory updates
   - Retry mechanism for transient failures

3. **System Errors**
   - Database connection issues
   - External service failures

## Example Usage

```typescript
// Create new inventory item
const createCommand = {
  sku: 'PROD-12345',
  productId: '8f7e6d5c-4b3a-2a1b-9c8d-7e6f5d4c3b2a',
  name: 'Premium Widget',
  warehouseId: 'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
  initialQuantity: 100,
  reorderThreshold: 20,
  targetStockLevel: 120
};

const inventoryItem = await inventoryService.createInventoryItem(createCommand);

// Add stock to inventory
const addStockCommand = {
  inventoryItemId: inventoryItem.id,
  warehouseId: inventoryItem.warehouseId,
  quantity: 50,
  referenceNumber: 'PO-98765',
  referenceType: 'PURCHASE_ORDER'
};

const transaction = await inventoryService.addStock(addStockCommand);
```