# 06: `WebhookHandlerService`

The `WebhookHandlerService` is responsible for the intake, verification, and initial processing or delegation of asynchronous webhook events received from external payment gateways. Webhooks are essential for keeping the Payment Service's state consistent with the actual status of payments, refunds, and other events occurring at the gateway.

## Responsibilities

1.  **Webhook Reception**: 
    *   Provides the HTTP endpoint(s) that payment gateways will call to deliver webhook events.
    *   Receives raw webhook payloads and headers.

2.  **Webhook Event Logging**: 
    *   Immediately logs the incoming webhook event details (gateway, event ID, type, full payload, relevant headers) into the `WebhookEventLog` entity. This ensures that no event is lost, even if subsequent processing fails.

3.  **Signature Verification**: 
    *   Critically important for security. Verifies the signature of each incoming webhook event using the appropriate secret key for the specific gateway (obtained via `ConfigurationService`).
    *   Rejects and logs any event with an invalid signature to prevent processing of fraudulent or tampered events.
    *   The actual verification logic might be delegated to the specific `PaymentGatewayIntegrationService` implementation (e.g., `stripeAdapter.verifyWebhookSignature(...)`).
    *   Updates the `isSignatureVerified` field in the `WebhookEventLog`.

4.  **Idempotency Check (Duplicate Event Handling)**: 
    *   Checks the `WebhookEventLog` (using `gatewayEventId` and `gateway`) to see if the event has already been received and processed (or is currently being processed). 
    *   If it's a duplicate, it might be ignored or acknowledged with a success response to the gateway without reprocessing, updating the log status accordingly.

5.  **Event Parsing and Delegation**: 
    *   Parses the verified webhook payload to understand the event type and extract relevant data.
    *   Based on the `eventType` (e.g., `payment_intent.succeeded`, `charge.refunded`, `customer.subscription.updated`), delegates the event to the appropriate internal service or method for business logic processing.
        *   For example, a `payment_intent.succeeded` event might be routed to a method in `PaymentProcessingService` to update the `Payment` status.
        *   A `charge.refund.updated` event might be routed to `RefundService`.
        *   A `customer.payment_method.attached` event might be routed to `PaymentMethodService`.

6.  **Acknowledgement Response**: 
    *   Sends an appropriate HTTP response to the payment gateway to acknowledge receipt of the webhook (typically a `200 OK`). This should be done relatively quickly, even if the full business logic processing is handled asynchronously, to prevent the gateway from retrying unnecessarily.

7.  **Error Handling for Initial Processing**: 
    *   Handles errors during the initial phases (logging, verification, basic parsing).
    *   Updates the `processingStatus` and `processingNotes` in the `WebhookEventLog` if initial handling fails.

## Interactions with Other Services

*   **`WebhookEventLog` Entity/Service**: For logging all incoming events immediately.
*   **`PaymentGatewayIntegrationService` (and its implementations)**: For webhook signature verification logic specific to each gateway.
*   **`ConfigurationService`**: To fetch webhook signing secrets for different gateways.
*   **`PaymentProcessingService`**: Delegates events related to payment status updates.
*   **`RefundService`**: Delegates events related to refund status updates.
*   **`PaymentMethodService`**: Delegates events related to payment method changes (e.g., card expiry updates if sent by webhook).
*   **`TransactionManagementService`**: May be called by the above services to update or create `Transaction` records based on webhook data.
*   **Message Queue (Optional)**: For complex or time-consuming business logic triggered by a webhook, this service might place the validated event onto an internal message queue for asynchronous processing by another worker/service. This allows the webhook endpoint to respond quickly to the gateway.

## Key Operations (Conceptual)

*   `handleIncomingWebhook(gatewayName: string, requestHeaders: any, rawBody: string | Buffer): Promise<void>` (This is the main entry point, typically called by an API controller).

Internal steps within `handleIncomingWebhook` would include:
1.  Log the event.
2.  Verify signature (using specific gateway adapter).
3.  Check for duplicates.
4.  Parse event type.
5.  Delegate to business logic handler based on event type.
6.  Update `WebhookEventLog` with processing status.

## Design Considerations

*   **Security**: Signature verification is non-negotiable. Webhook signing secrets must be protected.
*   **Reliability**: Logging events first ensures no data loss. Design for idempotent processing of events.
*   **Performance**: Webhook endpoints should respond quickly to gateways. If processing is lengthy, use a background queue.
*   **Scalability**: The endpoint must handle bursts of webhooks, especially during peak times or gateway incidents.
*   **Testability**: Mocking gateway requests and verifying internal delegation and state changes is important.
*   **Specific Gateway Logic**: Each gateway has its own set of event types and payload structures. The delegation logic needs to be aware of these specifics.

Failure to correctly and securely handle webhooks can lead to inconsistent data, security vulnerabilities, and a poor user experience. The `WebhookHandlerService` is therefore a critical component for maintaining data integrity and reliability.
