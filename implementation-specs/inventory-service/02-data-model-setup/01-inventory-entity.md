# Inventory Entity Model Specification

## Overview

This document details the implementation of the inventory management system for the Product Service. It covers inventory tracking, stock management, and inventory history.

## Entity Structure

### Inventory Entity

```typescript
@Entity('inventory')
export class Inventory {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @ManyToOne(() => ProductVariant)
    productVariant: ProductVariant;

    @Column('int')
    quantity: number;

    @Column('int')
    reservedQuantity: number;

    @Column('int')
    availableQuantity: number;

    @Column()
    status: InventoryStatus;

    @Column('jsonb')
    metadata: Record<string, any>;

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;
}
```

### Inventory History Entity

```typescript
@Entity('inventory_history')
export class InventoryHistory {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @ManyToOne(() => Inventory)
    inventory: Inventory;

    @Column('int')
    previousQuantity: number;

    @Column('int')
    newQuantity: number;

    @Column('int')
    quantityChange: number;

    @Column()
    changeType: InventoryChangeType;

    @Column('text')
    changeReason: string;

    @Column('uuid')
    changedBy: string;

    @CreateDateColumn()
    createdAt: Date;
}
```

## Database Schema

```sql
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_variant_id UUID NOT NULL REFERENCES product_variants(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    available_quantity INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT positive_quantity CHECK (quantity >= 0),
    CONSTRAINT positive_reserved CHECK (reserved_quantity >= 0),
    CONSTRAINT valid_available CHECK (available_quantity >= 0)
);

CREATE TABLE inventory_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID NOT NULL REFERENCES inventory(id),
    previous_quantity INTEGER NOT NULL,
    new_quantity INTEGER NOT NULL,
    quantity_change INTEGER NOT NULL,
    change_type VARCHAR(20) NOT NULL,
    change_reason TEXT,
    changed_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Business Rules

### Inventory Status

```typescript
export enum InventoryStatus {
    IN_STOCK = 'in_stock',
    LOW_STOCK = 'low_stock',
    OUT_OF_STOCK = 'out_of_stock',
    DISCONTINUED = 'discontinued'
}
```

### Inventory Change Types

```typescript
export enum InventoryChangeType {
    PURCHASE = 'purchase',
    SALE = 'sale',
    RETURN = 'return',
    ADJUSTMENT = 'adjustment',
    RESERVATION = 'reservation',
    CANCELLATION = 'cancellation'
}
```

### Validation Rules

1. **Quantity Rules**
   - All quantities must be non-negative
   - Available quantity = quantity - reserved quantity
   - Cannot reserve more than available quantity
   - Cannot have negative available quantity

2. **Status Rules**
   - IN_STOCK: quantity > low stock threshold
   - LOW_STOCK: quantity <= low stock threshold
   - OUT_OF_STOCK: quantity = 0
   - DISCONTINUED: manually set

3. **History Rules**
   - Every quantity change must be recorded
   - Must include reason for change
   - Must track who made the change
   - Must maintain audit trail

## Indexes

```sql
-- Inventory indexes
CREATE INDEX idx_inventory_variant ON inventory(product_variant_id);
CREATE INDEX idx_inventory_status ON inventory(status);
CREATE INDEX idx_inventory_available ON inventory(available_quantity);

-- Inventory history indexes
CREATE INDEX idx_inventory_history_inventory ON inventory_history(inventory_id);
CREATE INDEX idx_inventory_history_type ON inventory_history(change_type);
CREATE INDEX idx_inventory_history_date ON inventory_history(created_at);
```

## Repository Methods

### Inventory Repository

```typescript
@Injectable()
export class InventoryRepository {
    constructor(
        @InjectRepository(Inventory)
        private readonly repository: Repository<Inventory>
    ) {}

    async findByProductVariant(variantId: string): Promise<Inventory> {
        return this.repository.findOne({
            where: { productVariant: { id: variantId } }
        });
    }

    async updateQuantity(
        id: string,
        quantityChange: number,
        changeType: InventoryChangeType,
        reason: string,
        userId: string
    ): Promise<Inventory> {
        const inventory = await this.findById(id);
        if (!inventory) {
            throw new NotFoundException(`Inventory with ID ${id} not found`);
        }

        // Create history entry
        await this.createHistoryEntry(inventory, quantityChange, changeType, reason, userId);

        // Update inventory
        const newQuantity = inventory.quantity + quantityChange;
        await this.repository.update(id, {
            quantity: newQuantity,
            availableQuantity: newQuantity - inventory.reservedQuantity,
            status: this.calculateStatus(newQuantity)
        });

        return this.findById(id);
    }

    async reserveQuantity(
        id: string,
        quantity: number,
        userId: string
    ): Promise<Inventory> {
        const inventory = await this.findById(id);
        if (!inventory) {
            throw new NotFoundException(`Inventory with ID ${id} not found`);
        }

        if (inventory.availableQuantity < quantity) {
            throw new BadRequestException('Insufficient available quantity');
        }

        // Create history entry
        await this.createHistoryEntry(
            inventory,
            -quantity,
            InventoryChangeType.RESERVATION,
            'Order reservation',
            userId
        );

        // Update inventory
        await this.repository.update(id, {
            reservedQuantity: inventory.reservedQuantity + quantity,
            availableQuantity: inventory.availableQuantity - quantity
        });

        return this.findById(id);
    }

    private async createHistoryEntry(
        inventory: Inventory,
        quantityChange: number,
        changeType: InventoryChangeType,
        reason: string,
        userId: string
    ): Promise<void> {
        await this.historyRepository.save({
            inventory,
            previousQuantity: inventory.quantity,
            newQuantity: inventory.quantity + quantityChange,
            quantityChange,
            changeType,
            changeReason: reason,
            changedBy: userId
        });
    }

    private calculateStatus(quantity: number): InventoryStatus {
        if (quantity === 0) return InventoryStatus.OUT_OF_STOCK;
        if (quantity <= this.lowStockThreshold) return InventoryStatus.LOW_STOCK;
        return InventoryStatus.IN_STOCK;
    }
}
```

## Service Layer

### Inventory Service

```typescript
@Injectable()
export class InventoryService {
    constructor(
        private readonly inventoryRepository: InventoryRepository,
        private readonly productService: ProductService
    ) {}

    async updateInventory(
        variantId: string,
        updateInventoryDto: UpdateInventoryDto
    ): Promise<Inventory> {
        const inventory = await this.inventoryRepository.findByProductVariant(variantId);
        if (!inventory) {
            throw new NotFoundException(`Inventory for variant ${variantId} not found`);
        }

        // Validate update
        await this.validateInventoryUpdate(inventory, updateInventoryDto);

        // Update inventory
        const updatedInventory = await this.inventoryRepository.updateQuantity(
            inventory.id,
            updateInventoryDto.quantityChange,
            updateInventoryDto.changeType,
            updateInventoryDto.reason,
            updateInventoryDto.userId
        );

        // Create audit log
        await this.createAuditLog('UPDATE', updatedInventory);

        return updatedInventory;
    }

    async checkAvailability(
        variantId: string,
        quantity: number
    ): Promise<boolean> {
        const inventory = await this.inventoryRepository.findByProductVariant(variantId);
        if (!inventory) {
            throw new NotFoundException(`Inventory for variant ${variantId} not found`);
        }

        return inventory.availableQuantity >= quantity;
    }

    async getInventoryHistory(
        variantId: string,
        options: InventoryHistoryOptions
    ): Promise<InventoryHistory[]> {
        const inventory = await this.inventoryRepository.findByProductVariant(variantId);
        if (!inventory) {
            throw new NotFoundException(`Inventory for variant ${variantId} not found`);
        }

        return this.inventoryRepository.getHistory(inventory.id, options);
    }

    private async validateInventoryUpdate(
        inventory: Inventory,
        update: UpdateInventoryDto
    ): Promise<void> {
        // Implementation of inventory update validation
    }
}
```

## Testing Strategy

### Unit Tests

1. **Inventory Tests**
   - Test inventory creation
   - Test quantity updates
   - Test status calculations
   - Test validation rules

2. **History Tests**
   - Test history creation
   - Test history queries
   - Test audit trail
   - Test change tracking

3. **Service Tests**
   - Test inventory updates
   - Test availability checks
   - Test history retrieval
   - Test error handling

### Integration Tests

1. **Inventory Integration Tests**
   - Test concurrent updates
   - Test reservation system
   - Test status transitions
   - Test validation rules

2. **History Integration Tests**
   - Test history tracking
   - Test audit trail
   - Test concurrent changes
   - Test data consistency

## Performance Considerations

1. **Inventory Management**
   - Cache inventory status
   - Optimize quantity updates
   - Use appropriate indexes
   - Implement batch processing

2. **History Tracking**
   - Implement efficient history storage
   - Optimize history queries
   - Implement data archival
   - Use appropriate indexes

3. **Availability Checks**
   - Cache availability status
   - Optimize availability queries
   - Implement batch checks
   - Use appropriate indexes

## Security Considerations

1. **Inventory Protection**
   - Validate inventory changes
   - Audit inventory history
   - Protect inventory data
   - Implement access control

2. **History Protection**
   - Validate history entries
   - Audit history changes
   - Protect history data
   - Implement access control

## References

- [TypeORM Documentation](https://typeorm.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [NestJS Documentation](https://docs.nestjs.com/)
- [Class Validator Documentation](https://github.com/typestack/class-validator) 