# Allocation Management Service

## Overview

The Allocation Management Service handles the reservation and allocation of inventory for customer orders. It manages the lifecycle of allocations from creation through confirmation, fulfillment, or cancellation while ensuring inventory availability and consistency.

## Service Interface

```typescript
export interface IAllocationManagementService {
  // Allocation Creation
  createAllocation(command: CreateAllocationCommand): Promise<AllocationResult>;
  createBulkAllocations(command: CreateBulkAllocationsCommand): Promise<BulkAllocationResult>;
  
  // Allocation Lifecycle
  confirmAllocation(allocationId: string): Promise<void>;
  cancelAllocation(allocationId: string, reason: string): Promise<void>;
  fulfillAllocation(allocationId: string): Promise<void>;
  
  // Allocation Management
  updateAllocationQuantity(command: UpdateAllocationQuantityCommand): Promise<AllocationResult>;
  transferAllocation(command: TransferAllocationCommand): Promise<AllocationResult>;
  
  // Queries
  getAllocationsByOrder(orderId: string): Promise<InventoryAllocation[]>;
  getAllocationStatus(allocationId: string): Promise<AllocationStatusResult>;
  checkExpiredAllocations(): Promise<ExpiredAllocationResult[]>;
}
```

## Implementation

```typescript
@Injectable()
export class AllocationManagementService implements IAllocationManagementService {
  constructor(
    private readonly allocationRepository: IAllocationRepository,
    private readonly inventoryItemRepository: IInventoryItemRepository,
    private readonly inventoryManagementService: IInventoryManagementService,
    private readonly eventPublisher: IEventPublisher,
    private readonly eventStore: IEventStore,
    private readonly logger: Logger
  ) {}

  // Implementation of interface methods...
}
```

## CQRS Commands

### CreateAllocationCommand
```typescript
export class CreateAllocationCommand {
  readonly orderId: string;
  readonly orderItemId: string;
  readonly inventoryItemId: string;
  readonly quantity: number;
  readonly warehouseId?: string; // Optional - will use optimal warehouse if not specified
  readonly expiresAt?: Date; // Optional - will use default expiry if not specified
  readonly metadata?: Record<string, any>;
}
```

### CreateBulkAllocationsCommand
```typescript
export class CreateBulkAllocationsCommand {
  readonly orderId: string;
  readonly items: {
    orderItemId: string;
    inventoryItemId: string;
    quantity: number;
  }[];
  readonly warehouseId?: string;
  readonly expiresAt?: Date;
  readonly metadata?: Record<string, any>;
}
```

### UpdateAllocationQuantityCommand
```typescript
export class UpdateAllocationQuantityCommand {
  readonly allocationId: string;
  readonly newQuantity: number;
  readonly reason: string;
}
```

### TransferAllocationCommand
```typescript
export class TransferAllocationCommand {
  readonly allocationId: string;
  readonly newWarehouseId: string;
  readonly reason: string;
}
```

## Allocation Workflow

The allocation process follows these steps:

1. **Allocation Creation**
   - Check inventory availability
   - Create PENDING allocation
   - Reserve inventory quantity
   - Publish AllocationCreatedEvent

2. **Allocation Confirmation**
   - Change allocation status to CONFIRMED
   - Update expiry date (remove or extend)
   - Publish AllocationConfirmedEvent

3. **Allocation Fulfillment**
   - Change allocation status to FULFILLED
   - Deduct inventory from warehouse
   - Create SALE transaction
   - Publish AllocationFulfilledEvent

4. **Allocation Cancellation**
   - Change allocation status to CANCELLED
   - Release reserved inventory
   - Publish AllocationCancelledEvent

## Allocation Strategies

The service supports multiple allocation strategies that can be configured:

1. **Default Strategy**
   - Allocate from a single warehouse with sufficient inventory
   - Fail if no single warehouse can fulfill the allocation

2. **Split Allocation Strategy**
   - Allow allocation from multiple warehouses
   - Prioritize warehouses based on rules (proximity, cost, etc.)

3. **Backorder Strategy**
   - Allow allocation even when insufficient inventory exists
   - Create backorder records for tracking

4. **Prioritized Allocation Strategy**
   - Allocate based on customer tiers or order priority
   - May preempt existing allocations for high-priority orders

## Domain Events

### AllocationCreatedEvent
```typescript
export class AllocationCreatedEvent {
  readonly allocationId: string;
  readonly orderId: string;
  readonly orderItemId: string;
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly quantity: number;
  readonly expiresAt: Date;
  readonly timestamp: Date;
}
```

### AllocationConfirmedEvent
```typescript
export class AllocationConfirmedEvent {
  readonly allocationId: string;
  readonly orderId: string;
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly quantity: number;
  readonly timestamp: Date;
}
```

### AllocationCancelledEvent
```typescript
export class AllocationCancelledEvent {
  readonly allocationId: string;
  readonly orderId: string;
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly quantity: number;
  readonly reason: string;
  readonly timestamp: Date;
}
```

### AllocationFulfilledEvent
```typescript
export class AllocationFulfilledEvent {
  readonly allocationId: string;
  readonly orderId: string;
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly quantity: number;
  readonly timestamp: Date;
}
```

## Business Rules

1. **Allocation Creation Rules**
   - Cannot allocate more than available inventory (unless backorder is enabled)
   - Order must not already have an active allocation for the same item
   - Inventory item must be active

2. **Allocation Update Rules**
   - Cannot increase allocation quantity beyond available inventory
   - Only PENDING or CONFIRMED allocations can be updated

3. **Allocation Transfer Rules**
   - Destination warehouse must have sufficient inventory
   - Only PENDING or CONFIRMED allocations can be transferred

4. **Allocation Expiry Rules**
   - Pending allocations expire after a configurable period (default: 24 hours)
   - Expired allocations are automatically cancelled and inventory is released

## Example Usage

```typescript
// Create an allocation for an order
const createCommand = {
  orderId: 'ORD-123456',
  orderItemId: 'ITEM-789012',
  inventoryItemId: '3e4f5a6b-7c8d-9e0f-1a2b-3c4d5e6f7a8b',
  quantity: 2
};

const result = await allocationService.createAllocation(createCommand);

// Confirm the allocation when payment is processed
await allocationService.confirmAllocation(result.allocationId);

// Fulfill the allocation when order is shipped
await allocationService.fulfillAllocation(result.allocationId);
```