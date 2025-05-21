# 06 - Integration with Shared Platform Services

This document outlines how the User Service integrates with common, shared platform services that provide cross-cutting concerns like logging, monitoring, configuration, and service discovery. These integrations are essential for the operational health, observability, and manageability of the User Service.

## 1. Logging Service

*   **Purpose**: To centralize application logs for debugging, auditing, and analysis.
*   **Integration Mechanism**:
    *   The User Service uses a structured logging library (e.g., `pino`, `winston`, or NestJS's built-in `LoggerService` configured for JSON output).
    *   Logs are written to `stdout`/`stderr` within the container.
    *   A log aggregation agent (e.g., Fluentd, Filebeat, Promtail) running on the Kubernetes nodes (or as a sidecar) collects these logs and forwards them to a centralized logging platform (e.g., Elasticsearch/Logstash/Kibana - ELK stack, Grafana Loki, Splunk, Datadog Logs).
*   **Key Information Logged by User Service**:
    *   Standard request/response logs (method, path, status code, latency) via NestJS middleware or interceptors.
    *   Service startup and shutdown events.
    *   Significant business logic events (e.g., user registration attempt, login success/failure, password reset initiation) with appropriate context but **excluding PII** like passwords or full tokens from general logs.
    *   Errors and exceptions with stack traces.
    *   Event publication attempts and outcomes (success/failure to send to Kafka).
    *   Security-relevant audit events (which might go to a more specialized audit log sink).
*   **Log Structure**: Logs should be structured (e.g., JSON) and include common fields like `timestamp`, `level` (info, warn, error), `serviceName` (`user-service`), `correlationId`, `userId` (if available and safe), and a descriptive `message`.

## 2. Monitoring and Alerting Service

*   **Purpose**: To track the health, performance, and resource utilization of the User Service, and to alert operators of issues.
*   **Integration Mechanism**:
    *   **Metrics Exposition**: The User Service exposes an HTTP endpoint (e.g., `/metrics`) in Prometheus format. NestJS applications can use libraries like `prom-client` or `@nestjs/terminus` with Prometheus integration.
    *   **Metrics Collection**: A Prometheus server scrapes this `/metrics` endpoint periodically.
    *   **Visualization & Dashboards**: Grafana is used to visualize metrics from Prometheus and create dashboards for the User Service (e.g., request rates, error rates, latency percentiles, Kafka producer metrics, database connection pool stats).
    *   **Alerting**: Prometheus Alertmanager (or Grafana alerting) is configured with rules based on User Service metrics. Alerts are sent to operators via channels like Slack, PagerDuty, or email.
*   **Key Metrics Monitored for User Service**:
    *   **Application Metrics**: API request rates, error rates (per endpoint, per status code), request latency (average, percentiles like p95, p99).
    *   **System Metrics**: CPU utilization, memory usage, disk I/O, network I/O for User Service pods/containers.
    *   **JVM/Node.js Metrics**: Garbage collection stats, event loop lag (for Node.js).
    *   **Database Metrics**: Connection pool usage, query latency, error rates from the User Service's perspective.
    *   **Kafka Producer Metrics**: Message send rates, error rates, latency to Kafka brokers.
    *   **Health Checks**: `/health/live` and `/health/ready` endpoints for Kubernetes liveness and readiness probes (often provided by `@nestjs/terminus`).
*   **Key Alerts Configured**:
    *   High error rates (e.g., >5% 5xx errors).
    *   High request latency.
    *   High CPU/memory utilization.
    *   User Service pods down or restarting frequently.
    *   Failure to connect to database or Kafka.
    *   High number of Kafka message publishing failures.

## 3. Configuration Service

*   **Purpose**: To manage and provide externalized configuration for the User Service, allowing settings to be changed without redeploying the application.
*   **Integration Mechanism**:
    *   **NestJS `ConfigModule` (`@nestjs/config`)**: Used to load configuration from various sources:
        *   Environment variables (primary method in containerized environments).
        *   `.env` files (for local development).
        *   Potentially a centralized configuration management service (e.g., HashiCorp Consul, AWS AppConfig, Spring Cloud Config Server) if the platform uses one. The `ConfigModule` can be extended to fetch from these sources.
*   **Dynamic Configuration**: If a centralized configuration service is used, the User Service might periodically poll for updates or subscribe to change notifications for certain dynamic configurations (e.g., feature flags, password policy parameters if highly dynamic).
*   **Secrets Management**: Sensitive configurations (database passwords, API keys for external services, JWT secrets) MUST NOT be hardcoded. They should be injected as environment variables via secure mechanisms provided by the deployment platform (e.g., Kubernetes Secrets, HashiCorp Vault integration).

## 4. Service Discovery

*   **Purpose**: To allow the User Service to discover the network locations (IP addresses, ports) of other internal services it might need to call, and for other services/gateways to discover the User Service.
*   **Integration Mechanism (Kubernetes)**: When deployed in Kubernetes:
    *   **DNS-Based Discovery**: User Service (and other services) are exposed as Kubernetes Services. Other pods can discover them using their stable DNS names (e.g., `http://user-service.namespace.svc.cluster.local`). This is the most common and recommended approach within Kubernetes.
    *   The User Service registers itself implicitly by being deployed as a Kubernetes Service.
*   **Integration Mechanism (Non-Kubernetes/External Registry)**:
    *   If not using Kubernetes DNS or if needing more advanced features, a dedicated service registry like HashiCorp Consul or Netflix Eureka might be used.
    *   The User Service would then need a client library to register itself with the registry upon startup (sending its IP, port, health check endpoint) and to query the registry to find other services.
    *   `@nestjs/terminus` can integrate with service registries for health checking.

These integrations ensure that the User Service is observable, manageable, configurable, and discoverable within the broader e-commerce platform ecosystem.
