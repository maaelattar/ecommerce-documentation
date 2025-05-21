# 02: Key Payment Events

This document outlines the critical events related to the lifecycle of a payment within the Payment Service. These events are published to the `payment.events` topic exchange on RabbitMQ, using routing keys that allow for specific subscription by interested consumers. All events adhere to the `StandardMessageEnvelope` provided by the `@ecommerce-platform/rabbitmq-event-utils` shared library.

## 1. `PaymentInitiatedEvent`

*   **Routing Key:** `payment.initiated.v1`
*   **Trigger:** Published when a new payment process is started for an order, typically after the Order Service requests payment. This event signifies that the payment is not yet confirmed or processed but has been accepted by the Payment Service.
*   **Purpose:**
    *   Allows services like Order Service to track that payment processing has begun.
    *   Can trigger preliminary actions in other services (e.g., reserving stock for a short period if not already done).
*   **Key Payload Fields (within `data` object of `StandardMessageEnvelope`):**
    *   `paymentId`: Unique ID for this payment attempt.
    *   `orderId`: ID of the order associated with this payment.
    *   `userId`: ID of the user initiating the payment.
    *   `amount`: The total amount to be paid.
    *   `currency`: Currency of the payment (e.g., "USD").
    *   `paymentMethodType`: The type of payment method selected (e.g., "CREDIT_CARD", "PAYPAL").
    *   `initiatedAt`: Timestamp of initiation.

## 2. `PaymentProcessingEvent`

*   **Routing Key:** `payment.processing.v1`
*   **Trigger:** Published when the Payment Service has actively started interacting with a third-party payment gateway or processor (e.g., Stripe, PayPal) for the payment.
*   **Purpose:**
    *   Provides visibility into the payment actively being handled by an external system.
    *   Useful for monitoring and dashboards to see payments in an "in-flight" state.
*   **Key Payload Fields:**
    *   `paymentId`: Unique ID for this payment attempt.
    *   `orderId`: ID of the order.
    *   `gatewayTransactionId`: (Optional) ID assigned by the payment gateway, if available at this stage.
    *   `status`: "PROCESSING"
    *   `processingAt`: Timestamp.## 3. `PaymentSucceededEvent`

*   **Routing Key:** `payment.succeeded.v1`
*   **Trigger:** Published when the payment has been successfully processed and confirmed by the payment gateway and internal checks.
*   **Purpose:**
    *   The primary event for downstream services to confirm successful payment.
    *   Order Service: Triggers order fulfillment.
    *   Notification Service: Sends payment confirmation to the user.
    *   Inventory Service: Confirms stock deduction.
*   **Key Payload Fields:**
    *   `paymentId`: Unique ID for this payment.
    *   `orderId`: ID of the order.
    *   `userId`: ID of the user.
    *   `amountPaid`: The actual amount successfully paid.
    *   `currency`: Currency.
    *   `paymentMethodDetails`: Masked or summarized details of the payment method used (e.g., card type and last four digits).
    *   `gatewayTransactionId`: ID from the payment gateway.
    *   `status`: "SUCCEEDED"
    *   `succeededAt`: Timestamp of success.

## 4. `PaymentFailedEvent`

*   **Routing Key:** `payment.failed.v1`
*   **Trigger:** Published when the payment attempt fails at any stage (e.g., declined by gateway, fraud detection, internal error during processing).
*   **Purpose:**
    *   Allows services to react to payment failure.
    *   Order Service: May update order status to "payment_failed", potentially trigger retry logic or user notification to update payment method.
    *   Notification Service: May inform the user about the failure.
*   **Key Payload Fields:**
    *   `paymentId`: Unique ID for this payment attempt.
    *   `orderId`: ID of the order.
    *   `userId`: ID of the user.
    *   `amount`: The amount that was attempted.
    *   `currency`: Currency.
    *   `failureReason`: A code or message indicating the reason for failure (e.g., "insufficient_funds", "card_declined", "gateway_error").
    *   `gatewayResponseCode`: (Optional) Response code from the payment gateway.
    *   `status`: "FAILED"
    *   `failedAt`: Timestamp of failure.

## 5. `PaymentCapturedEvent`

*   **Routing Key:** `payment.captured.v1`
*   **Trigger:** For payment methods that involve a separate authorization and capture step (e.g., some credit card transactions), this event is published when a previously authorized payment is captured.
*   **Purpose:**
    *   Confirms that funds have been transferred after an initial authorization.
    *   Relevant for financial reconciliation and order fulfillment for "authorize then capture" flows.
*   **Key Payload Fields:**
    *   `paymentId`: Unique ID for this payment.
    *   `authorizationId`: ID of the initial authorization.
    *   `orderId`: ID of the order.
    *   `amountCaptured`: The amount captured.
    *   `currency`: Currency.
    *   `status`: "CAPTURED"
    *   `capturedAt`: Timestamp of capture.

These events provide a comprehensive view of the payment lifecycle, enabling robust and decoupled interactions between the Payment Service and other parts of the e-commerce platform.## 3. `PaymentSucceededEvent`

*   **Routing Key:** `payment.succeeded.v1`
*   **Trigger:** Published when the payment has been successfully processed and confirmed by the payment gateway and internal checks.
*   **Purpose:**
    *   The primary event for downstream services to confirm successful payment.
    *   Order Service: Triggers order fulfillment.
    *   Notification Service: Sends payment confirmation to the user.
    *   Inventory Service: Confirms stock deduction.
*   **Key Payload Fields:**
    *   `paymentId`: Unique ID for this payment.
    *   `orderId`: ID of the order.
    *   `userId`: ID of the user.
    *   `amountPaid`: The actual amount successfully paid.
    *   `currency`: Currency.
    *   `paymentMethodDetails`: Masked or summarized details of the payment method used (e.g., card type and last four digits).
    *   `gatewayTransactionId`: ID from the payment gateway.
    *   `status`: "SUCCEEDED"
    *   `succeededAt`: Timestamp of success.

## 4. `PaymentFailedEvent`

*   **Routing Key:** `payment.failed.v1`
*   **Trigger:** Published when the payment attempt fails at any stage (e.g., declined by gateway, fraud detection, internal error during processing).
*   **Purpose:**
    *   Allows services to react to payment failure.
    *   Order Service: May update order status to "payment_failed", potentially trigger retry logic or user notification to update payment method.
    *   Notification Service: May inform the user about the failure.
*   **Key Payload Fields:**
    *   `paymentId`: Unique ID for this payment attempt.
    *   `orderId`: ID of the order.
    *   `userId`: ID of the user.
    *   `amount`: The amount that was attempted.
    *   `currency`: Currency.
    *   `failureReason`: A code or message indicating the reason for failure (e.g., "insufficient_funds", "card_declined", "gateway_error").
    *   `gatewayResponseCode`: (Optional) Response code from the payment gateway.
    *   `status`: "FAILED"
    *   `failedAt`: Timestamp of failure.## 5. `PaymentCapturedEvent`

*   **Routing Key:** `payment.captured.v1`
*   **Trigger:** For payment methods that involve a separate authorization and capture step (e.g., some credit card transactions), this event is published when a previously authorized payment is captured.
*   **Purpose:**
    *   Confirms that funds have been transferred after an initial authorization.
    *   Relevant for financial reconciliation and order fulfillment for "authorize then capture" flows.
*   **Key Payload Fields:**
    *   `paymentId`: Unique ID for this payment.
    *   `authorizationId`: ID of the initial authorization.
    *   `orderId`: ID of the order.
    *   `amountCaptured`: The amount captured.
    *   `currency`: Currency.
    *   `status`: "CAPTURED"
    *   `capturedAt`: Timestamp of capture.

These events provide a comprehensive view of the payment lifecycle, enabling robust and decoupled interactions between the Payment Service and other parts of the e-commerce platform.