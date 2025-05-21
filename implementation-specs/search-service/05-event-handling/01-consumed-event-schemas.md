# Search Service - Consumed Event Schemas & Impact

## 1. Overview

This document details the key events consumed by the Search Service from other microservices. For each event, it outlines the expected payload structure (as defined by the publishing service) and how it impacts the search index documents (refer to `03-data-model-and-indexing.md` for the target search document structure).

All consumed events are expected to follow the `StandardMessage<T>` envelope from `@ecommerce-platform/rabbitmq-event-utils`.

## 2. Events from Product Service

### 2.1. `ProductCreatedEvent`
*   **Source**: Product Service
*   **Expected Payload (`ProductCreatedPayloadV1`)**: (Refer to Product Service's `05-event-publishing/01-event-schema-definitions.md` for the authoritative schema)
    ```json
    // Illustrative - Actual fields from Product Service event
    {
      "productId": "uuid",
      "name": "string",
      "descriptionShort": "string",
      "descriptionLong": "string",
      "sku": "string",
      "brandId": "uuid",
      "brandName": "string",
      "categoryIds": ["uuid"],
      "categoryNames": ["string"],
      "attributes": [{ "name": "string", "value": "string" }],
      "imageUrls": { "main": "string", "thumbnails": ["string"] },
      "isActive": "boolean",
      "createdAt": "timestamp",
      "tags": ["string"]
      // ... other core product fields
    }
    ```
*   **Impact on Search Index (`products` index)**:
    *   A new search document is created.
    *   Fields mapped: `id` (productId), `product_id`, `sku`, `name`, `name_exact`, `description_short`, `description_long`, `brand` (`brand_id`, `brand_name`), `categories` (from `categoryIds`, `categoryNames`), `attributes`, `image_url_main`, `image_urls_thumbnail`, `created_at`, `keywords` (from `tags`).
    *   Initial values for price, stock, ratings will be null/default until corresponding events are received or a full enrichment step occurs.
    *   `indexed_at` timestamp is set.
    *   If `isActive` is false, the document might be created but flagged as non-searchable or handled according to business rules.

### 2.2. `ProductUpdatedEvent`
*   **Source**: Product Service
*   **Expected Payload (`ProductUpdatedPayloadV1`)**: (Refer to Product Service)
    ```json
    // Illustrative
    {
      "productId": "uuid",
      "changes": { // Only includes fields that were changed
        "name": "string",
        "descriptionLong": "string",
        "categoryIds": ["uuid"],
        // ... any field from ProductCreatedPayload
      }
    }
    ```
*   **Impact on Search Index**:
    *   The existing search document for `productId` is updated (partial update preferred).
    *   Relevant fields in the search document are updated based on the `changes` in the payload.
    *   `indexed_at` timestamp is updated.

### 2.3. `ProductDeletedEvent`
*   **Source**: Product Service
*   **Expected Payload (`ProductDeletedPayloadV1`)**: (Refer to Product Service)
    ```json
    // Illustrative
    {
      "productId": "uuid",
      "reason": "string" // Optional
    }
    ```
*   **Impact on Search Index**:
    *   The search document corresponding to `productId` is deleted from the index.

### 2.4. `ProductPublishedEvent` / `ProductUnpublishedEvent`
*   **Source**: Product Service
*   **Expected Payload**: Contains `productId` and new status.
*   **Impact on Search Index**:
    *   Updates a status field in the search document (e.g., `is_searchable: true/false` or `product_status: "published"/"unpublished"`).
    *   This field would be used in search queries to filter out unpublished products.

## 3. Events from Price Service (Hypothetical)

*(Assuming a dedicated Price Service)*

### 3.1. `ProductPriceUpdatedEvent`
*   **Source**: Price Service
*   **Expected Payload (`ProductPriceUpdatedPayloadV1`)**:
    ```json
    {
      "productId": "uuid",
      "variantId": "uuid", // Optional, if prices are per variant
      "currentPrice": "float",
      "originalPrice": "float", // Optional
      "currency": "string", // e.g., "USD"
      "onSale": "boolean",
      "discountPercentage": "float", // Optional
      "effectiveFrom": "timestamp",
      "effectiveUntil": "timestamp" // Optional
    }
    ```
*   **Impact on Search Index**:
    *   Updates price-related fields in the search document for the given `productId` (and `variantId` if applicable): `price_current`, `price_original`, `currency`, `on_sale`, `discount_percentage`.
    *   `indexed_at` timestamp is updated.

## 4. Events from Inventory Service

### 4.1. `StockLevelChangedEvent`
*   **Source**: Inventory Service
*   **Expected Payload (`StockLevelChangedPayloadV1`)**: (Refer to Inventory Service `01-event-schema-definitions.md`)
    ```json
    // Illustrative
    {
      "inventoryItemId": "uuid",
      "productId": "uuid",
      "sku": "string",
      "variantId": "uuid", // Optional
      "warehouseId": "uuid",
      "newQuantityAvailable": "integer",
      "previousQuantityAvailable": "integer",
      "changeType": "string" // e.g., "sale", "receipt", "adjustment"
    }
    ```
*   **Impact on Search Index**:
    *   Updates stock-related fields for the `productId` (and `variantId` if applicable): `stock_status` (derived from `newQuantityAvailable`), `available_quantity`, `is_available`.
    *   If multiple warehouses exist, logic might be needed to aggregate stock status or determine overall availability for search (e.g., available if in stock in *any* shipping-enabled warehouse).
    *   `indexed_at` timestamp is updated.

## 5. Events from Review Service (Hypothetical)

*(Assuming a dedicated Review Service)*

### 5.1. `AverageRatingUpdatedEvent`
*   **Source**: Review Service
*   **Expected Payload (`AverageRatingUpdatedPayloadV1`)**:
    ```json
    {
      "productId": "uuid",
      "newAverageRating": "float",
      "newReviewCount": "integer"
    }
    ```
*   **Impact on Search Index**:
    *   Updates `average_rating` and `review_count` fields in the search document for `productId`.
    *   `indexed_at` timestamp is updated.

## 6. Data Transformation and Enrichment

*   The Search Service event handlers are responsible for transforming the incoming event payloads into the flat, denormalized structure of the search index document.
*   This might involve simple field mapping, data type conversions, or deriving new fields (e.g., calculating `discount_percentage`, determining `stock_status` based on quantity).
*   Enrichment (fetching additional data from other services synchronously during event processing) should be minimized to maintain low latency and loose coupling. Prefer that events carry all necessary information. If enrichment is unavoidable, it must be done with resilient clients (timeouts, retries, circuit breakers).

## 7. Handling Missing Data and Schema Evolution

*   Event handlers should be resilient to missing optional fields in event payloads.
*   As event schemas from publishing services evolve (e.g., new versions indicated in `StandardMessage.version`), the Search Service event handlers may need to be updated to correctly process new or changed fields.
    *   Consumers should be tolerant of new, non-breaking fields.
    *   Breaking changes in consumed event schemas will require coordinated updates.
