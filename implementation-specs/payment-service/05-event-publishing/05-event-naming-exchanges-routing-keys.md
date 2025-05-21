# 05: Event Naming, Exchanges, and Routing Key Conventions

Consistent naming conventions for events, exchanges, and routing keys are crucial for a maintainable and understandable event-driven architecture using RabbitMQ. This document outlines the conventions adopted by the Payment Service.

## Event Naming

Events are named using PascalCase and should clearly describe the business occurrence. They typically include the entity and the past-tense verb of the action performed. A version suffix can be included if major breaking changes to the payload are anticipated, though versioning is primarily handled by the `eventVersion` field in the `StandardMessageEnvelope`.

*   **Format:** `EntityActionOccurredEvent` (e.g., `PaymentSucceededEvent`, `RefundInitiatedEvent`)
*   **Clarity:** Names should be self-explanatory.
*   **Domain-Specific:** Reflect terms used in the payments domain.

The `eventType` field within the `StandardMessageEnvelope` will often mirror this name or be a string representation (e.g., "PaymentSucceeded", "RefundInitiated").

## RabbitMQ Exchanges

*   **Primary Exchange:** The Payment Service will primarily publish its events to a single, dedicated **topic exchange**.
    *   **Name:** `payment.events`
    *   **Type:** `topic`
    *   **Rationale:** A topic exchange provides the most flexibility for consumers to subscribe to specific patterns of events using wildcard bindings for routing keys.

*   **Dead Letter Exchange (DLX):**
    *   The `@ecommerce-platform/rabbitmq-event-utils` library's `RabbitMQProducerModule` will be configured to use a DLX for messages that cannot be routed or are rejected after processing attempts by consumers (if consumers are also using a similar setup with nacks).
    *   **Naming Convention (Example):** `payment.events.dlx`
    *   **Purpose:** To capture problematic messages for later inspection and potential reprocessing or error analysis, preventing message loss.

## Routing Keys

Routing keys are dot-separated strings and are fundamental to how messages are routed from a topic exchange to bound queues. They provide a hierarchical way to categorize events.

*   **Format:** `entity.action.version_attributes`
    *   `entity`: The primary domain entity (e.g., `payment`, `refund`, `paymentmethod`).
    *   `action`: The specific action performed on the entity (e.g., `initiated`, `succeeded`, `failed`, `added`, `updated`, `removed`).
    *   `version`: (Optional but recommended) A version number for the event type/schema, e.g., `v1`, `v2`. This allows for evolving event schemas without breaking existing consumers immediately. It aligns with the `eventVersion` in the `StandardMessageEnvelope`.
    *   `attributes`: (Optional) Further qualifying attributes if needed for finer-grained routing, though this should be used sparingly to avoid overly complex routing keys.*   **Examples:**
    *   `payment.initiated.v1`
    *   `payment.succeeded.v1`
    *   `payment.failed.v1`
    *   `refund.initiated.v1`
    *   `refund.processed.v1` (could also be `refund.succeeded.v1` if "processed" implies success)
    *   `paymentmethod.added.v1`
    *   `paymentmethod.updated.v1`

## Binding Keys (for Consumers)

Consumers will bind their queues to the `payment.events` topic exchange using binding keys that can include wildcards:

*   `*` (asterisk) can substitute for exactly one word.
*   `#` (hash) can substitute for zero or more words.

*   **Examples of Consumer Binding Keys:**
    *   `payment.*.v1`: Consume all payment-related V1 events (initiated, succeeded, failed).
    *   `*.succeeded.v1`: Consume all V1 "succeeded" events across any entity published by Payment Service.
    *   `payment.failed.#`: Consume all versions of payment failed events.
    *   `paymentmethod.#`: Consume all events related to payment methods, regardless of action or version.

Adherence to these conventions will ensure that:
*   Events are easy to identify and understand.
*   Message routing is flexible and robust.
*   Consumers can subscribe to precisely the events they need.
*   The system remains maintainable as it evolves.