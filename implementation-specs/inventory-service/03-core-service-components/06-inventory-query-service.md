# Inventory Query Service

## Overview

The Inventory Query Service provides optimized read-only access to inventory data. Following the CQRS pattern, this service is specifically designed for efficient querying operations, offering specialized views of inventory data tailored for different use cases. It maintains read models that are updated through event subscriptions from the command side of the system.

## Service Interface

```typescript
export interface IInventoryQueryService {
  // Item Queries
  getInventoryItemById(id: string): Promise<InventoryItemDto>;
  getInventoryItemBySku(sku: string): Promise<InventoryItemDto>;
  searchInventoryItems(query: InventorySearchQuery): Promise<PaginatedResult<InventoryItemDto>>;
  
  // Stock Queries
  getStockLevelsByProductId(productId: string): Promise<ProductStockLevelsDto>;
  getStockLevelsByWarehouses(query: WarehouseStockQuery): Promise<WarehouseStockLevelsDto[]>;
  getLowStockItems(thresholdPercentage?: number): Promise<LowStockItemDto[]>;
  getStockHistory(itemId: string, options?: StockHistoryOptions): Promise<StockHistoryEntryDto[]>;
  
  // Allocation Queries
  getItemAllocations(itemId: string): Promise<ItemAllocationDto[]>;
  getOrderAllocations(orderId: string): Promise<OrderAllocationDto[]>;
  getWarehouseAllocations(warehouseId: string, options?: PaginationOptions): Promise<PaginatedResult<WarehouseAllocationDto>>;
  
  // Dashboard & Reporting Queries
  getInventoryValueReport(options?: InventoryValueOptions): Promise<InventoryValueReportDto>;
  getInventoryTurnoverReport(options?: DateRangeOptions): Promise<InventoryTurnoverReportDto>;
  getTopMovingItems(options?: TopItemsOptions): Promise<TopMovingItemDto[]>;
  getStockoutReport(options?: DateRangeOptions): Promise<StockoutReportDto>;
  
  // Advanced Queries
  getInventoryProjections(daysAhead: number): Promise<InventoryProjectionDto[]>;
  getItemAvailabilityTimeline(itemId: string, days: number): Promise<AvailabilityTimelineDto>;
  getWarehouseCapacityUtilization(warehouseId: string): Promise<WarehouseCapacityDto>;
}
```

## Implementation

```typescript
@Injectable()
export class InventoryQueryService implements IInventoryQueryService {
  constructor(
    private readonly inventoryReadRepository: IInventoryReadRepository,
    private readonly warehouseReadRepository: IWarehouseReadRepository,
    private readonly stockHistoryRepository: IStockHistoryRepository,
    private readonly allocationReadRepository: IAllocationReadRepository,
    private readonly reportingRepository: IReportingRepository,
    private readonly cacheManager: ICacheManager,
    private readonly logger: Logger
  ) {}

  // Implementation of interface methods...
}
```

## Data Transfer Objects (DTOs)

### InventoryItemDto
```typescript
export interface InventoryItemDto {
  id: string;
  sku: string;
  productId: string;
  name: string;
  description?: string;
  quantityAvailable: number;
  quantityReserved: number;
  warehouseId: string;
  warehouseName: string;
  reorderThreshold: number;
  targetStockLevel: number;
  locations?: BinLocationDto[];
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}
```

### ProductStockLevelsDto
```typescript
export interface ProductStockLevelsDto {
  productId: string;
  productName: string;
  totalQuantityAvailable: number;
  totalQuantityReserved: number;
  warehouseStockLevels: {
    warehouseId: string;
    warehouseName: string;
    warehouseCode: string;
    quantityAvailable: number;
    quantityReserved: number;
  }[];
}
```

### StockHistoryEntryDto
```typescript
export interface StockHistoryEntryDto {
  timestamp: Date;
  transactionId: string;
  transactionType: string;
  quantity: number;
  previousQuantity: number;
  newQuantity: number;
  reason: string;
  referenceNumber?: string;
  referenceType?: string;
  username?: string;
}
```

## Query Optimization Techniques

### 1. Denormalized Read Models

The service maintains denormalized read models optimized for specific query patterns:

```typescript
// Example of a denormalized read model for product stock levels
interface ProductStockReadModel {
  productId: string;
  productName: string;
  skus: {
    sku: string;
    inventoryItemId: string;
    totalQuantityAvailable: number;
    totalQuantityReserved: number;
    warehouseStock: {
      warehouseId: string;
      warehouseName: string;
      warehouseCode: string;
      quantityAvailable: number;
      quantityReserved: number;
    }[];
  }[];
  lastUpdated: Date;
}
```

### 2. Caching Strategy

The service implements multi-level caching:

```typescript
async getInventoryItemBySku(sku: string): Promise<InventoryItemDto> {
  const cacheKey = `inventory_item_sku_${sku}`;
  
  // Try to get from cache first
  const cachedItem = await this.cacheManager.get<InventoryItemDto>(cacheKey);
  if (cachedItem) {
    return cachedItem;
  }
  
  // If not in cache, get from database
  const item = await this.inventoryReadRepository.findBySku(sku);
  if (!item) {
    throw new InventoryItemNotFoundException(sku);
  }
  
  // Store in cache for future requests
  await this.cacheManager.set(cacheKey, item, { ttl: 300 }); // 5 minutes TTL
  
  return item;
}
```

### 3. Pagination and Filtering

For large result sets, the service implements efficient pagination:

```typescript
async searchInventoryItems(
  query: InventorySearchQuery
): Promise<PaginatedResult<InventoryItemDto>> {
  const { 
    searchTerm, 
    warehouseIds, 
    isActive, 
    minQuantity, 
    maxQuantity,
    sortBy = 'name',
    sortDirection = 'asc',
    page = 1,
    pageSize = 20
  } = query;
  
  // Calculate offset from page and pageSize
  const offset = (page - 1) * pageSize;
  
  // Execute query with pagination
  const [items, totalCount] = await this.inventoryReadRepository.search({
    searchTerm,
    warehouseIds,
    isActive,
    minQuantity,
    maxQuantity,
    sortBy,
    sortDirection,
    offset,
    limit: pageSize
  });
  
  // Calculate total pages
  const totalPages = Math.ceil(totalCount / pageSize);
  
  return {
    items,
    pagination: {
      totalItems: totalCount,
      totalPages,
      currentPage: page,
      pageSize
    }
  };
}
```

## Event-Driven View Updates

The query service's read models are updated through event subscriptions:

```typescript
@EventSubscriber()
export class InventoryReadModelUpdater {
  constructor(
    private readonly inventoryReadRepository: IInventoryReadRepository,
    private readonly cacheManager: ICacheManager,
    private readonly logger: Logger
  ) {}
  
  @EventHandler(StockLevelChangedEvent)
  async handleStockLevelChanged(event: StockLevelChangedEvent): Promise<void> {
    try {
      // Update the read model
      await this.inventoryReadRepository.updateStockLevel(
        event.inventoryItemId,
        event.warehouseId,
        event.newQuantity
      );
      
      // Invalidate cache
      const cacheKey = `inventory_item_id_${event.inventoryItemId}`;
      await this.cacheManager.del(cacheKey);
      
      // If we have the product ID, invalidate product-level cache too
      if (event.productId) {
        await this.cacheManager.del(`product_stock_${event.productId}`);
      }
    } catch (error) {
      this.logger.error(
        `Failed to update read model for StockLevelChangedEvent: ${error.message}`,
        { eventId: event.eventId, inventoryItemId: event.inventoryItemId }
      );
      throw error;
    }
  }
  
  // Additional event handlers for other event types...
}
```

## Business Intelligence and Reporting Functionality

### Inventory Value Report

```typescript
async getInventoryValueReport(
  options?: InventoryValueOptions
): Promise<InventoryValueReportDto> {
  const { warehouseIds, categorize = true, includeInactive = false } = options || {};
  
  // Fetch raw inventory data
  const inventoryValue = await this.reportingRepository.getInventoryValue({
    warehouseIds,
    includeInactive
  });
  
  // Format the response
  const report: InventoryValueReportDto = {
    totalValue: inventoryValue.totalValue,
    timestamp: new Date(),
    warehouseSummary: inventoryValue.warehouseValues,
  };
  
  // Add categorization if requested
  if (categorize) {
    report.categorySummary = inventoryValue.categoryValues;
  }
  
  return report;
}
```

### Top Moving Items Report

```typescript
async getTopMovingItems(
  options?: TopItemsOptions
): Promise<TopMovingItemDto[]> {
  const { 
    warehouseIds, 
    timeFrame = 'MONTH', 
    movementType = 'ALL',
    limit = 10
  } = options || {};
  
  // Determine date range based on time frame
  const endDate = new Date();
  let startDate: Date;
  
  switch (timeFrame) {
    case 'WEEK':
      startDate = new Date();
      startDate.setDate(startDate.getDate() - 7);
      break;
    case 'MONTH':
      startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 1);
      break;
    case 'QUARTER':
      startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 3);
      break;
    default:
      startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 1);
  }
  
  return this.reportingRepository.getTopMovingItems({
    startDate,
    endDate,
    warehouseIds,
    movementType,
    limit
  });
}
```

## Performance Considerations

1. **Query Optimization**
   - Dedicated indexes for common query patterns
   - Compound indexes for multi-field filtering
   - Covering indexes for frequently used projections

2. **Database Considerations**
   - Read replicas for query scaling
   - Materialized views for complex aggregations
   - Time-series optimizations for historical data

3. **Caching Strategy**
   - Tiered caching (memory, distributed cache)
   - Cache invalidation based on event subscriptions
   - Configurable TTL based on data volatility

4. **Scaling Approach**
   - Horizontal scaling through stateless design
   - Partitioning by warehouse or product category
   - Read-heavy load balancing

## Example Usage

```typescript
// Get inventory levels for a product across all warehouses
const productId = '3f5d7e9a-1b2c-3d4e-5f6a-7b8c9d0e1f2a';
const stockLevels = await inventoryQueryService.getStockLevelsByProductId(productId);

// Search for inventory items with filters
const searchResults = await inventoryQueryService.searchInventoryItems({
  searchTerm: 'widget',
  warehouseIds: ['warehouse-north', 'warehouse-south'],
  minQuantity: 10,
  page: 1,
  pageSize: 25,
  sortBy: 'quantityAvailable',
  sortDirection: 'desc'
});

// Generate inventory value report for specific warehouses
const valueReport = await inventoryQueryService.getInventoryValueReport({
  warehouseIds: ['warehouse-east'],
  categorize: true
});

// Get stock history for an item
const stockHistory = await inventoryQueryService.getStockHistory(
  'inventory-item-123',
  {
    startDate: new Date('2023-01-01'),
    endDate: new Date('2023-03-31'),
    transactionTypes: ['RECEIPT', 'SALE', 'ADJUSTMENT']
  }
);
```