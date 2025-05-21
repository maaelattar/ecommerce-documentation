# Warehouse Endpoints

## Overview

Warehouse endpoints provide capabilities for managing warehouses, warehouse zones, bin locations, and obtaining warehouse-specific inventory information. These endpoints enable comprehensive warehouse management functionality within the inventory system.

## Base URL

```
https://api.example.com/inventory/v1
```

## Endpoints

### List Warehouses

Retrieves a list of warehouses with optional filtering.

```
GET /warehouses
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |
| search | string | Search term for warehouse name or code |
| type | string | Filter by warehouse type (DISTRIBUTION, FULFILLMENT, STORE, etc.) |
| isActive | boolean | Filter by active status (default: true) |
| sortBy | string | Sort field (name, code, createdAt) |
| sortDir | string | Sort direction (asc, desc) |

#### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "wh_01HXYZ789GHI",
      "name": "North Seattle Fulfillment Center",
      "code": "NSFC",
      "type": "FULFILLMENT",
      "address": {
        "street": "123 Distribution Way",
        "city": "Seattle",
        "state": "WA",
        "postalCode": "98101",
        "country": "USA"
      },
      "contactEmail": "north.warehouse@example.com",
      "contactPhone": "+1-206-555-0100",
      "isActive": true,
      "createdAt": "2023-01-15T08:30:00Z",
      "updatedAt": "2023-05-10T14:45:00Z"
    },
    {
      "id": "wh_01HXYZ890PQR",
      "name": "South Portland Distribution Center",
      "code": "SPDC",
      "type": "DISTRIBUTION",
      "address": {
        "street": "456 Logistics Boulevard",
        "city": "Portland",
        "state": "OR",
        "postalCode": "97201",
        "country": "USA"
      },
      "contactEmail": "south.warehouse@example.com",
      "contactPhone": "+1-503-555-0200",
      "isActive": true,
      "createdAt": "2023-02-20T10:15:00Z",
      "updatedAt": "2023-04-25T11:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "totalItems": 5,
    "totalPages": 1
  }
}
```

### Get Warehouse Details

Retrieves details for a specific warehouse.

```
GET /warehouses/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Warehouse ID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| includeZones | boolean | Include warehouse zone information |
| includeStats | boolean | Include warehouse statistics |

#### Response

```json
{
  "success": true,
  "data": {
    "id": "wh_01HXYZ789GHI",
    "name": "North Seattle Fulfillment Center",
    "code": "NSFC",
    "type": "FULFILLMENT",
    "address": {
      "street": "123 Distribution Way",
      "city": "Seattle",
      "state": "WA",
      "postalCode": "98101",
      "country": "USA"
    },
    "contactEmail": "north.warehouse@example.com",
    "contactPhone": "+1-206-555-0100",
    "operatingHours": {
      "monday": "08:00-20:00",
      "tuesday": "08:00-20:00",
      "wednesday": "08:00-20:00",
      "thursday": "08:00-20:00",
      "friday": "08:00-20:00",
      "saturday": "09:00-17:00",
      "sunday": "Closed"
    },
    "isActive": true,
    "createdAt": "2023-01-15T08:30:00Z",
    "updatedAt": "2023-05-10T14:45:00Z",
    "metadata": {
      "squareFootage": 120000,
      "dockDoors": 12,
      "supervisorName": "John Smith"
    },
    "zones": [
      {
        "id": "zone_01SXYZ901TUV",
        "name": "Electronics Picking Zone",
        "code": "EPZ",
        "zoneType": "PICKING",
        "isActive": true
      },
      {
        "id": "zone_01SXYZ012VWX",
        "name": "Bulk Storage Zone",
        "code": "BSZ",
        "zoneType": "STORAGE",
        "isActive": true
      }
    ],
    "stats": {
      "totalItems": 1250,
      "totalUniqueSkus": 325,
      "totalValue": 425000.50,
      "capacityUtilization": 65.5,
      "lowStockItems": 24,
      "outOfStockItems": 5,
      "activeAllocations": 87
    }
  }
}
```

### Create Warehouse

Creates a new warehouse.

```
POST /warehouses
```

#### Request Body

```json
{
  "name": "East Chicago Distribution Center",
  "code": "ECDC",
  "type": "DISTRIBUTION",
  "address": {
    "street": "789 Warehouse Avenue",
    "city": "Chicago",
    "state": "IL",
    "postalCode": "60601",
    "country": "USA"
  },
  "contactEmail": "east.warehouse@example.com",
  "contactPhone": "+1-312-555-0300",
  "operatingHours": {
    "monday": "07:00-19:00",
    "tuesday": "07:00-19:00",
    "wednesday": "07:00-19:00",
    "thursday": "07:00-19:00",
    "friday": "07:00-19:00",
    "saturday": "08:00-16:00",
    "sunday": "Closed"
  },
  "metadata": {
    "squareFootage": 150000,
    "dockDoors": 15,
    "supervisorName": "Emily Johnson"
  }
}
```

#### Required Fields

- `name`
- `code` (must be unique)
- `type`
- `address`

#### Response

```json
{
  "success": true,
  "data": {
    "id": "wh_01HXYZ123YZA",
    "name": "East Chicago Distribution Center",
    "code": "ECDC",
    "type": "DISTRIBUTION",
    "address": {
      "street": "789 Warehouse Avenue",
      "city": "Chicago",
      "state": "IL",
      "postalCode": "60601",
      "country": "USA"
    },
    "contactEmail": "east.warehouse@example.com",
    "contactPhone": "+1-312-555-0300",
    "operatingHours": {
      "monday": "07:00-19:00",
      "tuesday": "07:00-19:00",
      "wednesday": "07:00-19:00",
      "thursday": "07:00-19:00",
      "friday": "07:00-19:00",
      "saturday": "08:00-16:00",
      "sunday": "Closed"
    },
    "isActive": true,
    "createdAt": "2023-05-25T09:30:00Z",
    "updatedAt": "2023-05-25T09:30:00Z",
    "metadata": {
      "squareFootage": 150000,
      "dockDoors": 15,
      "supervisorName": "Emily Johnson"
    }
  }
}
```

### Update Warehouse

Updates an existing warehouse.

```
PUT /warehouses/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Warehouse ID |

#### Request Body

```json
{
  "name": "East Chicago Regional Distribution Center",
  "contactEmail": "eastregion.warehouse@example.com",
  "contactPhone": "+1-312-555-0350",
  "operatingHours": {
    "saturday": "08:00-18:00",
    "sunday": "10:00-16:00"
  },
  "metadata": {
    "supervisorName": "Emily R. Johnson",
    "securityLevel": "High"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": "wh_01HXYZ123YZA",
    "name": "East Chicago Regional Distribution Center",
    "code": "ECDC",
    "type": "DISTRIBUTION",
    "address": {
      "street": "789 Warehouse Avenue",
      "city": "Chicago",
      "state": "IL",
      "postalCode": "60601",
      "country": "USA"
    },
    "contactEmail": "eastregion.warehouse@example.com",
    "contactPhone": "+1-312-555-0350",
    "operatingHours": {
      "monday": "07:00-19:00",
      "tuesday": "07:00-19:00",
      "wednesday": "07:00-19:00",
      "thursday": "07:00-19:00",
      "friday": "07:00-19:00",
      "saturday": "08:00-18:00",
      "sunday": "10:00-16:00"
    },
    "isActive": true,
    "createdAt": "2023-05-25T09:30:00Z",
    "updatedAt": "2023-05-25T14:45:00Z",
    "metadata": {
      "squareFootage": 150000,
      "dockDoors": 15,
      "supervisorName": "Emily R. Johnson",
      "securityLevel": "High"
    }
  }
}
```

### Deactivate Warehouse

Deactivates a warehouse, preventing new inventory operations.

```
DELETE /warehouses/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Warehouse ID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| reason | string | Reason for deactivation (required) |

#### Response

```json
{
  "success": true,
  "data": {
    "id": "wh_01HXYZ123YZA",
    "isActive": false,
    "deactivatedAt": "2023-06-01T11:30:00Z",
    "deactivationReason": "Facility closure for renovation"
  }
}
```

### Get Warehouse Inventory

Retrieves inventory items stored in a specific warehouse.

```
GET /warehouses/{id}/inventory
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Warehouse ID |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (default: 20, max: 100) |
| search | string | Search term for item name or SKU |
| minQuantity | integer | Filter by minimum available quantity |
| maxQuantity | integer | Filter by maximum available quantity |
| includeZeroStock | boolean | Include items with zero stock (default: false) |
| sortBy | string | Sort field (name, sku, quantityAvailable) |
| sortDir | string | Sort direction (asc, desc) |

#### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "inv_01GXYZ234DEF",
      "sku": "WIDGET-2",
      "productId": "prod_01FXYZ789ABC",
      "name": "Widget Deluxe Plus",
      "quantityAvailable": 67,
      "quantityReserved": 3,
      "locations": [
        {
          "locationId": "loc_01JXYZ101KLM",
          "locationCode": "A-01-B-02",
          "quantity": 42
        },
        {
          "locationId": "loc_01JXYZ202NOP",
          "locationCode": "A-02-C-05",
          "quantity": 25
        }
      ]
    },
    {
      "id": "inv_01GXYZ345QRS",
      "sku": "GADGET-1",
      "productId": "prod_01FXYZ890DEF",
      "name": "Smart Gadget",
      "quantityAvailable": 35,
      "quantityReserved": 1,
      "locations": [
        {
          "locationId": "loc_01JXYZ303QRS",
          "locationCode": "B-03-A-01",
          "quantity": 35
        }
      ]
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "totalItems": 325,
    "totalPages": 17
  },
  "summary": {
    "totalItems": 1250,
    "totalValue": 425000.50,
    "lowStockItems": 24,
    "outOfStockItems": 5
  }
}
```

### Create Warehouse Zone

Creates a new zone within a warehouse.

```
POST /warehouses/{id}/zones
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Warehouse ID |

#### Request Body

```json
{
  "name": "High-Value Secure Zone",
  "code": "HVSZ",
  "description": "Secure area for high-value items",
  "zoneType": "SECURE_STORAGE",
  "metadata": {
    "securityLevel": "Maximum",
    "accessRestricted": true,
    "authorizedPersonnel": ["ID001", "ID002", "ID003"]
  }
}
```

#### Required Fields

- `name`
- `code` (must be unique within warehouse)
- `zoneType`

#### Response

```json
{
  "success": true,
  "data": {
    "id": "zone_01SXYZ345BCD",
    "warehouseId": "wh_01HXYZ789GHI",
    "name": "High-Value Secure Zone",
    "code": "HVSZ",
    "description": "Secure area for high-value items",
    "zoneType": "SECURE_STORAGE",
    "isActive": true,
    "createdAt": "2023-05-26T08:45:00Z",
    "updatedAt": "2023-05-26T08:45:00Z",
    "metadata": {
      "securityLevel": "Maximum",
      "accessRestricted": true,
      "authorizedPersonnel": ["ID001", "ID002", "ID003"]
    }
  }
}
```

### Create Bin Location

Creates a new bin location within a warehouse zone.

```
POST /warehouses/{warehouseId}/zones/{zoneId}/locations
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| warehouseId | string | Warehouse ID |
| zoneId | string | Zone ID |

#### Request Body

```json
{
  "locationCode": "HVSZ-A01-R01-L01-P01",
  "locationType": "SHELF",
  "position": {
    "aisle": "A01",
    "rack": "R01",
    "level": "L01", 
    "position": "P01"
  },
  "capacity": {
    "maxWeight": 50,
    "maxVolume": 0.5,
    "maxItems": 100
  },
  "metadata": {
    "specialHandling": "Fragile",
    "environmentalControls": "Temperature controlled"
  }
}
```

#### Required Fields

- `locationCode` (must be unique within warehouse)
- `locationType`

#### Response

```json
{
  "success": true,
  "data": {
    "id": "loc_01JXYZ456EFG",
    "warehouseId": "wh_01HXYZ789GHI",
    "zoneId": "zone_01SXYZ345BCD",
    "locationCode": "HVSZ-A01-R01-L01-P01",
    "locationType": "SHELF",
    "position": {
      "aisle": "A01",
      "rack": "R01",
      "level": "L01",
      "position": "P01"
    },
    "capacity": {
      "maxWeight": 50,
      "maxVolume": 0.5,
      "maxItems": 100
    },
    "isActive": true,
    "createdAt": "2023-05-26T09:30:00Z",
    "updatedAt": "2023-05-26T09:30:00Z",
    "metadata": {
      "specialHandling": "Fragile",
      "environmentalControls": "Temperature controlled"
    }
  }
}
```

### Assign Item to Location

Assigns an inventory item to a specific bin location.

```
POST /warehouses/{warehouseId}/locations/{locationId}/items
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| warehouseId | string | Warehouse ID |
| locationId | string | Location ID |

#### Request Body

```json
{
  "inventoryItemId": "inv_01GXYZ234DEF",
  "quantity": 15,
  "reason": "Reorganizing stock",
  "metadata": {
    "movedBy": "Jane Doe",
    "lotNumber": "L2023052601"
  }
}
```

#### Required Fields

- `inventoryItemId`
- `quantity` (must be positive)

#### Response

```json
{
  "success": true,
  "data": {
    "inventoryItemId": "inv_01GXYZ234DEF",
    "locationId": "loc_01JXYZ456EFG",
    "warehouseId": "wh_01HXYZ789GHI",
    "quantity": 15,
    "transaction": {
      "id": "tx_01KXYZ567HIJ",
      "type": "LOCATION_ASSIGNMENT",
      "inventoryItemId": "inv_01GXYZ234DEF",
      "quantity": 15,
      "warehouseId": "wh_01HXYZ789GHI",
      "locationId": "loc_01JXYZ456EFG",
      "reason": "Reorganizing stock",
      "createdAt": "2023-05-26T10:15:00Z",
      "createdBy": "user_01LXYZ456JKL"
    }
  }
}
```

## Error Responses

### Warehouse Not Found

```json
{
  "success": false,
  "error": {
    "code": "WAREHOUSE_NOT_FOUND",
    "message": "Warehouse not found",
    "details": {
      "id": "wh_invalid_id"
    }
  }
}
```

### Duplicate Code

```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_WAREHOUSE_CODE",
    "message": "Warehouse code already exists",
    "details": {
      "code": "ECDC"
    }
  }
}
```

### Zone Not Found

```json
{
  "success": false,
  "error": {
    "code": "ZONE_NOT_FOUND",
    "message": "Warehouse zone not found",
    "details": {
      "warehouseId": "wh_01HXYZ789GHI",
      "zoneId": "zone_invalid_id"
    }
  }
}
```

### Location Not Found

```json
{
  "success": false,
  "error": {
    "code": "LOCATION_NOT_FOUND",
    "message": "Bin location not found",
    "details": {
      "locationId": "loc_invalid_id"
    }
  }
}
```

### Location Capacity Exceeded

```json
{
  "success": false,
  "error": {
    "code": "LOCATION_CAPACITY_EXCEEDED",
    "message": "Bin location capacity would be exceeded",
    "details": {
      "locationId": "loc_01JXYZ456EFG",
      "currentItems": 85,
      "requestedItems": 20,
      "maxItems": 100
    }
  }
}
```