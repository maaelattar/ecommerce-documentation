# 06: `WebhookEventLog` Entity

The `WebhookEventLog` entity is responsible for storing a record of every incoming webhook event received from external payment gateways. This log is crucial for auditing, debugging asynchronous payment updates, ensuring reliability, and re-processing events if necessary.

## Attributes

| Attribute             | Data Type                               | Nullable | Description                                                                                                   |
| --------------------- | --------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- |
| `id`                  | UUID (Primary Key)                      | No       | Unique identifier for the webhook event log entry.                                                            |
| `gateway`             | String (e.g., "STRIPE", "PAYPAL")     | No       | The payment gateway that sent the webhook. Indexed.                                                           |
| `gatewayEventId`      | String                                  | No       | The unique identifier for the event provided by the gateway (e.g., Stripe `evt_xxx`). Indexed.                |
| `eventType`           | String                                  | No       | The type of event received from the gateway (e.g., `payment_intent.succeeded`, `charge.refunded`, `checkout.session.completed`). Indexed. |
| `payload`             | JSONB                                   | No       | The full JSON payload of the webhook event as received from the gateway.                                        |
| `headers`             | JSONB                                   | Yes      | Relevant HTTP headers received with the webhook (e.g., signature header for verification, idempotency key).   |
| `processingStatus`    | Enum (`RECEIVED`, `PROCESSING`, `COMPLETED`, `FAILED`, `IGNORED`) | No | Status of our internal processing of this event. Indexed.                                                      |
| `processingNotes`     | Text                                    | Yes      | Notes or error messages related to the processing of this event (e.g., "Payment record updated", "No corresponding payment found"). |
| `relatedPaymentId`    | UUID (Foreign Key to `Payment`)         | Yes      | If the event was successfully associated with an internal `Payment` record. Indexed.                          |
| `relatedTransactionId`| UUID (Foreign Key to `Transaction`)     | Yes      | If the event was successfully associated with an internal `Transaction` record.                               |
| `isSignatureVerified` | Boolean                                 | No       | Indicates if the webhook signature was successfully verified. Crucial for security.                           |
| `receivedAt`          | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the webhook was received by our service.                                                       |
| `processedAt`         | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | Yes      | Timestamp when the processing of this webhook event was completed or last attempted.                        |

## Enum: `WebhookProcessingStatus`

*   `RECEIVED`: The webhook has been received and logged but not yet processed.
*   `PROCESSING`: The webhook is currently being processed by a handler.
*   `COMPLETED`: The webhook was successfully processed, and relevant actions were taken (e.g., payment status updated).
*   `FAILED`: An error occurred during the processing of the webhook.
*   `IGNORED`: The webhook event was intentionally ignored (e.g., it was a duplicate, or an event type we don't handle).

## Relationships

*   Optionally relates to `Payment` (`relatedPaymentId`).
*   Optionally relates to `Transaction` (`relatedTransactionId`).

## Indexes

*   Primary key on `id`.
*   Unique composite index on (`gateway`, `gatewayEventId`) to prevent duplicate logging of the same event.
*   On `eventType` and `gateway` for querying specific types of events from a gateway.
*   On `processingStatus` to find events that need processing or have failed.
*   On `relatedPaymentId` to find all webhook events associated with a specific payment.
*   On `receivedAt` for time-based queries.

## Purpose and Usage

*   **Auditing**: Provides a complete audit trail of all asynchronous notifications received from payment gateways.
*   **Reliability**: Ensures that no gateway notification is lost. If processing fails, the event is still logged and can be retried or investigated.
*   **Debugging**: Essential for troubleshooting issues with payment status updates, refunds, or other gateway-driven processes. The raw `payload` is invaluable here.
*   **Idempotency**: By checking `gatewayEventId`, webhook handlers can ensure that an event is not processed multiple times if the gateway retries sending it.
*   **Security**: Storing `isSignatureVerified` confirms that the webhook was authenticated, preventing processing of forged events.

## Considerations

*   **Storage**: Webhook payloads can be large. Consider retention policies or archiving older logs if storage becomes a concern. However, for financial systems, a long retention might be required for audit purposes.
*   **Error Handling**: Robust error handling is needed in the webhook processing logic. Failed events should be clearly marked and potentially trigger alerts.
*   **Retry Mechanisms**: For transient processing failures, a retry mechanism (e.g., using a background job queue) might be implemented, which would update the `processingStatus` and `processingNotes`.
*   **Order of Events**: Gateways do not always guarantee the order of webhook delivery. Processing logic should be resilient to this, often by relying on the event's timestamp or specific event properties rather than assuming a strict sequence.

This `WebhookEventLog` entity is a critical component for building a reliable and auditable payment system that depends on asynchronous communication with external gateways.
