# Glossary & Ubiquitous Language

A comprehensive glossary to ensure clear, consistent communication across business and technical teams. This document defines key business, technical, and domain-specific terms used throughout the platform and its documentation.

---

## 1. Business & Domain Terms

- **Cart Abandonment:** When a customer adds items to their shopping cart but does not complete the purchase. Impacts conversion rates and is a key metric for marketing.
- **Order Lifecycle:** The sequence of states an order passes through (e.g., created, paid, shipped, delivered, returned, refunded, cancelled). Used in analytics and service orchestration.
- **Personalization:** Tailoring user experiences, recommendations, and offers based on user data and behavior. Drives engagement and sales.
- **SKU (Stock Keeping Unit):** Unique identifier for each distinct product and service that can be purchased. Used in inventory and catalog management.
- **Marketplace:** A platform where multiple third-party sellers can list and sell products. Requires onboarding, commission, and settlement processes.
- **Omnichannel:** Integration of multiple sales channels (web, mobile, in-store) for a seamless customer experience.
- **Fulfillment:** The process of receiving, processing, and delivering orders to customers. Includes picking, packing, shipping, and returns.
- **AOV (Average Order Value):** The average amount spent per order. Used in business analytics.
- **Churn Rate:** The percentage of customers who stop using the platform over a given period.
- **LTV (Lifetime Value):** The total revenue expected from a customer over their relationship with the platform.

---

## 2. Technical Terms

- **Microservice:** An independently deployable service focused on a specific business capability, communicating via APIs or events.
- **API Gateway:** Central entry point for managing, securing, and routing API traffic between clients and backend services.
- **Service Mesh:** Infrastructure layer for managing service-to-service communication, security, and observability (e.g., Istio, Linkerd).
- **Event-Driven Architecture (EDA):** System design where services communicate via asynchronous events, often using a message broker.
- **Polyglot Persistence:** Use of multiple database technologies, each chosen for a specific service's needs.
- **CI/CD:** Continuous Integration and Continuous Delivery pipelines for automated build, test, and deployment.
- **SLI (Service Level Indicator):** Quantitative measure of a service’s reliability (e.g., latency, error rate).
- **SLO (Service Level Objective):** Target value or range for an SLI (e.g., 99.9% availability).
- **Error Budget:** The maximum allowable threshold for errors within a given period, balancing reliability and release velocity.
- **Canary Deployment:** Gradually rolling out a new version to a subset of users to reduce risk.
- **Blue-Green Deployment:** Running two production environments to enable zero-downtime releases.
- **SBOM (Software Bill of Materials):** Manifest listing all components, libraries, and dependencies in a software artifact.
- **FinOps:** Cloud financial management practices for optimizing spend and value.
- **Paved Road:** Supported and recommended tools, patterns, and workflows for teams to ensure consistency and quality.
- **Service Discovery:** Mechanism for services to dynamically find and communicate with each other (e.g., DNS, Consul, Kubernetes).
- **Observability:** The ability to measure the internal state of a system by examining its outputs (logs, metrics, traces).
- **Idempotency:** Property of an operation that allows it to be performed multiple times without changing the result beyond the initial application.
- **Saga Pattern:** A sequence of local transactions where each step has a compensating action for distributed data consistency.
- **API Contract:** The formal definition of an API’s endpoints, request/response formats, and behaviors (often OpenAPI spec).

---

## 3. Domain-Driven Design (DDD) & Ubiquitous Language

- **Bounded Context:** A logical boundary within which a particular domain model is defined and applicable. Each microservice typically maps to a bounded context.
- **Aggregate:** A cluster of domain objects that can be treated as a single unit for data changes. Ensures consistency within the boundary.
- **Entity:** An object with a distinct identity that runs through time and different states.
- **Value Object:** An object that describes some characteristic or attribute but has no identity.
- **Domain Event:** An event that signifies something important has happened in the domain (e.g., OrderPlaced, PaymentReceived).
- **Repository:** A mechanism for encapsulating storage, retrieval, and search behavior for aggregates.
- **Ubiquitous Language:** A common language used by both developers and business experts to describe the domain, reflected in code, docs, and conversations.

---

## 4. Example Scenarios

- “The order microservice emits an `OrderShipped` domain event when an order transitions from ‘paid’ to ‘shipped’.”
- “Our SLO for checkout API latency is 300ms at the 99th percentile, as defined in the API contract.”
- “The inventory service uses polyglot persistence: relational DB for stock, NoSQL for event logs.”
- “A saga pattern is used for distributed checkout, with compensating actions for payment or inventory failures.”
- “FinOps reviews are held monthly to identify cost optimization opportunities and tag compliance.”

---

## 5. References & Cross-links

- [Domain-Driven Design Context Map](./ddd-context.md)
- [API Documentation Strategy](./api-documentation-strategy.md)
- [ADR-030: API Design Guidelines](./adr/ADR-030-api-design-guidelines.md)
- [ADR-008: Decentralized Data & Polyglot Persistence](./adr/ADR-008-decentralized-data-polyglot-persistence.md)
- [ADR-022: Resilience & Fault Tolerance Patterns](./adr/ADR-022-resilience-fault-tolerance-patterns.md)
- [ADR-041: Environmental Sustainability and Cost Efficiency](./adr/ADR-041-environmental-sustainability-cost-efficiency.md)

---

## 6. Cloud Native & Ecommerce-Specific Terms

- **Cloud Native:** An approach to building and running applications that fully exploit the advantages of the cloud computing delivery model. Emphasizes scalability, resilience, and automation.
- **Immutable Infrastructure:** Infrastructure that is never modified after deployment. If changes are needed, new infrastructure is provisioned and the old is decommissioned.
- **Infrastructure as Code (IaC):** Managing and provisioning infrastructure through machine-readable definition files (e.g., Terraform, CloudFormation).
- **Service Level Agreement (SLA):** A formal contract that defines the expected level of service between a provider and a customer.
- **Zero Downtime Deployment:** Deployment strategy that ensures users experience no service interruption during releases (e.g., blue-green, canary).
- **Observability Stack:** The set of tools and practices for logging, monitoring, and tracing (e.g., ELK, Prometheus, Grafana, Jaeger).
- **API Rate Limiting:** Restricting the number of API requests a client can make in a given time period to protect services from abuse.
- **PCI DSS:** Payment Card Industry Data Security Standard, a compliance requirement for handling credit card data.
- **GDPR/CCPA:** Data privacy regulations (General Data Protection Regulation, California Consumer Privacy Act) affecting how user data is handled.
- **A/B Testing:** Experimenting with two or more variants of a feature to determine which performs better for users.
- **Feature Flag:** A technique to enable or disable features in production without deploying new code.
- **Idempotency Key:** A unique value sent with API requests to ensure that repeated requests have the same effect as a single request (important for payment APIs).
- **Distributed Transaction:** A transaction that spans multiple services or databases, often coordinated using the Saga pattern.
- **Event Sourcing:** Storing the state of a system as a sequence of events rather than as a current snapshot.
- **CQRS (Command Query Responsibility Segregation):** Separating read and write operations into different models for scalability and clarity.

---

## 7. Best Practices & Patterns (Context7-Inspired)

- **Policy-Based Authorization:** Centralize authorization logic in policy objects rather than scattering checks throughout the codebase (see [example](https://github.com/rolemodel/bestpractices/blob/master/patterns/authorization.md)).
- **Parameter Filtering:** Use policies to filter permitted attributes for updates, not ad-hoc logic in controllers.
- **Environment Configuration:** Use environment variables and configuration files for secrets and environment-specific settings (see [configuration best practices](https://github.com/rolemodel/bestpractices/blob/master/rails/configuration.md)).
- **Release Tagging:** Use semantic versioning and Git tags to track releases (see [git tagging best practices](https://github.com/rolemodel/bestpractices/blob/master/git/tagging-versions.md)).
- **Job Concurrency Control:** Limit concurrent background jobs using job-specific keys to avoid duplicate processing (see [background job best practices](https://github.com/rolemodel/bestpractices/blob/master/rails/background_jobs.md)).
- **Retry & Error Handling:** Use built-in retry and discard mechanisms for background jobs to handle transient and irrecoverable errors gracefully.
- **API Contract Testing:** Ensure API changes are backward compatible and well-documented; use contract tests to validate expectations between services.

---

## 8. Example Glossary Usage in Code & Docs

- "The payment API uses an idempotency key to prevent duplicate charges if a request is retried."
- "Order fulfillment is coordinated using a distributed transaction and the Saga pattern."
- "Feature flags allow us to A/B test new checkout flows without redeploying."
- "All infrastructure changes are managed via IaC and tracked in version control."
- "Policy-based authorization ensures only admins can access the accountant dashboard."

---

## 9. How to Contribute to the Glossary

- Propose new terms or edits via pull request to `architecture/glossary.md`.
- Reference ADRs, RFCs, or external best practices when adding new terms.
- Use clear, concise definitions and provide examples or context where possible.
- Link to related documentation or code for deeper understanding.

---

## 10. DevOps, SRE, and Platform Engineering Terms

- **Continuous Deployment (CD):** Automatically deploying every code change that passes automated tests to production.
- **Infrastructure as Code (IaC):** Managing infrastructure (networks, VMs, load balancers, etc.) using code and automation tools (e.g., Terraform, CloudFormation).
- **Immutable Deployment:** Deploying new versions by replacing infrastructure rather than updating in place, ensuring consistency and rollback safety.
- **Service Level Indicator (SLI):** A quantitative measure of some aspect of the level of service provided (e.g., request latency, error rate).
- **Service Level Objective (SLO):** A target value or range for a service level that is measured by an SLI.
- **Service Level Agreement (SLA):** A formal agreement on the expected level of service between a provider and a customer.
- **Error Budget:** The maximum allowable threshold for errors within a given period, balancing reliability and release velocity.
- **Blameless Postmortem:** A retrospective analysis of an incident focused on learning and improvement, not assigning blame.
- **Runbook:** Step-by-step documentation for routine operations or incident response.
- **Playbook:** A collection of runbooks and procedures for handling specific scenarios (e.g., outages, scaling events).
- **On-call Rotation:** Schedule for engineers to be available to respond to incidents outside normal working hours.
- **Incident Management:** The process of detecting, responding to, and resolving unplanned service disruptions.
- **Change Management:** The process of requesting, reviewing, approving, and implementing changes to production systems.
- **Release Train:** A regular, scheduled release process (e.g., every two weeks) regardless of feature readiness.
- **Blue/Green Deployment:** A deployment strategy that reduces downtime and risk by running two identical production environments.
- **Canary Release:** Gradually rolling out a new version to a small subset of users before a full rollout.
- **Feature Toggle/Flag:** A technique to enable or disable features in production without deploying new code.
- **Observability:** The ability to understand the internal state of a system based on its outputs (logs, metrics, traces).
- **Chaos Engineering:** The discipline of experimenting on a system to build confidence in its ability to withstand turbulent conditions in production.

---

## 11. Security, Compliance, and Privacy Terms

- **Zero Trust:** A security model that assumes no implicit trust and verifies every request as though it originates from an open network.
- **Defense in Depth:** A security strategy that uses multiple layers of defense to protect data and resources.
- **Least Privilege:** Granting users and systems the minimum access necessary to perform their functions.
- **Identity and Access Management (IAM):** Policies and technologies for managing digital identities and controlling access to resources.
- **Multi-Factor Authentication (MFA):** Requiring two or more verification methods to access a system.
- **Encryption at Rest/In Transit:** Protecting data by encrypting it when stored and when transmitted over networks.
- **Vulnerability Scanning:** Automated process of identifying security weaknesses in systems and software.
- **Penetration Testing:** Simulated cyberattack to evaluate the security of a system.
- **Security Information and Event Management (SIEM):** Tools and processes for collecting, analyzing, and acting on security events.
- **GDPR/CCPA:** Regulations governing data privacy and protection for users in the EU (GDPR) and California (CCPA).
- **PCI DSS:** Payment Card Industry Data Security Standard, a set of requirements for secure handling of credit card data.
- **SOC 2:** A compliance standard for service organizations, focusing on security, availability, processing integrity, confidentiality, and privacy.
- **Data Masking:** Obscuring specific data within a database to protect it from unauthorized access.
- **Data Residency:** The physical or geographic location where data is stored and processed.
- **Audit Trail:** A record showing who has accessed a system and what operations they have performed.

---

## 12. Advanced Ecommerce & Business Metrics

- **Conversion Rate:** The percentage of users who complete a desired action (e.g., purchase) out of the total visitors.
- **Gross Merchandise Value (GMV):** The total value of merchandise sold over a given period.
- **Net Promoter Score (NPS):** A metric for customer loyalty and satisfaction.
- **Customer Acquisition Cost (CAC):** The cost associated with acquiring a new customer.
- **Customer Retention Rate:** The percentage of customers who continue to use the platform over time.
- **Repeat Purchase Rate:** The percentage of customers who make more than one purchase.
- **Churn Rate:** The percentage of customers who stop using the platform over a given period.
- **Average Revenue Per User (ARPU):** The average revenue generated per user.
- **Basket Size:** The average number of items per order.
- **Refund Rate:** The percentage of orders that are refunded.
- **Cart Conversion Rate:** The percentage of shopping carts that result in a completed purchase.
- **Upsell/Cross-sell:** Techniques to encourage customers to purchase higher-value or additional products.

---

## 13. API, Integration, and Data Terms

- **REST (Representational State Transfer):** An architectural style for designing networked applications using stateless HTTP requests.
- **gRPC:** A high-performance, open-source universal RPC framework using HTTP/2 and Protocol Buffers.
- **Webhooks:** User-defined HTTP callbacks triggered by specific events in a system.
- **API Rate Limiting:** Restricting the number of API requests a client can make in a given time period.
- **API Gateway:** A server that acts as an API front-end, handling requests, authentication, rate limiting, and routing.
- **OpenAPI/Swagger:** A specification for describing RESTful APIs, enabling automated documentation and client generation.
- **GraphQL:** A query language for APIs that allows clients to request exactly the data they need.
- **ETL (Extract, Transform, Load):** The process of moving and transforming data from source systems to a data warehouse.
- **Data Lake:** A centralized repository for storing structured and unstructured data at scale.
- **Data Warehouse:** A system for storing and analyzing structured data from multiple sources.
- **Data Pipeline:** A set of processes for moving and transforming data between systems.
- **Event Streaming:** Real-time processing of data streams (e.g., Kafka, Kinesis).
- **Idempotency Key:** A unique value sent with API requests to ensure that repeated requests have the same effect as a single request.
- **Pagination:** Dividing API responses into discrete pages to limit the amount of data returned in a single request.
- **WebSocket:** A protocol for full-duplex communication channels over a single TCP connection.

---

## 14. Modern Architecture & Deployment Patterns

- **Twelve-Factor App:** A methodology for building SaaS apps that are portable, resilient, and scalable.
- **Sidecar Pattern:** Deploying supporting components (e.g., logging, proxy) alongside the main application container.
- **Ambassador Pattern:** Using a proxy to manage communication between services and external systems.
- **Strangler Fig Pattern:** Incrementally replacing legacy systems by routing some requests to new services.
- **Backend for Frontend (BFF):** Creating separate backend services tailored to the needs of different frontend clients.
- **Service Registry:** A database of available service instances and their locations.
- **Circuit Breaker:** A pattern to detect failures and encapsulate the logic of preventing a failure from constantly recurring.
- **Bulkhead:** Isolating components so that failure in one does not cascade to others.
- **Graceful Degradation:** Designing systems to maintain limited functionality when parts fail.
- **Self-Healing:** Systems that automatically recover from failures without human intervention.
- **Horizontal Scaling:** Adding more instances to handle increased load.
- **Vertical Scaling:** Increasing the resources (CPU, RAM) of a single instance.
- **Multi-Cloud:** Deploying applications across multiple cloud providers for redundancy and flexibility.
- **Hybrid Cloud:** Combining on-premises infrastructure with public or private cloud resources.

---

For additional terms, see the [internal onboarding guide](../README.md) and service-specific documentation.
