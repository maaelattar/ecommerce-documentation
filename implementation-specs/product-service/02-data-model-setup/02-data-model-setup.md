# Data Model Setup for Product Service

## Overview

This document outlines the data model setup for the Product Service, including database selection, schema design, and implementation details. The data model is designed to support the product catalog functionality while maintaining scalability and performance.

## Database Selection

For detailed information about our database technology selection and configuration, please refer to [Database Selection and Configuration](./01-database-selection.md).

## Data Model Design

### Core Entities

1. **Product**
   - Primary entity representing a product in the catalog
   - Contains basic product information and metadata
   - Links to related entities like categories, variants, and attributes

2. **ProductVariant**
   - Represents different variations of a product (e.g., sizes, colors)
   - Contains variant-specific information like SKU, price, and inventory
   - Links to the parent product

3. **Category**
   - Hierarchical structure for product categorization
   - Supports multiple levels of nesting
   - Includes metadata for display and navigation

4. **Attribute**
   - Defines product attributes (e.g., color, size, material)
   - Supports different attribute types (text, number, boolean, etc.)
   - Used for filtering and search functionality

### Relationships

1. **Product-Category**
   - Many-to-many relationship
   - A product can belong to multiple categories
   - A category can contain multiple products

2. **Product-ProductVariant**
   - One-to-many relationship
   - A product can have multiple variants
   - Each variant belongs to exactly one product

3. **Product-Attribute**
   - Many-to-many relationship
   - Products can have multiple attributes
   - Attributes can be associated with multiple products

### Schema Design

#### Product Table
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

#### ProductVariant Table
```sql
CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id),
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    inventory_quantity INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

#### Category Table
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id),
    level INTEGER NOT NULL,
    path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### ProductCategory Table (Junction)
```sql
CREATE TABLE product_categories (
    product_id UUID NOT NULL REFERENCES products(id),
    category_id UUID NOT NULL REFERENCES categories(id),
    PRIMARY KEY (product_id, category_id)
);
```

#### Attribute Table
```sql
CREATE TABLE attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### ProductAttribute Table (Junction)
```sql
CREATE TABLE product_attributes (
    product_id UUID NOT NULL REFERENCES products(id),
    attribute_id UUID NOT NULL REFERENCES attributes(id),
    value TEXT NOT NULL,
    PRIMARY KEY (product_id, attribute_id)
);
```

### Indexes

1. **Product Table**
   - Index on `status` for filtering active/inactive products
   - Index on `brand` for brand-based queries
   - Index on `created_at` for time-based queries

2. **ProductVariant Table**
   - Index on `product_id` for variant lookups
   - Index on `sku` for quick SKU lookups
   - Index on `status` for filtering active/inactive variants

3. **Category Table**
   - Index on `parent_id` for hierarchical queries
   - Index on `path` for path-based queries
   - Index on `level` for level-based queries

4. **ProductCategory Table**
   - Index on `category_id` for category-based product lookups
   - Index on `product_id` for product-based category lookups

5. **Attribute Table**
   - Index on `type` for type-based attribute queries

6. **ProductAttribute Table**
   - Index on `attribute_id` for attribute-based product lookups
   - Index on `product_id` for product-based attribute lookups

### Constraints

1. **Product Table**
   - `status` must be one of: 'active', 'inactive', 'draft'
   - `name` must not be empty
   - `price` must be positive

2. **ProductVariant Table**
   - `sku` must be unique
   - `price` must be positive
   - `inventory_quantity` must be non-negative
   - `status` must be one of: 'active', 'inactive', 'draft'

3. **Category Table**
   - `name` must not be empty
   - `level` must be positive
   - `path` must be properly formatted

4. **Attribute Table**
   - `type` must be one of: 'text', 'number', 'boolean', 'date'
   - `name` must not be empty

## Implementation Details

### TypeORM Entities

1. **Product Entity**
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

    @OneToMany(() => ProductVariant, variant => variant.product)
    variants: ProductVariant[];

    @ManyToMany(() => Category)
    @JoinTable({
        name: 'product_categories',
        joinColumn: { name: 'product_id', referencedColumnName: 'id' },
        inverseJoinColumn: { name: 'category_id', referencedColumnName: 'id' }
    })
    categories: Category[];

    @ManyToMany(() => Attribute)
    @JoinTable({
        name: 'product_attributes',
        joinColumn: { name: 'product_id', referencedColumnName: 'id' },
        inverseJoinColumn: { name: 'attribute_id', referencedColumnName: 'id' }
    })
    attributes: Attribute[];

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;
}
```

2. **ProductVariant Entity**
```typescript
@Entity('product_variants')
export class ProductVariant {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @ManyToOne(() => Product, product => product.variants)
    product: Product;

    @Column()
    sku: string;

    @Column()
    name: string;

    @Column('decimal', { precision: 10, scale: 2 })
    price: number;

    @Column()
    inventoryQuantity: number;

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

3. **Category Entity**
```typescript
@Entity('categories')
export class Category {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    name: string;

    @Column('text')
    description: string;

    @ManyToOne(() => Category)
    parent: Category;

    @Column()
    level: number;

    @Column()
    path: string;

    @ManyToMany(() => Product)
    products: Product[];

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;
}
```

4. **Attribute Entity**
```typescript
@Entity('attributes')
export class Attribute {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    name: string;

    @Column()
    type: AttributeType;

    @Column('text')
    description: string;

    @ManyToMany(() => Product)
    products: Product[];

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;
}
```

### Data Access Layer

1. **Repository Pattern**
   - Implement repositories for each entity
   - Use TypeORM's repository pattern
   - Include custom query methods for common operations

2. **Query Optimization**
   - Use eager loading for related entities when appropriate
   - Implement pagination for large result sets
   - Use query caching for frequently accessed data

3. **Transaction Management**
   - Use TypeORM's transaction support
   - Implement unit of work pattern for complex operations
   - Handle concurrent updates appropriately

## Migration Strategy

1. **Initial Migration**
   - Create all tables with proper constraints
   - Set up indexes
   - Add initial seed data

2. **Version Control**
   - Store migrations in version control
   - Use semantic versioning for migration names
   - Include rollback scripts

3. **Deployment Process**
   - Run migrations as part of deployment
   - Validate migration success
   - Monitor for any issues

## Testing Strategy

1. **Unit Tests**
   - Test entity relationships
   - Validate constraints
   - Test repository methods

2. **Integration Tests**
   - Test database operations
   - Validate transactions
   - Test concurrent access

3. **Performance Tests**
   - Test query performance
   - Validate index usage
   - Test under load

## Monitoring and Maintenance

1. **Performance Monitoring**
   - Monitor query execution times
   - Track index usage
   - Monitor connection pool usage

2. **Data Integrity**
   - Regular integrity checks
   - Monitor constraint violations
   - Track data growth

3. **Backup and Recovery**
   - Regular backups
   - Test recovery procedures
   - Monitor backup success

## References

- [TypeORM Documentation](https://typeorm.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/index.html)
- [Database Selection and Configuration](./01-database-selection.md) 