# Order Service Database Selection

## 1. Introduction

This document outlines the database technology selection for the Order Service. The Order Service requires a reliable, consistent, and scalable database solution to manage order lifecycle data. The selection is based on the platform's architectural decisions, particularly [ADR-004-data-persistence-strategy](../../architecture/adr/ADR-004-data-persistence-strategy.md).

## 2. Database Requirements

### 2.1. Functional Requirements

- **ACID Transactions**: Orders require strong consistency and transactional integrity
- **Relational Data**: Orders have complex relationships with line items, addresses, payments, and users
- **Query Flexibility**: Support for complex queries across order data
- **Audit Trail**: Ability to track changes to orders over time
- **Historical Data**: Maintain complete order history for reporting and analysis

### 2.2. Non-Functional Requirements

- **High Availability**: 99.99% uptime for production environments
- **Scalability**: Support for growing order volumes
- **Performance**: Sub-100ms query response times for common operations
- **Security**: Encryption at rest and in transit
- **Backup and Recovery**: Point-in-time recovery capabilities
- **Compliance**: Support for data retention policies and regulatory requirements

## 3. Technology Selection

### 3.1. Primary Database: Amazon RDS for PostgreSQL

#### 3.1.1. Justification

PostgreSQL on Amazon RDS has been selected as the primary database for the Order Service for the following reasons:

1. **ACID Compliance**: PostgreSQL provides full ACID compliance, ensuring data integrity for critical order transactions.
2. **Relational Model Support**: Well-suited for the complex relationships in order data.
3. **Advanced Features**: Support for JSON fields, array types, and complex queries.
4. **AWS Integration**: Native integration with AWS services for monitoring, scaling, and backup.
5. **Read Replicas**: Support for read replicas to handle reporting and read-heavy workloads.
6. **Backup and Recovery**: Automated backups and point-in-time recovery.
7. **Managed Service**: Reduced operational overhead with Amazon RDS.
8. **Consistency with ADR**: Aligns with ADR-004, which recommends PostgreSQL for transactional data with complex relationships.

#### 3.1.2. Configuration Overview

| Environment | Instance Type  | Multi-AZ | Storage   | Read Replicas |
| ----------- | -------------- | -------- | --------- | ------------- |
| Production  | db.r6g.2xlarge | Yes      | 1TB gp3   | 2             |
| Staging     | db.r6g.xlarge  | Yes      | 500GB gp3 | 1             |
| Development | db.r6g.large   | No       | 200GB gp3 | 0             |

### 3.2. Supplementary Technology: Amazon DynamoDB

#### 3.2.1. Usage Context

While PostgreSQL serves as the primary database, DynamoDB will be used for:

1. **Order Status History**: Tracking detailed order status changes with timestamps
2. **Session-Scoped Order Data**: Temporary cart data before order finalization
3. **High-Throughput Metrics**: Real-time order statistics and counters

#### 3.2.2. Justification

1. **Scalability**: Better handles high-volume write operations for status updates
2. **TTL Support**: Automatic expiration for temporary data
3. **Low Latency**: Consistent single-digit millisecond performance for simple queries
4. **Seamless Scaling**: Auto-scaling without maintenance windows

## 4. Access Patterns

### 4.1. Write Patterns

| Operation                   | Frequency | Database   | Consistency Requirements |
| --------------------------- | --------- | ---------- | ------------------------ |
| Create Order                | High      | PostgreSQL | Strong                   |
| Update Order Status         | Very High | DynamoDB   | Eventual                 |
| Add Order Items             | High      | PostgreSQL | Strong                   |
| Update Payment Information  | Medium    | PostgreSQL | Strong                   |
| Update Shipping Information | Medium    | PostgreSQL | Strong                   |

### 4.2. Read Patterns

| Operation                     | Frequency | Database     | Read Type     |
| ----------------------------- | --------- | ------------ | ------------- |
| Get Order by ID               | Very High | PostgreSQL   | Point Read    |
| List User's Orders            | High      | PostgreSQL   | Range Query   |
| Search Orders by Status       | Medium    | PostgreSQL   | Range Query   |
| Get Order Status History      | Medium    | DynamoDB     | Point Read    |
| Order Analytics and Reporting | Low       | PostgreSQL\* | Complex Query |

\*Read replicas will be used for analytics and reporting queries.

## 5. Schema Migration Strategy

### 5.1. Schema Evolution

The Order Service database schema will evolve over time. The following practices will be used:

1. **Versioned Migrations**: All schema changes will use versioned migration scripts
2. **Backward Compatibility**: Schema changes should maintain backward compatibility when possible
3. **Downtime-Free Migrations**: Using techniques like:
   - Adding new nullable columns
   - Creating new tables before migrating data
   - Deploying application changes in multiple phases

### 5.2. Tools and Process

1. **Migration Tool**: Flyway for Java-based applications
2. **Verification Process**: Schema migrations will be tested in development and staging before production
3. **Rollback Strategy**: Each migration will have a corresponding rollback script
4. **Coordination**: Schema changes will be coordinated with application deployments

## 6. Data Access Layer Implementation

### 6.1. ORM Selection

The Order Service will use TypeORM as the ORM layer for PostgreSQL access, providing:

1. **Type Safety**: TypeScript integration for compile-time type checking
2. **Migrations**: Automated schema migration generation and management
3. **Repository Pattern**: Clean separation of data access logic
4. **Query Builder**: Flexible query construction for complex operations

### 6.2. DynamoDB Access

DynamoDB access will use the AWS SDK for JavaScript v3, with:

1. **Document Client**: Higher-level interface for DynamoDB operations
2. **Batch Operations**: Efficient batch read/write operations
3. **Typescript Models**: Type-safe data access
4. **Conditional Writes**: Support for optimistic concurrency control

## 7. References

- [Amazon RDS for PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [Amazon DynamoDB Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [TypeORM Documentation](https://typeorm.io/)
- [ADR-004-data-persistence-strategy](../../architecture/adr/ADR-004-data-persistence-strategy.md)
- [Data Storage and Management Specification](../infrastructure/06-data-storage-specification.md)
