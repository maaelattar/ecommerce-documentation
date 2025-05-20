# Database Selection and Configuration for Product Service

## Overview

This document details the database selection, configuration, and implementation approach for the Product Service. The decisions align with our architectural principles documented in [ADR-004: PostgreSQL for Relational Data](../../../architecture/adr/ADR-004-postgresql-for-relational-data.md) and [ADR-020: Database-per-Service](../../../architecture/adr/ADR-020-data-management-database-per-service.md).

## Database Technology Selection

### Primary Database: PostgreSQL via Amazon RDS

**Selection Justification**:
- **Structured Data**: Product data has well-defined schemas and relationships that benefit from a relational model
- **Transaction Support**: ACID properties required for product updates, pricing changes, and inventory adjustments
- **Query Capabilities**: Need for complex queries across product attributes
- **Team Expertise**: Development team has strong PostgreSQL experience
- **Operational Excellence**: Amazon RDS reduces operational overhead while providing high availability

### Supplementary Storage (Future Considerations)

For specific use cases, we may integrate additional storage technologies:
- **Amazon DynamoDB**: For flexible product attributes or high-read scenarios
- **Amazon OpenSearch Service**: For advanced product search capabilities
- **Amazon ElastiCache (Redis)**: For caching frequently accessed product data

## Amazon RDS Configuration

### Instance Configuration

**Production Environment**:
- **Instance Type**: db.r6g.large (initially)
  - 2 vCPUs, 16 GiB memory
  - Scaling plan: Vertical scaling to db.r6g.xlarge for initial growth, then consider read replicas
- **Multi-AZ**: Yes (for high availability)
- **Storage**: 
  - Initial allocation: 100 GB gp3
  - Auto-scaling: Enabled (max 500 GB)
- **Engine Version**: PostgreSQL 15.x

**Staging/Test Environment**:
- **Instance Type**: db.t4g.medium
- **Multi-AZ**: No
- **Storage**: 50 GB gp3
- **Engine Version**: Same as production

**Development Environment**:
- **Instance Type**: db.t4g.small or local Docker containers for development
- **Multi-AZ**: No
- **Storage**: 20 GB gp3

### Network Configuration

- **VPC**: Deploy within application VPC
- **Subnet Group**: Private database subnets across multiple AZs
- **Security Group**: 
  - Allow PostgreSQL traffic (port 5432) only from application security groups
  - No direct public access

### Security Configuration

- **Encryption**:
  - At-rest: Enabled (using AWS KMS)
  - In-transit: SSL/TLS connections required
- **Authentication**:
  - Password authentication
  - IAM authentication for enhanced security (evaluate during implementation)
- **Access Control**:
  - Principle of least privilege
  - Application-specific database user with limited permissions

### Backup and Recovery

- **Automated Backups**: Enabled, 7-day retention
- **Snapshot Schedule**: Daily automated snapshots
- **Point-in-Time Recovery**: Enabled
- **Recovery Objectives**:
  - RTO (Recovery Time Objective): 1 hour
  - RPO (Recovery Point Objective): 5 minutes

### Monitoring and Alerting

- **Enhanced Monitoring**: Enabled (15-second intervals)
- **Performance Insights**: Enabled
- **CloudWatch Alarms**:
  - High CPU utilization (>80% for 5 minutes)
  - Low free memory (<10% for 5 minutes)
  - High disk usage (>85%)
  - Connection count (>80% of maximum)
  - Replica lag (if/when read replicas implemented)

## Database Implementation Details

### Connection Management

- **Connection Pooling**: Implement using TypeORM built-in pooling or consider pg-pool
  - Min connections: 5
  - Max connections: 25 (adjust based on load testing)
- **Connection String Management**: 
  - Store in AWS Secrets Manager
  - Rotate credentials automatically

### Migration Strategy

- **Tool**: TypeORM migrations
- **Process**:
  - Migrations managed in version control
  - CI/CD pipeline to apply migrations automatically
  - Rollback procedures documented for each migration

### Performance Considerations

- **Indexes**: 
  - Create indexes on frequently queried fields:
    - Product SKU (unique)
    - Category IDs
    - Price ranges
    - Created/updated timestamps
- **Partitioning**: 
  - Initially no partitioning
  - Consider partitioning by category or creation date if table size exceeds 50 million rows
- **Query Optimization**:
  - Implement query monitoring
  - Regular EXPLAIN ANALYZE to optimize slow queries
  - Avoid N+1 query patterns in ORM usage

## Cost Estimates

The following monthly cost estimates are based on AWS US East (N. Virginia) region pricing as of 2025. Actual costs may vary based on region, reserved instance commitments, and real-world usage patterns.

### Production Environment

| Component | Configuration | Estimated Monthly Cost |
|-----------|---------------|------------------------|
| RDS Instance | db.r6g.large, Multi-AZ | $407.00 |
| Storage | 100 GB gp3, Multi-AZ (replicated) | $46.00 |
| Backup Storage | 100 GB (avg), 7-day retention | $10.00 |
| Data Transfer | 500 GB outbound | $45.00 |
| Enhanced Monitoring | 15-second intervals | $5.00 |
| Performance Insights | Enabled with 7-day retention | $5.00 |
| **Total (Production)** | | **$518.00** |

### Staging Environment

| Component | Configuration | Estimated Monthly Cost |
|-----------|---------------|------------------------|
| RDS Instance | db.t4g.medium, Single-AZ | $60.00 |
| Storage | 50 GB gp3 | $11.50 |
| Backup Storage | 50 GB (avg), 7-day retention | $5.00 |
| Enhanced Monitoring | 60-second intervals | $2.50 |
| Performance Insights | Enabled with 7-day retention | $5.00 |
| **Total (Staging)** | | **$84.00** |

### Development Environment

| Component | Configuration | Estimated Monthly Cost |
|-----------|---------------|------------------------|
| RDS Instance | db.t4g.small, Single-AZ | $30.00 |
| Storage | 20 GB gp3 | $4.60 |
| **Total (Development)** | | **$34.60** |

> **Note:** Development costs could be significantly reduced by using local Docker containers during development and only using RDS for shared development environments.

### Alternative: Reserved Instances

For production and staging environments, consider reserved instances for cost savings:

| Environment | On-Demand (Monthly) | 1-year RI (Monthly) | Savings |
|-------------|---------------------|---------------------|---------|
| Production | $407.00 | $255.00 | ~37% |
| Staging | $60.00 | $37.80 | ~37% |

### Cost Optimization Strategies

1. **Right-sizing:** Monitor actual CPU and memory usage to ensure instances aren't over-provisioned
2. **Reserved Instances:** Purchase 1-year or 3-year reserved instances for production and staging for 40-60% savings
3. **Storage Tiering:** For backups and snapshots, transition to cheaper storage tiers automatically after 30 days
4. **Development Environments:** Use local PostgreSQL Docker containers for individual developers
5. **Automated Scaling:** Implement automatic start/stop for non-production environments during non-business hours
6. **Performance Monitoring:** Continuously optimize queries to reduce resource consumption and potentially allow downsizing

### Cost Growth Projections

As the product catalog grows, anticipate these cost increases:

- **Year 1 → Year 2:** +50% (due to data growth and increased traffic)
- **Year 2 → Year 3:** +30% (with more gradual growth expected)

Vertical scaling to db.r6g.xlarge would add approximately $350/month to production costs, while each read replica would add approximately $200/month.

## Implementation Tasks

1. **Database Creation**:
   - Create RDS instance via Infrastructure as Code (CloudFormation/Terraform)
   - Configure parameter groups, option groups, and security settings

2. **Schema Setup**:
   - Implement initial database schema via TypeORM entities
   - Create migration scripts for schema creation

3. **Security Implementation**:
   - Set up IAM roles and policies
   - Configure SSL/TLS certificates
   - Implement credential management in Secrets Manager

4. **Monitoring Setup**:
   - Configure CloudWatch alarms
   - Set up Performance Insights dashboards
   - Integrate with centralized logging system

5. **Connection Management**:
   - Implement connection pooling in application code
   - Set up connection retry logic and error handling

## References

- [AWS RDS PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [TypeORM Documentation](https://typeorm.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/index.html)
- [ADR-004: PostgreSQL for Relational Data](../../../architecture/adr/ADR-004-postgresql-for-relational-data.md)
- [ADR-020: Database-per-Service](../../../architecture/adr/ADR-020-data-management-database-per-service.md)
- [AWS-Centric Technology Decisions: Relational Database - PostgreSQL](../../../architecture/technology-decisions-aws-centeric/05-relational-database-postgresql.md) 