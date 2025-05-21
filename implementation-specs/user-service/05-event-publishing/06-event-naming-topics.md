# 06 - Event Naming Conventions and Exchange/Routing Key Structure

This document outlines the standardized naming conventions for events published by the User Service and the structure of RabbitMQ exchanges and routing keys used for their dissemination, aligning with the platform's primary use of RabbitMQ (Amazon MQ).

## 1. Event Naming Conventions

A consistent naming convention is crucial for event discoverability, understanding, and schema management.

*   **Structure**: `AggregateActionPastTenseEventV[Version]`
    *   **`Aggregate`**: The primary domain entity or context the event relates to (e.g., `User`, `UserProfile`, `UserRole`, `Permission`).
    *   **`ActionPastTense`**: A verb in the past tense describing what happened (e.g., `Registered`, `Updated`, `Deleted`, `Assigned`, `LoggedIn`).
    *   **`Event`**: Suffix to clearly identify it as an event.
    *   **`V[Version]`**: Version number (e.g., `V1`, `V2`) to support schema evolution. Start with `V1`.
*   **Casing**: PascalCase for the event name.

*   **Examples**:
    *   `UserRegisteredEventV1`
    *   `UserProfileUpdatedEventV1`
    *   `UserAddressAddedEventV1`
    *   `UserLoggedInEventV1`
    *   `MfaStatusChangedEventV1`
    *   `RoleCreatedEventV1`
    *   `PermissionAssignedToRoleEventV1`

*   **Event Type Field**: The `messageType` field within the `StandardMessage<T>` envelope (see `01-event-publishing-mechanism.md` and `@ecommerce-platform/rabbitmq-event-utils`) will use this standardized event name.
    ```json
    {
      // ... common envelope fields ...
      "messageType": "UserRegisteredEventV1", // Formerly eventType
      "payload": { ... }
    }
    ```

## 2. RabbitMQ Exchange and Routing Key Structure

For RabbitMQ, messages are published to exchanges, which then route them to bound queues based on routing keys and exchange types.

*   **Primary Exchange**: A main `topic` exchange will be used for most User Service domain events.
    *   **Exchange Name**: `user.events` (configurable, e.g., via `USER_EVENTS_EXCHANGE` environment variable).
    *   **Exchange Type**: `topic`.
    *   **Rationale**: A topic exchange allows for flexible routing based on wildcard matching of routing keys. Consumers can subscribe to specific event patterns (e.g., all `UserRegistered` events, all events for a specific user if `userId` is part of the routing key, though less common for general topics).
    *   The `@ecommerce-platform/rabbitmq-event-utils` library will facilitate publishing to this exchange.

*   **Routing Key Structure**: Routing keys will be structured to enable granular consumption patterns. A common pattern is `<aggregate>.<action>.<version>` or `<source_service>.<aggregate>.<action>.<detail>.<version>`.
    *   **General Convention**: `user.<aggregate_lowercase>.<action_lowercase>.v[version_number]`
        *   Examples:
            *   `user.account.registered.v1` (for `UserRegisteredEventV1`)
            *   `user.profile.updated.v1` (for `UserProfileUpdatedEventV1`)
            *   `user.address.added.v1` (for `UserAddressAddedEventV1`)
            *   `user.auth.loggedin.v1` (for `UserLoggedInEventV1`)
            *   `user.auth.mfa.statuschanged.v1` (for `MfaStatusChangedEventV1`)
            *   `user.iam.role.created.v1` (for `RoleCreatedEventV1`)
            *   `user.iam.permission.assignedtorole.v1` (for `PermissionAssignedToRoleEventV1`)
    *   **Publishing**: The `UserEventPublisher` service will use the `RabbitMQProducerService` to publish events with these structured routing keys to the `user.events` exchange.
        *   Example: `producerService.publish('user.events', 'user.account.registered.v1', message);`
    *   **Consumption**: Consumers can then bind queues to the `user.events` exchange using specific routing keys or patterns:
        *   `user.account.registered.v1` (specific event)
        *   `user.account.registered.*` (all versions of UserRegistered event)
        *   `user.account.#` (all events related to user accounts)
        *   `user.#` (all events from the User Service published to this exchange path)

*   **Role of `partitionKey` in `StandardMessage<T>`**: While the routing key handles directing the message from the exchange, the optional `partitionKey` field in the `StandardMessage<T>` envelope (often set to `userId`, `roleId`, etc.) can be used by consumers for their own internal sharding, ordering, or parallel processing logic if they are consuming from a shared queue and require such semantics.

*   **Potential Future Exchanges (Consider if volume or segregation needs arise)**:
    *   `user.auth.events` (Topic Exchange): Specifically for high-volume authentication attempts (login success/failure, MFA challenges) if they need to be segregated for security monitoring with different retention, queueing, or access patterns.
    *   `user.admin.events` (Topic Exchange): For events strictly related to administrative actions on users, roles, or permissions, if a clear separation from general user activity events is beneficial for consumers or for different QoS settings.
    *   However, starting with a single primary `user.events` topic exchange and using detailed routing keys is often simpler and sufficient for many scenarios.

*   **Exchange and Queue Declaration**: Exchanges and any necessary durable queues for known, long-lived consumers should ideally be declared and configured by operations/SRE teams using infrastructure-as-code tools. The `rabbitmq-event-utils` library or services themselves can also be configured to idempotently declare exchanges/queues on startup, which is common in development and for service-specific temporary queues.

## 3. Consistency

*   All services publishing events should adhere to a platform-wide guideline for event naming and exchange/routing key structure to maintain consistency and ease of integration across the microservices ecosystem.

By following these conventions, the User Service ensures that its published events are well-organized, versionable, and flexibly consumable by other services in the platform using RabbitMQ.
