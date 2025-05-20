# Inventory API Specification

## Overview
The Inventory API provides endpoints for managing inventory for product variants, including stock updates, reservations, releases, and history. It supports integration with order and notification services.

## Endpoints

### 1. `GET /inventory/{variantId}`
- **Description:** Retrieve inventory details for a product variant
- **Authentication:** Required (admin, manager, warehouse)
- **Response:** 200 OK, 404 Not Found

### 2. `PATCH /inventory/{variantId}`
- **Description:** Update inventory for a product variant
- **Authentication:** Required (admin, manager, warehouse)
- **Request Body:**
```json
{
  "quantityChange": 10,
  "changeType": "purchase|sale|return|adjustment|reservation|cancellation",
  "reason": "string"
}
```
- **Response:** 200 OK, 400 Bad Request, 404 Not Found

### 3. `POST /inventory/{variantId}/reserve`
- **Description:** Reserve inventory for an order
- **Authentication:** Required (order service, admin, manager)
- **Request Body:** `{ "quantity": 2, "userId": "uuid" }`
- **Response:** 200 OK, 400 Bad Request, 404 Not Found, 409 Conflict

### 4. `POST /inventory/{variantId}/release`
- **Description:** Release reserved inventory (e.g., order cancellation)
- **Authentication:** Required (order service, admin, manager)
- **Request Body:** `{ "quantity": 2, "userId": "uuid" }`
- **Response:** 200 OK, 400 Bad Request, 404 Not Found, 409 Conflict

### 5. `GET /inventory/{variantId}/history`
- **Description:** Get inventory change history for a variant
- **Authentication:** Required (admin, manager, warehouse)
- **Query Parameters:** `from`, `to`, `changeType`, `userId`, `page`, `limit`
- **Response:**
```json
{
  "items": [ { /* inventory history */ } ],
  "total": 10,
  "page": 1,
  "limit": 20
}
```

## Request/Response Schemas
- See [Inventory Entity Model](../02-data-model-setup/02d-inventory-entity.md)

## Security & Authorization
- JWT required for all operations
- RBAC enforced for update, reserve, release
- Only authorized services/users can reserve/release inventory

## Pagination, Filtering, Sorting
- Use `page` and `limit` for history pagination
- Filter by `changeType`, `userId`, `from`, `to`

## Error Handling
- Standard error response:
```json
{
  "error": "string",
  "message": "string",
  "statusCode": 400
}
```

## Links
- [Inventory Service Specification](../03-core-service-components/03-inventory-service.md)
- [OpenAPI Spec](07-openapi-spec.md)

## References
- [OpenAPI Specification](https://swagger.io/specification/)
- [JSON:API Specification](https://jsonapi.org/) 