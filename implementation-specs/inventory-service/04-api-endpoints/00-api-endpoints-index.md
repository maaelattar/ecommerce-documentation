# Inventory Service API Endpoints

## Overview

The Inventory Service exposes a set of RESTful API endpoints for managing inventory, allocations, warehouses, and performing inventory operations. The API is designed following REST principles with consistent patterns, standardized responses, and comprehensive error handling.

## API Documentation

Complete API documentation is available in OpenAPI/Swagger format:
- [Inventory Service OpenAPI Specification](../openapi/inventory-service.yaml)

## Authentication and Authorization

All endpoints require authentication using JWT tokens. The following roles are used:

- **inventory-admin**: Full access to all endpoints
- **inventory-manager**: Access to manage inventory and allocations
- **inventory-viewer**: Read-only access to inventory data
- **order-service**: Limited access for order integration
- **product-service**: Limited access for product integration

## Base URL

```
https://api.example.com/inventory/v1
```

## API Endpoints

### Inventory Management

| Method | Endpoint | Description | Auth Roles |
|--------|----------|-------------|------------|
| GET | `/inventory-items` | List inventory items with filtering and pagination | inventory-admin, inventory-manager, inventory-viewer |
| GET | `/inventory-items/{id}` | Get inventory item details | inventory-admin, inventory-manager, inventory-viewer |
| POST | `/inventory-items` | Create new inventory item | inventory-admin, inventory-manager |
| PUT | `/inventory-items/{id}` | Update inventory item | inventory-admin, inventory-manager |
| DELETE | `/inventory-items/{id}` | Deactivate inventory item | inventory-admin |
| POST | `/inventory-items/{id}/add-stock` | Add stock to inventory item | inventory-admin, inventory-manager |
| POST | `/inventory-items/{id}/adjust-stock` | Adjust stock quantity | inventory-admin, inventory-manager |
| POST | `/inventory-items/{id}/transfer` | Transfer stock between warehouses | inventory-admin, inventory-manager |
| GET | `/inventory-items/{id}/transactions` | Get stock transactions for item | inventory-admin, inventory-manager, inventory-viewer |
| GET | `/inventory-items/{id}/allocations` | Get allocations for item | inventory-admin, inventory-manager, inventory-viewer |

### Allocation Management

| Method | Endpoint | Description | Auth Roles |
|--------|----------|-------------|------------|
| POST | `/allocations` | Create an allocation | inventory-admin, inventory-manager, order-service |
| POST | `/allocations/bulk` | Create multiple allocations | inventory-admin, inventory-manager, order-service |
| GET | `/allocations/{id}` | Get allocation details | inventory-admin, inventory-manager, inventory-viewer, order-service |
| PUT | `/allocations/{id}/confirm` | Confirm allocation | inventory-admin, inventory-manager, order-service |
| PUT | `/allocations/{id}/cancel` | Cancel allocation | inventory-admin, inventory-manager, order-service |
| PUT | `/allocations/{id}/fulfill` | Fulfill allocation | inventory-admin, inventory-manager, order-service |
| PUT | `/allocations/{id}` | Update allocation | inventory-admin, inventory-manager |
| GET | `/allocations/by-order/{orderId}` | Get allocations for order | inventory-admin, inventory-manager, inventory-viewer, order-service |

### Warehouse Management

| Method | Endpoint | Description | Auth Roles |
|--------|----------|-------------|------------|
| GET | `/warehouses` | List warehouses | inventory-admin, inventory-manager, inventory-viewer |
| GET | `/warehouses/{id}` | Get warehouse details | inventory-admin, inventory-manager, inventory-viewer |
| POST | `/warehouses` | Create warehouse | inventory-admin |
| PUT | `/warehouses/{id}` | Update warehouse | inventory-admin |
| DELETE | `/warehouses/{id}` | Deactivate warehouse | inventory-admin |
| GET | `/warehouses/{id}/inventory` | Get warehouse inventory | inventory-admin, inventory-manager, inventory-viewer |

### Stock Transactions

| Method | Endpoint | Description | Auth Roles |
|--------|----------|-------------|------------|
| GET | `/transactions` | List transactions with filtering | inventory-admin, inventory-manager, inventory-viewer |
| GET | `/transactions/{id}` | Get transaction details | inventory-admin, inventory-manager, inventory-viewer |
| GET | `/transactions/by-reference/{type}/{number}` | Get transactions by reference | inventory-admin, inventory-manager, inventory-viewer |

### Reporting

| Method | Endpoint | Description | Auth Roles |
|--------|----------|-------------|------------|
| GET | `/reports/low-stock` | Get low stock report | inventory-admin, inventory-manager, inventory-viewer |
| GET | `/reports/inventory-value` | Get inventory value report | inventory-admin, inventory-manager, inventory-viewer |
| GET | `/reports/stock-movements` | Get stock movement report | inventory-admin, inventory-manager, inventory-viewer |
| GET | `/reports/allocations` | Get allocations report | inventory-admin, inventory-manager, inventory-viewer |

## Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {
    // Response data specific to the endpoint
  },
  "meta": {
    // Metadata like pagination info
    "page": 1,
    "limit": 20,
    "totalItems": 100,
    "totalPages": 5
  }
}
```

## Error Format

Errors follow a standardized format:

```json
{
  "success": false,
  "error": {
    "code": "INVENTORY_NOT_FOUND",
    "message": "Inventory item not found",
    "details": {
      "id": "invalid-id"
    }
  }
}
```

## Detailed Endpoint Documentation

Further details for each endpoint group are provided in the following documents:

1. [Inventory Item Endpoints](./01-inventory-item-endpoints.md)
2. [Allocation Endpoints](./02-allocation-endpoints.md)
3. [Warehouse Endpoints](./03-warehouse-endpoints.md)
4. [Transaction Endpoints](./04-transaction-endpoints.md)
5. [Reporting Endpoints](./05-reporting-endpoints.md)