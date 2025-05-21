# Warehouse Entity

## Overview
The Warehouse entity represents a physical location where inventory items are stored. It contains information about the warehouse location, capacity, and operational parameters.

## Entity Definition

```typescript
@Entity('warehouses')
export class Warehouse {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar', length: 100, unique: true })
  code: string;

  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'text', nullable: true })
  description: string;

  @Column({ type: 'varchar', length: 255 })
  addressLine1: string;

  @Column({ type: 'varchar', length: 255, nullable: true })
  addressLine2: string;

  @Column({ type: 'varchar', length: 100 })
  city: string;

  @Column({ type: 'varchar', length: 100 })
  state: string;

  @Column({ type: 'varchar', length: 20 })
  postalCode: string;

  @Column({ type: 'varchar', length: 100 })
  country: string;

  @Column({ type: 'decimal', precision: 10, scale: 6, nullable: true })
  latitude: number;

  @Column({ type: 'decimal', precision: 10, scale: 6, nullable: true })
  longitude: number;

  @Column({ type: 'boolean', default: true })
  active: boolean;

  @Column({ type: 'int', nullable: true })
  maxCapacity: number;

  @Column({ type: 'varchar', length: 50, nullable: true })
  timeZone: string;

  @Column({ type: 'boolean', default: false })
  isPrimary: boolean;

  @Column({ type: 'boolean', default: false })
  isVirtual: boolean;

  @Column({ type: 'varchar', length: 100, nullable: true })
  contactEmail: string;

  @Column({ type: 'varchar', length: 20, nullable: true })
  contactPhone: string;

  @OneToMany(() => InventoryItem, inventoryItem => inventoryItem.warehouse)
  inventoryItems: InventoryItem[];

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  createdAt: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updatedAt: Date;

  @Column({ type: 'jsonb', nullable: true })
  operatingHours: Record<string, any>;

  @Column({ type: 'jsonb', nullable: true })
  metadata: Record<string, any>;
}
```

## Business Rules

1. **Warehouse Identification**
   - Each warehouse has a unique code within the system
   - Primary warehouses are used as default for allocation when no preference is specified

2. **Virtual Warehouses**
   - Virtual warehouses represent non-physical locations (e.g., in-transit inventory, vendor drop-ship)
   - Used for special inventory tracking purposes

3. **Warehouse Capacity**
   - `maxCapacity` represents the maximum number of SKUs the warehouse can hold
   - Used for planning and optimization purposes

4. **Geographical Information**
   - Latitude/longitude allow for distance calculations
   - Used for determining optimal fulfillment location

5. **Active Status**
   - Inactive warehouses are excluded from allocation strategies
   - Historical data is maintained even when a warehouse is deactivated

## Methods

```typescript
// Calculate current utilization percentage
calculateUtilization(): number {
  return this.inventoryItems.length / (this.maxCapacity || 1) * 100;
}

// Check if warehouse has capacity for new items
hasCapacity(): boolean {
  return !this.maxCapacity || this.inventoryItems.length < this.maxCapacity;
}

// Calculate distance to a given location (for shipping calculations)
distanceTo(lat: number, lng: number): number {
  // Haversine formula implementation for distance calculation
  // Returns distance in kilometers
}

// Check if warehouse is currently operating (based on hours)
isOperating(): boolean {
  // Logic to check if current time is within operating hours
  // Uses timeZone and operatingHours data
}
```

## Indexing Strategy

```sql
-- Index for quick lookup by warehouse code
CREATE INDEX idx_warehouses_code ON warehouses(code);

-- Index for filtering active warehouses
CREATE INDEX idx_warehouses_active ON warehouses(active);

-- Index for finding primary warehouses
CREATE INDEX idx_warehouses_primary ON warehouses(is_primary);

-- Geographic index for location-based queries
CREATE INDEX idx_warehouses_location ON warehouses(latitude, longitude);
```

## Additional Considerations

1. **Warehouse Hierarchy**
   - Support for parent-child relationships between warehouses (e.g., zones within a warehouse)
   - Will be implemented in a future version

2. **Capacity Management**
   - More granular capacity tracking (by area, shelf, bin)
   - Will be implemented in a future version

3. **Integration with WMS**
   - Standard interfaces for warehouse management system integration
   - API endpoints for real-time data synchronization