# 02 - Event Consumption by Other Microservices

This document describes how other microservices within the e-commerce platform consume and react to domain events published by the User Service. This event-driven integration is key to maintaining data consistency, enabling decoupled workflows, and allowing services to respond to user lifecycle changes.

## 1. Purpose of Event Consumption

Other microservices subscribe to User Service events for various reasons:

*   **Data Synchronization**: To keep their local data stores consistent with user information (e.g., Search Service indexing user names, Order Service updating customer details on existing orders if relevant).
*   **Triggering Workflows**: To initiate processes based on user actions (e.g., Notification Service sending a welcome email upon `UserRegisteredEventV1`).
*   **Analytics and Reporting**: To feed data into analytics pipelines for business intelligence.
*   **Security and Auditing**: To log user activities or react to security-relevant events (e.g., a fraud detection service analyzing login patterns).
*   **Personalization**: To update personalization models or caches based on user profile changes.

## 2. Mechanism for Event Consumption

*   **Message Broker (Kafka)**: Consuming services connect to the same Kafka cluster that the User Service publishes to.
*   **Kafka Consumers**: Each interested service implements a Kafka consumer (or consumer group) that subscribes to the relevant User Service topic(s), primarily `user.events`.
*   **NestJS Microservice Integration**: Services built with NestJS can use the `@nestjs/microservices` module with the Kafka transporter to act as event consumers.
    *   They define event handlers (e.g., methods decorated with `@EventPattern('UserRegisteredEventV1')`) to process specific event types from the `user.events` topic.
*   **Filtering**: Consumers are responsible for filtering the events they are interested in, typically based on the `eventType` field in the event envelope.

## 3. Key Consuming Services and Their Interests (Examples)

*   **Notification Service**:
    *   `UserRegisteredEventV1`: Send welcome email, initiate email verification process.
    *   `UserEmailVerifiedEventV1`: Send email verification success notification.
    *   `UserPasswordChangedEventV1`: Send password change security alert.
    *   `UserPasswordResetRequestedEventV1`: Send password reset instructions/link via email.
    *   `MfaStatusChangedEventV1`: Notify user of MFA enabling/disabling.
    *   `UserAccountStatusChangedEventV1`: Notify user of account suspension or reactivation.
*   **Order Service**:
    *   `UserAddressAddedEventV1` / `UserAddressUpdatedEventV1`: Potentially update customer address records for future orders, or flag existing unshipped orders if a default address changed significantly (though this requires careful consideration of data ownership at time of order).
    *   `UserProfileUpdatedEventV1`: Update customer name/contact details if the Order Service maintains a local cache or copy.
    *   `UserDeletedEventV1`: Anonymize or mark customer data associated with orders according to data retention policies.
*   **Search Service**:
    *   `UserRegisteredEventV1`, `UserProfileUpdatedEventV1`: If user profiles or user-generated content linked to users are searchable, these events trigger re-indexing of relevant user information.
    *   `UserDeletedEventV1`: Remove user data from the search index.
*   **Analytics Service**:
    *   Consumes a wide range of events (`UserRegisteredEventV1`, `UserLoggedInEventV1`, `UserProfileUpdatedEventV1`, etc.) to build user behavior models, track conversions, and generate reports.
*   **Personalization Service**:
    *   `UserProfileUpdatedEventV1` (especially changes to preferences, bio, etc.): Update personalization models.
    *   `UserAddressAddedEventV1` (country/city): Refine location-based recommendations.
*   **Fulfillment/Shipping Service**:
    *   `UserAddressAddedEventV1` / `UserAddressUpdatedEventV1` / `UserAddressDeletedEventV1`: May need to be aware of address changes if they maintain their own address validation or enrichment caches, especially for default addresses.
*   **Audit Log Service / Security Monitoring Service**:
    *   `UserLoggedInEventV1`, `UserLoginFailedEventV1`, `UserPasswordChangedEventV1`, `MfaStatusChangedEventV1`, `RoleCreatedEventV1`, `UserRoleAssignedEventV1`, etc.: Consume nearly all security-relevant events for auditing and threat detection.

## 4. Consumer Responsibilities

*   **Idempotency**: Consumers MUST design their event handlers to be idempotent. Processing the same event multiple times should not lead to incorrect data or duplicate actions.
    *   This is critical as Kafka (and other brokers) can sometimes deliver messages more than once (at-least-once delivery is common).
    *   Techniques: Tracking processed `eventId`s, using UPSERT database operations, designing handlers to be naturally idempotent.
*   **Error Handling**: Robust error handling is essential.
    *   If a consumer fails to process an event, it should have a retry mechanism (often provided by the Kafka client or consumer library).
    *   For persistent errors, the event might be moved to a Dead Letter Queue (DLQ) specific to that consumer for later analysis and manual intervention.
    *   Failures in one consumer should not impact other consumers or the User Service.
*   **Schema Compatibility & Versioning**: Consumers must be aware of event versions (e.g., `UserRegisteredEventV1`, `UserRegisteredEventV2`).
    *   They should be designed to handle expected schema changes gracefully (e.g., ignoring new optional fields in a new version if they only process V1 fields).
    *   When the User Service introduces a new event version, consumers need to be updated to support it if they require the new fields or if the old version is deprecated.
*   **Data Consistency Models**: Consumers need to understand the eventual consistency model. Data derived from events will eventually reflect the state in the User Service, but there might be a brief delay.
*   **Filtering and Projection**: Consumers should only process and store the data they actually need from the event payload to avoid unnecessary data duplication and processing overhead.

## 5. Data Flow Example (User Registration)

1.  User Service: Creates user, commits to DB.
2.  User Service: Publishes `UserRegisteredEventV1` (keyed by `userId`) to `user.events` Kafka topic.
3.  Notification Service (Consumer Group A, subscribed to `user.events`):
    *   Receives `UserRegisteredEventV1`.
    *   If `eventType` is `UserRegisteredEventV1`:
        *   Sends a welcome email using `payload.email`.
        *   If `payload.status` is `pending_verification`, initiates email verification flow.
        *   Marks `eventId` as processed.
4.  Search Service (Consumer Group B, subscribed to `user.events`):
    *   Receives `UserRegisteredEventV1`.
    *   If `eventType` is `UserRegisteredEventV1`:
        *   Extracts `userId`, `email`, `firstName`, `lastName` from payload.
        *   Updates its search index for users.
        *   Marks `eventId` as processed.

This event-driven approach allows for a highly scalable and resilient architecture where services can evolve independently while staying informed about critical user lifecycle changes.
