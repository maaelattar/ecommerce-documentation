# Search Service - Published Event Schemas (If Any)

## 1. Overview

The Search Service primarily functions as an event *consumer*, reacting to changes in other microservices to keep its indexes up-to-date. It is not typically a significant *producer* of domain events that other core business services would consume for their primary workflows.

However, the Search Service might publish a limited set of events related to its own operational status, critical errors, or significant lifecycle changes (like a major index rebuild). These events would primarily be consumed by monitoring, alerting, or administrative systems.

If any events are published, they will adhere to the `StandardMessage<T>` envelope from `@ecommerce-platform/rabbitmq-event-utils` and be published via the Transactional Outbox Pattern.

## 2. Potential Published Event Payloads

Below are examples of payloads for events the Search Service *might* publish. The actual need for these events will be evaluated based on operational requirements.

### 2.1. `SearchIndexBuildStatusChangedEvent`

*   **`messageType`**: `SearchIndexBuildStatusChanged`
*   **Description**: Published to indicate the status of a significant index build or rebuild operation.

```typescript
// Payload for StandardMessage<SearchIndexBuildStatusChangedPayloadV1>
// where version would be "1.0"
export interface SearchIndexBuildStatusChangedPayloadV1 {
  indexName: string;               // e.g., "products", "products_v2"
  operationId: string;             // Unique ID for this build operation
  status: "STARTED" | "IN_PROGRESS" | "COMPLETED" | "FAILED" | "CANCELLED";
  timestamp: string;               // ISO-8601 UTC
  details?: string;               // e.g., error message if FAILED, number of docs processed
  completionPercentage?: number;  // For IN_PROGRESS status (0-100)
  triggeredBy?: string;           // e.g., "admin_api", "scheduled_task"
}
```

### 2.2. `SearchRelevanceConfigUpdatedEvent`

*   **`messageType`**: `SearchRelevanceConfigUpdated`
*   **Description**: Published when a search relevance configuration (e.g., synonym list, boosting rule, field weight) is updated. This could be used by other Search Service instances to refresh their cache or for auditing.

```typescript
// Payload for StandardMessage<SearchRelevanceConfigUpdatedPayloadV1>
// where version would be "1.0"
export interface SearchRelevanceConfigUpdatedPayloadV1 {
  configType: "SYNONYMS" | "BOOSTING_RULES" | "FIELD_WEIGHTS" | "STOP_WORDS" | "ANALYZER_SETTINGS";
  configNameOrId: string;        // Identifier for the specific configuration item
  action: "CREATED" | "UPDATED" | "DELETED";
  timestamp: string;             // ISO-8601 UTC
  updatedBy?: string;           // User or system that made the change
  details?: Record<string, any>; // Optional: summary of the changes or new/old values
}
```

### 2.3. `CriticalIndexingFailureAlertEvent`

*   **`messageType`**: `CriticalIndexingFailureAlert`
*   **Description**: Published when a critical, persistent failure occurs in the event consumption or indexing pipeline that significantly impacts data freshness or availability in search. This event would likely be consumed by an alerting system.

```typescript
// Payload for StandardMessage<CriticalIndexingFailureAlertPayloadV1>
// where version would be "1.0"
export interface CriticalIndexingFailureAlertPayloadV1 {
  failureType: "EVENT_CONSUMPTION_ERROR" | "INDEX_WRITE_ERROR" | "DATA_TRANSFORMATION_ERROR";
  timestamp: string;                 // ISO-8601 UTC
  sourceEventIds?: string[];        // Optional: IDs of messages/events that failed processing
  indexName?: string;               // Optional: Target index affected
  errorMessage: string;
  errorDetails?: string;            // Optional: Stack trace or more context
  severity: "CRITICAL" | "HIGH";
}
```

## 3. Publishing Mechanism

If these events are implemented:

*   **Exchange**: A dedicated RabbitMQ exchange, e.g., `search.ops.events` (topic exchange).
*   **Routing Keys**: Based on `messageType`, e.g., `search.ops.SearchIndexBuildStatusChanged`, `search.ops.CriticalIndexingFailureAlert`.
*   **Outbox Pattern**: The Search Service would use its own outbox table (`search_event_outbox`) and an `OutboxProcessorService` (similar to other services) to ensure reliable publishing via `@ecommerce-platform/rabbitmq-event-utils`.

## 4. Consumers

Potential consumers for these operational events:

*   **Monitoring & Alerting System**: To trigger alerts for failures or track progress of index builds.
*   **Admin Portal/Dashboard**: To display status information.
*   **Other Search Service Instances**: For cache invalidation or configuration synchronization in a distributed setup (though other mechanisms like a shared config store might be preferred for some config types).
*   **Audit Logging Service**.

These events are not typically consumed by other core e-commerce domain services for their primary business logic.
