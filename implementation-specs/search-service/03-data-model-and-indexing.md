# Search Service - Data Model and Indexing

## 1. Overview

The Search Service maintains a denormalized search index optimized for fast and relevant query execution. This index is built by consuming data from various source-of-truth services (primarily Product Service, but also Inventory, Pricing, Reviews, etc.) via events.

## 2. Search Engine Choice

The underlying search engine (e.g., OpenSearch, Elasticsearch) will be determined by a specific ADR. This document assumes a document-based search engine with JSON-like document structures and powerful indexing/querying capabilities.

## 3. Search Index Design (`products` index)

A primary index, let's call it `products`, will store searchable product information. Each document in this index will represent a product (or a product variant if variants are individually searchable entities).

### 3.1. Document Structure (Illustrative)

The structure below is an example and will be refined based on specific search requirements and available data from source services. All fields are designed to support querying, filtering (faceting), sorting, and relevance scoring.

```json
{
  // Core Identifiers & Searchable Text
  "id": "uuid", // Unique ID for this search document (could be product_id or variant_id)
  "product_id": "uuid",
  "variant_id": "uuid", // If variants are indexed separately
  "sku": "string",
  "name": "text_analyzed", // Product name (e.g., tokenized, stemmed, lowercase)
  "name_exact": "keyword", // For exact matches or suggestions
  "description_short": "text_analyzed",
  "description_long": "text_analyzed",
  "keywords": ["text_analyzed"], // Tags, search terms
  
  // Categorization & Taxonomy
  "categories": [
    { "id": "uuid", "name": "keyword", "path": "keyword" } // e.g., "Electronics/Computers/Laptops"
  ],
  "category_ids": ["uuid"], // For filtering
  "category_names": ["keyword"],
  "brand": { "id": "uuid", "name": "keyword" },
  "brand_name": "keyword",
  
  // Pricing & Availability (denormalized from Price & Inventory Services)
  "price_current": "float", // Current sale price
  "price_original": "float", // Original price (for showing discounts)
  "currency": "keyword", // e.g., "USD"
  "on_sale": "boolean",
  "discount_percentage": "float",
  "stock_status": "keyword", // e.g., "in_stock", "out_of_stock", "low_stock", "preorder"
  "available_quantity": "integer", // Actual quantity (use with caution for display, good for filtering)
  "is_available": "boolean", // Simplifies filtering for "in stock"
  
  // Product Attributes (dynamic, for faceting and filtering)
  "attributes": [
    { "name": "keyword", "value_string": "keyword", "value_numeric": "float" } // e.g., color:red, size:XL, weight:2.5
    // Store values in typed fields for proper range queries and sorting if needed
  ],
  // Example of flattened attributes for easier faceting if structure is known:
  "color": ["keyword"], // e.g., ["Red", "Burgundy"]
  "size": ["keyword"],  // e.g., ["XL", "Extra Large"]
  "material": ["keyword"],
  
  // Imagery
  "image_url_main": "keyword", // URL of the primary image
  "image_urls_thumbnail": ["keyword"],
  
  // Ratings & Reviews (denormalized from a Reviews Service)
  "average_rating": "float",
  "review_count": "integer",
  
  // Timestamps & Flags
  "created_at": "date", // Product creation date
  "updated_at": "date", // Last update in source system
  "indexed_at": "date", // When this document was last indexed/updated
  "is_new_arrival": "boolean", // Flag for "new" products (e.g., created in last 30 days)
  "is_best_seller": "boolean", // Flag for best-selling products
  "is_featured": "boolean",   // Flag for featured products
  
  // Variant Information (if variants are grouped under a parent product document)
  "variants": [
    {
      "variant_id": "uuid",
      "sku": "string",
      "attributes": [{ "name": "keyword", "value": "keyword" }], // e.g., color:blue, size:M
      "price_current": "float",
      "stock_status": "keyword",
      "image_url": "keyword"
    }
  ],
  
  // Personalization & Merchandising Signals (optional, for future enhancements)
  "popularity_score": "float", // Derived from sales, views, etc.
  "boost_score": "float"      // For merchandising rules
}
```

### 3.2. Field Types and Analysis

*   **`keyword`**: For exact matches, sorting, aggregations (facets). Not tokenized.
*   **`text_analyzed`**: For full-text search. Undergoes analysis (tokenization, lowercasing, stemming, synonym expansion).
    *   Different analyzers might be used for different text fields (e.g., standard analyzer, language-specific analyzers).
*   **`integer`, `float`, `double`, `long`**: For numeric values, enabling range queries and sorting.
*   **`date`**: For date/time values, enabling range queries and sorting. Stored in a standard format (e.g., ISO 8601 or epoch milliseconds).
*   **`boolean`**: For true/false flags.
*   **`nested` or `object`**: For structured objects within a document. `nested` type is preferred if individual objects in an array need to be queried independently.

### 3.3. Index Mappings

Explicit mappings will be defined for the `products` index in the search engine. This includes:
*   Defining the data type for each field.
*   Specifying the analyzer for `text_analyzed` fields.
*   Enabling/disabling indexing (`index: true/false`) or doc values (`doc_values: true/false`) for specific fields to optimize storage and performance.
*   Setting up multi-fields (e.g., a `name` field analyzed for search and a `name.keyword` field for exact sorting/aggregation).

## 4. Indexing Process

### 4.1. Event-Driven Updates
*   The Search Service consumes events from services like Product, Price, Inventory, etc., via RabbitMQ.
*   Event handlers transform the incoming event data into the denormalized search document structure.
*   Updates are typically partial updates to existing documents to avoid re-indexing the entire document, if the search engine supports it efficiently (e.g., updating only price and stock_status).
*   If a product is newly created, a new document is added.
*   If a product is deleted, the corresponding document is removed from the index.

### 4.2. Data Denormalization
*   Data from various sources is combined into a single product document in the search index. For example:
    *   Core product details from Product Service.
    *   Pricing information from Price Service.
    *   Stock levels from Inventory Service.
    *   Average ratings from a Reviews Service.
*   This denormalization is crucial for fast query performance, as it avoids joins at query time.
*   The trade-off is increased complexity in keeping the denormalized data consistent via event handling.

### 4.3. Index Aliases
*   Index aliases (e.g., `products_alias` pointing to `products_v1`) will be used to allow for zero-downtime re-indexing or mapping changes.
*   When a new index version (`products_v2`) is built, the alias is atomically switched to point to the new version once it's ready.

### 4.4. Batch and Bulk Processing
*   For initial data loading or large updates, the Indexing Engine will use bulk APIs provided by the search engine to efficiently process many documents at once.

### 4.5. Handling Deletions and Updates
*   Events like `ProductDeleted`, `ProductUnpublished` will trigger the removal of the document from the search index.
*   Events like `ProductPriceUpdated`, `InventoryStockChanged` will trigger updates to specific fields within the existing search documents.

## 5. Data Consistency and Freshness

*   **Near Real-Time Updates**: The goal is to reflect changes in source systems in the search index within a few seconds to minutes.
*   **Eventual Consistency**: Due to the distributed nature, there might be brief periods of inconsistency between source systems and the search index. The system is designed for eventual consistency.
*   **Error Handling**: Robust error handling and retry mechanisms in the event consumption and indexing pipeline are critical.
*   **Full Re-indexing (Fallback)**: A mechanism for performing full or partial re-indexing from source systems should be available as a fallback or for periodic consistency checks, though event-driven updates are the primary method.

## 6. Considerations for Other Content Types

If the Search Service is extended to other content (e.g., blog posts, help articles):
*   Separate indexes might be created (e.g., `articles_index`).
*   The document structure and indexing process would be tailored to that content type.
*   Event sources for this content would need to be identified.
