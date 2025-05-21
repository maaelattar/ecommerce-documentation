# Event Publishing Overview for Notification Service

## 1. Introduction

The Notification Service is responsible for managing and dispatching various types of notifications to users and potentially other systems (e.g., email, SMS, push notifications, webhook callbacks).

While the primary role of the Notification Service is to *consume* events from other services to trigger notifications, it may also *publish* events related to its own operations, such as:
*   Notification dispatch status (e.g., `NotificationSentEvent`, `NotificationFailedEvent`).
*   User communication preferences changes (if managed centrally here and other services need to know).
*   Template rendering failures or successes if these are auditable events.

This document outlines the strategy and mechanisms for publishing these domain events if and when the Notification Service acts as a producer.

## 2. Event Publishing Architecture

The Notification Service will use **RabbitMQ** (via Amazon MQ) as its message broker, leveraging the `@ecommerce-platform/rabbitmq-event-utils` shared library for standardized message formats (`StandardMessage<T>`) and producer utilities.

```mermaid
graph TD
    A[Notification Service Logic] -- Generates event --> B(Event Object: StandardMessage<T>)
    B -- Uses RabbitMQProducerService --> C{RabbitMQ Exchange (e.g., notification.events)}
    C -- Routing Key --> D1[Queue for Audit Service]
    C -- Routing Key --> D2[Queue for Analytics Service]
    C -- Routing Key --> D3[Queue for Other Interested Consumers]
```

## 3. Event Publishing Process

If the Notification Service publishes events, it will follow the Transactional Outbox Pattern:
1.  **Event Creation**: An internal operation triggers an event payload (e.g., `NotificationSentPayload`).
2.  **Message Formulation**: The payload is wrapped in `StandardMessage<T>`.
3.  **Transactional Outbox**: The `StandardMessage<T>` components are saved to an outbox table within the same database transaction as any related state change in the Notification Service.
4.  **Publishing to RabbitMQ**: An `OutboxProcessorService` (similar to one defined for other services) will poll the outbox and use `RabbitMQProducerService` to publish the message.

## 4. Event Schema Management

*   **Standard Envelope**: `StandardMessage<T>` from `@ecommerce-platform/rabbitmq-event-utils`.
*   **Payload Schema Definition**: Specific payload schemas (e.g., `NotificationSentPayload`) will be defined in `01-event-schema-definitions.md`.
*   **Schema Versioning**: The `version` field in `StandardMessage<T>` will denote the payload schema version.

## 5. Key Event Types and Exchange Strategy (Examples)

*   **Primary Exchange**: `notification.events` (Topic Exchange)
*   **Routing Key Convention**: `notification.<MessageType>.<entityId>` (e.g., `notification.NotificationSent.USER123`, `notification.NotificationFailed.TEMPLATE_XYZ`)
*   **Example Event Message Types**:
    *   `NotificationSentEvent`: Confirms a notification was successfully dispatched.
    *   `NotificationFailedEvent`: Indicates a notification failed to dispatch after retries.
    *   `NotificationDeliveryStatusEvent`: Reports final delivery status from a provider (e.g., email delivered, bounced, SMS undelivered).
    *   `CommunicationPreferenceChangedEvent`: If user preferences are updated within this service and need to be broadcast.

## 6. Further Details

*   Specific event payload definitions: See `01-event-schema-definitions.md`.
*   Implementation details for event publishers: See `02-event-publisher-implementation.md`.
