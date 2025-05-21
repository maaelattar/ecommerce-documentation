# 03: `PaymentMethod` Entity

The `PaymentMethod` entity stores information about a customer's saved payment methods. A key design consideration for this entity is PCI DSS compliance, which means **never storing raw sensitive payment information** like full card numbers or CVV codes. Instead, it relies on tokens provided by payment gateways.

## Attributes

| Attribute             | Data Type                               | Nullable | Description                                                                                                 |
| --------------------- | --------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| `id`                  | UUID (Primary Key)                      | No       | Unique identifier for the payment method record.                                                            |
| `userId`              | UUID / String                           | No       | Identifier for the user this payment method belongs to (from the User Service). Indexed.                      |
| `type`                | Enum (`CARD`, `PAYPAL`, `APPLE_PAY`, `GOOGLE_PAY`, `BANK_TRANSFER`) | No    | Type of payment method.                                                                                     |
| `gateway`             | String (e.g., "STRIPE", "PAYPAL")     | No       | The payment gateway that tokenized and stores the actual payment details.                                   |
| `gatewayPaymentMethodId` | String                                 | No       | The token or identifier provided by the payment gateway for this specific payment method (e.g., Stripe `pm_xxx` or `card_xxx`). Indexed. |
| `isDefault`           | Boolean                                 | No       | Indicates if this is the default payment method for the user. Default `false`.                              |
| `status`              | Enum (`ACTIVE`, `INACTIVE`, `EXPIRED`, `FAILED_VALIDATION`) | No    | Status of the payment method. Default `ACTIVE`.                                                          |
| `cardBrand`           | String (e.g., "Visa", "Mastercard", "Amex") | Yes      | Card brand, if the type is `CARD`.                                                                          |
| `cardLastFour`        | String (4 digits)                       | Yes      | Last four digits of the card number, if the type is `CARD`.                                                 |
| `cardExpiryMonth`     | Integer (1-12)                          | Yes      | Card expiry month (MM), if the type is `CARD`.                                                              |
| `cardExpiryYear`      | Integer (YYYY)                          | Yes      | Card expiry year (YYYY), if the type is `CARD`.                                                             |
| `billingName`         | String                                  | Yes      | Name on the card or payment method.                                                                         |
| `billingAddressLine1` | String                                  | Yes      | Billing address line 1.                                                                                     |
| `billingAddressLine2` | String                                  | Yes      | Billing address line 2.                                                                                     |
| `billingCity`         | String                                  | Yes      | Billing address city.                                                                                       |
| `billingState`        | String                                  | Yes      | Billing address state/province.                                                                             |
| `billingPostalCode`   | String                                  | Yes      | Billing address postal code.                                                                                |
| `billingCountry`      | String (ISO 3166-1 alpha-2 code)        | Yes      | Billing address country code.                                                                               |
| `fingerprint`         | String                                  | Yes      | A unique fingerprint provided by some gateways for card details, helps in identifying duplicate cards.        |
| `metadata`            | JSONB                                   | Yes      | Additional metadata from the gateway or for internal use (e.g., gateway-specific customer ID if needed here). |
| `createdAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the payment method record was created.                                                       |
| `updatedAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the payment method record was last updated.                                                  |
| `lastValidatedAt`     | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | Yes      | Timestamp when the payment method was last successfully validated with the gateway (if applicable).       |

## Enum: `PaymentMethodType`

*   `CARD`: Credit or debit card.
*   `PAYPAL`: PayPal account.
*   `APPLE_PAY`: Apple Pay.
*   `GOOGLE_PAY`: Google Pay.
*   `BANK_TRANSFER`: ACH, SEPA, or other bank transfer methods (may have more specific subtypes).

## Enum: `PaymentMethodStatus`

*   `ACTIVE`: The payment method is active and can be used.
*   `INACTIVE`: The payment method has been deactivated by the user or system.
*   `EXPIRED`: The payment method (e.g., card) has expired.
*   `FAILED_VALIDATION`: The payment method failed validation with the gateway (e.g., card declined during verification).

## Relationships

*   **Has many `Payment` records**: One payment method can be used for multiple payments.
*   **Belongs to a User**: (Implicitly via `userId`).

## Indexes

*   Primary key on `id`.
*   On `userId` to list payment methods for a user.
*   On `gatewayPaymentMethodId` (and potentially `gateway`) for uniqueness and gateway correlation.
*   `userId` and `isDefault` to quickly find a user's default payment method.

## Security and PCI DSS Compliance

*   **No Sensitive Data Storage**: This table **MUST NOT** store full PAN (Primary Account Number), CVV, or other sensitive cardholder data.
*   **Tokenization**: `gatewayPaymentMethodId` is the cornerstone of security. It's a token provided by the PCI-compliant payment gateway that represents the actual card details stored securely by the gateway.
*   **Display Purposes Only**: Fields like `cardBrand`, `cardLastFour`, `cardExpiryMonth`, `cardExpiryYear` are stored for display to the user and for identification. They are not sufficient to make a transaction without the gateway token.
*   **API Security**: Endpoints for managing payment methods must be highly secure, with strong authentication and authorization.
*   **Audit Trails**: Changes to payment methods should be audited.

## Considerations

*   **Gateway Agnostic vs. Specific**: While aiming for a somewhat gateway-agnostic model, some fields might be more relevant to specific gateways. `metadata` can store gateway-specific details.
*   **Synchronization**: The status of a payment method (e.g., `EXPIRED`) might need to be updated based on gateway feedback or scheduled checks.
*   **User Experience**: Provide clear options for users to add, remove, and set a default payment method.

This `PaymentMethod` entity design prioritizes security and compliance while providing the necessary functionality for managing customer payment options.
