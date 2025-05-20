# Price and Discount API Specification

## Overview
The Price and Discount API, as part of the Product Service, provides endpoints for managing prices for product variants and handling discounts.

## Price Endpoints

### 1. `GET /products/{productVariantId}/price`
- **Description:** Retrieve the current price for a specific product variant.
- **Authentication:** Optional (typically public)
- **Parameters:**
  - `productVariantId` (Path): ID of the product variant.
- **Response:**
  - 200 OK (Returns `ProductPrice` schema)
  - 404 Not Found (if product variant or its price not found)
- **Validation Rules:**
  - `productVariantId` must be a valid identifier (e.g., UUID).

### 2. `PUT /products/{productVariantId}/price`
- **Description:** Set or update the price for a specific product variant.
- **Authentication:** Required (admin, manager)
- **Parameters:**
  - `productVariantId` (Path): ID of the product variant.
- **Request Body:** Uses `SetProductPriceRequest` schema. See [OpenAPI Spec](../openapi/product-service.yaml) and details in [Price and Discount Models](../02-data-model-setup/02c-price-models.md).
  Example:
  ```json
  {
    "basePrice": 19.99,
    "salePrice": 17.99,
    "msrp": 24.99,
    "currency": "USD",
    "priceType": "REGULAR"
  }
  ```
- **Response:**
  - 200 OK (Returns updated `ProductPrice` schema)
  - 400 Bad Request (validation error)
  - 401 Unauthorized
  - 404 Not Found (if product variant not found)
- **Validation Rules:**
  - `productVariantId` must be a valid identifier.
  - Refer to `SetProductPriceRequest` in [OpenAPI Spec](../openapi/product-service.yaml) and validation rules in [Price and Discount Models](../02-data-model-setup/02c-price-models.md).
  - Key rules: `basePrice`, `salePrice`, `msrp` (positive, currency format), `currency` (valid ISO code), `priceType` (valid enum).

## Discount Endpoints

### 3. `POST /discounts`
- **Description:** Create a new discount.
- **Authentication:** Required (admin, manager)
- **Request Body:** Uses `DiscountCreateRequest` schema. See [OpenAPI Spec](../openapi/product-service.yaml) and details in [Price and Discount Models](../02-data-model-setup/02c-price-models.md).
  Example:
  ```json
  {
    "name": "Summer Sale 10% Off",
    "description": "10% off on selected summer items.",
    "type": "PERCENTAGE",
    "value": 10.00,
    "startDate": "2024-06-01T00:00:00Z",
    "endDate": "2024-08-31T23:59:59Z",
    "status": "DRAFT",
    "conditions": {"minOrderValue": 50}
  }
  ```
- **Response:**
  - 201 Created (Returns `Discount` schema)
- **Validation Rules:**
  - Refer to `DiscountCreateRequest` in [OpenAPI Spec](../openapi/product-service.yaml) and validation rules in [Price and Discount Models](../02-data-model-setup/02c-price-models.md).

### 4. `GET /discounts/{discountId}`
- **Description:** Retrieve a discount by its ID.
- **Authentication:** Required (admin, manager)
- **Parameters:**
  - `discountId` (Path): ID of the discount.
- **Response:**
  - 200 OK (Returns `Discount` schema)
  - 404 Not Found
- **Validation Rules:**
  - `discountId` must be a valid UUID.

### 5. `GET /discounts`
- **Description:** List all discounts, with filtering options.
- **Authentication:** Required (admin, manager)
- **Query Parameters:**
  - `status`, `type`, `page`, `limit`, `sort`
- **Response:**
  - 200 OK (Returns `DiscountListResponse` schema)
- **Validation Rules:**
  - Query parameters validated as per [OpenAPI Spec](../openapi/product-service.yaml).

### 6. `PATCH /discounts/{discountId}`
- **Description:** Update an existing discount.
- **Authentication:** Required (admin, manager)
- **Parameters:**
  - `discountId` (Path): ID of the discount.
- **Request Body:** Uses `DiscountUpdateRequest` schema. See [OpenAPI Spec](../openapi/product-service.yaml).
- **Response:**
  - 200 OK (Returns `Discount` schema)
  - 404 Not Found
- **Validation Rules:**
  - `discountId` must be a valid UUID.
  - Refer to `DiscountUpdateRequest` in [OpenAPI Spec](../openapi/product-service.yaml).

### 7. `DELETE /discounts/{discountId}`
- **Description:** Delete a discount.
- **Authentication:** Required (admin, manager)
- **Parameters:**
  - `discountId` (Path): ID of the discount.
- **Response:**
  - 204 No Content
  - 404 Not Found
- **Validation Rules:**
  - `discountId` must be a valid UUID.

### 8. `POST /products/{productVariantId}/discounts`
- **Description:** Apply a discount to a specific product variant.
- **Authentication:** Required (admin, manager)
- **Parameters:**
  - `productVariantId` (Path): ID of the product variant.
- **Request Body:** `{ "discountId": "uuid", "priority": 0 }` (Uses `ApplyDiscountRequest` schema)
- **Response:**
  - 200 OK 
  - 400 Bad Request (e.g., discount not found, product not found)
  - 404 Not Found
- **Validation Rules:**
  - `productVariantId` and `discountId` must be valid UUIDs.
  - `priority` should be an integer.

### 9. `DELETE /products/{productVariantId}/discounts/{discountId}`
- **Description:** Remove a discount from a specific product variant.
- **Authentication:** Required (admin, manager)
- **Parameters:**
  - `productVariantId` (Path): ID of the product variant.
  - `discountId` (Path): ID of the discount to remove.
- **Response:**
  - 204 No Content
  - 404 Not Found
- **Validation Rules:**
  - `productVariantId` and `discountId` must be valid UUIDs.

## Request/Response Schemas
- Detailed request/response schemas (DTOs) are defined in the [OpenAPI Specification](../openapi/product-service.yaml) under `components.schemas`.
- These schemas are based on the [Price and Discount Models](../02-data-model-setup/02c-price-models.md).

## Error Handling
- Standard error response structure is defined by `ErrorResponse` schema in the [OpenAPI Specification](../openapi/product-service.yaml).

## Links
- [Pricing Service Component Specification](../03-core-service-components/03-pricing-component.md) (if exists, or link to Price entity model)
- [OpenAPI Specification](../openapi/product-service.yaml)

## References
- [OpenAPI Specification](https://swagger.io/specification/) 