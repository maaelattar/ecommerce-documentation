# Technology Decision: Relational Database Selection (PostgreSQL)

*   **Status:** Accepted (Re-documenting ADR-004 decision)
*   **Date:** 2025-05-12
*   **Deciders:** Project Team (as per ADR-004)
*   **Consulted:** (As per ADR-004)
*   **Informed:** All technical stakeholders

## 1. Context & Scope

This document provides a detailed elaboration on the decision to select **PostgreSQL** as the primary relational database management system (RDBMS) for the e-commerce platform. This decision was originally captured in [ADR-004: PostgreSQL for Relational Data](./../adr/ADR-004-postgresql-for-relational-data.md).

Many core services within the e-commerce platform, including User Management, Product Catalog (core structured data), Order Management, and Payment Processing, require a robust, transactional, and consistent data store. PostgreSQL is chosen to fulfill these needs for services such as `User DB`, `Product DB`, `Order DB`, and `Payment DB` as identified in the C2 Container Diagram ([`c2-container-diagram.md`](./../diagrams/c4/c2%20(Container)/c2-container-diagram.md)).

## 2. Decision Drivers (Recap & Expansion)

The selection of PostgreSQL is driven by several key factors, initially outlined in ADR-004:

*   **Data Integrity & Consistency:** Unwavering requirement for ACID (Atomicity, Consistency, Isolation, Durability) properties to ensure reliable transactions and data accuracy.
*   **Querying Capabilities:** Need for powerful SQL support for complex queries, joins, aggregations, and data manipulation.
*   **Maturity & Reliability:** Preference for a proven, stable, and enterprise-ready database system with a strong track record.
*   **Ecosystem & Tooling:** Availability of comprehensive client libraries, ORMs/query builders, administration tools, and extensive community support.
*   **Cloud Provider Support:** Essential for leveraging managed services for deployment, maintenance, and scalability (e.g., AWS RDS, Azure Database for PostgreSQL, Google Cloud SQL).
*   **Open Source & Cost-Effectiveness:** Strong preference for a leading open-source solution to avoid vendor lock-in and minimize licensing costs.
*   **Extensibility & Advanced Features:** Support for features like JSONB for semi-structured data, full-text search, and a wide range of extensions enhances versatility.

## 3. Chosen Technology: PostgreSQL

### 3.1. Overview

PostgreSQL is a powerful, open-source object-relational database system renowned for its reliability, feature robustness, data integrity, and extensibility. It has a long history of active development and a vibrant community.

### 3.2. Detailed Advantages & Feature Alignment

*   **ACID Compliance and Reliability:** PostgreSQL is strictly ACID compliant, providing a strong foundation for transactional integrity crucial for e-commerce operations.
*   **Advanced SQL and Data Types:** Offers a rich SQL dialect and supports a wide array of data types, including native JSON/JSONB support. JSONB allows for storing and querying semi-structured data efficiently within the relational model, offering flexibility where needed (e.g., product attributes, user preferences).
*   **Extensibility:** Supports a vast ecosystem of extensions (e.g., PostGIS for geospatial data, TimescaleDB for time-series data, PL/pgSQL for stored procedures) allowing customization for specific needs, though immediate complex extensions are not planned.
*   **MVCC (Multi-Version Concurrency Control):** PostgreSQL's implementation of MVCC handles concurrent access effectively, minimizing read/write contention and improving performance in multi-user environments.
*   **Performance Characteristics:** Delivers excellent performance for a wide range of workloads, including complex queries and mixed read/write operations typical in e-commerce.
*   **Strong Community and Ecosystem:** Benefits from a large, active global community, ensuring continuous improvement, ample documentation, and third-party tool support.
*   **Managed Service Availability:** Widely available as a fully managed service from all major cloud providers, simplifying deployment, operations, and scaling.

### 3.3. Specific Suitability for E-commerce Use Cases

*   **`User DB`:** Ideal for storing core user profiles, credentials, addresses, and relational links to orders and other user-specific data, ensuring data integrity.
*   **`Product DB`:** Suitable for managing structured product information, categories, pricing, relationships between products (e.g., variants, bundles), and core transactional inventory data.
*   **`Order DB`:** Effectively handles transactional order data, including line items, customer details, shipping information, order status, and relationships to payments and users.
*   **`Payment DB`:** Securely records financial transactions, ensuring data integrity and consistency for payment processing and reconciliation.

### 3.4. Considerations/Potential Challenges

*   **Horizontal Write Scalability:** Like most traditional RDBMS, scaling writes horizontally (beyond a single primary server) can be complex. This is typically addressed with read replicas for read scaling, and techniques like sharding or application-level partitioning for extreme write loads, which are advanced considerations for future scaling if needed.
*   **Complexity of Advanced Features/Administration:** While powerful, some advanced features and deep administration tasks can have a steeper learning curve if self-managed. This is largely mitigated by using managed PostgreSQL services.

## 4. Alternatives Briefly Re-Considered

As detailed in ADR-004:

*   **MySQL:** A popular open-source RDBMS. While a viable option, PostgreSQL was favored for its historically more comprehensive feature set (especially around advanced data types and extensibility like robust JSONB support), and its strong reputation for data integrity and standards compliance.
*   *(Other SQL options were not considered primary contenders against PostgreSQL and MySQL for this project's needs as per ADR-004.)*

## 5. Implementation & Operational Considerations

*   **Deployment:** For this AWS-centric project, the definitive deployment strategy is to use **Amazon RDS for PostgreSQL**. This aligns with our overarching goal of leveraging AWS managed services ([ADR-006 Cloud Native Deployment Strategy](./../adr/ADR-006-cloud-native-deployment-strategy.md)) to offload operational burdens such as patching, backups, and High Availability. While PostgreSQL is available as a managed service from other cloud providers (e.g., Azure Database for PostgreSQL, Google Cloud SQL), our current focus is on the AWS ecosystem.
    *   **AWS Free Tier:** For initial development and learning, Amazon RDS for PostgreSQL offers instances (e.g., `db.t3.micro` or `db.t4g.micro`) that qualify for the AWS Free Tier, providing a cost-effective way to start.
*   **Schema Management:** Service teams will be responsible for their respective database schemas, utilizing migration tools such as Flyway, Liquibase, or ORM-specific migration capabilities (e.g., TypeORM, Prisma Migrate, Sequelize migrations).
*   **High Availability & Disaster Recovery:** Leverage built-in HA features of managed services, including Multi-AZ deployments for automatic failover and Point-In-Time Recovery (PITR) for DR.
*   **Backup & Restore:** Utilize automated backup solutions provided by managed services, with clearly defined Recovery Point Objectives (RPO) and Recovery Time Objectives (RTO) for each service.
*   **Monitoring & Alerting:** Integrate database performance metrics (query latency, connection counts, disk I/O, CPU/memory utilization, replication lag) into the centralized monitoring and alerting platform ([ADR-011](./../adr/ADR-011-monitoring-and-alerting-strategy.md)).
*   **Security:** Implement robust security measures including strong credentials, principle of least privilege for database users, network security (VPCs, security groups), encryption at rest (provided by managed services), and encryption in transit (SSL/TLS for connections).
*   **Connection Pooling:** Applications will use connection pooling (e.g., PgBouncer if needed, or application-level poolers) to manage database connections efficiently and prevent resource exhaustion.
*   **Recommended PostgreSQL Version:** Utilize a recent, stable, and actively supported major version of PostgreSQL, typically one of the latest versions offered by the chosen managed service provider.

## 6. Consequences of Choosing PostgreSQL

*   **Benefits:**
    *   Strong data integrity and reliability for critical e-commerce transactions.
    *   Mature, feature-rich, and highly performant RDBMS.
    *   Excellent community support and wide availability of tools and expertise.
    *   Flexibility with JSONB for semi-structured data within a relational context.
    *   Reduced operational overhead when using managed services.
*   **Drawbacks/Risks:**
    *   Potential complexity and cost associated with scaling for extremely high write throughput compared to some NoSQL alternatives, requiring careful application design and potentially advanced database techniques in the future. This is a general PostgreSQL consideration, though Amazon Aurora (PostgreSQL-compatible) can offer enhanced performance at a higher cost tier.
    *   Cost of managed services (Amazon RDS) can increase significantly with scale and HA features beyond the Free Tier, requiring careful cost monitoring and optimization.

## 7. Open Issues & Future Considerations

*   Ongoing evaluation of specific PostgreSQL extensions if specialized needs arise (e.g., advanced search, time-series data optimizations).
*   Planning and execution strategy for major PostgreSQL version upgrades in managed environments.
*   Continuous performance tuning and optimization of critical queries as the application evolves and data grows.
*   Developing detailed data archiving and purging strategies for long-term data management.

## 8. References

*   [ADR-004: PostgreSQL for Relational Data](./../adr/ADR-004-postgresql-for-relational-data.md)
*   [ADR-006: Cloud Native Deployment Strategy](./../adr/ADR-006-cloud-native-deployment-strategy.md)
*   [ADR-011: Monitoring and Alerting Strategy](./../adr/ADR-011-monitoring-and-alerting-strategy.md)
*   [C2 Container Diagram (`c2-container-diagram.md`)](./../diagrams/c4/c2%20(Container)/c2-container-diagram.md)
*   [Official PostgreSQL Documentation](https://www.postgresql.org/docs/)
