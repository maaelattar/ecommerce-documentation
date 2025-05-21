# Product Events for Search Service

## Overview

The Search Service subscribes to a variety of events originating from the Product Service (and potentially other services that modify product data, like Inventory Service for stock updates) to keep its product search index current. These events signal creations, updates, deletions, and other relevant changes to product information.

## Subscribed Product Events

The following events are typically consumed by the Search Service. Event names and payloads should be standardized across the microservices.

### 1. `ProductCreated`

*   **Source Service**: Product Service
*   **Topic**: `product.events` (or a more specific `product.lifecycle.events`)
*   **Trigger**: A new product is successfully created and persisted in the Product Service.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-product-created-1",
      "eventType": "ProductCreated",
      "timestamp": "2023-11-15T10:00:00Z",
      "version": "1.0",
      "source": "ProductService",
      "data": {
        "id": "prod_12345",
        "name": "Organic Cotton T-Shirt",
        "description": "A comfortable and eco-friendly t-shirt made from 100% organic cotton.",
        "sku": "ORG-COT-TS-M-BLK",
        "price": {
          "amount": 25.99,
          "currency": "USD"
        },
        "categories": [
          {"id": "cat_001", "name": "Apparel"},
          {"id": "cat_005", "name": "T-Shirts"}
        ],
        "brand": {
          "id": "brand_xyz",
          "name": "EcoThreads"
        },
        "attributes": [
          {"name": "Color", "value": "Black"},
          {"name": "Size", "value": "M"},
          {"name": "Material", "value": "Organic Cotton"}
        ],
        "variants": [
          {
            "sku": "ORG-COT-TS-M-RED",
            "price": {"amount": 25.99, "currency": "USD"},
            "attributes": [{"name": "Color", "value": "Red"}, {"name": "Size", "value": "M"}],
            "stockQuantity": 50,
            "imageUrl": "https://example.com/images/prod_12345_red.jpg"
          }
        ],
        "tags": ["organic", "cotton", "eco-friendly", "casual"],
        "imageUrl": "https://example.com/images/prod_12345_black.jpg",
        "slug": "organic-cotton-t-shirt-black-m",
        "isActive": true,
        "createdAt": "2023-11-15T09:58:00Z",
        "updatedAt": "2023-11-15T09:58:00Z"
        // Include all necessary fields for indexing
      }
    }
    ```
*   **Search Service Action**: Create a new document in the product search index.

### 2. `ProductUpdated`

*   **Source Service**: Product Service
*   **Topic**: `product.events`
*   **Trigger**: An existing product's details (e.g., name, description, price, attributes, categories) are updated.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-product-updated-2",
      "eventType": "ProductUpdated",
      "timestamp": "2023-11-15T10:30:00Z",
      "version": "1.0",
      "source": "ProductService",
      "data": {
        "id": "prod_12345", // Identifier of the product being updated
        // Full updated product data or partial data with clear indication of changed fields.
        // Sending the full updated product data is often simpler for the search service to process.
        "name": "Premium Organic Cotton T-Shirt",
        "description": "An exceptionally soft and eco-friendly t-shirt, made from 100% GOTS certified organic cotton.",
        "price": {
          "amount": 27.99,
          "currency": "USD"
        },
        "attributes": [
          {"name": "Color", "value": "Black"},
          {"name": "Size", "value": "M"},
          {"name": "Material", "value": "GOTS Organic Cotton"} // Updated material
        ],
        "tags": ["organic", "cotton", "eco-friendly", "premium", "casual"], // Added a tag
        "updatedAt": "2023-11-15T10:29:00Z"
        // ... other fields that might have changed or the full product representation
      }
    }
    ```
*   **Search Service Action**: Update the corresponding document in the product search index. If partial updates are sent, the service needs to correctly merge changes. Full updates simplify this.

### 3. `ProductDeleted`

*   **Source Service**: Product Service
*   **Topic**: `product.events`
*   **Trigger**: A product is permanently deleted from the Product Service.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-product-deleted-3",
      "eventType": "ProductDeleted",
      "timestamp": "2023-11-15T11:00:00Z",
      "version": "1.0",
      "source": "ProductService",
      "data": {
        "id": "prod_67890", // Identifier of the product being deleted
        "deletedAt": "2023-11-15T10:59:50Z"
      }
    }
    ```
*   **Search Service Action**: Delete the corresponding document from the product search index.

### 4. `ProductPriceChanged`

*   **Source Service**: Product Service (or a dedicated Pricing Service)
*   **Topic**: `product.events` or `pricing.events`
*   **Trigger**: The price of a product or its variants changes.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-price-changed-4",
      "eventType": "ProductPriceChanged",
      "timestamp": "2023-11-15T12:00:00Z",
      "version": "1.0",
      "source": "PricingService",
      "data": {
        "productId": "prod_12345",
        "variantSku": "ORG-COT-TS-M-BLK", // Optional, if prices are per variant
        "newPrice": {
          "amount": 24.99,
          "currency": "USD"
        },
        "oldPrice": {
          "amount": 25.99,
          "currency": "USD"
        },
        "effectiveFrom": "2023-11-16T00:00:00Z"
      }
    }
    ```
*   **Search Service Action**: Update the price fields in the relevant product document(s) in the search index.

### 5. `ProductStockChanged` (or `InventoryUpdated`)

*   **Source Service**: Inventory Service (or Product Service if it manages stock)
*   **Topic**: `inventory.events` or `product.events`
*   **Trigger**: The stock level or availability status of a product/variant changes.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-stock-changed-5",
      "eventType": "ProductStockChanged",
      "timestamp": "2023-11-15T13:00:00Z",
      "version": "1.0",
      "source": "InventoryService",
      "data": {
        "productId": "prod_12345",
        "variantSku": "ORG-COT-TS-M-BLK", // Or other variant identifier
        "newStockQuantity": 75,
        "oldStockQuantity": 80,
        "isAvailable": true // Derived or direct status
      }
    }
    ```
*   **Search Service Action**: Update stock quantity and availability status in the product search index. This is crucial for filtering out-of-stock items or displaying stock levels.

### 6. `ProductStatusChanged` (e.g., `Published`, `Unpublished`, `Archived`)

*   **Source Service**: Product Service
*   **Topic**: `product.events`
*   **Trigger**: The visibility or status of a product changes (e.g., made active/inactive, published/unpublished).
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-status-changed-6",
      "eventType": "ProductStatusChanged",
      "timestamp": "2023-11-15T14:00:00Z",
      "version": "1.0",
      "source": "ProductService",
      "data": {
        "productId": "prod_inactive001",
        "newStatus": "inactive", // e.g., active, inactive, archived, draft
        "oldStatus": "active"
      }
    }
    ```
*   **Search Service Action**: Update the product's status in the search index. This can affect whether the product appears in search results.

## General Considerations for Product Events

*   **Data Granularity**: Events should contain sufficient data for the Search Service to update its index without needing to make synchronous calls back to the source service (unless absolutely necessary for data enrichment not available in the event).
*   **Event Versioning**: Include a `version` field in the event payload to manage changes to event structures over time.
*   **Timestamps**: Accurate `timestamp` fields are crucial for ordering and debugging.
*   **Idempotency Keys**: While event IDs (`eventId`) help, the processing logic in the Search Service should be idempotent, meaning processing the same event multiple times has no adverse effects.
*   **Schema Consistency**: Using a schema registry (e.g., Confluent Schema Registry with Avro) is highly recommended to enforce event schema consistency.

## Search Service Responsibilities

*   Subscribe to the relevant Kafka topics where these events are published.
*   Deserialize and validate incoming event messages.
*   Transform the event data into the format required by the Elasticsearch product index schema.
*   Perform the appropriate CRUD operation (Create, Update, Delete) on the Elasticsearch index.
*   Handle errors gracefully (e.g., retry mechanisms, dead-letter queues).
*   Ensure idempotency of event processing.
