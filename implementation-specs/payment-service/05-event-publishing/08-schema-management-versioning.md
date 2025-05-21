# 08: Schema Management and Event Versioning

As the e-commerce platform evolves, the structure of events (their schemas) published by the Payment Service may need to change. Effective schema management and versioning are essential to ensure that these changes do not break consuming services and that evolution can occur gracefully.

## Core Principles

*   **Schema Definition:** Event schemas (the structure of the `data` object within the `StandardMessageEnvelope`) should be clearly defined and documented for each event type.
*   **Immutability of Published Events:** Once an event with a specific `eventId` and `eventVersion` is published, its schema and payload for that instance should be considered immutable. Do not change events that are already in flight or stored in queues.
*   **Backward Compatibility (Preferred):** When evolving an event schema, strive for backward-compatible changes whenever possible. This means existing consumers can still process the new version of the event without breaking, even if they don't utilize the new fields.
*   **Explicit Versioning:** Use the `eventVersion` field in the `StandardMessageEnvelope` to explicitly version event schemas.

## `eventVersion` in `StandardMessageEnvelope`

*   **Format:** Semantic Versioning (e.g., "1.0", "1.1", "2.0") is recommended.
    *   **MAJOR (e.g., 1.x to 2.0):** Increment for breaking changes.
    *   **MINOR (e.g., 1.0 to 1.1):** Increment for backward-compatible additions or optional field changes.
    *   **PATCH (e.g., 1.0.0 to 1.0.1):** Typically for backward-compatible bug fixes in the event generation that don't alter the schema structure (less common for schema versioning itself, more for producer logic). Often, Minor version bumps are sufficient for schema additions.
*   **Granularity:** Versioning is per `eventType`. For example, `PaymentSucceededEvent` might be at "1.2" while `RefundInitiatedEvent` is at "1.0".

## Schema Evolution Strategies

### 1. Backward-Compatible Changes (Additive Changes)

*   **Adding New Optional Fields:** If a new piece of information needs to be added to an event, add it as a new optional field to the `data` payload.
    *   Increment the MINOR version (e.g., from "1.0" to "1.1").
    *   Existing consumers will ignore the new field if they don't know about it.
    *   New or updated consumers can choose to use the new field.
*   **Marking Fields as Optional (from Required):** This is generally a breaking change if consumers expect the field. Avoid if possible, or treat as a major version bump.### 2. Breaking Changes (Major Version Increment)

If a change cannot be made in a backward-compatible way (e.g., renaming a field, removing a required field, changing a field's data type fundamentally), a new MAJOR version of the event must be introduced.

*   **Procedure:**
    1.  Define the new event schema (e.g., `PaymentSucceededEvent` version "2.0").
    2.  The Payment Service starts publishing events with the new `eventType` (if renaming the type for clarity) or the same `eventType` but with the new `eventVersion` (e.g., `eventType: "PaymentSucceeded"`, `eventVersion: "2.0"`).
    3.  **Dual Publishing (Optional but Recommended for Smooth Transition):** For a transition period, the Payment Service might publish *both* the old version (e.g., "1.x") and the new version ("2.0") of the event, possibly to different routing keys or with clear version indicators that consumers can filter on. This allows existing consumers to continue functioning while new consumers are built/updated for the new version.
    4.  Consumers are updated to understand and process the new event version. They might need to handle both old and new versions for a while.
    5.  Once all critical consumers are migrated to the new version, the publisher can stop publishing the old version.
*   **Routing Key Adaptation:** If using versioned routing keys (e.g., `payment.succeeded.v1`, `payment.succeeded.v2`), this helps consumers subscribe specifically to the version(s) they support.

## Schema Registry (Consideration for Future Scale)

While not mandated for initial implementation, as the number of services and event types grows, a **Schema Registry** can become invaluable.

*   **Purpose:** A centralized service to store, manage, and version event schemas (e.g., using Apache Avro, JSON Schema, or Protobuf schemas).
*   **Benefits:**
    *   Enforces schema validation on publish and/or consume.
    *   Provides a single source of truth for event structures.
    *   Can facilitate schema compatibility checks.
    *   Client libraries can fetch schemas at runtime or build time.
*   **Popular Options:** Confluent Schema Registry (for Kafka, but concepts apply), Apicurio.## Documentation

*   All event types, their versions, and their schemas (fields, data types, required/optional status) MUST be clearly documented.
*   This documentation should be easily accessible to developers of consuming services. The markdown files within this `05-event-publishing` section serve this purpose.

By diligently applying versioning and managing schema changes thoughtfully, the Payment Service can evolve its event communication without causing widespread disruption to the e-commerce platform.