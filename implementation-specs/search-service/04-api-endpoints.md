# Search Service - API Endpoints

## 1. Overview

The Search Service exposes public-facing APIs that client applications (web frontend, mobile apps) use to perform product searches, retrieve suggestions, and navigate categorized product listings with filtering and sorting.

These APIs are designed for high performance and scalability, as they are critical to the user experience.

## 2. Key API Endpoints

### 2.1. Product Search API

*   **`GET /v1/search/products`** (or simply **`GET /v1/products`** if it serves as the primary product listing endpoint)
    *   **Description**: Performs a full-text search across the product catalog. Supports filtering, faceting, sorting, and pagination.
    *   **Query Parameters**:
        *   `q` (string, optional): The user's search query/keywords.
        *   `category` (string, optional): Category ID or slug to filter by.
        *   `brand` (string, optional): Brand ID or name to filter by.
        *   `price_min` (number, optional): Minimum price.
        *   `price_max` (number, optional): Maximum price.
        *   `attributes.{name}` (string, optional): Dynamic attribute filters, e.g., `attributes.color=Red&attributes.size=XL`.
        *   `rating_min` (number, optional): Minimum average product rating.
        *   `sort_by` (string, optional): Field to sort by (e.g., `relevance`, `price_asc`, `price_desc`, `created_at_desc`, `rating_desc`). Default is `relevance`.
        *   `page` (integer, optional, default: 1): Page number for pagination.
        *   `limit` (integer, optional, default: 20): Number of items per page.
        *   `include_facets` (boolean, optional, default: true): Whether to include facet counts in the response.
        *   `user_id` (string, optional): For personalization or analytics.
        *   `session_id` (string, optional): For analytics or A/B testing.
    *   **Responses**:
        *   `200 OK`: Successful search. Response body includes search results, pagination details, and facet information.
            ```json
            // Illustrative Response Structure
            {
              "meta": {
                "query": "user search query",
                "total_results": 1250,
                "page": 1,
                "limit": 20,
                "total_pages": 63,
                "sort_by": "relevance"
              },
              "results": [
                // Array of product documents (see 03-data-model-and-indexing.md for structure)
                { "id": "prod123", "name": "Awesome T-Shirt", ... }
              ],
              "facets": {
                "categories": [
                  { "id": "cat1", "name": "Electronics", "count": 300 },
                  { "id": "cat2", "name": "Laptops", "count": 150, "parent_id": "cat1" }
                ],
                "brand_name": [
                  { "value": "BrandA", "count": 120 },
                  { "value": "BrandB", "count": 90 }
                ],
                "color": [
                  { "value": "Red", "count": 50 },
                  { "value": "Blue", "count": 75 }
                ],
                "price_ranges": [ // Could be pre-defined or dynamically generated
                  { "label": "$0-$50", "min": 0, "max": 50, "count": 200 }
                ]
                // ... other facets
              }
            }
            ```
        *   `400 BAD REQUEST`: Invalid query parameters (e.g., invalid sort option, non-numeric price).
        *   `500 INTERNAL SERVER ERROR`: Search engine unavailable or other server-side error.

### 2.2. Autosuggest / Typeahead API

*   **`GET /v1/search/suggest`**
    *   **Description**: Provides search suggestions as the user types. Suggestions can include product names, categories, brands, or popular queries.
    *   **Query Parameters**:
        *   `q` (string, required): The partial search query typed by the user.
        *   `limit` (integer, optional, default: 10): Maximum number of suggestions to return.
        *   `include_types` (string, optional): Comma-separated list of suggestion types to include (e.g., `products,categories,brands,queries`). Default includes a mix.
    *   **Responses**:
        *   `200 OK`: Successful. Response body includes a list of suggestions.
            ```json
            // Illustrative Response Structure
            {
              "query": "lapto",
              "suggestions": [
                { "type": "product", "value": "Laptop Pro X1", "highlight": "<strong>Lapto</strong>p Pro X1", "id": "prod456" },
                { "type": "category", "value": "Laptops", "highlight": "<strong>Lapto</strong>ps", "id": "cat2" },
                { "type": "brand", "value": "LaptopBrand", "highlight": "<strong>Lapto</strong>pBrand" },
                { "type": "query", "value": "laptop charger", "highlight": "<strong>laptop</strong> charger" }
              ]
            }
            ```
        *   `400 BAD REQUEST`: Missing or empty `q` parameter.

### 2.3. Get Similar Products API (Optional)

*   **`GET /v1/products/{productId}/similar`**
    *   **Description**: Retrieves products that are similar to a given product. Similarity can be based on content (category, attributes) or collaborative filtering (users who viewed/bought this also viewed/bought these).
    *   **Query Parameters**:
        *   `limit` (integer, optional, default: 5): Number of similar products to return.
    *   **Responses**:
        *   `200 OK`: Returns a list of similar product documents.
        *   `404 NOT FOUND`: Product with `{productId}` not found.

### 2.4. Administrative APIs (Internal)

*   **`POST /v1/admin/index/rebuild`** (Protected Endpoint)
    *   **Description**: Triggers a full or partial re-indexing process. Should be used with caution.
    *   **Request Body**: `{ "index_name": "products", "type": "full" | "partial", "source_filters": { ... } }`
    *   **Responses**: `202 ACCEPTED`: Re-indexing job started.
*   **`POST /v1/admin/synonyms`** (Protected Endpoint)
    *   **Description**: Adds or updates a synonym rule.
    *   **Request Body**: `{ "term": "sofa", "synonyms": ["couch", "settee"] }`
    *   **Responses**: `200 OK` or `201 CREATED`.
*   **`GET /v1/admin/index/status`** (Protected Endpoint)
    *   **Description**: Returns the status of the search indexes (doc counts, size, health).
    *   **Responses**: `200 OK`.

## 3. API Design Principles

*   **RESTful**: Follow REST principles.
*   **Performance**: APIs must be highly performant, especially `/search/products` and `/search/suggest`.
*   **Caching**: Employ caching strategies (CDN, in-memory, distributed cache like Redis) for frequently accessed data and suggestions.
*   **Idempotency**: GET requests are naturally idempotent. POST/PUT for admin actions should be designed to be idempotent where possible.
*   **Security**: While largely public, consider rate limiting and protection against query abuse. Admin endpoints must be strictly secured.

## 4. OpenAPI Specification

The detailed OpenAPI specification for these endpoints will be maintained in:
`./openapi/openapi.yaml`

This file will provide formal definitions for request/response schemas, parameters, and authentication methods for admin APIs.
