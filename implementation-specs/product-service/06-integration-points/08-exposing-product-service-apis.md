# Exposing Product Service APIs (for Synchronous Consumption)

## 1. Introduction

This document provides guidelines and considerations for exposing Product Service APIs for **synchronous consumption** by other services within the e-commerce platform. As per the overall integration strategy ([00-overview.md](./00-overview.md)), synchronous inter-service calls are exceptional. Product Service APIs are primarily designed for its own operations and to support its UI/admin functionalities. Event-driven integration via Amazon MQ for RabbitMQ or Amazon MSK (as per [03-message-broker-selection.md](../../../architecture/technology-decisions-aws-centeric/03-message-broker-selection.md)), as detailed in [Phase 5: Event Publishing](../../05-event-publishing/), is the preferred method for other services to react to changes in product data.

However, in specific, justified scenarios, other services (e.g., Order Service at the point of checkout) might need to call Product Service APIs synchronously. These guidelines ensure such exposures are managed effectively.

## 2. API Contract and Design (Reference to Phase 4)

- **OpenAPI Specification**: All synchronously exposed APIs of the Product Service are authoritatively defined in its [OpenAPI Specification](../../openapi/product-service.yaml). This is the single source of truth for API contracts.
- **Consistency**: APIs exposed for synchronous inter-service consumption must follow the same design principles, authentication, authorization, versioning, and error handling mechanisms as detailed in [Phase 4: API Endpoints & Controllers](../../04-api-endpoints/).
- **Granularity**: APIs should be granular enough to allow clients to fetch only the data they need. Avoid overly chatty APIs or overly coarse-grained APIs that return excessive data.
- **AWS API Gateway**: APIs will typically be exposed through Amazon API Gateway, which enforces consistent security, throttling, and monitoring measures.

## 3. Key Considerations for Exposing APIs Synchronously

### 3.1. Justification and Necessity
- Before another service integrates synchronously with a Product Service API, the need for synchronous communication must be clearly justified and documented by the consuming service, confirming that an asynchronous/event-driven approach is not viable for the specific use case.
- Product Service team should review and approve such integration requests to ensure they align with architectural principles and do not pose an undue risk to Product Service stability.
- Consider creating an architecture decision record (ADR) for any high-volume or critical synchronous integration patterns to document the rationale and alternatives considered.

### 3.2. Performance and Scalability
- **Impact Assessment**: Understand the potential performance impact on the Product Service from synchronous calls. High-volume synchronous calls can affect the service's resources and response times for its primary functions.
- **Caching**: Consider if responses from frequently accessed, read-only synchronous endpoints can be cached (e.g., at the API Gateway level, using AWS CloudFront, or using HTTP caching headers), if data freshness requirements allow.
- **Rate Limiting and Throttling**: Implement rate limiting and throttling (as defined in Phase 4 and configured at the Amazon API Gateway) to protect the Product Service from being overwhelmed by misbehaving or high-traffic client services.
- **Auto-scaling**: Configure appropriate AWS Auto Scaling policies based on API usage metrics to ensure sufficient capacity during peak periods.

### 3.3. Versioning
- Adhere to the API versioning strategy defined in Phase 4. Client services must consume versioned endpoints (e.g., `/v1/products/...`).
- Provide clear deprecation policies and timelines for older API versions to allow client services to migrate smoothly.
- Use API Gateway stage variables or other AWS-specific mechanisms to manage different versions efficiently.

### 3.4. Security
- **Authentication & Authorization**: All synchronous API calls to Product Service must be authenticated and authorized using the mechanisms defined in Phase 4 (e.g., AWS Cognito, AWS IAM roles, service-to-service OAuth 2.0 client credentials flow via the API Gateway).
- **Principle of Least Privilege**: Client services should be granted only the necessary permissions to access specific Product Service APIs and data they require.
- **Input Validation**: Rigorously validate all input parameters from client services to protect against invalid data and potential security vulnerabilities, as per Phase 4 guidelines.
- **AWS WAF**: Consider using AWS WAF (Web Application Firewall) for additional protection against common web exploits for critical API endpoints.

### 3.5. Error Handling
- Consistently use standard HTTP status codes for responses, as defined in Phase 4 (e.g., `2xx` for success, `4xx` for client errors, `5xx` for server errors).
- Provide clear and concise error messages in the response body, preferably in a standardized JSON format, including a `correlationId`.
- Avoid leaking sensitive information or internal stack traces in error responses.
- Log errors to AWS CloudWatch with appropriate severity levels to enable monitoring and alerting.

### 3.6. Idempotency
- For any Product Service API endpoints that modify state (e.g., `POST`, `PUT`, `DELETE`, though these are less likely to be common synchronous inter-service integration points compared to `GET`), strive to make them idempotent if there's a chance clients might retry them.
- Consider using AWS DynamoDB or similar persistent storage to track idempotency tokens if needed for critical write operations.
- Clients consuming these APIs should also follow retry best practices (see [07-general-api-consumption-guidelines.md](./07-general-api-consumption-guidelines.md)).

## 4. Responsibilities of Consuming Services

Services that consume Product Service APIs synchronously are responsible for:
- Adhering to the API contract defined in the Product Service OpenAPI specification.
- Implementing resilience patterns on their side (timeouts, retries, circuit breakers) as outlined in their own API consumption guidelines (or a general platform guideline if available).
- Handling errors gracefully and not propagating Product Service failures in a way that destabilizes their own service.
- Managing their consumption rate and respecting any rate limits imposed by the Product Service or API Gateway.
- Keeping their integration updated in response to Product Service API version changes and deprecation notices.
- Following the principle that asynchronous event-driven integration is preferred and synchronous calls are exceptional.

## 5. Monitoring and Logging (Product Service Perspective)

- **Metrics**: Product Service (and the Amazon API Gateway in front of it) should expose metrics for all synchronously consumed API endpoints:
    - Request count (per client, per endpoint).
    - Error rates (per client, per endpoint).
    - Latency (average, p95, p99).
    - Rate limit hits.
- **AWS CloudWatch**: Use AWS CloudWatch for comprehensive logging and metrics collection:
    - Set up CloudWatch Dashboards for visualizing API performance and usage patterns.
    - Configure CloudWatch Alarms for anomaly detection and alerting.
- **Logging**: Log all incoming synchronous requests and their responses (sanitizing sensitive data), including `correlationId`, client identifier (if available from auth token), requested endpoint, and response status.
- **AWS X-Ray**: Consider using AWS X-Ray for distributed tracing across services to identify performance bottlenecks and troubleshoot request flows.
- **Alerting**: Set up alerts for high error rates, increased latency, or unusual traffic patterns on synchronously exposed APIs, especially if specific clients are causing issues.

## 6. Documentation

- The [Product Service OpenAPI Specification](../../openapi/product-service.yaml) serves as the primary technical documentation for exposed APIs.
- This document provides the overarching guidelines for such exposures.
- Specific high-impact synchronous integrations might warrant their own brief integration agreement or document outlining the justification and expected load, SLAs etc.
- Include AWS-specific configuration details (API Gateway settings, IAM permissions, etc.) in the documentation for each exposed API endpoint.

By following these guidelines, the Product Service can expose APIs for exceptional synchronous consumption in a controlled, secure, and manageable way, minimizing risks to its own stability and performance while still strongly preferring the asynchronous event-driven approach for most integration scenarios. 