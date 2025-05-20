# Notification Service: Testing and CI/CD Strategy

## 1. Introduction

*   **Importance of Robust Testing**: The Notification Service is a critical component responsible for all user-facing and system communications. Ensuring its reliability, accuracy, and timeliness is paramount for user trust and operational stability. Errors can lead to missed critical alerts, duplicate messages, or incorrect information being sent, negatively impacting user experience and business operations.
*   **Challenges**:
    *   **Event-Driven Nature**: The service primarily reacts to asynchronous events, requiring testing strategies that can effectively simulate and verify event consumption and processing.
    *   **External Provider Dependencies**: The service heavily relies on third-party providers (AWS SES, Twilio, AWS SNS) for actual notification delivery. Testing these interactions without incurring costs, flakiness, or spamming actual users requires robust mocking and carefully planned integration testing.
*   **Relevant ADRs**: This strategy aligns with the platform's architectural guidelines:
    *   **ADR-012 (CI/CD Strategy)**: General CI/CD principles.
    *   **ADR-013 (Testing Strategy)**: Overall testing pyramid and types.
    *   **ADR-035 (Test Data Management Strategy)**: Guidelines for test data.
    *   **ADR-037 (CI/CD Pipeline Strategy)**: Standardized pipeline stages.

The goal is to build confidence in the Notification Service's ability to correctly process notification requests and interact with channel providers under various conditions.

## 2. Testing Pyramid Levels

The Notification Service will adopt a balanced testing pyramid, emphasizing comprehensive lower-level tests and targeted higher-level tests.

### 2.1. Unit Tests

*   **Scope**: Focus on individual, isolated units of code within the Notification Service.
    *   Business logic within services: e.g., `TemplateManager` rendering logic, specific mapping logic within `NotificationDispatcher` (like selecting templates or channels based on event type or user preferences), validation of event data payloads within event handlers.
    *   Helper functions, utility classes.
    *   Individual DTO validation rules.
*   **Tools**:
    *   **Jest**: Primary testing framework for NestJS.
    *   **NestJS testing utilities**: For mocking providers and creating isolated test modules.
*   **Examples**:
    *   Testing `TemplateManager.renderTemplate()` with various data inputs and ensuring correct output for different template types (HTML, text, JSON).
    *   Testing `NotificationDispatcher` logic for choosing the correct channel integrator based on input parameters.
    *   Testing the validation logic in an event handler for an `OrderConfirmedEvent` payload.
    *   Testing any data transformation logic before passing data to templates or channel integrators.

### 2.2. Integration Tests

*   **Scope**: Verify interactions between different components *within* the Notification Service.
    *   Testing the flow from an event handler (`NotificationRequestConsumer`) through the `NotificationDispatcher` to the `TemplateManager`.
    *   Testing interactions with the database if notification history, templates, or user preferences are stored there (as per `02-data-model-setup.md`).
    *   Testing interactions with a mock or embedded message broker to ensure event parsing and basic flow to business logic.
*   **Tools**:
    *   **Jest**: As the testing framework.
    *   **In-memory message broker clients/mocks**: To simulate event publishing and consumption without needing a full broker instance (e.g., `MemoryMessageBroker` from `@nestjs/microservices/helpers` or custom mocks).
    *   **Testcontainers**: For spinning up ephemeral PostgreSQL instances if the service has its own database for logs, templates, or preferences.
*   **Examples**:
    *   Simulating an `OrderConfirmedEvent` being received by a `NotificationRequestConsumer`, verifying it calls the `NotificationDispatcher` with the correct parameters.
    *   Testing the `NotificationDispatcher`'s interaction with the `TemplateManager` to ensure the correct template is fetched and rendered based on event data.
    *   If using a database for notification logs, testing that the `NotificationAttemptRepository` correctly saves and updates notification attempt records.

### 2.3. Component/Service-Level Tests

This is a critical layer for the Notification Service, focusing on testing the service as a deployable unit, including its event consumption and, most importantly, its interactions with **mocked external channel providers**.

*   **Scope**:
    *   Testing the service's ability to consume events from a real (local or test-instance) message broker.
    *   Verifying that upon consuming an event, the service correctly processes it and attempts to interact with the appropriate external channel provider (e.g., AWS SES, Twilio, AWS SNS) by calling the correct methods on their SDKs or making the correct HTTP requests to their APIs (which will be mocked).
    *   Testing retry logic and error handling when mocked providers simulate failures.
    *   If any synchronous APIs are exposed by the Notification Service (as per `04-api-layer.md`, e.g., `POST /notifications/send`), testing these against mocked channel providers.
*   **Tools**:
    *   **Jest**: As the test orchestrator.
    *   **Docker Compose**: To run the Notification Service along with a real message broker (e.g., RabbitMQ) in a controlled environment.
    *   **Mocking Frameworks for External Providers**:
        *   **SDK Mocks**: Jest's `jest.mock()` can be used to mock entire SDK modules (e.g., `@aws-sdk/client-ses`, `twilio`, `@aws-sdk/client-sns`). Specific client methods can then be mocked (e.g., `mockedSesClient.sendEmail.mockResolvedValue(...)`). This is often the most straightforward approach for provider SDKs.
        *   **HTTP API Mocks (if not using SDKs or for deeper control)**: Tools like WireMock (run as a separate Docker container), Nock (for HTTP request mocking in Node.js), or MSW (Mock Service Worker) can be used to simulate the external provider's HTTP API.
    *   **Supertest**: If testing any synchronous APIs exposed by the Notification Service.
*   **Examples**:
    *   **Event-Triggered Email**:
        1.  Publish a sample `UserRegisteredEvent` to a test RabbitMQ instance.
        2.  The Notification Service consumes the event.
        3.  Verify that the mocked AWS SES SDK's `SendEmailCommand` (or equivalent) was called with the expected parameters (recipient email, correct "From" address, subject from template, body rendered from template).
    *   **Event-Triggered SMS with Provider Failure**:
        1.  Publish an `OrderShippedEvent` to RabbitMQ.
        2.  Configure the mocked Twilio SDK's `messages.create()` to simulate a failure (e.g., throw an error or return an error response) on the first call, then succeed on a retry.
        3.  Verify the Notification Service attempts to send the SMS, logs the initial failure, retries, and then succeeds.
    *   **Manual API Send**:
        1.  If the `POST /notifications/send` API exists, send a request using Supertest.
        2.  Verify that the appropriate mocked channel provider SDK method was called with the correct data.

### 2.4. Contract Tests

*   **Scope**:
    *   **Consumer-Side (Notification Service as Consumer)**: The Notification Service consumes events from various other services (User Service, Order Service, etc.). Consumer-driven contract tests ensure that the Notification Service can correctly parse and handle the structure of events published by these provider services, even if they evolve.
    *   **Provider-Side (Notification Service as Provider)**: If the Notification Service exposes any synchronous APIs that other services consume (as per `04-api-layer.md`), it should publish contracts for these APIs.
*   **Tools**:
    *   **Pact**: A common tool for consumer-driven contract testing.
*   **Examples**:
    *   **Consumer Contract**: The Notification Service defines a Pact consumer test for an `OrderConfirmedEvent` from the Order Service. This test specifies the expected structure of the event. The Order Service would then verify this contract on its side.
    *   **Provider Contract**: If the Notification Service has a `POST /notifications/send` API, it would act as a Pact provider, verifying contracts defined by any consuming services.

### 2.5. End-to-End (E2E) Tests (Limited Scope & Staging)

*   **Scope**: Test critical notification flows in a deployed staging environment. This involves sending a *limited number* of actual notifications to designated test email accounts, phone numbers, or devices.
*   **Focus**: Primarily "happy path" scenarios for the most critical notifications (e.g., user registration email, order confirmation).
*   **Considerations**:
    *   **Cost and Quotas**: Sending real notifications can incur costs and affect provider quotas. Use sparingly.
    *   **Flakiness**: External provider delivery can be variable. Tests should be designed to be resilient.
    *   **Test Account Management**: Requires dedicated, pre-configured test email inboxes (e.g., using services like Mailinator, or dedicated test accounts in Gmail/Outlook) and test phone numbers.
    *   **Verification Mechanism**: Need a way to verify receipt. For emails, this might involve programmatically checking the test inbox via IMAP or using a service with an API. For SMS/Push, verification is harder and might rely on manual checks or observing logs.
    *   **Provider Sandboxes**: Utilize provider sandboxes where available (e.g., AWS SES Sandbox mode allows sending to verified addresses only without affecting quotas/reputation).
*   **Execution**: These tests are run less frequently, typically post-deployment to a staging environment.

## 3. Specific Testing Strategies for Channels

*   **Mocking External Providers**: This is the cornerstone of testing channel interactions.
    *   Ensure mocks can simulate:
        *   Successful delivery.
        *   Common error scenarios (invalid recipient, authentication failure, rate limits, provider downtime).
        *   Delayed responses.
    *   Mocks should allow assertion of the exact payloads sent to the provider (e.g., recipient, subject, body, API keys used implicitly).
*   **Testing Template Rendering**:
    *   Unit tests for `TemplateManager` should cover rendering of all templates with various data inputs (missing data, optional data, data with special characters).
    *   Visual regression testing for HTML email templates can be considered if complex, though might be overkill initially.
*   **Testing Fallbacks/Retries**:
    *   Component tests should verify that the retry logic within each `ChannelIntegrator` works as expected when mocked providers simulate transient failures.
    *   Test fallback logic (e.g., if SMS fails, does it attempt to send an email if configured?).

## 4. CI/CD Pipeline Stages

The CI/CD pipeline for the Notification Service will align with **ADR-012** and **ADR-037**:

1.  **Source**: Triggered on code commit/merge to main branches.
2.  **Build**: Install dependencies, compile TypeScript, build Docker image.
3.  **Test**:
    *   Linters & Static Analysis (ESLint, Prettier).
    *   **Unit Tests**.
    *   **Integration Tests** (with in-memory/mocked message broker, Testcontainers for DB if applicable).
    *   **Component Tests** (with mocked external channel providers).
    *   **Publish Consumer Contract Tests / Verify Provider Contract Tests** (Pact Broker interaction).
4.  **Security Scans**: Vulnerability scanning on Docker image (e.g., Trivy, Snyk), SAST.
5.  **Push to Registry**: Push tagged Docker image to container registry (e.g., Amazon ECR).
6.  **Deploy to Staging Environment**: Deploy the new version.
7.  **Staging Environment Specifics & Tests**:
    *   Configuration points to actual (test/sandbox) versions of message broker.
    *   Channel integrators might be configured with:
        *   AWS SES in Sandbox mode (sending only to verified test email addresses).
        *   Twilio using specific test credentials and numbers.
        *   AWS SNS for push to test devices.
    *   Run **selected E2E tests** focusing on critical notification paths.
    *   Run **Consumer Contract Tests** against other services deployed in staging.
8.  **Promote to Production**: Manual approval after successful staging validation. Blue/green or canary deployment strategies can be considered.
9.  **Post-Deployment Health Checks**: Automated checks against the production deployment (API health if exists, basic event consumption check if feasible indirectly).

## 5. Mocking and Test Data Management

Consistent with **ADR-035**:

*   **Event Payloads for Testing**:
    *   Store sample event payloads (as JSON files or in test data factories) representing various scenarios (valid data, missing optional fields, different event types). These will be used to trigger event handlers in component tests.
*   **Configuration of Mock Provider Behavior**:
    *   Tests should be able to easily configure the behavior of mocked external providers.
    *   Example:
        ```typescript
        // In a component test for SES email sending
        mockedSesClient.sendEmail.mockResolvedValueOnce({ MessageId: 'test-message-id' }); // Simulate success
        mockedSesClient.sendEmail.mockRejectedValueOnce(new Error('SES Service Unavailable')); // Simulate failure
        ```
*   **Test Data for Templates**: Use factories to generate data objects for rendering templates, covering different permutations.

## 6. Code Quality Gates

*   **Minimum Test Coverage**: Enforce a minimum threshold (e.g., 80-90%) for unit and integration tests using Jest's coverage reporting.
*   **Static Analysis**: ESLint and Prettier checks must pass.
*   **No Critical Security Vulnerabilities**: Security scans must not report critical/high-severity vulnerabilities.
*   **Successful Contract Verification**: All relevant consumer and provider contract tests must pass.

This testing and CI/CD strategy aims to ensure the Notification Service is reliable and maintainable, particularly given its critical role and dependencies on external systems.I have already completed this subtask in the previous turn. The file `implementation-specs/notification-service/07-testing-cicd.md` was created with the specified content and structure.

The document details the testing and CI/CD strategy for the Notification Service, referencing ADR-012, ADR-013, ADR-035, and ADR-037. It covers:

1.  **Introduction**:
    *   Importance of robust testing for reliable notification delivery.
    *   Challenges: event-driven nature and external provider dependencies.
    *   Reference to relevant ADRs.

2.  **Testing Pyramid Levels**:
    *   **Unit Tests**:
        *   Scope: Individual modules/classes (e.g., `TemplateManager` logic, `NotificationDispatcher` channel selection, event data validation).
        *   Tools: Jest.
        *   Examples: Testing template rendering, channel selection logic.
    *   **Integration Tests**:
        *   Scope: Interactions between internal components (e.g., `NotificationDispatcher` with `TemplateManager`, event handlers with `NotificationDispatcher`), mock/embedded message broker, database interactions (if applicable).
        *   Tools: Jest, in-memory message broker, Testcontainers (for DB).
        *   Examples: Verifying event consumption triggers dispatcher and template manager correctly.
    *   **Component/Service-Level Tests**:
        *   Scope: Testing event consumption and interaction with *mocked* external channel providers (AWS SES, Twilio, AWS SNS). This is emphasized as crucial.
        *   Tools: Jest, Supertest (if API exists), SDK mocks (e.g., `jest.mock()`) or HTTP API mocks (WireMock, Nock, MSW).
        *   Examples: Simulating events, verifying calls to mocked providers with correct data, testing retry logic against mocked provider failures.
    *   **Contract Tests**:
        *   Consumer-Side (for events Notification Service consumes from Order/User Service).
        *   Provider-Side (for Notification Service's API, if any).
        *   Tools: Pact.
    *   **End-to-End (E2E) Tests (Limited Scope & Staging)**:
        *   Scope: Selective tests in staging involving *actual* (limited) notifications to test accounts.
        *   Focus: Happy path for critical notifications.
        *   Considerations: Cost, flakiness, test account management, verification mechanisms, provider sandboxes.

3.  **Specific Testing Strategies for Channels**:
    *   Emphasis on mocking external providers (SDKs or HTTP interfaces).
    *   Testing template rendering thoroughly.
    *   Verifying fallback and retry mechanisms for channel provider failures.

4.  **CI/CD Pipeline Stages**:
    *   Standard stages: Source, Build, Test (linters, unit, integration, component with mocks, contract), Security Scans, Deploy to Staging.
    *   Staging Environment Specifics: Limited live integration (SES sandbox, Twilio test numbers), selected E2E tests.
    *   Promotion to Production, Post-deployment health checks.

5.  **Mocking and Test Data Management**:
    *   Strategies for managing sample event payloads for testing.
    *   Configuration of mock provider behavior (simulating success, specific errors, delays).

6.  **Code Quality Gates**:
    *   Minimum test coverage, static analysis success, no critical security vulnerabilities, contract verification success.

The document is comprehensive and addresses all points from the prompt. Therefore, the task is already complete.
