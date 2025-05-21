# 01: `Payment` Entity

The `Payment` entity represents an overall payment attempt or intent associated with an order or a specific charge. It acts as a central record for the financial aspect of an order, linking various transactions and status updates.

## Attributes

| Attribute             | Data Type                               | Nullable | Description                                                                                                 |
| --------------------- | --------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| `id`                  | UUID (Primary Key)                      | No       | Unique identifier for the payment record.                                                                     |
| `orderId`             | UUID / String                           | No       | Identifier for the order this payment is associated with (from the Order Service). Indexed.                 |
| `userId`              | UUID / String                           | Yes      | Identifier for the user making the payment (from the User Service). Indexed. May be null for guest checkouts. |
| `amount`              | Decimal (e.g., 10,2)                    | No       | The total amount to be paid.                                                                                |
| `currency`            | String (ISO 4217 code, e.g., "USD")   | No       | Currency code for the payment amount.                                                                       |
| `status`              | Enum (`PENDING`, `PROCESSING`, `SUCCEEDED`, `FAILED`, `REQUIRES_ACTION`, `CANCELED`) | No       | Current status of the payment. Indexed.                                                                  |
| `paymentGateway`      | String (e.g., "STRIPE", "PAYPAL")     | Yes      | Name of the payment gateway used or intended for this payment.                                              |
| `gatewayPaymentIntentId`| String                                  | Yes      | The identifier for this payment intent within the external payment gateway (e.g., Stripe PaymentIntent ID). Indexed. |
| `description`         | Text                                    | Yes      | A brief description or memo for the payment (e.g., "Payment for Order #12345").                               |
| `metadata`            | JSONB                                   | Yes      | Any additional metadata related to the payment (e.g., specific instructions, source IP).                  |
| `paymentMethodId`     | UUID (Foreign Key to `PaymentMethod`)   | Yes      | Reference to the payment method used, if applicable (e.g., for saved card payments).                         |
| `lastErrorMessage`    | Text                                    | Yes      | Stores the last error message if the payment failed or encountered issues.                                  |
| `createdAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the payment record was created.                                                              |
| `updatedAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the payment record was last updated.                                                         |
| `expiresAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | Yes      | Timestamp when this payment intent or authorization might expire (e.g., for pre-authorized payments).       |

## Enum: `PaymentStatus`

*   `PENDING`: The payment has been initiated but not yet processed.
*   `PROCESSING`: The payment is currently being processed by the gateway.
*   `SUCCEEDED`: The payment was successful.
*   `FAILED`: The payment failed.
*   `REQUIRES_ACTION`: The payment requires additional action from the customer (e.g., 3D Secure authentication).
*   `CANCELED`: The payment was explicitly canceled before completion.

## Relationships

*   **Has many `Transaction` records**: One `Payment` can have multiple associated `Transaction` records (e.g., an authorization transaction followed by a capture transaction, or multiple refund transactions).
*   **Belongs to `PaymentMethod` (Optional)**: A `Payment` may be associated with a specific `PaymentMethod` if a stored payment method was used.

## Indexes

*   Primary key on `id`.
*   On `orderId` for quick lookup of payments for a specific order.
*   On `userId` for retrieving payments made by a specific user.
*   On `status` to efficiently query payments by their current state.
*   On `gatewayPaymentIntentId` for quick correlation with gateway records.
*   Consider a composite index on `(status, createdAt)` for querying pending/failed payments over time.

## Considerations

*   **Idempotency**: The combination of `orderId` and a unique request identifier (passed in `metadata` or a dedicated field if needed) can be used to ensure idempotency when initiating payments.
*   **Security**: While this entity itself doesn't store raw payment card data, `gatewayPaymentIntentId` can be sensitive if it provides direct access to payment details in the gateway. Access controls should be strict.
*   The `status` field is critical and will be updated based on gateway responses and webhook events.

This `Payment` entity provides a comprehensive overview of each payment attempt, facilitating tracking, management, and integration with other services.
