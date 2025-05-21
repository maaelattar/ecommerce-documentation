# Reporting Endpoints

## Overview

Reporting endpoints provide access to aggregated inventory data, analytics, and operational insights. These endpoints support business intelligence, inventory optimization, and operational decision-making.

## Base URL

```
https://api.example.com/inventory/v1
```

## Endpoints

### Low Stock Report

Retrieves a report of inventory items that are at or below their reorder threshold.

```
GET /reports/low-stock
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| warehouseId | string | Filter by warehouse ID |
| thresholdPercentage | integer | Custom threshold percentage (1-100, default: 100) |
| includeZeroStock | boolean | Include out-of-stock items (default: true) |
| sortBy | string | Sort field (name, sku, daysUntilStockout) |
| sortDir | string | Sort direction (asc, desc) |

#### Response

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "inv_01GXYZ345QRS",
        "sku": "GADGET-1",
        "name": "Smart Gadget",
        "productId": "prod_01FXYZ890DEF",
        "warehouseId": "wh_01HXYZ789GHI",
        "warehouseName": "North Seattle Fulfillment Center",
        "quantityAvailable": 5,
        "quantityReserved": 2,
        "reorderThreshold": 10,
        "targetStockLevel": 50,
        "thresholdPercentage": 50,
        "daysUntilStockout": 3,
        "averageDailyUsage": 1.67,
        "lastOrderDate": "2023-05-01T10:30:00Z",
        "suggestedOrderQuantity": 45
      },
      {
        "id": "inv_01GXYZ456TUV",
        "sku": "ACCESSORY-1",
        "name": "Premium Accessory",
        "productId": "prod_01FXYZ901GHI",
        "warehouseId": "wh_01HXYZ789GHI",
        "warehouseName": "North Seattle Fulfillment Center",
        "quantityAvailable": 0,
        "quantityReserved": 0,
        "reorderThreshold": 5,
        "targetStockLevel": 25,
        "thresholdPercentage": 0,
        "daysUntilStockout": 0,
        "averageDailyUsage": 0.83,
        "lastOrderDate": "2023-04-15T14:45:00Z",
        "suggestedOrderQuantity": 25
      }
    ],
    "summary": {
      "totalItems": 24,
      "criticalItems": 5,
      "lowStockItems": 19,
      "outOfStockItems": 5,
      "totalSuggestedOrderValue": 12750.50
    }
  },
  "meta": {
    "generatedAt": "2023-05-27T08:30:00Z",
    "parameters": {
      "warehouseId": "wh_01HXYZ789GHI",
      "thresholdPercentage": 100,
      "includeZeroStock": true
    }
  }
}
```

### Inventory Value Report

Retrieves a report of inventory value across warehouses.

```
GET /reports/inventory-value
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| warehouseIds | string | Comma-separated list of warehouse IDs |
| categorize | boolean | Group by product category (default: true) |
| includeInactive | boolean | Include inactive items (default: false) |

#### Response

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
      {
        "warehouseId": "wh_01HXYZ890PQR",
        "warehouseName": "South Portland Distribution Center",
        "itemCount": 412,
        "totalValue": 1111103.00,
        "valuePercentage": 47.37
      }
    ],
    "categorySummary": [
      {
        "categoryId": "cat_01TXYZ123JKL",
        "categoryName": "Electronics",
        "itemCount": 230,
        "totalValue": 980345.75,
        "valuePercentage": 41.79
      },
      {
        "categoryId": "cat_01TXYZ234LMN",
        "categoryName": "Home Goods",
        "itemCount": 315,
        "totalValue": 750890.45,
        "valuePercentage": 32.01
      },
      {
        "categoryId": "cat_01TXYZ345NOP",
        "categoryName": "Apparel",
        "itemCount": 192,
        "totalValue": 614434.69,
        "valuePercentage": 26.20
      }
    ]
  },
  "meta": {
    "generatedAt": "2023-05-27T09:15:00Z",
    "parameters": {
      "warehouseIds": "all",
      "categorize": true,
      "includeInactive": false
    }
  }
}
```

### Stock Movements Report

Retrieves a report of inventory movements over a specified time period.

```
GET /reports/stock-movements
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startDate | string | Start date (ISO format, required) |
| endDate | string | End date (ISO format, required) |
| warehouseIds | string | Comma-separated list of warehouse IDs |
| inventoryItemIds | string | Comma-separated list of inventory item IDs |
| categories | string | Comma-separated list of product category IDs |
| transactionTypes | string | Comma-separated list of transaction types |
| aggregateBy | string | Time aggregation (day, week, month) |

#### Response

```json
{
  "success": true,
  "data": {
    "summary": {
      "startDate": "2023-05-01T00:00:00Z",
      "endDate": "2023-05-31T23:59:59Z",
      "openingStock": 3456,
      "receipts": 789,
      "sales": -543,
      "returns": 47,
      "adjustments": -65,
      "transfersIn": 321,
      "transfersOut": -321,
      "closingStock": 3684,
      "netChange": 228,
      "turnoverRate": 0.15
    },
    "timeSeriesData": [
      {
        "period": "2023-05-01 - 2023-05-07",
        "receipts": 210,
        "sales": -125,
        "returns": 12,
        "adjustments": -18,
        "transfersIn": 78,
        "transfersOut": -78,
        "netChange": 79
      },
      {
        "period": "2023-05-08 - 2023-05-14",
        "receipts": 185,
        "sales": -142,
        "returns": 9,
        "adjustments": -15,
        "transfersIn": 65,
        "transfersOut": -65,
        "netChange": 37
      },
      {
        "period": "2023-05-15 - 2023-05-21",
        "receipts": 195,
        "sales": -156,
        "returns": 14,
        "adjustments": -12,
        "transfersIn": 92,
        "transfersOut": -92,
        "netChange": 41
      },
      {
        "period": "2023-05-22 - 2023-05-31",
        "receipts": 199,
        "sales": -120,
        "returns": 12,
        "adjustments": -20,
        "transfersIn": 86,
        "transfersOut": -86,
        "netChange": 71
      }
    ],
    "topItems": [
      {
        "id": "inv_01GXYZ234DEF",
        "sku": "WIDGET-2",
        "name": "Widget Deluxe Plus",
        "receipts": 75,
        "sales": -32,
        "netChange": 43
      },
      {
        "id": "inv_01GXYZ345QRS",
        "sku": "GADGET-1",
        "name": "Smart Gadget",
        "receipts": 65,
        "sales": -48,
        "netChange": 17
      }
    ],
    "warehouseBreakdown": [
      {
        "warehouseId": "wh_01HXYZ789GHI",
        "warehouseName": "North Seattle Fulfillment Center",
        "receipts": 420,
        "sales": -315,
        "returns": 32,
        "adjustments": -38,
        "transfersIn": 135,
        "transfersOut": -186,
        "netChange": 48
      },
      {
        "warehouseId": "wh_01HXYZ890PQR",
        "warehouseName": "South Portland Distribution Center",
        "receipts": 369,
        "sales": -228,
        "returns": 15,
        "adjustments": -27,
        "transfersIn": 186,
        "transfersOut": -135,
        "netChange": 180
      }
    ]
  },
  "meta": {
    "generatedAt": "2023-05-27T10:30:00Z",
    "parameters": {
      "startDate": "2023-05-01T00:00:00Z",
      "endDate": "2023-05-31T23:59:59Z",
      "warehouseIds": "all",
      "aggregateBy": "week"
    }
  }
}
```

### Allocations Report

Retrieves a report of inventory allocations and their status.

```
GET /reports/allocations
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startDate | string | Start date (ISO format) |
| endDate | string | End date (ISO format) |
| warehouseIds | string | Comma-separated list of warehouse IDs |
| status | string | Filter by allocation status |
| aggregateBy | string | Time aggregation (day, week, month) |

#### Response

```json
{
  "success": true,
  "data": {
    "summary": {
      "totalAllocations": 432,
      "totalQuantity": 876,
      "statusBreakdown": {
        "PENDING": {
          "count": 87,
          "quantity": 165,
          "percentage": 20.14
        },
        "CONFIRMED": {
          "count": 104,
          "quantity": 224,
          "percentage": 24.07
        },
        "FULFILLED": {
          "count": 215,
          "quantity": 425,
          "percentage": 49.77
        },
        "CANCELLED": {
          "count": 26,
          "quantity": 62,
          "percentage": 6.02
        }
      },
      "averageFulfillmentTime": "1.5 days",
      "cancellationRate": 6.02
    },
    "timeSeriesData": [
      {
        "period": "2023-05-01 - 2023-05-07",
        "created": 105,
        "confirmed": 98,
        "fulfilled": 85,
        "cancelled": 7
      },
      {
        "period": "2023-05-08 - 2023-05-14",
        "created": 118,
        "confirmed": 110,
        "fulfilled": 92,
        "cancelled": 8
      },
      {
        "period": "2023-05-15 - 2023-05-21",
        "created": 97,
        "confirmed": 95,
        "fulfilled": 83,
        "cancelled": 4
      },
      {
        "period": "2023-05-22 - 2023-05-31",
        "created": 112,
        "confirmed": 106,
        "fulfilled": 90,
        "cancelled": 7
      }
    ],
    "topAllocatedItems": [
      {
        "id": "inv_01GXYZ234DEF",
        "sku": "WIDGET-2",
        "name": "Widget Deluxe Plus",
        "allocatedQuantity": 78,
        "pendingQuantity": 15,
        "fulfilledQuantity": 63
      },
      {
        "id": "inv_01GXYZ345QRS",
        "sku": "GADGET-1",
        "name": "Smart Gadget",
        "allocatedQuantity": 65,
        "pendingQuantity": 12,
        "fulfilledQuantity": 53
      }
    ],
    "warehouseBreakdown": [
      {
        "warehouseId": "wh_01HXYZ789GHI",
        "warehouseName": "North Seattle Fulfillment Center",
        "allocations": 245,
        "quantity": 498,
        "pendingQuantity": 85,
        "fulfilledQuantity": 413
      },
      {
        "warehouseId": "wh_01HXYZ890PQR",
        "warehouseName": "South Portland Distribution Center",
        "allocations": 187,
        "quantity": 378,
        "pendingQuantity": 65,
        "fulfilledQuantity": 313
      }
    ]
  },
  "meta": {
    "generatedAt": "2023-05-27T11:45:00Z",
    "parameters": {
      "startDate": "2023-05-01T00:00:00Z",
      "endDate": "2023-05-31T23:59:59Z",
      "warehouseIds": "all",
      "aggregateBy": "week"
    }
  }
}
```

### Inventory Turnover Report

Retrieves a report of inventory turnover, showing how quickly inventory is sold and replenished.

```
GET /reports/inventory-turnover
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startDate | string | Start date (ISO format, required) |
| endDate | string | End date (ISO format, required) |
| warehouseIds | string | Comma-separated list of warehouse IDs |
| categories | string | Comma-separated list of product category IDs |

#### Response

```json
{
  "success": true,
  "data": {
    "summary": {
      "period": "2023-01-01 - 2023-05-31",
      "averageTurnoverRate": 3.8,
      "averageDaysInInventory": 96.1,
      "fastMovingThreshold": 6.0,
      "slowMovingThreshold": 2.0
    },
    "turnoverByCategory": [
      {
        "categoryId": "cat_01TXYZ123JKL",
        "categoryName": "Electronics",
        "turnoverRate": 4.5,
        "daysInInventory": 81.1,
        "classification": "Fast"
      },
      {
        "categoryId": "cat_01TXYZ234LMN",
        "categoryName": "Home Goods",
        "turnoverRate": 3.2,
        "daysInInventory": 114.1,
        "classification": "Medium"
      },
      {
        "categoryId": "cat_01TXYZ345NOP",
        "categoryName": "Apparel",
        "turnoverRate": 5.6,
        "daysInInventory": 65.2,
        "classification": "Fast"
      }
    ],
    "turnoverByWarehouse": [
      {
        "warehouseId": "wh_01HXYZ789GHI",
        "warehouseName": "North Seattle Fulfillment Center",
        "turnoverRate": 4.2,
        "daysInInventory": 86.9
      },
      {
        "warehouseId": "wh_01HXYZ890PQR",
        "warehouseName": "South Portland Distribution Center",
        "turnoverRate": 3.5,
        "daysInInventory": 104.3
      }
    ],
    "topTurnoverItems": [
      {
        "id": "inv_01GXYZ567UVW",
        "sku": "TRENDY-1",
        "name": "Trending Fashion Item",
        "turnoverRate": 9.8,
        "daysInInventory": 37.2,
        "averageInventory": 45,
        "totalSold": 441
      }
    ],
    "slowMovingItems": [
      {
        "id": "inv_01GXYZ678VWX",
        "sku": "LEGACY-2",
        "name": "Legacy Product Model",
        "turnoverRate": 0.7,
        "daysInInventory": 521.4,
        "averageInventory": 32,
        "totalSold": 22,
        "daysSinceLastSale": 45
      }
    ]
  },
  "meta": {
    "generatedAt": "2023-05-27T13:00:00Z",
    "parameters": {
      "startDate": "2023-01-01T00:00:00Z",
      "endDate": "2023-05-31T23:59:59Z",
      "warehouseIds": "all"
    }
  }
}
```

### Top Moving Items Report

Retrieves a report of the most active inventory items based on sales, receipts, or overall movement.

```
GET /reports/top-moving-items
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startDate | string | Start date (ISO format, required) |
| endDate | string | End date (ISO format, required) |
| warehouseIds | string | Comma-separated list of warehouse IDs |
| movementType | string | Type of movement to rank by (SALES, RECEIPTS, ALL) |
| limit | integer | Maximum number of items to return (default: 10, max: 100) |

#### Response

```json
{
  "success": true,
  "data": {
    "period": "2023-01-01 - 2023-05-31",
    "movementType": "SALES",
    "items": [
      {
        "id": "inv_01GXYZ567UVW",
        "sku": "TRENDY-1",
        "name": "Trending Fashion Item",
        "salesQuantity": 441,
        "salesValue": 22050.00,
        "percentageOfTotalSales": 8.5,
        "returnsQuantity": 12,
        "returnRate": 2.72,
        "currentStock": 68
      },
      {
        "id": "inv_01GXYZ345QRS",
        "sku": "GADGET-1",
        "name": "Smart Gadget",
        "salesQuantity": 352,
        "salesValue": 17600.00,
        "percentageOfTotalSales": 6.8,
        "returnsQuantity": 8,
        "returnRate": 2.27,
        "currentStock": 35
      },
      {
        "id": "inv_01GXYZ234DEF",
        "sku": "WIDGET-2",
        "name": "Widget Deluxe Plus",
        "salesQuantity": 315,
        "salesValue": 14175.00,
        "percentageOfTotalSales": 5.5,
        "returnsQuantity": 4,
        "returnRate": 1.27,
        "currentStock": 60
      }
      // Additional items...
    ],
    "summary": {
      "totalSales": 5175,
      "totalSalesValue": 258750.00,
      "averageReturnRate": 2.8,
      "topItemsPercentage": 21.5
    }
  },
  "meta": {
    "generatedAt": "2023-05-27T14:15:00Z",
    "parameters": {
      "startDate": "2023-01-01T00:00:00Z",
      "endDate": "2023-05-31T23:59:59Z",
      "warehouseIds": "all",
      "movementType": "SALES",
      "limit": 10
    }
  }
}
```

### Stockout Report

Retrieves a report of stockout incidents and their impact.

```
GET /reports/stockout
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startDate | string | Start date (ISO format, required) |
| endDate | string | End date (ISO format, required) |
| warehouseIds | string | Comma-separated list of warehouse IDs |
| minDuration | integer | Minimum stockout duration in hours |

#### Response

```json
{
  "success": true,
  "data": {
    "summary": {
      "period": "2023-01-01 - 2023-05-31",
      "totalStockouts": 87,
      "totalStockoutDays": 342,
      "averageStockoutDuration": "3.9 days",
      "estimatedLostSales": 431,
      "estimatedLostRevenue": 21550.00
    },
    "stockoutsByMonth": [
      {
        "month": "January 2023",
        "stockouts": 22,
        "averageDuration": "4.2 days"
      },
      {
        "month": "February 2023",
        "stockouts": 15,
        "averageDuration": "3.8 days"
      },
      {
        "month": "March 2023",
        "stockouts": 18,
        "averageDuration": "3.5 days"
      },
      {
        "month": "April 2023",
        "stockouts": 14,
        "averageDuration": "4.1 days"
      },
      {
        "month": "May 2023",
        "stockouts": 18,
        "averageDuration": "3.8 days"
      }
    ],
    "mostFrequentStockouts": [
      {
        "id": "inv_01GXYZ456TUV",
        "sku": "ACCESSORY-1",
        "name": "Premium Accessory",
        "stockoutCount": 4,
        "totalDuration": "24 days",
        "lastStockoutDate": "2023-05-15T00:00:00Z",
        "currentStatus": "out-of-stock",
        "estimatedLostSales": 48
      },
      {
        "id": "inv_01GXYZ789XYZ",
        "sku": "SEASONAL-3",
        "name": "Seasonal Product",
        "stockoutCount": 3,
        "totalDuration": "18 days",
        "lastStockoutDate": "2023-04-10T00:00:00Z",
        "currentStatus": "in-stock",
        "estimatedLostSales": 36
      }
    ],
    "warehouseBreakdown": [
      {
        "warehouseId": "wh_01HXYZ789GHI",
        "warehouseName": "North Seattle Fulfillment Center",
        "stockouts": 42,
        "totalDuration": "156 days",
        "averageDuration": "3.7 days"
      },
      {
        "warehouseId": "wh_01HXYZ890PQR",
        "warehouseName": "South Portland Distribution Center",
        "stockouts": 45,
        "totalDuration": "186 days",
        "averageDuration": "4.1 days"
      }
    ]
  },
  "meta": {
    "generatedAt": "2023-05-27T15:30:00Z",
    "parameters": {
      "startDate": "2023-01-01T00:00:00Z",
      "endDate": "2023-05-31T23:59:59Z",
      "warehouseIds": "all",
      "minDuration": 0
    }
  }
}
```

## Error Responses

### Invalid Date Range

```json
{
  "success": false,
  "error": {
    "code": "INVALID_DATE_RANGE",
    "message": "End date must be after start date",
    "details": {
      "startDate": "2023-06-01T00:00:00Z",
      "endDate": "2023-05-01T00:00:00Z"
    }
  }
}
```

### Invalid Parameter

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid movement type specified",
    "details": {
      "parameter": "movementType",
      "value": "UNKNOWN",
      "allowedValues": ["SALES", "RECEIPTS", "ALL"]
    }
  }
}
```

### Report Generation Failed

```json
{
  "success": false,
  "error": {
    "code": "REPORT_GENERATION_FAILED",
    "message": "Failed to generate report due to internal error",
    "details": {
      "reason": "Data aggregation timeout"
    }
  }
}
```