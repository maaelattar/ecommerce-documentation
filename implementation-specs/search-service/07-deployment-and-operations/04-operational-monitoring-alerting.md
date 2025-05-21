# Operational Monitoring and Alerting

## Overview

Effective operational monitoring and alerting are crucial for maintaining the health, performance, and reliability of the Search Service and its dependencies (especially Elasticsearch and Kafka) in a production environment. This document outlines key metrics to monitor, logging practices for operational insight, and alerting strategies to ensure timely responses to issues. It builds upon the general monitoring concepts in `../05-event-handling/09-monitoring-and-logging.md` but with a focus on the operational aspects post-deployment.

## Key Monitoring Areas (Operational Focus)

### 1. Search Service Application Instances (Pods/Containers)

*   **Resource Utilization**: CPU, memory usage, network I/O for each instance. Alerts on high sustained usage or approaching limits.
*   **Instance Health & Availability**: Number of running vs. desired instances. Liveness and readiness probe success/failure rates. Pod restarts and crash loops.
*   **HTTP API Performance (if applicable)**:
    *   Request rate (RPM/RPS).
    *   Request latency (average, p95, p99).
    *   Error rates (4xx, 5xx status codes).
*   **Event Consumption (Kafka Consumers)**:
    *   Consumer Lag per partition: Critical for ensuring search index freshness. Alerts on consistently high or growing lag.
    *   Events processed per second/minute.
    *   End-to-end processing latency (from Kafka message timestamp to ES commit, if traceable).
    *   DLQ submission rate: Number of messages sent to the Dead Letter Queue.
*   **JVM Metrics (if applicable, e.g., for Elasticsearch or Kafka itself, or if using a JVM-based service)**: Heap usage, garbage collection activity.
*   **Log Volume and Error Log Rate**: Monitor the volume of logs and specifically the rate of ERROR level logs from the application.

### 2. Elasticsearch Cluster (Recap from `02-elasticsearch-cluster-management.md` with operational lens)

*   **Cluster Health Status**: Green (ideal), Yellow (unassigned replicas - HA risk), Red (unassigned primaries - data loss risk!). **Alert immediately on Red, investigate Yellow.**
*   **Node Health**: CPU, memory (heap & OS), disk space (especially data nodes - alert on low disk space), I/O, network.
*   **Indexing Performance**: Indexing rate, indexing latency, bulk processing rejections/errors, merge/refresh times.
*   **Search Performance**: Query rate, query latency (per shard and overall), cache hit/miss rates (query cache, field data cache).
*   **Shard Status**: Number of initializing, relocating, or unassigned shards. Prolonged relocation or unassigned shards are problematic.
*   **Pending Tasks**: Number of tasks in the cluster pending queue. High numbers indicate overload.
*   **Circuit Breaker Status**: Monitor if any Elasticsearch circuit breakers have tripped (e.g., for memory).

### 3. Kafka Cluster (If self-managed, or key metrics from managed service)

*   **Broker Health**: Availability of Kafka brokers.
*   **Topic Metrics**: Message production/consumption rates per topic. Topic size, number of partitions.
*   **Controller Health**: Active controller, leader elections.
*   **Under-Replicated Partitions**: Partitions where the number of in-sync replicas is less than the configured replication factor. Risk of data loss.
*   **Disk Usage**: Disk space on Kafka brokers.
*   **Network Throughput**: Inbound/outbound traffic.

### 4. CI/CD Pipeline and Deployments

*   Deployment success/failure rates.
*   Deployment duration.
*   Rollback occurrences.

## Logging for Operational Insight

(Reiterating from `../05-event-handling/09-monitoring-and-logging.md` with an operational emphasis)

*   **Structured Logging (JSON)**: Essential for automated parsing and analysis.
*   **Correlation IDs**: Trace requests/events across service instances and even across different services (if using distributed tracing).
*   **Key Operational Log Events**: 
    *   Application startup and shutdown sequences.
    *   Configuration loaded.
    *   Connections established/lost to Kafka, Elasticsearch.
    *   Consumer group rebalances (Kafka).
    *   Significant state changes (e.g., HPA scaling events, circuit breaker state changes).
    *   Details of failed health checks (liveness/readiness probes).
    *   All errors with stack traces and relevant context (e.g., event ID, query parameters).

## Alerting Strategy

Alerts should be actionable and categorized by severity.

*   **P1: Critical Alerts (Immediate Action Required - potential user impact or data loss)**
    *   Search Service API 5xx error rate above X% for Y minutes.
    *   Elasticsearch cluster status RED.
    *   Kafka consumer lag for critical topics > N minutes for M minutes.
    *   DLQ size rapidly increasing or above critical threshold.
    *   High number of application pod restarts / crash loops.
    *   Elasticsearch data node disk space < X% free.
    *   Critical security alerts (e.g., from intrusion detection or vulnerability scans).
    *   Deployment failures for critical services.
*   **P2: Warning Alerts (Investigation Needed - potential future impact)**
    *   Search Service API latency (p99) > X ms for Y minutes.
    *   Elasticsearch cluster status YELLOW.
    *   Sustained high CPU/Memory on Search Service pods or Elasticsearch nodes.
    *   Kafka consumer lag showing consistent growth but not yet critical.
    *   Elevated rate of non-critical application errors.
    *   Elasticsearch shards relocating for an extended period.
    *   Elasticsearch JVM heap usage > X% consistently.
*   **P3: Informational Alerts (Awareness - may not require immediate action)**
    *   Successful deployments.
    *   HPA scaling events (up or down).
    *   Completion of major batch jobs (e.g., full re-index).

### Alerting Channels

*   **Email**: For less urgent alerts or summaries.
*   **Messaging Platforms (Slack, Microsoft Teams)**: For P2/P3 alerts, team awareness.
*   **PagerDuty / Opsgenie / VictorOps**: For P1 critical alerts requiring immediate on-call engineer response.

### Alert Configuration

*   **Thresholds**: Define clear, sensible thresholds for alerts. Avoid overly sensitive alerts (alert fatigue) or insensitive alerts (missing important issues).
*   **De-duplication**: Group similar alerts to avoid flooding.
*   **Escalation Policies**: Define how alerts are escalated if not acknowledged or resolved.
*   **Runbooks/Playbooks**: Link alerts to documentation (runbooks) that provide steps for diagnosing and resolving the issue.

## Tools

*   **Monitoring & Alerting Platforms**: Prometheus & Alertmanager, Grafana, Datadog, New Relic, Dynatrace, AWS CloudWatch, Google Cloud Monitoring, Azure Monitor.
*   **Log Aggregation & Analysis**: ELK Stack (Elasticsearch for logs, Logstash/Fluentd, Kibana), Splunk, Grafana Loki, Datadog Logs.

## Regular Review

*   Periodically review monitoring dashboards and alert configurations.
*   Adjust thresholds based on historical performance and evolving system behavior.
*   Conduct post-mortems for critical incidents and update monitoring/alerting as needed.

By implementing a comprehensive operational monitoring and alerting strategy, teams can ensure the Search Service runs smoothly, detect issues proactively, and minimize downtime and impact on users.
