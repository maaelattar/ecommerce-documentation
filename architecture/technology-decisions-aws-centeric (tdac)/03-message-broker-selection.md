# Message Broker Selection Decision

Date: 2025-05-12
Status: Accepted

## Context

Our Event-Driven Architecture (EDA), as defined in ADR-002, requires a robust message broker to facilitate asynchronous communication between microservices. ADR-018 (Message Broker Detailed Strategy and Selection) explored various options and proposed a primary and secondary choice. This document finalizes the selection and outlines the implementation approach for the primary broker using AWS managed services.

## Decision

We have selected **RabbitMQ**, implemented via **Amazon MQ for RabbitMQ**, as the primary message broker for the E-commerce Platform. **Apache Kafka**, likely via **Amazon Managed Streaming for Kafka (MSK)** or self-managed on EKS if specific needs arise, will be adopted for specific use cases demanding extremely high throughput or advanced event stream processing capabilities if RabbitMQ proves insufficient for those specialized needs.

## Rationale

**RabbitMQ (via Amazon MQ)** is chosen as the primary broker for the following reasons, aligning with ADR-018's choice of RabbitMQ technology:

1.  **Feature Set & Flexibility:** RabbitMQ offers a mature and comprehensive set of features, including flexible routing (exchanges, queues, bindings), message acknowledgments, persistence, and various message patterns (pub/sub, work queues) suitable for a wide range of microservice communication needs. Amazon MQ supports these core RabbitMQ features.
2.  **Developer Experience:** RabbitMQ has strong client library support for Node.js (our primary backend language per ADR-003), making integration straightforward. The AMQP protocol is well-documented and understood.
3.  **Operational Manageability (via Amazon MQ):** Using Amazon MQ for RabbitMQ significantly reduces operational overhead. AWS handles provisioning, patching, maintenance, backups, and provides built-in high availability options. This aligns with our preference for using managed services where appropriate to free up engineering resources.
4.  **Community & Maturity:** RabbitMQ is a widely adopted, mature open-source project. Leveraging it through Amazon MQ still benefits from this ecosystem knowledge while offloading direct management.
5.  **Balance for General EDA Needs:** For the majority of our anticipated event-driven scenarios (e.g., `OrderCreated`, `UserRegistered`, asynchronous task offloading), RabbitMQ provides a good balance of performance, features, and operational ease when deployed via Amazon MQ.
6.  **AWS Integration:** Amazon MQ integrates with other AWS services like CloudWatch for monitoring, IAM for access control, and VPC for network security.

**Apache Kafka (via Amazon MSK or self-managed)** is designated as a specialized, secondary solution because:

1.  **High-Throughput Streaming:** Kafka excels in scenarios requiring the ingestion and processing of massive volumes of events (e.g., analytics data, real-time logging streams).
2.  **Stream Processing Capabilities:** Its ecosystem (Kafka Streams, ksqlDB, Flink) provides powerful tools for complex event processing and stream analytics, which may be beneficial for future advanced features.
3.  **Operational Complexity:** A full Kafka deployment is generally more operationally complex. Using Amazon MSK mitigates some of this, but it's still typically reserved for use cases where RabbitMQ's capabilities are insufficient.

## Implementation Details (RabbitMQ via Amazon MQ - Primary)

### 1. Broker Configuration

*   **Deployment Mode:** Cluster Deployment (e.g., 3-node cluster across multiple Availability Zones for High Availability).
*   **Broker Instance Type:** Start with a general-purpose instance type (e.g., `mq.m5.large` or `mq.m5.xlarge`) and monitor performance (CPU, memory, network) to scale up or down as needed. Consider burstable instances (e.g., `mq.t3.medium`) for dev/test environments.
*   **Storage Type:** Amazon EBS, typically General Purpose SSD (gp2/gp3). Ensure sufficient IOPS for persistent messages.
*   **RabbitMQ Version:** Select a recent, stable version supported by Amazon MQ.
*   **Virtual Hosts (Vhosts):** Utilize vhosts to create logical separation for different applications or environments within the same broker cluster if needed (e.g., `ecommerce_prod_vhost`, `inventory_events_vhost`). Default vhost `/` can be used for simpler setups.

### 2. Network Configuration

*   **VPC:** Deploy brokers within the application's private VPC.
*   **Subnets:** Select private subnets across multiple Availability Zones (matching the cluster deployment) for HA.
*   **Security Group:** Configure a dedicated security group for Amazon MQ brokers. Restrict ingress AMQP(S) (5671/5672) and HTTPS (management console, 15671/15672) ports to only allow traffic from application servers/services within the VPC (typically from the security groups of your services running on EKS or EC2).
*   **Public Accessibility:** Set to `false`. Access should be from within the VPC.
*   **Endpoints:** Use the provided Amazon MQ broker endpoints for client connections. For clustered brokers, clients connect to a network load balancer endpoint provided by Amazon MQ.

### 3. Security

*   **IAM for Management:** Use IAM roles and policies to control access to manage Amazon MQ brokers (create, delete, modify).
*   **RabbitMQ User Authentication:** Create RabbitMQ users with strong passwords. Grant permissions (configure, write, read) to these users on specific vhosts and resources (exchanges, queues).
*   **Encryption In-Transit:** Enforce TLS for AMQP connections (AMQPS, port 5671). Amazon MQ brokers typically have TLS enabled by default.
*   **Encryption At-Rest:** Data stored on EBS volumes by Amazon MQ is encrypted by default using AWS managed keys (SSE-EBS). Customer Managed Keys (CMK) can also be configured if required.
*   **Audit Logging:** Configure audit logging to CloudWatch Logs for management API calls if needed for compliance.

### 4. Logging & Monitoring

*   **Amazon MQ Logs:** Configure Amazon MQ to send general logs and audit logs (if enabled) to Amazon CloudWatch Logs for analysis and retention.
*   **Amazon CloudWatch Metrics:** Amazon MQ automatically sends metrics to CloudWatch (e.g., `CPUUtilization`, `MemoryUsage`, `NetworkOut`, `MessageCount`, `MessagesEnqueued`, `MessagesDequeued`, `ConnectionCount`, `ChannelCount`, queue-specific metrics).
*   **Alerting:** Set up CloudWatch Alarms based on key metrics:
    *   High CPU/Memory utilization.
    *   Low `MessageCount` for critical queues (potential processing issues).
    *   Rapidly growing `MessageCount` (consumers falling behind).
    *   High number of unacknowledged messages.
    *   Broker health status.
*   Integrate with the central monitoring solution (Amazon Managed Grafana) by adding CloudWatch as a data source to visualize these metrics.

### 5. Maintenance

*   **AWS Managed Maintenance:** Amazon MQ handles patching and minor version upgrades for RabbitMQ during configured maintenance windows.
*   **Application-Side Maintenance:** Plan for application behavior during broker restarts (e.g., client reconnection logic, handling temporary unavailability).

### 6. Backup & High Availability

*   **High Availability:** Achieved by using a cluster deployment (multiple nodes across AZs). Amazon MQ manages failover between nodes.
*   **Backups:** Amazon MQ automatically takes daily snapshots for disaster recovery purposes. These are managed by AWS.

### 7. Key Client Considerations (e.g., for Node.js services)

*   **Client Library:** Use a robust AMQP client library like `amqplib` for Node.js.
*   **Connection Management:** Implement resilient connection and channel management, including automatic reconnection logic with exponential backoff in case of broker unavailability or network issues.
*   **Endpoints:** Connect to the AMQPS endpoint provided by Amazon MQ.
*   **TLS/SSL:** Ensure clients are configured to use TLS.
*   **Publisher Confirms & Consumer Acknowledgements:** Utilize publisher confirms to ensure messages are durably written to the broker and consumer acknowledgements to ensure messages are processed successfully before being removed from queues.
*   **Dead Letter Exchanges (DLX):** Configure DLXs to handle messages that cannot be processed successfully after multiple retries, allowing for later inspection and re-processing if necessary.
*   **Queue & Exchange Declaration:** Applications should declare required queues, exchanges, and bindings idempotently on startup if they don't exist, or rely on pre-provisioned infrastructure.
*   **Error Handling:** Implement robust error handling for connection issues, publishing failures, and processing errors.

## Implementation Details (Kafka - Secondary, if needed)

*(This section will be filled out if/when a specific use case arises that necessitates Kafka. It will likely detail using Amazon MSK.)*

*   **Deployment:** (e.g., Amazon MSK)
*   **Configuration:** (Topics, Partitions, Replication Factor, Security)
*   **Monitoring:** (Key Kafka metrics via CloudWatch for MSK)

## Next Steps

*   Provision Amazon MQ for RabbitMQ brokers in development/staging environments.
*   Develop standardized patterns and libraries for microservices to interact with RabbitMQ.
*   Define standard queue/exchange naming conventions.
*   Implement monitoring dashboards and alerts.

---
**Original ADR-018 Details (for reference):**

*   **Proposed Options:** RabbitMQ, Apache Kafka, Redis Streams, NATS.
*   **Evaluation Criteria:** Performance, Scalability, Reliability, Data Persistence, Ease of Use, Community Support, Operational Overhead, Cost, Feature Set.
*   **RabbitMQ Pros:** Mature, feature-rich, flexible routing, good for general-purpose messaging.
*   **Kafka Pros:** High-throughput, excellent for event streaming and log aggregation, durable.
*   **Decision for ADR-018:** RabbitMQ as primary, Kafka as secondary for specialized use cases.

## Alternatives Considered (Summary from ADR-018)

*   **Redis Streams:** Considered too lightweight and less feature-rich for a platform-wide broker.
*   **Managed Cloud Services (AWS SQS/SNS, Google Pub/Sub):** Viable but RabbitMQ (via Amazon MQ) was chosen for its richer feature set and protocol flexibility (AMQP) while still leveraging managed benefits. Kafka (via MSK) is secondary for high-throughput needs.

## Dependencies

*   **Infrastructure Team:** Provisioning and configuration of Amazon MQ resources via IaC.
*   **Development Teams:** Adopting RabbitMQ client libraries and EDA patterns for Amazon MQ.
*   **Observability Team:** Ensuring proper monitoring and alerting setup for Amazon MQ via CloudWatch.

## Action Items

1.  Finalize and deploy the Infrastructure as Code (IaC) for provisioning Amazon MQ brokers.
2.  Develop standardized NestJS modules/libraries for RabbitMQ integration (producer/consumer patterns) targeting Amazon MQ endpoints.
3.  Document best practices for exchange/queue design and error handling for development teams.
4.  Establish monitoring dashboards and alerts for RabbitMQ.
5.  Conduct training sessions on event-driven patterns with RabbitMQ.

## References

*   [ADR-002: Adoption of Event-Driven Architecture](./../adr/ADR-002-adoption-of-event-driven-architecture.md)
*   [ADR-018: Message Broker Detailed Strategy and Selection](./../adr/ADR-018-message-broker-strategy.md)
*   [Amazon MQ for RabbitMQ Documentation](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/rabbitmq.html)
*   [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
