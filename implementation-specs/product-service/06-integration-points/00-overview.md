# Phase 6: Integration with Other Services - Overview

## 1. Purpose

This phase details how the Product Service integrates with other microservices within the e-commerce platform. The **primary and preferred method for inter-service integration is asynchronous, event-driven communication**, as detailed in [Phase 5: Event Publishing](../../05-event-publishing/). This approach promotes loose coupling, resilience, and scalability, aligning with AWS best practices and our architectural principles.

This section (Phase 6) focuses on:
-   Re-evaluating previously considered synchronous interactions to prioritize asynchronous alternatives.
-   Detailing specific, justified scenarios where synchronous RESTful API calls might still be necessary for request/response interactions requiring immediate consistency.
-   Documenting the crucial asynchronous integration with the Search Service.

## 2. Integration Strategy: Asynchronous First

- **Asynchronous, Event-Driven (Primary)**: Most integrations are achieved by services consuming events published by the Product Service (and vice-versa) via a central message broker (Amazon MQ for RabbitMQ or Amazon MSK, as per [03-message-broker-selection.md](../../../architecture/technology-decisions-aws-centeric/03-message-broker-selection.md)). This is detailed in [Phase 5: Event Publishing](../../05-event-publishing/).
- **Synchronous API Calls (Secondary & Exceptional)**:
    - Direct synchronous API calls are considered secondary and should only be used for specific, well-justified scenarios where asynchronous patterns are not suitable. Examples include:
        -   Direct user-initiated requests requiring an immediate response where eventual consistency is not acceptable (e.g., a real-time price check *at the very moment of transaction finalization*, if event-driven updates to a local cache in the calling service are deemed insufficient).
        -   Interactions with highly available foundational services where the call is simple, and the data is not easily replicated or evented.
    - Any synchronous API call introduces tighter coupling and potential for cascading failures. Therefore, they must be accompanied by robust resilience patterns.
- **API-First Approach (for Synchronous APIs)**: When synchronous APIs are used, they must be well-defined and versioned RESTful APIs.
- **Loose Coupling**: Direct database sharing is strictly avoided. Services communicate via public API contracts or events.
- **Resilience (for Synchronous APIs)**: Product Service, when calling other services synchronously, MUST implement patterns like timeouts, retries (with backoff and jitter), and circuit breakers.
- **Security**: All inter-service communication (asynchronous via message broker, or synchronous via API) must be secured (e.g., mTLS for service-to-service API calls, appropriate authentication/authorization for accessing message brokers).
- **Contract Definition**:
    - Asynchronous: Event structures are defined in Phase 5.
    - Synchronous: OpenAPI specifications are used to define the contracts for APIs consumed and exposed.

## 3. Key Integrated Services & Interaction Patterns

### 3.1. Inventory Service
- **Product Service Interaction with Inventory Service**:
  - **Asynchronous (Preferred)**: For most stock updates, Product Service would rely on Inventory Service to consume product creation/update events to manage its own inventory records. Inventory Service would publish its own events (e.g., `StockLevelChanged`) which Product Service or other services could consume if they need to be aware of inventory changes (e.g., for updating a cache).
  - **Synchronous API Calls (Exceptional & Justified)**:
    - **Potentially**: A synchronous call from Product Service to Inventory Service *might* be justified to initialize an inventory record immediately after a new product variant is created *if* there's a strict business requirement that the variant cannot exist without a confirmed inventory record. This needs careful evaluation against an event-driven approach (e.g., Product Service creates variant, publishes event, Inventory Service consumes and confirms, variant becomes active after confirmation event).
    - **Fetching real-time stock (if absolutely necessary synchronously)**: If a direct, real-time stock check is needed by an internal Product Service administrative operation that cannot rely on an eventually consistent local cache, a synchronous call might be considered but should be a rare exception.
  - **Details**: See [01-inventory-service-integration.md](./01-inventory-service-integration.md)

### 3.2. Order Service
- **Order Service Interaction with Product Service**:
  - **Asynchronous (Preferred for data replication)**: Order Service should consume `ProductUpdated`, `ProductPriceChanged`, `ProductStatusChanged` events from Product Service to maintain a local, eventually consistent cache/projection of product data relevant for order processing (e.g., for cart validation against relatively stable data).
  - **Synchronous API Calls (Exceptional & Justified)**:
    - **Fetching Product Details/Price at Order Placement**: A synchronous call from Order Service to Product Service (`GET /products/variants/{variantId}` or `GET /products/variants/{variantId}/price`) *at the point of order creation/checkout* is likely justified. This ensures the Order Service captures the exact product details and price at the moment of transaction, preventing inconsistencies due to subsequent product changes. This captured data should then be snapshotted with the order.
  - **Data Consistency**: Order Service maintains a local denormalized snapshot of product details at the time of order creation to ensure historical accuracy and avoid dependencies on Product Service for retrieving historical product information.
  - **Details**: Product Service exposes its APIs (defined in Phase 4) for such justified synchronous consumption. Key endpoints are documented in [02-order-service-integration.md](./02-order-service-integration.md)

### 3.3. Search Service (Amazon OpenSearch Service)
-   **Product Service Integration with Search Service**: This is a core asynchronous integration.
    -   Product Service publishes events for all relevant data changes (products, categories, prices, etc.).
    -   A Search Event Consumer (separate service/component) consumes these events and updates the Amazon OpenSearch Service index.
    -   **Type**: Asynchronous, Event-Driven.
    -   **Details**: See [06-search-service-integration.md](./06-search-service-integration.md)

### 3.4. User Service (Potential)
- **Product Service Calls User Service**:
  - **Details**: See [03-user-service-integration.md](./03-user-service-integration.md) (Primarily asynchronous patterns with clearly justified exceptions for synchronous calls).
- **User Service Calls Product Service**: Potentially if user profiles or dashboards display product-related information.
  - **Asynchronous Preferred**: User service could consume product events to update its own views.
  - **Synchronous API Calls (Exceptional)**: If real-time data is needed for a specific user interaction.
  - **Type**: Primarily Asynchronous; Synchronous API calls if justified.

### 3.5. Review Service (Potential, if a separate service)
- **Product Service Calls Review Service**:
  - **Details**: See [04-review-service-integration.md](./04-review-service-integration.md) (Primarily asynchronous patterns with clearly justified exceptions for synchronous calls).
- **Review Service Calls Product Service**: To fetch product details when a review is submitted or displayed.
  - **Synchronous API Calls (Potentially Justified)**: When submitting a new review, Review Service might synchronously call Product Service to validate `productId` and fetch current product name. For displaying reviews, asynchronous population of product data is preferred.
  - **Type**: Mixed; Synchronous API calls for validation, Asynchronous for data enrichment where possible.

### 3.6. Notification Service (Potential for direct calls)
- **Product Service Calls Notification Service**:
  - **Details**: See [05-notification-service-integration.md](./05-notification-service-integration.md) (Primarily event-driven notifications with synchronous calls only for critical operational alerts).
  - **Type**: Primarily Asynchronous, with limited justified synchronous API calls (by nature of direct notification triggering, but event-driven notifications are preferred for most scenarios via a Notification Service consuming other services' events).

## 4. General API Consumption Guidelines (for Product Service as a Synchronous Client)

When Product Service, in exceptional and justified cases, calls other external services synchronously, it must adhere to best practices:
- Configurable timeouts for all external calls.
- Retry mechanisms (e.g., exponential backoff) for transient failures.
- Circuit breaker patterns for services that are critical or prone to instability.
- Secure handling of credentials or tokens required to call other services.
- Consistent logging of requests and responses (or errors) with correlation IDs.
- **Details**: See [./07-general-api-consumption-guidelines.md](./07-general-api-consumption-guidelines.md)

## 5. Exposing Product Service APIs (for Other Services as Synchronous Clients)

When other services, in exceptional and justified cases, call Product Service APIs synchronously:
- APIs are defined by the [Product Service OpenAPI Specification](../openapi/product-service.yaml).
- Versioning, authentication, authorization, rate limiting, and error handling are as defined in Phase 4 API documentation.
- Service Level Agreements (SLAs) for API availability and response times should be defined and monitored.
- **Details**: See [./08-exposing-product-service-apis.md](./08-exposing-product-service-apis.md)

## 6. Next Steps

- Define additional integration patterns that might emerge as the system evolves.
- Update service integration details as other microservices are designed in more detail.
- Refine error handling and resilience strategies as implementation begins.
- Document concrete message broker configuration once the specific AWS service (Amazon MQ or Amazon MSK) is finally selected and configured. 