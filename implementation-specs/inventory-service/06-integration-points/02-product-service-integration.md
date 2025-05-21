# Product Service Integration

## Overview

The integration between Inventory Service and Product Service ensures consistent product availability information across the platform. This integration enables Product Service to display accurate stock levels to customers while allowing Inventory Service to maintain the canonical source of inventory data.

## Integration Patterns

The integration uses a combination of event-driven communication and API calls:

```
┌───────────────────┐                   ┌───────────────────┐
│                   │                   │                   │
│  Product Service  │◀──── Events ─────▶│ Inventory Service │
│                   │                   │                   │
└────────┬──────────┘                   └────────┬──────────┘
         │                                       │
         │                                       │
         └───────── API Calls ─────────────────▶│
                                                 │
                                                 │
         ┌───────── API Calls ◀─────────────────┘
         │
┌────────▼──────────┐
│                   │
│  Message Broker   │
│  (RabbitMQ)       │
│                   │
└───────────────────┘
```

## Event-Driven Integration

### Events Published by Inventory Service

These events notify the Product Service about changes in inventory status.

1. **StockLevelChangedEvent**
   - **Purpose**: Notifies of changes to available inventory for a product
   - **Consumer Action**: Product Service updates product availability status
   - **Exchange**: `inventory.events`
   - **Routing Key**: `inventory.stocklevelchanged.inventoryitem`

   ```typescript
   // Example payload
   {
     "eventId": "e1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
     "eventType": "StockLevelChanged",
     "eventVersion": "1.0.0",
     "aggregateId": "inv_01GXYZ234DEF",
     "aggregateType": "InventoryItem",
     "timestamp": "2023-05-20T10:15:00Z",
     "metadata": {
       "correlationId": "tx_01KXYZ678KLM",
       "source": "inventory-service"
     },
     "payload": {
       "inventoryItemId": "inv_01GXYZ234DEF",
       "sku": "WIDGET-2",
       "productId": "prod_01FXYZ789ABC",
       "warehouseId": "wh_01HXYZ789GHI",
       "previousQuantity": 50,
       "newQuantity": 75,
       "changeAmount": 25,
       "changeReason": "Scheduled stock replenishment",
       "transactionId": "tx_01KXYZ678KLM",
       "transactionType": "RECEIPT",
       "referenceNumber": "PO-12345",
       "referenceType": "PURCHASE_ORDER"
     }
   }
   ```

2. **LowStockThresholdReachedEvent**
   - **Purpose**: Notifies that a product is running low on stock
   - **Consumer Action**: Product Service updates product with "low stock" indicator
   - **Exchange**: `inventory.events`
   - **Routing Key**: `inventory.lowstockthresholdreached.inventoryitem`

3. **OutOfStockEvent**
   - **Purpose**: Notifies that a product is completely out of stock
   - **Consumer Action**: Product Service updates product to show as "out of stock"
   - **Exchange**: `inventory.events`
   - **Routing Key**: `inventory.outofstock.inventoryitem`

### Events Consumed by Inventory Service

These events allow the Inventory Service to maintain inventory records in sync with product data.

1. **ProductCreatedEvent**
   - **Purpose**: Triggers creation of initial inventory records for a new product
   - **Producer**: Product Service
   - **Exchange**: `product.events`
   - **Routing Key**: `product.productcreated.product`
   - **Handler**: `ProductCreatedEventHandler`

   ```typescript
   // Implementation of event handler
   @Injectable()
   export class ProductCreatedEventHandler implements IEventHandler<ProductCreatedEvent> {
     constructor(
       private readonly inventoryService: IInventoryManagementService,
       private readonly warehouseService: IWarehouseManagementService,
       private readonly configService: ConfigService,
       private readonly logger: Logger
     ) {}

     async handle(event: ProductCreatedEvent): Promise<void> {
       this.logger.log(`Handling ProductCreatedEvent: ${event.payload.productId}`);
       
       try {
         // Check if automatic inventory creation is enabled
         const autoCreateInventory = this.configService.get<boolean>('inventory.autoCreateOnProductCreation', true);
         if (!autoCreateInventory) {
           this.logger.debug(`Auto inventory creation disabled, skipping for product ${event.payload.productId}`);
           return;
         }
         
         // Get default warehouse(s) for new product inventory
         const defaultWarehouseIds = this.configService.get<string[]>('inventory.defaultWarehouses', []);
         if (!defaultWarehouseIds.length) {
           this.logger.warn(`No default warehouses configured for auto inventory creation`);
           return;
         }
         
         // Create inventory items for each warehouse
         for (const warehouseId of defaultWarehouseIds) {
           // Check if warehouse exists
           const warehouse = await this.warehouseService.getWarehouse(warehouseId);
           if (!warehouse) {
             this.logger.warn(`Default warehouse ${warehouseId} not found, skipping`);
             continue;
           }
           
           // Create inventory item with 0 initial quantity
           await this.inventoryService.createInventoryItem({
             sku: event.payload.sku,
             productId: event.payload.productId,
             name: event.payload.name,
             warehouseId: warehouse.id,
             initialQuantity: 0,
             reorderThreshold: this.configService.get<number>('inventory.defaultReorderThreshold', 10),
             targetStockLevel: this.configService.get<number>('inventory.defaultTargetStockLevel', 50),
             metadata: {
               createdFromProductEvent: true,
               productEventId: event.eventId
             }
           });
           
           this.logger.log(`Created inventory item for product ${event.payload.productId} in warehouse ${warehouse.name}`);
         }
       } catch (error) {
         this.logger.error(
           `Failed to create inventory records for product ${event.payload.productId}`,
           error
         );
       }
     }
   }
   ```

2. **ProductUpdatedEvent**
   - **Purpose**: Updates existing inventory records when product details change
   - **Producer**: Product Service
   - **Exchange**: `product.events`
   - **Routing Key**: `product.productupdated.product`
   - **Handler**: `ProductUpdatedEventHandler`

3. **ProductDeletedEvent**
   - **Purpose**: Marks inventory records as inactive when a product is deleted
   - **Producer**: Product Service
   - **Exchange**: `product.events`
   - **Routing Key**: `product.productdeleted.product`
   - **Handler**: `ProductDeletedEventHandler`

## API-Based Integration

### APIs Exposed by Inventory Service

These endpoints allow the Product Service to query inventory information.

1. **Get Inventory by Product ID**
   - **Endpoint**: `GET /inventory-items/by-product/{productId}`
   - **Purpose**: Retrieve inventory information for a specific product across all warehouses
   - **Response**:
     ```json
     {
       "success": true,
       "data": {
         "totalQuantityAvailable": 85,
         "totalQuantityReserved": 5,
         "isLowStock": false,
         "isOutOfStock": false,
         "warehouseInventory": [
           {
             "inventoryItemId": "inv_01GXYZ234DEF",
             "warehouseId": "wh_01HXYZ789GHI",
             "warehouseName": "North Seattle Fulfillment Center",
             "quantityAvailable": 60,
             "quantityReserved": 3
           },
           {
             "inventoryItemId": "inv_01MXYZ890BCD",
             "warehouseId": "wh_01HXYZ890PQR",
             "warehouseName": "South Portland Distribution Center",
             "quantityAvailable": 25,
             "quantityReserved": 2
           }
         ]
       }
     }
     ```

2. **Check Product Availability**
   - **Endpoint**: `GET /inventory-items/{id}/availability`
   - **Purpose**: Check real-time availability status for a product
   - **Query Parameters**:
     - `quantity`: Desired quantity (default: 1)
     - `checkAllWarehouses`: Check across all warehouses (default: true)
   - **Response**:
     ```json
     {
       "success": true,
       "data": {
         "isAvailable": true,
         "availableQuantity": 85,
         "requestedQuantity": 10,
         "leadTimeEstimate": "1-2 days",
         "restockExpected": null
       }
     }
     ```

### APIs Consumed by Inventory Service

These endpoints allow the Inventory Service to fetch product information.

1. **Get Product Details**
   - **Endpoint**: `GET /products/{productId}`
   - **Purpose**: Retrieve product information for validation and processing
   - **Implementation**:
     ```typescript
     @Injectable()
     export class ProductServiceClient {
       constructor(
         private readonly httpService: HttpService,
         private readonly configService: ConfigService,
         private readonly jwtTokenService: JwtTokenService,
         private readonly logger: Logger
       ) {}
       
       async getProduct(productId: string): Promise<Product> {
         const productServiceUrl = this.configService.get<string>('integration.productService.url');
         const token = await this.jwtTokenService.generateServiceToken();
         
         try {
           const response = await this.httpService.axiosRef.get(
             `${productServiceUrl}/products/${productId}`,
             {
               headers: {
                 'Authorization': `Bearer ${token}`
               }
             }
           );
           
           return response.data.data;
         } catch (error) {
           if (error.response && error.response.status === 404) {
             throw new ProductNotFoundException(productId);
           }
           
           this.logger.error(`Failed to fetch product ${productId}`, error);
           throw new ProductServiceIntegrationError(`Failed to fetch product: ${error.message}`);
         }
       }
     }
     ```

2. **Get Product Variants**
   - **Endpoint**: `GET /products/{productId}/variants`
   - **Purpose**: Retrieve variant information to ensure correct inventory tracking

## Real-Time Inventory Updates

To provide customers with real-time inventory information, the integration includes:

1. **Inventory Cache**
   - Product Service maintains a cache of inventory levels
   - Updated via both events and periodic API calls
   - TTL-based expiration to ensure eventual freshness

2. **Near-Real-Time Updates**
   - Critical inventory changes (out-of-stock, back-in-stock) trigger immediate events
   - Product Service processes these events with high priority

3. **Inventory Projections**
   - For products with complex fulfillment requirements, Inventory Service provides availability projections
   - Includes lead time estimates and restock dates

## Inventory Display Rules

Different inventory statuses trigger different display behaviors in the Product Service:

1. **In Stock**
   - Quantity above low stock threshold
   - Product Service displays "In Stock" message

2. **Low Stock**
   - Quantity below low stock threshold but greater than zero
   - Product Service displays "Only X left in stock" message

3. **Out of Stock**
   - Quantity is zero across all warehouses
   - Product Service displays "Out of Stock" message
   - Optional estimated restock date if available

4. **Limited Availability**
   - Quantity is below requested quantity but greater than zero
   - Product Service displays "Limited Availability" message

## Authentication and Authorization

Service-to-service authentication uses JWT tokens with service-specific roles:

1. **Inventory Service → Product Service**
   - Token includes the `inventory-service` role
   - Limited to specific product-related endpoints

2. **Product Service → Inventory Service**
   - Token includes the `product-service` role
   - Access limited to inventory query endpoints
   - No access to inventory management functions

## Error Handling

1. **Synchronous Error Handling**
   - API calls implement retry logic with exponential backoff
   - Circuit breaker pattern prevents cascading failures

2. **Asynchronous Error Handling**
   - Failed event processing is sent to a dead letter queue
   - Administrative interface for manual resolution
   - Periodic reconciliation jobs to fix inconsistencies

## Monitoring and Observability

1. **Distributed Tracing**
   - Correlation IDs link all operations between Product and Inventory services
   - Full request path visualization in Jaeger

2. **Health Checks**
   - Product Service exposes a health endpoint for the Inventory Service
   - Inventory Service checks Product Service health regularly

3. **Integration Metrics**
   - Event processing latency and error rates
   - API call success rates and response times
   - Inventory/product synchronization status

## Example: Real-Time Inventory Display Implementation

This section illustrates how the Product Service uses data from the Inventory Service to display inventory status:

```typescript
@Injectable()
export class ProductInventoryService {
  constructor(
    private readonly inventoryClient: InventoryServiceClient,
    private readonly cacheManager: ICacheManager,
    private readonly eventBus: EventBus,
    private readonly logger: Logger
  ) {
    // Subscribe to inventory events
    this.eventBus.subscribe(
      'StockLevelChanged',
      this.handleStockLevelChangedEvent.bind(this)
    );
    this.eventBus.subscribe(
      'OutOfStock',
      this.handleOutOfStockEvent.bind(this)
    );
  }

  async getProductAvailability(productId: string, requestedQuantity: number = 1): Promise<ProductAvailability> {
    // Try to get from cache first
    const cacheKey = `product_availability_${productId}_${requestedQuantity}`;
    const cachedAvailability = await this.cacheManager.get<ProductAvailability>(cacheKey);
    
    if (cachedAvailability) {
      return cachedAvailability;
    }
    
    try {
      // Fetch from Inventory Service
      const inventory = await this.inventoryClient.getInventoryByProduct(productId);
      
      // Calculate availability
      const availability = this.calculateAvailability(inventory, requestedQuantity);
      
      // Cache the result (short TTL for high-turnover products)
      const ttl = availability.isLowStock ? 60 : 300; // 1 minute for low stock, 5 minutes otherwise
      await this.cacheManager.set(cacheKey, availability, { ttl });
      
      return availability;
    } catch (error) {
      this.logger.error(`Failed to get availability for product ${productId}`, error);
      
      // Return default availability in case of error
      return {
        isAvailable: true, // Assume available by default to prevent lost sales
        displayStatus: 'IN_STOCK',
        message: 'In Stock',
        leadTimeEstimate: null
      };
    }
  }

  private calculateAvailability(inventory: ProductInventory, requestedQuantity: number): ProductAvailability {
    const totalAvailable = inventory.totalQuantityAvailable;
    const lowStockThreshold = 10; // This could be configured or fetched from the product
    
    if (totalAvailable === 0) {
      return {
        isAvailable: false,
        displayStatus: 'OUT_OF_STOCK',
        message: 'Out of Stock',
        leadTimeEstimate: inventory.restockExpected 
          ? `Expected back in stock ${this.formatRestockDate(inventory.restockExpected)}`
          : null
      };
    }
    
    if (totalAvailable < requestedQuantity) {
      return {
        isAvailable: true,
        displayStatus: 'LIMITED_AVAILABILITY',
        message: `Only ${totalAvailable} available`,
        leadTimeEstimate: null
      };
    }
    
    if (totalAvailable <= lowStockThreshold) {
      return {
        isAvailable: true,
        displayStatus: 'LOW_STOCK',
        message: `Only ${totalAvailable} left in stock - order soon`,
        leadTimeEstimate: null
      };
    }
    
    return {
      isAvailable: true,
      displayStatus: 'IN_STOCK',
      message: 'In Stock',
      leadTimeEstimate: this.calculateLeadTime(inventory)
    };
  }

  // Event handlers that invalidate cache when inventory changes
  private async handleStockLevelChangedEvent(event: StockLevelChangedEvent): Promise<void> {
    const productId = event.payload.productId;
    await this.invalidateProductCache(productId);
  }
  
  private async handleOutOfStockEvent(event: OutOfStockEvent): Promise<void> {
    const productId = event.payload.productId;
    await this.invalidateProductCache(productId);
  }
  
  private async invalidateProductCache(productId: string): Promise<void> {
    // Delete all cache entries for this product (with different quantities)
    const keys = await this.cacheManager.store.keys(`product_availability_${productId}_*`);
    for (const key of keys) {
      await this.cacheManager.del(key);
    }
    this.logger.debug(`Invalidated availability cache for product ${productId}`);
  }
}
```