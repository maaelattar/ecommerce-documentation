# Notification Service: Channel Integrations

## 1. Introduction

*   **Purpose**: This document specifies how the Notification Service connects to and interacts with various third-party notification delivery services (channels). It provides detailed guidelines for implementing the `ChannelIntegrator` components (e.g., `EmailService`, `SmsService`, `PushNotificationService`) introduced in [03-core-service-components.md](./03-core-service-components.md).
*   **`ChannelIntegrator` Components**: Each `ChannelIntegrator` is responsible for encapsulating the logic required to send notifications through a specific channel provider, handling authentication, API calls, and provider-specific error management.

## 2. Supported Channels and Providers

The Notification Service will initially support Email, SMS, and Push Notifications. The choice of providers is guided by factors such as cost-effectiveness (especially leveraging existing cloud infrastructure as per **ADR-042: Cloud Provider Selection - AWS**), feature set, reliability, and ease of integration.

### 2.1. Email Channel

*   **Primary Provider Choice**: **Amazon Simple Email Service (AWS SES)**
*   **Justification**:
    *   **Cost-Effective**: Generally offers a competitive pricing model, especially when sending at scale.
    *   **Scalability & Reliability**: Built to handle large volumes of email.
    *   **AWS Ecosystem Integration**: Aligns with **ADR-042** by leveraging the existing AWS infrastructure. Easy integration with other AWS services like IAM for authentication and SNS for bounce/complaint handling.
    *   **Features**: Supports DKIM, SPF, dedicated IPs (optional), configuration sets for detailed event tracking.
*   **Fallback Provider**: Not planned for the initial version. Could consider SendGrid or Mailgun in the future if specific SES limitations are encountered.
*   **Authentication Method**: **IAM Roles** (preferred for services running on AWS infrastructure like EC2/ECS/EKS, providing secure, temporary credentials). API keys can be used for local development if necessary.
*   **Key API Endpoints/SDKs Used**:
    *   AWS SDK for JavaScript v3: `@aws-sdk/client-ses`
    *   `SendEmailCommand`: For sending formatted emails (HTML and/or Text).
    *   `SendRawEmailCommand`: For more complex scenarios, like sending emails with attachments or custom headers.
*   **Configuration Parameters Needed (as per ADR-016)**:
    *   `AWS_REGION`: e.g., "us-east-1"
    *   `SES_SENDER_EMAIL_ADDRESS`: The default "From" email address.
    *   `SES_CONFIGURATION_SET_NAME`: (Optional but recommended) For publishing email sending events (sends, deliveries, bounces, complaints).
    *   `SES_REPLY_TO_ADDRESSES`: (Optional) Default reply-to addresses.

### 2.2. SMS Channel

*   **Primary Provider Choice**: **Twilio Programmable SMS**
*   **Justification**:
    *   **Reliability & Deliverability**: Strong global carrier network and reputation for message deliverability.
    *   **Feature-Rich API**: Comprehensive API for sending messages, managing numbers, receiving delivery reports, handling opt-outs, and more.
    *   **Developer Experience**: Good documentation and SDKs.
    *   **Scalability**: Proven to handle large volumes.
*   **Fallback Provider**: Not planned for the initial version. Could consider Vonage (Nexmo) or AWS SNS (for SMS, though it has limitations in some regions/features compared to dedicated providers like Twilio).
*   **Authentication Method**: **Account SID and Auth Token** (API Key).
*   **Key API Endpoints/SDKs Used**:
    *   Twilio Node.js SDK: `twilio`
    *   `client.messages.create()`: To send SMS messages.
*   **Configuration Parameters Needed (as per ADR-016)**:
    *   `TWILIO_ACCOUNT_SID`: Account SID from Twilio.
    *   `TWILIO_AUTH_TOKEN`: Auth Token from Twilio.
    *   `TWILIO_SENDER_PHONE_NUMBER`: Default sender phone number or Messaging Service SID.
    *   `TWILIO_WEBHOOK_URL_DLR`: (Optional) Endpoint in Notification Service to receive delivery reports.
    *   `TWILIO_WEBHOOK_URL_INBOUND`: (Optional) Endpoint to receive inbound messages (e.g., STOP replies).

### 2.3. Push Notification Channel

*   **Primary Provider Choice**: **Amazon Simple Notification Service (AWS SNS)** as a unified gateway.
*   **Justification**:
    *   **Unified Endpoint**: SNS can manage communications with multiple push notification platforms (APNS for iOS, FCM for Android, etc.) through a single API.
    *   **AWS Ecosystem Integration**: Aligns with **ADR-042**. Integrates with IAM for secure authentication.
    *   **Scalability**: Designed for high-throughput message delivery.
    *   **Cost-Effective**: Pay-as-you-go pricing.
*   **Fallback Provider**: Not planned for the initial version. Could consider direct integration with Firebase Cloud Messaging (FCM) or OneSignal if specific features are needed that SNS abstracts poorly.
*   **Authentication Method**: **IAM Roles** for services running on AWS.
*   **Key API Endpoints/SDKs Used**:
    *   AWS SDK for JavaScript v3: `@aws-sdk/client-sns`
    *   `PublishCommand`: To send messages to a specific device endpoint (target ARN) or an SNS topic (if managing topic subscriptions).
    *   APIs for creating and managing Platform Applications and Endpoints in SNS (e.g., `CreatePlatformApplicationCommand`, `CreatePlatformEndpointCommand`) - typically handled during device registration by another service.
*   **Configuration Parameters Needed (as per ADR-016)**:
    *   `AWS_REGION`: e.g., "us-east-1"
    *   `SNS_PLATFORM_APPLICATION_ARN_FCM`: ARN for the FCM platform application in SNS.
    *   `SNS_PLATFORM_APPLICATION_ARN_APNS`: ARN for the APNS platform application in SNS.
    *   `SNS_PLATFORM_APPLICATION_ARN_APNS_SANDBOX`: ARN for the APNS sandbox platform application.

## 3. Channel-Specific Implementation Details

### 3.1. Email Integration (AWS SES)

*   **Sender Email Addresses/Domains**:
    *   Must be verified in AWS SES within the specified region.
    *   Domain verification (using DKIM and SPF records in DNS, e.g., AWS Route 53) is preferred over individual email address verification for better deliverability and management.
    *   The `SES_SENDER_EMAIL_ADDRESS` configuration will specify the default "From" address.
*   **Handling Bounces and Complaints**:
    *   Configure AWS SES to publish bounce, complaint, and delivery events to an SNS topic.
    *   An SQS queue can subscribe to this SNS topic.
    *   A dedicated worker process (or a Lambda function) within the Notification Service (or a separate microservice) will poll this SQS queue.
    *   **Actions**:
        *   **Hard Bounces/Complaints**: Mark the email address as invalid/unsubscribed in the User Service or a dedicated suppression list within the Notification Service to prevent future sends. Log the event.
        *   **Soft Bounces**: Log the event; may implement a retry mechanism or temporary suppression after multiple soft bounces.
*   **MIME Types**:
    *   The `EmailService` must support sending both HTML and Plain Text versions of emails. This is typically done using a multipart/alternative MIME type. The `TemplateManager` will provide both HTML and text templates.
*   **Attachments**:
    *   Support for attachments is **deferred for the initial version** to maintain simplicity.
    *   If implemented later, `SendRawEmailCommand` in SES would be used, requiring construction of the raw email MIME message.
*   **Rate Limits and Throttling**:
    *   AWS SES imposes sending quotas (emails per second, emails per day) which vary by account and region.
    *   The `EmailService` should be aware of these limits. While SES handles some internal queuing, for very high burst rates, the application might need to implement its own throttling or use a message queue to smooth out the sending rate.
    *   Monitor SES sending metrics in CloudWatch.

### 3.2. SMS Integration (Twilio)

*   **Sender Phone Numbers/Short Codes**:
    *   Configured via `TWILIO_SENDER_PHONE_NUMBER`. This can be a long code, short code, or Toll-Free number purchased and configured in the Twilio console.
    *   Using a Twilio Messaging Service SID is recommended as it allows for scaling across multiple numbers, geo-matching, and other advanced features.
*   **Message Encoding and Length Limits**:
    *   Standard SMS: GSM 03.38 character set (160 characters per segment).
    *   Unicode (e.g., for emojis): UCS-2 encoding (70 characters per segment).
    *   The Twilio SDK typically handles segmentation for messages longer than the limit (multi-part SMS). The service should be mindful of message length to control costs.
*   **Delivery Reports (DLRs)**:
    *   Configure a webhook URL in Twilio settings to point to an endpoint in the Notification Service (e.g., `/webhooks/twilio/sms-status`).
    *   This endpoint will receive status updates (e.g., `sent`, `delivered`, `failed`, `undelivered`).
    *   The service will update the status of the corresponding `NotificationAttempt` record (if used).
*   **Opt-out Handling**:
    *   Twilio handles standard English opt-out keywords (STOP, UNSUBSCRIBE) automatically for long codes and short codes based on carrier compliance.
    *   Configure Twilio to forward opt-out messages to a webhook so the Notification Service (or User Service) can update user preferences and maintain a suppression list.
*   **Rate Limits**:
    *   Twilio imposes rate limits based on sender number type (e.g., 1 MPS for long codes by default in the US, higher for short codes).
    *   The `SmsService` should implement appropriate error handling for rate limit responses from Twilio (e.g., HTTP 429). For high volume, queuing messages internally before sending might be necessary.

### 3.3. Push Notification Integration (AWS SNS)

*   **Platform Support**:
    *   SNS supports various platforms, including:
        *   **FCM (Firebase Cloud Messaging)** for Android.
        *   **APNS (Apple Push Notification service)** for iOS.
        *   APNS_SANDBOX for iOS development builds.
*   **Platform Application Credentials Management**:
    *   FCM Server Keys (for Android) and APNS Certificates/Authentication Keys (for iOS) must be configured within AWS SNS by creating "Platform Applications".
    *   The ARNs of these SNS Platform Applications are configured in the Notification Service (`SNS_PLATFORM_APPLICATION_ARN_FCM`, etc.).
*   **Device Token Management**:
    *   **Collection & Storage**: Client applications (iOS, Android, Web) are responsible for obtaining device tokens from their respective push notification services (FCM, APNS). These tokens are then sent to a backend service (e.g., User Service or a dedicated DeviceRegistration Service) and stored, associated with a user.
    *   **Receiving Tokens for Sending**: The Notification Service expects to receive the target device token(s) as part of the event payload that triggers the push notification (e.g., `OrderShippedEvent` might include `userId`, and the `NotificationDispatcher` would then fetch device tokens for that user from the User Service or a shared cache). Alternatively, a list of tokens could be directly provided in the event.
*   **Payload Structure**:
    *   The `PushNotificationService` will construct a JSON message payload. SNS requires this payload to be a JSON string, containing a top-level key for the default message and platform-specific keys (e.g., `GCM` for FCM, `APNS` for APNS).
    *   Example:
        ```json
        {
          "default": "Your order has been shipped!",
          "GCM": "{ \"notification\": { \"title\": \"Order Shipped\", \"body\": \"Your package is on its way!\" }, \"data\": { \"orderId\": \"123\", \"deepLink\": \"myapp://order/123\" } }",
          "APNS": "{ \"aps\": { \"alert\": { \"title\": \"Order Shipped\", \"body\": \"Your package is on its way!\" }, \"badge\": 1, \"sound\": \"default\" }, \"orderId\": \"123\", \"deepLink\": \"myapp://order/123\" }"
        }
        ```
    *   The `TemplateManager` will be responsible for generating these platform-specific JSON structures.
*   **Handling Token Expiry/Invalidation**:
    *   SNS provides feedback on message delivery attempts, including information about invalid or expired tokens (e.g., through CloudWatch Logs or event destinations for SNS).
    *   The Notification Service (or the service managing device tokens) should have a mechanism to process this feedback and remove invalid/expired tokens from the system to prevent further attempts and improve efficiency.
*   **Deep Linking**:
    *   Deep links (e.g., `myapp://order/123`) will be included in the `data` payload of the push notification. Client applications are responsible for handling these deep links to navigate the user to the appropriate screen.
*   **Rate Limits**:
    *   AWS SNS has high default quotas, but it's essential to be aware of them. Individual platforms (FCM, APNS) may also have their own fair-use policies.

## 4. Error Handling and Retries for Channel Integrations

*   **Common Error Types**:
    *   **Invalid Recipient**: Email address doesn't exist, phone number invalid/not registered, push token expired/invalid.
    *   **Authentication Failure**: Incorrect API keys/credentials for the provider.
    *   **Authorization Failure**: Credentials valid, but not authorized for the specific action (e.g., sending from an unverified email).
    *   **Provider Service Unavailable**: Transient issues with the third-party provider.
    *   **Rate Limiting/Throttling**: Sending too many requests in a short period.
    *   **Content Issues**: Message blocked due to content filters (spam, prohibited content).
    *   **Account Issues**: Account suspension, insufficient funds (for paid services).
*   **Retry Strategy**:
    *   The `ChannelIntegrator` services should implement a retry mechanism for transient errors (e.g., network timeouts, temporary provider unavailability, certain types of rate limiting).
    *   **Exponential Backoff with Jitter**: This is the recommended approach to avoid overwhelming the provider and to handle correlated failures.
    *   **Configurable Retry Attempts**: The number of retry attempts should be configurable.
*   **Permanent Failures**:
    *   For errors like invalid recipient, authentication failure (that isn't transient), or consistent content blocking, retries are unlikely to succeed.
    *   These should be logged as permanent failures.
    *   If a `NotificationAttemptRepository` is used, the status should be updated to `FAILED` with error details.
    *   Alerts might be triggered for high rates of permanent failures.

## 5. Scalability and Throughput

*   **SDK Client Management**:
    *   Instantiate SDK clients (e.g., SES client, Twilio client, SNS client) once and reuse them (singleton pattern within the service context or managed by NestJS DI) to avoid overhead of re-creating clients and re-establishing connections for every request.
    *   Ensure clients are configured with appropriate timeouts and connection settings.
*   **Asynchronous Operations**: All calls to external providers must be asynchronous (`async/await`) to prevent blocking the Node.js event loop.
*   **Concurrency Management**:
    *   If sending very large batches of notifications, manage concurrency to stay within provider rate limits and to avoid overwhelming the service itself (e.g., using `Promise.allSettled` with batches, or a job queue like BullMQ if processing becomes very intensive).
*   **Provider Limits**: Be aware of and respect the sending quotas and rate limits imposed by each provider. Design the system to either stay within these limits or to handle rate limit errors gracefully.
*   **Horizontal Scaling**: The Notification Service itself should be designed to be stateless (or manage state externally, e.g., in Redis or a database if using BullMQ) to allow for horizontal scaling of instances.

## 6. Security Considerations

*   **Secure Storage of API Keys and Credentials**:
    *   All API keys, tokens, and other secrets must be stored securely and managed as per **ADR-016 (Configuration Management)**. This typically involves using environment variables injected into the application, with secrets managed by a secrets management system (e.g., AWS Secrets Manager, HashiCorp Vault) in production environments.
    *   Avoid committing secrets directly into the codebase.
*   **Input Validation**:
    *   While SDKs often handle some level of input sanitization, always validate data received from events or API calls before passing it to channel providers. This is especially important if constructing any part of the message payload dynamically beyond simple template variable substitution.
    *   For example, ensure URLs in messages are well-formed and not malicious.
*   **Least Privilege**: IAM roles used for AWS services (SES, SNS) should be configured with the minimum necessary permissions.
*   **Webhook Security**: If exposing webhooks (e.g., for Twilio DLRs or SES bounce notifications via HTTPS endpoint), ensure they are secured:
    *   Use HTTPS.
    *   Validate webhook signatures (e.g., Twilio's request validation).
    *   Consider IP whitelisting if provider IPs are stable and known.

This document provides the framework for integrating with various notification channels. The specific implementation of each `ChannelIntegrator` will need to handle the nuances of the chosen provider's API and best practices.
