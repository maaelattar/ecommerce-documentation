# Search Service Foundation and Infrastructure

## Technology Selection

### Primary Search Engine: Elasticsearch

The Search Service is built upon Elasticsearch as its core search technology for the following reasons:

1. **Full-text Search Capabilities**: Provides advanced full-text search with language analyzers, relevance tuning, and query customization.

2. **Scalability**: Supports horizontal scaling through sharding and replication, making it suitable for growing product catalogs.

3. **Performance**: Delivers sub-100ms query response times for most search scenarios, meeting our performance requirements.

4. **Schema Flexibility**: Supports dynamic mapping and schema evolution, allowing for flexible product attributes.

5. **Rich Feature Set**: Offers faceted navigation, autocomplete, spell correction, synonyms, and other e-commerce specific features.

6. **Maturity**: Well-established technology with strong community support and extensive documentation.

7. **AWS Integration**: Available as a managed service (Amazon Elasticsearch Service) for simplified operations.

### Supporting Technologies

1. **NestJS**: Backend framework for building search APIs
   - TypeScript support for type safety
   - Modular architecture for maintainability
   - Well-defined dependency injection

2. **Redis**: For caching frequent search queries
   - Reduces Elasticsearch load
   - Improves response times for common searches
   - Supports time-based cache invalidation

3. **Kafka**: For consuming events from other services
   - Real-time index updates
   - Exactly-once semantics for consistency
   - Replay capabilities for index rebuilding

4. **AWS Infrastructure**:
   - Amazon Elasticsearch Service (or self-managed on EC2)
   - ECS/EKS for service deployment
   - CloudWatch for monitoring
   - S3 for index snapshots

## Architecture Overview

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│   Product     │────▶│    Kafka      │────▶│  Indexing     │
│   Service     │     │    Topics     │     │  Service      │
│               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────┬───────┘
                                                    │
                                                    ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│  Search API   │◀────│    Redis      │◀────│ Elasticsearch │
│  (NestJS)     │     │    Cache      │     │ Cluster       │
│               │     │               │     │               │
└───────┬───────┘     └───────────────┘     └───────────────┘
        │
        ▼
┌───────────────┐
│               │
│    Client     │
│ Applications  │
│               │
└───────────────┘
```

## Elasticsearch Cluster Architecture

### Production Cluster Configuration

The production Elasticsearch cluster consists of:

1. **Master Nodes**: 3 dedicated master nodes for cluster management
   - Instance Type: m5.large (2 vCPU, 8GB RAM)
   - Storage: 50GB gp3 EBS volumes
   - Role: Cluster state management, no data storage

2. **Data Nodes**: 6 data nodes for storing and searching indices
   - Instance Type: r5.xlarge (4 vCPU, 32GB RAM)
   - Storage: 500GB gp3 EBS volumes with 3000 IOPS
   - Role: Store and search indices

3. **Coordinating Nodes**: 4 client nodes for load balancing queries
   - Instance Type: c5.large (2 vCPU, 4GB RAM)
   - Role: Route queries, aggregate results, no data storage

4. **Ingest Nodes**: 2 dedicated ingest nodes for document processing
   - Instance Type: c5.large (2 vCPU, 4GB RAM)
   - Role: Pre-process documents before indexing

### Scaling Strategy

1. **Vertical Scaling**: For increased memory requirements (RAM is critical for search performance)
   - Upgrade instance types as needed

2. **Horizontal Scaling**: For increased storage and query throughput
   - Add data nodes for more storage capacity
   - Add coordinating nodes for higher query throughput

3. **Shard Sizing**:
   - Target shard size: 20-30GB per shard
   - Initial shards: 5 per index
   - Replicas: 1 per shard (2 copies of data total)

4. **Auto-scaling Rules**:
   - Scale out when CPU utilization > 70% for 15 minutes
   - Scale out when JVM heap usage > 75% for 15 minutes
   - Scale out when disk usage > 80%

## Index Lifecycle Management

1. **Hot Phase** (0-7 days):
   - Optimized for indexing and search performance
   - Stored on fastest storage
   - Full replica set

2. **Warm Phase** (7-30 days):
   - Optimized for search performance
   - Reduced replica count
   - Possibly on cheaper storage

3. **Cold Phase** (30-90 days):
   - Optimized for storage efficiency
   - Minimum replica count
   - Force-merged and compressed

4. **Delete Phase** (90+ days):
   - Archived to S3 before deletion (if needed)
   - Deleted from active cluster

## Backup and Recovery Strategy

1. **Snapshot Schedule**:
   - Daily full snapshots to S3
   - Retention: 30 days of daily snapshots

2. **Recovery Procedures**:
   - RTO (Recovery Time Objective): 30 minutes
   - RPO (Recovery Point Objective): 24 hours
   - Automated snapshot restoration playbooks

3. **Disaster Recovery**:
   - Cross-region snapshot replication
   - Standby cluster in secondary region

## Development and Test Environments

1. **Local Development**:
   - Docker Compose setup with single-node Elasticsearch
   - Volume mounts for configuration and data persistence
   - Pre-configured development indices

2. **Testing Environment**:
   - 3-node Elasticsearch cluster (1 master, 2 data nodes)
   - Automated index creation and sample data loading
   - Performance testing tools integration

3. **Staging Environment**:
   - Mirror of production with smaller instance sizes
   - Full integration with other services
   - Production-like data volumes (sampled)

## Configuration Management

Elasticsearch configuration is managed through:

1. **Kubernetes ConfigMaps**:
   - elasticsearch.yml
   - jvm.options
   - log4j2.properties

2. **Index Templates**:
   - Managed through IaC (Infrastructure as Code)
   - Version controlled in GitOps repository

3. **Security Configuration**:
   - Role-based access control
   - TLS configuration
   - Authentication settings

## Initial Setup Steps

1. **Infrastructure Provisioning**:
   ```bash
   terraform apply -var-file=env/production.tfvars
   ```

2. **Cluster Configuration**:
   ```bash
   kubectl apply -f k8s/elasticsearch/
   ```

3. **Index Templates Creation**:
   ```bash
   ./scripts/create-index-templates.sh
   ```

4. **Initial Indexing**:
   ```bash
   kubectl apply -f k8s/initial-indexing-job.yaml
   ```

## Monitoring and Observability

1. **Key Metrics to Monitor**:
   - Query latency (p50, p95, p99)
   - Indexing throughput
   - JVM heap usage
   - CPU and memory utilization
   - Disk I/O
   - Search request rate

2. **Monitoring Tools**:
   - CloudWatch for infrastructure metrics
   - Elasticsearch Metrics API
   - Prometheus for service metrics
   - Grafana for dashboards

3. **Alerting**:
   - PagerDuty integration for critical alerts
   - Slack notifications for non-critical issues
   - Runbooks for common alert scenarios