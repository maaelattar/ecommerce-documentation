# Inventory Item Endpoints

## Overview

Inventory Item endpoints provide capabilities for managing inventory items, including creating, updating, and querying inventory data, as well as performing stock operations like adding, adjusting, and transferring inventory.

## Base URL

```
https://api.example.com/inventory/v1
```

## Endpoints

### List Inventory Items

Retrieves a paginated list of inventory items with optional filtering.

```
GET /inventory-items
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |
| search | string | Search term for item name or SKU |
| warehouseId | string | Filter by warehouse ID |
| productId | string | Filter by product ID |
| minQuantity | integer | Filter by minimum available quantity |
| maxQuantity | integer | Filter by maximum available quantity |
| isActive | boolean | Filter by active status (default: true) |
| sortBy | string | Sort field (name, sku, quantityAvailable) |
| sortDir | string | Sort direction (asc, desc) |

#### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "inv_01GXYZ123ABC",
      "sku": "WIDGET-1",
      "productId": "prod_01FXYZ456DEF",
      "name": "Widget Pro",
      "description": "Professional grade widget",
      "quantityAvailable": 100,
      "quantityReserved": 25,
      "warehouseId": "wh_01HXYZ789GHI",
      "warehouseName": "North Warehouse", 
      "reorderThreshold": 20,
      "targetStockLevel": 120,
      "isActive": true,
      "createdAt": "2023-04-15T10:30:00Z",
      "updatedAt": "2023-04-20T14:45:00Z"
    }
    // Additional items...
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "totalItems": 135,
    "totalPages": 7
  }
}
```

### Get Inventory Item

Retrieves details for a specific inventory item.

```
GET /inventory-items/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Inventory item ID |

#### Response

```json
{
  "success": true,
  "data": {
    "id": "inv_01GXYZ123ABC",
    "sku": "WIDGET-1",
    "productId": "prod_01FXYZ456DEF",
    "name": "Widget Pro",
    "description": "Professional grade widget",
    "quantityAvailable": 100,
    "quantityReserved": 25,
    "warehouseId": "wh_01HXYZ789GHI",
    "warehouseName": "North Warehouse",
    "reorderThreshold": 20,
    "targetStockLevel": 120,
    "locations": [
      {
        "locationId": "loc_01JXYZ101KLM",
        "locationCode": "A-01-B-02",
        "quantity": 75
      },
      {
        "locationId": "loc_01JXYZ202NOP",
        "locationCode": "A-02-C-05",
        "quantity": 25
      }
    ],
    "isActive": true,
    "createdAt": "2023-04-15T10:30:00Z",
    "updatedAt": "2023-04-20T14:45:00Z",
    "metadata": {
      "supplier": "Acme Corp",
      "weight": "2.5kg",
      "dimensions": "10x15x5cm"
    }
  }
}
```

### Create Inventory Item

Creates a new inventory item.

```
POST /inventory-items
```

#### Request Body

```json
{
  "sku": "WIDGET-2",
  "productId": "prod_01FXYZ789ABC",
  "name": "Widget Deluxe",
  "description": "Deluxe version of our popular widget",
  "initialQuantity": 50,
  "warehouseId": "wh_01HXYZ789GHI",
  "reorderThreshold": 10,
  "targetStockLevel": 60,
  "metadata": {
    "supplier": "Acme Corp",
    "weight": "3.0kg",
    "dimensions": "12x18x7cm"
  }
}
```

#### Required Fields

- `sku`
- `productId`
- `name`
- `warehouseId`
- `initialQuantity` (must be non-negative)
- `reorderThreshold`
- `targetStockLevel` (must be greater than reorderThreshold)

#### Response

```json
{
  "success": true,
  "data": {
    "id": "inv_01GXYZ234DEF",
    "sku": "WIDGET-2",
    "productId": "prod_01FXYZ789ABC",
    "name": "Widget Deluxe",
    "description": "Deluxe version of our popular widget",
    "quantityAvailable": 50,
    "quantityReserved": 0,
    "warehouseId": "wh_01HXYZ789GHI",
    "warehouseName": "North Warehouse",
    "reorderThreshold": 10,
    "targetStockLevel": 60,
    "isActive": true,
    "createdAt": "2023-05-10T09:20:00Z",
    "updatedAt": "2023-05-10T09:20:00Z",
    "metadata": {
      "supplier": "Acme Corp",
      "weight": "3.0kg",
      "dimensions": "12x18x7cm"
    }
  }
}
```

### Update Inventory Item

Updates an existing inventory item.

```
PUT /inventory-items/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Inventory item ID |

#### Request Body

```json
{
  "name": "Widget Deluxe Plus",
  "description": "Enhanced deluxe version of our popular widget",
  "reorderThreshold": 15,
  "targetStockLevel": 75,
  "metadata": {
    "supplier": "Acme Corp Premium",
    "weight": "3.2kg",
    "dimensions": "12x18x7cm"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": "inv_01GXYZ234DEF",
    "sku": "WIDGET-2",
    "productId": "prod_01FXYZ789ABC",
    "name": "Widget Deluxe Plus",
    "description": "Enhanced deluxe version of our popular widget",
    "quantityAvailable": 50,
    "quantityReserved": 0,
    "warehouseId": "wh_01HXYZ789GHI",
    "warehouseName": "North Warehouse",
    "reorderThreshold": 15,
    "targetStockLevel": 75,
    "isActive": true,
    "createdAt": "2023-05-10T09:20:00Z",
    "updatedAt": "2023-05-10T11:45:00Z",
    "metadata": {
      "supplier": "Acme Corp Premium",
      "weight": "3.2kg",
      "dimensions": "12x18x7cm"
    }
  }
}
```

### Deactivate Inventory Item

Deactivates an inventory item, making it unavailable for new allocations.

```
DELETE /inventory-items/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Inventory item ID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| reason | string | Reason for deactivation (required) |

#### Response

```json
{
  "success": true,
  "data": {
    "id": "inv_01GXYZ234DEF",
    "isActive": false,
    "deactivatedAt": "2023-05-15T14:30:00Z",
    "deactivationReason": "Product discontinued"
  }
}
```

### Add Stock

Adds stock to an inventory item.

```
POST /inventory-items/{id}/add-stock
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Inventory item ID |

#### Request Body

```json
{
  "quantity": 25,
  "referenceNumber": "PO-12345",
  "referenceType": "PURCHASE_ORDER",
  "reason": "Scheduled stock replenishment",
  "lotNumber": "LOT-2023-05-01",
  "expirationDate": "2025-05-01T00:00:00Z",
  "locationId": "loc_01JXYZ101KLM",
  "metadata": {
    "receivedBy": "John Smith",
    "quality": "A-Grade"
  }
}
```

#### Required Fields

- `quantity` (must be positive)

#### Response

```json
{
  "success": true,
  "data": {
    "transaction": {
      "id": "tx_01KXYZ345GHI",
      "type": "RECEIPT",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "quantity": 25,
      "warehouseId": "wh_01HXYZ789GHI",
      "locationId": "loc_01JXYZ101KLM",
      "referenceNumber": "PO-12345",
      "referenceType": "PURCHASE_ORDER",
      "reason": "Scheduled stock replenishment",
      "lotNumber": "LOT-2023-05-01",
      "expirationDate": "2025-05-01T00:00:00Z",
      "createdAt": "2023-05-20T10:15:00Z",
      "createdBy": "user_01LXYZ456JKL"
    },
    "inventoryItem": {
      "id": "inv_01GXYZ234DEF",
      "previousQuantity": 50,
      "newQuantity": 75,
      "updatedAt": "2023-05-20T10:15:00Z"
    }
  }
}
```

### Adjust Stock

Adjusts the stock level of an inventory item (increase or decrease).

```
POST /inventory-items/{id}/adjust-stock
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Inventory item ID |

#### Request Body

```json
{
  "quantity": -5,
  "reason": "Damaged during handling",
  "referenceNumber": "ADJ-6789",
  "referenceType": "INVENTORY_ADJUSTMENT",
  "locationId": "loc_01JXYZ101KLM",
  "metadata": {
    "adjustedBy": "Jane Doe",
    "approvedBy": "Manager Smith"
  }
}
```

#### Required Fields

- `quantity` (positive for increase, negative for decrease)
- `reason` (required for all adjustments)

#### Response

```json
{
  "success": true,
  "data": {
    "transaction": {
      "id": "tx_01KXYZ567MNO",
      "type": "ADJUSTMENT",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "quantity": -5,
      "warehouseId": "wh_01HXYZ789GHI",
      "locationId": "loc_01JXYZ101KLM",
      "referenceNumber": "ADJ-6789",
      "referenceType": "INVENTORY_ADJUSTMENT",
      "reason": "Damaged during handling",
      "createdAt": "2023-05-21T14:30:00Z",
      "createdBy": "user_01LXYZ567MNO"
    },
    "inventoryItem": {
      "id": "inv_01GXYZ234DEF",
      "previousQuantity": 75,
      "newQuantity": 70,
      "updatedAt": "2023-05-21T14:30:00Z"
    }
  }
}
```

### Transfer Stock

Transfers stock between warehouses.

```
POST /inventory-items/{id}/transfer
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Inventory item ID |

#### Request Body

```json
{
  "quantity": 10,
  "sourceWarehouseId": "wh_01HXYZ789GHI",
  "destinationWarehouseId": "wh_01HXYZ890PQR",
  "sourceLocationId": "loc_01JXYZ101KLM",
  "destinationLocationId": "loc_01JXYZ678STU",
  "reason": "Balancing warehouse inventory",
  "referenceNumber": "TR-9012",
  "referenceType": "STOCK_TRANSFER",
  "metadata": {
    "shippingMethod": "Internal Truck",
    "estimatedArrival": "2023-05-25T00:00:00Z"
  }
}
```

#### Required Fields

- `quantity` (must be positive)
- `sourceWarehouseId`
- `destinationWarehouseId`

#### Response

```json
{
  "success": true,
  "data": {
    "outboundTransaction": {
      "id": "tx_01KXYZ678VWX",
      "type": "TRANSFER_OUT",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "quantity": 10,
      "warehouseId": "wh_01HXYZ789GHI",
      "locationId": "loc_01JXYZ101KLM",
      "destinationWarehouseId": "wh_01HXYZ890PQR",
      "referenceNumber": "TR-9012",
      "referenceType": "STOCK_TRANSFER",
      "reason": "Balancing warehouse inventory",
      "createdAt": "2023-05-22T09:45:00Z",
      "createdBy": "user_01LXYZ678STU"
    },
    "inboundTransaction": {
      "id": "tx_01KXYZ789YZA",
      "type": "TRANSFER_IN",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "quantity": 10,
      "warehouseId": "wh_01HXYZ890PQR",
      "locationId": "loc_01JXYZ678STU",
      "sourceWarehouseId": "wh_01HXYZ789GHI",
      "referenceNumber": "TR-9012",
      "referenceType": "STOCK_TRANSFER",
      "reason": "Balancing warehouse inventory",
      "createdAt": "2023-05-22T09:45:00Z",
      "createdBy": "user_01LXYZ678STU"
    },
    "sourceItem": {
      "id": "inv_01GXYZ234DEF",
      "warehouseId": "wh_01HXYZ789GHI",
      "previousQuantity": 70,
      "newQuantity": 60,
      "updatedAt": "2023-05-22T09:45:00Z"
    },
    "destinationItem": {
      "id": "inv_01MXYZ890BCD",
      "warehouseId": "wh_01HXYZ890PQR",
      "previousQuantity": 0,
      "newQuantity": 10,
      "updatedAt": "2023-05-22T09:45:00Z"
    }
  }
}
```

### Get Transactions for Item

Retrieves stock transactions for a specific inventory item.

```
GET /inventory-items/{id}/transactions
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Inventory item ID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |
| types | string | Comma-separated list of transaction types |
| startDate | string | Start date filter (ISO format) |
| endDate | string | End date filter (ISO format) |
| sortDir | string | Sort direction (asc, desc) |

#### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "tx_01KXYZ789YZA",
      "type": "TRANSFER_IN",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "quantity": 10,
      "warehouseId": "wh_01HXYZ890PQR",
      "locationId": "loc_01JXYZ678STU",
      "sourceWarehouseId": "wh_01HXYZ789GHI",
      "referenceNumber": "TR-9012",
      "referenceType": "STOCK_TRANSFER",
      "reason": "Balancing warehouse inventory",
      "createdAt": "2023-05-22T09:45:00Z",
      "createdBy": "user_01LXYZ678STU"
    },
    // Additional transactions...
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "totalItems": 8,
    "totalPages": 1
  }
}
```

### Get Allocations for Item

Retrieves allocations for a specific inventory item.

```
GET /inventory-items/{id}/allocations
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Inventory item ID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |
| status | string | Filter by allocation status (PENDING, CONFIRMED, FULFILLED, CANCELLED) |
| startDate | string | Start date filter (ISO format) |
| endDate | string | End date filter (ISO format) |
| sortDir | string | Sort direction (asc, desc) |

#### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "alloc_01NXYZ901EFG",
      "orderId": "ord_01OXYZ012HIJ",
      "orderItemId": "item_01PXYZ123KLM",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "warehouseId": "wh_01HXYZ789GHI",
      "quantity": 2,
      "status": "CONFIRMED",
      "expiresAt": null,
      "createdAt": "2023-05-23T11:30:00Z",
      "updatedAt": "2023-05-23T14:15:00Z"
    },
    // Additional allocations...
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "totalItems": 5,
    "totalPages": 1
  }
}
```

## Error Responses

### Item Not Found

```json
{
  "success": false,
  "error": {
    "code": "INVENTORY_ITEM_NOT_FOUND",
    "message": "Inventory item not found",
    "details": {
      "id": "inv_invalid_id"
    }
  }
}
```

### Insufficient Stock

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Insufficient stock available for this operation",
    "details": {
      "inventoryItemId": "inv_01GXYZ234DEF",
      "warehouseId": "wh_01HXYZ789GHI",
      "requested": 20,
      "available": 15
    }
  }
}
```

### Validation Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "fields": {
        "quantity": "Quantity must be a positive number",
        "referenceNumber": "Reference number is required"
      }
    }
  }
}
```