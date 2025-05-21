# 04: Event Publishing Mechanism

## 1. Overview

This document specifies the chosen event publishing mechanism and technology for the Product Service, in line with the platform's overall event-driven architecture strategy (see ADR-018 and TDAC/03-message-broker-selection.md).

## 2. Chosen Technology: RabbitMQ (Amazon MQ)

*   **Primary Technology**: RabbitMQ, specifically leveraging **Amazon MQ for RabbitMQ**.
*   **Rationale**:
    *   Provides reliable message delivery with acknowledgements and persistent messages.
    *   Offers flexible routing capabilities using exchanges and bindings, suitable for product catalog events.
    *   Mature and well-supported in the Node.js/NestJS ecosystem.
    *   Amazon MQ for RabbitMQ offers a managed service, reducing operational overhead.
    *   Aligns with the platform's decision (ADR-018) for a robust general-purpose message broker.
*   **Secondary/Specialized Option**: For scenarios requiring extremely high throughput or event stream processing capabilities beyond typical RabbitMQ use cases, Apache Kafka (via Amazon MSK) is the designated secondary option. The Product Service will primarily use RabbitMQ for its domain events.
*   **Shared Library**: The `@ecommerce-platform/rabbitmq-event-utils` shared library will be used to standardize RabbitMQ interactions, ensuring consistency in message production and envelope structure.

## 3. Configuration and Setup

### 3.1. Connection Details
*   **Connection URI**: Managed via `ConfigService` (e.g., `AMQP_URI`).
*   **Authentication**: Username/password credentials, securely managed and provided to the `RabbitMQProducerModule`.
*   **TLS**: Enforced for connections to Amazon MQ.

### 3.2. Exchanges and Routing Keys
*   **Primary Exchange Name**: `product.events` (configurable, e.g., via `PRODUCT_EVENTS_EXCHANGE` environment variable).
*   **Exchange Type**: `topic` (allows flexible, pattern-based routing).
*   **Routing Key Convention**: `product.<aggregate_lowercase>.<action_lowercase>.v[version_number]`
    *   Examples:
        *   `product.product.created.v1` (for `ProductCreatedEventV1`)
        *   `product.category.updated.v1` (for `CategoryUpdatedEventV1`)
        *   `product.price.effective.v1` (for `ProductPriceEffectiveEventV1`)
*   **Event Structure**: All events will use the `StandardMessage<T>` envelope from `@ecommerce-platform/rabbitmq-event-utils`.
*   **Declaration**: Exchanges and necessary durable queues (if any for specific direct consumers) are typically managed via IaC or declared idempotently by the service/library.

### 3.3. Message Format
*   **Serialization**: JSON, as handled by the `StandardMessage<T>` envelope and `RabbitMQProducerService`.
*   **Schema Management**: Versioning is handled via the `messageType` field (e.g., `ProductCreatedEventV1`). See `08-schema-management-versioning.md` in shared library documentation or service-level specifics if they deviate.

## 4. Reliability and Resilience

### 4.1. Message Persistence
*   Events intended for durable consumption will be published as **persistent** (`delivery_mode: 2`).
*   Consuming queues should be **durable**.

### 4.2. Delivery Guarantees
*   **Publisher Confirms**: The `RabbitMQProducerService` from the shared library will use publisher confirms to ensure messages are acknowledged by the broker, aiming for at-least-once delivery semantics.

### 4.3. Dead Letter Exchanges (DLX) / Error Handling
*   **Broker-Level DLX**: Can be configured on queues for messages that are unprocessable by consumers (e.g., after retries, or if a message is rejected without requeue).
*   **Publisher Error Handling**: The Product Service will handle errors from `RabbitMQProducerService.publish()` (e.g., persistent NACKs, timeouts before confirm). This may involve logging, alerting, and potentially using the Outbox pattern for critical events (see `07-idempotency-error-handling-publishing.md` or similar service-level docs).

### 4.4. Idempotent Consumers
*   Consumers must be designed to be idempotent, typically by tracking the `messageId` from the `StandardMessage<T>` envelope.

## 5. Monitoring and Alerting

*   **Key Metrics**: Monitor RabbitMQ metrics (message rates, queue depths, unacknowledged messages, connection status) via Amazon CloudWatch for Amazon MQ.
*   **Application Metrics**: The Product Service should monitor the success/failure rates of its event publishing operations.
*   **Alerting**: Set up alerts for critical issues (e.g., persistent publishing failures, deep queues, broker unavailability).

## 6. Security

*   **Encryption in Transit**: TLS is enforced by Amazon MQ.
*   **Encryption at Rest**: Handled by AWS for Amazon MQ broker storage.
*   **Access Control**: RabbitMQ permissions (username/password based) will control `write` access to the `product.events` exchange for the Product Service producer, and `read` access for consumers on their respective queues.

## 7. Integration

*   The Product Service will use the `RabbitMQProducerModule` and `RabbitMQProducerService` from the `@ecommerce-platform/rabbitmq-event-utils` library to publish events.
*   Configuration will be managed via `ConfigService` as shown in User/Payment service examples.

## 8. References

*   [Event Publishing Overview](./00-overview.md)
*   `@ecommerce-platform/rabbitmq-event-utils` (Shared Library Documentation)
*   `@ecommerce-platform/nestjs-core-utils` (Shared Library Documentation)
*   ADR-018: Message Broker Strategy
*   TDAC/03-message-broker-selection.md
