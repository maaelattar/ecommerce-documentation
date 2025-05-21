# Search Service Application Backup and Disaster Recovery (DR)

## Overview

While the Search Service application (NestJS service) is designed to be largely stateless (with primary state residing in Elasticsearch and Kafka), it's still important to have strategies for backing up its essential configurations and a plan for disaster recovery (DR) to ensure quick restoration of service in case of failures.

This document focuses on the application itself. Backup and DR for Elasticsearch data are covered in `02-elasticsearch-cluster-management.md`, and Kafka data durability is managed by Kafka's own replication and configuration.

## 1. Application State and Statelessness

*   **Stateless Design Goal**: The Search Service application instances (pods/containers) should ideally be stateless. This means that if an instance fails, a new one can be started without any loss of application-specific data within that instance.
    *   User session information (if any specific to search interaction) should be managed externally (e.g., client-side, or a shared session store like Redis if complex session state were needed, though uncommon for search APIs).
    *   In-memory caches within an instance are for performance and can be rebuilt. A distributed cache (like Redis) would have its own backup/DR strategy.
*   **Externalized State**: All critical persistent state is external:
    *   **Search Indexes**: Elasticsearch.
    *   **Event Stream (for recovery/reprocessing)**: Kafka.
    *   **Configurations**: Managed via ConfigMaps, Secrets, or an external Config Service.
    *   **Idempotency Data (Processed Event IDs)**: Should be stored in a persistent store (e.g., Redis, a database, or even a dedicated Elasticsearch index) – this store needs its own backup/DR.

## 2. Configuration Backup

Even if the application is stateless, its operational behavior is defined by its configurations.

*   **Kubernetes Manifests (IaC)**:
    *   `Deployment.yaml`, `Service.yaml`, `ConfigMap.yaml`, `Secret.yaml`, `HorizontalPodAutoscaler.yaml`, etc.
    *   **Strategy**: These YAML files should be stored in a version control system (e.g., Git) as part of Infrastructure as Code (IaC). This is the primary "backup."
    *   Regular backups of the Git repository are essential.
*   **Environment Variables**: If configurations are injected purely via environment variables set by the CI/CD pipeline or orchestrator, the source of these variables (e.g., CI/CD pipeline definitions, Vault, AWS Systems Manager Parameter Store) must be backed up.
*   **External Configuration Service**: If using a service like HashiCorp Consul, Spring Cloud Config Server, or AWS AppConfig, that service needs its own robust backup and DR plan for the configurations it stores.
*   **Secrets Management**: Sensitive data stored in Kubernetes Secrets or external secret managers (like HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) must be securely backed up according to the secret manager's best practices.

## 3. Disaster Recovery (DR) for the Application

Disaster recovery for the Search Service application focuses on restoring its ability to run and serve requests, assuming its dependencies (Elasticsearch, Kafka) are also being recovered or are available.

### DR Scenarios:

*   **Application Pod/Node Failure**: Kubernetes (or other orchestrators) automatically handles this by rescheduling pods to healthy nodes.
*   **Accidental Deletion of Kubernetes Resources**: Restore manifests from Git and re-apply (`kubectl apply -f ...`).
*   **Container Registry Unavailability**: While rare for major cloud providers, having a secondary registry or cached images in the cluster could be an extreme mitigation. More practically, ensure the chosen registry has high availability.
*   **Zone Failure (in a multi-AZ deployment)**: If Kubernetes cluster and dependent services (ES, Kafka) are deployed across multiple Availability Zones, the orchestrator should automatically shift load or reschedule pods to healthy AZs, provided enough capacity exists.
*   **Region Failure (Full DR Site)**:
    *   **Strategy**: Requires a full DR site in a different region with replicated Elasticsearch data (e.g., via CCR or snapshot/restore), replicated Kafka topics (e.g., via MirrorMaker or similar), and the ability to deploy the Search Service application in the DR region.
    *   **Application Deployment in DR Region**: The CI/CD pipeline should be capable of deploying the application (Docker image + configurations) to the DR region.
    *   **DNS Failover**: A global DNS load balancer (e.g., AWS Route 53, Azure Traffic Manager, Google Cloud DNS) would be used to switch traffic to the DR region if the primary region fails.
    *   **Configuration for DR**: Application configurations in the DR region must point to the DR instances of Elasticsearch, Kafka, etc.

### Key DR Elements for the Application:

1.  **Rapid Re-deployment Capability**: The CI/CD pipeline must be able to quickly deploy a working version of the application to any environment (primary or DR).
2.  **Statelessness**: Critical for quick recovery, as no application data needs to be restored to individual instances.
3.  **Infrastructure as Code (IaC)**: Being able to recreate the application's environment (K8s resources) from code is essential.
4.  **Configuration Availability**: Ensure configurations (especially secrets) are accessible for deployment in the DR scenario.
5.  **Dependency Recovery**: The Search Service DR plan is tightly coupled with the DR plans for Elasticsearch and Kafka. The RTO/RPO of the Search Service application itself (excluding data) is usually very low, but overall service RTO depends on its stateful dependencies.

## 4. Backup of Idempotency Data Store

If the Search Service uses a separate persistent store (e.g., Redis) to track processed event IDs for idempotency:

*   **Backup Strategy**: This store must have its own backup mechanism (e.g., Redis RDB snapshots and AOF logs).
*   **Impact of Loss**: Losing this data could lead to reprocessing of some Kafka events upon service restart if their offsets were not yet committed or if the consumer starts from an earlier point. Due to idempotent design in Elasticsearch indexing (using document IDs), reprocessing should not corrupt data but might cause redundant work and temporary inconsistencies if versioning isn't also used to discard older updates.

## 5. Testing DR Plans

*   **Regular Drills**: Periodically test the DR plan by simulating failures (e.g., failover to another AZ, simulate regional failover to the DR site).
*   **Test Application Re-deployment**: Verify that the application can be deployed from scratch using IaC and CI/CD pipelines.
*   **Validate Data Integrity (Post-Recovery)**: After a DR test involving data restoration for ES/Kafka, ensure data consistency as much as possible.

## Conclusion

For the largely stateless Search Service application, the backup strategy centers on version-controlling its deployment configurations (Kubernetes manifests, CI/CD pipeline definitions). The disaster recovery plan relies on the ability to rapidly re-deploy the application using these configurations in a healthy environment, with the overall service recovery time being heavily influenced by the RTO of its stateful dependencies like Elasticsearch and Kafka, and any separate persistent store used for idempotency tracking.
