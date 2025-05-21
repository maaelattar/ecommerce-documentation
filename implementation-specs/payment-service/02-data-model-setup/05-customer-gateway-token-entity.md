# 05: `CustomerGatewayToken` Entity

Many payment gateways allow creating a "customer" object or profile within their system. This `CustomerGatewayToken` entity stores the mapping between our platform's `userId` and the customer identifier (`gatewayCustomerId`) provided by the specific payment gateway. This is essential for features like charging saved payment methods directly using gateway customer profiles, managing subscriptions, or simplifying recurring billing without handling sensitive payment data directly.

## Attributes

| Attribute             | Data Type                               | Nullable | Description                                                                                                   |
| --------------------- | --------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- |
| `id`                  | UUID (Primary Key)                      | No       | Unique identifier for the customer gateway token record.                                                      |
| `userId`              | UUID / String                           | No       | Identifier for the user in our system (from the User Service). Indexed.                                       |
| `gateway`             | String (e.g., "STRIPE", "PAYPAL")     | No       | The payment gateway this customer token belongs to. Indexed.                                                  |
| `gatewayCustomerId`   | String                                  | No       | The customer identifier provided by the payment gateway (e.g., Stripe `cus_xxx`). Indexed.                    |
| `description`         | Text                                    | Yes      | A brief description or note about this gateway customer entry (e.g., "Stripe customer profile for user X"). |
| `metadata`            | JSONB                                   | Yes      | Any additional metadata from the gateway related to this customer object, or for internal use.                |
| `isActive`            | Boolean                                 | No       | Indicates if this gateway customer mapping is currently active. Default `true`.                               |
| `createdAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the record was created.                                                                        |
| `updatedAt`           | Timestamp (YYYY-MM-DD HH:MM:SS Z)       | No       | Timestamp when the record was last updated.                                                                   |

## Relationships

*   **Belongs to a User**: (Implicitly via `userId`). One user can have multiple `CustomerGatewayToken` records, one for each payment gateway they have interacted with where a customer object was created.

## Indexes

*   Primary key on `id`.
*   Unique composite index on (`userId`, `gateway`) to ensure a user has only one customer ID per gateway.
*   On `gatewayCustomerId` (and `gateway`) for quick lookup based on gateway identifiers (e.g., when processing webhooks related to a gateway customer).

## Purpose and Usage

*   **Saving Payment Methods**: When a user saves a payment method, the payment gateway might create a customer object and associate the payment method with it. This entity stores the link to that customer object.
*   **Recurring Billing/Subscriptions**: For subscription services, the `gatewayCustomerId` is often used to charge the customer on a recurring basis without needing to re-prompt for payment details.
*   **Simplified Checkout**: If a user has a customer profile with a saved payment method at the gateway, this token allows the e-commerce platform to initiate payments using that saved method via an API call that references the `gatewayCustomerId`.
*   **PCI DSS Compliance**: By using gateway-managed customer objects and payment methods, the platform avoids handling and storing sensitive payment data, helping with PCI DSS compliance.

## Considerations

*   **Synchronization**: The existence or status of the customer object in the payment gateway might change (e.g., if the user deletes their account on the gateway side, though this is rare). The `isActive` flag can be used, but robust synchronization is complex and often relies on webhooks or periodic checks if critical.
*   **Data Minimization**: Only store the necessary identifiers. Avoid duplicating information that is already securely stored by the payment gateway.
*   **Gateway Specifics**: The concept and capabilities of "customer" objects vary between payment gateways. This entity provides a generic way to store the mapping.
*   **Creation Logic**: This record is typically created the first time a user interacts with a specific payment gateway in a way that results in a customer object being created at the gateway (e.g., saving a card, first payment with "save card" option).

This `CustomerGatewayToken` entity plays a vital role in enabling advanced payment features and maintaining a high level of security by leveraging the capabilities of external payment gateways.
