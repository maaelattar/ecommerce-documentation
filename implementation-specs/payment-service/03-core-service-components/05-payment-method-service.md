# 05: `PaymentMethodService`

The `PaymentMethodService` is responsible for managing all aspects of customer payment methods. Its primary goal is to provide a secure and user-friendly way for customers to save, list, update, and delete their payment options, while adhering to PCI DSS compliance by relying on gateway tokenization.

## Responsibilities

1.  **Adding Payment Methods**: 
    *   Handles requests to add a new payment method for a user.
    *   Coordinates with the `PaymentGatewayIntegrationService` to:
        *   Create a customer object in the gateway if one doesn't already exist for the user (using `CustomerGatewayToken` entity).
        *   Send the raw payment details (obtained securely from the client-side, e.g., via Stripe Elements or PayPal SDK) to the gateway to be tokenized and associated with the gateway customer object.
    *   Creates a `PaymentMethod` entity in the local database, storing the gateway-provided token (`gatewayPaymentMethodId`) and non-sensitive details (card brand, last four, expiry) for display.
    *   Ensures sensitive data like full PAN or CVV never touches the application server.

2.  **Listing Payment Methods**: 
    *   Provides functionality to retrieve a list of saved payment methods for a given user (`userId`).
    *   Fetches records from the local `PaymentMethod` table.

3.  **Setting a Default Payment Method**: 
    *   Allows a user to designate one of their saved payment methods as the default for future transactions.
    *   Updates the `isDefault` flag on the `PaymentMethod` entities for that user (ensuring only one can be default per user, or per user per gateway if that level of granularity is needed).

4.  **Updating Payment Method Details (Limited)**: 
    *   Some payment method details (e.g., expiry date, billing address) might be updatable via the gateway. This service would coordinate such updates.
    *   Direct updates to card numbers are generally not allowed; the user would typically add a new card and delete the old one.

5.  **Deleting Payment Methods**: 
    *   Handles requests to remove a saved payment method.
    *   Calls the `PaymentGatewayIntegrationService` to detach or delete the payment method from the customer's profile within the gateway.
    *   Deletes or marks as inactive the corresponding `PaymentMethod` entity in the local database.

6.  **Validation and Status Synchronization**: 
    *   Potentially interacts with gateways to validate payment methods (e.g., using $0 or $1 authorization) if required, although this is often handled by the gateway itself upon adding.
    *   May include logic to synchronize the status of payment methods (e.g., `EXPIRED`) based on information from webhooks or periodic checks, if feasible and provided by the gateway.

7.  **Retrieving Payment Method Details for Processing**: 
    *   Provides a secure way for the `PaymentProcessingService` to retrieve the `gatewayPaymentMethodId` for a chosen payment method when a user initiates a payment with a saved option.

## Interactions with Other Services

*   **`PaymentGatewayIntegrationService`**: This is a primary collaborator. The `PaymentMethodService` uses it for all direct communication with payment gateways regarding tokenization, saving, detaching, and listing payment methods at the gateway level.
*   **`CustomerGatewayToken` Entity/Service**: Manages the creation and retrieval of `CustomerGatewayToken` records, which link platform users to gateway customer IDs. This is essential before a payment method can be saved to a gateway customer.
*   **Database (via ORM)**: Persists and manages `PaymentMethod` entities.
*   **User Service (Conceptually)**: Depends on `userId` to associate payment methods with users. No direct calls typically, but `userId` is a key data point.

## Key Operations (Conceptual)

*   `addPaymentMethod(userId: string, gateway: string, paymentMethodClientToken: string, billingDetails: object, isDefault?: boolean): Promise<PaymentMethod>` (clientToken is from gateway SDKs)
*   `listPaymentMethods(userId: string, gateway?: string): Promise<PaymentMethod[]>`
*   `setDefaultPaymentMethod(userId: string, paymentMethodId: string): Promise<PaymentMethod>`
*   `updatePaymentMethodDetails(paymentMethodId: string, updates: { billingDetails?: object; expiryMonth?: number; expiryYear?: number }): Promise<PaymentMethod>` (capabilities depend on gateway)
*   `deletePaymentMethod(userId: string, paymentMethodId: string): Promise<void>`
*   `getPaymentMethodForProcessing(paymentMethodId: string): Promise<{ gatewayPaymentMethodId: string; gateway: string; gatewayCustomerId?: string } | null>`

## Design Considerations

*   **PCI DSS Compliance**: The entire design must revolve around PCI DSS compliance. The core principle is that sensitive cardholder data is handled directly by the client-side integration with the payment gateway SDKs and then tokenized by the gateway. The backend service only ever deals with these tokens.
*   **User Experience**: The service should support a smooth and intuitive user experience for managing payment methods.
*   **Gateway Abstraction**: While this service interacts with the `PaymentGatewayIntegrationService`, its own API to the rest of the application (e.g., API controllers) should be as gateway-agnostic as possible for common operations like listing methods.
*   **Security of Tokens**: `gatewayPaymentMethodId` tokens are sensitive in the sense that they can be used to charge the customer. Access to them should be strictly controlled.

This `PaymentMethodService` is crucial for providing users with the convenience of saved payment options while maintaining the highest level of security and compliance by offloading sensitive data handling to specialized payment gateways.
