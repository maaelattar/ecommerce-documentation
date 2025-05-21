# 00: Testing Utilities - Overview

## 1. Purpose

The `testing-utils` shared library provides a collection of common utilities, mock implementations, and helper functions designed to streamline and standardize the testing (unit, integration) of NestJS microservices within the e-commerce platform.

Effective and efficient testing is crucial for maintaining code quality and ensuring the reliability of the microservices. This library aims to:

*   Reduce boilerplate code in service-specific test suites.
*   Provide consistent ways to mock shared dependencies (like those from `nestjs-core-utils`, `rabbitmq-event-utils`, and `auth-client-utils`).
*   Simplify the setup for common testing scenarios.
*   Promote best practices in testing across different services.

This library is intended for use during development and in CI/CD pipelines, not for production deployment.

## 2. Scope and Key Components (Examples)

This library could include components such as:

1.  **Mock Implementations for Core Utilities:**
    *   `MockLogger`: A simple, in-memory logger implementation that can be used to assert that certain log messages were (or were not) called, without actual I/O.
    *   `MockConfigService`: For providing controlled configuration values during tests.

2.  **RabbitMQ Testing Helpers:**
    *   `MockRabbitMQProducer`: A mock producer that allows tests to verify that messages would have been sent, with what payload, to which exchange/routing key, without actual RabbitMQ interaction.
    *   `RabbitMQMessageFactory`: Helper functions to construct valid RabbitMQ message objects (conforming to the standard envelope) for testing consumer logic.
    *   Utilities to simulate NestJS microservice event handling for RabbitMQ consumers (e.g., using `@nestjs/testing` with mock contexts).

3.  **Authentication/Authorization Testing Helpers:**
    *   `MockJwtAuthGuard`: A mock guard that can be configured to simulate successful or failed authentication, or to pass through a predefined user payload, for testing protected endpoints.
    *   `TokenFactory`: Functions to generate mock JWT payloads (or even signed tokens if needed for specific tests) with desired user properties (ID, roles, permissions).

4.  **Database Testing Utilities (if applicable and common):**
    *   Helpers for setting up and tearing down test databases (e.g., using in-memory databases like SQLite for TypeORM, or test containers for PostgreSQL).
    *   Factories for creating mock entity data.
    *   *(Note: This area needs careful consideration to avoid making the library too heavy or too coupled to specific database technologies if services might diverge.)*

5.  **Common Test Setup/Teardown Utilities:**
    *   Functions to simplify the creation of NestJS testing modules (`Test.createTestingModule(...)`) with commonly mocked providers.

## 3. Technical Stack

*   **Language:** TypeScript
*   **Framework:** NestJS (primarily using `@nestjs/testing`)
*   **Testing Libraries:** Jest (assuming it's the platform standard), Sinon (for spies, stubs, mocks if needed).

## 4. Non-Goals

*   **A Full-Fledged Test Runner/Framework:** This library provides utilities *for* testing frameworks like Jest, not a replacement for them.
*   **Service-Specific Mock Logic:** Mocks for business-specific components of a microservice should reside within that service's test suite.
*   **End-to-End (E2E) Test Orchestration across Multiple Services:** While utilities might help in testing individual services that participate in E2E flows, orchestrating full E2E tests is a broader concern.

## 5. Versioning and Distribution

*   **Versioning:** The library will follow Semantic Versioning (SemVer).
*   **Distribution:** It will be published as a private NPM package to the organization's package registry (likely as a `devDependency`).

## 6. Evolution

*   The contents of `testing-utils` will evolve based on common needs identified across service development. Modules and utilities will be added as patterns of repeated test code emerge.

This library will be instrumental in improving the efficiency, consistency, and quality of testing across the microservices ecosystem.
