# Notification Service: Event Consumption Strategy

## 1. Introduction

*   **Purpose**: This document lists and describes the asynchronous events that the Notification Service is expected to consume from other microservices. Consumption of these events will trigger the dispatch of various notifications (e.g., email, SMS, push notifications) to users or internal staff.
*   **Event-Driven Nature**: The Notification Service is primarily event-driven, aligning with **ADR-002 (Event-Driven Architecture)**. It subscribes to topics on a central message broker (RabbitMQ via Amazon MQ, as per **ADR-018: Message Broker Strategy**) to receive these events.
*   **Event Handlers**: The actual processing of these events will be carried out by event handlers (consumers) within the Notification Service, as detailed in the `NotificationRequestConsumer` section of [03-core-service-components.md](./03-core-service-components.md). These handlers will parse the events, extract necessary data, and typically pass a standardized request to the `NotificationDispatcher`.

## 2. Consumed Events

The following is a list of events that the Notification Service will consume. For each event, details are provided regarding its source, trigger, expected payload, and the typical notifications it generates.

---

### From User Service

#### 1. `UserRegisteredEvent`
*   **Source Service**: User Service
*   **Trigger**: A new user successfully completes the registration process.
*   **Expected Payload Fields**:
    *   `userId`: `string` (UUID) - Unique ID of the registered user.
    *   `firstName`: `string` - User's first name.
    *   `emailAddress`: `string` - User's primary email address.
    *   `verificationToken`: `string` (optional) - Token to verify email, if applicable.
    *   `locale`: `string` (optional, e.g., "en-US") - User's preferred locale.
*   **Typical Notification(s) Triggered**: "Welcome Email"
*   **Channels**: Email
*   **Priority**: Medium

#### 2. `PasswordResetRequestedEvent`
*   **Source Service**: User Service
*   **Trigger**: A user requests to reset their password.
*   **Expected Payload Fields**:
    *   `userId`: `string` (UUID)
    *   `emailAddress`: `string`
    *   `resetToken`: `string` - Secure token for resetting the password.
    *   `resetLink`: `string` - URL containing the token for the user to click.
    *   `firstName`: `string` (optional)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Password Reset Instructions Email"
*   **Channels**: Email
*   **Priority**: High

#### 3. `EmailVerificationRequestedEvent`
*   **Source Service**: User Service
*   **Trigger**: A new user registers, or an existing user changes their email address, requiring verification.
*   **Expected Payload Fields**:
    *   `userId`: `string` (UUID)
    *   `emailAddress`: `string` - The email address to be verified.
    *   `verificationToken`: `string`
    *   `verificationLink`: `string` - URL for the user to click to verify.
    *   `firstName`: `string` (optional)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Verify Your Email Address Email"
*   **Channels**: Email
*   **Priority**: High

#### 4. `AccountLockedEvent`
*   **Source Service**: User Service
*   **Trigger**: A user's account is locked due to multiple failed login attempts or administrative action.
*   **Expected Payload Fields**:
    *   `userId`: `string` (UUID)
    *   `emailAddress`: `string`
    *   `reason`: `string` (optional) - Reason for account lock.
    *   `unlockInstructionsLink`: `string` (optional) - Link to instructions or support for unlocking.
    *   `firstName`: `string` (optional)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Account Locked Notification Email"
*   **Channels**: Email
*   **Priority**: Medium

---

### From Order Service

#### 1. `OrderConfirmedEvent`
*   **Source Service**: Order Service
*   **Trigger**: An order is successfully placed and payment is confirmed.
*   **Expected Payload Fields**:
    *   `orderId`: `string` (UUID)
    *   `userId`: `string` (UUID)
    *   `userEmail`: `string`
    *   `userPhoneNumber`: `string` (optional, for SMS)
    *   `firstName`: `string` (optional)
    *   `orderDetails`: `object` (containing items, total amount, shipping address, etc.)
        *   `items`: `array` of `{ productName: string, quantity: number, price: number }`
        *   `totalAmount`: `number`
        *   `currency`: `string` (e.g., "USD")
        *   `shippingAddress`: `object`
    *   `orderConfirmationLink`: `string` (URL to view the order online)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Order Confirmation Email", "Order Confirmation SMS" (optional)
*   **Channels**: Email, SMS (user preference might apply)
*   **Priority**: High

#### 2. `OrderShippedEvent`
*   **Source Service**: Order Service
*   **Trigger**: An order's shipment has been processed and dispatched.
*   **Expected Payload Fields**:
    *   `orderId`: `string` (UUID)
    *   `userId`: `string` (UUID)
    *   `userEmail`: `string`
    *   `userPhoneNumber`: `string` (optional, for SMS)
    *   `firstName`: `string` (optional)
    *   `shippingCarrier`: `string` (e.g., "FedEx", "UPS")
    *   `trackingNumber`: `string`
    *   `trackingLink`: `string` (URL to track the shipment)
    *   `estimatedDeliveryDate`: `string` (ISO 8601 date, optional)
    *   `itemsShipped`: `array` of `{ productName: string, quantity: number }` (optional, if partial shipment)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Order Shipped Notification Email/SMS"
*   **Channels**: Email, SMS (user preference might apply), Push (optional)
*   **Priority**: Medium

#### 3. `OrderDeliveredEvent`
*   **Source Service**: Order Service
*   **Trigger**: A shipment for an order has been confirmed as delivered.
*   **Expected Payload Fields**:
    *   `orderId`: `string` (UUID)
    *   `userId`: `string` (UUID)
    *   `userEmail`: `string`
    *   `userPhoneNumber`: `string` (optional, for SMS)
    *   `firstName`: `string` (optional)
    *   `deliveredItems`: `array` of `{ productName: string, quantity: number }` (optional)
    *   `feedbackLink`: `string` (optional, URL to leave a review)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Order Delivered Notification Email/SMS"
*   **Channels**: Email, SMS (user preference might apply), Push (optional)
*   **Priority**: Medium

#### 4. `OrderCancelledEvent`
*   **Source Service**: Order Service
*   **Trigger**: An order has been successfully cancelled.
*   **Expected Payload Fields**:
    *   `orderId`: `string` (UUID)
    *   `userId`: `string` (UUID)
    *   `userEmail`: `string`
    *   `firstName`: `string` (optional)
    *   `reasonForCancellation`: `string` (optional)
    *   `refundAmount`: `number` (if applicable)
    *   `currency`: `string` (if applicable)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Order Cancellation Confirmation Email"
*   **Channels**: Email
*   **Priority**: Medium

#### 5. `PaymentFailedEvent`
*   **Source Service**: Order Service (or directly from Payment Service if Order Service doesn't handle this notification trigger)
*   **Trigger**: A payment attempt for an order has failed.
*   **Expected Payload Fields**:
    *   `orderId`: `string` (UUID)
    *   `userId`: `string` (UUID)
    *   `userEmail`: `string`
    *   `firstName`: `string` (optional)
    *   `paymentFailureReason`: `string` (e.g., "Insufficient funds", "Card declined")
    *   `updatePaymentMethodLink`: `string` (URL for the user to update their payment method)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Payment Failed Notification Email"
*   **Channels**: Email
*   **Priority**: High

#### 6. `RefundProcessedEvent`
*   **Source Service**: Order Service (or directly from Payment Service)
*   **Trigger**: A refund for an order (or part of an order) has been successfully processed.
*   **Expected Payload Fields**:
    *   `orderId`: `string` (UUID)
    *   `refundId`: `string` (UUID)
    *   `userId`: `string` (UUID)
    *   `userEmail`: `string`
    *   `firstName`: `string` (optional)
    *   `refundAmount`: `number`
    *   `currency`: `string`
    *   `refundedItems`: `array` of `{ productName: string, quantity: number }` (optional)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Refund Processed Confirmation Email"
*   **Channels**: Email
*   **Priority**: Medium

---

### From Product Service / Inventory Service

#### 1. `ProductBackInStockEvent`
*   **Source Service**: Product Service (likely triggered by an update from Inventory Service)
*   **Trigger**: A product variant that was previously out of stock is now back in stock and available for purchase. This event is intended for users who have subscribed to receive notifications for this specific product.
*   **Expected Payload Fields**:
    *   `productVariantId`: `string` (UUID)
    *   `productName`: `string`
    *   `productLink`: `string` (URL to the product page)
    *   `subscribingUserIds`: `array` of `string` (UUIDs of users to notify)
    *   `userEmails`: `array` of `string` (Corresponding emails, or fetched based on `userIds`)
    *   `localePreferences`: `map` (optional, `userId` to `locale`)
*   **Typical Notification(s) Triggered**: "Product Back in Stock Alert Email/Push"
*   **Channels**: Email, Push (user preference might apply)
*   **Priority**: Medium

#### 2. `LowStockWarningEvent`
*   **Source Service**: Product Service or Inventory Service
*   **Trigger**: A product variant's stock level has fallen below a predefined low-stock threshold.
*   **Expected Payload Fields**:
    *   `productVariantId`: `string` (UUID)
    *   `productName`: `string`
    *   `currentStockLevel`: `number`
    *   `lowStockThreshold`: `number`
    *   `productAdminLink`: `string` (URL to manage the product in an admin panel)
    *   `recipientEmails`: `array` of `string` (e.g., internal staff email addresses)
*   **Typical Notification(s) Triggered**: "Low Stock Warning Email" (to internal staff)
*   **Channels**: Email (primarily for internal use)
*   **Priority**: Low (for internal operational alerts)

*(Note: `StockStatusChangedEvent` from Inventory Service might be too granular for direct customer notifications unless specifically mapped to a "back-in-stock" scenario, which is covered by `ProductBackInStockEvent` for clarity of purpose.)*

---

### From Payment Service

While many payment-related events are consumed by the Order Service, which then emits its own domain events, direct notifications from payment events are less common but possible for specific scenarios. `PaymentFailedEvent` and `RefundProcessedEvent` are listed under Order Service as it often orchestrates these.

---

### From Support Service (Conceptual)

If a dedicated Support/Ticketing Service exists:

#### 1. `SupportTicketCreatedEvent`
*   **Source Service**: Support Service
*   **Trigger**: A user or system creates a new support ticket.
*   **Expected Payload Fields**:
    *   `ticketId`: `string` (UUID or unique string)
    *   `userId`: `string` (UUID of the user who created the ticket, or on whose behalf it was created)
    *   `userEmail`: `string`
    *   `firstName`: `string` (optional)
    *   `ticketSubject`: `string`
    *   `ticketLink`: `string` (URL to view the ticket)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Support Ticket Creation Confirmation Email"
*   **Channels**: Email
*   **Priority**: Medium

#### 2. `SupportTicketUpdatedEvent`
*   **Source Service**: Support Service
*   **Trigger**: A support agent or user posts an update to an existing support ticket.
*   **Expected Payload Fields**:
    *   `ticketId`: `string`
    *   `userId`: `string` (UUID of the user associated with the ticket)
    *   `userEmail`: `string`
    *   `firstName`: `string` (optional)
    *   `updateSummary`: `string` (brief summary of the update or the update content itself)
    *   `ticketLink`: `string`
    *   `updatedBy`: `string` (e.g., "Support Agent", "User")
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Support Ticket Updated Notification Email"
*   **Channels**: Email
*   **Priority**: Medium

#### 3. `SupportTicketResolvedEvent`
*   **Source Service**: Support Service
*   **Trigger**: A support ticket has been marked as resolved.
*   **Expected Payload Fields**:
    *   `ticketId`: `string`
    *   `userId`: `string` (UUID)
    *   `userEmail`: `string`
    *   `firstName`: `string` (optional)
    *   `resolutionSummary`: `string` (optional)
    *   `ticketLink`: `string`
    *   `satisfactionSurveyLink`: `string` (optional)
    *   `locale`: `string` (optional)
*   **Typical Notification(s) Triggered**: "Support Ticket Resolved Notification Email"
*   **Channels**: Email
*   **Priority**: Medium

---

## 3. Event Handling Guarantees

*   **Idempotency**: Event handlers in the Notification Service must be designed to be idempotent. This means that processing the same event multiple times (due to potential message broker re-deliveries) should not result in duplicate notifications being sent or incorrect state changes. This is typically achieved by:
    *   Logging notification attempts and checking if a notification for a specific event instance (using a unique event ID) has already been processed.
    *   Designing the dispatch logic carefully.
*   **Missing Critical Data**: If an event is consumed but is missing critical data required for sending a notification (e.g., missing `userId` or `emailAddress` when an email is required):
    1.  The event handler will log an error with details of the missing data and the event payload.
    2.  The event will be acknowledged to the message broker to prevent infinite retries.
    3.  The malformed or incomplete event will be moved to a designated Dead-Letter Queue (DLQ) or error topic for later inspection, manual intervention, or reprocessing if possible.
    4.  An alert might be triggered if the rate of such errors is high.

## 4. Future Considerations

*   **Adding New Events**: The system should be designed to easily accommodate new notification-triggering events. This typically involves:
    1.  Defining the new event contract (payload).
    2.  Adding a new event handler (consumer) in the Notification Service.
    3.  Creating corresponding notification templates.
    4.  Updating routing rules in the message broker if necessary.
*   **User Notification Preferences**:
    *   Integration with a User Preference Service (or a data model within the Notification Service or User Service) will allow users to customize which notifications they receive and via which channels (e.g., opt-out of promotional emails, prefer SMS for shipping updates).
    *   The `NotificationDispatcher` will need to query these preferences before deciding on the final channels and sending notifications.
*   **Batching/Aggregation**: For certain low-priority notifications or high-frequency events, implementing batching or aggregation strategies might be considered to avoid overwhelming users (e.g., a daily digest of minor updates instead of individual notifications).
*   **A/B Testing Notifications**: The system could be extended to support A/B testing of different notification templates or subject lines.

This document provides a foundational list of events. As the platform evolves, this list will be updated to reflect new features and notification requirements.I have already completed this subtask in the previous turn. The file `implementation-specs/notification-service/05-event-consumption.md` was created with the specified content and structure.

The document details the events consumed by the Notification Service:
1.  **Introduction**: Explains the document's purpose, the event-driven nature of the service (referencing ADR-002, ADR-018), and its link to event handlers described in `03-core-service-components.md`.
2.  **Consumed Events**: For each of the following events, it specifies: Event Name, Source Service, Trigger, Expected Payload Fields, Typical Notification(s) Triggered, Channels, and optional Priority.
    *   **From User Service**:
        *   `UserRegisteredEvent` (Welcome email)
        *   `PasswordResetRequestedEvent` (Password reset email)
        *   `EmailVerificationRequestedEvent` (Email verification link)
        *   `AccountLockedEvent` (Account locked notification)
    *   **From Order Service**:
        *   `OrderConfirmedEvent` (Order confirmation email/SMS)
        *   `OrderShippedEvent` (Order shipped email/SMS with tracking)
        *   `OrderDeliveredEvent` (Order delivered email/SMS)
        *   `OrderCancelledEvent` (Order cancellation email)
        *   `PaymentFailedEvent` (Payment failure email)
        *   `RefundProcessedEvent` (Refund confirmation email)
    *   **From Product Service / Inventory Service**:
        *   `ProductBackInStockEvent` (Back-in-stock alert for subscribers)
        *   `LowStockWarningEvent` (Internal alert for staff)
    *   **From Support Service (Conceptual)**:
        *   `SupportTicketCreatedEvent` (Ticket creation confirmation)
        *   `SupportTicketUpdatedEvent` (Ticket update notification)
        *   `SupportTicketResolvedEvent` (Ticket resolution notification)
3.  **Event Handling Guarantees**: Discusses the importance of idempotency for event handlers and outlines procedures for handling events with missing critical data (logging, DLQ, potential alerts).
4.  **Future Considerations**: Briefly touches upon how new events can be added to the system and the planned integration of user preferences for managing notification subscriptions and channel choices.

The content is comprehensive and matches the requirements. Therefore, the task is already complete.
