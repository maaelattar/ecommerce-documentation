# 10: AVS (Address Verification System) / CVV (Card Verification Value) Integration

Address Verification System (AVS) and Card Verification Value (CVV, also known as CVC2, CVV2, CID) checks are important security features used in card-not-present transactions to help reduce fraud. The Payment Service itself does not perform these checks directly but relies on the payment gateways to do so.

## Role of Payment Gateways in AVS/CVV

1.  **Data Collection (Client-Side via Gateway SDKs)**:
    *   **CVV**: The CVV code (the 3 or 4-digit code on the back or front of a credit card) is typically collected from the user by the payment gateway's client-side SDK (e.g., Stripe Elements, PayPal JS SDK) when the user enters their card details.
        *   **Crucially, the CVV code should never be sent to or stored on the e-commerce platform's backend servers (including the Payment Service)**. This is a strict PCI DSS requirement.
    *   **Billing Address (for AVS)**: The billing address (street number and postal code are primary for AVS) is also collected from the user, often via the same client-side form integrated with the gateway SDK.

2.  **Data Transmission to Gateway**: The gateway's client-side SDK securely transmits the CVV and billing address information directly to the gateway along with the other card details when creating a payment method token or processing a payment.

3.  **Checks Performed by Gateway/Processor**: 
    *   The payment gateway (or the underlying card processor it communicates with) performs the AVS and CVV checks during the transaction authorization process.
    *   **AVS**: Compares the numeric parts of the billing address provided by the customer with the address on file with the card issuer.
    *   **CVV**: Verifies that the provided CVV matches the one associated with the card account.

4.  **Response Codes from Gateway**: 
    *   The payment gateway's API response for a payment attempt (e.g., when creating a charge or confirming a payment intent) will include AVS and CVV response codes.
    *   These codes indicate the results of the checks (e.g., AVS match, AVS partial match, AVS no match, CVV match, CVV no match, CVV not processed).
    *   Examples (Stripe AVS/CVV codes):
        *   AVS: `Y` (Exact match), `A` (Address match only), `Z` (Zip match only), `N` (No match), `U` (Unavailable), `S` (Not supported by issuer).
        *   CVV: `M` (Match), `N` (No match), `P` (Not processed), `U` (Issuer unable to process), `S` (Not provided by customer).

## Payment Service Responsibilities

1.  **Receiving and Logging AVS/CVV Responses**: 
    *   The `PaymentGatewayIntegrationService` (and its specific implementations) should be designed to parse the AVS and CVV response codes from the gateway's API response.
    *   These codes should be stored in the `Transaction` entity (e.g., in fields like `avsResponse`, `cvvResponse`) for auditing, reporting, and potential use in risk assessment.

2.  **Risk Assessment (Optional Use of Responses)**:
    *   The AVS and CVV responses can be used as inputs to the `FraudDetectionService` or internal risk rules.
    *   For example, a transaction with an AVS mismatch and a CVV mismatch might be considered higher risk and could be flagged for review or automatically declined, even if the card authorization itself was initially approved by the issuer (issuers may still approve transactions despite AVS/CVV mismatches, leaving the merchant to assume the risk).

3.  **Configuration of Gateway Rules (Indirect)**:
    *   Many payment gateways allow merchants to configure rules in their gateway dashboard based on AVS/CVV responses (e.g., automatically decline transactions with AVS "N" and CVV "N").
    *   The Payment Service doesn't directly manage these rules via API in most cases, but its behavior (e.g., whether it proceeds with a capture after an auth) might be influenced by these gateway-level risk settings reflected in the transaction outcome.

## What the Payment Service DOES NOT DO

*   **Collect CVV**: The Payment Service backend **never** directly collects or stores CVV codes.
*   **Perform AVS/CVV Checks**: It does not implement the logic to compare addresses or validate CVVs. This is the responsibility of the PCI-compliant payment gateway.

**Conclusion**: Integration for AVS and CVV checks primarily involves the Payment Service correctly relaying information to the gateway (via client-side SDKs for sensitive data) and then receiving, storing, and potentially acting upon the AVS/CVV response codes provided by the gateway. This approach leverages the security and compliance of the payment gateway while providing valuable risk indicators to the merchant.
