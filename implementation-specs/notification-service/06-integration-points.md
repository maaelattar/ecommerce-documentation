# Notification Service - Integration Points

## 1. Overview

The Notification Service, while central to dispatching communications, integrates with various other components both internally within the e-commerce platform and externally with third-party providers.

## 2. Inbound Integrations (Receiving Triggers & Data)

### 2.1. Event Consumption from Internal Microservices
*   **Mechanism**: Asynchronous via RabbitMQ (using `@ecommerce-platform/rabbitmq-event-utils`).
*   **Purpose**: To receive domain events that trigger notifications (e.g., `OrderCreatedEvent`, `UserPasswordResetRequestedEvent`).
*   **Key Services Integrated With (Examples)**:
    *   **Order Service**: For order lifecycle events.
    *   **User Service**: For account-related events, identity verification.
    *   **Payment Service**: For payment status events, refund confirmations.
    *   **Inventory Service**: For stock alerts (e.g., back-in-stock notifications).
    *   **(Future) Support Service**: For support ticket updates.
*   **Data Contract**: `StandardMessage<T>` envelope. Payloads defined by publishing services.
*   **Considerations**: Notification Service relies on these events carrying sufficient data. If not, synchronous API calls (see below) might be needed as a fallback, which is less ideal.

### 2.2. API Calls from Internal Microservices (Less Common)
*   **Mechanism**: Synchronous HTTPS/REST calls to internal API endpoints exposed by Notification Service (secured by `@ecommerce-platform/auth-client-utils`).
*   **Purpose**: 
    *   Specific administrative actions (e.g., an Admin Portal triggering a test notification).
    *   Rare, critical, immediate notification scenarios where event-driven latency is unacceptable (use with extreme caution to avoid tight coupling).
*   **Considerations**: Introduces tighter coupling and synchronous dependencies. Should be minimized in favor of event-driven integration.

### 2.3. API Calls *to* Internal Microservices (for Data Enrichment - Use Sparingly)
*   **Mechanism**: Synchronous HTTPS/REST calls from Notification Service to other internal services.
*   **Purpose**: To fetch additional data required for notification personalization if not available in the triggering event (e.g., fetching detailed user preferences or profile information from User Service if only `userId` is in the event).
*   **Key Services Integrated With (Examples)**:
    *   **User Service**: To get user details (name, contact info if not in event, specific preferences).
*   **Considerations**: 
    *   Increases latency in notification processing.
    *   Introduces runtime dependencies; if the target service is down, notification processing can be affected.
    *   Prefer carrying necessary data within the triggering event (event-carried state transfer).

## 3. Outbound Integrations (Dispatching Notifications & Status Updates)

### 3.1. External Notification Providers
*   **Mechanism**: HTTPS/REST API calls or SDKs provided by third-party services.
*   **Purpose**: To dispatch actual notifications via various channels.
*   **Key Provider Categories & Examples**:
    *   **Email**: 
        *   AWS SES (Simple Email Service)
        *   SendGrid
        *   Mailgun
    *   **SMS**: 
        *   Twilio
        *   AWS SNS (Simple Notification Service)
        *   Vonage (Nexmo)
    *   **Push Notifications**:
        *   Firebase Cloud Messaging (FCM) for Android & Web
        *   Apple Push Notification service (APNs) for iOS
    *   **Webhooks**: (If Notification Service supports sending webhooks to external partner systems)
        *   Direct HTTPS POST calls to configured partner URLs.
*   **Data Contract**: Provider-specific API request/response formats.
*   **Security**: Secure management of API keys, tokens, and credentials for these providers (using `@ecommerce-platform/nestjs-core-utils` `ConfigModule` integrated with a secrets manager like AWS Secrets Manager or HashiCorp Vault).

### 3.2. Provider Callback Webhooks (Inbound to Notification Service)
*   **Mechanism**: HTTPS POST requests from external providers to dedicated callback endpoints hosted by the Notification Service.
*   **Purpose**: To receive asynchronous updates on notification delivery status (e.g., delivered, bounced, failed, opened, clicked).
*   **Key Providers (Examples)**:
    *   AWS SES (via SNS topics)
    *   Twilio
    *   SendGrid
*   **Data Contract**: Provider-specific webhook payload formats.
*   **Security**: Endpoints must be secured using provider-specific mechanisms (e.g., signature verification for Twilio/AWS SNS, IP whitelisting if applicable).

## 4. Internal Shared Libraries

*   **`@ecommerce-platform/rabbitmq-event-utils`**: For consuming and publishing events via RabbitMQ.
*   **`@ecommerce-platform/nestjs-core-utils`**: For logging, configuration, common error handling, health checks.
*   **`@ecommerce-platform/auth-client-utils`**: For securing any exposed API endpoints.
*   **`@ecommerce-platform/testing-utils`**: For common testing utilities.

## 5. Integration Diagram (Conceptual)

```mermaid
graph LR
    subgraph ECommerce Platform
        UserService[User Service]
        OrderService[Order Service]
        PaymentService[Payment Service]
        InventoryService[Inventory Service]
        AdminPortal[Admin Portal/Tools]
        NS[Notification Service]
    end

    subgraph External Providers
        EmailGw[Email Gateway (e.g., SES)]
        SmsGw[SMS Gateway (e.g., Twilio)]
        PushGw[Push Gateway (e.g., FCM)]
    end

    UserService -- Publishes Events --> RMQ[(RabbitMQ)]
    OrderService -- Publishes Events --> RMQ
    PaymentService -- Publishes Events --> RMQ
    InventoryService -- Publishes Events --> RMQ

    RMQ -- Consumes Events --> NS

    AdminPortal -- Admin API Calls --> NS

    NS -- Dispatch Calls --> EmailGw
    NS -- Dispatch Calls --> SmsGw
    NS -- Dispatch Calls --> PushGw

    EmailGw -- Webhook Callbacks --> NS
    SmsGw -- Webhook Callbacks --> NS
    PushGw -- (Status APIs/Callbacks) --> NS
    
    NS -- (Optional) API calls for data --> UserService
```

This diagram illustrates the primary integration flows. The Notification Service is central for communications, reacting to internal events and interacting with external gateways.
