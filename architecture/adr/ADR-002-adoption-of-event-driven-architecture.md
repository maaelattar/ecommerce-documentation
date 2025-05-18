# ADR: Adoption of Event-Driven Architecture (EDA)

*   **Status:** Accepted
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team (Aligned with architectural vision)
*   **Consulted:** (N/A - can be updated)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In a microservices architecture, services need to communicate and react to changes in other parts of the system. Relying solely on synchronous, request/response communication can lead to tight coupling, reduced resilience (cascading failures if a synchronous dependency is down), and scalability bottlenecks. The platform requires mechanisms for services to be loosely coupled, highly available, responsive, and scalable, allowing for asynchronous processing and complex workflows.

## Decision Drivers

*   **Loose Coupling:** Services should be able to operate and evolve independently without direct knowledge of all consumers or producers of information.
*   **Resilience & Fault Tolerance:** The system should be able to withstand failures in individual services without major disruptions. Asynchronous communication helps decouple service availability.
*   **Scalability & Responsiveness:** Enable services to handle load independently and process requests asynchronously, improving overall system responsiveness and throughput.
*   **Extensibility:** Allow new services to easily subscribe to relevant events and react to them without requiring changes in existing services.
*   **Complex Event Processing:** Support for scenarios where multiple services need to react to the same event, or where workflows are triggered by sequences of events.

## Considered Options

### Option 1: Exclusively Synchronous (Request/Response) Communication

*   **Description:** All inter-service communication relies on direct API calls (e.g., REST, gRPC).
*   **Pros:**
    *   Simpler to understand and implement for basic interactions.
    *   Immediate feedback for requests.
    *   Well-established patterns and tooling.
*   **Cons:**
    *   Creates tight coupling between services; a service needs to know the direct address and API of services it calls.
    *   Reduced resilience; failure or slowdown in a called service directly impacts the caller.
    *   Can lead to complex chained calls, increasing latency and reducing overall system availability ("temporal coupling").
    *   Difficult to implement "fire-and-forget" patterns or broadcast information to multiple interested parties efficiently.
    *   Scalability of a service can be limited by the scalability of its synchronous dependencies.

### Option 2: Predominantly Event-Driven Architecture (EDA) with Asynchronous Communication

*   **Description:** Prioritize asynchronous communication between services using a message broker. Services publish events when significant state changes occur, and other interested services subscribe to these events. Synchronous communication is used judiciously where immediate responses are essential (e.g., queries).
*   **Pros:**
    *   **Loose Coupling:** Services interact via events and a message broker, reducing direct dependencies. Producers don't need to know about consumers.
    *   **Improved Resilience:** The message broker can act as a buffer, allowing services to operate even if other services are temporarily unavailable. Failures are less likely to cascade.
    *   **Enhanced Scalability & Elasticity:** Services can be scaled independently. The message broker can absorb spikes in load.
    *   **Increased Responsiveness:** Services can offload work for asynchronous processing, improving response times for primary requests.
    *   **Greater Extensibility:** New services can easily subscribe to existing event streams without modifying producer services.
    *   **Supports complex workflows and data consistency patterns** (e.g., Sagas for distributed transactions).
*   **Cons:**
    *   **Increased Complexity:** Introduces a message broker as a critical infrastructure component that needs to be managed and monitored.
    *   **Eventual Consistency:** Data consistency across services is often eventual, which requires careful design and can be harder to reason about for developers.
    *   **Debugging and Tracing:** Tracking a request flow across multiple asynchronous services can be more challenging (though distributed tracing tools help).
    *   **Requires careful event design and schema management.**
    *   Potential for message ordering issues if not handled correctly.

## Decision Outcome

**Chosen Option:** Predominantly Event-Driven Architecture (EDA) with Asynchronous Communication

**Reasoning:**
EDA is chosen as a primary architectural style to complement the Microservices architecture. It directly addresses the requirements for loose coupling, resilience, scalability, and extensibility, which are critical for the e-commerce platform's success. The benefits of decoupling services and improving fault tolerance outweigh the added complexity of managing a message broker and dealing with eventual consistency.

Synchronous communication will still be used where appropriate (e.g., user-facing queries requiring immediate data, or commands where a direct response is integral to the flow), but asynchronous event-based interaction will be the preferred default for inter-service communication involving state changes or triggering downstream processes.

This aligns with the guiding principles outlined in the `00-system-architecture-overview.md`.

### Positive Consequences
*   Services are more independent and resilient.
*   Improved system scalability and responsiveness.
*   Easier to add new services and features that react to existing system events.
*   Better support for complex, distributed workflows.
*   Decouples services in time; a service can publish an event even if consumers are not immediately available.

### Negative Consequences (and Mitigations)
*   **Operational Overhead of Message Broker:** Requires deployment, maintenance, and monitoring of a message broker.
    *   **Mitigation:** Leverage managed cloud services for message brokers (e.g., AWS Kinesis/SQS/SNS, Azure Event Hubs/Service Bus, Google Pub/Sub, or managed Kafka).
*   **Challenges with Eventual Consistency:** Developers need to understand and design for eventual consistency.
    *   **Mitigation:** Provide clear guidelines, patterns (e.g., Sagas), and training. Implement robust monitoring to detect consistency issues.
*   **Complexity in Debugging and Tracing:**
    *   **Mitigation:** Implement comprehensive distributed tracing across services and the message broker. Ensure structured logging with correlation IDs.
*   **Need for Event Schema Management and Governance:**
    *   **Mitigation:** Establish a schema registry and clear processes for evolving event schemas in a backward-compatible way.

### Neutral Consequences
*   Requires developers to be proficient in asynchronous programming paradigms.

## Links

*   [ADR-001: Adoption of Microservices Architecture for E-commerce Platform](./ADR-001-adoption-of-microservices-architecture.md)
*   [ADR-033: Inter-Service Communication Patterns](./ADR-033-inter-service-communication-patterns.md)
*   [E-commerce Platform: System Architecture Overview](../00-system-architecture-overview.md)

## Future Considerations

*   Selection of a specific message broker technology (e.g., Kafka, RabbitMQ, NATS, or cloud-specific options) will be documented in a separate ADR.
*   Patterns for handling event retries, dead-letter queues (DLQs), and idempotency will need to be standardized.
*   Consideration of Event Sourcing for specific services where appropriate.

## Rejection Criteria

*   If the majority of inter-service interactions prove to require immediate, strong consistency and synchronous responses, diminishing the benefits of EDA.
*   If the complexity of managing EDA significantly hampers development velocity despite mitigations.
