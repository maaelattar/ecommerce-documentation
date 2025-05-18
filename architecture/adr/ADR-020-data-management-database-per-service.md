# ADR-020: Data Management and Database per Service Strategy

*   **Status:** Proposed
*   **Date:** 2025-05-11
*   **Deciders:** Project Team
*   **Consulted:** Lead Developers, Database Administrators (if any)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In a microservices architecture (ADR-001), each service is responsible for its own domain and should have autonomy over its data. This ADR outlines the strategy for data management, emphasizing the "database per service" pattern, and addresses challenges like data consistency, choosing appropriate database technologies, and data isolation.

## Decision Drivers

*   **Service Autonomy & Loose Coupling:** Services should be able to choose their own database technology and evolve their schema independently.
*   **Scalability:** Individual databases can be scaled based on the specific needs of their service.
*   **Resilience:** Failure in one service's database should not directly impact other services.
*   **Technology Diversity (Polyglot Persistence):** Ability to use the best database type (SQL, NoSQL, graph, etc.) for each service's specific requirements.
*   **Data Integrity:** Maintaining consistency of data, especially for transactions spanning multiple services.

## Considered Options

1.  **Shared Database:** All services share a single, monolithic database. (Violates microservice principles).
2.  **Database per Service:** Each microservice owns and manages its private database. No other service can access it directly.
3.  **Schema per Service (in a Shared Database Server):** Services have their own schemas within a shared database server. (Offers some isolation but less autonomy than database per service).

## Decision Outcome

**Chosen Option:** Database per Service.

*   **Private Databases:** Each microservice will have its own dedicated database (or a private schema on a shared database server if strict physical isolation is not immediately feasible for all services, but with the clear goal of eventual dedicated databases). Direct database access between services is strictly prohibited.
*   **API-based Data Access:** Services must expose APIs for other services to access or modify their data. This enforces encapsulation and allows the owning service to manage its data integrity and schema evolution.
*   **Polyglot Persistence:** Teams are encouraged to choose the database technology (e.g., PostgreSQL, MongoDB, Redis, Cassandra, Elasticsearch) that best fits their service's specific needs (data structure, query patterns, consistency requirements, scalability). This choice should be justified and documented.
*   **Data Consistency Across Services:**
    *   **Eventual Consistency:** For many scenarios, eventual consistency will be acceptable. Asynchronous communication via a message broker (ADR-018, e.g., RabbitMQ, Kafka) and event-driven patterns (ADR-002) will be the primary mechanism for propagating state changes between services.
    *   **Saga Pattern:** For transactions that span multiple services and require atomicity or compensation, the Saga pattern will be implemented. This involves a sequence of local transactions, where each service commits its own transaction and publishes an event to trigger the next step in the saga. Compensation logic must be implemented to roll back changes in case of failures.
    *   **Synchronous Queries (Avoid if Possible):** If data from multiple services is needed synchronously for a read operation, an API Gateway (ADR-014) or a dedicated aggregator service might be used to compose data. However, designs should favor asynchronous data replication or cached views where possible to avoid tight coupling.
*   **Data Replication and Caching:** For read-heavy scenarios or to reduce latency, services may maintain local, read-only replicas or caches of data owned by other services, updated via events.
*   **Database Schema Management:** Each service team is responsible for managing its database schema evolution (e.g., using migration tools like Flyway, Liquibase, or ORM-specific tools).
*   **Backup and Recovery:** Each database must have a defined backup and recovery strategy, aligned with the service's RPO/RTO requirements.

## Consequences

*   **Pros:**
    *   Enforces loose coupling and high cohesion for services.
    *   Allows teams to choose the best data store for their needs.
    *   Improved scalability and resilience at the service level.
    *   Independent schema evolution.
*   **Cons:**
    *   Increased complexity in managing multiple databases.
    *   Implementing sagas and ensuring eventual consistency can be challenging.
    *   Reporting across multiple services can be more complex, potentially requiring data warehousing or specialized query services.
    *   Higher operational overhead (provisioning, monitoring, backing up multiple databases).
*   **Risks:**
    *   Potential for data inconsistencies if event-driven updates or sagas are not implemented correctly.
    *   Difficulty in choosing the 'right' database if teams lack experience with diverse data stores.

## Next Steps

*   Provide guidelines and examples for implementing the Saga pattern.
*   Establish best practices for choosing database technologies.
*   Develop common libraries or patterns for event publishing and consumption related to data changes.
*   Define operational procedures for managing a diverse set of databases on Kubernetes (ADR-006), possibly leveraging database operators.
