# ADR-010: Logging Strategy

*   **Status:** Proposed
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (N/A - Lead Developers, SRE/Ops Team if distinct)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In a microservices architecture (ADR-001), requests often traverse multiple services. Understanding system behavior, debugging issues, auditing actions, and monitoring performance requires a robust and consistent logging strategy. Without a centralized and structured approach, diagnosing problems in a distributed environment becomes exceedingly difficult and time-consuming. Each service generating logs in isolation, in different formats, or without proper context (like correlation IDs) hinders effective observability.

## Decision Drivers

*   **Debuggability & Troubleshooting:** Quickly identify and diagnose issues across distributed services.
*   **Auditing & Compliance:** Provide a clear trail of actions for security and compliance purposes.
*   **Performance Monitoring & Analysis:** Understand request lifecycles, identify bottlenecks, and analyze system behavior.
*   **System Health Monitoring:** Aggregate logs to detect anomalies and errors.
*   **Developer Productivity:** Provide developers with easy access to relevant logs for their services.
*   **Standardization:** Ensure logs are consistent in format and content across all services.
*   **Scalability:** The logging solution must handle a high volume of log data from numerous services.

## Considered Options

### Option 1: Console Logging Only (Per Service)

*   **Description:** Each service writes logs to its standard output (console). Log inspection relies on accessing individual container logs (e.g., via `kubectl logs`).
*   **Pros:** Simplest to implement within each service. No external dependencies for the service itself.
*   **Cons:**
    *   No centralized aggregation or searching.
    *   Logs are lost if containers/pods are restarted (unless an external log collector is already configured at the K8s level, but this option assumes no *application-level* strategy).
    *   Very difficult to trace requests across services.
    *   No long-term storage or advanced analysis capabilities.
    *   Not scalable for production environments.

### Option 2: File-Based Logging (Per Service, Local Files)

*   **Description:** Each service writes logs to local files within its container. Requires a sidecar or node agent to collect these files for central storage.
*   **Pros:** Logs persist within the container filesystem (until container is destroyed).
*   **Cons:**
    *   Still requires a separate mechanism for log collection, aggregation, and searching.
    *   Managing log rotation and disk space within containers can be problematic.
    *   Accessing logs for troubleshooting is still cumbersome without a central platform.

### Option 3: Centralized Logging Platform with Structured Logging

*   **Description:** All services send logs (preferably in a structured format like JSON) to a dedicated, centralized logging platform. This platform handles aggregation, storage, searching, and analysis.
    *   **Key Components:**
        *   **Structured Logging:** Services emit logs as structured data (e.g., JSON) rather than plain text strings, including common fields like timestamp, log level, service name, correlation ID, user ID, etc.
        *   **Log Collection Agent:** A lightweight agent (e.g., Fluentd, Fluent Bit, Vector) runs as a sidecar or daemonset to collect logs from services/nodes.
        *   **Log Aggregation & Storage:** A central system like Elasticsearch, Loki, or a cloud provider service (AWS CloudWatch Logs, Google Cloud Logging, Azure Monitor Logs).
        *   **Log Visualization & Querying:** A tool like Kibana, Grafana (for Loki), or the cloud provider's console.
*   **Pros:**
    *   Centralized view of all logs.
    *   Powerful search, filtering, and analysis capabilities.
    *   Enables easy tracing of requests across services using correlation IDs.
    *   Long-term log retention and archival.
    *   Facilitates alerting based on log patterns.
    *   Improved developer productivity for troubleshooting.
*   **Cons:**
    *   Higher initial setup complexity and cost (for self-hosted solutions, or usage costs for cloud services).
    *   Requires services to adhere to structured logging practices.
    *   Potential performance overhead if logging is excessively verbose or synchronous.

## Decision Outcome

**Chosen Option:** Centralized Logging Platform with Structured Logging

**Reasoning:**
For a distributed microservices platform, a centralized logging strategy with structured logging is essential for effective observability and manageability. This approach provides the necessary tools to debug issues, monitor system health, and audit activity efficiently.

**Key Implementation Details:**

1.  **Structured Logging Format:** All services MUST emit logs in JSON format. A standard set of fields will be defined (e.g., `timestamp`, `level`, `service_name`, `instance_id`, `correlation_id`, `user_id`, `message`, `error_details`, `stack_trace`). NestJS logging capabilities can be configured for JSON output.
2.  **Correlation IDs:** A unique correlation ID MUST be generated at the entry point of a request (e.g., API Gateway or first service) and propagated through all subsequent service calls (via HTTP headers or message metadata). This ID must be included in every log entry related to that request.
3.  **Log Levels:** Standard log levels (e.g., `DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`) will be used consistently. Log levels should be configurable per environment.
4.  **Chosen Platform (Initial Recommendation):**
    *   **Log Collection:** Fluent Bit (due to its lightweight nature and performance) deployed as a DaemonSet in Kubernetes.
    *   **Log Aggregation & Storage:** Elasticsearch (proven, powerful, good ecosystem).
    *   **Log Visualization & Querying:** Kibana.
    *   This is often referred to as the "EFK Stack" (Elasticsearch, Fluent Bit, Kibana). Cloud-native alternatives (e.g., AWS OpenSearch with CloudWatch Logs, Grafana Loki) will also be considered based on cloud provider choice and managed service offerings.
5.  **Asynchronous Logging:** Services should log asynchronously where possible to minimize performance impact on request processing. Logging libraries typically handle this.
6.  **Sensitive Data:** Personally Identifiable Information (PII) and other sensitive data MUST NOT be logged unless explicitly required for audit purposes and properly masked or tokenized according to security policies.

### Positive Consequences
*   Greatly improved ability to troubleshoot and debug issues in a distributed environment.
*   Centralized and searchable logs for all services.
*   Standardized log format enhances readability and automated analysis.
*   Enables effective performance monitoring and auditing.
*   Better operational insights into system behavior.

### Negative Consequences (and Mitigations)
*   **Initial Setup Overhead:** Setting up and maintaining a centralized logging stack (if self-hosted) requires effort.
    *   **Mitigation:** Leverage managed cloud services for logging (e.g., AWS OpenSearch Service, Google Cloud Logging) to reduce operational burden. Utilize Helm charts or IaC for deploying open-source stacks.
*   **Cost:** Storage and processing costs for log data.
    *   **Mitigation:** Implement appropriate log retention policies. Sample or reduce verbosity of `DEBUG` logs in production. Use cost-effective storage tiers for older logs.
*   **Discipline for Structured Logging:** Developers need to adhere to structured logging practices and include correlation IDs.
    *   **Mitigation:** Provide clear logging guidelines, libraries, and examples. Integrate linters or checks for logging practices.
*   **Performance Overhead of Logging:** If not implemented carefully, logging can impact application performance.
    *   **Mitigation:** Use asynchronous logging. Avoid excessive logging in hot paths. Control log verbosity via configurable log levels.

## Links

*   [ADR-001: Adoption of Microservices Architecture](./ADR-001-adoption-of-microservices-architecture.md)
*   [ADR-002: Adoption of Event-Driven Architecture](./ADR-002-adoption-of-event-driven-architecture.md) (Correlation IDs are also critical in event-driven flows)
*   [ADR-032: System-Wide Error Handling and Propagation Strategy](./ADR-032-system-wide-error-handling-propagation.md) (Defines error details to be logged)
*   (To be created) ADR-011: Monitoring and Alerting Strategy (Logging is a key input)
*   [E-commerce Platform: System Architecture Overview](../00-system-architecture-overview.md)

## Future Considerations

*   Selection of specific managed cloud service for logging if self-hosting EFK is deemed too burdensome.
*   Integration with a distributed tracing system (e.g., Jaeger, Zipkin) which complements logging by providing a visual trace of requests. Log entries should include trace IDs.
*   Automated log analysis and anomaly detection.
*   Defining detailed log retention and archival policies.

## Rejection Criteria

*   If the chosen centralized logging solution proves to be prohibitively expensive or complex to manage for the team's capabilities, and simpler cloud-native solutions are available that meet most needs.
*   If the performance impact of structured logging and log shipping becomes a significant bottleneck for services.
