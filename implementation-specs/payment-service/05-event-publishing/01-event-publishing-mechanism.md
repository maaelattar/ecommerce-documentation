# 01: Event Publishing Mechanism in Payment Service

## Core Mechanism: RabbitMQ Producer via Shared Library

The Payment Service publishes events using a **RabbitMQ producer**. This producer is part of the `@ecommerce-platform/rabbitmq-event-utils` shared library, which provides a standardized and simplified interface for interacting with RabbitMQ.

### Key Components from `@ecommerce-platform/rabbitmq-event-utils`:

1.  **`RabbitMQProducerModule`:**
    *   **Purpose:** Provides the core service (`RabbitMQProducerService`) for publishing messages.
    *   **Configuration:** Initialized with RabbitMQ connection details (host, port, username, password, vhost) and default exchange information. This configuration is typically loaded via the `@ecommerce-platform/nestjs-core-utils` `SharedConfigModule`.
    *   **Error Handling:** Includes built-in retry mechanisms and dead-letter exchange (DLX) configuration for handling publishing failures.

2.  **`RabbitMQProducerService`:**
    *   **`publish<T>(exchange: string, routingKey: string, messagePayload: T, options?: PublishOptions): Promise<void>`:**
        *   The primary method used by the Payment Service to send events.
        *   `exchange`: The target RabbitMQ exchange (e.g., `payment.events`).
        *   `routingKey`: The routing key for the message (e.g., `payment.created.v1`).
        *   `messagePayload`: The actual event data (e.g., `PaymentCreatedEventPayload`).
        *   `options`: Optional parameters like `correlationId`, `messageId`, `timestamp`, custom headers, and persistence settings. The `StandardMessageEnvelope` from the shared library is often used here or incorporated into the `messagePayload` itself.
    *   **Resilience:** Handles connection management, channel pooling, and acknowledgments from RabbitMQ to ensure reliable message delivery.

3.  **`StandardMessageEnvelope`:**
    *   **Purpose:** Defines a consistent structure for all messages. This is crucial for consumers to parse and process events uniformly.
    *   **Fields (example):**
        *   `eventId`: Unique identifier for the event instance.
        *   `eventType`: The type of event (e.g., "PaymentCreated", "RefundProcessed").
        *   `eventVersion`: Version of the event schema (e.g., "1.0").
        *   `timestamp`: ISO 8601 timestamp of when the event occurred.
        *   `sourceService`: Name of the publishing service (e.g., "payment-service").
        *   `correlationId`: ID to correlate related events or requests.
        *   `data`: The actual event-specific payload.## Publishing Flow within Payment Service:

1.  **Service Logic:** A core service component (e.g., `PaymentProcessingService`) performs a business operation (e.g., processes a payment).
2.  **Database Transaction:** The operation results in changes to the Payment Service's database (e.g., a new payment record is created or updated).
3.  **Outbox Pattern Implementation:**
    *   As part of the same database transaction, an "event record" is written to an `outbox` table. This record contains all necessary information to construct the actual event message (type, payload, destination exchange/routing key).
    *   This ensures atomicity: the event is only marked for publishing if the business transaction succeeds.
4.  **Event Assemblage:** The event record is transformed into the `StandardMessageEnvelope` format, including the specific event payload.
5.  **Publishing via `RabbitMQProducerService`:**
    *   A separate, dedicated process or a scheduled job (the "Relay" or "Publisher") polls the `outbox` table for new event records.
    *   For each new record, it uses the `RabbitMQProducerService.publish()` method to send the event to the designated RabbitMQ exchange with the appropriate routing key.
6.  **Confirmation and Cleanup:**
    *   Upon successful acknowledgment from RabbitMQ that the message has been durably queued, the relay process marks the event record in the `outbox` table as "published" or deletes it.
    *   If publishing fails (after retries handled by the `RabbitMQProducerService`), the event remains in the outbox for a subsequent attempt. DLX mechanisms are used for persistent failures requiring manual intervention.

## Exchange and Routing Key Strategy:

*   **Exchanges:** The Payment Service will typically publish events to a dedicated exchange, for example, `payment.events`. This will be a topic exchange to allow for flexible routing based on event types.
*   **Routing Keys:** Routing keys will follow a consistent pattern, typically including the entity, the action, and the version, e.g.:
    *   `payment.created.v1`
    *   `payment.succeeded.v1`
    *   `payment.failed.v1`
    *   `refund.initiated.v1`
    *   `refund.processed.v1`
    *   `paymentmethod.added.v1`

This structured approach ensures that event publishing is reliable, consistent, and easy for consumer services to integrate with, leveraging the robust capabilities of RabbitMQ and the standardized utilities from the shared library.