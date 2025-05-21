# 01: `PaymentProcessingService`

The `PaymentProcessingService` is a central orchestrator within the Payment Service. It is responsible for managing the end-to-end lifecycle of a payment, from initiation to final settlement or failure. It coordinates interactions between various other components, such as the `PaymentGatewayIntegrationService`, `TransactionManagementService`, and `PaymentEventPublisherService`.

## Responsibilities

1.  **Payment Initiation**: 
    *   Receives requests to create and process payments (e.g., from an API controller when a user checks out).
    *   Validates the payment request data (amount, currency, order details, user information).
    *   Creates a `Payment` entity with an initial status (e.g., `PENDING`).

2.  **Gateway Interaction Orchestration**: 
    *   Determines the appropriate payment gateway based on the request or configuration.
    *   Invokes the `PaymentGatewayIntegrationService` to:
        *   Create a payment intent or equivalent construct with the chosen gateway.
        *   Process the actual charge using a provided payment method (token) or by redirecting the user for gateway-hosted payment pages.

3.  **State Management**: 
    *   Updates the status of the `Payment` entity based on the outcomes of gateway operations (e.g., `PROCESSING`, `SUCCEEDED`, `FAILED`, `REQUIRES_ACTION`).
    *   Coordinates with the `TransactionManagementService` to record detailed `Transaction` entries for each step (e.g., authorization, capture, sale attempt).

4.  **Handling Different Payment Flows**: 
    *   Manages various payment scenarios:
        *   Direct charges (authorize and capture in one step).
        *   Separate authorization and capture.
        *   Payments requiring customer redirection (e.g., 3D Secure, PayPal checkout).
        *   Payments using saved payment methods (customer-initiated transactions - CIT) vs. merchant-initiated transactions (MIT) if applicable.

5.  **Error Handling and Retries**: 
    *   Implements logic for handling errors returned by the payment gateway.
    *   May implement retry mechanisms for transient failures, adhering to gateway best practices (e.g., not retrying hard declines).
    *   Logs detailed error information in the `Payment` and `Transaction` entities.

6.  **Event Publication**: 
    *   After significant status changes (e.g., payment success, failure), invokes the `PaymentEventPublisherService` to publish relevant events (e.g., `PaymentSucceeded`, `PaymentFailed`).

7.  **Idempotency**: 
    *   Ensures that payment initiation requests are idempotent to prevent duplicate payments for the same order/intent, possibly by checking for existing `Payment` records with a matching idempotency key or order ID within a certain timeframe.

## Interactions with Other Services

*   **`PaymentGatewayIntegrationService`**: Delegates all direct communication with external payment gateways to this service (or its concrete implementations like `StripeIntegrationService`).
*   **`TransactionManagementService`**: Uses this service to create and update `Transaction` entities that provide an audit trail for each payment operation.
*   **`PaymentMethodService`**: May interact with this service to retrieve details of a saved payment method if one is being used.
*   **`PaymentEventPublisherService`**: Calls this service to publish domain events after payment processing is complete or has reached a terminal state.
*   **`FraudDetectionService`**: May call this service before processing a payment to get a risk assessment. The outcome might influence whether the payment is processed or requires further review.
*   **Database (via ORM)**: Persists and updates `Payment` entities.

## Key Operations (Conceptual)

*   `initiatePayment(orderId: string, userId: string, amount: number, currency: string, paymentMethodToken?: string, metadata?: object): Promise<Payment>`
*   `processPayment(paymentId: string, paymentDetails: any): Promise<Payment>` (handles actual charge based on intent)
*   `handleGatewayResponse(paymentId: string, gatewayResponse: any): Promise<Payment>` (updates status based on synchronous response)
*   `handleWebhookPaymentUpdate(gatewayPaymentIntentId: string, eventData: any): Promise<Payment>` (updates status based on asynchronous webhook data, often delegated to `WebhookHandlerService` which then calls this or a similar internal method).
*   `capturePreAuthorizedPayment(paymentId: string, amountToCapture?: number): Promise<Payment>`
*   `cancelPayment(paymentId: string, reason?: string): Promise<Payment>`

## Design Considerations

*   **Statelessness**: This service should ideally be stateless, with all persistent state managed in the database (`Payment` and `Transaction` entities).
*   **Clarity of Flows**: Given the complexity of payment flows, the logic within this service must be clear, well-documented, and thoroughly tested.
*   **Resilience**: Must be resilient to failures in downstream services (e.g., gateway timeouts) and handle them gracefully.

The `PaymentProcessingService` is the engine of the Payment Service, ensuring that all payments are handled consistently, securely, and reliably.
