# 06: Payment Gateways Integration (e.g., Stripe, PayPal)

Integration with external payment gateways is the cornerstone of the Payment Service's functionality. These gateways are third-party services that securely process electronic payments, handle sensitive cardholder data, and manage compliance (like PCI DSS) for the actual transaction processing.

## Key Aspects of Integration

This integration is primarily managed by the `PaymentGatewayIntegrationService` and its concrete implementations (e.g., `StripeIntegrationService`, `PayPalIntegrationService`).

1.  **API Communication**: 
    *   The Payment Service communicates with gateways via their respective HTTP APIs.
    *   All communication **must** be over HTTPS.
    *   Requests include creating payment intents, charges, customers, payment methods (tokens), processing refunds, etc.
    *   Responses from the gateway provide success/failure status, transaction IDs, error codes, and other relevant data.

2.  **Authentication**: 
    *   Each gateway requires authentication, typically using API keys (secret keys).
    *   These keys are highly sensitive and **must** be stored securely (e.g., using a secrets management system like HashiCorp Vault or AWS Secrets Manager) and injected into the Payment Service as environment variables or through a secure configuration mechanism.
    *   Keys should never be hardcoded in the application.
    *   Different keys are usually provided for test/sandbox environments and live/production environments.

3.  **Client-Side SDKs (for PCI DSS Compliance)**:
    *   For collecting sensitive payment information (e.g., credit card numbers, CVV), direct integration with the gateway's client-side SDKs (e.g., Stripe.js, PayPal JavaScript SDK) is essential.
    *   These SDKs ensure that sensitive data is sent directly from the user's browser/client to the gateway's servers, tokenized, and then a non-sensitive token (e.g., `payment_method_id`, `source_token`) is returned to the client.
    *   The client then sends this token to the Payment Service backend, which uses it to process the payment via server-to-server API calls to the gateway.
    *   This significantly reduces the PCI DSS scope for the e-commerce platform, as its backend systems never handle raw cardholder data.

4.  **Tokenization**: 
    *   **Payment Method Tokens**: When a user enters their card details, the gateway SDK tokenizes it into a temporary token (source token) for a single charge or a more permanent payment method token if the card is to be saved.
    *   **Customer Tokens**: Gateways often allow creating "Customer" objects to store multiple payment methods and other details. The Payment Service stores the `gatewayCustomerId` (as in `CustomerGatewayToken` entity) to interact with these gateway customer profiles.

5.  **Webhook Handling**: 
    *   Gateways use webhooks to send asynchronous notifications about events that occur after the initial API interaction (e.g., payment success for asynchronous methods, disputes, refund status updates, subscription renewals).
    *   The Payment Service must expose secure webhook endpoints (`04-api-endpoints/05-webhook-handling-endpoints.md`) and verify the authenticity of these webhooks (usually via signature verification using a webhook signing secret provided by the gateway).

6.  **Idempotency**: 
    *   Gateway APIs often support idempotency keys for mutable requests (e.g., creating a charge or refund). The Payment Service should generate and send these keys to prevent accidental duplicate operations due to network retries.

7.  **Error Handling**: 
    *   Gateway APIs return a wide range of error codes and messages.
    *   The `PaymentGatewayIntegrationService` must parse these responses, map them to internal error representations if needed, and provide sufficient detail for logging and potential user feedback.
    *   Distinguish between retryable errors (e.g., temporary network issue) and non-retryable errors (e.g., card declined, invalid API key).

8.  **Specific Gateway Features**: 
    *   Each gateway has unique features, APIs, and terminology (e.g., Stripe's PaymentIntents, Charges, Sources, PaymentMethods; PayPal's Orders API, Subscriptions).
    *   The specific adapter (e.g., `StripeIntegrationService`) handles these nuances.
    *   Features like 3D Secure, Apple Pay, Google Pay, local payment methods (e.g., iDEAL, SEPA Direct Debit) require specific integration patterns with each gateway.

9.  **Sandbox/Test Environments**: 
    *   All gateways provide sandbox or test environments with test API keys and test card numbers.
    *   Thorough testing of all payment flows, including success, failure, and edge cases, must be performed in these test environments before going live.

## Data Exchanged

*   **To Gateway**: Order amount, currency, description, customer information (name, email, address if needed by gateway for fraud or Level 2/3 data), payment method tokens, gateway customer IDs, return URLs.
*   **From Gateway**: Transaction IDs, payment intent IDs, status (success, failed, pending), error codes/messages, client secrets (for SDKs), AVS/CVV responses, fraud scores (if built-in), webhook event payloads.

## Security & Compliance

*   **PCI DSS**: The primary driver for how integration is structured (client-side tokenization).
*   **API Key Security**: Critical.
*   **Webhook Security**: Signature verification is mandatory.
*   **Data Privacy**: Only send necessary PII to gateways and understand their data handling policies.

Successful and secure integration with payment gateways is fundamental to the Payment Service's operation. This requires careful implementation of API interactions, robust error handling, and adherence to security best practices dictated by the gateways and industry standards.
