# 04: `Refund` Entity

The `Refund` entity represents a request to return funds to a customer for a previously completed payment. It tracks the amount, reason, status, and linkage to the original payment and any gateway-specific refund transaction identifiers.

## Attributes

| Attribute             | Data Type                               | Nullable | Description                                                                                                |
| --------------------- | --------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| `id`                  | UUID (Primary Key)                      | No       | Unique identifier for the refund record.                                                                   |
| `paymentId`           | UUID (Foreign Key to `Payment`)         | No       | Identifier for the original `Payment` this refund is associated with. Indexed.                             |
| `transactionId`       | UUID (Foreign Key to `Transaction`)     | Yes      | Identifier for the specific `Transaction` (e.g., a `CAPTURE` or `SALE`) that is being refunded. Indexed.    |
| `amount`              | Decimal (e.g., 10,2)                    | No       | The amount to be refunded.                                                                                 |
| `currency`            | String (ISO 4217 code, e.g., "USD")   | No       | Currency code for the refund amount (must match the original payment currency).                            |
| `reason`              | Text                                    | Yes      | Reason for the refund (e.g., "Product returned", "Order canceled", "Customer dissatisfaction").             |
| `status`              | Enum (`PENDING`, `PROCESSING`, `SUCCEEDED`, `FAILED`, `REQUIRES_MANUAL_INTERVENTION`) | No | Current status of the refund. Indexed.                                                                |
| `gatewayRefundId`     | String                                  | Yes      | The identifier for this refund within the external payment gateway (e.g., Stripe Refund ID `re_xxx`). Indexed. |
| `gatewayStatus`       | String                                  | Yes      | The status of the refund as reported by the payment gateway (can be more granular than our internal `status`). |
| `gatewayFailureCode`  | String                                  | Yes      | If the refund failed at the gateway, the error code provided.                                              |
| `gatewayFailureMessage`| Text                                   | Yes      | If the refund failed at the gateway, the detailed error message.                                           |
| `metadata`            | JSONB                                   | Yes      | Additional metadata related to the refund (e.g., initiated by admin ID, notes).                            |
| `requestedByUserId`   | UUID / String                           | Yes      | ID of the user or system component that requested the refund.                                              |
| `processedAt`         | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | Yes      | Timestamp when the refund was successfully processed by the gateway.                                       |
| `createdAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the refund record was created.                                                              |
| `updatedAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the refund record was last updated.                                                         |

## Enum: `RefundStatus`

*   `PENDING`: The refund has been requested but not yet processed by the gateway.
*   `PROCESSING`: The refund is currently being processed by the payment gateway.
*   `SUCCEEDED`: The refund was successfully processed, and funds are being returned to the customer.
*   `FAILED`: The refund attempt failed at the payment gateway.
*   `REQUIRES_MANUAL_INTERVENTION`: The refund requires manual review or action (e.g., due to gateway issues, complex conditions).

## Relationships

*   **Belongs to `Payment`**: Each refund is associated with one original `Payment`.
*   **Optionally belongs to `Transaction`**: A refund can be linked to a specific successful transaction (like a `CAPTURE` or `SALE`) of the parent `Payment`.
*   A `Refund` record might also result in a new `Transaction` record of type `REFUND` being created, linked to this `Refund` entity or directly to the `Payment`. The `gatewayRefundId` on this entity might be the same as the `gatewayTransactionId` on that `REFUND` type `Transaction`.

## Indexes

*   Primary key on `id`.
*   On `paymentId` to list all refunds for a specific payment.
*   On `transactionId` if refunds are often queried by the original transaction being refunded.
*   On `status` to query refunds by their current state.
*   On `gatewayRefundId` for correlation with gateway records.

## Considerations

*   **Partial Refunds**: The system should support partial refunds (refunding less than the original payment amount).
*   **Multiple Refunds**: A single payment might have multiple partial refunds, up to the total original payment amount.
*   **Idempotency**: Refund requests should be idempotent. If a refund for a specific amount and reason on a payment is requested multiple times, it should only be processed once.
*   **Gateway Limitations**: Different payment gateways have different rules and time limits for processing refunds.
*   **Reconciliation**: Refund data is critical for financial reconciliation.
*   **State Management**: The `status` of the refund will be updated based on responses from the payment gateway, potentially via webhooks.

This `Refund` entity allows for clear tracking and management of all refund operations, ensuring financial accuracy and providing a good audit trail.
