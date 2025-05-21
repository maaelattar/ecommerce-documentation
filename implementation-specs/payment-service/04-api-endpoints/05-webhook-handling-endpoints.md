# 05: Webhook Handling Endpoints

These endpoints are not called by end-users or typical client applications but are targeted by external payment gateways to send asynchronous notifications about events related to payments, refunds, disputes, payment methods, etc. Securely and reliably handling these webhooks is critical for maintaining data consistency.

## 1. Generic Gateway Webhook Receiver

It's common to have a primary webhook endpoint per gateway, or a generic one that can route based on a path parameter or payload content if dealing with multiple gateways that have distinct webhook structures or security mechanisms.

*   **Endpoint**: `POST /v1/webhooks/{gatewayName}`
    *   Example: `POST /v1/webhooks/stripe`, `POST /v1/webhooks/paypal`
*   **Purpose**: To receive all incoming webhook events from a specific payment gateway.
*   **Authentication**: Relies on signature verification. The endpoint itself might be open, but the payload must be verifiable.
*   **Request Body**: 
    *   The structure is entirely dependent on the payment gateway and the specific event type.
    *   The service expects a raw JSON payload from the gateway.
*   **Headers**: 
    *   Gateway-specific signature header(s) are crucial (e.g., `Stripe-Signature` for Stripe, `Paypal-Transmission-Sig` for PayPal).
    *   Other headers like `User-Agent` (to identify the gateway) or idempotency keys from the gateway might also be present.
*   **Success Response (200 OK or 202 Accepted)**:
    *   A `200 OK` (or `202 Accepted`) response should be sent promptly to the gateway to acknowledge receipt of the event. 
    *   The response body is typically empty or a simple `{ "received": true }`.
    *   **Important**: The actual business logic processing of the webhook should often be handled asynchronously (e.g., after validating and queuing the event) to ensure the endpoint can respond quickly to the gateway. Failure to respond in a timely manner can lead to the gateway retrying the webhook, potentially causing duplicate processing if not handled carefully.
*   **Error Responses (sent to the gateway)**:
    *   `400 Bad Request`: If the payload is malformed, a required header is missing, or the signature verification fails outright due to a bad secret or algorithm mismatch (though signature failures specifically might also be logged and a `200` returned to prevent a compromised endpoint from revealing too much).
    *   `401 Unauthorized / 403 Forbidden`: If signature verification fails (depending on strategy - some prefer to still return 200 to avoid information leakage and log the failure internally).
    *   `500 Internal Server Error`: If an unexpected error occurs during the very initial intake (e.g., failure to write to the `WebhookEventLog` if that's the first step).

## Processing Logic (Handled by `WebhookHandlerService`)

Upon receiving a request at this endpoint, the `WebhookHandlerService` performs the following steps (as detailed in `03-core-service-components/06-webhook-handler-service.md`):

1.  **Immediate Logging**: Logs the raw event to `WebhookEventLog`.
2.  **Signature Verification**: Verifies the webhook signature using the appropriate gateway secret. If verification fails, the event is marked as unverified in the log, and processing typically stops. A `200 OK` might still be returned to the gateway to prevent it from continuously retrying and to avoid leaking information about signature validation failure, while an internal alert is raised.
3.  **Idempotency Check**: Checks if the `gatewayEventId` has been processed before.
4.  **Parsing and Delegation**: Parses the event type and payload, then delegates to the relevant business logic service (e.g., `PaymentProcessingService`, `RefundService`, `PaymentMethodService`).
5.  **Acknowledgement**: Sends `200 OK` to the gateway.

## Security Considerations

*   **Signature Verification**: This is the most critical security aspect. Each gateway has its own mechanism (e.g., HMAC-SHA256 for Stripe). Secrets used for verification must be stored securely and differ per gateway.
*   **HTTPS**: Webhook endpoints must use HTTPS.
*   **IP Whitelisting**: If the gateway publishes a list of IP addresses from which webhooks will originate, consider whitelisting these IPs at the firewall or load balancer level as an additional layer of security (though signature verification is primary).
*   **Logging Unverified Attempts**: Log all incoming webhook attempts, including those that fail signature verification, for security monitoring.
*   **Principle of Least Privilege**: The code handling webhooks should only have the permissions necessary to process them.

This endpoint structure ensures that the Payment Service can reliably and securely receive and process asynchronous updates from various payment providers, which is essential for maintaining accurate and up-to-date payment statuses.
