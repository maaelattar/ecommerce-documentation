# Allocation Endpoints

## Overview

Allocation endpoints provide functionality for reserving, confirming, and managing inventory allocations for orders. These endpoints facilitate the process of reserving inventory for a specific order until it's fulfilled or cancelled.

## Base URL

```
https://api.example.com/inventory/v1
```

## Endpoints

### Create Allocation

Creates a new inventory allocation for an order item.

```
POST /allocations
```

#### Request Body

```json
{
  "orderId": "ord_01OXYZ012HIJ",
  "orderItemId": "item_01PXYZ123KLM",
  "inventoryItemId": "inv_01GXYZ234DEF",
  "quantity": 2,
  "warehouseId": "wh_01HXYZ789GHI",
  "expiresAt": "2023-05-24T23:59:59Z",
  "metadata": {
    "priority": "high",
    "customerTier": "premium"
  }
}
```

#### Required Fields

- `orderId`
- `orderItemId`
- `inventoryItemId`
- `quantity` (must be positive)

#### Optional Fields

- `warehouseId` (if not provided, the system will select an optimal warehouse)
- `expiresAt` (if not provided, default expiry period will be used)
- `metadata`

#### Response

```json
{
  "success": true,
  "data": {
    "id": "alloc_01NXYZ901EFG",
    "orderId": "ord_01OXYZ012HIJ",
    "orderItemId": "item_01PXYZ123KLM",
    "inventoryItemId": "inv_01GXYZ234DEF",
    "warehouseId": "wh_01HXYZ789GHI",
    "quantity": 2,
    "status": "PENDING",
    "expiresAt": "2023-05-24T23:59:59Z",
    "createdAt": "2023-05-23T11:30:00Z",
    "updatedAt": "2023-05-23T11:30:00Z",
    "metadata": {
      "priority": "high",
      "customerTier": "premium"
    },
    "inventoryItem": {
      "sku": "WIDGET-2",
      "name": "Widget Deluxe Plus",
      "quantityAvailable": 68,
      "quantityReserved": 2
    }
  }
}
```

### Create Bulk Allocations

Creates multiple allocations for different items in a single order.

```
POST /allocations/bulk
```

#### Request Body

```json
{
  "orderId": "ord_01OXYZ012HIJ",
  "items": [
    {
      "orderItemId": "item_01PXYZ123KLM",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "quantity": 2
    },
    {
      "orderItemId": "item_01PXYZ234NOP",
      "inventoryItemId": "inv_01GXYZ345QRS",
      "quantity": 1
    }
  ],
  "warehouseId": "wh_01HXYZ789GHI",
  "expiresAt": "2023-05-24T23:59:59Z",
  "metadata": {
    "priority": "high",
    "customerTier": "premium"
  }
}
```

#### Required Fields

- `orderId`
- `items` (array of items with required orderItemId, inventoryItemId, and quantity)

#### Response

```json
{
  "success": true,
  "data": {
    "allocations": [
      {
        "id": "alloc_01NXYZ901EFG",
        "orderId": "ord_01OXYZ012HIJ",
        "orderItemId": "item_01PXYZ123KLM",
        "inventoryItemId": "inv_01GXYZ234DEF",
        "warehouseId": "wh_01HXYZ789GHI",
        "quantity": 2,
        "status": "PENDING",
        "expiresAt": "2023-05-24T23:59:59Z",
        "createdAt": "2023-05-23T11:30:00Z"
      },
      {
        "id": "alloc_01NXYZ012TUV",
        "orderId": "ord_01OXYZ012HIJ",
        "orderItemId": "item_01PXYZ234NOP",
        "inventoryItemId": "inv_01GXYZ345QRS",
        "warehouseId": "wh_01HXYZ789GHI",
        "quantity": 1,
        "status": "PENDING",
        "expiresAt": "2023-05-24T23:59:59Z",
        "createdAt": "2023-05-23T11:30:00Z"
      }
    ],
    "summary": {
      "totalAllocations": 2,
      "successfulAllocations": 2,
      "failedAllocations": 0
    }
  }
}
```

### Get Allocation Details

Retrieves details for a specific allocation.

```
GET /allocations/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Allocation ID |

#### Response

```json
{
  "success": true,
  "data": {
    "id": "alloc_01NXYZ901EFG",
    "orderId": "ord_01OXYZ012HIJ",
    "orderItemId": "item_01PXYZ123KLM",
    "inventoryItemId": "inv_01GXYZ234DEF",
    "warehouseId": "wh_01HXYZ789GHI",
    "quantity": 2,
    "status": "PENDING",
    "expiresAt": "2023-05-24T23:59:59Z",
    "createdAt": "2023-05-23T11:30:00Z",
    "updatedAt": "2023-05-23T11:30:00Z",
    "metadata": {
      "priority": "high",
      "customerTier": "premium"
    },
    "inventoryItem": {
      "id": "inv_01GXYZ234DEF",
      "sku": "WIDGET-2",
      "name": "Widget Deluxe Plus",
      "quantityAvailable": 68,
      "quantityReserved": 2
    },
    "warehouse": {
      "id": "wh_01HXYZ789GHI",
      "name": "North Warehouse",
      "code": "NW"
    },
    "statusHistory": [
      {
        "status": "PENDING",
        "timestamp": "2023-05-23T11:30:00Z",
        "userId": "user_01LXYZ456JKL"
      }
    ]
  }
}
```

### Confirm Allocation

Confirms a pending allocation, typically after payment is processed.

```
PUT /allocations/{id}/confirm
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Allocation ID |

#### Request Body

```json
{
  "notes": "Payment processed successfully",
  "metadata": {
    "paymentId": "pay_01QXYZ567STU",
    "paymentMethod": "credit_card"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": "alloc_01NXYZ901EFG",
    "orderId": "ord_01OXYZ012HIJ",
    "status": "CONFIRMED",
    "previousStatus": "PENDING",
    "expiresAt": null,
    "updatedAt": "2023-05-23T14:15:00Z",
    "notes": "Payment processed successfully",
    "metadata": {
      "priority": "high",
      "customerTier": "premium",
      "paymentId": "pay_01QXYZ567STU",
      "paymentMethod": "credit_card"
    }
  }
}
```

### Cancel Allocation

Cancels an allocation and releases the reserved inventory.

```
PUT /allocations/{id}/cancel
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Allocation ID |

#### Request Body

```json
{
  "reason": "Customer cancelled order",
  "metadata": {
    "cancellationCode": "CUST_REQ",
    "refundId": "ref_01RXYZ678VWX"
  }
}
```

#### Required Fields

- `reason`

#### Response

```json
{
  "success": true,
  "data": {
    "id": "alloc_01NXYZ901EFG",
    "orderId": "ord_01OXYZ012HIJ",
    "status": "CANCELLED",
    "previousStatus": "PENDING",
    "cancelledAt": "2023-05-23T16:45:00Z",
    "reason": "Customer cancelled order",
    "inventoryItem": {
      "id": "inv_01GXYZ234DEF",
      "quantityAvailable": 70,
      "quantityReserved": 0,
      "updatedAt": "2023-05-23T16:45:00Z"
    }
  }
}
```

### Fulfill Allocation

Marks an allocation as fulfilled, indicating that the items have been shipped or delivered.

```
PUT /allocations/{id}/fulfill
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Allocation ID |

#### Request Body

```json
{
  "referenceNumber": "SHIP-3456",
  "referenceType": "SHIPMENT",
  "locationId": "loc_01JXYZ101KLM",
  "metadata": {
    "trackingNumber": "1Z9999999999999999",
    "carrier": "UPS",
    "shipDate": "2023-05-24T09:30:00Z"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": "alloc_01NXYZ901EFG",
    "orderId": "ord_01OXYZ012HIJ",
    "status": "FULFILLED",
    "previousStatus": "CONFIRMED",
    "fulfilledAt": "2023-05-24T09:30:00Z",
    "transaction": {
      "id": "tx_01KXYZ890YZA",
      "type": "SALE",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "quantity": 2,
      "warehouseId": "wh_01HXYZ789GHI",
      "locationId": "loc_01JXYZ101KLM",
      "referenceNumber": "SHIP-3456",
      "referenceType": "SHIPMENT",
      "reason": "Order fulfillment",
      "createdAt": "2023-05-24T09:30:00Z"
    },
    "inventoryItem": {
      "id": "inv_01GXYZ234DEF",
      "previousQuantityAvailable": 70,
      "newQuantityAvailable": 68,
      "previousQuantityReserved": 2,
      "newQuantityReserved": 0,
      "updatedAt": "2023-05-24T09:30:00Z"
    }
  }
}
```

### Update Allocation

Updates a pending or confirmed allocation.

```
PUT /allocations/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Allocation ID |

#### Request Body

```json
{
  "quantity": 3,
  "warehouseId": "wh_01HXYZ890PQR",
  "reason": "Customer updated order quantity",
  "metadata": {
    "priority": "urgent",
    "customerTier": "VIP"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": "alloc_01NXYZ901EFG",
    "orderId": "ord_01OXYZ012HIJ",
    "orderItemId": "item_01PXYZ123KLM",
    "inventoryItemId": "inv_01GXYZ234DEF",
    "warehouseId": "wh_01HXYZ890PQR",
    "previousWarehouseId": "wh_01HXYZ789GHI",
    "quantity": 3,
    "previousQuantity": 2,
    "status": "PENDING",
    "expiresAt": "2023-05-24T23:59:59Z",
    "updatedAt": "2023-05-23T18:30:00Z",
    "metadata": {
      "priority": "urgent",
      "customerTier": "VIP"
    },
    "inventoryItem": {
      "id": "inv_01GXYZ234DEF",
      "quantityAvailable": 67,
      "quantityReserved": 3,
      "updatedAt": "2023-05-23T18:30:00Z"
    }
  }
}
```

### Get Allocations by Order

Retrieves all allocations for a specific order.

```
GET /allocations/by-order/{orderId}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| orderId | string | Order ID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by allocation status |
| includeInventoryDetails | boolean | Include detailed inventory information |

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
      "warehouseId": "wh_01HXYZ890PQR",
      "quantity": 3,
      "status": "PENDING",
      "expiresAt": "2023-05-24T23:59:59Z",
      "createdAt": "2023-05-23T11:30:00Z",
      "updatedAt": "2023-05-23T18:30:00Z",
      "inventoryItem": {
        "sku": "WIDGET-2",
        "name": "Widget Deluxe Plus"
      }
    },
    {
      "id": "alloc_01NXYZ012TUV",
      "orderId": "ord_01OXYZ012HIJ",
      "orderItemId": "item_01PXYZ234NOP",
      "inventoryItemId": "inv_01GXYZ345QRS",
      "warehouseId": "wh_01HXYZ789GHI",
      "quantity": 1,
      "status": "PENDING",
      "expiresAt": "2023-05-24T23:59:59Z",
      "createdAt": "2023-05-23T11:30:00Z",
      "updatedAt": "2023-05-23T11:30:00Z",
      "inventoryItem": {
        "sku": "GADGET-1",
        "name": "Smart Gadget"
      }
    }
  ],
  "summary": {
    "totalQuantity": 4,
    "allocationsByStatus": {
      "PENDING": 2,
      "CONFIRMED": 0,
      "FULFILLED": 0,
      "CANCELLED": 0
    }
  }
}
```

## Error Responses

### Allocation Not Found

```json
{
  "success": false,
  "error": {
    "code": "ALLOCATION_NOT_FOUND",
    "message": "Allocation not found",
    "details": {
      "id": "alloc_invalid_id"
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
    "message": "Insufficient stock available for allocation",
    "details": {
      "inventoryItemId": "inv_01GXYZ234DEF",
      "warehouseId": "wh_01HXYZ789GHI",
      "requested": 10,
      "available": 5
    }
  }
}
```

### Invalid Status Transition

```json
{
  "success": false,
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "Cannot transition allocation from FULFILLED to CONFIRMED",
    "details": {
      "allocationId": "alloc_01NXYZ901EFG",
      "currentStatus": "FULFILLED",
      "requestedStatus": "CONFIRMED"
    }
  }
}
```