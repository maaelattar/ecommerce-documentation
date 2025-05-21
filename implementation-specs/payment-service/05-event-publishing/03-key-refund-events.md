# 03: Key Refund Events

This document describes the significant events related to the refund process within the Payment Service. Like payment events, these are published to a dedicated RabbitMQ topic exchange (e.g., `payment.events` or a more specific `refund.events` if granularity is desired) using clear routing keys. All events utilize the `StandardMessageEnvelope`.

## 1. `RefundInitiatedEvent`

*   **Routing Key:** `refund.initiated.v1` (or `payment.refund.initiated.v1` if using `payment.events` exchange)
*   **Trigger:** Published when a request to refund a previous payment is received and validated by the Payment Service. This could be triggered by a customer service action or an automated process (e.g., due to order cancellation).
*   **Purpose:**
    *   Signals to other services (e.g., Order Service, Notification Service) that a refund process has started.
    *   Allows for tracking the refund from its inception.
*   **Key Payload Fields (within `data` object of `StandardMessageEnvelope`):**
    *   `refundId`: Unique ID for this refund transaction.
    *   `paymentId`: ID of the original payment being refunded.
    *   `orderId`: ID of the order associated with the original payment.
    *   `userId`: ID of the user associated with the order.
    *   `amount`: The amount to be refunded.
    *   `currency`: Currency of the refund.
    *   `reason`: Reason for the refund (e.g., "customer_request", "product_returned", "order_cancelled").
    *   `initiatedBy`: Identifier for who or what initiated the refund (e.g., "cs_agent_X", "system_cancellation_policy").
    *   `initiatedAt`: Timestamp of initiation.

## 2. `RefundProcessingEvent`

*   **Routing Key:** `refund.processing.v1`
*   **Trigger:** Published when the Payment Service actively starts processing the refund with the payment gateway or internal ledger.
*   **Purpose:**
    *   Indicates that the refund is actively being handled.
    *   Useful for monitoring and to show an "in-progress" status for the refund.
*   **Key Payload Fields:**
    *   `refundId`: Unique ID for this refund.
    *   `paymentId`: ID of the original payment.
    *   `gatewayRefundId`: (Optional) ID assigned by the payment gateway for the refund transaction, if available at this stage.
    *   `status`: "PROCESSING"
    *   `processingAt`: Timestamp.## 3. `RefundSucceededEvent`

*   **Routing Key:** `refund.succeeded.v1`
*   **Trigger:** Published when the refund has been successfully processed, and funds are confirmed to be on their way back to the customer or credited appropriately.
*   **Purpose:**
    *   Confirms successful completion of the refund.
    *   Order Service: Updates order status or item return status.
    *   Notification Service: Informs the user about the successful refund.
    *   Finance/Ledger Systems: For reconciliation.
*   **Key Payload Fields:**
    *   `refundId`: Unique ID for this refund.
    *   `paymentId`: ID of the original payment.
    *   `orderId`: ID of the order.
    *   `amountRefunded`: The actual amount successfully refunded.
    *   `currency`: Currency.
    *   `gatewayRefundId`: ID from the payment gateway for the refund transaction.
    *   `status`: "SUCCEEDED"
    *   `succeededAt`: Timestamp of success.

## 4. `RefundFailedEvent`

*   **Routing Key:** `refund.failed.v1`
*   **Trigger:** Published if the refund attempt fails (e.g., rejected by gateway, technical error).
*   **Purpose:**
    *   Signals that the refund could not be processed.
    *   Requires attention, potentially manual intervention or communication with the customer.
    *   Order Service: May need to revert refund status or flag for review.
    *   Notification Service: May inform relevant internal teams or, carefully, the user.
*   **Key Payload Fields:**
    *   `refundId`: Unique ID for this refund attempt.
    *   `paymentId`: ID of the original payment.
    *   `orderId`: ID of the order.
    *   `amount`: The amount that was attempted for refund.
    *   `currency`: Currency.
    *   `failureReason`: A code or message indicating why the refund failed.
    *   `gatewayResponseCode`: (Optional) Response code from the payment gateway.
    *   `status`: "FAILED"
    *   `failedAt`: Timestamp of failure.

These refund events ensure that the status of refund operations is clearly communicated throughout the platform, enabling consistent state management and appropriate actions by consuming services.