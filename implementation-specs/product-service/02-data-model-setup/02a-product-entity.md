# Product Entity Model Specification

## Overview

This document details the implementation of the Product entity model, including its attributes, relationships, and business rules. The Product entity serves as the core entity in our product catalog system.

## Entity Structure

### Core Attributes

```typescript
@Entity('products')
export class Product {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    name: string;

    @Column('text')
    description: string;

    @Column()
    brand: string;

    @Column()
    status: ProductStatus;

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
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    brand VARCHAR(100),
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

## Relationships

### Product Variants (One-to-Many)
```typescript
@OneToMany(() => ProductVariant, variant => variant.product)
variants: ProductVariant[];
```

### Categories (Many-to-Many)
```typescript
@ManyToMany(() => Category)
@JoinTable({
    name: 'product_categories',
    joinColumn: { name: 'product_id', referencedColumnName: 'id' },
    inverseJoinColumn: { name: 'category_id', referencedColumnName: 'id' }
})
categories: Category[];
```

### Attributes (Many-to-Many)
```typescript
@ManyToMany(() => Attribute)
@JoinTable({
    name: 'product_attributes',
    joinColumn: { name: 'product_id', referencedColumnName: 'id' },
    inverseJoinColumn: { name: 'attribute_id', referencedColumnName: 'id' }
})
attributes: Attribute[];
```

## Business Rules

### Status Management
```typescript
export enum ProductStatus {
    DRAFT = 'draft',
    ACTIVE = 'active',
    INACTIVE = 'inactive',
    DISCONTINUED = 'discontinued'
}
```

### Validation Rules
1. **Name**
   - Required
   - Maximum length: 255 characters
   - Must be unique within the same brand

2. **Description**
   - Optional
   - Maximum length: 10,000 characters
   - Supports HTML formatting

3. **Brand**
   - Required
   - Maximum length: 100 characters
   - Must exist in the brands table

4. **Status**
   - Required
   - Must be one of: DRAFT, ACTIVE, INACTIVE, DISCONTINUED
   - Default: DRAFT

5. **Metadata**
   - Optional
   - JSONB format
   - Can include:
     - SEO information
     - Custom attributes
     - Product specifications
     - Media references

## Indexes

```sql
-- Name index for search
CREATE INDEX idx_products_name ON products(name);

-- Brand index for filtering
CREATE INDEX idx_products_brand ON products(brand);

-- Status index for filtering
CREATE INDEX idx_products_status ON products(status);

-- Created date index for sorting
CREATE INDEX idx_products_created_at ON products(created_at);

-- GIN index for metadata JSONB
CREATE INDEX idx_products_metadata ON products USING GIN (metadata);
```

## Repository Methods

```typescript
@Injectable()
export class ProductRepository {
    constructor(
        @InjectRepository(Product)
        private readonly repository: Repository<Product>
    ) {}

    async findById(id: string): Promise<Product> {
        return this.repository.findOne({
            where: { id },
            relations: ['variants', 'categories', 'attributes']
        });
    }

    async findByName(name: string): Promise<Product[]> {
        return this.repository.find({
            where: { name: ILike(`%${name}%`) },
            relations: ['variants', 'categories']
        });
    }

    async findByBrand(brand: string): Promise<Product[]> {
        return this.repository.find({
            where: { brand },
            relations: ['variants', 'categories']
        });
    }

    async findByStatus(status: ProductStatus): Promise<Product[]> {
        return this.repository.find({
            where: { status },
            relations: ['variants', 'categories']
        });
    }

    async create(product: Partial<Product>): Promise<Product> {
        const newProduct = this.repository.create(product);
        return this.repository.save(newProduct);
    }

    async update(id: string, product: Partial<Product>): Promise<Product> {
        await this.repository.update(id, product);
        return this.findById(id);
    }

    async delete(id: string): Promise<void> {
        await this.repository.delete(id);
    }
}
```

## DTOs (Data Transfer Objects)

### CreateProductDto
```typescript
export class CreateProductDto {
    @IsString()
    @IsNotEmpty()
    @MaxLength(255)
    name: string;

    @IsString()
    @MaxLength(10000)
    description?: string;

    @IsString()
    @IsNotEmpty()
    @MaxLength(100)
    brand: string;

    @IsEnum(ProductStatus)
    @IsOptional()
    status?: ProductStatus;

    @IsObject()
    @IsOptional()
    metadata?: Record<string, any>;
}
```

### UpdateProductDto
```typescript
export class UpdateProductDto {
    @IsString()
    @IsOptional()
    @MaxLength(255)
    name?: string;

    @IsString()
    @IsOptional()
    @MaxLength(10000)
    description?: string;

    @IsString()
    @IsOptional()
    @MaxLength(100)
    brand?: string;

    @IsEnum(ProductStatus)
    @IsOptional()
    status?: ProductStatus;

    @IsObject()
    @IsOptional()
    metadata?: Record<string, any>;
}
```

## Service Layer

```typescript
@Injectable()
export class ProductService {
    constructor(
        private readonly productRepository: ProductRepository,
        private readonly categoryService: CategoryService,
        private readonly attributeService: AttributeService
    ) {}

    async createProduct(createProductDto: CreateProductDto): Promise<Product> {
        // Validate brand exists
        await this.validateBrand(createProductDto.brand);

        // Create product
        const product = await this.productRepository.create(createProductDto);

        // Create audit log
        await this.createAuditLog('CREATE', product);

        return product;
    }

    async updateProduct(id: string, updateProductDto: UpdateProductDto): Promise<Product> {
        // Validate product exists
        const existingProduct = await this.productRepository.findById(id);
        if (!existingProduct) {
            throw new NotFoundException(`Product with ID ${id} not found`);
        }

        // Validate brand if being updated
        if (updateProductDto.brand) {
            await this.validateBrand(updateProductDto.brand);
        }

        // Update product
        const updatedProduct = await this.productRepository.update(id, updateProductDto);

        // Create audit log
        await this.createAuditLog('UPDATE', updatedProduct);

        return updatedProduct;
    }

    async deleteProduct(id: string): Promise<void> {
        // Validate product exists
        const product = await this.productRepository.findById(id);
        if (!product) {
            throw new NotFoundException(`Product with ID ${id} not found`);
        }

        // Delete product
        await this.productRepository.delete(id);

        // Create audit log
        await this.createAuditLog('DELETE', product);
    }

    private async validateBrand(brand: string): Promise<void> {
        // Implementation of brand validation
    }

    private async createAuditLog(action: string, product: Product): Promise<void> {
        // Implementation of audit logging
    }
}
```

## Testing Strategy

### Unit Tests

1. **Entity Tests**
   - Test entity creation with valid data
   - Test entity validation rules
   - Test entity relationships

2. **Repository Tests**
   - Test CRUD operations
   - Test custom query methods
   - Test relationship loading

3. **Service Tests**
   - Test business logic
   - Test validation rules
   - Test error handling

### Integration Tests

1. **API Tests**
   - Test product creation endpoint
   - Test product update endpoint
   - Test product deletion endpoint
   - Test product retrieval endpoints

2. **Database Tests**
   - Test database constraints
   - Test index performance
   - Test concurrent operations

## Performance Considerations

1. **Query Optimization**
   - Use appropriate indexes
   - Implement pagination for list queries
   - Use eager loading for related entities

2. **Caching Strategy**
   - Cache frequently accessed products
   - Implement cache invalidation on updates
   - Use Redis for distributed caching

3. **Bulk Operations**
   - Implement batch insert/update methods
   - Use transactions for bulk operations
   - Optimize bulk delete operations

## Security Considerations

1. **Input Validation**
   - Validate all input data
   - Sanitize HTML content
   - Prevent SQL injection

2. **Access Control**
   - Implement role-based access control
   - Validate user permissions
   - Audit all operations

3. **Data Protection**
   - Encrypt sensitive data
   - Implement data masking
   - Follow GDPR requirements

## References

- [TypeORM Documentation](https://typeorm.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [NestJS Documentation](https://docs.nestjs.com/)
- [Class Validator Documentation](https://github.com/typestack/class-validator) 