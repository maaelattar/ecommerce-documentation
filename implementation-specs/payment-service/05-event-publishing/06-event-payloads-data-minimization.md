# 06: Event Payloads and Data Minimization

The structure and content of event payloads are critical for effective and secure event-driven communication. The Payment Service adheres to principles of data minimization and uses a standardized envelope for all its events.

## Standard Message Envelope

All events published by the Payment Service MUST use the `StandardMessageEnvelope` provided by the `@ecommerce-platform/rabbitmq-event-utils` shared library. This envelope provides essential metadata for event tracking, routing, and processing.

*   **Key Fields in `StandardMessageEnvelope`:**
    *   `eventId`: (UUID) Unique identifier for this specific event instance.
    *   `eventType`: (String) Type of the event (e.g., "PaymentSucceeded", "RefundInitiated").
    *   `eventVersion`: (String) Version of the event's data schema (e.g., "1.0", "1.1").
    *   `timestamp`: (ISO 8601 String) Timestamp of when the event logically occurred.
    *   `sourceService`: (String) Identifier of the publishing service (i.e., "payment-service").
    *   `correlationId`: (UUID, Optional) ID to correlate this event with an originating request or other related events in a workflow.
    *   `data`: (Object) The actual payload specific to the event type.

## Data Minimization in the `data` Object

The `data` object within the `StandardMessageEnvelope` contains the information specific to the event that occurred. The core principle here is **data minimization**:

*   **Include Only What's Necessary:** Payloads should only contain data that consumers genuinely need to perform their functions based on the event. Avoid including large, complex objects or extraneous information.
*   **No Sensitive Raw Data:**
    *   Full credit card numbers (PANs), CVCs, full bank account numbers, or other highly sensitive payment credentials MUST NEVER be included in event payloads.
    *   If payment method identification is needed, use tokenized representations, last four digits, card brand, or other non-sensitive identifiers.
*   **Prefer IDs over Full Objects:** If an event relates to an entity managed by another service (e.g., an `Order` or `User`), the payload should typically include the `orderId` or `userId`, not the entire Order or User object. Consumers can then fetch further details from the authoritative service if needed, using these IDs. This reduces data duplication and keeps events lightweight.
*   **Context-Specific Information:** The `data` payload should be tailored to the specific event. For example:
    *   `PaymentSucceededEvent` might include `paymentId`, `orderId`, `amountPaid`, `currency`, and masked payment method details.
    *   `RefundFailedEvent` might include `refundId`, `orderId`, `amount`, `currency`, and `failureReason`.## Benefits of Data Minimization:

*   **Reduced Security Risk:** Less sensitive data in transit and at rest in message queues or consumer logs.
*   **Smaller Message Sizes:** Improves performance and reduces network/storage overhead.
*   **Lower Coupling:** Consumers are less coupled to the full internal data models of the Payment Service. Changes to non-essential fields within the Payment Service are less likely to break consumers.
*   **Improved Clarity:** Simpler payloads are easier for developers to understand and work with.
*   **GDPR and Compliance:** Helps in adhering to data privacy regulations by not broadcasting unnecessary personal data.

## Payload Design Process:

1.  **Identify Consumers:** For each event, determine which services will consume it.
2.  **Determine Consumer Needs:** Understand what information each consumer *absolutely requires* from the event to perform its task.
3.  **Design `data` Schema:** Define the fields for the `data` object based on these needs, always applying data minimization principles.
4.  **Versioning:** Use the `eventVersion` field in the envelope to manage changes to the payload schema over time. Semantic versioning (e.g., "1.0", "1.1", "2.0") is recommended.

By following these guidelines, the Payment Service will publish events that are secure, efficient, and provide clear, actionable information to consumers.