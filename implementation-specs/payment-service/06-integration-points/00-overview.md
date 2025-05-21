# 00: Integration Points - Overview

The Payment Service, while specialized, does not operate in isolation. It integrates with various internal microservices and external systems to fulfill its responsibilities. This section outlines these key integration points.

## Internal Integrations (Consuming Events from or Exposing APIs to other E-commerce Services):

1.  **Order Service (`01-order-service-integration.md`)**:
    *   **Payment Service as Provider**: Order Service initiates payment requests to the Payment Service APIs.
    *   **Payment Service as Consumer (of Events)**: N/A directly for core payment flows, but could consume order events if payment initiation is triggered by `OrderCreated` or `OrderReadyForPayment` events (event-driven flow).
    *   **Order Service as Consumer (of Events)**: Order Service consumes events like `PaymentSucceeded`, `PaymentFailed`, `RefundProcessed` from the Payment Service to update order status and manage fulfillment.

2.  **User Service (`02-user-service-integration.md`)**:
    *   **Payment Service as Consumer**: Payment Service may query User Service (or rely on data in JWT) for `userId` to associate with payments and payment methods. It fetches user details if needed for display or gateway requirements (e.g., customer name, email if not passed directly).
    *   **User Service as Consumer (of Events)**: User Service consumes events like `PaymentMethodAdded`, `PaymentMethodRemoved`, `DefaultPaymentMethodChanged` to update its view of a user's payment profile.

3.  **Notification Service (`03-notification-service-integration.md`)**:
    *   **Notification Service as Consumer (of Events)**: Consumes events like `PaymentSucceeded`, `PaymentFailed`, `RefundProcessed`, `PaymentRequiresAction` from the Payment Service to send appropriate notifications (email, SMS) to users or administrators.

4.  **API Gateway (`04-api-gateway-integration.md`)**:
    *   The Payment Service exposes its APIs (defined in `04-api-endpoints/`) through an API Gateway, which handles concerns like request routing, rate limiting, and initial authentication/authorization for client-facing interactions.

5.  **Reporting/Analytics Service (`05-reporting-analytics-integration.md`)**:
    *   **Reporting/Analytics Service as Consumer (of Events/Data)**: Consumes payment events or reads from a data replica/data warehouse populated by payment data for financial reporting, sales analytics, and business intelligence.

## External System Integrations:

These are critical for the core functionality of the Payment Service.

1.  **Payment Gateways (e.g., Stripe, PayPal, Adyen) (`06-payment-gateways-integration.md`)**:
    *   The primary external integration. The Payment Service makes API calls to gateways for payment processing, tokenization, refunds, etc.
    *   Receives webhooks from gateways for asynchronous status updates.

2.  **Fraud Detection Services (e.g., Sift, Kount, Stripe Radar) (`07-fraud-detection-services-integration.md`)**:
    *   If an external fraud service is used, the Payment Service sends transaction data to it for risk assessment and receives a score/recommendation.

3.  **Tax Calculation Services (e.g., Avalara, TaxJar) (`08-tax-calculation-services-integration.md`)**:
    *   While order creation might handle initial tax calculation, the Payment Service might need to confirm final amounts or integrate if tax needs to be itemized or reported specifically during payment processing in some jurisdictions or with some gateways.
    *   Often, the final tax amount is passed to the Payment Service by the Order Service.

4.  **Banking and Settlement Systems (`09-banking-settlement-integration.md`)**:
    *   Indirect integration. The Payment Service itself usually doesn't integrate directly with banks for settlement. Gateways handle this.
    *   However, financial data from the Payment Service (via reports or events) is crucial for the finance team to reconcile settlements received from gateways into company bank accounts.

5.  **Address Verification Services (AVS) / CVV Check Services (`10-avs-cvv-integration.md`)**:
    *   These are typically part of the Payment Gateway's functionality. The Payment Service passes relevant data (billing address, CVV if collected by client-side gateway SDK) to the gateway, which then performs these checks.
    *   The Payment Service receives and logs AVS/CVV responses.

## Shared Platform Services Integrations:

1.  **Logging Service (`11-logging-service-integration.md`)**: All components within Payment Service will integrate with a centralized logging platform (e.g., ELK/EFK, Splunk, Grafana Loki).
2.  **Monitoring and Alerting Service (`12-monitoring-alerting-integration.md`)**: Exposes metrics and health checks for monitoring; integrates with alerting systems (e.g., Prometheus, Grafana, CloudWatch).
3.  **Configuration Management (`13-configuration-management-integration.md`)**: Uses a centralized or environment-based configuration system (as discussed in `03-core-service-components/10-configuration-service.md` and `08-deployment-operations/03-configuration-management.md`).
4.  **Secrets Management (`14-secrets-management-integration.md`)**: Integrates with a secure vault (e.g., HashiCorp Vault, AWS Secrets Manager) for handling sensitive credentials like gateway API keys.

Understanding these integration points is key to understanding the Payment Service's role and dependencies within the broader system architecture.
