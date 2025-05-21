# 02: `Transaction` Entity

The `Transaction` entity records each individual financial operation that occurs as part of a `Payment`. This provides a detailed audit trail of all actions taken, such as authorization, capture, sale, void, or refund attempts and their outcomes.

## Attributes

| Attribute                | Data Type                                  | Nullable | Description                                                                                                    |
| ------------------------ | ------------------------------------------ | -------- | -------------------------------------------------------------------------------------------------------------- |
| `id`                     | UUID (Primary Key)                         | No       | Unique identifier for the transaction record.                                                                  |
| `paymentId`              | UUID (Foreign Key to `Payment`)            | No       | Links this transaction to the parent `Payment` record. Indexed.                                                  |
| `type`                   | Enum (`AUTHORIZATION`, `CAPTURE`, `SALE`, `VOID`, `REFUND`, `CHARGEBACK_NOTIFICATION`, `INFO`) | No    | Type of transaction. Indexed.                                                                               |
| `gatewayTransactionId`   | String                                     | Yes      | The identifier for this specific transaction within the external payment gateway (e.g., Stripe Charge ID or Refund ID). Indexed. |
| `amount`                 | Decimal (e.g., 10,2)                       | No       | The amount of this specific transaction (e.g., amount authorized, amount captured, amount refunded).           |
| `currency`               | String (ISO 4217 code, e.g., "USD")      | No       | Currency code for the transaction amount.                                                                      |
| `status`                 | Enum (`PENDING`, `SUCCEEDED`, `FAILED`, `REQUIRES_GATEWAY_ACTION`)    | No       | Status of this individual transaction. Indexed.                                                                  |
| `gatewayResponseCode`    | String                                     | Yes      | Response code received from the payment gateway for this transaction (e.g., approval code, error code).       |
| `gatewayResponseMessage` | Text                                       | Yes      | Detailed response message from the payment gateway.                                                            |
| `processorResponseCode`  | String                                     | Yes      | Response code from the underlying card processor, if available.                                                |
| `processorResponseMessage`| Text                                       | Yes      | Detailed message from the card processor, if available.                                                        |
| `avsResponse`            | String                                     | Yes      | Address Verification System (AVS) response code, if applicable.                                                |
| `cvvResponse`            | String                                     | Yes      | Card Verification Value (CVV) response code, if applicable.                                                    |
| `metadata`               | JSONB                                      | Yes      | Additional metadata specific to this transaction (e.g., retry attempt number, webhook data snippet).           |
| `parentTransactionId`    | UUID (Foreign Key to `Transaction`, Self-referential) | Yes   | For linked transactions, e.g., a `CAPTURE` links to its `AUTHORIZATION`, or a `REFUND` to its `CAPTURE`/`SALE`. |
| `processedAt`            | Timestamp (YYYY-MM-DD HH:MM:SS Z)          | Yes      | Timestamp when the transaction was processed by the gateway.                                                   |
| `createdAt`              | Timestamp (YYYY-MM-DD HH:MM:SS Z)          | No       | Timestamp when the transaction record was created in our system.                                               |

## Enum: `TransactionType`

*   `AUTHORIZATION`: A pre-authorization of funds on a payment method.
*   `CAPTURE`: Capturing previously authorized funds.
*   `SALE`: An atomic operation that both authorizes and captures funds in a single step.
*   `VOID`: Canceling a previous `AUTHORIZATION` or an uncaptured `SALE`.
*   `REFUND`: Returning funds to the customer for a previous `CAPTURE` or `SALE`.
*   `CHARGEBACK_NOTIFICATION`: Notification of a chargeback initiated by the customer (status might be `INFO` or `REQUIRES_GATEWAY_ACTION`).
*   `INFO`: An informational record, perhaps from a webhook that doesn't fit other types but needs logging against the payment.

## Enum: `TransactionStatus`

*   `PENDING`: The transaction has been initiated but is not yet confirmed by the gateway.
*   `SUCCEEDED`: The transaction was successfully processed by the gateway.
*   `FAILED`: The transaction was declined or failed at the gateway.
*   `REQUIRES_GATEWAY_ACTION`: The transaction requires further action or confirmation at the gateway (e.g., for asynchronous processes or disputes).

## Relationships

*   **Belongs to `Payment`**: Each transaction is part of a single `Payment`.
*   **Can optionally belong to `Transaction` (Parent Transaction)**: Facilitates linking related transactions, like a capture to its authorization.

## Indexes

*   Primary key on `id`.
*   On `paymentId` for quick retrieval of all transactions for a payment.
*   On `gatewayTransactionId` for correlation with gateway records.
*   On `type` and `status` for querying specific types/statuses of transactions.
*   Consider a composite index on `(paymentId, type, status)`.

## Considerations

*   **Granularity**: This entity provides fine-grained details about each step in the payment lifecycle.
*   **Gateway Specifics**: `gatewayResponseCode`, `gatewayResponseMessage`, `processorResponseCode`, and `processorResponseMessage` are crucial for debugging and understanding gateway behavior. These can vary significantly between gateways.
*   **Asynchronous Updates**: The status of a transaction can be updated asynchronously via webhooks from the payment gateway.
*   **Data Integrity**: Ensuring the sum of `CAPTURE` or `SALE` transactions (minus `REFUND` transactions) matches the final paid amount in the parent `Payment` record is important for reconciliation.

This `Transaction` entity is fundamental for a detailed audit trail and operational management of the payment process.
