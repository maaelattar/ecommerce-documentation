# 01: Standard Message Envelope

## 1. Purpose

A standardized message envelope is crucial for consistency and interoperability when microservices communicate via RabbitMQ (specifically Amazon MQ for RabbitMQ). This envelope wraps the actual business payload, providing common metadata for tracing, versioning, routing, and processing of messages.

All messages published by services within the e-commerce platform should adhere to this standard envelope structure.

## 2. Envelope Structure

The message envelope will be a JSON object. The actual business data (payload) will be a property within this JSON object. AMQP message properties (like `correlation_id`, `reply_to`, `content_type`, `message_id`, `timestamp`, `type`, `app_id`) will also be utilized where appropriate and may overlap or complement the fields in the JSON envelope.

For clarity, we define fields within the JSON message body itself, which gives us full control over naming and structure. Standard AMQP properties will be set by the producer library for broker-level concerns.

**Proposed JSON Message Body Envelope:**

```typescript
interface StandardMessage<T> {
  /**
   * Unique identifier for this specific message instance.
   * Recommended: UUID v4.
   * Note: AMQP also has a `message_id` property; this can be the same or a separate app-level ID.
   */
  messageId: string;

  /**
   * Type or name of the message/event (e.g., "UserRegisteredEvent", "OrderCreatedEvent").
   * Should include a version suffix if the schema of the payload changes significantly (e.g., "OrderCreatedEvent.v1", "OrderCreatedEvent.v2").
   * Corresponds to AMQP `type` property conceptually.
   */
  messageType: string;

  /**
   * Version of the message envelope schema itself (e.g., "1.0"). 
   * This is distinct from the messageType version which refers to payload schema version.
   */
  envelopeVersion: string; // e.g., "1.0"

  /**
   * Timestamp of when the message was created by the source service.
   * ISO 8601 format (e.g., "2023-10-28T12:00:00.123Z").
   * Note: AMQP also has a `timestamp` property (seconds since epoch).
   */
  timestamp: string;

  /**
   * Name of the microservice that originally published this message.
   * e.g., "UserService", "OrderService".
   * Corresponds to AMQP `app_id` property.
   */
  sourceService: string;

  /**
   * Identifier used to correlate messages across multiple services, often originating from an initial API request.
   * Should be propagated from incoming requests or generated if not present.
   * Corresponds to AMQP `correlation_id` property.
   */
  correlationId?: string;

  /**
   * The actual business data for this message.
   * The structure of T will vary based on the messageType.
   */
  payload: T;

  /**
   * Optional field for data residency, sharding key, or other routing hints if not solely reliant on AMQP routing keys.
   */
  partitionKey?: string; 
}
```

## 3. AMQP Message Properties Complementing the Envelope

When publishing to RabbitMQ, the `rabbitmq-event-utils` library will ensure appropriate AMQP message properties are set in addition to the JSON body envelope. These are crucial for RabbitMQ's operation and for consumers.

*   **`message_id`**: Can be set to the same value as `envelope.messageId`.
*   **`correlation_id`**: Can be set to the same value as `envelope.correlationId`.
*   **`reply_to`**: Used for request/reply patterns (less common for typical EDA events, but supported by AMQP).
*   **`content_type`**: Will be set to `"application/json"`.
*   **`content_encoding`**: Typically `"UTF-8"`.
*   **`timestamp`**: AMQP timestamp (seconds since epoch). The library can generate this from `envelope.timestamp`.
*   **`type`**: Can be set to the `envelope.messageType`.
*   **`app_id`**: Can be set to `envelope.sourceService`.
*   **`delivery_mode`**: Set to `2` (persistent) for durable messages, assuming queues are also durable.
*   **Headers (Custom AMQP Headers):** Can be used for additional out-of-band metadata if necessary (e.g., retry counts if implementing custom retry logic outside of DLX mechanisms, tracing headers if not part of `correlationId`).

## 4. Serialization

*   The entire `StandardMessage<T>` object (the JSON envelope) will be serialized to a JSON string. This string will form the body of the AMQP message.

## 5. Rationale for In-Body Envelope Fields

*   **Clarity and Explicitness:** Having fields like `messageType`, `sourceService`, `correlationId` explicitly in the JSON body makes the message content self-describing even if AMQP properties are somehow stripped or not easily accessible in all debugging/tooling contexts.
*   **Ease of Deserialization:** Consumers deserialize the JSON body once and have all necessary metadata and payload readily available in a typed object.
*   **Flexibility:** Allows for fields like `envelopeVersion` or `partitionKey` that don't have direct, standard AMQP property equivalents but might be useful for application-level logic.
*   **Consistency with Potential Future Systems:** If messages ever need to be passed through systems that don't natively understand AMQP properties, the in-body envelope ensures metadata remains intact.

The producer library will handle the mapping between the JSON envelope fields and the standard AMQP properties where there is overlap to ensure best use of RabbitMQ features.

## 6. Example

**AMQP Message to RabbitMQ:**
*   **Properties:**
    *   `message_id: "a1b2c3d4-e5f6-7890-1234-567890abcdef"`
    *   `correlation_id: "req-xyz-789"`
    *   `content_type: "application/json"`
    *   `type: "UserRegisteredEvent.v1"`
    *   `app_id: "UserService"`
    *   `timestamp: 1672531200` (seconds since epoch)
    *   `delivery_mode: 2`
*   **Body (JSON String):**
    ```json
    {
      "messageId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "messageType": "UserRegisteredEvent.v1",
      "envelopeVersion": "1.0",
      "timestamp": "2023-01-01T00:00:00.000Z",
      "sourceService": "UserService",
      "correlationId": "req-xyz-789",
      "payload": {
        "userId": "user-uuid-123",
        "email": "test@example.com",
        "registeredAt": "2023-01-01T00:00:00.000Z"
      }
    }
    ```

This standard envelope provides a comprehensive and consistent way to structure messages for event-driven communication.