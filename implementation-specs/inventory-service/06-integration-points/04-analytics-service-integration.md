# Analytics Service Integration

## Overview

The integration between Inventory Service and Analytics Service enables comprehensive reporting, business intelligence, and data-driven decision making. This integration allows the Analytics Service to collect, process, and analyze inventory data for strategic planning, operational efficiency, and business performance monitoring.

## Integration Patterns

The integration primarily uses event-driven communication with additional API access for historical and aggregated data:

```
┌───────────────────┐                   ┌───────────────────┐
│                   │                   │                   │
│    Inventory      │─── Events ───────▶│    Analytics      │
│    Service        │                   │    Service        │
│                   │◀─── API Calls ────│                   │
└───────────────────┘                   └────────┬──────────┘
                                                 │
                                                 │
                                                 ▼
                                        ┌───────────────────┐
                                        │                   │
                                        │   Data Lake &     │
                                        │   Warehousing     │
                                        │                   │
                                        └───────────────────┘
```

## Event-Driven Integration

### Events Consumed by Analytics Service

The Analytics Service consumes all events from the Inventory Service to build comprehensive data models and perform trend analysis.

1. **All Inventory Domain Events**
   - **Purpose**: Collect complete inventory activity for analytics processing
   - **Consumer Action**: Store in data lake, process for metrics and dashboards
   - **Exchange**: `inventory.events`
   - **Routing Key**: `inventory.#` (captures all inventory events)

   ```typescript
   // Analytics service event consumer
   @Injectable()
   export class InventoryEventConsumer {
     constructor(
       private readonly dataLakeService: DataLakeService,
       private readonly metricsService: MetricsService,
       private readonly logger: Logger
     ) {}

     @RabbitSubscribe({
       exchange: 'inventory.events',
       routingKey: 'inventory.#',
       queue: 'analytics.inventory.events'
     })
     async handleInventoryEvent(event: any, amqpMsg: ConsumeMessage): Promise<void> {
       const eventType = event.eventType;
       const timestamp = event.timestamp;
       
       try {
         // Log event to structured data lake
         await this.dataLakeService.storeEvent('inventory', eventType, event);
         
         // Update real-time metrics based on event type
         switch (eventType) {
           case 'StockLevelChanged':
             await this.processStockLevelChanged(event);
             break;
           case 'AllocationCreated':
             await this.processAllocationCreated(event);
             break;
           case 'AllocationFulfilled':
             await this.processAllocationFulfilled(event);
             break;
           // Handle other event types...
         }
         
         // Acknowledge successful processing
         amqpMsg.ack();
       } catch (error) {
         this.logger.error(`Failed to process inventory event: ${eventType}`, error);
         
         // Negative acknowledge for retry, with dead-letter after multiple failures
         amqpMsg.nack(false);
       }
     }
     
     private async processStockLevelChanged(event: StockLevelChangedEvent): Promise<void> {
       const { productId, warehouseId, previousQuantity, newQuantity, changeAmount } = event.payload;
       
       // Update inventory level metrics
       await this.metricsService.updateInventoryLevels(
         productId,
         warehouseId,
         newQuantity,
         event.timestamp
       );
       
       // Record inventory movement
       await this.metricsService.recordInventoryMovement({
         productId,
         warehouseId,
         changeAmount,
         changeType: event.payload.transactionType,
         timestamp: event.timestamp
       });
     }
     
     // Additional event processing methods...
   }
   ```

2. **Key Events of Interest**
   - **StockLevelChangedEvent**: Updates inventory levels and records movements
   - **AllocationCreatedEvent**: Tracks demand and reservation patterns
   - **AllocationFulfilledEvent**: Measures fulfillment rates and times
   - **LowStockThresholdReachedEvent**: Monitors inventory health
   - **OutOfStockEvent**: Tracks stockout frequency and duration

## API-Based Integration

### APIs Exposed by Inventory Service

These endpoints allow the Analytics Service to access aggregated and historical inventory data.

1. **Inventory Value Report**
   - **Endpoint**: `GET /reports/inventory-value`
   - **Purpose**: Retrieve aggregated inventory value data for financial analysis
   - **Query Parameters**:
     - `warehouseIds`: Optional filtering by warehouse
     - `categorize`: Group by product category
     - `asOfDate`: Historical point-in-time snapshot
   - **Response**:
     ```json
     {
       "success": true,
       "data": {
         "totalValue": 2345670.89,
         "timestamp": "2023-05-27T09:15:00Z",
         "warehouseSummary": [
           {
             "warehouseId": "wh_01HXYZ789GHI",
             "warehouseName": "North Seattle Fulfillment Center",
             "itemCount": 325,
             "totalValue": 1234567.89,
             "valuePercentage": 52.63
           },
           ...
         ],
         "categorySummary": [
           {
             "categoryId": "cat_01TXYZ123JKL",
             "categoryName": "Electronics",
             "itemCount": 230,
             "totalValue": 980345.75,
             "valuePercentage": 41.79
           },
           ...
         ]
       }
     }
     ```

2. **Stock Movements Report**
   - **Endpoint**: `GET /reports/stock-movements`
   - **Purpose**: Retrieve inventory movement data for trend analysis
   - **Query Parameters**:
     - `startDate`: Beginning of analysis period
     - `endDate`: End of analysis period
     - `warehouseIds`: Optional filtering by warehouse
     - `aggregateBy`: Time aggregation (day, week, month)

3. **Inventory Turnover Report**
   - **Endpoint**: `GET /reports/inventory-turnover`
   - **Purpose**: Retrieve inventory turnover metrics for efficiency analysis
   - **Query Parameters**:
     - `startDate`: Beginning of analysis period
     - `endDate`: End of analysis period
     - `categories`: Optional filtering by product category

4. **Stockout Report**
   - **Endpoint**: `GET /reports/stockout`
   - **Purpose**: Retrieve stockout incidents and impact metrics
   - **Query Parameters**:
     - `startDate`: Beginning of analysis period
     - `endDate`: End of analysis period
     - `minDuration`: Minimum stockout duration in hours

## Data Models and Metrics

The Analytics Service builds several data models from inventory events:

### 1. Inventory Level Time Series

Tracks inventory levels over time for trend analysis:

```typescript
interface InventoryLevelTimePoint {
  productId: string;
  sku: string;
  productName: string;
  categoryId: string;
  warehouseId: string;
  timestamp: string;
  quantityAvailable: number;
  quantityReserved: number;
  totalValue: number;
}
```

### 2. Inventory Movement Analysis

Tracks patterns in inventory movements:

```typescript
interface InventoryMovementAnalysis {
  productId: string;
  sku: string;
  productName: string;
  categoryId: string;
  warehouseId: string;
  period: string; // day, week, month
  receipts: number;
  sales: number;
  returns: number;
  adjustments: number;
  transfersIn: number;
  transfersOut: number;
  netChange: number;
}
```

### 3. Inventory KPIs

Calculates key performance indicators:

```typescript
interface InventoryKPI {
  productId?: string; // Optional - can be overall or per product
  categoryId?: string; // Optional - can be per category
  warehouseId?: string; // Optional - can be per warehouse
  period: string;
  turnoverRate: number;
  daysOfSupply: number;
  stockoutRate: number;
  stockoutDuration: number;
  fillRate: number;
  allocationSuccessRate: number;
  carryCost: number;
}
```

## ETL and Data Processing

The Analytics Service uses the following ETL processes for inventory data:

1. **Real-time Stream Processing**
   - Events are processed in real-time for updating current metrics
   - Kafka Streams or similar technology handles event processing

2. **Batch Processing**
   - Daily aggregation jobs for historical analysis
   - Scheduled jobs for complex metrics calculation

3. **Data Enrichment**
   - Combining inventory data with order, product, and cost data
   - Enhancing with third-party market data when available

```typescript
@Injectable()
export class InventoryDataPipeline {
  constructor(
    private readonly dataLakeService: DataLakeService,
    private readonly dataWarehouseService: DataWarehouseService,
    private readonly inventoryClient: InventoryServiceClient,
    private readonly productClient: ProductServiceClient,
    private readonly logger: Logger
  ) {}

  @Scheduled('0 2 * * *') // Run at 2 AM every day
  async runDailyInventoryETL(): Promise<void> {
    this.logger.log('Starting daily inventory ETL process');
    
    try {
      // Extract yesterday's data
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      yesterday.setHours(0, 0, 0, 0);
      
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      // Get raw events from data lake
      const events = await this.dataLakeService.getEventsByDateRange(
        'inventory',
        yesterday.toISOString(),
        today.toISOString()
      );
      
      // Transform events into analytical models
      const inventoryLevels = this.transformToInventoryLevels(events);
      const inventoryMovements = this.transformToInventoryMovements(events);
      
      // Enrich with product data
      await this.enrichWithProductData(inventoryLevels);
      await this.enrichWithProductData(inventoryMovements);
      
      // Calculate daily KPIs
      const kpis = await this.calculateDailyKPIs(inventoryLevels, inventoryMovements);
      
      // Load data into data warehouse
      await this.dataWarehouseService.loadInventoryLevels(inventoryLevels);
      await this.dataWarehouseService.loadInventoryMovements(inventoryMovements);
      await this.dataWarehouseService.loadInventoryKPIs(kpis);
      
      this.logger.log('Completed daily inventory ETL process');
    } catch (error) {
      this.logger.error('Failed to complete daily inventory ETL process', error);
      throw error;
    }
  }
  
  // Implementation of transformation, enrichment, and calculation methods...
}
```

## Dashboard and Reporting

The Analytics Service provides several inventory-related dashboards:

1. **Inventory Overview Dashboard**
   - Total inventory value and trends
   - Stock distribution by warehouse
   - Top and bottom performing products by turnover

2. **Inventory Health Dashboard**
   - Low stock and out-of-stock items
   - Stockout frequency and duration
   - Reorder recommendations

3. **Inventory Performance Dashboard**
   - Turnover rates by category and product
   - Fill rate and service levels
   - Carrying costs and optimization opportunities

## Predictive Analytics

The Analytics Service uses inventory data for predictive models:

1. **Demand Forecasting**
   - Predict future demand based on historical data
   - Account for seasonality and trends

2. **Stockout Prediction**
   - Identify products at risk of stockout
   - Prioritize reordering based on risk

3. **Optimal Stock Level Recommendation**
   - Suggest optimal stock levels to minimize costs
   - Balance carrying costs against stockout risks

```typescript
@Injectable()
export class InventoryPredictiveAnalytics {
  constructor(
    private readonly modelService: PredictiveModelService,
    private readonly dataWarehouseService: DataWarehouseService
  ) {}

  async predictDemand(productId: string, daysAhead: number): Promise<DemandForecast> {
    // Get historical data
    const historicalData = await this.dataWarehouseService.getProductSalesHistory(productId);
    
    // Prepare data for model
    const preparedData = this.prepareDataForDemandModel(historicalData);
    
    // Generate forecast
    const forecast = await this.modelService.forecast('demand', preparedData, daysAhead);
    
    // Format and return forecast
    return {
      productId,
      forecastPeriods: forecast.map(f => ({
        date: f.date,
        predictedDemand: f.value,
        confidenceLow: f.confidenceLow,
        confidenceHigh: f.confidenceHigh
      })),
      aggregatedDemand: forecast.reduce((sum, f) => sum + f.value, 0),
      modelAccuracy: forecast.accuracy
    };
  }
  
  async recommendStockLevels(productId: string): Promise<StockLevelRecommendation> {
    // Get product details
    const product = await this.dataWarehouseService.getProductMetrics(productId);
    
    // Get demand forecast
    const forecast = await this.predictDemand(productId, 90); // 90-day forecast
    
    // Calculate economic order quantity
    const eoq = this.calculateEconomicOrderQuantity(
      forecast.aggregatedDemand / 90 * 365, // Annual demand
      product.orderingCost,
      product.carryingCostPercentage,
      product.unitCost
    );
    
    // Calculate reorder point
    const reorderPoint = this.calculateReorderPoint(
      forecast.forecastPeriods.slice(0, product.leadTime).reduce((sum, f) => sum + f.predictedDemand, 0), // Lead time demand
      product.serviceLevel,
      product.demandStdDev,
      product.leadTime
    );
    
    return {
      productId,
      sku: product.sku,
      recommendedTargetStockLevel: Math.round(eoq),
      recommendedReorderThreshold: Math.round(reorderPoint),
      safetyStock: Math.round(reorderPoint - (forecast.aggregatedDemand / 90 * product.leadTime)),
      economicOrderQuantity: Math.round(eoq),
      expectedAnnualCarryingCost: eoq / 2 * product.unitCost * product.carryingCostPercentage,
      expectedAnnualOrderingCost: (forecast.aggregatedDemand / 90 * 365) / eoq * product.orderingCost,
      serviceLevel: product.serviceLevel
    };
  }
  
  // Helper methods for calculations...
}
```

## Machine Learning Applications

The Analytics Service applies machine learning to inventory data:

1. **Anomaly Detection**
   - Identify unusual inventory movements
   - Flag potential theft, damage, or system errors

2. **Product Segmentation**
   - Classify products by movement patterns
   - Tailor inventory strategies by segment

3. **Cross-Product Correlation**
   - Identify products with correlated demand
   - Optimize stock levels based on relationships

## Data Security and Governance

1. **Data Masking and Anonymization**
   - Sensitive values are masked in analytical data
   - Cost information is restricted by role

2. **Data Retention Policies**
   - Raw events: 90 days
   - Aggregated data: 7 years
   - KPIs and metrics: Indefinite

3. **Access Control**
   - Role-based access to analytical dashboards
   - Fine-grained permissions for sensitive metrics

## Authentication and Authorization

Service-to-service authentication uses JWT tokens with service-specific roles:

1. **Analytics Service → Inventory Service**
   - Token includes the `analytics-service` role
   - Access limited to reporting endpoints
   - Read-only access to inventory data

## Error Handling and Resilience

1. **Event Processing Errors**
   - Failed event processing is retried with backoff
   - Dead letter queue for manual resolution
   - Missing events are reconciled in daily batch process

2. **API Call Failures**
   - Circuit breaker prevents cascading failures
   - Fallback to cached data when available

## Example Use Cases

### Inventory Optimization

The Analytics Service helps optimize inventory levels by:

1. Analyzing historical demand patterns
2. Calculating optimal safety stock levels
3. Recommending reorder thresholds
4. Simulating various stocking strategies

### Financial Reporting

The Analytics Service supports financial reporting by:

1. Providing accurate inventory valuation
2. Tracking inventory write-offs and adjustments
3. Calculating carrying costs
4. Measuring inventory as percentage of assets

### Supply Chain Visibility

The Analytics Service improves supply chain visibility by:

1. Tracking end-to-end product flow
2. Measuring warehouse performance
3. Identifying bottlenecks and constraints
4. Monitoring supplier performance through receipt analysis