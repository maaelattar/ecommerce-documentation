# Notification Service - Core Service Components

## 1. Overview

The Notification Service is designed as a modular NestJS application. Its core components handle the lifecycle of a notification: receiving a trigger, processing it, interacting with providers, and tracking its status.

## 2. Architectural Layers and Key Modules

```mermaid
graph TD
    subgraph "Notification Service"
        A[Event Consumers / API Layer]
        B[Orchestration & Processing Layer]
        C[Templating Engine]
        D[Provider Integration Layer]
        E[Data Persistence Layer]
        F[Shared Utilities]

        A --> B
        B --> C
        B --> D
        B --> E
        C --> E  # (Templates might be stored in DB)
        D --> F  # (e.g., for secure credential management)
        B --> F  # (e.g., for logging, config)
    end

    X[Other Microservices] -- Publishes Events --> A
    Y[External Notification Providers] <-- HTTP/SDK Calls --> D
    Z[Database: PostgreSQL/DynamoDB] <-- CRUD --> E
```

### 2.1. Event Consumers / API Layer (`NotificationTriggerModule`)

*   **Responsibilities**: 
    *   Receives incoming requests to send notifications. This is primarily achieved by consuming events from other microservices via RabbitMQ (using `@ecommerce-platform/rabbitmq-event-utils`).
    *   May expose a minimal internal API for specific use cases (e.g., administrative-triggered notifications, or a "send test notification" endpoint).
*   **Key Components**:
    *   `RabbitMQEventConsumer`: Subscribes to relevant topics/queues from other services (e.g., `order.OrderCreated`, `user.PasswordResetRequested`). Uses message handlers (e.g., `@RabbitListener` from a potential NestJS RabbitMQ utility or custom setup) to trigger notification processing.
    *   `NotificationRequestController` (Optional, internal API): Handles direct HTTP requests for notifications.
    *   `NotificationRequestDTOs`: Data Transfer Objects for incoming event payloads or API requests.
    *   `NotificationRequestValidationPipe`: Validates incoming DTOs.

### 2.2. Orchestration & Processing Layer (`NotificationOrchestrationModule`)

*   **Responsibilities**:
    *   Coordinates the overall notification workflow.
    *   Retrieves user communication preferences.
    *   Fetches necessary data (if not fully event-carried) from other services (with caution, preferring event-carried state).
    *   Selects the appropriate notification channel(s) and template(s).
    *   Invokes the Templating Engine to render the notification content.
    *   Handles scheduling and dispatch priority.
    *   Manages retries for processing steps (not provider dispatch retries, which are handled lower down).
    *   Logs the notification attempt and its initial status.
*   **Key Components**:
    *   `NotificationProcessingService`: Core service orchestrating the steps.
    *   `PreferenceService`: Interacts with the Data Persistence Layer to fetch user preferences.
    *   `ChannelSelectionStrategy`: Logic to decide which channel(s) to use based on event type, user preference, and context.
    *   `NotificationJobQueue` (Optional, e.g., using BullMQ): If notifications need to be queued for scheduled dispatch or for handling high volumes.

### 2.3. Templating Engine (`TemplatingModule`)

*   **Responsibilities**:
    *   Manages notification templates (potentially stored in a database or versioned files).
    *   Renders personalized notification content using a chosen templating language (e.g., Handlebars, Nunjucks, or a more sophisticated multi-channel template management system).
    *   Supports localization/internationalization (i18n) of templates.
*   **Key Components**:
    *   `TemplateRepository`: Fetches templates from storage.
    *   `TemplateRenderingService`: Takes a template ID/name and a data context, and returns the rendered content (e.g., HTML for email, plain text for SMS).
    *   `LocalizationService`: Provides localized strings or template variants.

### 2.4. Provider Integration Layer (`ProviderGatewayModule`)

*   **Responsibilities**:
    *   Abstracts interactions with external third-party notification providers (e.g., AWS SES, Twilio, Firebase Admin SDK).
    *   Handles provider-specific API calls, authentication, and error mapping.
    *   Implements retry logic for transient provider errors.
    *   Manages provider-specific configurations and credentials securely (e.g., via `@ecommerce-platform/nestjs-core-utils` `ConfigModule` and a secrets manager).
*   **Key Components (Examples)**:
    *   `EmailProviderService` (e.g., `SesEmailService`): Interface and implementation for sending emails.
    *   `SmsProviderService` (e.g., `TwilioSmsService`): Interface and implementation for sending SMS.
    *   `PushProviderService` (e.g., `FcmPushService`): Interface and implementation for sending push notifications.
    *   `WebhookProviderService`: Interface and implementation for sending webhook notifications.
    *   Provider-specific DTOs and mappers.

### 2.5. Data Persistence Layer (`PersistenceModule`)

*   **Responsibilities**:
    *   Manages all data storage for the Notification Service.
    *   Stores notification templates, user communication preferences, notification logs/history, and potentially scheduled notification jobs.
*   **Technology**: PostgreSQL (primary relational store), potentially complemented by DynamoDB for high-volume logs or specific NoSQL use cases (to be decided by ADR).
*   **Key Components**:
    *   TypeORM Entities: `NotificationTemplate`, `UserPreference`, `NotificationLog`, `NotificationJob` (if using a DB-backed queue).
    *   Repositories: For CRUD operations on entities.
    *   Database migration scripts.

### 2.6. Shared Utilities & Cross-Cutting Concerns

*   **`@ecommerce-platform/nestjs-core-utils`**: Used for logging, configuration management, error handling, health checks.
*   **`@ecommerce-platform/rabbitmq-event-utils`**: Used for consuming events (if this service listens to RabbitMQ) and for publishing its own events (via the Outbox pattern described in `05-event-publishing`).
*   **Authentication/Authorization**: If exposing APIs, secures them using `@ecommerce-platform/auth-client-utils` (e.g., for internal admin APIs).
*   **Scheduling Module (`ScheduleModule` from `@nestjs/schedule`)**: For periodic tasks like the outbox processor or cleaning up old logs.

## 3. Workflow Example (Order Confirmation Email)

1.  **Event Consumer**: Receives `OrderCreatedEvent` from RabbitMQ.
2.  **NotificationOrchestrationModule**: `NotificationProcessingService` is invoked.
    *   Fetches user preferences for 'order_confirmation' (e.g., user wants email).
    *   Confirms email channel is appropriate.
3.  **TemplatingModule**: `TemplateRenderingService` fetches the 'order_confirmation_email' template and renders it with data from the `OrderCreatedEvent` payload.
4.  **ProviderGatewayModule**: `SesEmailService` is called with the rendered HTML email, recipient address, and subject.
    *   `SesEmailService` interacts with AWS SES API to send the email.
5.  **PersistenceModule**: `NotificationLog` entry is created/updated with status (e.g., 'SENT_TO_PROVIDER', then later 'DELIVERED' or 'BOUNCED' via webhook callback).
6.  **Event Publishing**: If the email is successfully handed off to SES, `NotificationProcessingService` might use `EventPublisherService` to queue a `NotificationSentEvent` via the outbox.
