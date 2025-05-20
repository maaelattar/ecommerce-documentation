# General API Consumption Guidelines (for Product Service as a Synchronous Client)

## 1. Introduction

This document outlines best practices and mandatory guidelines for the Product Service when it acts as a client making **synchronous API calls** to other services within the e-commerce platform. As per the overall integration strategy ([00-overview.md](./00-overview.md)), synchronous calls are considered exceptional and must be justified. When they are used, adherence to these guidelines is critical to maintain system resilience and stability.

These guidelines apply when Product Service *consumes* synchronous APIs from services like Inventory Service, User Service, etc., in specific, limited scenarios.

## 2. Core Principles for Synchronous API Consumption

- **Asynchronous First**: Prioritize asynchronous event-driven patterns via Amazon MQ for RabbitMQ or Amazon MSK (as per [03-message-broker-selection.md](../../../architecture/technology-decisions-aws-centeric/03-message-broker-selection.md)). Only consider synchronous calls when event-driven patterns cannot meet the specific requirement.
- **Necessity**: Confirm that a synchronous call is absolutely necessary and an asynchronous, event-driven alternative is not feasible or does not meet a critical, immediate consistency requirement.
- **Resilience by Default**: Assume external services can fail or respond slowly. Implement robust resilience patterns for every synchronous call.
- **Minimize Payload**: Only request and send the data essential for the interaction to reduce latency and network overhead.
- **Stateless Interactions**: Prefer stateless interactions. Avoid designs where the Product Service relies on maintaining session state with the called service across multiple synchronous calls.
- **Proper Contracts**: Develop against specific, versioned API contracts (e.g., OpenAPI specifications) of the downstream services.
- **Configuration Over Code**: All parameters related to synchronous API consumption must be externally configurable and not hardcoded.

## 3. Mandatory Resilience Patterns

For every synchronous outbound API call, the Product Service MUST implement the following:

### 3.1. Timeouts
- **Connection Timeouts**: Configure a short timeout for establishing a connection to the remote service (e.g., 1-2 seconds).
- **Request/Response Timeouts (Read Timeouts)**: Configure a timeout for how long the Product Service will wait for a response after a connection is established and the request is sent (e.g., 2-5 seconds, depending on the criticality and typical response time of the called service). This must be less than the timeout of the calling user's request or the parent process, to prevent cascading timeouts.
- **Configuration**: Timeouts must be configurable per called service and potentially per endpoint.

### 3.2. Retries
- **Idempotent Operations Only**: Retries should only be implemented for operations that are idempotent (safe to retry without unintended side effects).
- **Transient Failures**: Only retry on transient errors (e.g., `502 Bad Gateway`, `503 Service Unavailable`, `504 Gateway Timeout`, network connection errors, request timeouts).
- **Retry Strategy**: Implement retries with exponential backoff and jitter to avoid overwhelming a struggling downstream service.
    - Example: Retry up to 3 times, with initial backoff of 100ms, then 200ms, then 400ms, plus a random jitter.
- **Configuration**: Retry attempts and backoff parameters should be configurable.

### 3.3. Circuit Breakers
- **Purpose**: To prevent an application from repeatedly trying to execute an operation that is likely to fail, especially when a downstream service is unhealthy.
- **Implementation**: Utilize a circuit breaker library (e.g., resilience4j if Java, Polly if .NET, or equivalent in other languages).
- **States**: The circuit breaker should transition between CLOSED, OPEN, and HALF-OPEN states based on configurable error thresholds and durations.
    - **CLOSED**: Requests pass through. If failures exceed a threshold, it trips to OPEN.
    - **OPEN**: Requests fail fast without attempting to call the downstream service for a configured duration. After the timeout, it transitions to HALF-OPEN.
    - **HALF-OPEN**: A limited number of test requests are allowed. If successful, the breaker resets to CLOSED. If they fail, it returns to OPEN.
- **Configuration**: Error thresholds, open duration, and half-open test request counts must be configurable per called service.
- **Fallback (Optional but Recommended)**: Where appropriate, define a fallback behavior when the circuit is open (e.g., return cached data if available and acceptable, return a default response, or fail gracefully with a specific error message).

### 3.4. Security Measures
- **Authentication**: Product Service must securely manage and use credentials (e.g., OAuth 2.0 client credentials tokens, API keys) required to authenticate with downstream services.
    - Credentials must be stored securely (e.g., using AWS Secrets Manager) and not hardcoded.
    - Tokens should have the minimum necessary scopes/permissions.
- **Authorization**: Ensure the Product Service is authorized to access the specific endpoints it calls.
- **TLS**: All synchronous API calls MUST be made over HTTPS (TLS) to ensure data is encrypted in transit.
- **AWS IAM Roles**: When applicable, utilize AWS IAM roles and service-linked roles with appropriate policies for service-to-service communication within the AWS ecosystem.

### 3.5. Version Management
- Implement strategies to handle downstream API version changes gracefully (e.g., support for multiple versions if necessary).
- Be aware of and respect downstream service deprecation policies.
- Consider using API client libraries provided by the downstream services if available and regularly updated.

## 4. Testing Requirements

- **Unit Tests**: Test the logic for resilience patterns (e.g., ensuring timeouts, retries, circuit breakers behave as expected using mock services).
- **Integration Tests**: Test interactions with actual downstream services in controlled environments, including simulating failure scenarios (e.g., using tools like Toxiproxy or Mountebank).
- **Chaos Testing**: If possible, perform chaos testing (e.g., network delays, service termination) to validate resilience mechanisms.
- **Load Testing**: Validate behavior under load, especially for critical synchronous integrations.

## 5. Monitoring and Logging

- **Correlation IDs**: Ensure a correlation ID is generated (or propagated if received from an upstream call) and included in the logs and as a header (e.g., `X-Correlation-ID`) in the outbound synchronous API call. This is crucial for distributed tracing.
- **Comprehensive Logging**: For each synchronous call, log:
    - Target service and endpoint.
    - Request (headers and body, sanitizing sensitive data).
    - Response (status code, headers, and body, sanitizing sensitive data).
    - Latency of the call.
    - Outcome (success, failure, retries attempted, circuit breaker state if changed).
    - Any errors encountered.
- **Metrics**: Expose metrics for synchronous calls, including:
    - Call count (per service/endpoint).
    - Error count (per service/endpoint, per error type).
    - Latency distribution (e.g., average, p95, p99).
    - Circuit breaker state changes.
- **AWS CloudWatch**: Use AWS CloudWatch for logs and metrics, with appropriate log groups and metric namespaces.
- **Alerting**: Configure alerts based on high error rates, increased latency, or frequent circuit breaker openings for critical synchronous integrations using AWS CloudWatch Alarms.
- **AWS X-Ray**: Consider using AWS X-Ray for distributed tracing to identify performance bottlenecks and troubleshoot request flows across services.

## 6. Documentation Requirements

- Any synchronous API integration implemented by the Product Service must be documented, including:
    - The service and endpoint being called.
    - The justification for using a synchronous call over asynchronous event-driven alternatives.
    - Key resilience parameters configured.
    - Expected error handling and fallback behaviors.
    - Relevant AWS service configurations.
- Configuration parameters should be well-documented with their purpose, default values, and acceptable ranges.
- Update documentation when integration patterns or downstream APIs change.

By adhering to these guidelines, the Product Service can minimize the risks associated with exceptional synchronous API calls and contribute to the overall stability and resilience of the e-commerce platform. 