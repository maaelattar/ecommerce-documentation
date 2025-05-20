# Product Service Specification

## Overview

The Product Service is responsible for managing the lifecycle and business logic of products within the e-commerce platform. It orchestrates product creation, updates, deletion, and retrieval, and integrates with related services such as category, inventory, and pricing. The service ensures data integrity, enforces business rules, and provides a robust API for product management.

## Responsibilities

- Manage product creation, updates, and deletion
- Enforce business rules and validation for product data
- Handle product status transitions (draft, active, inactive, discontinued)
- Integrate with category, inventory, and price/discount services
- Support product search, filtering, and pagination
- Maintain audit logs for product changes
- Publish and consume domain events for product lifecycle changes
- Ensure data consistency and transactional integrity
- Provide APIs for internal and external consumers

## Main Methods & Workflows

### Service Methods

#### 1. `createProduct(createProductDto: CreateProductDto): Promise<Product>`
- **Description:** Creates a new product, validates input, links categories/attributes, initializes inventory and price, and logs the operation.
- **Error Scenarios:**
  - Duplicate product name within brand (409 Conflict)
  - Invalid category or attribute references (400 Bad Request)
  - Database errors (500 Internal Server Error)
- **Example:**
```typescript
async createProduct(dto: CreateProductDto): Promise<Product> {
    await this.validateBrand(dto.brand);
    await this.validateCategories(dto.categoryIds);
    const product = await this.productRepository.create(dto);
    await this.inventoryService.initializeInventory(product.id);
    await this.priceDiscountService.initializePrice(product.id, dto.price);
    await this.auditLogger.log('CREATE', 'Product', product.id, dto);
    this.eventBus.publish(new ProductCreatedEvent(product));
    return product;
}
```

#### 2. `updateProduct(id: string, updateProductDto: UpdateProductDto): Promise<Product>`
- **Description:** Updates product details, validates changes, updates linked entities, and logs the operation.
- **Error Scenarios:**
  - Product not found (404 Not Found)
  - Invalid update data (400 Bad Request)
  - Unauthorized update (403 Forbidden)

#### 3. `deleteProduct(id: string): Promise<void>`
- **Description:** Deletes a product, ensures no active dependencies (e.g., inventory, orders), and logs the operation.
- **Error Scenarios:**
  - Product not found (404 Not Found)
  - Product linked to active orders (409 Conflict)

#### 4. `getProductById(id: string): Promise<Product>`
- **Description:** Retrieves a product by its ID, including related entities (categories, attributes, variants, prices, inventory).
- **Error Scenarios:**
  - Product not found (404 Not Found)

#### 5. `listProducts(filter: ProductFilterDto): Promise<Product[]>`
- **Description:** Returns a paginated and filtered list of products based on criteria (name, brand, category, status, price range).
- **Features:**
  - Supports full-text search
  - Supports sorting and pagination

#### 6. `changeProductStatus(id: string, status: ProductStatus): Promise<Product>`
- **Description:** Changes the status of a product (e.g., activate, deactivate, discontinue), enforcing business rules.
- **Error Scenarios:**
  - Invalid status transition (400 Bad Request)

### Example Workflow: Product Creation
1. Validate input data and business rules
2. Check for unique product name within brand
3. Validate referenced categories and attributes
4. Create product entity and persist to database
5. Link product to categories, attributes, and variants
6. Initialize inventory and price
7. Create audit log entry
8. Publish `ProductCreated` event
9. Return created product

### Sequence Diagram (Textual)
- User → ProductService: createProduct()
- ProductService → CategoryService: validateCategories()
- ProductService → ProductRepository: save()
- ProductService → InventoryService: initializeInventory()
- ProductService → PriceDiscountService: initializePrice()
- ProductService → AuditLogger: log('CREATE')
- ProductService → EventBus: publish(ProductCreated)
- ProductService → User: return Product

## Integration

- **Repositories:**
  - ProductRepository: CRUD and query operations
  - CategoryRepository: Category validation and linking
  - AttributeRepository: Attribute validation and linking
- **Other Services:**
  - CategoryService: Category validation, hierarchy management
  - InventoryService: Inventory initialization and updates
  - PriceDiscountService: Price and discount setup and updates
  - AuditLogger: Audit trail for all operations
  - EventBus (e.g., RabbitMQ, Kafka): Publish/subscribe to product lifecycle events
- **Events:**
  - Publishes: `ProductCreated`, `ProductUpdated`, `ProductDeleted`, `ProductStatusChanged`
  - Subscribes: Inventory/price updates, category changes (if event-driven)
- **External Integrations:**
  - Search Service: Indexing products for search
  - Notification Service: Sending notifications on product changes

## Error Handling & Validation

- **Input Validation:**
  - Use DTOs and class-validator for all input
  - Enforce required fields, value ranges, and formats
- **Business Rule Enforcement:**
  - Unique product name within brand
  - Valid status transitions
  - Category and attribute existence
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
  - Enforce RBAC for product management (admin, manager, editor roles)
  - Resource-based access for product owners
- **Audit Logging:**
  - Log all create, update, delete, and status change operations
  - Include user context and before/after state
- **Data Protection:**
  - Mask or encrypt sensitive product metadata
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
  - Test workflows involving multiple services (e.g., product creation with inventory and price)
  - Validate event publishing and consumption
- **End-to-End (E2E) Tests:**
  - Test product API endpoints (creation, update, delete, retrieval, listing)
  - Simulate real user scenarios
- **Test Utilities:**
  - Test factories for product, category, and attribute creation
  - Database cleanup and seeding scripts
- **Coverage:**
  - Aim for >90% coverage on service logic

## Performance & Scalability

- **Query Optimization:**
  - Use indexes on frequently queried fields (name, brand, status, category)
  - Use pagination and limit/offset for large result sets
- **Caching:**
  - Cache frequently accessed products and product lists
  - Invalidate cache on updates
- **Bulk Operations:**
  - Support batch product imports and updates
  - Use transactions for bulk changes
- **Horizontal Scaling:**
  - Stateless service design for scaling
  - Use message queues for event-driven workflows

## Example Code Snippet: Product Creation
```typescript
@Injectable()
export class ProductService {
    constructor(
        private readonly productRepository: ProductRepository,
        private readonly categoryService: CategoryService,
        private readonly inventoryService: InventoryService,
        private readonly priceDiscountService: PriceDiscountService,
        private readonly auditLogger: AuditLogger,
        private readonly eventBus: EventBus
    ) {}

    async createProduct(dto: CreateProductDto): Promise<Product> {
        // Validate brand and categories
        await this.categoryService.validateCategories(dto.categoryIds);
        // Check for duplicate name
        const exists = await this.productRepository.findByNameAndBrand(dto.name, dto.brand);
        if (exists) throw new ConflictException('Product name already exists for this brand');
        // Create product
        const product = await this.productRepository.create(dto);
        // Initialize inventory and price
        await this.inventoryService.initializeInventory(product.id);
        await this.priceDiscountService.initializePrice(product.id, dto.price);
        // Audit log
        await this.auditLogger.log('CREATE', 'Product', product.id, dto);
        // Publish event
        this.eventBus.publish(new ProductCreatedEvent(product));
        return product;
    }
}
```

## References

- [Product Entity Model](../02-data-model-setup/02a-product-entity.md)
- [Category Service Specification](02-category-service.md)
- [Inventory Service Specification](03-inventory-service.md)
- [Price & Discount Service Specification](04-price-discount-service.md)
- [Audit Logging](../02-data-model-setup/06-security-considerations.md)
- [Testing Strategy](06-testing-strategy.md)
- [NestJS Service Best Practices](https://docs.nestjs.com/providers)
- [Domain-Driven Design Patterns](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Event-Driven Architecture](https://microservices.io/patterns/data/event-driven-architecture.html) 