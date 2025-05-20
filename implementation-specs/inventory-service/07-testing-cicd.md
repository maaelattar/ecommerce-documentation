# Inventory Service: Testing and CI/CD Strategy

## 1. Introduction

The Inventory Service is a critical component of the e-commerce platform, directly responsible for managing stock levels, reservations, and providing accurate availability information. Given its central role, a comprehensive testing strategy and a robust CI/CD pipeline are paramount to ensure its reliability, correctness, and performance. Errors in inventory management can lead to overselling, underselling, poor customer experience, and financial discrepancies.

This document outlines the specific testing and CI/CD approach for the Inventory Service. It aligns with the overall architectural guidelines established in:
-   **ADR-012 (CI/CD Strategy)**: Defines the general Continuous Integration and Continuous Delivery principles.
-   **ADR-013 (Testing Strategy)**: Outlines the global testing pyramid and types of tests.
-   **ADR-035 (Test Data Management Strategy)**: Provides guidelines for managing test data.
-   **ADR-037 (CI/CD Pipeline Strategy)**: Details the standardized pipeline stages.

The goal is to catch defects early, ensure that changes are deployed safely and efficiently, and maintain high confidence in the service's behavior in production.

## 2. Testing Pyramid Levels

The Inventory Service will adopt a balanced testing pyramid approach as advocated in **ADR-013**, focusing on a large base of unit tests, a significant number of integration and component tests, and fewer, more targeted contract and end-to-end tests.

### 2.1. Unit Tests

*   **Scope**: Focus on individual, isolated units of code such as modules, classes, methods, or functions. Business logic within services (e.g., `InventoryManagerService`, `ReservationManagerService`), repository methods (mocking actual database interaction), helper functions, and DTO validation logic are key candidates.
*   **Tools**:
    *   **Jest**: As the primary testing framework, given the NestJS context.
    *   **NestJS testing utilities**: For mocking providers and modules.
*   **Examples**:
    *   Testing `InventoryManagerService` logic for correct `InventoryStatus` transitions (e.g., from `IN_STOCK` to `LOW_STOCK` or `OUT_OF_STOCK`) based on quantity changes.
    *   Verifying `ReservationManagerService` rules, such as preventing reservation of more stock than available (`availableQuantity`).
    *   Testing validation logic for Data Transfer Objects (DTOs) using `class-validator` and `class-transformer`.
    *   Ensuring `InventoryHistoryService` correctly formats and prepares history entries.
    *   Testing individual repository methods with mocked database responses to verify query construction or data transformation logic.

### 2.2. Integration Tests

*   **Scope**: Verify the interaction between different components *within* the Inventory Service. This typically involves testing a service layer method along with its direct dependencies, such as the database repository, or how different internal services collaborate.
*   **Tools**:
    *   **Jest**: As the testing framework.
    *   **Testcontainers**: For spinning up ephemeral PostgreSQL instances to test actual database interactions. This ensures queries are valid and transactions behave as expected.
    *   **In-memory message broker (e.g., mock an RabbitMQ client or use a lightweight in-memory alternative)**: For testing event publishing logic within the service without relying on an external broker.
*   **Examples**:
    *   Testing the full flow of `ReservationManagerService.reserveStock()`, ensuring it correctly calls `InventoryRepository` to update quantities, and then triggers `InventoryHistoryService` to log the reservation.
    *   Verifying that an `InventoryManagerService.updateStock()` call correctly persists changes to the database and subsequently publishes a `StockLevelChangedEvent` (to a mocked/in-memory broker).
    *   Testing database constraints (e.g., non-negative quantities) by attempting to save invalid data via repositories.

### 2.3. Component Tests (or Service-Level Tests)

*   **Scope**: Test the Inventory Service as a deployable unit, including its external API endpoints and its interactions with its direct, external dependencies (actual database, actual message broker in a controlled test environment). These tests focus on the service's contract with the outside world.
*   **Tools**:
    *   **Supertest**: For making HTTP requests to the service's API endpoints.
    *   **Jest**: As the orchestrator for these tests.
    *   **Testcontainers/Docker**: To manage instances of PostgreSQL and RabbitMQ specifically for these tests, ensuring a clean and isolated environment.
*   **Examples**:
    *   Sending a `POST` request to `/api/v1/inventory/{productVariantId}/reserve`, then verifying the HTTP response code, the response body, the state of the database (e.g., `reservedQuantity` updated), and that an `InventoryReservedEvent` was published to the message broker.
    *   Sending a `GET` request to `/api/v1/inventory/{productVariantId}` and validating the returned inventory data against a known database state.
    *   Testing error responses for invalid requests (e.g., reserving stock for a non-existent product variant).

### 2.4. Contract Tests (Consumer-Driven)

*   **Scope**: Ensure that the Inventory Service's API (as a provider) and its published events meet the expectations (contracts) defined by its consumers (e.g., Order Service, Product Service). This helps prevent integration issues when services change independently.
*   **Tools**:
    *   **Pact**: A popular choice for consumer-driven contract testing. Consumers define contracts, and providers verify them.
    *   **Spring Cloud Contract**: An alternative, especially if other services in the ecosystem use it.
*   **Examples**:
    *   **API Contract (Inventory Service as Provider)**:
        *   The Product Service (consumer) defines a contract for `GET /api/v1/inventory/{productVariantId}` specifying the expected request and response structure. The Inventory Service runs tests to verify it adheres to this contract.
    *   **Event Contract (Inventory Service as Provider)**:
        *   The Notification Service (consumer) defines a contract for the `StockStatusChangedEvent`, specifying the expected event payload structure. The Inventory Service verifies that the events it publishes match this contract.
    *   **API Contract (Inventory Service as Consumer)**:
        *   If the Inventory Service consumes APIs from other services (e.g., Product Service to validate product existence on startup, though generally discouraged for runtime operations), it would define contracts for those APIs.

### 2.5. End-to-End (E2E) Tests

*   **Scope**: Test complete business flows that span multiple microservices. For the Inventory Service, this would involve scenarios like a full order placement process (User Service -> Product Service -> Order Service -> Inventory Service -> Payment Service).
*   **Mention**: The Inventory Service will participate in these broader E2E tests, which are typically owned and managed at a platform or system level. The detailed specification for these tests usually resides outside individual service implementation plans. The primary focus of *this* document is on tests owned and executed by the Inventory Service team.

## 3. Specific Testing Scenarios for Inventory Service

Beyond the general pyramid levels, the following scenarios are critical to test for the Inventory Service:

*   **Concurrency Testing**:
    *   Simulate multiple concurrent requests to update stock or reserve stock for the same product variant to ensure data integrity (no race conditions leading to incorrect quantities) and that locking mechanisms (e.g., optimistic or pessimistic) work as expected.
*   **Accuracy of `availableQuantity`**:
    *   Test various sequences of stock updates, reservations, and releases to ensure `availableQuantity` (`quantity - reservedQuantity`) is always calculated correctly and never drops below zero inappropriately.
*   **`InventoryStatus` Transitions**:
    *   Verify that the `status` (e.g., `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `DISCONTINUED`) is correctly updated based on quantity changes, thresholds, and manual overrides.
*   **Resilience Testing**:
    *   Test how the service behaves if a dependent service (e.g., RabbitMQ, database) is temporarily unavailable. Ensure appropriate error handling, retries (especially for event publishing via outbox), and graceful degradation if applicable.
*   **Inventory History Logging**:
    *   Verify that all relevant stock movements, status changes, and reservations are accurately and comprehensively logged in the `InventoryHistory` entity.
*   **Idempotency of Event Consumers**:
    *   If the Inventory Service consumes events (e.g., `ProductVariantCreatedEvent`), ensure its handlers are idempotent.
*   **Transactional Integrity**:
    *   For operations involving database changes and event publishing (using the transactional outbox pattern), verify that either both succeed or neither does.

## 4. CI/CD Pipeline Stages

The CI/CD pipeline for the Inventory Service will follow the standards defined in **ADR-012 (CI/CD Strategy)** and **ADR-037 (CI/CD Pipeline Strategy)**. A typical pipeline would include:

1.  **Source**: Triggered on code commit/merge to main branches (e.g., `main`, `develop`) in Git.
2.  **Build**:
    *   Install dependencies (`npm install`).
    *   Compile TypeScript to JavaScript.
    *   Build Docker image for the Inventory Service.
3.  **Test**:
    *   **Linters & Static Analysis**: Run ESLint, Prettier to enforce code style and catch early issues.
    *   **Unit Tests**: Execute all unit tests (`npm run test:unit`).
    *   **Integration Tests**: Execute integration tests (`npm run test:integration`). This may involve spinning up Testcontainers for PostgreSQL.
    *   **Component Tests**: Execute component tests (`npm run test:component`). This will involve spinning up PostgreSQL and RabbitMQ via Docker/Testcontainers.
    *   **(Optional) Publish Contract Tests**: If using Pact, publish provider contracts to a Pact Broker.
4.  **Security Scans**:
    *   Perform vulnerability scanning on the built Docker image (e.g., using Trivy, Snyk).
    *   Static Application Security Testing (SAST) if configured.
5.  **Push to Registry**: Push the tagged Docker image to a container registry (e.g., Amazon ECR, Docker Hub).
6.  **Deploy to Staging/Test Environment**: Deploy the new version of the Inventory Service to a staging environment that mirrors production as closely as possible.
7.  **Run E2E & Consumer-Driven Contract Tests (against Staging)**:
    *   Execute broader E2E tests involving the deployed Inventory Service and other services in the staging environment.
    *   Run consumer-driven contract tests against the deployed service.
8.  **Promote to Production**:
    *   Requires manual approval after successful staging deployment and E2E tests.
    *   May involve strategies like blue/green deployment or canary releases.
9.  **Post-Deployment**:
    *   Automated health checks against the production deployment.
    *   Active monitoring of key metrics (error rates, latency, stock accuracy) and logs.

## 5. Mocking and Test Data Management

Consistent with **ADR-035 (Test Data Management Strategy)**:

*   **Mocking External Dependencies**:
    *   **Unit Tests**: External services and repositories are mocked using Jest's mocking capabilities (`jest.fn()`, `jest.mock()`).
    *   **Integration/Component Tests**:
        *   For direct dependencies like databases or message brokers, use Testcontainers or managed Docker instances.
        *   For other microservices (e.g., Product Service, Order Service), use tools like WireMock or specific client mocks if these services are not part of the component test scope. For consumer-driven contract tests, Pact handles provider mocking.
*   **Test Data Management**:
    *   **Factories**: Use factory functions or libraries (e.g., `factory.ts`) to generate consistent and valid test data (entities, DTOs) for different scenarios.
    *   **Seed Scripts**: For integration and component tests requiring a specific database state, use seed scripts executed before tests run (e.g., via TypeORM migrations or custom scripts).
    *   **Data Isolation**: Ensure tests are isolated and can run in parallel. Clean up data after tests or use fresh database instances (Testcontainers makes this easier).
    *   Avoid relying on pre-existing data in shared test environments where possible.

## 6. Code Quality Gates

To maintain a high standard of code quality:

*   **Minimum Test Coverage**:
    *   Enforce a minimum test coverage threshold (e.g., 80-90% for statement, branch, and function coverage) using Jest's coverage reporting. This will be a check in the CI pipeline.
*   **Static Analysis Rules**:
    *   Successful completion of ESLint and Prettier checks is mandatory.
*   **No Critical Security Vulnerabilities**: Security scans must not report critical or high-severity vulnerabilities.
*   **Successful Contract Verification**: All relevant provider contract tests must pass.

By adhering to this testing and CI/CD strategy, the Inventory Service aims for robustness, maintainability, and reliable operation in the e-commerce platform.
