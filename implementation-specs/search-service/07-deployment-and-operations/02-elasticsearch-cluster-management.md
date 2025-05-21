# Elasticsearch Cluster Management

## Overview

Effective management of the Elasticsearch cluster is paramount for the performance, reliability, and scalability of the Search Service. This document covers key aspects of deploying, configuring, and maintaining an Elasticsearch cluster tailored for search workloads.

## Deployment Options

1.  **Managed Services (Recommended for most use cases)**:
    *   **AWS OpenSearch Service (formerly Amazon Elasticsearch Service)**: Offers managed Elasticsearch and OpenSearch clusters, handling many operational burdens like patching, backups, monitoring, and scaling.
    *   **Elastic Cloud (by Elastic, the creators of Elasticsearch)**: Provides managed Elasticsearch clusters on various cloud platforms (AWS, GCP, Azure) with features like an official Kibana, APM, and other Elastic Stack components.
    *   **Other Cloud Provider Offerings**: Some cloud providers offer their own managed Elasticsearch or OpenSearch compatible services.
    *   **Pros**: Reduced operational overhead, built-in high availability and durability, easier scaling, expert support.
    *   **Cons**: Potentially higher cost than self-managed (though TCO can be lower), sometimes a slight delay in getting the absolute latest Elasticsearch versions or features, less control over underlying infrastructure specifics.

2.  **Self-Managed on Virtual Machines (e.g., EC2, Azure VMs, GCP Compute Engine)**:
    *   Manually install and configure Elasticsearch on a cluster of VMs.
    *   **Pros**: Full control over configuration and infrastructure, potentially lower direct infrastructure costs if managed efficiently.
    *   **Cons**: Significant operational burden (provisioning, installation, configuration, patching, upgrades, monitoring, backups, security hardening, scaling), requires deep Elasticsearch expertise.

3.  **Self-Managed on Kubernetes (e.g., using ECK - Elastic Cloud on Kubernetes)**:
    *   Deploy and manage Elasticsearch clusters within a Kubernetes environment using operators like ECK (from Elastic) or other community Helm charts.
    *   **Pros**: Leverages Kubernetes orchestration capabilities for deployment and some aspects of management, more control than managed services.
    *   **Cons**: Still requires significant Elasticsearch operational knowledge, managing stateful sets on Kubernetes has its own complexities (storage, networking).

**Recommendation**: For most teams, a **managed Elasticsearch/OpenSearch service** is highly recommended to offload operational complexity and focus on application development.

## Cluster Sizing and Topology

*   **Node Roles**: Understand different node roles in Elasticsearch (master, data, ingest, coordinating-only, ml).
    *   **Dedicated Master Nodes**: Crucial for cluster stability in production. At least 3 dedicated master-eligible nodes are recommended.
    *   **Data Nodes**: Store indexed data and handle search/aggregation queries. Sizing (CPU, RAM, disk) depends on data volume, indexing rate, and query complexity.
    *   **Ingest Nodes (Optional)**: Can pre-process documents before indexing if using Elasticsearch ingest pipelines.
    *   **Coordinating-Only Nodes (Optional)**: Can handle incoming search requests, distribute them to data nodes, and gather results. Useful for offloading coordinating work from data or master nodes in very large clusters.
*   **Sizing Considerations**:
    *   **Data Volume**: Total size of indexed data (source data size * replication factor * indexing overhead).
    *   **Indexing Rate**: How many documents per second need to be indexed.
    *   **Query Volume & Complexity**: Number of search queries per second and their complexity (heavy aggregations, complex filters).
    *   **RAM**: Elasticsearch heavily uses RAM for heap (for cluster management and query processing) and off-heap for file system cache (for I/O performance). A common rule of thumb is to allocate no more than 50% of a node's RAM to the Elasticsearch heap (max ~30-31GB heap per node).
    *   **CPU**: Sufficient cores for indexing and search query processing.
    *   **Disk**: Fast SSDs (e.g., NVMe) are essential for good performance. Ensure enough disk space with room for growth.
*   **Sharding Strategy**:
    *   **Primary Shards**: Data is distributed across primary shards. The number of primary shards is fixed after index creation (unless re-indexed).
    *   **Replica Shards**: Copies of primary shards, providing data redundancy (high availability) and increased read throughput.
    *   **Sizing Shards**: Aim for shard sizes typically between 10GB and 50GB for optimal performance, but this can vary. Too many small shards can be inefficient; too few large shards can be slow and hard to manage/relocate.
    *   Plan the number of primary shards based on expected total data volume and desired shard size. It's better to over-allocate slightly than under-allocate for primary shards if unsure, as changing it requires re-indexing.
*   **Replication**: At least 1 replica shard (total 2 copies of data) is recommended for production for HA. More replicas can improve read scaling but increase storage costs.
*   **Zone Awareness (for HA)**: If deploying across multiple availability zones (AZs) in a cloud environment, configure Elasticsearch shard allocation awareness to distribute primary and replica shards across different AZs to tolerate AZ failures.

## Index and Mapping Management

*   **Index Templates**: Use index templates to automatically apply predefined settings (number of shards, replicas, analyzers) and mappings to new indexes matching a pattern.
*   **Dynamic Mapping vs. Explicit Mapping**: While Elasticsearch can dynamically create mappings, it's best practice to define explicit mappings for production indexes to ensure correct data types, analyzers, and indexing options.
*   **Analyzers**: Configure appropriate text analyzers (standard, language-specific, custom) for different fields to optimize search relevance.
*   Refer to `../02-data-model-and-indexing/` for details on search service specific mappings and analysis.

## Backups and Disaster Recovery (DR)

*   **Snapshots**: Regularly take snapshots of the Elasticsearch cluster using the Snapshot API.
    *   Store snapshots in a remote, durable repository (e.g., AWS S3, Azure Blob Storage, Google Cloud Storage, HDFS).
    *   Define a snapshot lifecycle management (SLM) policy to automate snapshot creation, retention, and deletion.
*   **Restore**: Test the snapshot restore process regularly.
*   **Cross-Cluster Replication (CCR)**: For more advanced DR scenarios or maintaining a hot/warm standby cluster, CCR can replicate indexes from one cluster to another.
*   **RPO/RTO**: Define Recovery Point Objective (RPO) and Recovery Time Objective (RTO) for Elasticsearch data and ensure backup/DR strategy meets them.

## Upgrades and Maintenance

*   **Version Compatibility**: Ensure Search Service application (Elasticsearch client library) is compatible with the Elasticsearch cluster version.
*   **Upgrade Process**: Follow Elasticsearch documentation for rolling upgrades to minimize downtime.
    *   Upgrade master nodes first, then data nodes.
    *   Test upgrades in a staging environment before applying to production.
*   **Patching**: Keep the underlying OS and Elasticsearch itself patched for security vulnerabilities.
*   **Managed services often handle much of this automatically.**

## Security

*   **Network Security**: Run Elasticsearch in a private network. Use security groups/firewalls to restrict access to necessary ports (e.g., 9200, 9300) only from authorized sources (Search Service instances, Kibana, admin hosts).
*   **Authentication**: Enable Elasticsearch security features. Require authentication for all API calls.
    *   Native realm (username/password), LDAP, SAML, PKI, API Keys.
*   **Authorization (RBAC)**: Use Role-Based Access Control to grant users and applications (like the Search Service) only the minimum necessary privileges on specific indexes or cluster operations.
*   **Encryption in Transit**: Enable TLS/SSL for all communication to and within the Elasticsearch cluster (HTTP and transport layers).
*   **Encryption at Rest**: Encrypt data on disk (often handled by underlying storage infrastructure or KMS integration).
*   **Audit Logging**: Enable audit logs in Elasticsearch to track access, queries, and administrative actions.

## Monitoring and Alerting (Elasticsearch Specific)

(Covered more broadly in `04-operational-monitoring-alerting.md`, but key ES metrics include)
*   **Cluster Health**: Green, Yellow, Red. Yellow indicates unassigned replica shards. Red indicates unassigned primary shards (data loss risk!).
*   **Node Metrics**: CPU, RAM (heap usage, JVM pressure), disk space, I/O, network traffic.
*   **Indexing Performance**: Indexing rate, latency, bulk rejections.
*   **Search Performance**: Query rate, latency, cache hit rates.
*   **Shard Status**: Unassigned shards, relocating shards.
*   **JVM Health**: Garbage collection frequency and duration.
*   **Tools**: Kibana (for Elastic Stack), Prometheus with Elasticsearch exporter, Grafana, Datadog, etc.

Effective Elasticsearch cluster management is a continuous process requiring expertise and proactive monitoring. Using managed services can significantly simplify these operational complexities.
