# Product API Specification

## Overview
The Product API provides endpoints for managing products in the e-commerce platform, including creation, retrieval, update, deletion, and search. It supports advanced filtering, pagination, and integrates with category, inventory, and price services.

## Endpoints

### 1. `POST /products`
- **Description:** Create a new product
- **Authentication:** Required (admin, manager, editor)
- **Request Body:** Uses `ProductCreateRequest` schema. See [OpenAPI Spec](../openapi/product-service.yaml) and details in [Product Entity Model](../02-data-model-setup/02a-product-entity.md#dtos-data-transfer-objects).
  Example:
```json
{
  "name": "string",
  "description": "string",
  "brand": "string",
  "categoryIds": ["uuid"],
  "status": "draft|active|inactive|discontinued",
  "metadata": {"key": "value"}
}
```
- **Response:**
  - 201 Created (Returns `Product` schema)
  - Example:
```json
{
  "id": "uuid",
  "name": "string",
  "brand": "string",
  "status": "draft",
  "createdAt": "ISO8601"
}
```
- **Validation Rules:**
  - Refer to `ProductCreateRequest` in [OpenAPI Spec](../openapi/product-service.yaml) and validation decorators in [Product Entity Model](../02-data-model-setup/02a-product-entity.md#dtos-data-transfer-objects).
  - Key rules include: `name` (required, 3-255 chars), `categoryIds` (required, at least 1).
- **Error Responses:**
  - 400 Bad Request (validation error, see `ErrorResponse` schema in OpenAPI spec)
  - 401 Unauthorized
  - 409 Conflict (duplicate name)

### 2. `GET /products/{id}`
- **Description:** Retrieve a product by ID
- **Authentication:** Optional (public for viewing, required for management)
- **Response:**
  - 200 OK (Returns `Product` schema)
  - 404 Not Found
- **Validation Rules:**
  - Path parameter `id` must be a valid UUID.

### 3. `GET /products`
- **Description:** List products with filtering, pagination, and sorting
- **Authentication:** Optional
- **Query Parameters:**
  - `page`, `limit`, `sort`, `status`, `brand`, `categoryId`, `search`
- **Response:**
  - 200 OK (Returns `ProductListResponse` schema)
  Example:
```json
{
  "items": [ { /* product */ } ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```
- **Validation Rules:**
  - Query parameters are validated as per [OpenAPI Spec](../openapi/product-service.yaml) (e.g., `page`/`limit` are integers, `status` is an enum).

### 4. `PATCH /products/{id}`
- **Description:** Update a product
- **Authentication:** Required (admin, manager, editor)
- **Request Body:** Uses `ProductUpdateRequest` schema. See [OpenAPI Spec](../openapi/product-service.yaml) and details in [Product Entity Model](../02-data-model-setup/02a-product-entity.md#dtos-data-transfer-objects).
  Example: Partial product fields like:
```json
{
  "description": "Updated description",
  "status": "active"
}
```
- **Response:** 200 OK (Returns `Product` schema), 404 Not Found, 400 Bad Request
- **Validation Rules:**
  - Path parameter `id` must be a valid UUID.
  - Refer to `ProductUpdateRequest` in [OpenAPI Spec](../openapi/product-service.yaml) and validation decorators in [Product Entity Model](../02-data-model-setup/02a-product-entity.md#dtos-data-transfer-objects).

### 5. `DELETE /products/{id}`
- **Description:** Delete a product
- **Authentication:** Required (admin, manager)
- **Response:** 204 No Content, 404 Not Found
- **Validation Rules:**
  - Path parameter `id` must be a valid UUID.

### 6. `POST /products/{id}/status`
- **Description:** Change product status
- **Authentication:** Required (admin, manager)
- **Request Body:** `{ "status": "active|inactive|discontinued" }` (Uses a specific inline schema or a dedicated DTO if more complex, e.g. `ProductStatusUpdateRequest`)
- **Response:** 200 OK, 400 Bad Request, 404 Not Found
- **Validation Rules:**
  - Path parameter `id` must be a valid UUID.
  - `status` in request body must be one of the allowed enum values.

## Request/Response Schemas
- Detailed request/response schemas (DTOs) are defined in the [OpenAPI Specification](../openapi/product-service.yaml) under `components.schemas`.
- These schemas are based on the [Product Entity Model](../02-data-model-setup/02a-product-entity.md) and its defined DTOs (`CreateProductDto`, `UpdateProductDto`).

## Security & Authorization
- JWT required for all write operations
- RBAC enforced for create, update, delete, status change
- Public read access for product listing and details

## Pagination, Filtering, Sorting
- Use `page` and `limit` for pagination
- Use `sort` for sorting by fields (e.g., name, createdAt)
- Filter by `status`, `brand`, `categoryId`, `search` (full-text)

## Error Handling
- Standard error response structure is defined by `ErrorResponse` schema in the [OpenAPI Specification](../openapi/product-service.yaml).
  Example:
```json
{
  "error": "string",
  "message": "string",
  "statusCode": 400
}
```

## Links
- [Product Service Specification](../03-core-service-components/01-product-service.md)
- [OpenAPI Specification](../openapi/product-service.yaml)

## References
- [OpenAPI Specification](https://swagger.io/specification/)
- [JSON:API Specification](https://jsonapi.org/) 