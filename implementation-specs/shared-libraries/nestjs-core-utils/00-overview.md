# 00: NestJS Core Utilities - Overview

## 1. Purpose

The `nestjs-core-utils` library is a shared package designed to provide common, reusable utilities and standardized implementations for cross-cutting concerns frequently encountered in NestJS-based microservices within the e-commerce platform.

Its primary goals are to:
*   Promote consistency in logging, error handling, and configuration across services.
*   Reduce boilerplate code in individual services.
*   Encapsulate best practices for common NestJS patterns.
*   Accelerate the development of new NestJS microservices.

This library is intended to be a foundational package imported by most, if not all, NestJS services in the platform.

## 2. Scope and Key Modules

This library will be organized into logical modules, each addressing a specific cross-cutting concern:

1.  **Logging Module (`LoggingModule`):**
    *   Provides a pre-configured, production-ready logger (e.g., based on Winston or Pino).
    *   Supports structured logging (JSON format).
    *   Includes middleware or interceptors for automatic request logging.
    *   Facilitates context propagation (e.g., correlation IDs) in logs.
    *   Configurable log levels.

2.  **Error Handling Module (`ErrorHandlingModule`):**
    *   Provides a global exception filter for consistent error responses.
    *   Defines standardized error DTOs (Data Transfer Objects) for API responses.
    *   May include common custom exception classes.
    *   Integrates with the LoggingModule to ensure errors are properly logged.

3.  **Configuration Module (`SharedConfigModule`):**
    *   Extends or provides utilities for `@nestjs/config`.
    *   May include base validation schemas (e.g., for common environment variables like `NODE_ENV`, `PORT`).
    *   Simplifies loading and accessing typed configurations.

4.  **Common Decorators & Interceptors (`common/`):**
    *   Collection of useful decorators (e.g., for user context extraction from requests).
    *   Common interceptors (e.g., for transforming responses, request validation helpers if not covered by pipes alone).

5.  **Health Check Utilities (`HealthModule` - Optional Integration):**
    *   Utilities to simplify the creation of health check endpoints, possibly integrating with `@nestjs/terminus`.
    *   Standardized checks for common dependencies (e.g., database, Kafka).

## 3. Technical Stack

*   **Language:** TypeScript
*   **Framework:** NestJS (as these are utilities *for* NestJS services)
*   **Key Dependencies (Examples):** `@nestjs/common`, `@nestjs/core`, `@nestjs/config`, a logging library (e.g., `winston`, `pino`), `class-validator`, `class-transformer`.

## 4. Non-Goals

*   **Business Logic:** This library will not contain any business domain-specific logic for any particular service (e.g., no order processing or payment logic).
*   **Highly Specialized Utilities:** Utilities that are only relevant to a single service or a very small subset of services should reside within those services themselves.
*   **Replacing NestJS Core Functionality:** The goal is to complement and standardize the use of NestJS, not to replace its core modules.

## 5. Versioning and Distribution

*   **Versioning:** The library will follow Semantic Versioning (SemVer) to ensure consumers can manage updates predictably.
*   **Distribution:** It will be published as a private NPM package to the organization's package registry.

## 6. Stability and Testing

*   **Stability:** As a foundational library, `nestjs-core-utils` aims for high stability. Changes will be managed carefully to minimize disruption to consuming services.
*   **Testing:** Each module within this library will be accompanied by a comprehensive suite of unit and integration tests to ensure reliability and correctness.

Subsequent documents will detail the API and implementation specifics for each module within this library.