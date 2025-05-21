# 04: Monitoring and Alerting

Continuous monitoring and timely alerting are critical for maintaining the reliability, availability, and performance of the User Service. This document outlines the strategy for observing the service in production.

## 1. Key Metrics to Monitor

A comprehensive monitoring setup will track metrics across various categories:

### a. Application Performance Metrics (APM)
*   **Request Rate**: Number of requests per second/minute for each API endpoint.
*   **Error Rates**: Percentage of requests resulting in errors (HTTP 5xx, 4xx client errors if indicative of service issues).
    *   Breakdown by endpoint and error type.
*   **Latency (Response Time)**: Average, median, 95th, and 99th percentile latency for API requests.
    *   Breakdown by endpoint.
*   **Saturation**: Potentially queue lengths or processing time if internal queues are used (e.g., for event publishing if synchronous calls are made before handing off to Kafka client).
*   **JWT Validation/Issuance Time**: If significant, monitor time taken for token operations.

### b. System Resource Utilization (per Pod/Node)
*   **CPU Utilization**: Percentage of CPU used.
*   **Memory Utilization**: Amount of RAM used, watching for potential memory leaks.
*   **Network I/O**: Bytes sent/received per second.
*   **Disk I/O**: (If applicable, though User Service is largely stateless, temporary disk usage could occur).

### c. Kafka Integration Metrics
*   **Producer Metrics**:
    *   Message send rate.
    *   Send error rate.
    *   Serialization errors.
    *   Latency for message acknowledgments.
*   **Consumer Metrics (If User Service also consumes events)**:
    *   Consumer lag (per partition, per consumer group).
    *   Message processing rate.
    *   Processing error rate.
    *   Deserialization errors.
*   **Kafka Broker Health**: Monitored at the Kafka cluster level (e.g., under-replicated partitions, disk space, network throughput) - usually the responsibility of the team managing Kafka, but User Service team should be aware of its impact.

### d. Database Interaction Metrics
*   **Query Latency**: Average/percentile latency for critical database queries.
*   **Connection Pool Metrics**: Active connections, idle connections, connection wait time.
*   **Error Rates**: Number of database query errors.
*   **Transaction Throughput**: Number of transactions per second.

### e. Business-Specific Metrics
*   **User Registrations**: Rate of new user sign-ups.
*   **Logins/Authentication Attempts**: Rate of successful and failed logins.
*   **Password Reset Requests**: Frequency of password reset initiations.
*   **Profile Update Rate**: How often user profiles are modified.

## 2. Logging Strategy

*   **Structured Logging**: Logs should be in a structured format (e.g., JSON) to facilitate easier parsing, searching, and analysis by log management systems.
    *   Include contextual information like `timestamp`, `logLevel`, `serviceName` (`user-service`), `correlationId`, `userId` (where appropriate and PII allows), `endpoint`, `method`.
    *   NestJS logging capabilities can be customized to output JSON.
*   **Log Levels**: Use standard log levels (ERROR, WARN, INFO, DEBUG, TRACE). Production environment should typically run at INFO, with the ability to dynamically change log levels for specific modules or globally for debugging if needed (via configuration).
*   **Log Aggregation**: Logs from all User Service instances (pods) will be collected and aggregated into a centralized log management system.
    *   **Tools**: ELK Stack (Elasticsearch, Logstash, Kibana), EFK Stack (Elasticsearch, Fluentd, Kibana), Grafana Loki, Splunk, or cloud-provider specific solutions (AWS CloudWatch Logs, Google Cloud Logging, Azure Monitor Logs).
*   **Correlation ID**: Implement a correlation ID (transaction ID) that is generated at the entry point of a request (e.g., API Gateway or first service) and propagated through all service calls and log messages related to that request. This is crucial for tracing requests in a distributed system.

## 3. Distributed Tracing

*   **Purpose**: To trace the path of a request as it flows through multiple services in the microservices architecture.
*   **Integration**: The User Service should be instrumented to participate in distributed traces.
    *   Propagate trace context headers (e.g., W3C Trace Context, B3 Propagation).
    *   Generate spans for significant operations within the service (e.g., API request handling, database calls, Kafka message publishing).
*   **Tools**: Jaeger, Zipkin, OpenTelemetry (collector and SDKs). Many APM tools also provide distributed tracing capabilities.
*   **Benefits**: Helps identify bottlenecks, understand service dependencies, and debug issues in complex distributed workflows.

## 4. Alerting

*   **Alerting System**: Integrated with the monitoring system (e.g., Prometheus Alertmanager, Grafana Alerting, AWS CloudWatch Alarms, Azure Monitor Alerts).
*   **Key Alerting Thresholds**:
    *   High error rates (e.g., >1% of requests failing for 5+ minutes).
    *   High latency (e.g., 95th percentile latency > 500ms for 5+ minutes).
    *   High CPU/Memory utilization (e.g., >80% for 10+ minutes).
    *   Kafka producer errors or high send latency.
    *   Database connection issues or high query latency.
    *   Significant Kafka consumer lag (if applicable).
    *   Health check failures.
    *   Critical security events (though these might also go to a SIEM).
*   **Notification Channels**: Alerts will be routed to appropriate channels based on severity.
    *   **High Severity (Urgent)**: PagerDuty, OpsGenie, SMS, dedicated Slack/Teams channel for on-call engineers.
    *   **Medium/Low Severity (Informational)**: Email, general Slack/Teams channel.
*   **Actionable Alerts**: Alerts should be actionable and provide enough context for an engineer to start investigating. Avoid noisy alerts.
*   **Runbooks**: For common alerts, runbooks or troubleshooting guides should be available.

## 5. Health Check Endpoints

*   **Purpose**: Kubernetes uses health checks (liveness and readiness probes) to determine the health and readiness of pods.
*   **Liveness Probe**: Indicates if the container is running. If it fails, Kubernetes will restart the container.
    *   Example: A simple HTTP endpoint `/health/live` that returns 200 OK if the application process is up.
*   **Readiness Probe**: Indicates if the container is ready to accept traffic. If it fails, Kubernetes will remove the pod from service load balancers.
    *   Example: An HTTP endpoint `/health/ready` that checks dependencies like database connectivity and Kafka connectivity. It should return 200 OK only if the service can function properly.
*   **Startup Probe (Optional)**: For applications that have a long startup time, to ensure liveness/readiness probes don't kill the application before it's ready.

NestJS Actuator or Terminus modules can be used to easily expose health check endpoints with checks for database, Kafka, etc.

By implementing a robust monitoring and alerting strategy, the operations team can proactively identify and address issues, ensuring the User Service remains stable and performant.
