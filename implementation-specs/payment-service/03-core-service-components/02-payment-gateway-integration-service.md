# 02: `PaymentGatewayIntegrationService`

The `PaymentGatewayIntegrationService` acts as an abstraction layer between the core logic of the Payment Service and the specific APIs of various external payment gateways (e.g., Stripe, PayPal, Adyen). It might be designed as an interface or an abstract class, with concrete implementations for each supported gateway.

## Responsibilities

1.  **API Abstraction**: 
    *   Defines a common set of methods for payment operations (e.g., `createPaymentIntent`, `charge`, `refund`, `tokenizePaymentMethod`, `getCustomer`, `savePaymentMethodToCustomer`).
    *   Hides the complexities and differences of various gateway APIs from the rest of the Payment Service.

2.  **Gateway-Specific Implementation**: 
    *   Each concrete implementation (e.g., `StripeIntegrationService`, `PayPalIntegrationService`) translates the common method calls into specific HTTP API requests to the respective gateway.
    *   Handles authentication with the gateway (e.g., using API keys, OAuth tokens).
    *   Formats request payloads according to the gateway's requirements.
    *   Parses response payloads from the gateway and maps them to a common internal representation or directly to relevant entity fields.

3.  **Tokenization and Secure Data Handling**: 
    *   Manages the process of sending sensitive payment information (e.g., card details collected via a secure frontend form/SDK) directly to the gateway for tokenization, ensuring such data never transits through or is stored on our servers (except for non-sensitive parts like last four digits, card brand).
    *   Retrieves and returns gateway-generated tokens (e.g., payment method tokens, customer IDs).

4.  **Error Mapping and Handling**: 
    *   Catches gateway-specific errors and maps them to standardized error codes or messages that can be understood by the `PaymentProcessingService`.
    *   Provides context for errors (e.g., whether an error is retryable, a hard decline, or a configuration issue).

5.  **Configuration Management**: 
    *   Accesses and uses gateway-specific configurations (e.g., API keys, webhook secrets) securely, typically via the `ConfigurationService`.

6.  **Webhook Signature Verification**: 
    *   While the `WebhookHandlerService` might be the entry point for webhooks, this service (or its specific implementations) would contain the logic to verify the signature of incoming webhooks to ensure they are authentic and originated from the correct gateway.

## Interface Definition (Conceptual)

```typescript
interface IPaymentGatewayAdapter {
  readonly gatewayName: string;

  // Create a payment intent or equivalent in the gateway
  createPaymentIntent(params: { 
    amount: number; 
    currency: string; 
    orderId: string; 
    customerId?: string; // Gateway customer ID
    paymentMethodId?: string; // Gateway payment method ID
    captureMethod?: 'automatic' | 'manual';
    metadata?: object; 
    returnUrl?: string; // For redirect-based flows
    // ...other common params
  }): Promise<GatewayPaymentIntentResponse>;

  // Capture a previously authorized payment
  capturePaymentIntent(gatewayPaymentIntentId: string, amountToCapture?: number): Promise<GatewayTransactionResponse>;

  // Create a charge (can be direct or using a payment intent)
  createCharge(params: { 
    amount: number; 
    currency: string; 
    sourceTokenOrPaymentMethodId: string; // Gateway token
    customerId?: string;
    description?: string; 
    metadata?: object; 
    capture?: boolean; // true for sale, false for auth
  }): Promise<GatewayTransactionResponse>;

  // Refund a charge
  createRefund(params: { 
    gatewayChargeId: string; 
    amount: number; 
    reason?: string; 
    metadata?: object; 
  }): Promise<GatewayRefundResponse>;

  // Tokenize raw payment details (typically done client-side with gateway SDKs, but server might facilitate or confirm)
  // Or more commonly, create/attach a payment method to a customer
  savePaymentMethod(customerId: string, paymentMethodToken: string): Promise<GatewayPaymentMethodResponse>;
  detachPaymentMethod(gatewayPaymentMethodId: string): Promise<boolean>;
  listPaymentMethods(customerId: string): Promise<GatewayPaymentMethodResponse[]>;

  // Customer management at gateway level
  createCustomer(params: { email?: string; userId: string; name?: string; metadata?: object }): Promise<GatewayCustomerResponse>;
  retrieveCustomer(gatewayCustomerId: string): Promise<GatewayCustomerResponse | null>;

  // Webhook signature verification
  verifyWebhookSignature(payload: string | Buffer, signatureHeader: string, webhookSecret: string): boolean;
}

// Conceptual response types
interface GatewayPaymentIntentResponse { gatewayPaymentIntentId: string; status: string; clientSecret?: string; nextAction?: any; rawResponse: any; }
interface GatewayTransactionResponse { gatewayTransactionId: string; status: string; amount: number; currency: string; rawResponse: any; errorCode?: string; errorMessage?: string; }
interface GatewayRefundResponse { gatewayRefundId: string; status: string; amount: number; rawResponse: any; }
interface GatewayPaymentMethodResponse { gatewayPaymentMethodId: string; type: string; last4?: string; brand?: string; /* ... */ rawResponse: any; }
interface GatewayCustomerResponse { gatewayCustomerId: string; /* ... */ rawResponse: any; }
```

## Concrete Implementations

*   **`StripeIntegrationService implements IPaymentGatewayAdapter`**: Handles all interactions with the Stripe API.
*   **`PayPalIntegrationService implements IPaymentGatewayAdapter`**: Handles all interactions with the PayPal API.
*   Future gateways would have their own adapter implementations.

## Service Selection

A factory or strategy pattern could be used by the `PaymentProcessingService` to select the appropriate gateway adapter based on configuration or request parameters (e.g., if a user specifically chose PayPal, or if Stripe is the default).

```typescript
// Example in PaymentProcessingService
constructor(private stripeAdapter: StripeIntegrationService, private paypalAdapter: PayPalIntegrationService) {}

private getGatewayAdapter(gatewayName: string): IPaymentGatewayAdapter {
  if (gatewayName === 'STRIPE') return this.stripeAdapter;
  if (gatewayName === 'PAYPAL') return this.paypalAdapter;
  throw new Error('Unsupported payment gateway');
}
```

## Design Considerations

*   **Resilience**: Implementations should handle gateway API timeouts, rate limits, and intermittent errors gracefully, possibly with configurable retry logic for idempotent operations.
*   **Logging**: Detailed logging of requests and responses (with sensitive data masked) is crucial for debugging integration issues.
*   **Testability**: The abstraction allows for easier testing. Core payment logic can be tested by mocking the `IPaymentGatewayAdapter` interface.
*   **Security**: Securely manage and use API keys for each gateway. Ensure requests are made over HTTPS.

This service is fundamental for isolating gateway-specific complexities and allowing the Payment Service to be extensible to support multiple payment providers without significant changes to the core processing logic.
