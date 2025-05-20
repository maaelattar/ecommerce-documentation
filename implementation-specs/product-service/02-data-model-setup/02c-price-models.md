# Price and Discount Models Specification

## Overview

This document details the implementation of price and discount models for the Product Service. It covers the base price structure, discount and promotion models, and pricing history tracking.

## Price Models

### Base Price Structure

```typescript
@Entity('product_prices')
export class ProductPrice {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @ManyToOne(() => ProductVariant)
    productVariant: ProductVariant;

    @Column('decimal', { precision: 10, scale: 2 })
    basePrice: number;

    @Column('decimal', { precision: 10, scale: 2 })
    salePrice: number;

    @Column('decimal', { precision: 10, scale: 2 })
    msrp: number;

    @Column()
    currency: string;

    @Column()
    priceType: PriceType;

    @Column('jsonb')
    metadata: Record<string, any>;

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;
}
```

### Database Schema

```sql
CREATE TABLE product_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_variant_id UUID NOT NULL REFERENCES product_variants(id),
    base_price DECIMAL(10,2) NOT NULL,
    sale_price DECIMAL(10,2) NOT NULL,
    msrp DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    price_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_price_id UUID NOT NULL REFERENCES product_prices(id),
    base_price DECIMAL(10,2) NOT NULL,
    sale_price DECIMAL(10,2) NOT NULL,
    msrp DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    price_type VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_by UUID NOT NULL,
    change_reason TEXT
);
```

## Discount Models

### Discount Structure

```typescript
@Entity('discounts')
export class Discount {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    name: string;

    @Column('text')
    description: string;

    @Column()
    type: DiscountType;

    @Column('decimal', { precision: 5, scale: 2 })
    value: number;

    @Column()
    startDate: Date;

    @Column()
    endDate: Date;

    @Column()
    status: DiscountStatus;

    @Column('jsonb')
    conditions: Record<string, any>;

    @Column('jsonb')
    metadata: Record<string, any>;

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;
}
```

### Database Schema

```sql
CREATE TABLE discounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(20) NOT NULL,
    value DECIMAL(5,2) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL,
    conditions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE product_discounts (
    product_variant_id UUID NOT NULL REFERENCES product_variants(id),
    discount_id UUID NOT NULL REFERENCES discounts(id),
    priority INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_variant_id, discount_id)
);
```

## Business Rules

### Price Rules

1. **Base Price**
   - Required
   - Must be positive
   - Maximum precision: 2 decimal places
   - Must be less than or equal to MSRP

2. **Sale Price**
   - Required
   - Must be positive
   - Maximum precision: 2 decimal places
   - Must be less than or equal to base price

3. **MSRP (Manufacturer's Suggested Retail Price)**
   - Required
   - Must be positive
   - Maximum precision: 2 decimal places
   - Must be greater than or equal to base price

4. **Currency**
   - Required
   - Must be a valid ISO 4217 currency code
   - Default: USD

5. **Price Type**
   - Required
   - Must be one of: REGULAR, SALE, CLEARANCE, PROMOTIONAL

### Discount Rules

1. **Discount Types**
   ```typescript
   export enum DiscountType {
       PERCENTAGE = 'percentage',
       FIXED_AMOUNT = 'fixed_amount',
       FREE_SHIPPING = 'free_shipping',
       BUY_X_GET_Y = 'buy_x_get_y'
   }
   ```

2. **Discount Status**
   ```typescript
   export enum DiscountStatus {
       DRAFT = 'draft',
       ACTIVE = 'active',
       PAUSED = 'paused',
       EXPIRED = 'expired'
   }
   ```

3. **Validation Rules**
   - Name must be unique
   - Value must be positive
   - For percentage discounts: value must be <= 100
   - Start date must be before end date
   - Cannot overlap with existing discounts for the same product

## Indexes

```sql
-- Price indexes
CREATE INDEX idx_product_prices_variant ON product_prices(product_variant_id);
CREATE INDEX idx_product_prices_currency ON product_prices(currency);
CREATE INDEX idx_product_prices_type ON product_prices(price_type);

-- Price history indexes
CREATE INDEX idx_price_history_price ON price_history(product_price_id);
CREATE INDEX idx_price_history_changed_at ON price_history(changed_at);

-- Discount indexes
CREATE INDEX idx_discounts_status ON discounts(status);
CREATE INDEX idx_discounts_dates ON discounts(start_date, end_date);
CREATE INDEX idx_discounts_type ON discounts(type);

-- Product discount indexes
CREATE INDEX idx_product_discounts_variant ON product_discounts(product_variant_id);
CREATE INDEX idx_product_discounts_priority ON product_discounts(priority);
```

## Repository Methods

### Price Repository

```typescript
@Injectable()
export class PriceRepository {
    constructor(
        @InjectRepository(ProductPrice)
        private readonly repository: Repository<ProductPrice>
    ) {}

    async findByProductVariant(variantId: string): Promise<ProductPrice> {
        return this.repository.findOne({
            where: { productVariant: { id: variantId } }
        });
    }

    async updatePrice(id: string, price: Partial<ProductPrice>): Promise<ProductPrice> {
        await this.repository.update(id, price);
        return this.findById(id);
    }

    async getPriceHistory(priceId: string): Promise<PriceHistory[]> {
        return this.priceHistoryRepository.find({
            where: { productPrice: { id: priceId } },
            order: { changedAt: 'DESC' }
        });
    }
}
```

### Discount Repository

```typescript
@Injectable()
export class DiscountRepository {
    constructor(
        @InjectRepository(Discount)
        private readonly repository: Repository<Discount>
    ) {}

    async findActiveDiscounts(): Promise<Discount[]> {
        const now = new Date();
        return this.repository.find({
            where: {
                status: DiscountStatus.ACTIVE,
                startDate: LessThanOrEqual(now),
                endDate: MoreThanOrEqual(now)
            }
        });
    }

    async findProductDiscounts(variantId: string): Promise<Discount[]> {
        return this.repository
            .createQueryBuilder('discount')
            .innerJoin('product_discounts', 'pd', 'pd.discount_id = discount.id')
            .where('pd.product_variant_id = :variantId', { variantId })
            .andWhere('discount.status = :status', { status: DiscountStatus.ACTIVE })
            .orderBy('pd.priority', 'ASC')
            .getMany();
    }
}
```

## Service Layer

### Price Service

```typescript
@Injectable()
export class PriceService {
    constructor(
        private readonly priceRepository: PriceRepository,
        private readonly priceHistoryRepository: PriceHistoryRepository
    ) {}

    async updatePrice(id: string, updatePriceDto: UpdatePriceDto): Promise<ProductPrice> {
        const existingPrice = await this.priceRepository.findById(id);
        if (!existingPrice) {
            throw new NotFoundException(`Price with ID ${id} not found`);
        }

        // Validate price rules
        await this.validatePriceRules(updatePriceDto);

        // Create price history entry
        await this.createPriceHistory(existingPrice);

        // Update price
        const updatedPrice = await this.priceRepository.updatePrice(id, updatePriceDto);

        // Create audit log
        await this.createAuditLog('UPDATE', updatedPrice);

        return updatedPrice;
    }

    async calculateFinalPrice(variantId: string): Promise<number> {
        const price = await this.priceRepository.findByProductVariant(variantId);
        const discounts = await this.discountRepository.findProductDiscounts(variantId);

        let finalPrice = price.basePrice;
        for (const discount of discounts) {
            finalPrice = this.applyDiscount(finalPrice, discount);
        }

        return Math.max(finalPrice, 0);
    }

    private async validatePriceRules(price: Partial<ProductPrice>): Promise<void> {
        // Implementation of price validation rules
    }

    private async createPriceHistory(price: ProductPrice): Promise<void> {
        // Implementation of price history creation
    }
}
```

### Discount Service

```typescript
@Injectable()
export class DiscountService {
    constructor(
        private readonly discountRepository: DiscountRepository,
        private readonly productService: ProductService
    ) {}

    async createDiscount(createDiscountDto: CreateDiscountDto): Promise<Discount> {
        // Validate discount rules
        await this.validateDiscountRules(createDiscountDto);

        // Create discount
        const discount = await this.discountRepository.create(createDiscountDto);

        // Create audit log
        await this.createAuditLog('CREATE', discount);

        return discount;
    }

    async applyDiscountToProduct(
        discountId: string,
        variantId: string,
        priority: number
    ): Promise<void> {
        // Validate discount and product exist
        const [discount, variant] = await Promise.all([
            this.discountRepository.findById(discountId),
            this.productService.findVariantById(variantId)
        ]);

        if (!discount || !variant) {
            throw new NotFoundException('Discount or product not found');
        }

        // Apply discount to product
        await this.discountRepository.addProductDiscount(discountId, variantId, priority);

        // Create audit log
        await this.createAuditLog('APPLY', { discount, variant });
    }

    private async validateDiscountRules(discount: Partial<Discount>): Promise<void> {
        // Implementation of discount validation rules
    }
}
```

## Testing Strategy

### Unit Tests

1. **Price Tests**
   - Test price creation and validation
   - Test price history tracking
   - Test price calculations
   - Test currency handling

2. **Discount Tests**
   - Test discount creation and validation
   - Test discount application
   - Test discount priority
   - Test discount expiration

3. **Service Tests**
   - Test price update logic
   - Test discount application logic
   - Test final price calculation
   - Test error handling

### Integration Tests

1. **Price Integration Tests**
   - Test price updates with history
   - Test concurrent price updates
   - Test price validation rules
   - Test price calculations

2. **Discount Integration Tests**
   - Test discount application
   - Test multiple discounts
   - Test discount expiration
   - Test discount conflicts

## Performance Considerations

1. **Price Calculations**
   - Cache calculated prices
   - Optimize discount queries
   - Use appropriate indexes
   - Implement batch processing

2. **Discount Management**
   - Cache active discounts
   - Optimize discount queries
   - Use appropriate indexes
   - Implement batch processing

3. **History Tracking**
   - Implement efficient history storage
   - Optimize history queries
   - Implement data archival
   - Use appropriate indexes

## Security Considerations

1. **Price Protection**
   - Validate price changes
   - Audit price history
   - Protect price data
   - Implement access control

2. **Discount Protection**
   - Validate discount rules
   - Audit discount usage
   - Protect discount data
   - Implement access control

## References

- [TypeORM Documentation](https://typeorm.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [NestJS Documentation](https://docs.nestjs.com/)
- [Class Validator Documentation](https://github.com/typestack/class-validator) 