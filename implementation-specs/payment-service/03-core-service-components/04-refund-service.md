# 04: `RefundService`

The `RefundService` is dedicated to managing all aspects of refund processing. It handles requests to refund payments, interacts with payment gateways (via the `PaymentGatewayIntegrationService`) to execute refunds, and ensures that `Refund` entities and related `Payment` and `Transaction` records are updated accurately.

## Responsibilities

1.  **Refund Initiation**: 
    *   Receives requests to initiate a refund (e.g., from an API controller used by customer service or an automated process).
    *   Validates refund requests: 
        *   Checks if the original payment exists and was successful.
        *   Verifies that the refund amount does not exceed the refundable amount of the original payment (considering previous refunds).
        *   Validates other parameters like currency and refund reason.
    *   Creates a `Refund` entity with an initial status (e.g., `PENDING`).

2.  **Gateway Interaction for Refunds**: 
    *   Determines the appropriate payment gateway used for the original transaction.
    *   Invokes the `PaymentGatewayIntegrationService` to process the refund with the gateway, providing necessary details like the original gateway charge/transaction ID and the refund amount.

3.  **State Management**: 
    *   Updates the status of the `Refund` entity based on the outcome of the gateway refund operation (e.g., `PROCESSING`, `SUCCEEDED`, `FAILED`).
    *   Coordinates with the `TransactionManagementService` to create a corresponding `Transaction` record of type `REFUND` to log this financial operation.
    *   Updates the parent `Payment` entity if necessary (e.g., to reflect the refunded amount or update its status if fully refunded).

4.  **Error Handling**: 
    *   Manages errors returned by the payment gateway during refund processing.
    *   Logs detailed error information in the `Refund` entity and the associated `REFUND` type `Transaction`.
    *   May set status to `REQUIRES_MANUAL_INTERVENTION` for complex failures.

5.  **Event Publication**: 
    *   After a refund reaches a terminal state (e.g., `SUCCEEDED`, `FAILED`), invokes the `PaymentEventPublisherService` to publish relevant events (e.g., `RefundProcessed`, `RefundFailed`).

6.  **Idempotency**: 
    *   Ensures that refund requests are idempotent. If multiple requests are made to refund the same amount for the same reason against a specific payment, it should only be processed once. This can be managed by checking existing `Refund` records or using an idempotency key provided in the request.

7.  **Querying Refunds**: 
    *   Provides methods to query refund status or list refunds associated with a payment.
    *   Example: `getRefundDetails(refundId: string): Promise<Refund>`, `getRefundsForPayment(paymentId: string): Promise<Refund[]>`.

## Interactions with Other Services

*   **`PaymentGatewayIntegrationService`**: Delegates all direct communication with external payment gateways for processing refunds.
*   **`TransactionManagementService`**: Uses this service to create `Transaction` entities of type `REFUND`.
*   **`PaymentProcessingService` (or directly `Payment` entity access)**: May query or update the original `Payment` entity to reflect refunded amounts.
*   **`PaymentEventPublisherService`**: Calls this service to publish domain events related to refund status changes.
*   **Database (via ORM)**: Persists and updates `Refund` entities.

## Key Operations (Conceptual)

*   `requestRefund(params: { paymentId: string; amount: number; currency: string; reason?: string; requestedByUserId?: string; metadata?: object; idempotencyKey?: string }): Promise<Refund>`
*   `processGatewayRefundCallback(refundId: string, gatewayResponse: any): Promise<Refund>` (handles synchronous response from gateway call)
*   `handleWebhookRefundUpdate(gatewayRefundId: string, eventData: any): Promise<Refund>` (updates status based on asynchronous webhook data, often via `WebhookHandlerService`)
*   `getRefundStatus(refundId: string): Promise<RefundStatus>`

## Design Considerations

*   **Partial Refunds**: The service must correctly handle partial refunds and ensure the total refunded amount does not exceed the original payment amount.
*   **Multiple Refunds**: Support for multiple partial refunds against a single payment.
*   **Gateway Limitations**: Be aware of and handle limitations imposed by gateways regarding refund windows (e.g., some gateways only allow refunds within 60-90 days) or refund capabilities (e.g., some payment methods might not be directly refundable).
*   **Atomicity**: Refund operations involving database updates (to `Refund`, `Transaction`, `Payment` entities) and gateway calls should be handled carefully to maintain consistency. If a gateway refund succeeds but a database update fails, a reconciliation process or retry might be needed.
*   **Auditability**: All refund actions, attempts, and outcomes must be clearly logged in the `Refund` and `Transaction` entities.

The `RefundService` plays a crucial role in customer satisfaction and financial accuracy by ensuring that refund processes are handled efficiently, reliably, and transparently.
