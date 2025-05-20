# Category Service Specification

## Overview

The Category Service manages the hierarchical taxonomy of product categories within the e-commerce platform. It is responsible for category creation, updates, deletion, and retrieval, as well as maintaining parent-child relationships, enforcing hierarchy rules, and integrating with the Product Service and other components. The service ensures data integrity, supports efficient category navigation, and provides APIs for category management.

## Responsibilities

- Manage category creation, updates, and deletion
- Enforce hierarchy and business rules (e.g., max depth, unique names)
- Maintain parent-child relationships and path management
- Integrate with Product Service for category-product associations
- Support category search, filtering, and tree traversal
- Maintain audit logs for category changes
- Publish and consume domain events for category lifecycle changes
- Ensure data consistency and transactional integrity
- Provide APIs for internal and external consumers

## Main Methods & Workflows

### Service Methods

#### 1. `createCategory(createCategoryDto: CreateCategoryDto): Promise<Category>`
- **Description:** Creates a new category, validates input, manages hierarchy, and logs the operation.
- **Error Scenarios:**
  - Duplicate category name within parent (409 Conflict)
  - Invalid parent reference or circular hierarchy (400 Bad Request)
  - Database errors (500 Internal Server Error)

#### 2. `updateCategory(id: string, updateCategoryDto: UpdateCategoryDto): Promise<Category>`
- **Description:** Updates category details, manages hierarchy changes, and logs the operation.
- **Error Scenarios:**
  - Category not found (404 Not Found)
  - Invalid update data or hierarchy violation (400 Bad Request)
  - Unauthorized update (403 Forbidden)

#### 3. `deleteCategory(id: string): Promise<void>`
- **Description:** Deletes a category, ensures no child categories or associated products, and logs the operation.
- **Error Scenarios:**
  - Category not found (404 Not Found)
  - Category has children or associated products (409 Conflict)

#### 4. `getCategoryById(id: string): Promise<Category>`
- **Description:** Retrieves a category by its ID, including parent, children, and associated products.
- **Error Scenarios:**
  - Category not found (404 Not Found)

#### 5. `listCategories(filter: CategoryFilterDto): Promise<Category[]>`
- **Description:** Returns a filtered list of categories, supports tree traversal and search.
- **Features:**
  - Supports hierarchical queries (e.g., descendants, ancestors)
  - Supports pagination and sorting

#### 6. `moveCategory(id: string, newParentId: string): Promise<Category>`
- **Description:** Moves a category to a new parent, updates hierarchy, and logs the operation.
- **Error Scenarios:**
  - Invalid move (circular reference, max depth exceeded) (400 Bad Request)

### Example Workflow: Category Creation
1. Validate input data and business rules
2. Check for unique name within parent
3. Validate parent category (if provided)
4. Calculate level and path
5. Create category entity and persist to database
6. Create audit log entry
7. Publish `CategoryCreated` event
8. Return created category

### Sequence Diagram (Textual)
- User → CategoryService: createCategory()
- CategoryService → CategoryRepository: save()
- CategoryService → AuditLogger: log('CREATE')
- CategoryService → EventBus: publish(CategoryCreated)
- CategoryService → User: return Category

## Integration

- **Repositories:**
  - CategoryRepository: CRUD, hierarchy, and query operations
  - ProductRepository: For category-product associations
- **Other Services:**
  - ProductService: For product-category linking and validation
  - AuditLogger: Audit trail for all operations
  - EventBus: Publish/subscribe to category lifecycle events
- **Events:**
  - Publishes: `CategoryCreated`, `CategoryUpdated`, `CategoryDeleted`, `CategoryMoved`
  - Subscribes: Product changes (if event-driven)
- **External Integrations:**
  - Search Service: Indexing categories for navigation
  - Notification Service: Sending notifications on category changes

## Error Handling & Validation

- **Input Validation:**
  - Use DTOs and class-validator for all input
  - Enforce required fields, value ranges, and formats
- **Business Rule Enforcement:**
  - Unique category name within parent
  - Valid parent reference, no circular hierarchy
  - Max hierarchy depth
- **Error Handling:**
  - Use custom exceptions for domain errors
  - Return appropriate HTTP status codes
  - Log all errors and failed operations
- **Transactional Integrity:**
  - Use database transactions for multi-step operations
  - Rollback on failure

## Security & Access Control

- **Authentication:**
  - Require JWT or OAuth2 tokens for all operations
- **Authorization:**
  - Enforce RBAC for category management (admin, manager, editor roles)
- **Audit Logging:**
  - Log all create, update, delete, and move operations
  - Include user context and before/after state
- **Data Protection:**
  - Mask or encrypt sensitive category metadata
  - Validate and sanitize all user input
- **API Security:**
  - Rate limiting on write operations
  - CORS and security headers

## Testing Strategy

- **Unit Tests:**
  - Test all service methods in isolation
  - Mock repositories and external services
  - Cover all business rules and error scenarios
- **Integration Tests:**
  - Test workflows involving multiple services (e.g., category creation with product linking)
  - Validate event publishing and consumption
- **End-to-End (E2E) Tests:**
  - Test category API endpoints (creation, update, delete, retrieval, listing)
  - Simulate real user scenarios
- **Test Utilities:**
  - Test factories for category and product creation
  - Database cleanup and seeding scripts
- **Coverage:**
  - Aim for >90% coverage on service logic

## Performance & Scalability

- **Query Optimization:**
  - Use indexes on frequently queried fields (name, parent, path, level)
  - Optimize tree traversal queries (e.g., using path or closure table)
- **Caching:**
  - Cache category trees and frequently accessed categories
  - Invalidate cache on updates
- **Bulk Operations:**
  - Support batch category imports and updates
  - Use transactions for bulk changes
- **Horizontal Scaling:**
  - Stateless service design for scaling
  - Use message queues for event-driven workflows

## Example Code Snippet: Category Creation
```typescript
@Injectable()
export class CategoryService {
    constructor(
        private readonly categoryRepository: CategoryRepository,
        private readonly auditLogger: AuditLogger,
        private readonly eventBus: EventBus
    ) {}

    async createCategory(dto: CreateCategoryDto): Promise<Category> {
        // Validate parent
        if (dto.parentId) {
            await this.validateParent(dto.parentId);
        }
        // Check for duplicate name
        const exists = await this.categoryRepository.findByNameAndParent(dto.name, dto.parentId);
        if (exists) throw new ConflictException('Category name already exists under this parent');
        // Calculate level and path
        const { level, path } = await this.calculateHierarchy(dto.parentId);
        // Create category
        const category = await this.categoryRepository.create({ ...dto, level, path });
        // Audit log
        await this.auditLogger.log('CREATE', 'Category', category.id, dto);
        // Publish event
        this.eventBus.publish(new CategoryCreatedEvent(category));
        return category;
    }
}
```

## References

- [Category Entity Model](../02-data-model-setup/02b-category-entity.md)
- [Product Service Specification](01-product-service.md)
- [Audit Logging](../02-data-model-setup/06-security-considerations.md)
- [Testing Strategy](06-testing-strategy.md)
- [NestJS Service Best Practices](https://docs.nestjs.com/providers)
- [Domain-Driven Design Patterns](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Event-Driven Architecture](https://microservices.io/patterns/data/event-driven-architecture.html) 