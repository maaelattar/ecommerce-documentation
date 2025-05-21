# Search Service - Core Service Components

## 1. Overview

The Search Service is architected to efficiently index data and serve search queries. It typically consists of a data ingestion pipeline, a search engine core, and an API layer.

## 2. Architectural Layers and Key Modules

```mermaid
graph TD
    subgraph "Search Service"
        A[API Layer (Query & Suggestion API)]
        B[Query Processing Engine]
        C[Indexing Engine & Data Sync]
        D[Search Engine Core (e.g., Elasticsearch/OpenSearch Cluster)]
        E[Configuration & Relevancy Management]
        F[Shared Utilities]

        A --> B
        B --> D
        C --> D
        E --> B
        E --> C
        A --> F
        B --> F
        C --> F
    end

    U[User / Client Application] -- Search Queries / Suggestions --> A
    EV[Other Microservices (Product, Inventory, etc.)] -- Publishes Events --> RMQ[(RabbitMQ)]
    RMQ -- Consumes Events --> C
```

### 2.1. API Layer (`SearchApiModule`)

*   **Responsibilities**:
    *   Exposes public-facing RESTful APIs for search queries, faceted navigation, autosuggestions, and potentially other search-related functionalities.
    *   Handles incoming API requests, authentication/authorization (if any, e.g., API key for certain clients), and request validation.
    *   Transforms API responses into a consistent format for client consumption.
*   **Key Components**:
    *   `SearchController`: Handles `/search` and `/products` (or similar) endpoints for full-text search, filtering, and sorting.
    *   `SuggestController`: Handles `/suggest` or `/autocomplete` endpoints for typeahead suggestions.
    *   `RequestDTOs`: Data Transfer Objects for search queries, filter parameters, pagination, etc.
    *   `ResponseDTOs`: DTOs for search results, facets, suggestions.
    *   `ValidationPipes`: For validating request parameters.

### 2.2. Query Processing Engine (`QueryEngineModule`)

*   **Responsibilities**:
    *   Takes parsed and validated search requests from the API layer.
    *   Constructs complex queries to be executed against the Search Engine Core (e.g., Elasticsearch DSL queries).
    *   Applies business rules, boosts, filtering logic, and sorting parameters based on the input and configurations from Relevancy Management.
    *   Handles pagination of results.
    *   May interact with a caching layer for frequently queried terms or filter combinations.
*   **Key Components**:
    *   `QueryBuilderService`: Translates API search parameters into search engine-specific queries.
    *   `FacetBuilderService`: Constructs aggregations for faceted search.
    *   `SortBuilderService`: Applies sorting logic.
    *   `RelevanceService`: (Works with E.2) Applies relevance and ranking rules.
    *   `SearchService`: Orchestrates query execution against the Search Engine Core and formats results.

### 2.3. Indexing Engine & Data Synchronization (`IndexingModule`)

*   **Responsibilities**:
    *   Consumes events (e.g., `ProductCreated`, `PriceUpdated`, `InventoryChanged`) from other microservices via RabbitMQ (using `@ecommerce-platform/rabbitmq-event-utils`).
    *   Transforms and enriches incoming data into a denormalized document structure suitable for the search index.
    *   Performs Create, Update, and Delete operations on documents in the Search Engine Core.
    *   Manages index aliases for zero-downtime re-indexing.
    *   Handles bulk indexing operations and batch processing of updates.
    *   Implements retry mechanisms for indexing failures.
    *   Potentially handles periodic full or partial re-indexing from source systems if event-based updates are insufficient or for consistency checks.
*   **Key Components**:
    *   `RabbitMQEventConsumer` / `EventListenerService`: Listens to relevant topics and queues.
    *   `ProductIndexHandler`, `PriceIndexHandler`, etc.: Specific handlers for different event types that update the search index.
    *   `DocumentTransformerService`: Converts incoming data/events into search engine document format.
    *   `IndexManagerService`: Interacts with the Search Engine Core to manage indexes, mappings, and aliases.
    *   `BulkIndexerService`: Optimizes batch updates to the search engine.

### 2.4. Search Engine Core (External Technology)

*   **Responsibilities**: This is the underlying search technology itself.
    *   Stores and manages the search indexes (collections of documents).
    *   Provides powerful query capabilities, text analysis (tokenization, stemming, etc.), and aggregation features.
    *   Handles sharding, replication, and clustering for scalability and fault tolerance.
*   **Technology Choice**: **OpenSearch** or **Elasticsearch** are common choices. This will be formally decided by an ADR (e.g., `ADR-00X-Search-Engine-Selection.md`).
*   **Interaction**: The Search Service application communicates with this cluster via its client libraries (e.g., OpenSearch/Elasticsearch NestJS client).

### 2.5. Configuration & Relevancy Management (`SearchConfigModule`)

*   **Responsibilities**:
    *   Manages search configurations such as:
        *   Index mappings and settings (analyzers, tokenizers).
        *   Field weightings for relevance scoring.
        *   Synonym lists, stop words.
        *   Business rules for boosting or burying certain products.
        *   Configuration for A/B testing different search settings.
    *   Provides an interface (API or admin UI, TBD) for search administrators to tune relevance and manage configurations.
*   **Key Components**:
    *   `ConfigService` (from `@ecommerce-platform/nestjs-core-utils` extended for search-specific configs).
    *   `SynonymManagerService`, `RelevanceRuleService`.
    *   Potentially integrates with a feature flagging system for A/B testing.

### 2.6. Shared Utilities & Cross-Cutting Concerns

*   **`@ecommerce-platform/nestjs-core-utils`**: For logging, configuration, error handling, health checks.
*   **`@ecommerce-platform/rabbitmq-event-utils`**: For consuming events for indexing.
*   **Authentication/Authorization**: If an admin API for configuration is exposed, it would be secured.
*   **Caching**: A caching layer (e.g., Redis) might be used for: 
        *   Frequently accessed search results (for popular queries).
        *   Facet counts.
        *   Autosuggestion results.

## 3. Key Workflows

*   **Indexing Workflow**: Event Consumed -> Data Transformed -> Document Indexed/Updated in Search Engine.
*   **Search Query Workflow**: API Request -> Query Parsed & Built -> Query Executed on Search Engine -> Results Formatted & Returned.
*   **Suggestion Workflow**: API Request -> Suggestion Query Built -> Query Executed -> Suggestions Returned.
