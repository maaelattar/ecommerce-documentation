# Transaction Endpoints

## Overview

Transaction endpoints provide access to stock transactions, allowing for querying and analyzing inventory movements. These endpoints are primarily read-only, as transactions are typically created indirectly through inventory operations.

## Base URL

```
https://api.example.com/inventory/v1
```

## Endpoints

### List Transactions

Retrieves a paginated list of stock transactions with optional filtering.

```
GET /transactions
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |
| types | string | Comma-separated list of transaction types (RECEIPT, ADJUSTMENT, TRANSFER_IN, TRANSFER_OUT, SALE, RETURN, etc.) |
| inventoryItemId | string | Filter by inventory item ID |
| warehouseId | string | Filter by warehouse ID |
| startDate | string | Start date filter (ISO format) |
| endDate | string | End date filter (ISO format) |
| referenceType | string | Filter by reference type (PURCHASE_ORDER, SHIPMENT, etc.) |
| referenceNumber | string | Filter by reference number |
| sortBy | string | Sort field (createdAt, quantity) |
| sortDir | string | Sort direction (asc, desc) |

#### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "tx_01KXYZ567HIJ",
      "type": "LOCATION_ASSIGNMENT",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "sku": "WIDGET-2",
      "itemName": "Widget Deluxe Plus",
      "quantity": 15,
      "warehouseId": "wh_01HXYZ789GHI",
      "warehouseName": "North Seattle Fulfillment Center",
      "locationId": "loc_01JXYZ456EFG",
      "locationCode": "HVSZ-A01-R01-L01-P01",
      "reason": "Reorganizing stock",
      "createdAt": "2023-05-26T10:15:00Z",
      "createdBy": "user_01LXYZ456JKL"
    },
    {
      "id": "tx_01KXYZ678KLM",
      "type": "RECEIPT",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "sku": "WIDGET-2",
      "itemName": "Widget Deluxe Plus",
      "quantity": 25,
      "warehouseId": "wh_01HXYZ789GHI",
      "warehouseName": "North Seattle Fulfillment Center",
      "locationId": "loc_01JXYZ101KLM",
      "locationCode": "A-01-B-02",
      "referenceNumber": "PO-12345",
      "referenceType": "PURCHASE_ORDER",
      "reason": "Scheduled stock replenishment",
      "lotNumber": "LOT-2023-05-01",
      "expirationDate": "2025-05-01T00:00:00Z",
      "createdAt": "2023-05-20T10:15:00Z",
      "createdBy": "user_01LXYZ456JKL"
    }
    // Additional transactions...
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "totalItems": 156,
    "totalPages": 8
  }
}
```

### Get Transaction Details

Retrieves details for a specific transaction.

```
GET /transactions/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Transaction ID |

#### Response

```json
{
  "success": true,
  "data": {
    "id": "tx_01KXYZ678KLM",
    "type": "RECEIPT",
    "inventoryItemId": "inv_01GXYZ234DEF",
    "sku": "WIDGET-2",
    "itemName": "Widget Deluxe Plus",
    "quantity": 25,
    "warehouseId": "wh_01HXYZ789GHI",
    "warehouseName": "North Seattle Fulfillment Center",
    "locationId": "loc_01JXYZ101KLM",
    "locationCode": "A-01-B-02",
    "referenceNumber": "PO-12345",
    "referenceType": "PURCHASE_ORDER",
    "reason": "Scheduled stock replenishment",
    "lotNumber": "LOT-2023-05-01",
    "expirationDate": "2025-05-01T00:00:00Z",
    "createdAt": "2023-05-20T10:15:00Z",
    "createdBy": "user_01LXYZ456JKL",
    "createdByName": "John Smith",
    "relatedTransactionId": null,
    "previousQuantity": 50,
    "newQuantity": 75,
    "metadata": {
      "receivedBy": "John Smith",
      "quality": "A-Grade",
      "supplierName": "Acme Corp",
      "invoiceNumber": "INV-56789"
    },
    "item": {
      "id": "inv_01GXYZ234DEF",
      "sku": "WIDGET-2",
      "name": "Widget Deluxe Plus",
      "productId": "prod_01FXYZ789ABC",
      "currentQuantity": 70
    }
  }
}
```

### Get Related Transactions

Retrieves transactions related to a specific transaction (e.g., corresponding TRANSFER_IN for a TRANSFER_OUT).

```
GET /transactions/{id}/related
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Transaction ID |

#### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "tx_01KXYZ789NOP",
      "type": "TRANSFER_IN",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "sku": "WIDGET-2",
      "itemName": "Widget Deluxe Plus",
      "quantity": 10,
      "warehouseId": "wh_01HXYZ890PQR",
      "warehouseName": "South Portland Distribution Center",
      "locationId": "loc_01JXYZ678STU",
      "locationCode": "B-03-C-05",
      "sourceWarehouseId": "wh_01HXYZ789GHI",
      "referenceNumber": "TR-9012",
      "referenceType": "STOCK_TRANSFER",
      "reason": "Balancing warehouse inventory",
      "createdAt": "2023-05-22T09:45:00Z",
      "createdBy": "user_01LXYZ678STU",
      "relationship": "Transfer destination"
    }
  ]
}
```

### Get Transactions by Reference

Retrieves transactions by their reference information.

```
GET /transactions/by-reference/{type}/{number}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Reference type (e.g., PURCHASE_ORDER, SHIPMENT) |
| number | string | Reference number |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |

#### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "tx_01KXYZ678KLM",
      "type": "RECEIPT",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "sku": "WIDGET-2",
      "itemName": "Widget Deluxe Plus",
      "quantity": 25,
      "warehouseId": "wh_01HXYZ789GHI",
      "warehouseName": "North Seattle Fulfillment Center",
      "referenceNumber": "PO-12345",
      "referenceType": "PURCHASE_ORDER",
      "reason": "Scheduled stock replenishment",
      "createdAt": "2023-05-20T10:15:00Z"
    },
    {
      "id": "tx_01KXYZ789QRS",
      "type": "RECEIPT",
      "inventoryItemId": "inv_01GXYZ345QRS",
      "sku": "GADGET-1",
      "itemName": "Smart Gadget",
      "quantity": 15,
      "warehouseId": "wh_01HXYZ789GHI",
      "warehouseName": "North Seattle Fulfillment Center",
      "referenceNumber": "PO-12345",
      "referenceType": "PURCHASE_ORDER",
      "reason": "Scheduled stock replenishment",
      "createdAt": "2023-05-20T10:20:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "totalItems": 2,
    "totalPages": 1
  },
  "summary": {
    "referenceType": "PURCHASE_ORDER",
    "referenceNumber": "PO-12345",
    "totalTransactions": 2,
    "totalQuantity": 40,
    "transactionsByType": {
      "RECEIPT": 2
    }
  }
}
```

### Get Stock Transaction History for an Item

Retrieves the complete transaction history for a specific inventory item, showing how the stock levels have changed over time.

```
GET /transactions/history/item/{inventoryItemId}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| inventoryItemId | string | Inventory item ID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| startDate | string | Start date filter (ISO format) |
| endDate | string | End date filter (ISO format) |
| warehouseId | string | Filter by warehouse ID |
| aggregateBy | string | Time aggregation (day, week, month) |

#### Response

```json
{
  "success": true,
  "data": {
    "inventoryItem": {
      "id": "inv_01GXYZ234DEF",
      "sku": "WIDGET-2",
      "name": "Widget Deluxe Plus",
      "currentQuantity": 70
    },
    "history": [
      {
        "timestamp": "2023-05-10T09:20:00Z",
        "transactionId": "tx_01KXYZ123ABC",
        "type": "INITIAL",
        "quantity": 50,
        "runningTotal": 50,
        "reason": "Initial stock"
      },
      {
        "timestamp": "2023-05-20T10:15:00Z",
        "transactionId": "tx_01KXYZ678KLM",
        "type": "RECEIPT",
        "quantity": 25,
        "runningTotal": 75,
        "reason": "Scheduled stock replenishment",
        "reference": "PO-12345"
      },
      {
        "timestamp": "2023-05-21T14:30:00Z",
        "transactionId": "tx_01KXYZ567MNO",
        "type": "ADJUSTMENT",
        "quantity": -5,
        "runningTotal": 70,
        "reason": "Damaged during handling",
        "reference": "ADJ-6789"
      },
      {
        "timestamp": "2023-05-22T09:45:00Z",
        "transactionId": "tx_01KXYZ678VWX",
        "type": "TRANSFER_OUT",
        "quantity": -10,
        "runningTotal": 60,
        "reason": "Balancing warehouse inventory",
        "reference": "TR-9012"
      },
      {
        "timestamp": "2023-05-26T10:15:00Z",
        "transactionId": "tx_01KXYZ567HIJ",
        "type": "LOCATION_ASSIGNMENT",
        "quantity": 0,
        "runningTotal": 60,
        "reason": "Reorganizing stock"
      }
    ],
    "summary": {
      "openingStock": 0,
      "receipts": 75,
      "sales": 0,
      "returns": 0,
      "adjustments": -5,
      "transfersIn": 0,
      "transfersOut": -10,
      "closingStock": 60,
      "netChange": 60
    }
  }
}
```

### Get Transaction Types

Retrieves the list of available transaction types and their descriptions.

```
GET /transactions/types
```

#### Response

```json
{
  "success": true,
  "data": [
    {
      "type": "RECEIPT",
      "description": "Receiving inventory into stock",
      "affectsQuantity": true,
      "direction": "increase"
    },
    {
      "type": "ADJUSTMENT",
      "description": "Manual adjustment of inventory quantity",
      "affectsQuantity": true,
      "direction": "both"
    },
    {
      "type": "TRANSFER_OUT",
      "description": "Outbound transfer to another warehouse",
      "affectsQuantity": true,
      "direction": "decrease"
    },
    {
      "type": "TRANSFER_IN",
      "description": "Inbound transfer from another warehouse",
      "affectsQuantity": true,
      "direction": "increase"
    },
    {
      "type": "SALE",
      "description": "Reduction due to sales/order fulfillment",
      "affectsQuantity": true,
      "direction": "decrease"
    },
    {
      "type": "RETURN",
      "description": "Increase due to customer returns",
      "affectsQuantity": true,
      "direction": "increase"
    },
    {
      "type": "RESERVATION",
      "description": "Reservation for an order (no quantity change)",
      "affectsQuantity": false,
      "direction": "none"
    },
    {
      "type": "RESERVATION_RELEASE",
      "description": "Release of a reservation (no quantity change)",
      "affectsQuantity": false,
      "direction": "none"
    },
    {
      "type": "LOCATION_ASSIGNMENT",
      "description": "Assignment to a warehouse location (no quantity change)",
      "affectsQuantity": false,
      "direction": "none"
    },
    {
      "type": "CYCLE_COUNT",
      "description": "Adjustment based on physical inventory count",
      "affectsQuantity": true,
      "direction": "both"
    },
    {
      "type": "DAMAGE",
      "description": "Reduction due to damaged goods",
      "affectsQuantity": true,
      "direction": "decrease"
    },
    {
      "type": "EXPIRY",
      "description": "Reduction due to expired goods",
      "affectsQuantity": true,
      "direction": "decrease"
    }
  ]
}
```

## Error Responses

### Transaction Not Found

```json
{
  "success": false,
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Transaction not found",
    "details": {
      "id": "tx_invalid_id"
    }
  }
}
```

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

### Invalid Transaction Type

```json
{
  "success": false,
  "error": {
    "code": "INVALID_TRANSACTION_TYPE",
    "message": "Invalid transaction type specified",
    "details": {
      "providedType": "UNKNOWN_TYPE",
      "allowedTypes": [
        "RECEIPT",
        "ADJUSTMENT",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "SALE",
        "RETURN",
        "RESERVATION",
        "RESERVATION_RELEASE",
        "LOCATION_ASSIGNMENT",
        "CYCLE_COUNT",
        "DAMAGE",
        "EXPIRY"
      ]
    }
  }
}
```