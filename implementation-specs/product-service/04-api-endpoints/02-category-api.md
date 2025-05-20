# Category API Specification

## Overview
The Category API provides endpoints for managing product categories, including their hierarchical structure.

## Endpoints

### 1. `POST /categories`
- **Description:** Create a new category.
- **Authentication:** Required (admin, manager)
- **Request Body:** Uses `CategoryCreateRequest` schema. See [OpenAPI Spec](../openapi/product-service.yaml) and details in [Category Entity Model](../02-data-model-setup/02b-category-entity.md#dtos-data-transfer-objects).
  Example:
  ```json
  {
    "name": "Electronics",
    "description": "All kinds of electronic gadgets.",
    "parentId": null,
    "metadata": {"icon": "fa-bolt"}
  }
  ```
- **Response:**
  - 201 Created (Returns `Category` schema)
  - Example:
  ```json
  {
    "id": "uuid-category-1",
    "name": "Electronics",
    "description": "All kinds of electronic gadgets.",
    "parentId": null,
    "level": 1,
    "path": "/uuid-category-1",
    "metadata": {"icon": "fa-bolt"},
    "createdAt": "ISO8601"
  }
  ```
- **Validation Rules:**
  - Refer to `CategoryCreateRequest` in [OpenAPI Spec](../openapi/product-service.yaml) and validation decorators in [Category Entity Model](../02-data-model-setup/02b-category-entity.md#dtos-data-transfer-objects).
  - Key rules include: `name` (required, max 100 chars, unique within parent), `parentId` (optional, must be valid UUID if provided).
- **Error Responses:**
  - 400 Bad Request (validation error, see `ErrorResponse` schema in OpenAPI spec)
  - 401 Unauthorized
  - 409 Conflict (e.g., duplicate name under the same parent)

### 2. `GET /categories/{id}`
- **Description:** Retrieve a category by ID, including its children and parent.
- **Authentication:** Optional
- **Response:**
  - 200 OK (Returns `Category` schema, potentially with populated `children` and `parent` relations)
  - 404 Not Found
- **Validation Rules:**
  - Path parameter `id` must be a valid UUID.

### 3. `GET /categories`
- **Description:** List categories. Supports filtering by parent ID to fetch root categories or children of a specific category.
- **Authentication:** Optional
- **Query Parameters:**
  - `parentId`: (optional) UUID of the parent category. If not provided, root categories are returned.
  - `page`, `limit`, `sort`
- **Response:**
  - 200 OK (Returns `CategoryListResponse` schema)
  Example:
  ```json
  {
    "items": [ { /* category */ } ],
    "total": 10,
    "page": 1,
    "limit": 20
  }
  ```
- **Validation Rules:**
  - Query parameters are validated as per [OpenAPI Spec](../openapi/product-service.yaml). `parentId` must be a valid UUID if provided.

### 4. `PATCH /categories/{id}`
- **Description:** Update a category (e.g., name, description, parent). Moving a category (changing `parentId`) may have complex implications for its children's paths and levels.
- **Authentication:** Required (admin, manager)
- **Request Body:** Uses `CategoryUpdateRequest` schema. See [OpenAPI Spec](../openapi/product-service.yaml) and details in [Category Entity Model](../02-data-model-setup/02b-category-entity.md#dtos-data-transfer-objects).
  Example:
  ```json
  {
    "name": "Consumer Electronics",
    "description": "All kinds of consumer electronic gadgets."
  }
  ```
- **Response:** 200 OK (Returns `Category` schema), 404 Not Found, 400 Bad Request (e.g., attempting to create a circular dependency)
- **Validation Rules:**
  - Path parameter `id` must be a valid UUID.
  - Refer to `CategoryUpdateRequest` in [OpenAPI Spec](../openapi/product-service.yaml) and validation decorators in [Category Entity Model](../02-data-model-setup/02b-category-entity.md#dtos-data-transfer-objects).
  - Business logic must prevent circular dependencies if `parentId` is changed.

### 5. `DELETE /categories/{id}`
- **Description:** Delete a category. Behavior for categories with children needs to be defined (e.g., disallow, re-parent children, or cascade delete).
- **Authentication:** Required (admin, manager)
- **Response:** 204 No Content, 404 Not Found, 400 Bad Request (e.g., if category has children and deletion policy prevents it)
- **Validation Rules:**
  - Path parameter `id` must be a valid UUID.
  - Business rules for deleting categories with subcategories must be enforced.

## Request/Response Schemas
- Detailed request/response schemas (DTOs) are defined in the [OpenAPI Specification](../openapi/product-service.yaml) under `components.schemas`.
- These schemas are based on the [Category Entity Model](../02-data-model-setup/02b-category-entity.md) and its defined DTOs (`CreateCategoryDto`, `UpdateCategoryDto`).

## Error Handling
- Standard error response structure is defined by `ErrorResponse` schema in the [OpenAPI Specification](../openapi/product-service.yaml).

## Links
- [Category Service Specification](../03-core-service-components/02-category-service.md)
- [OpenAPI Specification](../openapi/product-service.yaml)

## References
- [OpenAPI Specification](https://swagger.io/specification/)
- [Hierarchical Data in SQL](https://www.postgresql.org/docs/current/ltree.html) (Example for path-based hierarchy) 