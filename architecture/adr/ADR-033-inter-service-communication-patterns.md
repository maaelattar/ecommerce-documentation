# ADR-033: Inter-Service Communication Patterns

*   **Status:** Proposed
*   **Date:** 2025-05-11
*   **Deciders:** Project Team, Lead Developers, Architects
*   **Consulted:** Development Teams
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In our microservices architecture (ADR-001), services need to communicate with each other. The choice of communication patterns significantly impacts system characteristics like coupling, resilience, latency, and complexity. While ADR-002 advocates for Event-Driven Architecture (EDA) as a primary style, and ADR-030 defines API design for synchronous interactions, this ADR provides a more detailed decision framework for choosing appropriate inter-service communication patterns based on specific needs.

## Decision Drivers

*   **Coupling:** Minimize tight coupling between services to allow independent development, deployment, and scaling.
*   **Resilience & Fault Tolerance (ADR-022):** Ensure that the failure of one service does not cascade and bring down other services.
*   **Performance & Latency:** Select patterns that meet the performance requirements of specific interactions.
*   **Consistency:** Balance between strong and eventual consistency based on business needs.
*   **Complexity:** Choose patterns that are understandable and manageable for the development team.
*   **Scalability:** Support scaling of individual services based on demand.
*   **Observability (ADR-010, ADR-011, ADR-017):** Ensure communication can be effectively logged, monitored, and traced.

## Decision Outcome

**Chosen Approach:** Employ a hybrid approach, favoring asynchronous communication for loose coupling and resilience, but allowing synchronous communication where strong consistency or immediate responses are critical. The choice will be guided by the nature of the interaction (query vs. command, need for immediate response, data consistency requirements).

### 1. Asynchronous Communication (Preferred for Decoupling and Resilience)

Based on ADR-002 (Event-Driven Architecture) and ADR-018 (Message Broker Strategy - RabbitMQ/Kafka).

*   **Pattern: Event-Based / Publish-Subscribe**
    *   **Description:** Services publish events to a message broker when significant state changes occur. Other interested services subscribe to these events and react accordingly.
    *   **Use Cases:**
        *   Notifying other services of domain events (e.g., `OrderCreated`, `UserRegistered`, `InventoryUpdated`).
        *   Decoupling services that don't need an immediate response from the producer.
        *   Workflows spanning multiple services where eventual consistency is acceptable.
        *   Data synchronization across different bounded contexts.
    *   **Technology:** RabbitMQ (for typical pub/sub, work queues) or Kafka (for high-throughput event streaming, event sourcing - ADR-018).
    *   **Pros:** High decoupling, resilience to consumer unavailability, scalability of consumers, producer is unaware of consumers.
    *   **Cons:** Eventual consistency, complexity in managing event schemas and versions, requires careful design of idempotent consumers (ADR-018), harder to trace end-to-end flows without good distributed tracing (ADR-017).

*   **Pattern: Command-Based / Asynchronous Request-Response (via Queues)**
    *   **Description:** A service sends a command message to a queue, and another service processes it. If a response is needed, the processing service can send a reply message to a dedicated reply queue, often correlated with a `CorrelationId`.
    *   **Use Cases:**
        *   Offloading long-running tasks (e.g., report generation, bulk email sending).
        *   Operations where the caller doesn't need to wait for immediate completion but might need eventual status/result.
        *   Improving resilience when the processing service might be temporarily unavailable.
    *   **Technology:** RabbitMQ (ADR-018).
    *   **Pros:** Decoupling, improved resilience, caller not blocked.
    *   **Cons:** More complex than simple pub/sub if a response is needed, eventual consistency of the outcome.

### 2. Synchronous Communication (For Immediate Consistency or Queries)

Based on ADR-030 (API Design Guidelines).

*   **Pattern: Request-Response (e.g., REST, gRPC)**
    *   **Description:** A service makes a direct request to another service and waits for a response.
    *   **Use Cases:**
        *   Queries that require immediate data from another service (e.g., `Order Service` fetching product details from `Product Service` to validate an order if local cache is stale).
        *   Operations requiring strong consistency where an immediate success/failure confirmation is essential and atomicity is managed by the caller or a distributed transaction coordinator (use with caution).
        *   Client-facing interactions via an API Gateway (ADR-014) often involve synchronous calls to backend services.
    *   **Technology:** RESTful APIs over HTTP/S (ADR-030), potentially gRPC for internal, high-performance scenarios (though NestJS primarily supports REST out-of-the-box - ADR-003).
    *   **Pros:** Simpler to understand and implement for basic interactions, immediate feedback, strong consistency (if designed correctly).
    *   **Cons:** Tighter coupling (caller and callee must be available simultaneously), can lead to cascading failures if not managed with resilience patterns (ADR-022 like circuit breakers, timeouts, retries), can introduce latency if call chains are long.

### Guiding Principles for Choosing:

1.  **Favor Asynchronous by Default:** Start by considering if an interaction can be asynchronous. This promotes better decoupling and resilience.
2.  **Queries vs. Commands:**
    *   **Commands** (actions that change state) are good candidates for asynchronous patterns, especially if they can be eventually consistent.
    *   **Queries** (requests for data) often necessitate synchronous communication if the data is needed immediately. However, consider if a stale (but recent) local copy/cache of the data is acceptable (see Caching Strategy ADR-009 and Data Management ADR-020), which could reduce synchronous calls.
3.  **Consistency Needs:** If an operation requires immediate, strong consistency across services, synchronous communication might be necessary. However, evaluate if the business process can tolerate eventual consistency, which allows for more resilient asynchronous patterns.
4.  **Temporal Coupling:** If Service A *must* have an immediate response from Service B to proceed, synchronous is likely. If Service A can continue its work and get a response/confirmation later, asynchronous is better.
5.  **Resilience Requirements (ADR-022):** All synchronous calls MUST be protected by resilience patterns (timeouts, retries, circuit breakers).
6.  **Service Autonomy:** Asynchronous communication generally enhances service autonomy more than synchronous communication.

### Hybrid Patterns

*   **Saga Pattern (for distributed transactions - often asynchronous):** For long-running business processes that span multiple services and require atomicity or compensation. Orchestrated sagas (a central coordinator) or choreographed sagas (services react to each other's events) can be implemented using asynchronous messaging.
*   **API Composition / Aggregation (often synchronous at the edge):** The API Gateway (ADR-014) or a dedicated Backend-For-Frontend (BFF) might make multiple synchronous calls to internal services and aggregate their responses for an external client.

## Consequences

*   **Pros:**
    *   Provides a flexible framework for choosing the most appropriate communication style.
    *   Promotes loose coupling and resilience by defaulting to asynchronous patterns where feasible.
    *   Allows for performance and consistency optimizations by using synchronous patterns when necessary.
    *   Aligns with existing ADRs for EDA, API design, and message brokers.
*   **Cons:**
    *   Requires careful consideration by developers for each interaction, increasing design effort.
    *   Managing a mix of synchronous and asynchronous patterns can add complexity to the overall system architecture and observability.
    *   Potential for misuse if guidelines are not followed (e.g., overusing synchronous calls where asynchronous would be better).
*   **Risks:**
    *   Teams might default to familiar synchronous patterns without adequately evaluating asynchronous alternatives.
    *   Increased complexity in debugging and tracing interactions that span multiple patterns without robust observability tools (ADR-017).

## Next Steps

*   Educate development teams on these patterns and the decision-making framework.
*   Incorporate discussion of inter-service communication choices into design reviews for new features/services.
*   Provide examples and potentially starter code/libraries for implementing common patterns (e.g., reliable event publishing, request-response over queues).
*   Ensure monitoring and tracing tools (ADR-011, ADR-017) are configured to provide visibility into both synchronous and asynchronous interactions.
*   Periodically review the effectiveness of chosen patterns and update guidelines as needed.
