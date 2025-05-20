# Data Storage and Management Specification

## 1. Introduction

This document specifies the data storage and management infrastructure for the e-commerce platform. It defines the database systems, object storage, caching layers, and data lifecycle management strategies for the platform's various data needs. The specification aligns with our AWS-centric architecture and ensures scalability, reliability, and performance across all environments.

## 2. Database Architecture

### 2.1. Database Systems Overview

| Data Category  | Primary Database          | Secondary/Analytics                 | Use Cases                          |
| -------------- | ------------------------- | ----------------------------------- | ---------------------------------- |
| Transactional  | Amazon RDS PostgreSQL     | Amazon RDS PostgreSQL Read Replicas | Orders, Inventory, Users, Products |
| Document-based | Amazon DynamoDB           | DynamoDB Streams to S3/Redshift     | Product Catalogs, User Preferences |
| Search         | Amazon OpenSearch Service | -                                   | Product Search, Full-text Search   |
| Analytics      | Amazon Redshift           | -                                   | Business Intelligence, Reporting   |
| Time Series    | Amazon Timestream         | -                                   | Metrics, Monitoring Data           |

### 2.2. Database Distribution Strategy

- **Service Ownership**: Each microservice owns its data and exposes it via APIs
- **Data Isolation**: Separate database instances for production, staging, and development
- **Cross-service Access**: Controlled through service APIs, no direct cross-service database access

## 3. Relational Database Configuration (Amazon RDS)

### 3.1. PostgreSQL Instances

#### 3.1.1. Production Environment

| Parameter            | Value                        |
| -------------------- | ---------------------------- |
| Instance Type        | db.r6g.2xlarge               |
| Multi-AZ             | Yes                          |
| Storage              | 1TB gp3                      |
| Backup Retention     | 35 days                      |
| Encryption           | Yes (AWS KMS)                |
| Read Replicas        | 2 (cross-AZ)                 |
| Performance Insights | Enabled                      |
| Parameter Group      | custom-postgres14-production |

#### 3.1.2. Staging Environment

| Parameter            | Value                     |
| -------------------- | ------------------------- |
| Instance Type        | db.r6g.xlarge             |
| Multi-AZ             | Yes                       |
| Storage              | 500GB gp3                 |
| Backup Retention     | 14 days                   |
| Encryption           | Yes (AWS KMS)             |
| Read Replicas        | 1                         |
| Performance Insights | Enabled                   |
| Parameter Group      | custom-postgres14-staging |

#### 3.1.3. Development Environment

| Parameter            | Value                         |
| -------------------- | ----------------------------- |
| Instance Type        | db.r6g.large                  |
| Multi-AZ             | No                            |
| Storage              | 200GB gp3                     |
| Backup Retention     | 7 days                        |
| Encryption           | Yes (AWS KMS)                 |
| Read Replicas        | 0                             |
| Performance Insights | Enabled                       |
| Parameter Group      | custom-postgres14-development |

### 3.2. Database Security

- **Network Isolation**:

  - Databases in private subnets
  - Security groups limited to application node groups
  - No public access allowed

- **Authentication**:

  - IAM authentication for database access
  - Service-specific database users
  - Credentials managed via AWS Secrets Manager

- **Encryption**:
  - At-rest encryption with KMS
  - TLS for in-transit encryption

### 3.3. High Availability and Disaster Recovery

- **Multi-AZ Deployment** for production and staging
- **Automated Backups** with point-in-time recovery
- **Cross-region Snapshot Copy** for disaster recovery
- **RTO**: < 4 hours for regional failure
- **RPO**: < 5 minutes for production databases

## 4. NoSQL Database Configuration (Amazon DynamoDB)

### 4.1. Table Design

#### 4.1.1. Capacity Mode

- **Production**: On-demand capacity for most tables
- **Staging**: On-demand capacity
- **Development**: Provisioned capacity with auto-scaling

#### 4.1.2. Key Tables

| Table Name      | Primary Key   | Sort Key      | Global Secondary Indexes       | Purpose                       |
| --------------- | ------------- | ------------- | ------------------------------ | ----------------------------- |
| Products        | productId (S) | -             | category-index, brand-index    | Product information           |
| UserPreferences | userId (S)    | -             | -                              | User settings and preferences |
| ProductCatalog  | catalogId (S) | productId (S) | category-index, date-index     | Catalog management            |
| Sessions        | sessionId (S) | -             | userId-index, expiryTime-index | User session management       |

### 4.2. Performance Optimization

- **Partition Key Design**: Even distribution of read/write operations
- **Sparse Indexes**: When only a small subset of items have the indexed attribute
- **TTL Settings**: For temporary data like sessions
- **DAX Caching**: Enabled for frequently read tables
- **Item Size Limit**: Keep items under 4KB when possible

### 4.3. Backup and Recovery

- **Point-in-time Recovery**: Enabled for all production tables
- **On-demand Backups**: Weekly full backups with 90 days retention
- **Cross-region Replication**: For critical tables with global table configuration

## 5. Search Database Configuration (Amazon OpenSearch Service)

### 5.1. Cluster Configuration

#### 5.1.1. Production Environment

| Parameter              | Value                     |
| ---------------------- | ------------------------- |
| Instance Type          | r6g.xlarge.search         |
| Instance Count         | 3 (one per AZ)            |
| Storage                | 500GB gp3 per node        |
| Dedicated Master Nodes | 3 x m6g.large.search      |
| Zone Awareness         | Enabled                   |
| Encryption             | At-rest and in-transit    |
| UltraWarm              | Enabled for older indices |

#### 5.1.2. Staging and Development Environments

| Parameter              | Value                  |
| ---------------------- | ---------------------- |
| Instance Type          | r6g.large.search       |
| Instance Count         | 2                      |
| Storage                | 100GB gp3 per node     |
| Dedicated Master Nodes | None                   |
| Zone Awareness         | Enabled                |
| Encryption             | At-rest and in-transit |
| UltraWarm              | Disabled               |

### 5.2. Index Management

- **Index Naming**: `{service}-{entity}-{YYYY-MM}`
- **Index Rotation**: Monthly rotation for time-series data
- **Index Templates**: Standardized mappings and settings
- **Lifecycle Policies**:
  - Hot tier: Latest 30 days
  - UltraWarm tier: 31-90 days
  - Cold storage: 91-365 days
  - Delete: After 365 days

### 5.3. Search Optimization

- **Custom Analyzers**:
  - Product search with synonyms
  - Multi-language support
  - N-gram tokenizers for partial matching
- **Query Templates**: Standardized query structures for common operations
- **Field Mappings**: Explicit mappings to control indexing behavior

## 6. Object Storage (Amazon S3)

### 6.1. Bucket Strategy

| Bucket Purpose   | Lifecycle Policy                                                        | Versioning | Access Pattern         |
| ---------------- | ----------------------------------------------------------------------- | ---------- | ---------------------- |
| Product Images   | Standard-IA after 30 days, Glacier after 90 days                        | Enabled    | High-read, Low-write   |
| Order Documents  | Standard-IA after 30 days, Glacier after 180 days                       | Enabled    | Medium-read, Low-write |
| Application Logs | Standard-IA after 14 days, Glacier after 30 days, Delete after 365 days | Disabled   | Low-read, High-write   |
| Database Backups | Standard-IA after 7 days, Glacier after 30 days                         | Enabled    | Low-read, Medium-write |
| Static Assets    | None                                                                    | Disabled   | High-read, Low-write   |

### 6.2. Security Configuration

- **Encryption**: SSE-KMS for sensitive data, SSE-S3 for non-sensitive data
- **Bucket Policies**: Least privilege access
- **Public Access**: Blocked at account level except for static assets
- **Object Lock**: Enabled for regulated data with compliance mode

### 6.3. Performance Optimization

- **CloudFront Integration**: For static assets and product images
- **S3 Transfer Acceleration**: For large file uploads
- **S3 Access Points**: For service-specific access patterns
- **Prefix Strategy**: Optimize for high-throughput use cases
- **Request Rate Partitioning**: Hash prefixes for high-volume buckets

## 7. Caching Strategy

### 7.1. Amazon ElastiCache Deployment

#### 7.1.1. Redis Clusters

| Purpose            | Instance Type    | Node Count     | Multi-AZ | Auto-failover |
| ------------------ | ---------------- | -------------- | -------- | ------------- |
| Session Cache      | cache.r6g.large  | 3 (one per AZ) | Yes      | Yes           |
| Product Cache      | cache.r6g.xlarge | 3 (one per AZ) | Yes      | Yes           |
| API Response Cache | cache.r6g.large  | 3 (one per AZ) | Yes      | Yes           |

#### 7.1.2. Parameters and Settings

- **Eviction Policy**: `volatile-lru` (Least Recently Used with expiration)
- **Maxmemory Percentage**: 75%
- **Backup Schedule**: Daily snapshot, 7-day retention
- **Encryption**: At-rest and in-transit

### 7.2. CloudFront Caching

- **TTL Configuration**:
  - Product images: 24 hours
  - Static assets: 7 days
  - API responses: Based on Cache-Control headers
- **Cache Invalidation**:
  - Automated invalidation on product image updates
  - Path-based invalidation for targeted updates

### 7.3. Application-level Caching

- **Local Cache**: In-memory caching for high-frequency references
- **Cache Invalidation**: Event-based invalidation via SNS/SQS
- **Cache Warming**: Proactive caching for predictable high-demand periods

## 8. Data Lifecycle Management

### 8.1. Data Retention Policies

| Data Type     | Active Storage           | Archive Storage | Retention Period   |
| ------------- | ------------------------ | --------------- | ------------------ |
| Order Data    | RDS PostgreSQL           | S3 Glacier      | 7 years            |
| Product Data  | RDS PostgreSQL, DynamoDB | S3 Standard-IA  | Indefinite         |
| User Activity | DynamoDB, OpenSearch     | S3 Glacier      | 2 years            |
| Session Data  | ElastiCache, DynamoDB    | None            | 24 hours - 30 days |
| Audit Logs    | CloudWatch Logs          | S3 Glacier      | 7 years            |

### 8.2. Archiving Strategy

- **Periodic Batch Jobs**: Monthly archiving of historical data
- **Data Transformations**: Format changes for optimized storage
- **Access Methods**: SQL interface for Glacier via Athena when needed
- **Archive Verification**: Quarterly sample restore tests

### 8.3. Data Deletion

- **GDPR Compliance**: Automated user data deletion processes
- **Soft Delete**: Logical deletion with retention period
- **Hard Delete**: Physical removal after retention period
- **Cascade Strategy**: Referenced data handling during deletion

## 9. Data Migration and ETL

### 9.1. AWS Glue ETL Jobs

```hcl
# Terraform example for AWS Glue ETL job
resource "aws_glue_job" "order_analytics_etl" {
  name              = "order-analytics-etl"
  role_arn          = aws_iam_role.glue_service_role.arn
  glue_version      = "3.0"
  worker_type       = "G.1X"
  number_of_workers = 5

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_scripts.bucket}/scripts/order_analytics.py"
    python_version  = "3"
  }

  default_arguments = {
    "--TempDir"                        = "s3://${aws_s3_bucket.glue_temp.bucket}/temp/"
    "--job-bookmark-option"            = "job-bookmark-enable"
    "--enable-metrics"                 = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--SOURCE_DATABASE"                = "orders_db"
    "--SOURCE_TABLE"                   = "orders"
    "--TARGET_BUCKET"                  = aws_s3_bucket.analytics_data.bucket
  }

  execution_property {
    max_concurrent_runs = 2
  }
}
```

### 9.2. Scheduled Data Pipelines

- **Daily Product Data Sync**: RDS to OpenSearch for search functionality
- **Hourly Analytics Update**: Transactional data to Redshift
- **Real-time Event Processing**: DynamoDB Streams to Lambda for event-driven updates

### 9.3. Data Quality Checks

- **Schema Validation**: Before loading to target systems
- **Completeness Checks**: Verification of required data elements
- **Reconciliation**: Counts and checksums between source and target
- **Alerting**: Notification on data quality issues

## 10. Monitoring and Management

### 10.1. Database Monitoring

- **Performance Metrics**:

  - CPU Utilization: Alert at 80% sustained for 5 minutes
  - Storage: Alert at 80% capacity
  - Connection Count: Alert at 80% of maximum connections
  - Replication Lag: Alert at > 30 seconds

- **Query Performance**:
  - Slow Query Logs: Enabled and exported to CloudWatch
  - Performance Insights: Enabled with 7-day retention
  - Query Plan Analysis: Automated plan capture for slow queries

### 10.2. Storage Monitoring

- **S3 Metrics**:
  - Request Rates: Baseline monitoring with anomaly detection
  - 4xx/5xx Errors: Alert on sustained error rates
  - Replication Time: Alert on delays > 15 minutes
- **Capacity Planning**:
  - Growth Projection: Monthly review of storage trends
  - Cost Optimization: Lifecycle policy effectiveness review

### 10.3. Cache Performance

- **Cache Hit Rate**: Alert if below 80% for critical caches
- **Eviction Rate**: Alert on sustained evictions
- **Memory Fragmentation**: Monitor and plan maintenance when required

## 11. Implementation Plan

### 11.1. Phased Rollout

1. **Phase 1: Core Transactional Storage**

   - RDS PostgreSQL setup with read replicas
   - DynamoDB core tables
   - Basic Redis caching

2. **Phase 2: Object Storage and Search**

   - S3 bucket configuration
   - CloudFront integration
   - OpenSearch cluster deployment

3. **Phase 3: Analytics and ETL**

   - Redshift cluster
   - Glue ETL jobs
   - Analytics data pipeline

4. **Phase 4: Advanced Caching and Optimization**

   - Enhanced Redis configurations
   - Advanced CloudFront settings
   - Performance tuning

5. **Phase 5: Lifecycle Management**
   - Archiving automation
   - Compliance validation
   - Disaster recovery testing

### 11.2. Database Migration Process

1. **Schema Design**: Finalize schema with service teams
2. **Initial Load**: Batch load of reference data
3. **Incremental Updates**: Change Data Capture (CDC) for ongoing updates
4. **Validation**: Data comparison between old and new systems
5. **Cutover**: Traffic redirection with fallback option

### 11.3. Terraform Examples

```hcl
# RDS PostgreSQL instance
resource "aws_db_instance" "product_db" {
  identifier             = "product-db-${var.environment}"
  allocated_storage      = var.environment == "production" ? 1000 : 200
  storage_type           = "gp3"
  engine                 = "postgres"
  engine_version         = "14.5"
  instance_class         = var.environment == "production" ? "db.r6g.2xlarge" : "db.r6g.large"
  db_name                = "product_service"
  username               = "admin"
  password               = data.aws_secretsmanager_secret_version.db_password.secret_string
  parameter_group_name   = aws_db_parameter_group.postgres14_custom.name
  backup_retention_period = var.environment == "production" ? 35 : 7
  multi_az               = var.environment == "production" ? true : false
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.db_encryption.arn
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.private.name
  skip_final_snapshot    = var.environment != "production"
  deletion_protection    = var.environment == "production"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  lifecycle {
    prevent_destroy = var.environment == "production"
  }

  tags = {
    Name        = "product-db-${var.environment}"
    Environment = var.environment
    Service     = "product-service"
  }
}

# DynamoDB table
resource "aws_dynamodb_table" "product_catalog" {
  name           = "ProductCatalog-${var.environment}"
  billing_mode   = var.environment == "production" ? "PAY_PER_REQUEST" : "PROVISIONED"
  read_capacity  = var.environment != "production" ? 5 : null
  write_capacity = var.environment != "production" ? 5 : null
  hash_key       = "catalogId"
  range_key      = "productId"

  attribute {
    name = "catalogId"
    type = "S"
  }

  attribute {
    name = "productId"
    type = "S"
  }

  attribute {
    name = "category"
    type = "S"
  }

  attribute {
    name = "createDate"
    type = "S"
  }

  global_secondary_index {
    name               = "category-index"
    hash_key           = "category"
    range_key          = "createDate"
    projection_type    = "ALL"
    read_capacity      = var.environment != "production" ? 5 : null
    write_capacity     = var.environment != "production" ? 5 : null
  }

  point_in_time_recovery {
    enabled = var.environment == "production"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "product-catalog-${var.environment}"
    Environment = var.environment
    Service     = "product-service"
  }
}
```

## 12. References

- [Amazon RDS Documentation](https://docs.aws.amazon.com/rds/)
- [Amazon DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Amazon S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Amazon ElastiCache Documentation](https://docs.aws.amazon.com/elasticache/)
- [Amazon OpenSearch Service Documentation](https://docs.aws.amazon.com/opensearch-service/)
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Main_Page)
- [Redis Best Practices](https://redis.io/topics/best-practices)
- [Database Migration Guide](https://docs.aws.amazon.com/dms/latest/userguide/Welcome.html)
- [ADR-004-data-persistence-strategy](../../architecture/adr/ADR-004-data-persistence-strategy.md)
- [ADR-005-search-implementation-approach](../../architecture/adr/ADR-005-search-implementation-approach.md)
