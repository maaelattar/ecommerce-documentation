# Inventory Service: Production Readiness Checklist

## 1. Introduction

*   **Purpose**: This document serves as a comprehensive checklist and guide to ensure that the Inventory Service meets all necessary operational, performance, security, and reliability standards before being deployed to and maintained in the production environment. Its goal is to minimize risks and ensure smooth operations.
*   **Platform Guidelines**: This checklist is specific to the Inventory Service but aligns with the overall platform production readiness guidelines (assume a link to a general platform-wide document would be here, e.g., `../../architecture/00-production-readiness-overview.md` if it existed).

---

## 2. Monitoring & Alerting (Ref: ADR-011 Monitoring and Observability, ADR-021 Logging Strategy)

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

### 2.1. Key Metrics to Monitor

*   **API Endpoint Metrics**:
    *   [ ] Request Rate (per endpoint, overall)
    *   [ ] Error Rate (4xx, 5xx, per endpoint, overall)
    *   [ ] Latency (average, 95th percentile, 99th percentile, per endpoint, overall)
*   **Service Health**:
    *   [ ] CPU Usage (per instance, aggregate)
    *   [ ] Memory Usage (per instance, aggregate)
    *   [ ] Disk Space (if service uses significant local disk beyond container image)
    *   [ ] Container Restarts / Pod Restarts
    *   [ ] Number of running instances/replicas
*   **Inventory-Specific Metrics**:
    *   [ ] Rate of stock updates (by type: purchase, sale, return, adjustment)
    *   [ ] Rate of inventory reservations (successes, failures)
    *   [ ] Number of `InventoryReservedEvent` published
    *   [ ] Number of `InventoryReservationFailedEvent` published
    *   [ ] Number of `StockLevelChangedEvent` published
    *   [ ] Number of `StockStatusChangedEvent` published
    *   [ ] Occurrences of "out-of-stock" status changes
    *   [ ] Event publishing latency (time from business event to message broker ACK, if measurable via outbox)
    *   [ ] Age of oldest message in transactional outbox (if applicable)
*   **Database Metrics (PostgreSQL via RDS - ADR-004)**:
    *   [ ] Connection Pool Usage (active connections vs. max connections)
    *   [ ] Query Latency (average, 95th percentile for key queries)
    *   [ ] Replication Lag (if read replicas are used)
    *   [ ] CPU/Memory/Disk IOPS for the database instance
    *   [ ] Number of deadlocks or long-running transactions
*   **Message Broker Metrics (RabbitMQ via Amazon MQ - ADR-018)**:
    *   [ ] `inventory.events` exchange: message rates (in/out)
    *   [ ] Relevant Queue Lengths (for queues consuming Inventory Service events, and for its outbox poller if applicable)
    *   [ ] Message Publishing Rate (from Inventory Service)
    *   [ ] Consumer Acknowledgement Rate / Consumer Lag (for consumers of Inventory Service events)
    *   [ ] Dead Letter Queue (DLQ) size for inventory-related events

### 2.2. Dashboards

*   [ ] **Service Overview Dashboard**: Aggregating key health metrics (CPU, memory, requests, errors, latency), instance count.
*   [ ] **API Performance Dashboard**: Detailed breakdown of request rates, error rates, and latencies per API endpoint.
*   [ ] **Inventory KPIs Dashboard**: Tracks core inventory metrics like stock update rates, reservation success/failure, out-of-stock events, event publishing volumes.
*   [ ] **Database Performance Dashboard**: Monitors health and performance of the PostgreSQL instance.
*   [ ] **Message Broker Dashboard**: Monitors health of RabbitMQ, exchange rates, and queue states relevant to inventory.

### 2.3. Alerting

*   **Critical Alerts (High Priority - immediate notification to on-call)**:
    *   [ ] Service unavailable (e.g., health checks failing consistently).
    *   [ ] API error rate exceeds X% over Y minutes (e.g., >5% 5xx errors over 5 mins).
    *   [ ] API latency (99th percentile) exceeds Z ms over Y minutes (e.g., >2s over 5 mins).
    *   [ ] Critical database issues (e.g., CPU >90%, very high connection count, replication lag > X minutes).
    *   [ ] Message broker unavailable or critical queue length for Inventory Service outbox exceeds threshold.
    *   [ ] Consistent inventory reservation failures (e.g., >X% failure rate over Y minutes).
    *   [ ] Transactional outbox queue length consistently high or growing.
    *   [ ] DLQ message count increasing for inventory events.
*   **Warning Alerts (Medium Priority - notification, may not require immediate page)**:
    *   [ ] Elevated (but not critical) error rates or latency.
    *   [ ] High resource utilization (CPU, memory > X% for Y duration).
    *   [ ] Database connection pool nearing capacity.
    *   [ ] Non-critical message queue lengths growing.
*   **Notification Channels**:
    *   [ ] Defined (e.g., PagerDuty, Slack, Email).
    *   [ ] Alert escalation paths understood.

---

## 3. Logging (Ref: ADR-010 Structured Logging, ADR-021 Logging Strategy)

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

*   [ ] **Log Levels**: Appropriate log levels (INFO, DEBUG, WARN, ERROR) used effectively. Default production log level is INFO.
*   [ ] **Structured Logging**: Logs are in JSON format for easier parsing and analysis.
*   **Key Information Logged**:
    *   [ ] Request details: HTTP method, path, status code, duration (excluding sensitive headers/body).
    *   [ ] Response details: status code, duration (excluding sensitive body).
    *   [ ] Errors: error messages, stack traces, relevant context.
    *   [ ] Key business operations:
        *   Stock reservation attempts (variantId, quantity, success/failure, orderId).
        *   Stock quantity updates (variantId, changeQuantity, newQuantity, type, reason).
        *   Inventory status changes (variantId, oldStatus, newStatus).
    *   [ ] Event publishing: event type, eventId, success/failure, target exchange/topic.
    *   [ ] Event consumption (if applicable): event type, eventId, success/failure of processing.
*   [ ] **Correlation IDs**: Present in all logs and propagated across service calls (both incoming and outgoing).
*   [ ] **Log Aggregation**: Logs are shipped to a central log management system (e.g., ELK Stack, CloudWatch Logs, Splunk).
*   [ ] **Searchability**: Logs are easily searchable and filterable in the aggregation tool.
*   [ ] **PII/Sensitive Data**: No sensitive PII or security-related data (passwords, tokens) logged in plain text.

---

## 4. Scalability & Performance (Ref: ADR-027 Scalability and Performance Testing)

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

*   [ ] **Performance Testing**:
    *   Load testing conducted to identify bottlenecks and determine max sustainable TPS.
    *   Target TPS for key endpoints defined (e.g., `/reserve`, `/stock-levels`).
    *   Acceptable latency under load (average, 95th, 99th percentile) defined and met.
    *   Endurance testing performed to check for memory leaks or performance degradation over time.
*   [ ] **Scalability Configuration**:
    *   Horizontal Pod Autoscaler (HPA) configured with appropriate metrics (e.g., CPU, custom metrics like queue length if applicable).
    *   Minimum and maximum replica counts for HPA defined based on load tests and baseline requirements.
*   [ ] **Database Connection Pooling**:
    *   Connection pool size optimized for expected load and database capacity.
    *   Connection timeouts and acquisition timeouts configured appropriately.
*   [ ] **Caching Strategy**:
    *   (As per ADR-009, caching is mostly at API Gateway/CDN level).
    *   [ ] Any service-specific caching needs for frequently accessed, relatively static inventory data identified and implemented if necessary (e.g., product variant existence if not relying purely on events).
*   [ ] **Resource Requests and Limits**:
    *   Container CPU and memory requests and limits defined in deployment configurations.
    *   Requests set to realistic values based on typical usage to ensure QOS.
    *   Limits set to prevent resource starvation across the cluster.
*   [ ] **Database Indexing**: Critical query paths are optimized with appropriate database indexes.

---

## 5. Security (Ref: ADR-005 Authentication and Authorization, ADR-019 API Gateway and Service Mesh Security, ADR-026 Security Best Practices)

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

*   **Authentication & Authorization**:
    *   [ ] API endpoints secured using service-to-service authentication (e.g., OAuth 2.0 client credentials, JWTs).
    *   [ ] Authorization rules implemented (e.g., Order Service can reserve/release, Product Service can read).
    *   [ ] No public, unauthenticated endpoints unless explicitly designed and approved.
*   [ ] **Secrets Management (ADR-016)**:
    *   No hardcoded secrets (API keys, database passwords, etc.) in code or configuration files.
    *   Secrets managed via a secure store (e.g., HashiCorp Vault, AWS Secrets Manager).
*   [ ] **Input Validation**:
    *   All incoming API request data (path params, query params, body) is validated (type, format, range).
    *   DTOs use validation decorators (`class-validator`).
*   [ ] **Dependency Vulnerabilities**:
    *   Regular scans for known vulnerabilities in third-party libraries (`npm audit` or tools like Snyk, Trivy).
    *   Process in place to update vulnerable dependencies.
*   [ ] **Container Security**:
    *   Base Docker image is from a trusted source and regularly updated.
    *   Container image scanned for vulnerabilities.
    *   Application runs with the least privilege necessary (non-root user).
    *   No unnecessary tools or packages in the final image.
*   [ ] **Rate Limiting & Throttling**:
    *   Configured on the API Gateway (ADR-006) or at the service level if necessary to protect against abuse.
*   [ ] **Security Audits**:
    *   Plan for regular security code reviews or penetration testing (if applicable).
*   [ ] **TLS**: Communication encrypted using TLS for all external and internal API calls.

---

## 6. Configuration Management (Ref: ADR-016 Configuration Management)

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

*   [ ] **Externalized Configuration**: All environment-specific configurations (e.g., database URLs, queue names, log levels, external service endpoints) are externalized from the application code.
*   [ ] **Configuration Source**: Configurations managed via Kubernetes ConfigMaps/Secrets, or a dedicated configuration server (e.g., Spring Cloud Config, HashiCorp Consul).
*   [ ] **Environment Promotion**: Clear process for managing and promoting configurations across environments (dev, staging, prod).
*   [ ] **Sensitive Data**: Configuration containing sensitive data is treated as a secret and managed accordingly.

---

## 7. Data Management & Backup (Ref: ADR-004 Database Selection, ADR-020 Database per Service, ADR-025 Data Backup and Recovery)

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

*   [ ] **Database Backup**:
    *   Automated backups configured for the PostgreSQL database (e.g., RDS snapshots).
    *   Backup frequency and retention period defined and meet RPO/RTO requirements.
*   [ ] **Restore Procedures**:
    *   Database restore procedures documented and tested.
    *   Time to restore verified.
*   [ ] **Data Retention Policies**:
    *   Data retention policy defined for `InventoryHistory` records (e.g., how long to keep detailed history).
    *   Mechanism for archiving or purging old data in place if necessary.
*   [ ] **Data Migration**:
    *   Strategy for handling schema migrations (e.g., using TypeORM migrations) tested.
    *   Rollback plan for failed migrations.
*   [ ] **Data Integrity**: Measures in place to ensure data integrity (e.g., database constraints, validation).

---

## 8. Resilience & Fault Tolerance (Ref: ADR-022 Fault Tolerance and Resilience)

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

*   **Health Check Endpoints**:
    *   [ ] Liveness endpoint (`/health/live` or similar) implemented to indicate if the service is running.
    *   [ ] Readiness endpoint (`/health/ready` or similar) implemented to indicate if the service is ready to accept traffic (e.g., database connected, initial setup complete).
    *   [ ] Kubernetes liveness and readiness probes configured correctly.
*   [ ] **Retry Mechanisms**:
    *   Implemented for transient failures in outbound calls (e.g., to RabbitMQ, potentially other services if synchronous calls are made).
    *   Uses exponential backoff and jitter.
    *   Transactional Outbox pattern for event publishing handles retries for message broker communication.
*   [ ] **Graceful Shutdown**:
    *   Service handles `SIGTERM` signals to shut down gracefully (finish processing in-flight requests, release resources, close connections).
    *   Kubernetes `terminationGracePeriodSeconds` configured appropriately.
*   [ ] **Circuit Breaker Pattern**:
    *   Considered/implemented for critical outbound synchronous calls (if any) to prevent cascading failures. (Inventory Service aims to minimize these).
*   [ ] **Idempotent Operations**: Critical operations (e.g., event handlers, some API endpoints) are designed to be idempotent.

---

## 9. Documentation

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

*   [ ] **API Documentation**:
    *   OpenAPI (Swagger) specification (`openapi/inventory-service.yaml`) is up-to-date and accurately reflects all exposed endpoints.
    *   Documentation is accessible to consumer services/developers.
*   [ ] **Runbooks**:
    *   Basic troubleshooting steps for common issues documented.
    *   Procedures for common operational tasks (e.g., manual data correction if ever needed, checking outbox status).
    *   Escalation paths for unresolved issues.
*   [ ] **This Production Readiness Checklist**: Completed and reviewed.
*   [ ] **Architecture Decision Records (ADRs)**: Relevant ADRs are referenced and their principles applied.
*   [ ] **Onboarding Documentation**: For new team members to understand the service.

---

## 10. Team & Operations

**Status**: [ ] TODO / [ ] In Progress / [ ] Completed

*   [ ] **Team Familiarity**: Development team members are familiar with the service architecture, common troubleshooting procedures, and monitoring dashboards.
*   [ ] **On-Call Rotation**:
    *   On-call rotation schedule established and communicated.
    *   Contact information for on-call personnel readily available.
*   [ ] **Incident Response Plan**:
    *   Basic incident response plan understood by the team (communication, escalation, post-mortem).
    *   Access to necessary tools (logs, monitoring, infrastructure) for on-call personnel confirmed.
*   [ ] **Dependencies Understood**: Team understands dependencies on other services and infrastructure, and their SLAs if applicable.

---

**Final Review & Sign-off**:

*   [ ] Lead Developer:
*   [ ] Operations Lead:
*   [ ] Product Owner (if applicable):

Date: ______________
