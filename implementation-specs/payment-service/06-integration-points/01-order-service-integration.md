# 01: Order Service Integration

The Order Service and Payment Service are tightly coupled in the e-commerce workflow. The Order Service is typically responsible for managing the lifecycle of an order, including gathering cart details, calculating totals, and then initiating the payment process.

## Flows and Interactions

**1. Payment Initiation (Order Service -> Payment Service API)**

*   **Trigger**: When an order is confirmed by a customer and is ready for payment (e.g., after checkout steps are completed).
*   **Interaction**: The Order Service makes an API call to the Payment Service to initiate payment.
    *   This usually involves calling an endpoint like `POST /v1/payments/intents` or `POST /v1/payments` on the Payment Service.
*   **Data Passed by Order Service**:
    *   `orderId` (crucial for linking the payment to the order).
    *   Total `amount` due.
    *   `currency`.
    *   `userId` (if available).
    *   Line items description or summary (for display on gateway pages or for Level 2/3 card data processing if supported and configured).
    *   Customer details (name, email, billing/shipping addresses, if not already managed by Payment Service or for guest checkouts).
    *   Any selected payment method token (if the user chose a saved payment method, this token would have been obtained by the client and passed to the Order Service, which then relays it).
*   **Payment Service Response**: The Payment Service responds with details like:
    *   `paymentId` (its internal ID for the payment attempt).
    *   `gatewayPaymentIntentId` (if applicable).
    *   `clientSecret` (if client-side confirmation with a gateway SDK is needed, e.g., for Stripe).
    *   `status` (e.g., `REQUIRES_PAYMENT_METHOD`, `REQUIRES_ACTION`).
    *   `nextAction` (e.g., a redirect URL if the user needs to be sent to the gateway's page).
*   **Order Service Action**: The Order Service updates the order status (e.g., `PENDING_PAYMENT`, `AWAITING_USER_ACTION`) and may relay necessary information (like `clientSecret` or redirect URL) to the frontend client.

**2. Payment Status Updates (Payment Service Events -> Order Service Consumer)**

*   **Trigger**: The Payment Service publishes events when the status of a payment changes.
*   **Interaction**: The Order Service subscribes to relevant events from the `payment.events` Kafka topic (or equivalent).
*   **Key Events Consumed by Order Service**:
    *   `PaymentSucceeded`:
        *   Order Service updates the order status to `PAID` or `PROCESSING_FULFILLMENT`.
        *   May trigger fulfillment workflows (e.g., notifying warehouse, initiating shipping).
        *   Records payment details against the order.
    *   `PaymentFailed`:
        *   Order Service updates the order status to `PAYMENT_FAILED`.
        *   May trigger notifications to the user to try again or use a different payment method.
        *   May release any reserved inventory.
    *   `PaymentRequiresAction`:
        *   Order Service might update status to `AWAITING_USER_PAYMENT_ACTION` and ensure the user is guided correctly.
    *   `PaymentCaptured` (if using auth/capture flow):
        *   Signals that funds are secured; can be a trigger for final fulfillment steps.
    *   `RefundProcessed` (or `RefundSucceeded`):
        *   Order Service updates the order to reflect the refund (e.g., partially refunded, fully refunded).
        *   May adjust order totals and trigger related processes like inventory restock for returned items.
    *   `RefundFailed`:
        *   Order Service notes the failure; may require manual intervention or re-initiation.
*   **Order Service Action**: Updates its internal order state based on these events to maintain consistency.

**3. Refund Initiation (Order Service -> Payment Service API - Optional/Admin)**

*   **Trigger**: A customer service representative or an automated process (e.g., return processing) determines a refund is needed for an order.
*   **Interaction**: If the Order Service (or an associated admin tool) has the authority to initiate refunds, it would call an endpoint like `POST /v1/refunds` on the Payment Service.
*   **Data Passed**: `paymentId` (obtained when payment was made or queried), `amount`, `currency`, `reason`.
*   **Note**: This flow often has stricter authorization as it involves financial operations.

## Data Consistency

*   It's crucial to ensure data consistency between the Order Service and Payment Service.
*   Eventual consistency is achieved through event-driven updates. The Order Service relies on payment events to reflect the true financial status of an order.
*   Robust error handling and retry mechanisms in event consumption are important for the Order Service.
*   Compensating transactions or reconciliation processes might be needed if discrepancies occur, though a well-designed event flow minimizes this.

## Security Considerations

*   API calls between Order Service and Payment Service should be secured (e.g., mTLS, or JWT-based service-to-service authentication if traversing an API Gateway).
*   The Payment Service should validate that the `orderId` and `amount` in payment requests are legitimate, potentially by a quick check-back to Order Service if high security is needed (though this adds coupling).

This tight integration ensures that orders are only processed upon successful payment and that both services maintain an accurate and consistent view of the order's financial lifecycle.
