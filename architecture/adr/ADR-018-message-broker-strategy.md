# ADR-018: Message Broker Detailed Strategy and Selection

*   **Status:** Proposed
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (Lead Developers, DevOps/SRE Team)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

Our adoption of Event-Driven Architecture (ADR-002) necessitates a robust message broker to facilitate asynchronous communication between microservices. This allows for decoupling, improved resilience, and better scalability by enabling services to produce and consume events without direct synchronous dependencies. Events might include `OrderCreated`, `PaymentProcessed`, `InventoryUpdated`, `UserRegistered`, etc.

This ADR focuses on selecting a specific message broker technology and outlining key strategies for its usage, such as topic/queue design, message formats, error handling, and ensuring reliability.

## Decision Drivers

*   **Asynchronous Communication:** Enable services to communicate without blocking each other.
*   **Decoupling:** Producers of events should not need to know about the consumers, and vice-versa.
*   **Resilience & Fault Tolerance:** If a consumer service is temporarily unavailable, messages should be persisted by the broker and processed later.
*   **Scalability:** The broker must handle a high volume of messages and support scaling of producer/consumer services.
*   **Data Persistence:** Ensure messages are not lost in transit or due to broker failures (configurable).
*   **Ordering Guarantees:** Provide mechanisms for preserving message order where necessary (e.g., within a partition).
*   **Delivery Guarantees:** Support different delivery semantics (e.g., at-least-once, at-most-once).
*   **Developer Experience:** Ease of integration with our primary technology stack (Node.js/NestJS - ADR-003).
*   **Operational Manageability:** The broker should be manageable on Kubernetes (ADR-006) or available as a reliable managed service.
*   **Ecosystem & Community:** Availability of client libraries, documentation, and community support.

## Considered Options

### Option 1: No Message Broker (Direct HTTP/gRPC for all communication)

*   **Description:** All inter-service communication uses synchronous request/response patterns.
*   **Pros:** Simpler for request/response interactions.
*   **Cons:** Violates the principles of EDA (ADR-002). Leads to tight coupling and reduced resilience. Not suitable for event-driven workflows. (Already implicitly rejected by ADR-002).

### Option 2: Redis Streams

*   **Description:** Use Redis (already selected for caching in ADR-009) and its Streams feature as a lightweight message broker.
*   **Pros:**
    *   Leverages an existing technology component if Redis is already in place for other purposes.
    *   Relatively simple to understand and use for basic streaming.
    *   Persistent, append-only log structure. Supports consumer groups.
*   **Cons:**
    *   Not as feature-rich as dedicated message brokers (e.g., complex routing, dead-letter queue (DLQ) mechanisms might require more manual implementation, ecosystem for advanced stream processing is less mature).
    *   Might not scale as well or offer the same operational tooling as dedicated brokers for very high-throughput or complex eventing scenarios.
    *   Using Redis for both caching and primary message brokering might lead to resource contention or operational coupling.

### Option 3: RabbitMQ

*   **Description:** A mature, widely-used open-source message broker that implements protocols like AMQP.
*   **Pros:**
    *   Flexible routing capabilities (exchanges, queues, bindings).
    *   Supports various message patterns (e.g., pub/sub, request/reply, work queues).
    *   Good support for message acknowledgments, persistence, and consumer features like prefetch.
    *   Strong community and good client library support for Node.js.
    *   Mature management UI and operational tooling.
*   **Cons:**
    *   Can have a steeper learning curve for its routing model (AMQP).
    *   Clustering and high availability can be complex to set up and manage correctly, though Kubernetes operators can help.
    *   Performance might not match log-based brokers like Kafka for extremely high-throughput scenarios, but generally very good for typical microservice workloads.

### Option 4: Apache Kafka

*   **Description:** A distributed streaming platform designed for high-throughput, fault-tolerance, and scalability.
*   **Pros:**
    *   Extremely high performance and scalability.
    *   Durable, ordered, and replayable message logs (topics/partitions).
    *   Rich ecosystem, including Kafka Streams and ksqlDB for stream processing.
    *   Strong community and wide adoption.
*   **Cons:**
    *   More operationally complex to set up and manage than RabbitMQ, especially Zookeeper (though Kraft is simplifying this). Kubernetes operators (e.g., Strimzi) significantly help.
    *   Client-side complexity can be higher.
    *   Point-to-point queuing and complex routing scenarios require more thought compared to RabbitMQ's model.
    *   Might be overkill if the primary need is just simple asynchronous task queuing rather than high-volume event streaming or stream processing.

### Option 5: Managed Cloud Provider Message Broker Service

*   **Description:** Use a managed service like AWS SQS/SNS, Google Cloud Pub/Sub, or Azure Service Bus.
*   **Pros:**
    *   Reduced operational overhead (serverless or managed).
    *   Scalability and reliability managed by the cloud provider.
    *   Pay-as-you-go.
    *   Often integrates well with other services from the same cloud provider.
*   **Cons:**
    *   Vendor lock-in.
    *   Features and APIs are specific to the provider.
    *   May lack some of the advanced configuration or flexibility of self-hosted solutions.
    *   Cost can become a factor at very high volumes.

## Decision Outcome

**Chosen Option:** **RabbitMQ** as the primary message broker, deployed on Kubernetes (potentially using the RabbitMQ Cluster Kubernetes Operator). **Apache Kafka** will be considered for specific use cases requiring very high throughput or event stream processing capabilities if RabbitMQ proves insufficient for those.

**Reasoning:**

*   **RabbitMQ (Primary Choice):**
    *   Offers a good balance of features, flexibility, maturity, and developer experience for typical microservice eventing and asynchronous task processing.
    *   Its routing capabilities (exchanges and queues) are well-suited for various EDA patterns.
    *   Good Node.js client support aligns with ADR-003.
    *   The RabbitMQ Cluster Kubernetes Operator simplifies deployment and management on Kubernetes (ADR-006).
    *   It's generally considered easier to operate and manage for common microservice workloads compared to a full Kafka setup, especially when not needing Kafka's extreme scale or stream processing features from day one.

*   **Apache Kafka (Secondary/Specialized):**
    *   Recognized for its superior performance in high-throughput scenarios and its stream processing capabilities. If specific services (e.g., analytics event ingestion, real-time data pipelines) require these characteristics, Kafka (managed by an operator like Strimzi) would be the preferred choice for those event streams.

*   **Managed Services / Redis Streams:**
    *   Managed services are a good fallback if self-hosting RabbitMQ becomes an operational burden, but we prefer to start with an open-source solution that aligns with our self-hosted Kubernetes strategy.
    *   Redis Streams, while convenient, is deemed less feature-rich and robust for a general-purpose, platform-wide message broker compared to RabbitMQ or Kafka.

**Key Implementation Strategies:**

1.  **Topic/Exchange Design:**
    *   Use consistent naming conventions for exchanges and queues (e.g., `<ServiceName>.<EventName>.Exchange`, `<ConsumingService>.<EventName>.Queue`).
    *   Primarily use topic exchanges for pub/sub patterns, allowing flexible routing based on routing keys.
    *   Direct exchanges or fanout exchanges may be used for specific scenarios.
2.  **Message Format:**
    *   Standardize on **JSON** as the message payload format for interoperability.
    *   Consider using a schema definition (e.g., AsyncAPI, JSON Schema) for events to ensure clear contracts.
3.  **Error Handling & Dead Letter Queues (DLQs):**
    *   Implement robust error handling in consumers, including retries with backoff.
    *   Configure DLQs for messages that repeatedly fail processing, allowing for later inspection and potential reprocessing.
4.  **Idempotent Consumers:** Design consumers to be idempotent to safely handle message redeliveries (which can happen with at-least-once delivery).
5.  **Persistence:** Configure message and queue persistence in RabbitMQ to ensure messages survive broker restarts.
6.  **Monitoring:** Integrate RabbitMQ monitoring with our central monitoring solution (ADR-011) to track queue depths, message rates, consumer acknowledgments, etc.
7.  **Client Libraries:** Use well-supported Node.js client libraries for RabbitMQ (e.g., `amqplib`).

### Positive Consequences
*   Enables robust asynchronous communication and decoupling of services.
*   Improves system resilience by buffering messages.
*   Supports scalable processing of events.
*   RabbitMQ offers a good balance of features and operational manageability for our needs.

### Negative Consequences (and Mitigations)
*   **Operational Overhead (Self-Hosted RabbitMQ):** Managing a RabbitMQ cluster requires operational effort.
    *   **Mitigation:** Use the RabbitMQ Cluster Kubernetes Operator to simplify deployment, scaling, and management. Provide training and documentation. Consider a managed RabbitMQ service if self-hosting becomes too complex.
*   **Complexity:** EDA itself introduces a different programming model and potential complexities in debugging distributed flows (though ADR-017 for Tracing helps).
    *   **Mitigation:** Provide clear guidelines, best practices, and training for developing event-driven services. Use distributed tracing extensively.
*   **Message Ordering:** While RabbitMQ can guarantee order within a single queue, achieving global order across distributed consumers can be complex if strictly needed.
    *   **Mitigation:** Design systems to minimize the need for strict global ordering where possible. Utilize partitioned queues or ensure a single consumer per ordered stream if critical. For most e-commerce events, per-entity ordering (e.g., all events for a specific order ID are processed in order) is often sufficient and achievable.
*   **Potential for "Message Hell":** Proliferation of too many event types or complex routing without clear governance.
    *   **Mitigation:** Establish clear event definitions, a schema registry (potentially), and governance around event creation and consumption.

## Links

*   [ADR-001: Adoption of Microservices Architecture](./ADR-001-adoption-of-microservices-architecture.md)
*   [ADR-002: Adoption of Event-Driven Architecture](./ADR-002-adoption-of-event-driven-architecture.md)
*   [ADR-003: Node.js with NestJS for Initial Services](./ADR-003-nodejs-nestjs-for-initial-services.md)
*   [ADR-006: Cloud-Native Deployment Strategy](./ADR-006-cloud-native-deployment-strategy.md)
*   [ADR-011: Monitoring and Alerting Strategy](./ADR-011-monitoring-and-alerting-strategy.md)
*   [ADR-017: Distributed Tracing Strategy](./ADR-017-distributed-tracing-strategy.md)
*   [RabbitMQ](https://www.rabbitmq.com/)
*   [Apache Kafka](https://kafka.apache.org/)
*   [RabbitMQ Cluster Kubernetes Operator](https://www.rabbitmq.com/kubernetes/operator/rabbitmq-operator.html)

## Future Considerations

*   Adopting a schema registry for event definitions (e.g., Confluent Schema Registry if Kafka is used more broadly, or a standalone solution for JSON Schema).
*   Implementing more advanced stream processing patterns if Kafka usage expands.
*   Formalizing event versioning strategies.

## Rejection Criteria

*   If RabbitMQ proves unable to meet specific high-throughput or complex stream processing requirements for critical new features, those specific event streams will be implemented using Kafka.
*   If self-hosting RabbitMQ becomes an unmanageable operational burden, a switch to a managed RabbitMQ service or a suitable cloud provider messaging service will be considered.
