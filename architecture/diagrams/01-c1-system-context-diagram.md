```markdown
# C1 System Context Diagram

Date: {{TIMESTAMP}}
Status: Adopted

## Diagram

This diagram illustrates the overall context of the E-commerce Platform, showing its interactions with various external users and systems.

![C1 System Context Diagram](./c1_system_context_diagram.png)

## Elements

### System

*   **E-commerce Platform:** The core system being developed, encompassing all functionalities for online retail operations.

### Actors

*   **Customer:** End-users who browse products, place orders, and manage their accounts.
*   **Administrator:** Internal users responsible for managing the platform, including user accounts, product catalog, orders, and system configurations.
*   *(Optional) Seller:* If the platform supports a multi-vendor marketplace, sellers would be actors who manage their product listings and fulfill orders.

### External Systems

*   **Payment Gateway:** An external service responsible for processing online payments securely (e.g., Stripe, PayPal).
*   **Shipping Provider:** External logistics companies or services used for order fulfillment and delivery (e.g., FedEx, UPS, Shippo).
*   **Social Login IdP (Identity Provider):** External services that allow users to register or log in using their existing social media accounts (e.g., Google, Facebook, Apple).
*   **Email Service:** An external service used for sending transactional emails and notifications to users (e.g., SendGrid, AWS SES, Mailchimp Transactional).
*   **Analytics Platform:** External tools used for tracking user behavior, sales data, and overall platform performance (e.g., Google Analytics, Mixpanel).

## Interactions

Key interactions include:

*   **Customers** interact with the platform to browse, search, add to cart, checkout, and manage their profiles.
*   **Administrators** interact with the platform to manage users, products, orders, inventory, promotions, and system settings.
*   The **E-commerce Platform** interacts with:
    *   **Payment Gateway** to process payments.
    *   **Shipping Provider** to arrange shipments and get tracking updates.
    *   **Social Login IdP** to authenticate users via social accounts.
    *   **Email Service** to send notifications.
    *   **Analytics Platform** to send event data for tracking.

This diagram provides a high-level overview, with more detailed breakdowns provided in subsequent C2 (Container) and C3 (Component) diagrams.
```
