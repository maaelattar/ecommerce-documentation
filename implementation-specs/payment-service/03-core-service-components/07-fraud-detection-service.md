# 07: `FraudDetectionService` (or Integration Point)

The `FraudDetectionService` is responsible for assessing the risk associated with payment transactions to prevent fraudulent activities. Depending on the complexity and requirements, this can range from a simple internal rules engine to a sophisticated integration with a dedicated third-party fraud prevention service.

## Responsibilities

1.  **Risk Assessment**: 
    *   Receives transaction details (e.g., amount, currency, payment method details (non-sensitive like BIN, IP address, email, shipping address, user history indicators) from the `PaymentProcessingService` before a payment is attempted or authorized.
    *   Analyzes these details to calculate a fraud risk score or a set of risk indicators.

2.  **Rule Engine (Internal - Basic Scenario)**:
    *   May implement a basic internal rules engine based on predefined criteria:
        *   Velocity checks (e.g., too many transactions from the same IP or user in a short period).
        *   High-value transaction limits.
        *   Checks against deny lists (e.g., known fraudulent email addresses, IP addresses).
        *   Consistency checks (e.g., billing address vs. shipping address vs. IP geolocation).

3.  **Integration with External Fraud Services (Advanced/Recommended Scenario)**:
    *   Integrates with specialized third-party fraud detection platforms (e.g., Stripe Radar, PayPal Fraud Protection, Sift, Kount, Forter).
    *   Sends transaction data to the external service via API.
    *   Receives a risk score, recommendation (e.g., `approve`, `review`, `reject`), and detailed risk factors from the external service.

4.  **Decision Making/Recommendation**: 
    *   Based on the risk assessment (internal or external), provides a decision or recommendation to the `PaymentProcessingService`:
        *   `APPROVE`: Proceed with the transaction.
        *   `REVIEW`: Flag the transaction for manual review by an internal team before proceeding or rejecting.
        *   `REJECT` / `BLOCK`: Do not proceed with the transaction.

5.  **Data Collection for Analysis**: 
    *   Collects and prepares relevant data points for fraud analysis. This might include:
        *   Transaction details (amount, currency, items).
        *   Payment method details (BIN, card type, last4 - no full PAN).
        *   User information (account age, order history, email, IP address).
        *   Device fingerprinting data (if available).
        *   Shipping and billing address information.

6.  **Feedback Loop (for ML-based services)**: 
    *   If using an ML-powered external fraud service, it's often important to provide feedback on the accuracy of its predictions (e.g., confirming if a manually reviewed transaction was indeed fraudulent or legitimate, or reporting chargebacks).

## Interactions with Other Services

*   **`PaymentProcessingService`**: The primary consumer. It calls the `FraudDetectionService` before processing or authorizing a payment to get a risk assessment.
*   **External Fraud Detection Platform(s)**: If an external service is used, this component makes API calls to it.
*   **Database (via ORM)**: May access historical transaction data or user data to build features for an internal rules engine or to supplement data sent to an external service.
*   **`WebhookHandlerService` (Potentially)**: May receive webhook updates from external fraud services regarding the status of reviewed transactions or updated risk scores.

## Key Operations (Conceptual)

*   `assessTransactionRisk(transactionDetails: FraudAssessmentRequest): Promise<FraudAssessmentResponse>`

```typescript
interface FraudAssessmentRequest {
  orderId: string;
  userId?: string;
  amount: number;
  currency: string;
  paymentMethodType: string; // e.g., 'CARD', 'PAYPAL'
  cardBin?: string;
  cardLastFour?: string;
  ipAddress?: string;
  email?: string;
  shippingAddress?: AddressInfo;
  billingAddress?: AddressInfo;
  // ... other relevant data points
  gatewaySpecificData?: any; // Data from client-side gateway SDKs (e.g. Stripe Radar session)
}

interface FraudAssessmentResponse {
  riskScore?: number; // 0-100
  recommendation: 'APPROVE' | 'REVIEW' | 'REJECT';
  reason?: string; // Or a list of rule IDs / risk factors
  externalFraudServiceTransactionId?: string;
  rawProviderResponse?: any;
}

interface AddressInfo {
  line1: string; line2?: string; city: string; state: string; postalCode: string; country: string;
}
```

## Design Considerations

*   **Performance**: Fraud checks must be fast to avoid adding significant latency to the payment process. External API calls should have tight timeouts.
*   **Accuracy vs. Friction**: The goal is to block fraud without creating excessive friction for legitimate customers (i.e., minimizing false positives).
*   **Configurability**: Rules (for internal engine) or thresholds (for external scores) should be configurable, potentially dynamically.
*   **Bypass Logic**: Mechanisms for bypassing fraud checks for trusted users or specific scenarios might be needed but should be used with extreme caution and strong controls.
*   **Data Privacy**: Be mindful of data privacy regulations when collecting and sending user data to external fraud services. Ensure clear consent and data handling policies.
*   **Cost**: External fraud services often have a per-transaction cost, which needs to be factored in.
*   **Fallback Strategy**: If an external fraud service is temporarily unavailable, define a fallback strategy (e.g., use a more conservative internal ruleset, or allow transactions with a warning, or temporarily reject based on risk profile).
*   **Security**: API keys and credentials for external fraud services must be managed securely.

Integrating robust fraud detection is essential for protecting the business from financial losses and maintaining a trustworthy platform.
