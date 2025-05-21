# Search Service - Event Handling Overview

## 1. Introduction

Event handling is fundamental to the Search Service. It relies on consuming events from other microservices to keep its search indexes accurate and up-to-date in near real-time. This ensures that changes in product information, pricing, stock levels, etc., are quickly reflected in search results.

The Search Service itself typically *does not publish* many events, as its primary role is to provide query capabilities. However, it might publish events related to its own operational status or critical indexing issues if necessary for monitoring or alerting other systems.

## 2. Event Consumption

### 2.1. Mechanism
*   **Message Broker**: The Search Service listens for events on **RabbitMQ** (via Amazon MQ).
*   **Shared Library**: It utilizes the `@ecommerce-platform/rabbitmq-event-utils` shared library for:
    *   Connecting to RabbitMQ.
    *   Defining consumer groups and queue bindings.
    *   Deserializing messages from the `StandardMessage<T>` envelope.
*   **Queues**: Dedicated queues will be bound to relevant exchanges and routing keys from services whose data needs to be indexed. Examples:
    *   `search.product.events` (consuming from `product.events` exchange)
    *   `search.price.events` (consuming from `price.events` exchange)
    *   `search.inventory.events` (consuming from `inventory.events` exchange)
    *   `search.review.events` (consuming from `review.events` exchange, if applicable)
*   **Idempotency**: Event handlers must be idempotent (e.g., by checking `messageId` or using optimistic locking on search documents if updates are versioned).
*   **Error Handling**: Robust error handling, retries for transient errors, and DLQs for persistent issues.

### 2.2. Purpose
*   **Index Updates**: The primary purpose of consuming events is to update the search index (e.g., OpenSearch/Elasticsearch documents).
*   **Data Denormalization**: Events provide the data that is denormalized into the search index documents.
*   **Near Real-Time Sync**: To ensure search results are as fresh as possible.

### 2.3. Key Consumed Event Categories (Examples)
*   **Product Lifecycle Events**: `ProductCreated`, `ProductUpdated`, `ProductDeleted`, `ProductPublished`, `ProductUnpublished` (from Product Service).
*   **Pricing Events**: `PriceUpdated` (from a Price Service).
*   **Inventory Events**: `StockLevelChanged`, `InventoryStatusUpdated` (from Inventory Service).
*   **Review Events**: `ReviewCreated`, `ReviewUpdated`, `ReviewDeleted`, `AverageRatingUpdated` (from a Review Service).
*   **Category/Brand Events**: `CategoryCreated/Updated/Deleted`, `BrandCreated/Updated/Deleted` (if these entities are managed separately and impact search).

Details of specific consumed events and their impact on the search index are in `01-consumed-event-schemas.md`.

## 3. Event Publishing (If Applicable)

While the Search Service is mainly a consumer, it might publish events in specific scenarios:

### 3.1. Potential Published Events
*   **`SearchIndexBuildStatusEvent`**: Published during major re-indexing operations (e.g., `STARTED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`). Useful for operational monitoring.
*   **`SearchRelevanceConfigUpdatedEvent`**: If relevance configurations (e.g., field weights, synonym lists) are updated via an admin interface within the Search Service, it might publish an event to notify other instances or for audit purposes.
*   **`CriticalIndexingFailureEvent`**: If a significant, persistent failure occurs in the indexing pipeline that might impact data freshness or accuracy for a large set of documents.

### 3.2. Mechanism
*   If publishing events, the Search Service would also use the `@ecommerce-platform/rabbitmq-event-utils` library and the Transactional Outbox Pattern to ensure reliable publishing.
*   Events would be formatted using the `StandardMessage<T>` envelope.
*   Published to a dedicated exchange, e.g., `search.ops.events`.

Details of any published event schemas are in `02-published-event-schemas.md`.

## 4. Event Processing Workflow (Consumption for Indexing)

1.  **Event Reception**: `RabbitMQEventConsumer` receives a `StandardMessage<T>`.
2.  **Deserialization & Validation**: Message is deserialized. Payload schema might be validated.
3.  **Idempotency Check**: Ensure the event hasn't been processed before.
4.  **Data Transformation**: The `IndexingModule` (e.g., `ProductIndexHandler`) transforms the event payload into the required fields for the search document.
    *   This may involve fetching minimal additional data if the event is not fully self-contained (though this is less desirable).
5.  **Index Operation**: The transformed data is used to create, update, or delete a document in the Search Engine Core (e.g., OpenSearch/Elasticsearch) via its client library.
    *   Partial updates are preferred for efficiency.
    *   Bulk operations are used for batch event processing where appropriate.
6.  **Acknowledgement**: The event is acknowledged to RabbitMQ upon successful processing (or NACKed/sent to DLQ on failure).

## 5. Further Details

*   Specific consumed event schemas and their impact on the search index: See `01-consumed-event-schemas.md`.
*   Schema definitions for any events published by the Search Service: See `02-published-event-schemas.md`.
