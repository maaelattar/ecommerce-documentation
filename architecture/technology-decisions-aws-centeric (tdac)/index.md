# AWS-Centric Technology Decisions Summary

This section documents the key technology selections for the e-commerce platform, with a specific focus on leveraging AWS managed services where appropriate to reduce operational overhead and benefit from the AWS ecosystem.

These decisions build upon the strategies outlined in the [Architecture Decision Records (ADRs)](../adr/).

## Core Technology Selections

*   **[01-api-gateway-selection.md](./01-api-gateway-selection.md):** Amazon API Gateway
*   **[02-identity-provider-selection.md](./02-identity-provider-selection.md):** Amazon Cognito
*   **[03-message-broker-selection.md](./03-message-broker-selection.md):** Amazon MQ for RabbitMQ (Primary), Amazon MSK (Secondary)
*   **[04-nosql-database-selection.md](./04-nosql-database-selection.md):** Amazon OpenSearch Service, Amazon ElastiCache for Redis, Amazon DynamoDB
*   **[05-relational-database-postgresql.md](./05-relational-database-postgresql.md):** Amazon RDS for PostgreSQL
*   **[06-service-mesh-selection.md](./06-service-mesh-selection.md):** AWS App Mesh
*   **[07-caching-implementation-details.md](./07-caching-implementation-details.md):** AWS ElastiCache for Redis (Distributed), AWS CloudFront (CDN)
*   **[08-monitoring-observability-stack.md](./08-monitoring-observability-stack.md):** Amazon OpenSearch Service / Amazon Managed Service for Prometheus (AMP) / Amazon Managed Grafana (AMG) / AWS X-Ray / Fluent Bit / AWS Distro for OpenTelemetry (ADOT)

Refer to the individual documents for detailed rationale, implementation guidance, and alternatives considered.
