# 02: Infrastructure Requirements

This document outlines the infrastructure components and their configurations necessary to support the User Service in a production environment. These requirements are based on the expectation of a scalable, resilient, and secure service.

## 1. Compute Resources (Kubernetes Nodes)

*   **Instance Types**: General-purpose instances (e.g., AWS m5/m6g series, GCP n2/e2 series, Azure Dsv3/DSv4 series) are suitable. The choice may depend on specific cloud provider preferences and cost-performance analysis.
*   **CPU & Memory**: Initial sizing per User Service pod might be conservative (e.g., 0.5 vCPU, 512MiB RAM), with Horizontal Pod Autoscaler (HPA) configured to scale based on actual load. Node capacity should accommodate multiple service replicas and other cluster components.
*   **Operating System**: Standard Linux distributions used by the Kubernetes provider (e.g., Amazon Linux 2 for EKS, Ubuntu for GKE/AKS).
*   **Node Pools**: Consider separate node pools for critical stateful workloads (like databases if self-managed, though a managed service is preferred) versus stateless application workloads like the User Service.

## 2. Database (PostgreSQL)

*   **Service Type**: Managed PostgreSQL service is highly recommended (e.g., AWS RDS for PostgreSQL, Google Cloud SQL for PostgreSQL, Azure Database for PostgreSQL).
    *   **Benefits**: Automated backups, patching, point-in-time recovery, read replicas, high availability configurations.
*   **Sizing**: Initial sizing depends on the estimated number of users, profiles, and related data. Start with a moderately sized instance (e.g., `db.t3.medium` or `db.m5.large` on AWS) and monitor performance to scale up or down as needed.
*   **Replication**: At least one read replica in a different availability zone (AZ) for high availability and offloading read traffic if necessary.
*   **Backups**: Daily automated backups with a retention period of at least 7-30 days. Point-in-time recovery enabled.
*   **Connectivity**: Secure connectivity from the User Service pods (running in Kubernetes) to the database, typically via private networking (VPC peering, private endpoints). Network policies in Kubernetes should restrict access to the database only from User Service pods.
*   **Version**: A recent, stable major version of PostgreSQL (e.g., PostgreSQL 14, 15, or 16 at the time of writing).

## 3. Message Broker (Apache Kafka)

*   **Service Type**: Managed Kafka service is recommended (e.g., Amazon MSK, Confluent Cloud, Aiven for Apache Kafka).
    *   **Benefits**: Simplifies cluster management, scaling, and maintenance.
*   **Cluster Setup**:
    *   **Brokers**: Minimum of 3 brokers spread across multiple Availability Zones for high availability.
    *   **Topics**: The `user.events` topic (and potentially others if granular topics are decided for different event categories, though a single primary topic is simpler to manage initially).
    *   **Partitions**: Start with a reasonable number of partitions (e.g., 3-6) for the `user.events` topic. The number of partitions determines the maximum parallelism for consumers. This can be increased later, but not decreased easily.
    *   **Replication Factor**: A replication factor of 3 for all topics to ensure data durability and availability across AZs.
*   **Retention Policy**: Define an appropriate retention period for events (e.g., 7 days for general events, longer for audit-critical events if not offloaded elsewhere). Consider storage implications.
*   **Connectivity**: Secure connectivity from User Service pods and consumer services to the Kafka cluster. TLS encryption for data in transit. Authentication and authorization mechanisms (e.g., SASL/SCRAM, mTLS).

## 4. Networking

*   **Virtual Private Cloud (VPC)**: The entire application infrastructure, including Kubernetes cluster, database, and Kafka, should reside within a dedicated VPC.
*   **Subnets**: Multiple subnets across different Availability Zones for high availability.
    *   Private subnets for Kubernetes worker nodes, database, and Kafka brokers.
    *   Public subnets (optional, if needed) for internet-facing load balancers or NAT gateways.
*   **Load Balancers**: Application Load Balancers (ALBs) or equivalent to distribute traffic to User Service instances (via Kubernetes Ingress or Service type LoadBalancer).
*   **Firewalls/Security Groups/Network Policies**:
    *   Strict ingress/egress rules to control traffic flow between components.
    *   Kubernetes Network Policies to control pod-to-pod communication.
    *   Security Groups (AWS) or equivalent for fine-grained control at the instance/service level.
*   **DNS**: Internal DNS for service discovery within the Kubernetes cluster. Public DNS for externally accessible endpoints.

## 5. Secrets Management

*   **Technology**: A dedicated secrets management solution is crucial.
    *   **Options**: HashiCorp Vault, AWS Secrets Manager, Google Cloud Secret Manager, Azure Key Vault.
    *   Kubernetes Secrets can be used, but for enhanced security and auditability, integration with an external secrets manager is preferred, often via a CSI driver or sidecar injector.
*   **Secrets to Manage**: Database credentials, API keys for external services (e.g., HIBP, CAPTCHA, social login providers), Kafka credentials, JWT signing keys, internal service-to-service authentication tokens.
*   **Access Control**: Strict access controls and audit logs for all secrets.
*   **Rotation**: Policies and mechanisms for regular rotation of sensitive credentials, especially database passwords and API keys.

By carefully planning and provisioning these infrastructure components, the User Service can be deployed in a manner that is secure, scalable, and highly available, meeting the demands of a modern e-commerce platform.
