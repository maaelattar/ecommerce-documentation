# Product Service Integration with Search Service (Amazon OpenSearch Service)

## 1. Overview

This document details how the Product Service integrates with the central Search Service, which is powered by **Amazon OpenSearch Service** as per the technology decision in [04-nosql-database-selection.md](../../../architecture/technology-decisions-aws-centeric/04-nosql-database-selection.md).

The primary goal of this integration is to make product catalog data (products, variants, categories, pricing information) searchable and discoverable by end-users through various client applications (e.g., web storefront, mobile app).

The integration is primarily **asynchronous and event-driven**. The Product Service publishes events related to data changes, and a dedicated Search Indexing mechanism (potentially a separate microservice or a component within a broader Search Service) consumes these events to keep the Amazon OpenSearch Service index up-to-date.

## 2. Integration Architecture & Data Flow

```
+-------------------+     (Events: ProductCreated,     +------------------------+     (Updates Index)     +-------------------------+
|  Product Service  | -->  ProductUpdated, etc.)  --> | Search Event Consumer  | -->                     --> | Amazon OpenSearch Service |
+-------------------+     (via Message Broker)        +------------------------+                           +-------------------------+
                                   ^                                                                                   |
                                   | (Search Queries)                                                                  | (Serves Search API)
                                   |                                                                                   V
+-------------------+     (API Calls)                 +------------------------+
| Client Application| <--                             <-- |   Search API / Gateway |
+-------------------+                                 +------------------------+
```

**Key Components:**

1.  **Product Service**:
    *   Publishes fine-grained events for all relevant data changes (CRUD operations on products, variants, categories, prices, etc.). See [Phase 5: Event Publishing](../../05-event-publishing/) for event details.
    *   The "Search Integration Component" mentioned in the `00-implementation-plan-index.md` can be considered as the part of Product Service responsible for ensuring all necessary data attributes are included in these events for search indexing purposes.
2.  **Message Broker**: (e.g., Amazon MQ for RabbitMQ or Amazon MSK, as per [03-message-broker-selection.md](../../../architecture/technology-decisions-aws-centeric/03-message-broker-selection.md))
    *   Decouples the Product Service from the Search Event Consumer.
    *   Provides resilience and durability for events.
3.  **Search Event Consumer/Indexer**:
    *   A dedicated microservice or component responsible for subscribing to product-related events from the message broker.
    *   Transforms event payloads into the document structure required by the OpenSearch index.
    *   Handles Create, Update, and Delete operations against the OpenSearch index based on the event type.
    *   Implements error handling, retries, and dead-letter queue (DLQ) mechanisms for failed indexing attempts.
4.  **Amazon OpenSearch Service**:
    *   The managed search engine where product data is indexed and made searchable.
    *   Stores product documents in a denormalized format optimized for search.
5.  **Search API / Gateway**:
    *   Provides a dedicated API endpoint for client applications to perform search queries against the OpenSearch index.
    *   This API is *not* directly part of the Product Service but consumes the data indexed from it.

## 3. Data to be Indexed

The following information from the Product Service domain should be indexed in OpenSearch for a comprehensive search experience. The exact OpenSearch mapping will define data types, analyzers, and indexing options.

### 3.1. Product Document Structure (Conceptual)

A single document in OpenSearch will typically represent a **searchable product entity**, which might be a specific product variant or a parent product depending on the desired search granularity. Often, variants are indexed to allow searching by specific attributes like size or color.

```json
{
  "id": "unique_document_id_e.g_variant_uuid", // Or product_uuid if indexing at product level
  "productId": "product_uuid",
  "variantId": "variant_uuid_if_applicable",
  "sku": "SKU12345",
  "name": "Men's Classic Cotton T-Shirt - Blue, Large", // Analyzed for full-text search
  "description": "A comfortable and durable t-shirt made from 100% premium cotton...", // Analyzed
  "shortDescription": "Classic cotton t-shirt.", // Analyzed
  "brand": "AwesomeBrand", // Facetable
  "categories": [ // Facetable, searchable
    { "id": "cat_uuid_1", "name": "Apparel", "path": "Apparel" },
    { "id": "cat_uuid_2", "name": "Men's", "path": "Apparel/Men's" },
    { "id": "cat_uuid_3", "name": "T-Shirts", "path": "Apparel/Men's/T-Shirts" }
  ],
  "attributes": [ // Dynamic, facetable, searchable
    { "name": "color", "value": "Blue" },
    { "name": "size", "value": "Large" },
    { "name": "material", "value": "Cotton" }
  ],
  "price": { // Sortable, range filterable
    "originalAmount": "25.00",
    "saleAmount": "19.99", // Current effective price
    "currency": "USD"
  },
  "imageUrl": "https://example.com/images/product_123.jpg",
  "thumbnailUrl": "https://example.com/images/product_123_thumb.jpg",
  "productStatus": "ACTIVE", // Filterable (e.g., only show ACTIVE products)
  "tags": ["cotton", "summer", "casual"], // Searchable, potentially facetable
  "averageRating": 4.5, // Sortable, filterable
  "reviewCount": 150, // Sortable, filterable
  "inventoryStatus": "IN_STOCK", // Filterable (e.g. IN_STOCK, OUT_OF_STOCK, LOW_STOCK)
  "stockLevel": 130, // Potentially sortable or for boosting if available, filterable
  "isNewArrival": true, // Filterable, for promotions
  "onSale": true, // Filterable
  "createdAt": "ISO8601_timestamp",
  "updatedAt": "ISO8601_timestamp", // For relevance scoring (e.g., boost recent updates)
  "searchKeywords": ["tshirt", "tee", "mens wear", "top"] // Hidden field with synonyms, common misspellings for improved recall
}
```

**Notes on Fields:**

*   **Analyzed Fields**: Fields like `name`, `description`, `tags`, `searchKeywords` will use appropriate OpenSearch analyzers (e.g., standard, language-specific) for tokenization, stemming, and stop word removal to enable effective full-text search.
*   **Facetable Fields**: Fields like `brand`, `categories.name`, `attributes.name` and `attributes.value`, `productStatus`, `onSale` will be indexed to allow for faceted navigation (filtering by these attributes). These are typically keyword or term fields.
*   **Sortable Fields**: Fields like `price.saleAmount`, `averageRating`, `reviewCount`, `updatedAt` will be indexed appropriately to allow sorting of search results.
*   **Denormalization**: Category names, attribute names/values are denormalized into the product document for efficient filtering and display without requiring joins at query time.
*   `inventoryStatus` and `stockLevel`: This data originates from the Inventory Service. The Search Event Consumer might need to enrich the product data by fetching this information from the Inventory Service (if available synchronously via an API) or by consuming events from the Inventory Service itself before indexing into OpenSearch. This introduces a dependency and potential consistency challenge that needs careful design. A simpler approach is to only index product data, and client applications make separate calls if live inventory is needed post-search. However, for filtering by "IN_STOCK", some level of inventory status in the index is often required.

## 4. Event Handling by Search Event Consumer

The Search Event Consumer will handle the following events from Product Service (and potentially Inventory Service for stock status):

*   **ProductCreated/ProductVariantAdded**: Creates a new document in OpenSearch.
*   **ProductUpdated/ProductVariantUpdated**: Updates an existing document. This might involve a partial update or re-indexing the entire document.
*   **ProductPriceUpdated/DiscountApplied**: Updates pricing information in the relevant product documents.
*   **ProductStatusChanged**: Updates the `productStatus` field.
*   **ProductDeleted/ProductVariantRemoved**: Deletes the document from OpenSearch.
*   **CategoryCreated/Updated/Deleted**: If category information changes, all associated product documents might need updating if category details are denormalized.
*   **(Optional) InventoryUpdated**: If the Search Event Consumer also listens to inventory events, it updates `inventoryStatus` and `stockLevel` in the search index.

## 5. OpenSearch Index Configuration Considerations

*   **Index Name**: A clear naming convention for indices (e.g., `products_v1`). Aliases should be used to allow for zero-downtime re-indexing (e.g., `products_live` pointing to `products_v1`).
*   **Mappings**: Explicitly define mappings for all fields to ensure correct data types, analyzers, and indexing options.
*   **Sharding and Replicas**: Configure appropriate number of primary shards for scalability and replica shards for availability and query throughput, based on expected data volume and query load. This is managed by Amazon OpenSearch Service.
*   **Analyzers and Tokenizers**: Customize analyzers for specific fields (e.g., language-specific analyzers, analyzers for SKU/codes).
*   **Refresh Interval**: Configure the index refresh interval to balance near real-time indexing with performance.

## 6. Querying the Index

Client applications will query the Search API, which in turn constructs and executes queries against Amazon OpenSearch Service. Typical search functionalities will include:

*   Full-text search across multiple fields.
*   Filtering by facets (category, brand, attributes, price range, status).
*   Sorting by relevance, price, rating, recency, etc.
*   Pagination.
*   Suggestions (autocomplete).
*   "Did you mean?" functionality.

The Product Service itself generally does *not* query the OpenSearch index for its own operations. It relies on its primary database (PostgreSQL).

## 7. Resilience and Error Handling

*   **Product Service**: Publishes events reliably to the message broker.
*   **Message Broker**: Ensures event persistence.
*   **Search Event Consumer**:
    *   Implements idempotent processing to handle duplicate events.
    *   Uses retries with exponential backoff for transient errors when updating OpenSearch.
    *   Sends unrecoverable messages to a Dead-Letter Queue (DLQ) for investigation.
    *   Monitors the health of OpenSearch and the size of event queues.
*   **Amazon OpenSearch Service**: Leverages AWS managed service capabilities for high availability and fault tolerance.

## 8. Security

*   Access to Amazon OpenSearch Service will be controlled via IAM roles and security groups/VPC configurations.
*   The Search Event Consumer will use appropriate credentials to write to OpenSearch.
*   The Search API will use appropriate credentials to read from OpenSearch.

## 9. Future Considerations

*   Personalized search results.
*   Machine learning for query understanding and ranking (e.g., Amazon Personalize, OpenSearch Learning to Rank).
*   A/B testing of different search algorithms or ranking strategies.

## 10. References

*   [Phase 5: Event Publishing](../../05-event-publishing/)
*   [Technology Decision: NoSQL Database Selection (Amazon OpenSearch Service)](../../../architecture/technology-decisions-aws-centeric/04-nosql-database-selection.md)
*   [Technology Decision: Message Broker Selection](../../../architecture/technology-decisions-aws-centeric/03-message-broker-selection.md)
*   [Amazon OpenSearch Service Documentation](https://aws.amazon.com/opensearch-service/) 