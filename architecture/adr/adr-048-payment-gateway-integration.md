# ADR-048: Payment Gateway Integration Strategy

**Status:** Proposed
**Date:** 2025-05-19

## 1. Context

As part of Milestone 2, an MVP Payment Service is being introduced to handle payment processing for the e-commerce platform. This service needs to integrate with an external payment gateway to process actual (test mode for MVP) financial transactions. This ADR outlines the strategy for this integration, including the choice of an initial gateway for MVP purposes and key integration patterns.

Key requirements for the integration include:
*   Ability to initiate payments for orders.
*   Ability to receive and process payment status updates (e.g., success, failure).
*   Secure handling of API keys and sensitive information (as per ADR-047 - Secrets Management Strategy).
*   Scalability for future real-world transaction volumes.
*   Ease of integration with the NestJS-based Payment Service.

## 2. Decision Drivers

*   **Speed of MVP Development:** Prioritize a gateway with good documentation, SDKs, and a straightforward API for quick initial implementation in test mode.
*   **Developer Experience:** Ease of use of SDKs and APIs for NestJS developers.
*   **Scalability & Reliability:** The chosen gateway (or the pattern of integration) should be capable of handling production loads in the future.
*   **Security:** Robust security features and compliance (e.g., PCI DSS) are critical, though for MVP test mode, the focus is on secure API key handling.
*   **Cost:** While less critical for MVP test mode, future transaction costs and fee structures are a consideration.
*   **Feature Set:** Availability of features like payment intents, webhooks, and a good testing environment.

## 3. Considered Options

*   **Option 1: Stripe**
    *   *Pros:* Excellent developer documentation, robust APIs and SDKs (including Node.js), widely used, strong testing capabilities (test mode, mock webhooks), good security features.
    *   *Cons:* Can be slightly more expensive for certain transaction types in production (future consideration).
*   **Option 2: PayPal**
    *   *Pros:* Widely recognized brand, supports various payment methods.
    *   *Cons:* APIs and developer experience sometimes considered less modern or more complex than Stripe's for direct integration.
*   **Option 3: Braintree (a PayPal service)**
    *   *Pros:* Supports PayPal, Venmo, cards, etc. Good SDKs.
    *   *Cons:* Might be more features than needed for MVP.
*   **Option 4: [Other relevant local/regional gateway - e.g., Adyen, Square]**
    *   *Pros:*
    *   *Cons:*

## 4. Decision Outcome

**Chosen Option:** [To be decided - Strong candidate: Stripe for MVP]

Rationale:
*   Stripe's comprehensive documentation, clear API structure, and robust Node.js SDK make it ideal for rapid MVP development and testing.
*   The test environment and webhook simulation capabilities are excellent for development and CI/CD integration.
*   While other options are viable, Stripe generally offers a smoother initial developer experience for building direct integrations.

## 5. Integration Pattern Details

*   **Payment Initiation:** 
    1.  Client (Frontend/Mobile) requests to initiate payment for an order via the Order Service.
    2.  Order Service (after validating the order) calls the Payment Service to create a payment intent.
    3.  Payment Service interacts with the chosen Payment Gateway (e.g., Stripe) to create a payment intent, providing amount, currency, and order reference.
    4.  Gateway returns a `client_secret` (for Stripe) or similar mechanism.
    5.  Payment Service records the payment attempt (with status 'pending' or 'requires_action') and returns the `client_secret` to the Order Service, which relays it to the client.
    6.  Client uses the `client_secret` with the gateway's frontend SDK (e.g., Stripe.js) to complete the payment action (e.g., enter card details).
*   **Payment Confirmation (Webhook-based):**
    1.  Gateway processes the payment and sends an asynchronous webhook event (e.g., `payment_intent.succeeded`, `payment_intent.payment_failed`) to a dedicated endpoint on the Payment Service.
    2.  Payment Service verifies the webhook signature for security.
    3.  Payment Service updates the status of the PaymentAttempt record based on the webhook event.
    4.  Payment Service publishes an internal event (e.g., using Kafka as per ADR-002, or a simpler mechanism for MVP) like `PaymentSucceededEvent` or `PaymentFailedEvent`, including order ID and payment details.
    5.  Order Service (and potentially other services like Notification Service in the future) subscribes to these events to update order status accordingly.
*   **Data Storage:** Payment Service stores payment attempts, statuses, gateway transaction IDs, amounts, currency. **No raw cardholder data (PAN, CVV) is ever stored in our system.**
*   **Error Handling:** Implement idempotent handling for webhooks. Define clear error codes and retry strategies for transient issues when communicating with the gateway.
*   **Security:** API keys for the payment gateway will be stored in AWS Secrets Manager (as per ADR-047) and accessed by the Payment Service at runtime. All communication with the gateway must be over HTTPS.

## 6. Pros and Cons of the Decision (Assuming Stripe for MVP)

### Pros
*   Rapid development for MVP due to excellent SDKs and documentation.
*   Strong testing environment provided by Stripe.
*   Secure and PCI-compliant handling of sensitive data by Stripe, reducing our PCI scope.
*   Scalable for future production use.

### Cons
*   Vendor lock-in to some extent, though an abstraction layer in Payment Service can mitigate this for future gateway changes.
*   Transaction fees for production use (future concern).

## 7. Consequences

*   The Payment Service will have a direct dependency on the chosen gateway's SDK (e.g., `stripe-node`).
*   Frontend components will need to integrate with the chosen gateway's client-side SDK (e.g., Stripe.js).
*   Robust webhook handling and security (signature verification) is critical.
*   A strategy for managing different API keys for test and live environments will be needed (covered by ADR-047).

## 8. Links

*   ADR-002: Asynchronous Communication (Kafka)
*   ADR-047: Secrets Management Strategy
*   ADR-005: JWT Based Authentication & Authorization (for securing Payment Service APIs if called directly)
*   Milestone 2, Sprint 2 Plan (PBIs: PBI-M2-2.5 to PBI-M2-2.9)
*   [Stripe Documentation: https://stripe.com/docs]

---
