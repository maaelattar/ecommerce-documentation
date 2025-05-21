# 03: Notification Service Integration

The Notification Service is responsible for sending various communications (email, SMS, push notifications) to users and potentially administrators. The Payment Service integrates with it by publishing events that trigger these notifications, keeping users informed about the status of their payments and refunds.

## Flow and Interactions

**Payment Service Events -> Notification Service Consumer**

*   **Trigger**: The Payment Service publishes events related to significant changes in payment, refund, or payment method status.
*   **Interaction**: The Notification Service is a consumer of events from the `payment.events` Kafka topic (or equivalent).
*   **Data Processing by Notification Service**: 
    1.  Consumes an event (e.g., `PaymentSucceeded`).
    2.  Parses the event payload to extract relevant information (e.g., `userId`, `orderId`, `amountPaid`, `currency`, `paymentMethodSummary`).
    3.  Determines the type of notification to send based on the `eventType`.
    4.  May fetch additional user details (like email address or phone number) from the User Service using the `userId` provided in the event.
    5.  May fetch additional order details (like items purchased) from the Order Service using the `orderId` for richer notification content.
    6.  Constructs the notification message (email template, SMS content).
    7.  Sends the notification via the appropriate channel (email, SMS provider).

## Key Events Consumed by Notification Service (from Payment Service)

*   **`PaymentSucceeded`**: 
    *   **Notification Type**: Payment confirmation email/SMS.
    *   **Content**: Confirmation of successful payment, amount, order number, last few digits of card used.
*   **`PaymentFailed`**: 
    *   **Notification Type**: Payment failure notification email/SMS.
    *   **Content**: Inform user that payment failed, reason (if user-friendly), suggest trying again or using a different payment method, link to order.
*   **`PaymentRequiresAction`**: 
    *   **Notification Type**: Action required for payment email/SMS.
    *   **Content**: Inform user that their payment needs an additional step (e.g., 3D Secure), provide instructions or a link to complete the action.
*   **`RefundSucceeded` (or `RefundProcessed`)**: 
    *   **Notification Type**: Refund confirmation email/SMS.
    *   **Content**: Confirmation that a refund has been processed, amount refunded, original order number.
*   **`RefundFailed`**: 
    *   **Notification Type**: Refund failure notification (typically to admin/support, possibly to user if appropriate).
    *   **Content**: Inform that a refund attempt failed, reason, requires investigation.
*   **`PaymentMethodAdded`**: 
    *   **Notification Type**: Optional: Payment method added confirmation email.
    *   **Content**: Confirmation that a new payment method was successfully added to their account.
*   **`PaymentMethodRemoved`**: 
    *   **Notification Type**: Optional: Payment method removed confirmation email.
*   **`PaymentDisputeOpened` (if this event is published)**:
    *   **Notification Type**: Dispute notification (to admin/finance/support team).
    *   **Content**: Details of the dispute, payment involved, deadline for response.
*   **Upcoming Card Expiry Reminders (Advanced)**:
    *   While not a direct event from Payment Service transaction processing, if Payment Service can identify cards nearing expiry (e.g., via a batch job or webhook from gateway), it could publish an event like `PaymentMethodNearingExpiry` that Notification Service consumes to send reminders to users.

## Data Considerations

*   **Event Payloads**: Events from Payment Service should contain necessary identifiers (`userId`, `orderId`, `paymentId`, `refundId`) and key non-sensitive data points relevant to the notification.
*   **Data Enrichment**: The Notification Service acts as an aggregator, enriching events with data from other services (User Service, Order Service) to create comprehensive notifications.
*   **Templates**: Notification templates (for email, SMS) are managed within or by the Notification Service.

## Decoupling

*   This integration is highly decoupled. The Payment Service is only responsible for publishing facts (events) about what happened.
*   The Notification Service decides if, when, how, and to whom notifications are sent based on these events.
*   This allows changes in notification logic or channels without impacting the Payment Service.

## Security

*   The Notification Service must handle any PII (like email addresses fetched from User Service) securely and in compliance with privacy regulations.
*   Events consumed from Kafka should be from a trusted, secured topic.

This event-driven integration with the Notification Service ensures timely and relevant communication to users and stakeholders regarding their financial transactions and payment method management.
