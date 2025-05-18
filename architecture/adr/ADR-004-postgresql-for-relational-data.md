# ADR: Primary Relational Database Choice (PostgreSQL)

*   **Status:** Accepted
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (N/A - can be updated)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

Many services within the e-commerce platform, such as User Management, Order Management, and Product Catalog (for core structured data), will require a persistent data store that ensures data integrity, supports complex relationships, and provides transactional consistency (ACID properties). A relational database management system (RDBMS) is typically well-suited for these requirements. This ADR documents the choice of a specific RDBMS for services needing such capabilities.

## Decision Drivers

*   **Data Integrity & Consistency:** Strong enforcement of schemas, relationships (foreign keys), and ACID properties for transactions.
*   **Querying Capabilities:** Powerful SQL support for complex queries, joins, and aggregations.
*   **Maturity & Reliability:** A proven, stable, and reliable database system.
*   **Ecosystem & Tooling:** Availability of good client libraries, ORMs/query builders, administration tools, and community support.
*   **Cloud Provider Support:** Widely available as a managed service on major cloud platforms.
*   **Open Source & Cost:** Preference for a strong open-source option to avoid vendor lock-in and reduce licensing costs.
*   **Extensibility & Advanced Features:** Support for features like JSONB, full-text search, GIS extensions, etc., can be beneficial.

## Considered Options

### Option 1: PostgreSQL

*   **Description:** A powerful, open-source object-relational database system with a strong reputation for reliability, feature robustness, and data integrity.
*   **Pros:**
    *   **ACID Compliance:** Strong transactional integrity.
    *   **Feature-Rich:** Supports advanced SQL features, JSONB (for semi-structured data), full-text search, extensibility (custom types, functions, extensions).
    *   **Highly Reliable and Stable.**
    *   **Strong Open Source Community & Ecosystem.**
    *   **Excellent Cloud Support:** Available as a managed service (e.g., AWS RDS for PostgreSQL, Azure Database for PostgreSQL, Google Cloud SQL for PostgreSQL).
    *   **Good performance for complex queries.**
    *   **MVCC (Multi-Version Concurrency Control):** Handles concurrent access well.
*   **Cons:**
    *   **Scalability for Extreme Write Loads:** Like most traditional RDBMS, scaling writes horizontally can be complex and may require techniques like sharding or read replicas with careful application design.
    *   **Complexity:** Can have a steeper learning curve for advanced features and administration compared to simpler databases if self-managed.

### Option 2: MySQL

*   **Description:** Another very popular open-source relational database system.
*   **Pros:**
    *   **Widely Used & Large Community.**
    *   **Good Performance:** Especially for read-heavy workloads.
    *   **ACID Compliant (with InnoDB engine).**
    *   **Good Cloud Support:** Available as a managed service.
    *   **Simpler to set up and manage for basic use cases for some users.**
*   **Cons:**
    *   **Historically Lagged PostgreSQL in Some Advanced Features:** Though it has caught up significantly.
    *   **Oracle Ownership:** While open source, Oracle's stewardship raises concerns for some regarding future licensing or development direction (though Percona Server and MariaDB are popular forks).
    *   **Default transaction isolation levels sometimes cause confusion.**

### Option 3: NoSQL Document Database (e.g., MongoDB) - as a primary for structured data

*   **Description:** Using a NoSQL document database as the primary store for traditionally relational data.
*   **Pros:**
    *   **Flexible Schema:** Easier to change data structures.
    *   **Horizontal Scalability:** Often designed for easier horizontal scaling of writes and reads for specific workloads.
    *   **Developer Friendliness for Certain Data Models:** Mapping application objects to documents can be straightforward.
*   **Cons:**
    *   **Not Ideal for Highly Relational Data:** Managing relationships and ensuring consistency across documents/collections can be complex and often requires application-level logic.
    *   **Limited ACID Transaction Support:** While improving (e.g., MongoDB multi-document transactions), it's often not as comprehensive or as ingrained as in RDBMS for complex transactions.
    *   **Eventual Consistency:** Can be a default for many operations, which may not be suitable for core transactional data requiring strong consistency.
    *   **Complex Queries:** Ad-hoc complex queries and joins across different types of documents can be less efficient or harder to implement than in SQL.

## Decision Outcome

**Chosen Option:** PostgreSQL

**Reasoning:**
PostgreSQL is chosen as the primary relational database for services requiring strong transactional consistency and complex relational data modeling. Its reputation for data integrity, comprehensive feature set (including excellent JSONB support which offers flexibility), strong adherence to SQL standards, robust open-source community, and excellent support as a managed service on major cloud platforms make it a compelling choice.

For services like User Management, Order Management, and others dealing with critical, structured data, PostgreSQL provides the necessary reliability and ACID guarantees. Its extensibility also offers future-proofing should advanced database features be required.

While NoSQL databases will be considered for specific use cases where their strengths are more aligned (as per the "Decentralized Data Management & Polyglot Persistence" principle), PostgreSQL will be the default choice for relational persistence needs.

### Positive Consequences
*   Strong data integrity and ACID compliance for transactional data.
*   Powerful SQL querying capabilities.
*   Mature and reliable platform with a large, active community.
*   Flexibility with JSONB support for semi-structured data within a relational model.
*   Excellent availability as a managed service, reducing operational burden.
*   Avoids vendor lock-in associated with proprietary RDBMS solutions.

### Negative Consequences (and Mitigations)
*   **Write Scalability Challenges for Extreme Loads:**
    *   **Mitigation:** Employ good database design, indexing, query optimization. Utilize read replicas for read scaling. For extreme write loads, consider application-level sharding or explore PostgreSQL clustering/distribution solutions if necessary, though this adds complexity. For services where this is a primary concern from the outset, a NoSQL database might be a better fit for that specific service.
*   **Operational Complexity if Self-Managed:**
    *   **Mitigation:** Strongly prefer using managed PostgreSQL services from cloud providers to offload a significant portion of the operational tasks (backups, patching, scaling, HA).

### Neutral Consequences
*   Requires developers to be proficient with SQL and relational database concepts.

## Links

*   [ADR-003: Primary Programming Language and Framework for Initial Services (Node.js with NestJS)](./ADR-003-nodejs-nestjs-for-initial-services.md)
*   [E-commerce Platform: System Architecture Overview](../00-system-architecture-overview.md)
*   (Potentially: Link to `02-user-management-service.md` once updated)

## Future Considerations

*   Standardize on a specific managed PostgreSQL offering (e.g., AWS RDS for PostgreSQL) and version.
*   Establish guidelines for schema design, indexing, and query optimization.
*   Evaluate the need for connection pooling strategies.
*   Consider tools for schema migration management (e.g., TypeORM migrations if using NestJS, Flyway, Liquibase).

## Rejection Criteria

*   If the vast majority of services evolve to require data models that are overwhelmingly non-relational and PostgreSQL's strengths are underutilized, making its overhead less justifiable.
*   If a specific managed cloud RDBMS offers compelling advantages in terms of serverless capabilities, extreme scalability, or unique features that significantly outweigh the benefits of standard PostgreSQL for most services.
