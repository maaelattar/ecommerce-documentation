# Search Service - Deployment and Operations

## 1. Overview

This document outlines the deployment strategy, operational considerations, monitoring, and maintenance aspects for the Search Service. Given its critical role in user experience and its dependency on a specialized search engine cluster, operational excellence is paramount.

## 2. Deployment Strategy

*   **Application Containerization**: The Search Service application (NestJS) will be packaged as a **Docker container**.
    *   `Dockerfile` specifics: Similar to other Node.js services (base image, dependency installation, code copy, port exposure, run command).
*   **Search Engine Deployment**: The underlying search engine (e.g., OpenSearch, Elasticsearch) will be deployed as a **managed cluster** (e.g., Amazon OpenSearch Service, Elastic Cloud) or a self-managed cluster on Kubernetes.
    *   The choice between managed service vs. self-managed will be determined by an ADR, considering operational overhead, cost, and feature requirements.
*   **Application Orchestration**: The Search Service Docker containers will be deployed on **Kubernetes** (e.g., Amazon EKS).
    *   Standard Kubernetes manifests (`Deployment`, `Service`, `ConfigMap`, `Secret`, `HPA`).
*   **CI/CD Pipeline**: Automated CI/CD (Jenkins, GitLab CI, AWS CodePipeline) for the Search Service application:
    *   Testing, image building, registry push, Kubernetes deployment.

## 3. Infrastructure Requirements

*   **Kubernetes Cluster**: For the Search Service application pods.
*   **Search Engine Cluster**: 
    *   Sufficient nodes (master, data, coordinating if applicable) with adequate CPU, memory, and fast storage (SSD recommended).
    *   Proper network configuration for access from the Search Service application.
*   **Database (Optional)**: A small PostgreSQL instance might be needed for the Search Service itself if it stores complex configurations, detailed A/B test settings, or an outbox for its own operational events. Simpler configurations might live in ConfigMaps or the search engine's own config indexes.
*   **Message Broker**: RabbitMQ (e.g., Amazon MQ) for consuming events for indexing.
*   **Container Registry**: Amazon ECR or similar.
*   **Logging & Monitoring Stack**: Centralized logging, metrics (Prometheus), dashboards/alerts (Grafana/CloudWatch).
*   **Secrets Management**: For API keys (if any needed by the service itself, beyond search engine access which might use IAM roles or VPC security).

## 4. Operational Considerations

### 4.1. Scaling
*   **Application Tier**: Stateless Search Service application pods can be horizontally scaled using Kubernetes HPA based on CPU/memory or custom metrics (e.g., API request rate).
*   **Search Engine Cluster**: 
    *   Scale data nodes based on index size, query load, and indexing throughput.
    *   Scale master/coordinating nodes as needed.
    *   Sharding strategy for indexes is critical for distributing data and load.

### 4.2. High Availability & Resilience
*   **Application Tier**: Multiple replicas of Search Service pods across different Kubernetes nodes/AZs.
*   **Search Engine Cluster**: 
    *   Multi-node cluster with replica shards for data redundancy and failover.
    *   Deployed across multiple AZs.
    *   Regular snapshots/backups of search indexes.
*   **RabbitMQ**: Configured for high availability.
*   Resilient communication with the search engine (retries, timeouts).

### 4.3. Security
*   **Network Security**: Restrict access to the Search Engine Cluster (e.g., VPC security groups, Kubernetes Network Policies).
*   **API Security**: Rate limiting on public search APIs. Authentication/Authorization for admin APIs.
*   **Search Engine Security**: Authentication for accessing the search engine cluster. Encryption at rest and in transit for search engine data.
*   Regular patching of Search Service application, base images, and the search engine itself.

### 4.4. Index Management
*   **Mappings and Settings**: Carefully manage index mappings and settings. Changes often require re-indexing.
*   **Re-indexing**: Strategies for zero-downtime re-indexing using aliases.
    *   Full re-indexing might be needed for major mapping changes or data consistency checks.
    *   Partial re-indexing for specific segments of data.
*   **Index Optimization**: Regularly optimize indexes (e.g., force merge segments in Elasticsearch/OpenSearch) if beneficial for performance, though modern versions handle this better automatically.
*   **Monitoring Index Health**: Shard status, disk space, document counts.

## 5. Monitoring and Alerting

Key metrics for the Search Service and its underlying Search Engine:

*   **Application Health**: Standard pod/container metrics (CPU, memory, restarts), health check status.
*   **API Performance**:
    *   Search API (`/search/products`): Request rate, latency (p50, p90, p99), error rates (4xx, 5xx).
    *   Suggest API (`/search/suggest`): Request rate, latency, error rates.
*   **Search Relevance / User Experience (Indirect via Analytics)**:
    *   Click-Through Rate (CTR) on search results.
    *   Conversion rate from search.
    *   Zero-result search queries.
    *   Average position of clicked items.
*   **Indexing Performance**: 
    *   Event consumption rate from RabbitMQ queues.
    *   Lag in processing indexing queues.
    *   Indexing throughput (documents/sec) into the search engine.
    *   Indexing error rates.
    *   Time for changes to be reflected in search (index freshness).
*   **Search Engine Cluster Health (Critical)**:
    *   Cluster status (green, yellow, red).
    *   Node health (CPU, memory, disk space, JVM heap usage for Elasticsearch/OpenSearch).
    *   Shard status and allocation.
    *   Search query latency and throughput *at the engine level*.
    *   Indexing latency *at the engine level*.
    *   Cache hit/miss rates (query cache, field data cache).
    *   Pending tasks, queue rejections.
*   **RabbitMQ Queues**: Message depth for queues consumed by the Search Service.

**Alerting**: 
*   Search API latency or error rate thresholds exceeded.
*   Search engine cluster status red or yellow.
*   High disk space usage on search engine data nodes.
*   High JVM heap usage or frequent garbage collection pauses on search engine nodes.
*   Significant lag in indexing queues.
*   Failed health checks for application pods.
*   High rate of zero-result searches.

## 6. Logging

*   **Application Logs**: Structured JSON logging from the NestJS application.
    *   Log each API request (query, filters, sort, pagination).
    *   Log constructed search engine query (sanitized).
    *   Log indexing operations (event received, document transformed, document indexed/updated/deleted).
    *   Include correlation IDs, user IDs (if available), session IDs.
*   **Search Engine Logs**: Logs from the search engine nodes themselves (query logs, slow logs, general logs). These are crucial for deep troubleshooting.
*   Ship all logs to a centralized logging system.

## 7. Maintenance

*   **Search Engine Upgrades**: Plan and carefully execute upgrades to the search engine software. Often requires significant testing.
*   **Application Dependency Updates**: Regular updates for Node.js, NestJS, libraries.
*   **Review and Tune Relevance**: Periodically review search performance and relevance, making adjustments to configurations (weights, synonyms, etc.).
*   **Capacity Planning**: Monitor resource usage and plan for future capacity needs for both the application and the search engine cluster.
