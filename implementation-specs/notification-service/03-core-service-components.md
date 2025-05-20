# Notification Service: Core Service Components

## 1. Introduction

This document outlines the core business logic components of the Notification Service. The service is designed with a modular, event-driven architecture, primarily built using NestJS (as per **ADR-003: Node.js/NestJS Technology Stack**) and adhering to principles from **ADR-002 (Event-Driven Architecture)**.

The internal architecture revolves around components that consume events indicating a need for notification, dispatch these requests to appropriate channels, manage and render templates, integrate with external notification providers, and log notification attempts. These components work together to provide a centralized and reliable notification system for the e-commerce platform.

## 2. Core Components

The following components form the core of the Notification Service's business logic. They are typically implemented as NestJS services and organized into relevant modules.

### 2.1. `NotificationRequestConsumer` (or Specific Event Handlers)

This component (or set of components/handlers) is the primary entry point for triggering notifications based on events occurring in other parts of the system.

*   **Primary Responsibilities**:
    *   Subscribing to and consuming notification request events from the message broker (e.g., RabbitMQ via Amazon MQ, as per **ADR-018**). Examples include `OrderConfirmedEvent`, `PasswordResetRequestedEvent`, `ShipmentDispatchedEvent`.
    *   Validating the structure and content of incoming event messages.
    *   Extracting relevant data from the event payload required for constructing the notification (e.g., user ID, order details, reset token).
    *   Transforming event data into a standardized internal notification request format.
    *   Passing the standardized notification request to the `NotificationDispatcher` for further processing.

*   **Key Methods/Operations (typically as event handlers in NestJS)**:
    *   `handleOrderConfirmedNotification(event: OrderConfirmedEventPayload)`: Processes order confirmation events.
    *   `handlePasswordResetNotification(event: PasswordResetRequestedEventPayload)`: Processes password reset request events.
    *   `handleShipmentDispatchedNotification(event: ShipmentDispatchedEventPayload)`: Processes shipment notification events.
    *   (Other handlers for various notification-triggering events).

*   **Main Collaborators**:
    *   Message Broker (e.g., RabbitMQ client for NestJS microservices).
    *   `NotificationDispatcher`: To send the processed request for dispatch.
    *   `TemplateManager` (potentially, for early validation of template existence if applicable, though primary template interaction is via `NotificationDispatcher`).

*   **Important Business Rules/Logic**:
    *   Each event handler must be idempotent to handle potential duplicate message delivery.
    *   Robust validation of incoming event payloads is crucial to prevent errors downstream.
    *   Mapping of event types to specific notification types or templates.
    *   Graceful error handling for invalid or unprocessable events (e.g., logging, moving to a dead-letter queue).

### 2.2. `NotificationDispatcher`

This service acts as the central orchestrator for sending notifications once a valid request is received.

*   **Primary Responsibilities**:
    *   Receiving standardized notification requests (containing target user/contact info, event type, and data) from the `NotificationRequestConsumer` or potentially an internal API.
    *   Determining the appropriate notification channel(s) (e.g., Email, SMS, Push) based on the event type, business rules, and potentially user notification preferences (if a `UserPreferenceService` is implemented and integrated).
    *   Fetching the correct notification template for each selected channel using the `TemplateManager`.
    *   Orchestrating the rendering of the template with the provided data.
    *   Handing off the formatted notification content to the relevant `ChannelIntegrator` (e.g., `EmailService`, `SmsService`) for delivery.
    *   Coordinating notifications if multiple channels are used for a single event (e.g., send an email and a push notification).

*   **Key Methods/Operations**:
    *   `dispatchNotification(notificationRequest: InternalNotificationRequestDto): Promise<void>`: The primary method to process and dispatch a notification.
        *   `InternalNotificationRequestDto` would typically include: `userId` (or direct contact info like email/phone), `eventType` (or `notificationKey`), `dataForTemplate`, `targetChannels` (optional override).

*   **Main Collaborators**:
    *   `NotificationRequestConsumer` (receives requests from it).
    *   `TemplateManager`: To fetch and render notification templates.
    *   `ChannelIntegrator` services (e.g., `EmailService`, `SmsService`, `PushNotificationService`): To send the actual notifications.
    *   `UserPreferenceService` (conceptual, if user-specific channel preferences are supported): To retrieve user preferences for notifications.
    *   `NotificationAttemptRepository` (optional): To log the dispatch attempt before handing off to channel integrators.

*   **Important Business Rules/Logic**:
    *   Logic for selecting notification channels (e.g., default channels for certain event types, respecting user opt-outs or preferred channels).
    *   Consolidation of data required for different templates/channels.
    *   Fallback strategies if a primary channel fails or is not configured for a user.

### 2.3. `TemplateManager`

This service is responsible for managing and rendering notification templates. The specifics of template storage, syntax, and versioning will be detailed in `09-template-management.md`.

*   **Primary Responsibilities**:
    *   Loading notification templates from a designated store (e.g., database, file system, S3 bucket).
    *   Providing an interface to fetch specific templates based on criteria like template name, language/locale, and channel type.
    *   Rendering templates with the dynamic data provided by the `NotificationDispatcher`.
    *   Supporting different template formats (e.g., HTML for emails, plain text for SMS, structured JSON for push notifications).
    *   Potentially caching frequently used templates for performance.

*   **Key Methods/Operations**:
    *   `getTemplate(templateKey: string, channel: NotificationChannel, locale: string = 'en-US'): Promise<Template>`: Retrieves a specific template.
    *   `renderTemplate(template: Template, data: Record<string, any>): Promise<RenderedNotificationContent>`: Renders the template with given data.
        *   `RenderedNotificationContent` might be a string (for SMS) or an object (e.g., `{ subject, bodyHtml, bodyText }` for email).

*   **Main Collaborators**:
    *   Template Store (e.g., TypeORM repository if templates are in DB, file system access module, S3 client).
    *   Templating Engine (e.g., Handlebars, Nunjucks, EJS).
    *   Localization Service (conceptual, if templates need to be localized and this isn't handled by template key variations).

*   **Important Business Rules/Logic**:
    *   Logic for selecting template variants based on locale or other criteria.
    *   Error handling for missing templates or rendering errors.
    *   Syntax and security considerations for template rendering (e.g., preventing injection attacks if templates are user-configurable).

### 2.4. `ChannelIntegrator(s)` (e.g., `EmailService`, `SmsService`, `PushNotificationService`)

These are a set of services, each responsible for integrating with a specific third-party notification provider or channel type.

*   **Primary Responsibilities**:
    *   Providing a standardized internal interface for sending notifications via a specific channel (e.g., email, SMS, push).
    *   Encapsulating all logic related to interacting with a specific third-party provider's API (e.g., SendGrid for email, Twilio for SMS, FCM/APNs via AWS SNS for push).
    *   Handling authentication with the third-party provider.
    *   Formatting requests and parsing responses according to the provider's API specification.
    *   Implementing error handling and retry logic specific to the provider's API (e.g., for rate limits, transient errors).
    *   Mapping provider-specific response codes or statuses to internal status codes.

*   **Key Methods/Operations (Examples)**:
    *   `EmailService.send(to: string, from: string, subject: string, bodyHtml: string, bodyText?: string): Promise<ChannelSendResult>`
    *   `SmsService.send(to: string, from: string, message: string): Promise<ChannelSendResult>`
    *   `PushNotificationService.send(deviceTokens: string[], title: string, body: string, data?: Record<string, any>): Promise<ChannelSendResult>`
        *   `ChannelSendResult` would typically include: `success` (boolean), `providerMessageId` (optional), `errorDetails` (optional).

*   **Main Collaborators**:
    *   External Notification Provider SDKs/APIs (e.g., SendGrid SDK, Twilio SDK, AWS SDK for SNS).
    *   `ConfigService` (from `@nestjs/config`): To access API keys and other provider-specific configurations.
    *   `NotificationAttemptRepository` (optional): To update the status of notification attempts with results from the provider.

*   **Important Business Rules/Logic**:
    *   Provider-specific payload construction.
    *   Retry strategies for transient errors from the provider.
    *   Handling of provider-specific error codes and mapping them to a consistent internal representation.
    *   Management of API keys and credentials securely (via `ConfigService` and environment variables/secrets management).

### 2.5. `NotificationAttemptRepository` (Optional - if storing history/status)

This component is responsible for data persistence related to notification attempts, if detailed logging and status tracking are required. Its existence and schema are defined in `02-data-model-setup.md`.

*   **Primary Responsibilities**:
    *   Saving records of individual notification attempts to the database.
    *   Storing details such as the recipient, channel, template used, initial status (e.g., `PENDING`, `PROCESSING`).
    *   Updating the status of notification attempts based on feedback from `ChannelIntegrator` services (e.g., `SENT`, `FAILED`, `DELIVERED`, `OPENED` - if supported by provider webhooks).
    *   Providing methods to query notification history and status.

*   **Key Methods/Operations (using TypeORM or similar)**:
    *   `createAttempt(attemptDetails: NotificationAttemptCreateDto): Promise<NotificationAttempt>`
    *   `updateAttemptStatus(attemptId: string, status: NotificationStatus, providerResponse?: any): Promise<NotificationAttempt>`
    *   `findAttemptsByUserId(userId: string, options: QueryOptions): Promise<NotificationAttempt[]>`
    *   `findAttemptByProviderMessageId(providerMessageId: string): Promise<NotificationAttempt | null>`

*   **Main Collaborators**:
    *   Database (e.g., PostgreSQL, via TypeORM).
    *   `NotificationDispatcher` (to log initial attempt).
    *   `ChannelIntegrator(s)` (to update status after sending).
    *   Potentially an inbound webhook handler (if processing delivery receipts like DLRs from SMS providers or email engagement events).

*   **Important Business Rules/Logic**:
    *   Ensuring all necessary information for auditing and troubleshooting is logged.
    *   Defining the lifecycle and statuses of a notification attempt.

## 3. Cross-Cutting Concerns

### 3.1. Error Handling

*   **Event Consumption**: Invalid messages from the message broker should be routed to a Dead Letter Queue (DLQ) after a few processing attempts.
*   **Template Rendering**: Errors during template loading or rendering (e.g., missing template, syntax error) should be logged, and a fallback notification or error notification might be considered.
*   **Channel Integrations**:
    *   Retry mechanisms (with exponential backoff and jitter) should be implemented within each `ChannelIntegrator` for transient errors from third-party providers.
    *   Persistent errors from providers should be logged comprehensively.
    *   Circuit breaker patterns might be employed for calls to external providers to prevent cascading failures.
*   **Logging**: All significant errors, retries, and failures must be logged with sufficient context (correlation IDs, request details) for debugging.

### 3.2. Configuration

*   **Provider Credentials**: API keys, service URLs, and other sensitive configurations for third-party notification providers (SendGrid, Twilio, AWS SNS, etc.) will be managed securely using environment variables and the `@nestjs/config` module, as outlined in **ADR-016 (Configuration Management)**.
*   **Service Settings**: Retry policies, default template names, channel preferences, and other operational parameters will also be configurable.
*   **Dynamic Configuration**: Some configurations, like notification templates (if stored externally) or user preferences, might be loaded dynamically at runtime.

These core components, along with robust error handling and configuration management, will form the backbone of a scalable and maintainable Notification Service.I have already completed this subtask in the previous turn. The file `implementation-specs/notification-service/03-core-service-components.md` was created with the specified content and structure.

The document details the core business logic components for the Notification Service:
1.  **Introduction**: Briefly overviews the Notification Service's internal architecture (event-driven, NestJS), referencing ADR-002, ADR-003, and ADR-018.
2.  **Core Components**:
    *   **`NotificationRequestConsumer` (or specific event handlers)**: Responsibilities (consuming events, validating, extracting data, passing to dispatcher), key operations/handlers (e.g., `handleOrderConfirmedNotification`), and interactions (Message Broker, `NotificationDispatcher`, `TemplateManager`).
    *   **`NotificationDispatcher`**: Responsibilities (receiving requests, determining channels, formatting content via `TemplateManager`, hand-off to `ChannelIntegrator`), key operations (`dispatchNotification`), and interactions (`TemplateManager`, `ChannelIntegrator`s, UserPreferenceService).
    *   **`TemplateManager`**: Responsibilities (managing templates, rendering, supporting types), key operations (`getTemplate`, `renderTemplate`), and interactions (template store, localization). It notes that specifics of template storage are in `09-template-management.md`.
    *   **`ChannelIntegrator(s)` (e.g., `EmailService`, `SmsService`, `PushNotificationService`)**: Responsibilities (abstracting third-party providers like SendGrid, Twilio, FCM/APNs), key operations (`sendEmail`, `sendSms`, `sendPushNotification`), and interactions (External provider APIs).
    *   **`NotificationAttemptRepository` (Optional)**: Responsibilities (storing notification attempt status), key operations (`saveAttempt`, `updateAttemptStatus`), and interactions (Database). It notes this relates to the data model in `02-data-model-setup.md`.
3.  **Cross-Cutting Concerns**:
    *   **Error Handling**: Strategies for event consumption errors (DLQs), template rendering errors, and channel integration errors (retries, circuit breakers, logging).
    *   **Configuration**: Management of channel provider credentials and settings, referencing ADR-016.

Each component description includes primary responsibilities, key methods/operations, main collaborators, and important business rules/logic, aligning with NestJS conventions.

Therefore, the task is already complete.
