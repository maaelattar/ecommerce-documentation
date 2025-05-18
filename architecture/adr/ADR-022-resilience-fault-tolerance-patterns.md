# ADR-022: Resilience and Fault Tolerance Patterns

*   **Status:** Proposed
*   **Date:** 2025-05-11
*   **Deciders:** Project Team
*   **Consulted:** Lead Developers, DevOps/SRE Team
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In a microservices architecture (ADR-001), services communicate over a network, which is inherently unreliable. Failures in one service (due to bugs, overload, or infrastructure issues) can cascade and impact other services, potentially leading to system-wide outages. This ADR defines standard resilience and fault tolerance patterns to be implemented to prevent such cascading failures and ensure the system remains available and responsive, or degrades gracefully, in the face of partial failures.

## Decision Drivers

*   **System Availability:** Maximize uptime and minimize the impact of individual service failures.
*   **Fault Isolation:** Prevent failures in one part of the system from spreading to others.
*   **Graceful Degradation:** Allow the system to continue functioning with reduced capability rather than failing completely.
*   **User Experience:** Provide a consistent and predictable experience even during partial outages.
*   **Recoverability:** Enable services to recover quickly from transient failures.

## Considered Options & Patterns

This ADR focuses on adopting a suite of well-known resilience patterns rather than choosing between mutually exclusive high-level options. The key is to decide which patterns are mandatory, recommended, and how they should be implemented.

**Key Resilience Patterns:**

1.  **Timeouts:** Setting maximum wait times for responses from dependencies.
2.  **Retries (with Exponential Backoff and Jitter):** Automatically re-attempting failed requests, especially for transient network issues.
3.  **Circuit Breakers:** Preventing repeated calls to a failing service after a certain threshold of failures, allowing it time to recover.
4.  **Bulkheads:** Isolating resources (e.g., thread pools, connection pools) used for different dependencies to prevent one misbehaving dependency from exhausting resources for all others.
5.  **Fallbacks:** Providing alternative responses or functionality when a primary operation fails (e.g., returning cached data, default values, or a simplified response).
6.  **Rate Limiting and Throttling:** Protecting services from being overwhelmed by too many requests.
7.  **Idempotent Operations:** Designing operations so that making the same request multiple times has the same effect as making it once (crucial for safe retries).
8.  **Health Checks:** Exposing endpoints for services to report their health status, used by orchestration platforms (Kubernetes - ADR-006) and load balancers.

## Decision Outcome

**Chosen Approach:** Implement a combination of resilience patterns strategically across services and at the API Gateway level.

*   **Mandatory Patterns for Inter-Service Communication:**
    *   **Timeouts:** All synchronous network calls between services MUST have configurable timeouts.
    *   **Retries:** Implement retries with exponential backoff and jitter for transient, idempotent read operations. For write operations, ensure idempotency before enabling retries.
    *   **Circuit Breakers:** Services SHOULD implement circuit breakers for calls to critical dependencies. Libraries like Resilience4j (Java), Polly (.NET), Hystrix (Java - maintenance mode, but concepts are valid), or Istio/Linkerd capabilities (if a service mesh is adopted) can be used.
*   **Recommended Patterns:**
    *   **Fallbacks:** Where feasible, provide fallback mechanisms for critical functionalities if a dependency is unavailable (e.g., serving stale data from a cache, providing a default response).
    *   **Bulkheads:** Consider bulkhead patterns for services that interact with multiple, distinct downstream services, especially if some are less reliable than others.
*   **API Gateway (ADR-014) Responsibilities:**
    *   The API Gateway SHOULD implement patterns like timeouts, retries (for idempotent requests), and potentially circuit breakers for routes to backend services.
    *   It will also be a key point for implementing rate limiting and throttling for external clients.
*   **Idempotency:** Services providing write operations that might be retried MUST ensure those operations are idempotent. This can be achieved using unique request IDs or by designing operations to be naturally idempotent.
*   **Health Checks:** All services MUST implement comprehensive health check endpoints (liveness and readiness probes as per Kubernetes ADR-006 requirements) that accurately reflect their ability to serve traffic and connect to their dependencies.
*   **Configuration:** Resilience patterns (timeout durations, retry attempts, circuit breaker thresholds) MUST be configurable externally (ADR-016 Configuration Management).
*   **Monitoring:** The state of circuit breakers, retry rates, and timeout occurrences MUST be monitored (ADR-021 Centralized Logging and Monitoring).

## Consequences

*   **Pros:**
    *   Increased system stability and availability.
    *   Better isolation of failures, preventing cascading effects.
    *   Improved user experience during partial outages through graceful degradation.
    *   Faster recovery from transient issues.
*   **Cons:**
    *   Adds complexity to service development and testing.
    *   Configuring these patterns appropriately requires understanding of service dependencies and failure modes.
    *   Can introduce subtle bugs if not implemented correctly (e.g., non-idempotent retries).
    *   Overhead of resilience libraries or service mesh components.
*   **Risks:**
    *   Incorrectly configured timeouts or retry storms can exacerbate problems.
    *   Circuit breakers might open too slowly or too quickly if thresholds are not tuned.

## Next Steps

*   Select and provide standard libraries or frameworks for implementing these patterns in our primary programming languages (Node.js/NestJS - ADR-003).
*   Develop guidelines and best practices for configuring timeouts, retries, and circuit breakers.
*   Incorporate testing of resilience patterns into service testing strategies (ADR-013).
*   Integrate monitoring of resilience mechanisms into the centralized monitoring solution (ADR-021).
*   Consider adopting a service mesh (e.g., Istio, Linkerd) in the future to offload some of these patterns from application code.
