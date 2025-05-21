# Warehouse Management Service

## Overview

The Warehouse Management Service is responsible for managing warehouse information, locations, and operations within the inventory system. It provides capabilities for creating and managing warehouses, warehouse zones, and bin locations, as well as supporting operations like inventory transfers and warehouse-specific inventory rules.

## Service Interface

```typescript
export interface IWarehouseManagementService {
  // Warehouse Management
  createWarehouse(command: CreateWarehouseCommand): Promise<Warehouse>;
  updateWarehouse(command: UpdateWarehouseCommand): Promise<Warehouse>;
  deactivateWarehouse(warehouseId: string, reason: string): Promise<void>;
  
  // Zone Management
  createWarehouseZone(command: CreateWarehouseZoneCommand): Promise<WarehouseZone>;
  updateWarehouseZone(command: UpdateWarehouseZoneCommand): Promise<WarehouseZone>;
  deactivateWarehouseZone(zoneId: string, reason: string): Promise<void>;
  
  // Location Management
  createBinLocation(command: CreateBinLocationCommand): Promise<BinLocation>;
  updateBinLocation(command: UpdateBinLocationCommand): Promise<BinLocation>;
  deactivateBinLocation(locationId: string, reason: string): Promise<void>;
  
  // Warehouse Operations
  assignItemToLocation(command: AssignItemToLocationCommand): Promise<void>;
  moveItemBetweenLocations(command: MoveItemCommand): Promise<void>;
  
  // Queries
  getWarehouse(warehouseId: string): Promise<Warehouse>;
  listWarehouses(filters?: WarehouseFilters): Promise<Warehouse[]>;
  getWarehouseZones(warehouseId: string): Promise<WarehouseZone[]>;
  getBinLocations(warehouseId: string, zoneId?: string): Promise<BinLocation[]>;
  getItemLocations(inventoryItemId: string, warehouseId?: string): Promise<ItemLocationInfo[]>;
}
```

## Implementation

```typescript
@Injectable()
export class WarehouseManagementService implements IWarehouseManagementService {
  constructor(
    private readonly warehouseRepository: IWarehouseRepository,
    private readonly warehouseZoneRepository: IWarehouseZoneRepository,
    private readonly binLocationRepository: IBinLocationRepository,
    private readonly itemLocationRepository: IItemLocationRepository,
    private readonly eventPublisher: IEventPublisher,
    private readonly eventStore: IEventStore,
    private readonly logger: Logger
  ) {}

  // Implementation of interface methods...
}
```

## CQRS Commands

### CreateWarehouseCommand
```typescript
export class CreateWarehouseCommand {
  readonly name: string;
  readonly code: string;
  readonly address: WarehouseAddress;
  readonly type: WarehouseType; // DISTRIBUTION, FULFILLMENT, STORE, etc.
  readonly isActive: boolean;
  readonly metadata?: Record<string, any>;
}
```

### CreateWarehouseZoneCommand
```typescript
export class CreateWarehouseZoneCommand {
  readonly warehouseId: string;
  readonly name: string;
  readonly code: string;
  readonly description?: string;
  readonly zoneType: ZoneType; // PICKING, STORAGE, RECEIVING, SHIPPING, etc.
  readonly metadata?: Record<string, any>;
}
```

### CreateBinLocationCommand
```typescript
export class CreateBinLocationCommand {
  readonly warehouseId: string;
  readonly zoneId: string;
  readonly locationCode: string;
  readonly locationType: LocationType; // SHELF, RACK, BIN, PALLET, etc.
  readonly position?: {
    aisle: string;
    rack: string;
    level: string;
    position: string;
  };
  readonly capacity?: {
    maxWeight?: number;
    maxVolume?: number;
    maxItems?: number;
  };
  readonly metadata?: Record<string, any>;
}
```

### AssignItemToLocationCommand
```typescript
export class AssignItemToLocationCommand {
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly locationId: string;
  readonly quantity: number;
  readonly reason?: string;
  readonly metadata?: Record<string, any>;
}
```

### MoveItemCommand
```typescript
export class MoveItemCommand {
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly sourceLocationId: string;
  readonly destinationLocationId: string;
  readonly quantity: number;
  readonly reason?: string;
  readonly metadata?: Record<string, any>;
}
```

## Domain Objects

### Warehouse
```typescript
export interface Warehouse {
  id: string;
  name: string;
  code: string;
  address: WarehouseAddress;
  type: WarehouseType;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}
```

### WarehouseZone
```typescript
export interface WarehouseZone {
  id: string;
  warehouseId: string;
  name: string;
  code: string;
  description?: string;
  zoneType: ZoneType;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}
```

### BinLocation
```typescript
export interface BinLocation {
  id: string;
  warehouseId: string;
  zoneId: string;
  locationCode: string;
  locationType: LocationType;
  position?: {
    aisle: string;
    rack: string;
    level: string;
    position: string;
  };
  capacity?: {
    maxWeight?: number;
    maxVolume?: number;
    maxItems?: number;
  };
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}
```

## Business Rules

1. **Warehouse Rules**
   - Warehouse codes must be unique within the system
   - A warehouse must be active to perform operations
   - Warehouses have associated address and contact information

2. **Zone Rules**
   - Zone codes must be unique within a warehouse
   - Zones must be associated with an active warehouse
   - Certain zone types may have special handling rules

3. **Location Rules**
   - Location codes must be unique within a zone
   - Locations can have capacity constraints (weight, volume, items)
   - Items can be assigned to multiple locations within a warehouse

4. **Item Placement Rules**
   - Certain items may be restricted to specific zone types
   - Capacity constraints must be respected when placing items
   - Some items may require specialized storage conditions

## Domain Events

### WarehouseCreatedEvent
```typescript
export class WarehouseCreatedEvent {
  readonly warehouseId: string;
  readonly name: string;
  readonly code: string;
  readonly type: WarehouseType;
  readonly timestamp: Date;
}
```

### ItemAssignedToLocationEvent
```typescript
export class ItemAssignedToLocationEvent {
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly locationId: string;
  readonly locationCode: string;
  readonly quantity: number;
  readonly timestamp: Date;
}
```

### ItemMovedEvent
```typescript
export class ItemMovedEvent {
  readonly inventoryItemId: string;
  readonly warehouseId: string;
  readonly sourceLocationId: string;
  readonly destinationLocationId: string;
  readonly quantity: number;
  readonly timestamp: Date;
}
```

## Warehouse Types and Specifications

The service supports different warehouse types with specific characteristics:

1. **Distribution Center**
   - Large-scale storage and distribution
   - Multiple zones for different product types
   - High-volume handling capabilities
   - Often includes automated systems

2. **Fulfillment Center**
   - Focused on order processing and fulfillment
   - Optimized picking and packing zones
   - Often closer to end customers
   - Emphasis on fast turnover

3. **Retail Store Warehouse**
   - Supports retail operations
   - Limited storage capacity
   - Often has both back-of-house storage and retail floor
   - Emphasis on visual merchandising needs

4. **Dark Store**
   - Retail-like layout but for online order fulfillment
   - No customer access
   - Optimized for picking efficiency
   - Often used for rapid local delivery

## Example Usage

```typescript
// Create a new warehouse
const createWarehouseCommand = {
  name: 'North Seattle Fulfillment Center',
  code: 'NSFC',
  address: {
    street: '123 Distribution Way',
    city: 'Seattle',
    state: 'WA',
    postalCode: '98101',
    country: 'USA'
  },
  type: 'FULFILLMENT',
  isActive: true
};

const warehouse = await warehouseService.createWarehouse(createWarehouseCommand);

// Create a zone in the warehouse
const createZoneCommand = {
  warehouseId: warehouse.id,
  name: 'Electronics Picking Zone',
  code: 'EPZ',
  description: 'Zone for picking electronic items',
  zoneType: 'PICKING'
};

const zone = await warehouseService.createWarehouseZone(createZoneCommand);

// Create a bin location
const createLocationCommand = {
  warehouseId: warehouse.id,
  zoneId: zone.id,
  locationCode: 'EPZ-A01-R01-L01-P01',
  locationType: 'SHELF',
  position: {
    aisle: 'A01',
    rack: 'R01',
    level: 'L01',
    position: 'P01'
  }
};

const location = await warehouseService.createBinLocation(createLocationCommand);

// Assign an item to the location
const assignCommand = {
  inventoryItemId: '1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d',
  warehouseId: warehouse.id,
  locationId: location.id,
  quantity: 10
};

await warehouseService.assignItemToLocation(assignCommand);
```