# Category Entity Model Specification

## Overview

This document details the implementation of the Category entity model, including its hierarchical structure, relationships, and business rules. The Category entity is used to organize products in a hierarchical taxonomy.

## Entity Structure

### Core Attributes

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
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id),
    level INTEGER NOT NULL,
    path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

## Relationships

### Parent-Child Relationship (Self-Referential)
```typescript
@ManyToOne(() => Category)
parent: Category;

@OneToMany(() => Category, category => category.parent)
children: Category[];
```

### Products (Many-to-Many)
```typescript
@ManyToMany(() => Product)
@JoinTable({
    name: 'product_categories',
    joinColumn: { name: 'category_id', referencedColumnName: 'id' },
    inverseJoinColumn: { name: 'product_id', referencedColumnName: 'id' }
})
products: Product[];
```

## Business Rules

### Hierarchy Management
1. **Level Calculation**
   - Root categories have level 1
   - Child categories have level = parent.level + 1
   - Maximum level depth: 5

2. **Path Management**
   - Root categories: path = '/{id}'
   - Child categories: path = '{parent.path}/{id}'
   - Used for efficient tree traversal

3. **Validation Rules**
   - Name must be unique within the same parent
   - Cannot create circular references
   - Cannot move category to its own descendant

### Validation Rules
1. **Name**
   - Required
   - Maximum length: 100 characters
   - Must be unique within the same parent

2. **Description**
   - Optional
   - Maximum length: 1000 characters
   - Supports HTML formatting

3. **Parent**
   - Optional (null for root categories)
   - Must reference a valid category
   - Cannot reference self or descendants

4. **Level**
   - Required
   - Must be between 1 and 5
   - Automatically calculated based on parent

5. **Path**
   - Required
   - Must be properly formatted
   - Automatically generated based on hierarchy

6. **Metadata**
   - Optional
   - JSONB format
   - Can include:
     - SEO information
     - Display preferences
     - Custom attributes

## Indexes

```sql
-- Name index for search
CREATE INDEX idx_categories_name ON categories(name);

-- Parent index for hierarchy queries
CREATE INDEX idx_categories_parent_id ON categories(parent_id);

-- Path index for tree traversal
CREATE INDEX idx_categories_path ON categories(path);

-- Level index for level-based queries
CREATE INDEX idx_categories_level ON categories(level);

-- GIN index for metadata JSONB
CREATE INDEX idx_categories_metadata ON categories USING GIN (metadata);
```

## Repository Methods

```typescript
@Injectable()
export class CategoryRepository {
    constructor(
        @InjectRepository(Category)
        private readonly repository: Repository<Category>
    ) {}

    async findById(id: string): Promise<Category> {
        return this.repository.findOne({
            where: { id },
            relations: ['parent', 'children', 'products']
        });
    }

    async findByName(name: string): Promise<Category[]> {
        return this.repository.find({
            where: { name: ILike(`%${name}%`) },
            relations: ['parent', 'children']
        });
    }

    async findByParent(parentId: string): Promise<Category[]> {
        return this.repository.find({
            where: { parent: { id: parentId } },
            relations: ['children']
        });
    }

    async findRootCategories(): Promise<Category[]> {
        return this.repository.find({
            where: { parent: IsNull() },
            relations: ['children']
        });
    }

    async findDescendants(categoryId: string): Promise<Category[]> {
        const category = await this.findById(categoryId);
        return this.repository.find({
            where: { path: Like(`${category.path}/%`) }
        });
    }

    async create(category: Partial<Category>): Promise<Category> {
        const newCategory = this.repository.create(category);
        return this.repository.save(newCategory);
    }

    async update(id: string, category: Partial<Category>): Promise<Category> {
        await this.repository.update(id, category);
        return this.findById(id);
    }

    async delete(id: string): Promise<void> {
        await this.repository.delete(id);
    }

    async moveCategory(id: string, newParentId: string): Promise<Category> {
        // Implementation of category movement logic
    }
}
```

## DTOs (Data Transfer Objects)

### CreateCategoryDto
```typescript
export class CreateCategoryDto {
    @IsString()
    @IsNotEmpty()
    @MaxLength(100)
    name: string;

    @IsString()
    @MaxLength(1000)
    description?: string;

    @IsUUID()
    @IsOptional()
    parentId?: string;

    @IsObject()
    @IsOptional()
    metadata?: Record<string, any>;
}
```

### UpdateCategoryDto
```typescript
export class UpdateCategoryDto {
    @IsString()
    @IsOptional()
    @MaxLength(100)
    name?: string;

    @IsString()
    @IsOptional()
    @MaxLength(1000)
    description?: string;

    @IsUUID()
    @IsOptional()
    parentId?: string;

    @IsObject()
    @IsOptional()
    metadata?: Record<string, any>;
}
```

## Service Layer

```typescript
@Injectable()
export class CategoryService {
    constructor(
        private readonly categoryRepository: CategoryRepository,
        private readonly productService: ProductService
    ) {}

    async createCategory(createCategoryDto: CreateCategoryDto): Promise<Category> {
        // Validate parent exists if provided
        if (createCategoryDto.parentId) {
            await this.validateParent(createCategoryDto.parentId);
        }

        // Create category
        const category = await this.categoryRepository.create(createCategoryDto);

        // Create audit log
        await this.createAuditLog('CREATE', category);

        return category;
    }

    async updateCategory(id: string, updateCategoryDto: UpdateCategoryDto): Promise<Category> {
        // Validate category exists
        const existingCategory = await this.categoryRepository.findById(id);
        if (!existingCategory) {
            throw new NotFoundException(`Category with ID ${id} not found`);
        }

        // Validate parent if being updated
        if (updateCategoryDto.parentId) {
            await this.validateParent(updateCategoryDto.parentId, id);
        }

        // Update category
        const updatedCategory = await this.categoryRepository.update(id, updateCategoryDto);

        // Create audit log
        await this.createAuditLog('UPDATE', updatedCategory);

        return updatedCategory;
    }

    async deleteCategory(id: string): Promise<void> {
        // Validate category exists
        const category = await this.categoryRepository.findById(id);
        if (!category) {
            throw new NotFoundException(`Category with ID ${id} not found`);
        }

        // Check for child categories
        const children = await this.categoryRepository.findByParent(id);
        if (children.length > 0) {
            throw new BadRequestException('Cannot delete category with children');
        }

        // Check for associated products
        const products = await this.productService.findByCategory(id);
        if (products.length > 0) {
            throw new BadRequestException('Cannot delete category with associated products');
        }

        // Delete category
        await this.categoryRepository.delete(id);

        // Create audit log
        await this.createAuditLog('DELETE', category);
    }

    private async validateParent(parentId: string, excludeId?: string): Promise<void> {
        // Implementation of parent validation
    }

    private async createAuditLog(action: string, category: Category): Promise<void> {
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
   - Test hierarchy rules

2. **Repository Tests**
   - Test CRUD operations
   - Test hierarchy queries
   - Test path management
   - Test relationship loading

3. **Service Tests**
   - Test business logic
   - Test validation rules
   - Test error handling
   - Test hierarchy operations

### Integration Tests

1. **API Tests**
   - Test category creation endpoint
   - Test category update endpoint
   - Test category deletion endpoint
   - Test category retrieval endpoints
   - Test hierarchy operations

2. **Database Tests**
   - Test database constraints
   - Test index performance
   - Test concurrent operations
   - Test hierarchy integrity

## Performance Considerations

1. **Query Optimization**
   - Use appropriate indexes
   - Implement pagination for list queries
   - Use eager loading for related entities
   - Optimize tree traversal queries

2. **Caching Strategy**
   - Cache category trees
   - Cache frequently accessed categories
   - Implement cache invalidation on updates
   - Use Redis for distributed caching

3. **Bulk Operations**
   - Implement batch insert/update methods
   - Use transactions for bulk operations
   - Optimize bulk delete operations
   - Handle hierarchy updates efficiently

## Security Considerations

1. **Input Validation**
   - Validate all input data
   - Sanitize HTML content
   - Prevent SQL injection
   - Validate hierarchy operations

2. **Access Control**
   - Implement role-based access control
   - Validate user permissions
   - Audit all operations
   - Protect hierarchy operations

3. **Data Protection**
   - Encrypt sensitive data
   - Implement data masking
   - Follow GDPR requirements
   - Protect category metadata

## References

- [TypeORM Documentation](https://typeorm.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [NestJS Documentation](https://docs.nestjs.com/)
- [Class Validator Documentation](https://github.com/typestack/class-validator) 