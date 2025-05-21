# Projections

## 1. Overview

Projections transform event streams into optimized read models that support efficient querying. As part of the CQRS pattern, projections form the query side of the system, providing a denormalized view of data optimized for specific use cases.

## 2. Projection Types

### 2.1. Real-time Projections

Real-time projections process events as they occur, maintaining an up-to-date view of the data. These projections subscribe to the event store and update their state immediately as new events are published.

### 2.2. Rebuild Projections

Rebuild projections can reconstruct their state from scratch by replaying all events. This is useful for creating new projections, fixing corrupted projections, or changing projection schemas.

## 3. Core Product Projections

### 3.1. Product Catalog Projection

**Purpose:** Provides an optimized view of products for listing, filtering, and searching.

**Schema:**
```typescript
interface ProductCatalogItem {
  id: string;
  name: string;
  description: string;
  brand: string;
  status: ProductStatus;
  sku: string;
  tags: string[];
  categoryIds: string[];
  categoryNames: string[]; // Denormalized for display
  price: {
    amount: number;
    currency: string;
  };
  variantCount: number;
  thumbnailUrl?: string;
  averageRating?: number;
  reviewCount?: number;
  lastUpdated: string; // ISO 8601 timestamp
}
```

**Event Handlers:**
```typescript
class ProductCatalogProjection {
  constructor(private readonly repository: ProductCatalogRepository) {}
  
  // Handle ProductCreated event
  async handleProductCreated(event: DomainEvent<ProductCreatedData>): Promise<void> {
    const product: ProductCatalogItem = {
      id: event.entityId,
      name: event.data.name,
      description: event.data.description,
      brand: event.data.brand,
      status: event.data.status,
      sku: event.data.sku,
      tags: event.data.tags || [],
      categoryIds: event.data.categoryIds || [],
      categoryNames: [], // Will be populated by a separate process
      price: event.data.listPrice || { amount: 0, currency: 'USD' },
      variantCount: 0,
      lastUpdated: event.eventTime
    };
    
    await this.repository.create(product);
  }
  
  // Handle ProductBasicInfoUpdated event
  async handleProductBasicInfoUpdated(event: DomainEvent<ProductBasicInfoUpdatedData>): Promise<void> {
    const product = await this.repository.findById(event.entityId);
    
    if (!product) return;
    
    // Update fields that are present in the event
    if (event.data.name) product.name = event.data.name;
    if (event.data.description) product.description = event.data.description;
    if (event.data.brand) product.brand = event.data.brand;
    if (event.data.sku) product.sku = event.data.sku;
    if (event.data.tags) product.tags = event.data.tags;
    
    product.lastUpdated = event.eventTime;
    
    await this.repository.update(product);
  }
  
  // Handle ProductStatusChanged event
  async handleProductStatusChanged(event: DomainEvent<ProductStatusChangedData>): Promise<void> {
    const product = await this.repository.findById(event.entityId);
    
    if (!product) return;
    
    product.status = event.data.newStatus;
    product.lastUpdated = event.eventTime;
    
    await this.repository.update(product);
  }
  
  // Handle ProductCategoriesUpdated event
  async handleProductCategoriesUpdated(event: DomainEvent<ProductCategoriesUpdatedData>): Promise<void> {
    const product = await this.repository.findById(event.entityId);
    
    if (!product) return;
    
    // Update category IDs
    product.categoryIds = product.categoryIds
      .filter(id => !event.data.removedCategoryIds.includes(id))
      .concat(event.data.addedCategoryIds);
    
    product.lastUpdated = event.eventTime;
    
    await this.repository.update(product);
    
    // Category names will be updated by a separate process
  }
  
  // Handle ProductPriceUpdated event
  async handleProductPriceUpdated(event: DomainEvent<ProductPriceUpdatedData>): Promise<void> {
    const product = await this.repository.findById(event.entityId);
    
    if (!product) return;
    
    product.price = event.data.newPrice;
    product.lastUpdated = event.eventTime;
    
    await this.repository.update(product);
  }
  
  // Handle ProductVariantAdded event
  async handleProductVariantAdded(event: DomainEvent<ProductVariantAddedData>): Promise<void> {
    const product = await this.repository.findById(event.entityId);
    
    if (!product) return;
    
    product.variantCount += 1;
    product.lastUpdated = event.eventTime;
    
    await this.repository.update(product);
  }
  
  // Handle ProductVariantRemoved event
  async handleProductVariantRemoved(event: DomainEvent<ProductVariantRemovedData>): Promise<void> {
    const product = await this.repository.findById(event.entityId);
    
    if (!product) return;
    
    product.variantCount = Math.max(0, product.variantCount - 1);
    product.lastUpdated = event.eventTime;
    
    await this.repository.update(product);
  }
  
  // Handle ProductMediaAdded event
  async handleProductMediaAdded(event: DomainEvent<ProductMediaAddedData>): Promise<void> {
    const product = await this.repository.findById(event.entityId);
    
    if (!product) return;
    
    // If primary image, update thumbnail
    if (event.data.isPrimary && event.data.mediaType === 'IMAGE') {
      product.thumbnailUrl = event.data.url;
    }
    
    product.lastUpdated = event.eventTime;
    
    await this.repository.update(product);
  }
  
  // Other event handlers...
}
```

### 3.2. Product Detail Projection

**Purpose:** Provides complete product information for product detail pages.

**Schema:**
```typescript
interface ProductDetailItem {
  id: string;
  name: string;
  description: string;
  brand: string;
  status: ProductStatus;
  sku: string;
  tags: string[];
  attributes: Record<string, string | number | boolean>;
  metadata: Record<string, any>;
  categoryIds: string[];
  categories: Array<{ id: string; name: string; path: string }>;
  variants: Array<{
    id: string;
    sku: string;
    name?: string;
    attributes: Record<string, string | number | boolean>;
    price: {
      amount: number;
      currency: string;
    };
    stockKeepingUnit: string;
    isDefault: boolean;
  }>;
  media: Array<{
    id: string;
    type: string;
    url: string;
    title?: string;
    altText?: string;
    sortOrder: number;
    variantId?: string;
    isPrimary: boolean;
  }>;
  relatedProducts: Array<{
    productId: string;
    relationType: string;
    name: string;
    thumbnailUrl?: string;
  }>;
  discounts: Array<{
    id: string;
    type: string;
    value: number;
    startDate: string;
    endDate?: string;
    conditions?: object;
  }>;
  createdAt: string;
  updatedAt: string;
}
```

### 3.3. Product Search Projection

**Purpose:** Optimized for full-text search across products.

**Schema:**
```typescript
interface ProductSearchItem {
  id: string;
  name: string;
  description: string;
  brand: string;
  status: ProductStatus;
  sku: string;
  tags: string[];
  categoryIds: string[];
  categoryNames: string[];
  price: {
    amount: number;
    currency: string;
  };
  attributes: Record<string, string | number | boolean>;
  variantAttributes: Record<string, Array<string | number | boolean>>;
  searchableText: string; // Concatenated text for full-text search
  thumbnailUrl?: string;
  updatedAt: string;
}
```

### 3.4. Product Inventory Projection

**Purpose:** Provides a view of products with their inventory status for inventory management screens.

**Schema:**
```typescript
interface ProductInventoryItem {
  id: string;
  name: string;
  sku: string;
  status: ProductStatus;
  variants: Array<{
    id: string;
    sku: string;
    name?: string;
    attributes: Record<string, string | number | boolean>;
    stockKeepingUnit: string;
    // These would be updated by inventory service events
    stockLevel?: number;
    availableStock?: number;
    reservedStock?: number;
    backorderLevel?: number;
    restockThreshold?: number;
    restockStatus?: string;
  }>;
  updatedAt: string;
}
```

## 4. Projection Rebuilding

The system includes a mechanism to rebuild projections from the event store:

```typescript
class ProjectionRebuilder {
  constructor(
    private readonly eventStore: EventStore,
    private readonly projectionHandlers: Map<string, Function>
  ) {}
  
  async rebuildProjection(
    projectionName: string,
    fromTimestamp?: string,
    toTimestamp?: string
  ): Promise<void> {
    // Clear existing projection data if needed
    
    // Get relevant event types for this projection
    const eventTypes = this.getEventTypesForProjection(projectionName);
    
    // Fetch all events of these types
    let events: DomainEvent<any>[] = [];
    for (const eventType of eventTypes) {
      const typeEvents = await this.eventStore.getEventsByType(
        'Product', // or other aggregate types
        eventType,
        fromTimestamp,
        toTimestamp
      );
      events = events.concat(typeEvents);
    }
    
    // Sort events by timestamp
    events.sort((a, b) => 
      new Date(a.eventTime).getTime() - new Date(b.eventTime).getTime()
    );
    
    // Process events
    for (const event of events) {
      const handlerName = `handle${event.eventType}`;
      const handler = this.projectionHandlers.get(handlerName);
      
      if (handler) {
        await handler(event);
      }
    }
  }
  
  private getEventTypesForProjection(projectionName: string): string[] {
    // Map projections to the event types they handle
    const projectionEventMap = {
      'ProductCatalog': [
        'ProductCreated',
        'ProductBasicInfoUpdated',
        'ProductStatusChanged',
        'ProductCategoriesUpdated',
        'ProductPriceUpdated',
        'ProductVariantAdded',
        'ProductVariantRemoved',
        'ProductMediaAdded'
      ],
      'ProductDetail': [
        // All product events
      ],
      // Other projections...
    };
    
    return projectionEventMap[projectionName] || [];
  }
}
```

## 5. Projection Synchronization

To keep projections in sync with the event store:

```typescript
class ProjectionSynchronizer {
  constructor(
    private readonly eventBus: EventBus,
    private readonly projectionHandlers: Map<string, Function>
  ) {}
  
  start(): void {
    // Subscribe to all relevant events
    this.eventBus.subscribe('ProductCreated', this.handleEvent.bind(this));
    this.eventBus.subscribe('ProductBasicInfoUpdated', this.handleEvent.bind(this));
    this.eventBus.subscribe('ProductStatusChanged', this.handleEvent.bind(this));
    // ... other event subscriptions
  }
  
  async handleEvent(event: DomainEvent<any>): Promise<void> {
    try {
      const handlerName = `handle${event.eventType}`;
      const handler = this.projectionHandlers.get(handlerName);
      
      if (handler) {
        await handler(event);
      }
    } catch (error) {
      // Log error and handle projection failure
      console.error(`Error handling event ${event.eventType} for projection:`, error);
      
      // Implement recovery strategy
      // - Retry
      // - Mark projection as inconsistent
      // - Trigger rebuilding
    }
  }
}
```

## 6. Query Interfaces

With projections in place, query interfaces become simple and efficient:

```typescript
@Injectable()
export class ProductQueryService {
  constructor(
    private readonly productCatalogRepository: ProductCatalogRepository,
    private readonly productDetailRepository: ProductDetailRepository,
    private readonly productSearchRepository: ProductSearchRepository
  ) {}
  
  async findProducts(
    filter: ProductFilterDto,
    sort: ProductSortDto,
    pagination: PaginationDto
  ): Promise<PaginatedResult<ProductCatalogItem>> {
    return this.productCatalogRepository.findAll(filter, sort, pagination);
  }
  
  async findProductById(id: string): Promise<ProductDetailItem | null> {
    return this.productDetailRepository.findById(id);
  }
  
  async searchProducts(
    query: string,
    filter?: ProductFilterDto,
    pagination?: PaginationDto
  ): Promise<PaginatedResult<ProductSearchItem>> {
    return this.productSearchRepository.search(query, filter, pagination);
  }
  
  // Other query methods...
}
```

## 7. Consistency Considerations

1. **Eventually Consistent**: Projections are eventually consistent with the event store
2. **Versioning**: Include version information to detect stale data
3. **Compensating Updates**: Handle out-of-order events gracefully
4. **Idempotency**: Ensure projection updates are idempotent
5. **Recovery**: Implement strategies for handling projection failures and inconsistencies

## 8. References

- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Domain-Driven Design](https://domainlanguage.com/ddd/)