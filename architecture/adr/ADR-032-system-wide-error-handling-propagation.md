# ADR-032: System-Wide Error Handling and Propagation Strategy

*   **Status:** Proposed
*   **Date:** 2025-05-11
*   **Deciders:** Project Team, Lead Developers, Operations Team
*   **Consulted:** Development Teams, API Consumers (future)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In a distributed microservices architecture (ADR-001), errors can originate in any service and may need to propagate across service boundaries. A consistent, system-wide strategy for error handling, classification, logging (ADR-010), monitoring (ADR-011), and propagation is crucial for building resilient (ADR-022) and debuggable applications. ADR-030 (API Design Guidelines) defines error response formats for external APIs, but this ADR addresses the broader strategy for internal error management and inter-service error communication.

## Decision Drivers

*   **Resilience & Fault Tolerance:** Graceful degradation of services in the presence of errors.
*   **Debuggability & Observability:** Quickly identify, diagnose, and resolve issues across service boundaries.
*   **Consistency:** Uniform approach to handling and reporting errors simplifies development and operations.
*   **User Experience:** Provide meaningful feedback to users or calling services without exposing internal details.
*   **Operational Efficiency:** Standardized error information aids monitoring, alerting, and automated recovery actions.

## Decision Outcome

**Chosen Approach:** Implement a layered error handling strategy that standardizes error types, ensures consistent logging and monitoring, and defines clear patterns for error propagation between services, distinguishing between synchronous and asynchronous communication (ADR-002).

### 1. Error Classification
Standardize error classification to facilitate consistent handling and analysis:
*   **Business Errors (Recoverable/Expected):** Errors that are part of the normal business flow, often due to invalid input or unmet business rules (e.g., insufficient stock, invalid coupon code, payment declined). These are often expected and might be handled by retrying with different parameters or informing the user.
    *   Typically map to HTTP 4xx status codes in synchronous APIs (as per ADR-030).
*   **Application Errors (Potentially Recoverable/Unexpected):** Bugs within a service or unexpected conditions that prevent normal operation (e.g., null pointer exception, misconfiguration leading to failed logic). These might be recoverable with a generic retry, or they might indicate a need for a code fix.
    *   Typically map to HTTP 5xx status codes in synchronous APIs.
*   **System/Infrastructure Errors (Often Unrecoverable by the service itself):** Failures in underlying infrastructure or critical dependencies (e.g., database unavailable, network partition, message broker down - ADR-018).
    *   These often require intervention or an external system to recover (e.g., Kubernetes restarting a pod - ADR-006).
    *   Typically map to HTTP 5xx (e.g., 502, 503, 504) status codes.

### 2. Error Representation
*   **Internal Errors:** Within a service, use custom error classes or a standardized error object that includes:
    *   `errorCode` (a unique, service-specific or global code for the error type).
    *   `message` (human-readable description).
    *   `originalError` (the underlying error object/stack trace, for internal logging).
    *   `context` (key-value pairs providing additional relevant information).
    *   `isRetryable` (boolean, indicating if the operation can be retried as-is).
*   **External API Errors:** Follow ADR-030 for formatting error responses in public/external APIs.

### 3. Error Logging (ADR-010)
*   **Structured Logging:** All errors MUST be logged in a structured format (JSON).
*   **Essential Information:** Logs MUST include:
    *   Timestamp
    *   Service Name
    *   Error Code
    *   Error Message
    *   Stack Trace (for application/system errors, potentially truncated for brevity in logs but available in full detail if needed).
    *   Correlation ID (ADR-017, ADR-021) to trace requests across services.
    *   Request details (e.g., endpoint, relevant parameters - sanitized to remove PII).
    *   User ID / Client ID (if applicable and available).
*   **Log Levels:** Use appropriate log levels (ERROR for actual errors, WARN for potential issues).

### 4. Error Monitoring & Alerting (ADR-011)
*   **Metrics:** Track error rates (total, per error code, per endpoint), error latency.
*   **Dashboards:** Visualize error trends to identify problematic services or endpoints.
*   **Alerts:** Configure alerts for:
    *   Significant spikes in error rates (overall or for specific error codes).
    *   High percentage of failed requests.
    *   Specific critical error occurrences.
    *   Failures in critical dependencies (e.g., message broker, database connection pools).

### 5. Error Propagation & Handling Patterns

**A. Synchronous Communication (e.g., REST APIs - ADR-030, gRPC)**
*   **Translate, Don't Expose:** When a service calls another service and receives an error, it should generally not blindly propagate the downstream error. Instead, it should translate it into an error meaningful to its own domain or context.
    *   For example, if an `Order Service` calls an `Inventory Service` which returns an "ItemNotFound" error, the `Order Service` might translate this to an "OrderItemUnavailable" error before responding to its caller.
*   **Maintain Context:** While translating, preserve the original error's `traceId` and potentially log the original error details for debugging.
*   **HTTP Status Codes:** Use appropriate HTTP status codes as per ADR-030. Avoid generic 500s where possible.
*   **Resilience Patterns (ADR-022):** Apply patterns like Timeouts, Retries (with backoff and jitter), and Circuit Breakers to handle transient downstream failures gracefully.
    *   Retries should primarily be for `isRetryable` system/infrastructure errors or specifically marked application errors.

**B. Asynchronous Communication (e.g., Message Queues - ADR-018)**
*   **Dead Letter Queues (DLQs):** For unrecoverable message processing errors or messages that repeatedly fail after configured retries, move them to a DLQ.
    *   Each primary queue should have an associated DLQ.
    *   Messages in DLQs must be monitored.
    *   Establish processes for analyzing and re-processing/discarding messages from DLQs.
*   **Idempotent Consumers (ADR-018):** Design message consumers to be idempotent to safely retry messages without unintended side effects.
*   **Error Headers/Payload:** When publishing an event that signifies an error or when moving a message to a DLQ, include error information (error code, message, original event details) in message headers or the payload.
*   **Retry Mechanisms:** Implement retry mechanisms within message consumers (e.g., with exponential backoff) before sending to a DLQ.
*   **Error Reporting Services (Optional):** Consider a dedicated service that subscribes to error topics or monitors DLQs to provide centralized error reporting or trigger compensatory actions.

### 6. Client-Side Error Handling
*   Frontend clients or API consumers should be prepared to handle standard HTTP error codes and structured error responses (ADR-030).
*   Implement user-friendly error messages and appropriate fallback mechanisms.

## Consequences

*   **Pros:**
    *   Improved system resilience and ability to handle partial failures.
    *   Faster identification and resolution of issues due to consistent logging and tracing.
    *   Better user experience by providing meaningful (but safe) error feedback.
    *   Simplified development due to clear error handling conventions.
*   **Cons:**
    *   Requires careful implementation and discipline across all services.
    *   Can introduce some overhead in error translation and context propagation.
    *   Defining a comprehensive set of global error codes can be challenging.
*   **Risks:**
    *   Inconsistent adoption by different service teams.
    *   Over-logging or under-logging errors, making diagnosis difficult.
    *   Poorly configured retry mechanisms could exacerbate system load during failures (retry storms).

## Next Steps

*   Develop a shared library (or guidelines for each service) for creating, logging, and propagating standardized error objects.
*   Define an initial set of common error codes or a convention for service-specific error codes.
*   Update service templates to include robust error handling middleware/interceptors.
*   Ensure CI/CD pipelines for services include checks or promote patterns for proper error handling.
*   Conduct training sessions for developers on these error handling principles and patterns.
*   Set up monitoring and alerting for DLQs and critical error metrics.
