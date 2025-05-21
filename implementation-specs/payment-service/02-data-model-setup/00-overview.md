# 00: Data Model Setup - Overview

This section outlines the data model for the Payment Service. A robust and well-defined data model is crucial for accurately recording financial transactions, managing payment methods, and ensuring data integrity.

## Key Data Entities

The core data entities for the Payment Service include:

1.  **`Payment` (`01-payment-entity.md`)**: Represents an overall payment attempt or intent for a specific order or charge. It tracks the amount, currency, status, and links to related transactions and the customer/order.

2.  **`Transaction` (`02-transaction-entity.md`)**: Records individual operations related to a payment, such as authorization, capture, sale (atomic auth and capture), void, or refund. Each payment can have multiple transactions.

3.  **`PaymentMethod` (`03-payment-method-entity.md`)**: Stores information about a customer's payment method. To comply with PCI DSS, this entity will primarily store non-sensitive information like the payment method type (Card, PayPal), a tokenized representation provided by the payment gateway, card brand, last four digits, and expiry date. It will also link to the customer (User ID).

4.  **`Refund` (`04-refund-entity.md`)**: Represents a refund processed against a specific payment or transaction. It includes the refund amount, reason, status, and links to the original payment and any gateway refund transaction identifiers.

5.  **`CustomerGatewayToken` (`05-customer-gateway-token-entity.md`)**: Stores customer identifiers or tokens specific to each payment gateway. This helps in managing recurring payments or saved customer profiles within the gateway's system without storing sensitive data locally.

6.  **`WebhookEventLog` (`06-webhook-event-log-entity.md`)**: Logs incoming webhook events received from payment gateways. This is crucial for auditing, debugging, and ensuring that all asynchronous updates are processed.

## Database Technology

*   **[07-database-selection.md](./07-database-selection.md)**: PostgreSQL is recommended for its reliability, transactional integrity (ACID compliance), and robust feature set suitable for financial data.

## ORM and Migration Strategy

*   **[08-orm-migrations.md](./08-orm-migrations.md)**: TypeORM (or a similar robust ORM for Node.js/TypeScript) will be used for interacting with the database. Database schema changes will be managed through TypeORM migrations.

This structure ensures that all payment-related data is captured comprehensively, supporting accurate financial tracking, operational needs, and compliance requirements.
