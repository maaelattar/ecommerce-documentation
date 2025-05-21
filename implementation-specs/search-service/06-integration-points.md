# Search Service - Integration Points

## 1. Overview

The Search Service integrates with multiple components: it consumes data from various upstream services, exposes APIs for client applications, and relies on an underlying search engine technology.

## 2. Inbound Integrations (Data Sources & Triggers)

### 2.1. Event Consumption from Internal Microservices
*   **Mechanism**: Asynchronous via RabbitMQ (using `@ecommerce-platform/rabbitmq-event-utils`).
*   **Purpose**: To receive domain events that signal changes in data that needs to be indexed (e.g., product updates, price changes, stock level adjustments).
*   **Key Services Integrated With (Sources for Index Data)**:
    *   **Product Service**: Primary source for core product information (name, description, SKU, categories, brands, attributes, images).
    *   **Price Service (or Product Service if prices are managed there)**: Source for current prices, original prices, currency, sale status.
    *   **Inventory Service**: Source for stock status, available quantity.
    *   **Review Service (if applicable)**: Source for average ratings, review counts.
    *   **(Future) Content Management Service**: If indexing articles, FAQs, etc.
*   **Data Contract**: `StandardMessage<T>` envelope. Payloads are defined by the publishing services.

### 2.2. API Calls from Administrative Tools (Internal)
*   **Mechanism**: Synchronous HTTPS/REST calls to internal admin API endpoints exposed by the Search Service (secured by `@ecommerce-platform/auth-client-utils`).
*   **Purpose**: 
    *   Triggering manual re-indexing operations.
    *   Managing search configurations (synonyms, boosting rules, field weights).
    *   Retrieving index status and statistics.
*   **Key Integrators**: Admin Portal, internal CLI tools.

## 3. Outbound Integrations (Serving Search & Suggestions)

### 3.1. API Exposure to Client Applications
*   **Mechanism**: Public-facing HTTPS/REST APIs.
*   **Purpose**: To provide search functionality (keyword search, filtering, sorting, faceting) and typeahead suggestions to end-user clients.
*   **Key Consumers**: 
    *   Web Frontend Application (e-commerce website).
    *   Mobile Applications (iOS, Android).
    *   (Potentially) Third-party integrators or partner applications if allowed.
*   **Data Contract**: Defined by the Search Service's OpenAPI specification (see `04-api-endpoints.md`).

### 3.2. Interaction with Search Engine Core
*   **Mechanism**: Via the search engine's client library (e.g., OpenSearch/Elasticsearch NestJS client or official Node.js client).
*   **Purpose**: 
    *   **Indexing**: Sending data to be indexed (create, update, delete documents).
    *   **Querying**: Executing search queries, aggregations (for facets), and suggestion queries.
    *   **Management**: Managing index settings, mappings, aliases.
*   **Key Interaction Points**: The `IndexingModule` and `QueryEngineModule` within the Search Service heavily interact with the search engine.

## 4. Internal Shared Libraries

*   **`@ecommerce-platform/rabbitmq-event-utils`**: For consuming events for indexing, and potentially publishing operational events.
*   **`@ecommerce-platform/nestjs-core-utils`**: For logging, configuration, common error handling, health checks.
*   **`@ecommerce-platform/auth-client-utils`**: For securing any exposed administrative API endpoints.
*   **`@ecommerce-platform/testing-utils`**: For common testing utilities.

## 5. Integration Diagram (Conceptual)

```mermaid
graph LR
    subgraph ECommercePlatform
        ProductService[Product Service]
        PriceService[Price Service]
        InventoryService[Inventory Service]
        ReviewService[Review Service]
        AdminTools[Admin Portal/Tools]
        ClientApps[Client Apps (Web/Mobile)]
        SS[Search Service]
    end

    subgraph Infrastructure
        RMQ[(RabbitMQ)]
        SearchCluster[(Search Engine: OpenSearch/ES)]
    end

    ProductService -- Publishes Events --> RMQ
    PriceService -- Publishes Events --> RMQ
    InventoryService -- Publishes Events --> RMQ
    ReviewService -- Publishes Events --> RMQ

    RMQ -- Consumes Events for Indexing --> SS

    SS -- Indexing/Querying --> SearchCluster
    
    ClientApps -- Search/Suggest API Calls --> SS
    AdminTools -- Admin API Calls --> SS

    SS -- (If Publishing Ops Events) --> RMQ_Ops[(RabbitMQ for Ops)]
    RMQ_Ops --> Monitoring[Monitoring/Alerting System]
```

This diagram shows the Search Service consuming events to build its index in the Search Engine Cluster, and then serving search queries to client applications. Administrative tools can also interact with it for management tasks.
