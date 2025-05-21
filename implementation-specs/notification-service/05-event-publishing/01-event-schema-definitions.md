# Notification Service Event Schema Definitions

## 1. Overview

This document defines the schemas for the **payloads** of events published by the Notification Service. All events adhere to the `StandardMessage<T>` envelope provided by the `@ecommerce-platform/rabbitmq-event-utils` shared library.

## 2. Standard Event Envelope

All events use the `StandardMessage<T>` envelope. Refer to the shared library documentation or other service event schema definitions (e.g., Inventory Service) for the structure of `StandardMessage<T>`.
Key fields include `messageId`, `messageType`, `timestamp`, `source` (which will be "notification-service"), `payload`, and `version` (for the payload schema).

## 3. Payload Schema Versioning Strategy

Payload schemas use a versioning scheme (e.g., "1.0", "1.1") stored in the `version` field of the `StandardMessage` envelope, following semantic versioning principles for the payload itself.

## 4. Notification Service Event Payloads

These interfaces define the structure of the `payload` field for various notification-related events.

### 4.1. `NotificationSentEvent`

*   **`messageType`**: `NotificationSent`
*   **Description**: Published when a notification has been successfully dispatched to the underlying provider (e.g., email sent to SMTP server, SMS submitted to gateway).

```typescript
// Payload for StandardMessage<NotificationSentPayloadV1>
// where version would be "1.0"
export interface NotificationSentPayloadV1 {
  notificationId: string;    // Unique ID of the notification attempt/record in Notification Service
  originalEventId?: string; // Optional: ID of the event that triggered this notification
  recipientId: string;       // User ID or system identifier of the recipient
  channel: "EMAIL" | "SMS" | "PUSH" | "WEBHOOK"; // Channel used
  templateId?: string;      // Optional: Template used for the notification
  dispatchTimestamp: string; // ISO-8601 UTC when it was sent to the provider
  externalMessageId?: string; // Optional: ID from the external provider (e.g., SMTP message ID, SMS gateway ID)
  subjectOrTitle?: string;  // Optional: Subject for email, title for push
  recipientAddress: string;  // e.g., email address, phone number, webhook URL
}
```

### 4.2. `NotificationFailedEvent`

*   **`messageType`**: `NotificationFailed`
*   **Description**: Published when a notification dispatch attempt fails definitively after all configured retries, or if a non-retriable error occurs.

```typescript
// Payload for StandardMessage<NotificationFailedPayloadV1>
// where version would be "1.0"
export interface NotificationFailedPayloadV1 {
  notificationId: string;    // Unique ID of the notification attempt/record
  originalEventId?: string; // Optional: ID of the event that triggered this notification
  recipientId: string;
  channel: "EMAIL" | "SMS" | "PUSH" | "WEBHOOK";
  templateId?: string;
  attemptTimestamp: string;  // ISO-8601 UTC of the final failed attempt
  reason: string;            // Description of why it failed
  errorCode?: string;         // Optional: Error code from provider or internal system
  isRetriable: boolean;      // Indicates if the failure was deemed non-retriable or retries exhausted
  recipientAddress: string;
}
```

### 4.3. `NotificationDeliveryUpdateEvent`

*   **`messageType`**: `NotificationDeliveryUpdate`
*   **Description**: Published when an update on the final delivery status is received from an external provider (e.g., email bounced, delivered, opened; SMS delivered, undelivered).

```typescript
// Payload for StandardMessage<NotificationDeliveryUpdatePayloadV1>
// where version would be "1.0"
export interface NotificationDeliveryUpdatePayloadV1 {
  notificationId: string;    // ID of the original notification dispatch
  externalMessageId?: string; // ID from the external provider, if available
  channel: "EMAIL" | "SMS" | "PUSH"; // Typically for channels that provide delivery receipts
  status: "DELIVERED" | "BOUNCED" | "UNDELIVERED" | "OPENED" | "CLICKED" | "SPAM_COMPLAINT" | "REJECTED";
  updateTimestamp: string;   // ISO-8601 UTC when this status update was processed
  providerResponse?: Record<string, any>; // Optional: Raw response or details from the provider
  recipientAddress: string;
}
```

### 4.4. `CommunicationPreferenceUpdatedEvent`

*   **`messageType`**: `CommunicationPreferenceUpdated`
*   **Description**: Published if the Notification Service manages user communication preferences and an update occurs that other services might need to be aware of (e.g., for filtering event consumers based on preferences before even attempting to send to Notification Service).

```typescript
// Payload for StandardMessage<CommunicationPreferenceUpdatedPayloadV1>
// where version would be "1.0"
export interface CommunicationPreferenceUpdatedPayloadV1 {
  userId: string;
  channel: "EMAIL" | "SMS" | "PUSH" | "ALL"; // Specific channel or all
  preferenceType: string; // e.g., "marketing_updates", "order_confirmations", "security_alerts"
  isEnabled: boolean;
  updateTimestamp: string; // ISO-8601 UTC
  sourceOfChange: string;  // e.g., "user_profile_settings", "admin_update"
}
```

### 4.5. `NotificationTemplateUpdatedEvent`

*   **`messageType`**: `NotificationTemplateUpdated`
*   **Description**: Published if the Notification Service is responsible for managing notification templates and a template is created, updated, or deleted. This could be used for cache invalidation in services that pre-fetch template info or for auditing.

```typescript
// Payload for StandardMessage<NotificationTemplateUpdatedPayloadV1>
// where version would be "1.0"
export interface NotificationTemplateUpdatedPayloadV1 {
  templateId: string;
  templateName: string;
  channel: "EMAIL" | "SMS" | "PUSH";
  action: "CREATED" | "UPDATED" | "DELETED";
  versionTag?: string;       // Optional: new version tag/number of the template
  updateTimestamp: string;  // ISO-8601 UTC
  updatedBy?: string;        // Optional: User/system that made the change
}
```

## 5. Example: `NotificationSentEvent`

```json
{
  "messageId": "msg-uuid-goes-here",
  "messageType": "NotificationSent",
  "timestamp": "2023-11-01T12:00:00Z",
  "source": "notification-service",
  "partitionKey": "user-uuid-goes-here", // e.g., recipientId
  "correlationId": "trigger-event-uuid",
  "payload": {
    "notificationId": "notif-uuid-internal",
    "recipientId": "user-uuid-goes-here",
    "channel": "EMAIL",
    "templateId": "order_confirmation_v2",
    "dispatchTimestamp": "2023-11-01T12:00:05Z",
    "externalMessageId": "smtp-message-id-external",
    "subjectOrTitle": "Your Order #12345 Has Been Confirmed!",
    "recipientAddress": "customer@example.com"
  },
  "version": "1.0"
}
```
