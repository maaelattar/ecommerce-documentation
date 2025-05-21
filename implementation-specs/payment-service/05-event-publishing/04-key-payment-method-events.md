# 04: Key Payment Method Events

This document outlines events related to the management of customer payment methods within the Payment Service. These events are crucial for keeping other services, particularly the User Service or a dedicated Profile Service, informed about changes to a user's available payment options. Events are published to a RabbitMQ topic exchange (e.g., `payment.events` or `customermanagement.events`) and use the `StandardMessageEnvelope`.

## 1. `PaymentMethodAddedEvent`

*   **Routing Key:** `paymentmethod.added.v1` (or a more specific key like `customer.paymentmethod.added.v1`)
*   **Trigger:** Published when a new payment method (e.g., credit card, bank account link) is successfully added and tokenized/stored for a user.
*   **Purpose:**
    *   Allows the User Service/Profile Service to update its record of the user's available payment methods.
    *   Can trigger notifications to the user confirming the new payment method.
    *   Enables features like displaying saved payment methods during checkout in the Order Service or UI.
*   **Key Payload Fields (within `data` object of `StandardMessageEnvelope`):**
    *   `paymentMethodId`: Unique ID for the stored payment method.
    *   `userId`: ID of the user to whom this payment method belongs.
    *   `type`: Type of payment method (e.g., "CREDIT_CARD", "DEBIT_CARD", "SEPA_DEBIT", "PAYPAL_ACCOUNT").
    *   `details`: Masked and summarized details (e.g., card brand "Visa", last four digits "1234", expiry "12/2028"). **Never include full PAN, CVC, or sensitive details.**
    *   `isDefault`: Boolean indicating if this is now the user's default payment method.
    *   `gatewayToken`: (Optional/Internal) The token or reference provided by the payment gateway for this stored method. Avoid exposing this broadly if it's highly sensitive.
    *   `addedAt`: Timestamp.

## 2. `PaymentMethodUpdatedEvent`

*   **Routing Key:** `paymentmethod.updated.v1`
*   **Trigger:** Published when details of an existing payment method are updated (e.g., new expiry date for a card, change in billing address associated with the method, setting a method as default).
*   **Purpose:**
    *   Ensures other services have the latest information about a user's payment methods.
    *   Important for avoiding payment failures due to outdated information.
*   **Key Payload Fields:**
    *   `paymentMethodId`: Unique ID of the payment method being updated.
    *   `userId`: ID of the user.
    *   `updatedFields`: An object or list specifying which fields were changed (e.g., `{"expiryMonth": "01", "expiryYear": "2029", "isDefault": true}`).
    *   `details`: The new masked and summarized details (as in `PaymentMethodAddedEvent`).
    *   `updatedAt`: Timestamp.## 3. `PaymentMethodRemovedEvent`

*   **Routing Key:** `paymentmethod.removed.v1`
*   **Trigger:** Published when a user removes a stored payment method.
*   **Purpose:**
    *   Allows User Service/Profile Service to delete the payment method from the user's profile.
    *   Prevents the outdated payment method from being offered in future checkouts.
*   **Key Payload Fields:**
    *   `paymentMethodId`: Unique ID of the payment method that was removed.
    *   `userId`: ID of the user.
    *   `removedAt`: Timestamp.

## 4. `PaymentMethodBecameDefaultEvent` (Optional - can be covered by `PaymentMethodUpdatedEvent`)

*   **Routing Key:** `paymentmethod.default.changed.v1`
*   **Trigger:** Published specifically when a user changes their default payment method. This might be redundant if `PaymentMethodUpdatedEvent` includes `isDefault` changes.
*   **Purpose:**
    *   Highlights a significant change in user preference for payments.
*   **Key Payload Fields:**
    *   `userId`: ID of the user.
    *   `newDefaultPaymentMethodId`: ID of the payment method now set as default.
    *   `oldDefaultPaymentMethodId`: (Optional) ID of the previously default payment method.
    *   `changedAt`: Timestamp.

Careful consideration must be given to the sensitivity of payment method data. Events should only contain tokenized or non-sensitive representations of payment details suitable for display or identification, not raw payment credentials.