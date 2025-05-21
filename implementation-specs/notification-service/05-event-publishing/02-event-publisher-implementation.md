# Event Publisher Implementation for Notification Service

## 1. Overview

This document outlines the implementation details for the event publishing mechanism within the Notification Service, specifically if it needs to publish its own domain events (e.g., `NotificationSentEvent`, `NotificationFailedEvent`). It will adhere to the platform's standard Outbox Pattern and leverage the `@ecommerce-platform/rabbitmq-event-utils` shared library.

## 2. Core Components

The implementation will mirror the pattern established in other services like the Inventory Service:

*   **`EventOutbox` Entity**: A database table (`notification_event_outbox`) to store messages before they are published. Its structure will be identical to the `EventOutbox` entity defined for the Inventory Service (storing `messageId`, `messageType`, `source`, `payloadJson`, `payloadVersion`, `status`, etc.).
*   **`EventPublisherService`**: A service responsible for:
    *   Accepting event details (payload, message type, version, etc.).
    *   Serializing the payload to JSON.
    *   Saving the event components to the `EventOutbox` table within the same database transaction as any related Notification Service state changes.
*   **`OutboxProcessorService`**: A background worker (e.g., cron job) that:
    *   Periodically polls the `notification_event_outbox` table for pending messages.
    *   Constructs the full `StandardMessage<T>` from the outbox entry.
    *   Uses the `RabbitMQProducerService` (from `@ecommerce-platform/rabbitmq-event-utils`) to publish the message to the appropriate RabbitMQ exchange (e.g., `notification.events`).
    *   Updates the outbox entry status (e.g., `PUBLISHED`, `FAILED`), manages retries, and handles errors.
*   **`EventSchemaValidator` (Optional)**: If strict schema validation for outgoing event payloads is required before they are even written to the outbox, this component can be used. It would validate the payload against its defined JSON schema based on `messageType` and `payloadVersion`.

## 3. Implementation Details

Refer to the `ecommerce-documentation/implementation-specs/inventory-service/05-event-publishing/02-event-publisher-implementation.md` for detailed code structure examples of:

*   The `EventOutbox` TypeORM entity.
*   The `EventPublisherService` (specifically the `scheduleEventForPublish` method showing how to save to the outbox within a transaction).
*   The `OutboxProcessorService` (showing polling logic, message construction, use of `RabbitMQProducerService`, and error/retry handling).

The Notification Service will adapt these examples, ensuring:
*   The `source` field in `StandardMessage<T>` is set to `"notification-service"`.
*   The `EventOutbox` entity is named appropriately (e.g., `notification_event_outbox`).
*   The `OutboxProcessorService` publishes to a Notification Service-specific exchange (e.g., `notification.events`) or a general platform exchange if events are globally categorized.

## 4. Key Considerations for Notification Service Publishing

*   **Low Volume**: The Notification Service is primarily an event *consumer*. The volume of events it *publishes* is expected to be relatively low compared to services like Order or Inventory. This might simplify some aspects of the outbox processor (e.g., less aggressive polling, smaller batch sizes initially).
*   **Idempotency of Published Events**: While the outbox pattern helps ensure at-least-once delivery to RabbitMQ, if consumers of `NotificationSentEvent` (for example) trigger critical actions, they must still be idempotent.
*   **Primary Use Case**: The main events (`NotificationSentEvent`, `NotificationFailedEvent`, `NotificationDeliveryUpdateEvent`) are crucial for observability, auditing, and potentially for triggering retry strategies or user alerts *about* notifications.
*   **Configuration**: Similar to other services, cron expressions, batch sizes, and retry limits for the outbox processor will be configurable.

## 5. Transaction Management

It is critical that the `EventPublisherService` operations (writing to the outbox) are part of the same database transaction that handles the core business logic of the Notification Service (e.g., recording a notification attempt before saving its publish-pending event to the outbox). This ensures data consistency.

```typescript
// Conceptual example in a NotificationService method
// ...
// import { EventPublisherService, EventToPublish } from './event-publisher.service';
// import { NotificationSentPayloadV1 } from './payloads/notification-sent.payload';

// async sendEmailNotification(details: EmailDetails): Promise<void> {
//   await this.entityManager.transaction(async (transactionalEM) => {
//     // 1. Logic to interact with email provider (e.g., AWS SES)
//     let dispatchSuccess = false;
//     let externalId: string | undefined;
//     try {
//       const result = await emailProvider.send(details.to, details.subject, details.body);
//       externalId = result.messageId;
//       dispatchSuccess = true;
//       // Record successful dispatch in Notification Service DB using transactionalEM
//     } catch (error) {
//       // Record failure in Notification Service DB using transactionalEM
//       throw error; // Or handle and then prepare a NotificationFailedEvent
//     }

//     // 2. If successful, prepare NotificationSentEvent
//     if (dispatchSuccess) {
//       const payload: NotificationSentPayloadV1 = {
//         notificationId: "internal-notif-id", // From DB record
//         recipientId: details.userId,
//         channel: "EMAIL",
//         dispatchTimestamp: new Date().toISOString(),
//         externalMessageId: externalId,
//         recipientAddress: details.to,
//       };
//       const eventToPublish: EventToPublish<NotificationSentPayloadV1> = {
//         messageType: "NotificationSent",
//         payload: payload,
//         payloadVersion: "1.0",
//         partitionKey: details.userId,
//       };
//       await this.eventPublisher.scheduleEventForPublish(eventToPublish, transactionalEM);
//     } else {
//       // Prepare and schedule NotificationFailedEvent similarly
//     }
//   });
// }
// ...
```

This example illustrates binding the event scheduling to the main database transaction, ensuring that the event is only queued for publishing if the primary operation (and its DB record) succeeds.
