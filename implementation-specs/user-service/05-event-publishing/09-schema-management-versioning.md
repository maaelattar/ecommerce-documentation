# 09 - Schema Management and Versioning

Effective schema management and versioning are critical for evolving event-driven architectures without breaking downstream consumers. This document outlines the User Service's approach to managing the schemas of its published events.

## 1. Schema Definition

*   **Clear Definition**: For each event type (e.g., `UserRegisteredEventV1`), the structure of its `payload` must be clearly defined.
*   **DTOs as Source of Truth (Initial Approach)**: Initially, NestJS DTOs (Data Transfer Objects) used within the User Service to construct event payloads can serve as an implicit schema definition.
    *   These DTOs should be well-documented, and changes to them should be considered carefully as they impact event consumers.
*   **Formal Schema Definition (Future Consideration - Schema Registry)**:
    *   For more robust schema enforcement and management, especially in a polyglot environment or with many consumers, a dedicated Schema Registry (e.g., Confluent Schema Registry for Kafka, Apicurio, or a custom solution) is recommended.
    *   If a schema registry is used, event schemas would be defined in a formal language like Apache Avro, JSON Schema, or Protobuf.
    *   Producers (like the User Service) would register schemas and validate outgoing events against them.
    *   Consumers could fetch schemas from the registry to deserialize and validate incoming events.

## 2. Event Versioning

Versioning is essential to allow event structures to change over time without breaking existing consumers that rely on an older version of the schema.

*   **Versioning in Event Name**: The primary versioning strategy is to include a version number directly in the `eventType` field of the common event envelope.
    *   Example: `UserRegisteredEventV1`, `UserRegisteredEventV2`.
*   **Separate Streams/Exchanges (Optional)**: While the primary approach for the User Service is to use a common exchange and differentiate event versions via the `messageType` or routing key, some systems might publish different event versions to entirely separate exchanges or routing key prefixes for strong isolation. This can increase complexity and is not the default strategy here.
*   **Version Field in Envelope**: The common event envelope also includes a `version` field (e.g., `"version": "1.0"`). This can be used in conjunction with the `eventType` versioning or for more minor, compatible revisions if needed, though relying on `eventType` for breaking changes is clearer.

## 3. Schema Evolution Rules

When evolving an event schema (i.e., creating a new version), rules must be followed to ensure compatibility as much as possible.

*   **Backward Compatibility (Consumers of New Schema Reading Old Events)**:
    *   Generally, when introducing `EventV2`, it should be able to process data from `EventV1` if necessary, or consumers should be updated.
    *   If using a schema registry with formats like Avro, backward compatibility rules include:
        *   Fields can be removed (consumers of the new schema must have default values for removed fields).
        *   New optional fields (with default values) can be added.
*   **Forward Compatibility (Consumers of Old Schema Reading New Events)**:
    *   This is often more critical. Consumers built for `EventV1` should ideally not break when they encounter an `EventV2` if the changes are additive and non-breaking for their specific needs.
    *   If using a schema registry, forward compatibility rules include:
        *   New fields must be optional (have default values).
        *   Fields cannot be removed (unless the old consumer inherently ignores unknown fields, which is typical for JSON but needs schema validation to be robust).
*   **Making Breaking Changes**:
    *   If a breaking change is unavoidable (e.g., renaming a field, changing a data type, removing a required field), a **new event version must be created** (e.g., `UserRegisteredEventV2`).
    *   Both the old and new event versions might need to be published for a transition period to allow consumers to migrate at their own pace.
    *   Clear communication with consumer teams is essential.

## 4. User Service Strategy

1.  **Initial Phase**: 
    *   Event versions will be managed via the `eventType` field (e.g., `UserRegisteredEventV1`).
    *   Schemas are implicitly defined by the User Service's internal DTOs used to generate event payloads.
    *   Focus on making only backward-compatible changes to an existing event version if absolutely necessary (e.g., adding new optional fields to `V1`).
    *   For any breaking change, a new event version (e.g., `V2`) will be introduced.
    *   The User Service will publish the new version. It may or may not continue publishing the old version, depending on consumer needs and migration timelines.

2.  **Future Phase (with Schema Registry)**:
    *   If a platform-wide Schema Registry is adopted:
        *   User Service will define its event schemas in the registry (e.g., using JSON Schema or Avro).
        *   It will validate outgoing events against these registered schemas.
        *   Versioning will be managed according to the registry's capabilities and platform conventions (e.g., Avro schema evolution rules).
        *   This will provide stronger guarantees and better tooling for schema management and consumer/producer compatibility checks.

## 5. Documentation and Communication

*   **Clear Documentation**: All published event types and their schemas (payload structures for each version) must be clearly documented as part of the User Service's API/integration specifications (as is being done in these markdown files).
*   **Change Announcements**: When new event versions are introduced or existing ones are planned for deprecation, this must be communicated to all known consumer teams well in advance, providing clear migration paths and timelines.

By adhering to these schema management and versioning practices, the User Service aims to provide a stable and evolvable event stream for its consumers.
