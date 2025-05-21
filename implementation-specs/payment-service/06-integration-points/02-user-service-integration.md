# 02: User Service Integration

The User Service manages user accounts, profiles, and authentication. The Payment Service integrates with it primarily to associate payments and payment methods with specific users, and to enable a personalized payment experience.

## Flows and Interactions

**1. Associating Payments and Payment Methods with Users (Payment Service -> User Service Info)**

*   **Trigger**: When a payment is initiated or a payment method is saved by an authenticated user.
*   **Interaction Type**: The Payment Service typically receives the `userId` as part of the request (e.g., from a JWT claim processed by the API Gateway or passed by the calling service like Order Service).
*   **Data Usage by Payment Service**:
    *   The `userId` is stored in `Payment` and `PaymentMethod` entities to link them to the user.
    *   If the Payment Service needs user details (e.g., name, email) to pass to a payment gateway (e.g., for creating a customer profile at the gateway if one doesn't exist, or for fraud prevention data), it might:
        *   Expect these details to be passed in the initial request from the client/Order Service (preferred to minimize direct calls).
        *   Make a synchronous API call to the User Service (`GET /v1/users/{userId}/profile` or similar) to fetch necessary, non-sensitive profile information if it's not provided but required by a gateway. This should be a last resort to avoid tight coupling and performance overhead.
*   **Security**: PII fetched from User Service should be handled securely and only transmitted to gateways over HTTPS. The Payment Service should not store PII unless absolutely necessary and compliant (e.g., billing name on `PaymentMethod` for display).

**2. Updating User Profile with Payment Information (User Service consumes Payment Service Events)**

*   **Trigger**: The Payment Service publishes events when payment methods are managed by a user.
*   **Interaction**: The User Service subscribes to relevant events from the `payment.events` Kafka topic.
*   **Key Events Consumed by User Service**:
    *   `PaymentMethodAdded`:
        *   The User Service might update its own representation of the user's profile to indicate a new payment method is available (e.g., for display in a "My Payment Methods" section of the user's account page). It would typically store a reference or a non-sensitive summary, not the full details from the event.
    *   `PaymentMethodRemoved`:
        *   User Service updates its view to reflect the removal.
    *   `DefaultPaymentMethodChanged`:
        *   User Service updates which payment method is marked as default for the user.
    *   `PaymentMethodUpdated`:
        *   User Service updates details like card expiry if it displays this information.
*   **User Service Action**: Updates its local user profile data to provide a consistent view to the user regarding their payment options. It **does not** store sensitive payment tokens; it only manages references or displayable summaries.

**3. Guest Checkouts**

*   For guest checkouts, the `userId` field in `Payment` entities might be null.
*   Payment methods are generally not saved for guest users, so interactions related to `PaymentMethod` entities for guests are minimal or non-existent.
*   If a guest user later creates an account with the same email, there might be a business process to link past guest orders/payments, but this is typically outside the direct User Service-Payment Service integration for real-time transactions.

## Data Considerations

*   **`userId` as the Link**: The `userId` is the primary key for linking payment activities to user accounts.
*   **Data Minimization**: The Payment Service should only request or store the minimal user information necessary for its operations and for gateway interactions.
*   **Consistency**: Eventual consistency is achieved by the User Service consuming events from the Payment Service. If the User Service needs to present a completely up-to-the-second accurate list of payment methods, it might need to make an API call to the Payment Service, but event-driven updates are preferred for typical profile displays.

## Security and Compliance

*   Communication between Payment Service and User Service (if any direct API calls are made) must be secured (e.g., mTLS or service-to-service JWT).
*   User PII must be handled in accordance with data privacy regulations (GDPR, CCPA, etc.).
*   The Payment Service should not become a secondary store for extensive user profile data. It should focus on payment-related attributes and link to the User Service via `userId`.

This integration allows for a personalized payment experience (e.g., using saved payment methods) while ensuring that user account management and payment processing remain distinct and specialized domains.
