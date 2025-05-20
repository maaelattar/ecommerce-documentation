# Inventory Service: Event Publishing Strategy

## 1. Introduction

The Inventory Service plays a crucial role in the e-commerce platform by managing real-time stock levels. Event publishing is a core aspect of its design, enabling it to communicate significant changes to other microservices in a decoupled manner. This allows for a reactive and resilient architecture, supporting choreography patterns where downstream services can subscribe to inventory events and trigger their own processes (e.g., updating product availability in the Product Service, notifying customers, or initiating reordering workflows).

This strategy aligns with key architectural decisions:
-   **ADR-002 (Event-Driven Architecture)**: Emphasizes the use of asynchronous events for inter-service communication.
-   **ADR-018 (Message Broker Strategy)**: Specifies the choice of message broker technology (RabbitMQ via Amazon MQ) and general patterns for its usage.

The primary purpose of event publishing in the Inventory Service is to:
-   Notify other services (e.g., Product Service, Order Service, Notification Service) of changes in stock levels.
-   Signal successful or failed inventory reservations.
-   Communicate changes in inventory status (e.g., to `OUT_OF_STOCK`).
-   Enable data synchronization and consistency across the platform without tight coupling.

## 2. Events to be Published

The Inventory Service will publish the following domain events. Each event will carry a `correlationId` to trace the event back to the originating request or process.

### 2.1. `StockLevelChangedEvent`

*   **Description**: Published whenever the physical stock quantity of a product variant changes due to actions like new stock arrival (purchase), sale completion, customer returns, or manual adjustments. This event is critical for services tracking overall product availability.
*   **Trigger**: Successful completion of an operation that modifies the `quantity` field in the `Inventory` entity.
*   **Payload**:
    *   `productVariantId`: `string` (UUID) - Identifier for the specific product variant.
    *   `newQuantity`: `number` (integer) - The quantity after the change.
    *   `oldQuantity`: `number` (integer) - The quantity before the change.
    *   `quantityChanged`: `number` (integer) - The amount by which the quantity changed (positive for increase, negative for decrease).
    *   `changeType`: `string` (enum: `PURCHASE`, `SALE`, `RETURN`, `ADJUSTMENT`) - The reason for the stock level change.
    *   `timestamp`: `string` (ISO 8601 datetime) - Time of the event.
    *   `correlationId`: `string` (UUID) - Identifier for tracing the originating request.

### 2.2. `InventoryReservedEvent`

*   **Description**: Published when stock is successfully reserved for an order or other purposes (e.g., cart). This informs services that the reserved quantity is no longer available for other transactions.
*   **Trigger**: Successful completion of a stock reservation operation by the `ReservationManagerService`.
*   **Payload**:
    *   `productVariantId`: `string` (UUID) - Identifier for the product variant.
    *   `quantityReserved`: `number` (integer) - The quantity that was successfully reserved.
    *   `availableQuantityAfterReservation`: `number` (integer) - The available stock after this reservation.
    *   `orderId`: `string` (UUID) - Identifier for the order associated with this reservation.
    *   `userId`: `string` (UUID, optional) - Identifier for the user who initiated the action.
    *   `reservationId`: `string` (UUID, optional) - A unique ID for this specific reservation action.
    *   `timestamp`: `string` (ISO 8601 datetime) - Time of the event.
    *   `correlationId`: `string` (UUID) - Identifier for tracing the originating request.

### 2.3. `InventoryReservationFailedEvent`

*   **Description**: Published when an attempt to reserve stock fails, typically due to insufficient available quantity. This allows other services (e.g., Order Service) to handle the failure gracefully.
*   **Trigger**: Failure of a stock reservation operation in the `ReservationManagerService`.
*   **Payload**:
    *   `productVariantId`: `string` (UUID) - Identifier for the product variant.
    *   `quantityAttempted`: `number` (integer) - The quantity that was attempted to be reserved.
    *   `reasonForFailure`: `string` (e.g., "INSUFFICIENT_STOCK", "PRODUCT_NOT_FOUND") - Code or message indicating why reservation failed.
    *   `orderId`: `string` (UUID) - Identifier for the order associated with this reservation attempt.
    *   `userId`: `string` (UUID, optional) - Identifier for the user who initiated the action.
    *   `timestamp`: `string` (ISO 8601 datetime) - Time of the event.
    *   `correlationId`: `string` (UUID) - Identifier for tracing the originating request.

### 2.4. `InventoryReleasedEvent`

*   **Description**: Published when previously reserved stock is released back into the available pool. This can happen due to order cancellation, reservation timeout, or when an order is completed and the reservation is cleared (if not directly converted to a sale).
*   **Trigger**: Successful completion of a stock release operation by the `ReservationManagerService`.
*   **Payload**:
    *   `productVariantId`: `string` (UUID) - Identifier for the product variant.
    *   `quantityReleased`: `number` (integer) - The quantity of stock that was released.
    *   `availableQuantityAfterRelease`: `number` (integer) - The available stock after this release.
    *   `orderId`: `string` (UUID) - Identifier for the order associated with this release.
    *   `userId`: `string` (UUID, optional) - Identifier for the user who initiated the action.
    *   `reservationId`: `string` (UUID, optional) - The ID of the reservation that was released.
    *   `reasonForRelease`: `string` (enum: `ORDER_CANCELLED`, `RESERVATION_EXPIRED`, `ORDER_COMPLETED_ADJUSTMENT`)
    *   `timestamp`: `string` (ISO 8601 datetime) - Time of the event.
    *   `correlationId`: `string` (UUID) - Identifier for tracing the originating request.

### 2.5. `StockStatusChangedEvent`

*   **Description**: Published when the overall status of a product variant's inventory changes (e.g., from `IN_STOCK` to `LOW_STOCK`, or `LOW_STOCK` to `OUT_OF_STOCK`). This is useful for triggering alerts or updating display information.
*   **Trigger**: Change in the `status` field of the `Inventory` entity.
*   **Payload**:
    *   `productVariantId`: `string` (UUID) - Identifier for the product variant.
    *   `newStatus`: `string` (enum: `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `DISCONTINUED`) - The new status.
    *   `oldStatus`: `string` (enum) - The previous status.
    *   `currentQuantity`: `number` (integer) - The current physical quantity at the time of status change.
    *   `timestamp`: `string` (ISO 8601 datetime) - Time of the event.
    *   `correlationId`: `string` (UUID) - Identifier for tracing the originating request.

### 2.6. `LowStockThresholdReachedEvent` (Optional - To be confirmed if specifically needed beyond `StockStatusChangedEvent`)

*   **Description**: A more specific event that could be published when a product variant's quantity drops below its defined low stock threshold. This might be redundant if `StockStatusChangedEvent` (for `LOW_STOCK`) is sufficient.
*   **Trigger**: `quantity` <= `lowStockThreshold` and previous quantity was > `lowStockThreshold`.
*   **Payload**:
    *   `productVariantId`: `string` (UUID)
    *   `currentQuantity`: `number` (integer)
    *   `lowStockThreshold`: `number` (integer)
    *   `timestamp`: `string` (ISO 8601 datetime)
    *   `correlationId`: `string` (UUID)

## 3. Event Structure (General)

All events published by the Inventory Service will adhere to a common envelope structure to ensure consistency and provide essential metadata for consumers.

```json
{
  "eventId": "uuid", // Unique identifier for this specific event instance
  "eventType": "string", // e.g., "StockLevelChangedEvent", "InventoryReservedEvent"
  "eventVersion": "string", // e.g., "1.0", "1.1" - Version of the event payload schema
  "timestamp": "string", // ISO 8601 datetime - When the event was generated
  "sourceService": "InventoryService", // Identifies the origin of the event
  "correlationId": "uuid", // ID to correlate with the originating request or process
  "data": {
    // Event-specific payload as defined in Section 2
    // e.g., for StockLevelChangedEvent:
    // "productVariantId": "uuid",
    // "newQuantity": 100,
    // ...
  }
}
```

**Idempotency Considerations**:
Consumers should be designed to handle events idempotently. This means processing the same event multiple times should not result in incorrect data or unintended side effects. Strategies include:
-   Checking `eventId` to detect and ignore duplicate events.
-   Using optimistic locking or versioning if updating shared resources based on events.
-   Designing business logic to be naturally idempotent (e.g., setting a status is idempotent).

## 4. Publishing Mechanism

*   **Message Broker**: As per **ADR-018 (Message Broker Strategy)**, the Inventory Service will use **RabbitMQ (via Amazon MQ)** for publishing events.
*   **Exchange**: Events will be published to a topic exchange named `inventory.events`. This allows for flexible routing to different queues based on routing keys.
*   **Routing Keys**: Events will be published with routing keys that allow consumers to subscribe to specific types of events or events related to specific entities. A hierarchical dot-notation will be used:
    *   `inventory.stock.changed`: For `StockLevelChangedEvent`.
    *   `inventory.stock.status.changed`: For `StockStatusChangedEvent`.
    *   `inventory.reservation.created`: For `InventoryReservedEvent`.
    *   `inventory.reservation.failed`: For `InventoryReservationFailedEvent`.
    *   `inventory.reservation.released`: For `InventoryReleasedEvent`.
    *   (If implemented) `inventory.stock.low_threshold_reached`: For `LowStockThresholdReachedEvent`.
    *   More general keys like `inventory.stock.*` or `inventory.reservation.*` can also be used for broader subscriptions.

*   **Publishing from Service**:
    Within the NestJS application, a dedicated `EventPublisherService` (or similar module) will be responsible for constructing and sending events to RabbitMQ. This service will be injected into the core logic services (`InventoryManagerService`, `ReservationManagerService`).
    ```typescript
    // Example in InventoryManagerService
    // ... after successfully updating stock ...
    // await this.eventPublisherService.publish(stockLevelChangedEvent);
    ```
    This centralizes event publishing logic, making it easier to manage and ensure consistency.

## 5. Error Handling & Reliability

Ensuring that events are published reliably is critical. The Inventory Service will implement the following strategies:

*   **Transactional Outbox Pattern**: This is the preferred approach for achieving strong reliability.
    1.  When a business operation (e.g., updating stock) is performed, the event to be published is saved to a dedicated "outbox" table within the same database transaction as the business data.
    2.  A separate process (or a scheduled job) polls the outbox table, picks up unpublished events, and sends them to RabbitMQ.
    3.  Once an event is successfully published, it's marked as published or deleted from the outbox.
    This ensures that an event is generated if and only if the business transaction commits, preventing data loss or phantom events if the service crashes before publishing.
*   **Retry Mechanisms**: The event publishing mechanism (e.g., the outbox poller or the direct publisher if not using outbox initially) should implement retries with exponential backoff for transient failures when communicating with RabbitMQ.
*   **Dead Letter Queues (DLQs)**: Configure DLQs in RabbitMQ to capture events that cannot be delivered or processed after multiple retries. This allows for later inspection and manual intervention if necessary.
*   **Monitoring and Alerting**: Implement monitoring on the event publishing flow, including the size of the outbox (if used) and error rates for publishing to RabbitMQ. Alerts should be triggered for persistent failures.

By implementing these strategies, the Inventory Service aims to provide a robust and reliable event publishing system that other services can depend on.
