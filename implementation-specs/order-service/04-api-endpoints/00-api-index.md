# Order Service API Endpoints

## Introduction

This document provides an overview of the RESTful API endpoints exposed by the Order Service. The API is designed following RESTful principles and adheres to the platform's API standards as defined in [ADR-002-rest-api-standards-openapi](../../../architecture/adr/ADR-002-rest-api-standards-openapi.md).

## API Base URL

- **Development**: `https://dev-api.example.com/orders`
- **Staging**: `https://staging-api.example.com/orders`
- **Production**: `https://api.example.com/orders`

## Authentication and Authorization

All Order Service API endpoints require authentication. The service uses JWT-based authentication with the following requirements:

1. **Authentication**: Valid JWT token in the `Authorization` header
2. **Authorization**:
   - Customer permissions for managing their own orders
   - Admin permissions for managing all orders or performing administrative actions

## API Versioning

The API is versioned through the URL path:

```
https://api.example.com/v1/orders
```

Current API version: `v1`

## Endpoint Overview

| Method | Endpoint             | Description                               | Authentication |
| ------ | -------------------- | ----------------------------------------- | -------------- |
| POST   | /orders              | Create a new order                        | Customer       |
| GET    | /orders              | List orders with filtering and pagination | Customer/Admin |
| GET    | /orders/{id}         | Get order details by ID                   | Customer/Admin |
| PATCH  | /orders/{id}         | Update order (limited fields)             | Customer/Admin |
| PATCH  | /orders/{id}/status  | Update order status                       | Admin          |
| DELETE | /orders/{id}         | Cancel order (soft delete)                | Customer/Admin |
| GET    | /orders/{id}/history | Get order status history                  | Customer/Admin |
| GET    | /orders/{id}/items   | Get order items                           | Customer/Admin |
| POST   | /orders/{id}/refund  | Request refund for an order               | Customer/Admin |
| GET    | /orders/statistics   | Get order statistics                      | Admin          |

## Detailed Endpoint Specifications

Each API endpoint is described in detail in its own specification document:

- [01-create-order.md](./01-create-order.md): Create a new order
- [02-get-orders.md](./02-get-orders.md): List and filter orders
- [03-get-order-by-id.md](./03-get-order-by-id.md): Get order details
- [04-update-order.md](./04-update-order.md): Update order information
- [05-update-order-status.md](./05-update-order-status.md): Update order status
- [06-cancel-order.md](./06-cancel-order.md): Cancel an existing order
- [07-order-history.md](./07-order-history.md): Retrieve order status history
- [08-order-items.md](./08-order-items.md): Manage order items
- [09-order-refund.md](./09-order-refund.md): Process order refunds
- [10-order-statistics.md](./10-order-statistics.md): Order reporting and statistics

## Common Request/Response Formats

### Standard Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {
    /* Response data */
  },
  "meta": {
    "timestamp": "2023-11-21T12:34:56.789Z",
    "requestId": "req-123456789"
  }
}
```

### Error Response Format

Error responses follow a standardized format:

```json
{
  "success": false,
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "Order with ID '123' was not found",
    "details": {
      /* Additional error details */
    }
  },
  "meta": {
    "timestamp": "2023-11-21T12:34:56.789Z",
    "requestId": "req-123456789"
  }
}
```

### Pagination Format

List endpoints that return multiple items use a consistent pagination format:

```json
{
  "success": true,
  "data": [
    /* Array of items */
  ],
  "meta": {
    "timestamp": "2023-11-21T12:34:56.789Z",
    "requestId": "req-123456789",
    "pagination": {
      "page": 1,
      "pageSize": 10,
      "totalItems": 42,
      "totalPages": 5
    }
  }
}
```

## API Documentation

The complete OpenAPI specification for the Order Service API is available at:

- **Development**: `https://dev-api.example.com/orders/docs`
- **Staging**: `https://staging-api.example.com/orders/docs`
- **Production**: `https://api.example.com/orders/docs`

The specification is also available in the `openapi` directory:

- [OpenAPI Specification](../openapi/order-service-openapi.yaml)

## Rate Limiting

The Order Service API implements rate limiting to prevent abuse:

| Environment | Customer Rate Limit | Admin Rate Limit |
| ----------- | ------------------- | ---------------- |
| Development | 100 req/min         | 200 req/min      |
| Staging     | 100 req/min         | 200 req/min      |
| Production  | 300 req/min         | 600 req/min      |

Rate limit headers are included in each response:

- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in the current window
- `X-RateLimit-Reset`: Timestamp when the rate limit resets

## Cross-Service Dependencies

The Order Service API has dependencies on the following services:

| Service              | Dependency Type | Purpose                             |
| -------------------- | --------------- | ----------------------------------- |
| User Service         | Synchronous     | Validate user information           |
| Product Service      | Synchronous     | Validate product information        |
| Inventory Service    | Synchronous     | Check and reserve inventory         |
| Payment Service      | Synchronous     | Process payments                    |
| Notification Service | Asynchronous    | Send order confirmation and updates |

## References

- [Order Service Data Model](../02-data-model-setup/00-data-model-index.md)
- [Order Service Components](../03-core-service-components/00-service-components-index.md)
- [ADR-001-microservice-architecture-principles](../../../architecture/adr/ADR-001-microservice-architecture-principles.md)
- [ADR-002-rest-api-standards-openapi](../../../architecture/adr/ADR-002-rest-api-standards-openapi.md)
- [ADR-003-nodejs-nestjs-for-initial-services](../../../architecture/adr/ADR-003-nodejs-nestjs-for-initial-services.md)
