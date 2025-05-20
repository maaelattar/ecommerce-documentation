# Product Service Integration with Notification Service (Potential)

## 1. Overview

This document outlines how the **Product Service** integrates with a central **Notification Service**. The primary and preferred mechanism for triggering notifications related to product data changes is **asynchronous and event-driven**. Product Service publishes events (as detailed in [Phase 5](../../05-event-publishing/)), and the Notification Service subscribes to these events to orchestrate and send notifications to appropriate recipients based on its own logic and user preferences.

Direct, synchronous API calls from the Product Service to the Notification Service are considered **exceptional**. They are reserved for scenarios requiring immediate, targeted, often operational or administrative alerts that are not part of the standard business event flow that other services or users would subscribe to.

## 2. Event-Driven Notifications (Primary Mechanism)

- **Product Service Role**: Publishes domain events related to products, categories, prices, etc. Examples relevant to notifications (which Notification Service might consume) include:
  - `ProductStatusChanged` (e.g., a product becoming `ACTIVE` after being `DRAFT`, or `OUT_OF_STOCK`)
  - `ProductPriceChanged` (especially significant drops for wishlisted items)
  - `NewProductInCategory` (if Product Service enriches and emits such an event, or if Notification Service derives it)
  - `DiscountAppliedToProduct` / `DiscountEndingSoon`
- **Notification Service Role (as Event Consumer)**:
  - Subscribes to relevant events from Product Service (and other services).
  - Manages user notification preferences (e.g., "notify me when products on my wishlist have a price drop").
  - Contains the logic to determine _who_ to notify, _what_ channel to use (email, SMS, push), and the _content_ of the notification (often using templates).
  - Product Service does not dictate these aspects for general business notifications; it simply provides the factual events.

## 3. Exceptional Synchronous API Calls to Notification Service

These are direct calls made by Product Service for immediate, specific, often operational alerts. Product Service MUST adhere to [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md) when making these calls.

- **Purpose Examples (for direct, immediate alerts)**:
  - Sending an alert to an administrator after a critical internal Product Service batch job (e.g., data import/sync) fails validation.
  - Notifying a specific internal compliance team about a product that has been automatically flagged by Product Service logic for urgent review due to policy violations.
  - Triggering a one-time, direct notification upon the successful completion of a significant, long-running administrative task initiated via a Product Service API (where an event isn't suitable for the recipient).
- **Notification Service Endpoint(s)**: _[To be defined by Notification Service, e.g., POST /notifications/send-direct-alert]_
- **Request Payload(s) Example (Conceptual)**:
  ```json
  {
    "channel": "EMAIL", // or "SLACK", specific admin channels
    "recipientDetails": {
      "emailAddress": "product-admins@example.com", // Specific group or role
      "slackChannelId": "C123ABC456"
    },
    "severity": "CRITICAL", // e.g., CRITICAL, WARNING, INFO
    "title": "Product Service: Critical Data Import Failure",
    "messageBody": "The product data import job (ID: job-uuid-123) failed at {timestamp}. Reason: {failure_reason}. Please investigate immediately. Link to logs: {...}",
    "sourceService": "ProductService",
    "correlationId": "correlation-uuid-abc",
    "metadata": {
      // Optional context
      "jobId": "job-uuid-123",
      "failedRecordCount": 150
    }
  }
  ```
- **Response Payload(s) Example (from Notification Service)**:
  ```json
  {
    "notificationAttemptId": "notif-attempt-uuid-xyz",
    "dispatchStatus": "QUEUED" // or "SENT_SUCCESS", "FAILED_TO_DISPATCH"
  }
  ```

## 4. Considerations

- **Clear Distinction**: It's crucial to distinguish between:
  - Product Service publishing general domain events (handled by Notification Service for broad notification purposes).
  - Product Service making exceptional, direct synchronous calls for specific, urgent operational alerts.
- **Notification Service Capabilities**: The structure of synchronous request payloads will depend on the Notification Service's API design for direct alerting (e.g., support for specific channels, recipient types, templating for alerts vs. raw messages).

## 5. References

- [Notification Service OpenAPI Specification](../../../notification-service/openapi/notification-service.yaml) _(Assumed path, would define the direct alert API)_
- [Product Service - Phase 5 Event Publishing](../../05-event-publishing/)
- [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md)
