# 03 - User Service as a Consumer (Service-to-Service API Calls)

While the User Service is primarily a provider of identity and user data, there might be limited scenarios where it acts as a consumer, making API calls to other microservices. Generally, the preference is for User Service to be self-contained or to trigger actions in other services via events. However, direct outbound API calls can occur.

## 1. Guiding Principles

*   **Minimize Outbound Dependencies**: The User Service, being a foundational service, should minimize its synchronous runtime dependencies on other services to maintain high availability and reduce cascading failure risks.
*   **Prefer Events for Decoupling**: If the User Service needs to trigger an action in another service (e.g., send an email), publishing an event (e.g., `PasswordResetRequestedEventV1`) and letting the Notification Service consume it is generally preferred over a direct API call from User Service to Notification Service.
*   **Necessity**: Outbound API calls should only be made when:
    *   The required functionality cannot be achieved through event-driven patterns.
    *   The interaction is inherently request/response and synchronous.
    *   The external service provides data or capabilities essential for a User Service operation that cannot be localized.

## 2. Potential Scenarios (Illustrative)

### a. Integration with a Notification Service (If not purely event-driven)

*   **Scenario**: While events are preferred, a design might exist where `AuthService` directly calls a `NotificationService.sendEmail()` API after generating a password reset token or an email verification link.
*   **API Call Example**:
    *   User Service -> Notification Service
    *   `POST /notifications/email`
    *   Payload: `{ "to": "user@example.com", "templateId": "password-reset", "context": { "resetLink": "...", "userName": "..." } }`
*   **Considerations**:
    *   **Synchronous Coupling**: User Service operation (e.g., password reset request) now depends on Notification Service availability.
    *   **Retries & Timeouts**: User Service needs robust retry logic and timeouts for these calls.
    *   **Failure Handling**: What if the Notification Service call fails? Does the user operation fail, or is it logged and retried later (e.g., via an internal queue)?

### b. Breached Password Check (Have I Been Pwned - HIBP)

*   **Scenario**: The `PasswordPolicyService` calls the external HIBP API to check if a password has been compromised.
*   **API Call Example**:
    *   User Service (`PasswordPolicyService`) -> HIBP API
    *   `GET https://api.pwnedpasswords.com/range/{hashPrefix}`
*   **Considerations**:
    *   **External Dependency**: Relies on an external, third-party service.
    *   **Availability**: If HIBP API is down, User Service needs a fallback (e.g., allow registration with a warning, temporarily skip check, or deny if policy is strict).
    *   **Security**: Uses k-anonymity to protect the full password hash.
    *   **Rate Limiting**: Be mindful of HIBP API rate limits.

### c. CAPTCHA Verification

*   **Scenario**: Before processing a registration or login attempt, User Service calls a CAPTCHA verification service (e.g., Google reCAPTCHA API) to validate a CAPTCHA token submitted by the client.
*   **API Call Example**:
    *   User Service (`AuthService`) -> CAPTCHA Service API
    *   `POST https://www.google.com/recaptcha/api/siteverify`
    *   Payload: `{ "secret": "your_secret_key", "response": "captcha_token_from_client" }`
*   **Considerations**:
    *   **External Dependency**.
    *   **Critical for Flow**: If CAPTCHA fails or service is down, the user action (registration/login) typically cannot proceed.

### d. Retrieving Platform-Wide Configuration (If not injected at startup)

*   **Scenario**: If certain configurations critical for the User Service (e.g., global security policies, list of allowed email domains for a specific tenant in a multi-tenant system) are managed by a central `ConfigurationService` and need to be fetched dynamically.
*   **API Call Example**:
    *   User Service -> Configuration Service
    *   `GET /config/user-service/security-policies`
*   **Considerations**:
    *   **Caching**: User Service should heavily cache such configurations to avoid frequent calls.
    *   **Startup Dependency**: Might be a blocking call during User Service startup.

## 3. Implementation Details

*   **HTTP Client**: If making outbound HTTP calls, User Service would use an HTTP client like NestJS's `HttpService` (which wraps Axios) or a more specialized SDK if calling cloud provider services.
*   **Service Discovery**: If calling other internal microservices, User Service would use the platform's service discovery mechanism (e.g., Kubernetes DNS, Consul) to resolve service addresses.
*   **Authentication & Authorization for Outbound Calls**:
    *   If the User Service calls another internal secured microservice, it may need to authenticate itself (e.g., using a client credentials grant OAuth token or a service account JWT).
*   **Resilience Patterns**: For critical outbound calls, implement patterns like:
    *   **Retries**: With exponential backoff and jitter.
    *   **Timeouts**: To prevent indefinite blocking.
    *   **Circuit Breakers**: To stop making calls to a failing service for a period, preventing cascading failures and giving the downstream service time to recover.

## 4. Security Considerations

*   **Secrets Management**: Securely manage any API keys or credentials needed to call external or internal services (e.g., using environment variables injected via a secure configuration system like HashiCorp Vault or cloud provider secret managers).
*   **Data Exposure**: Be mindful of what data is sent in outbound API calls.
*   **Trust**: Only integrate with trusted and verified services.

While direct API consumption by the User Service is minimized, these examples illustrate potential scenarios. The primary mode of inter-service communication triggered by User Service actions remains event publishing.
