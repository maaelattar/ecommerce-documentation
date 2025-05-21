# 00: Auth Client Utilities - Overview

## 1. Purpose

The `auth-client-utils` shared library is designed to provide NestJS microservices within the e-commerce platform with a standardized and secure way to handle client-side authentication and authorization tasks, primarily focusing on validating JSON Web Tokens (JWTs) issued by the central User Service.

As microservices often need to protect their endpoints and make decisions based on the authenticated user's identity and permissions, this library aims to:

*   Simplify the integration of JWT validation logic into resource services.
*   Ensure consistent application of security best practices for token validation.
*   Reduce boilerplate code related to authentication and authorization in individual services.
*   Provide easy access to user context (ID, roles, permissions) from validated tokens.

## 2. Scope and Key Components

This library will primarily consist of:

1.  **JWT Validation Module/Guard (`JwtAuthModule`, `JwtAuthGuard`):**
    *   A NestJS module that configures `passport` with the `passport-jwt` strategy.
    *   A `JwtAuthGuard` that can be easily applied to controllers or specific routes to protect them.
    *   Handles fetching the public key (e.g., from a JWKS URI provided by the User Service or via configuration) for JWT signature verification.
    *   Validates token claims (issuer, audience, expiration).

2.  **User Context Decorator (`CurrentUser`):**
    *   A NestJS parameter decorator (e.g., `@CurrentUser()`) to easily inject the validated user object (or specific parts like `userId` or `roles`) into route handlers.

3.  **Role/Permission-Based Access Control (RBAC) Utilities (Optional/Future):**
    *   Potentially, simple guards or decorators to check for specific roles or permissions present in the validated JWT payload (e.g., `@Roles('admin')`, `@HasPermission('manage:products')`). This would depend on the complexity and commonality of RBAC needs.

4.  **Configuration Utilities:**
    *   Helpers to configure crucial parameters like the JWKS endpoint URI, expected issuer, and audience for JWT validation, likely integrating with the `SharedConfigModule` from `nestjs-core-utils`.

## 3. Technical Stack

*   **Language:** TypeScript
*   **Framework:** NestJS
*   **Key Dependencies:** `@nestjs/passport`, `passport`, `passport-jwt`, `jwks-rsa` (for fetching keys from a JWKS URI).

## 4. Non-Goals

*   **Token Issuance:** This library is purely for client-side token validation. Token issuance remains the responsibility of the User Service.
*   **User Management:** Managing user identities, roles, or permissions is outside the scope of this library.
*   **Complex Authorization Policies:** For very complex authorization scenarios (e.g., attribute-based access control - ABAC), services might need more specialized solutions, though this library can provide the foundational authenticated identity.

## 5. Versioning and Distribution

*   **Versioning:** The library will follow Semantic Versioning (SemVer) to ensure consumers can manage updates predictably.
*   **Distribution:** It will be published as a private NPM package to the organization's package registry.

## 6. Stability and Testing

*   **Stability:** This library is critical for security; therefore, it aims for high stability. Changes will be managed carefully.
*   **Testing:** Will include comprehensive unit and integration tests, including scenarios with valid/invalid tokens and different key management setups.

This library will be a key enabler for securing microservice APIs consistently across the platform.
