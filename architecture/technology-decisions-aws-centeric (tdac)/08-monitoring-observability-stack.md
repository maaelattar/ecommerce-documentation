# Technology Decision: Monitoring and Observability Stack

*   **Status:** Accepted
*   **Date:** 2025-05-12
*   **Deciders:** Project Team
*   **Consulted:** Lead Developers, SRE/Ops Team
*   **Informed:** All technical stakeholders

## 1. Context and Scope

This document outlines the technology decisions for the comprehensive Monitoring and Observability stack for the e-commerce platform. It builds upon the foundational principles and decisions established in:

*   [ADR-010: Logging Strategy](./../adr/ADR-010-logging-strategy.md)
*   [ADR-011: Monitoring and Alerting Strategy](./../adr/ADR-011-monitoring-and-alerting-strategy.md)
*   [ADR-017: Distributed Tracing Strategy](./../adr/ADR-017-distributed-tracing-strategy.md)

The primary cloud provider for this platform is Amazon Web Services (AWS). Therefore, this document will focus on leveraging AWS-native and AWS-managed services where appropriate to meet our observability goals while balancing operational overhead, cost, and feature requirements.

The observability stack will cover three main pillars:
1.  **Logging:** Collection, aggregation, storage, and analysis of logs from all services and infrastructure components.
2.  **Metrics & Alerting:** Collection, storage, visualization of metrics, and alerting on predefined conditions and Service Level Objectives (SLOs).
3.  **Distributed Tracing:** End-to-end tracking of requests as they traverse multiple services.

## 2. Core Principles & Decisions Recap (from ADRs)

The following core principles and decisions from the referenced ADRs guide our technology choices:

*   **Centralized Observability:** All telemetry data (logs, metrics, traces) will be sent to a centralized platform.
*   **Structured Logging:** Logs MUST be in JSON format, including standard fields like `timestamp`, `level`, `service_name`, `correlation_id` (ADR-010).
*   **Correlation IDs:** Mandatory for tracing requests across services and events (ADR-010, ADR-017).
*   **Standard Log Levels:** Consistent use of `DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL` (ADR-010).
*   **Metrics - The Four Golden Signals:** Services MUST expose Latency, Traffic, Errors, and Saturation (ADR-011).
*   **Standardized Metrics Exposition:** Prometheus format for application metrics (ADR-011).
*   **Instrumentation Standard:** OpenTelemetry (OTel) for generating and collecting telemetry data (traces, metrics, and eventually logs) to ensure vendor-neutrality at the instrumentation layer (ADR-017).
*   **Alerting:** Based on SLO violations and critical error conditions, focusing on actionable alerts (ADR-011).

## 3. Chosen Observability Stack on AWS

Given AWS as the primary cloud provider, the following services and tools are selected to form the core of our observability stack:

### 3.1. Logging Solution

*   **Chosen Technologies:**
    *   **Log Aggregation & Storage:** Amazon OpenSearch Service (successor to Amazon Elasticsearch Service).
    *   **Log Collection:** Fluent Bit (deployed as a DaemonSet on Amazon EKS).
    *   **Log Visualization & Querying:** OpenSearch Dashboards (comes with Amazon OpenSearch Service).
*   **Rationale:**
    *   Amazon OpenSearch Service provides a managed, scalable, and powerful search and analytics engine compatible with Elasticsearch APIs, which aligns with the EFK stack recommendation in ADR-010. It offers robust querying capabilities via OpenSearch Dashboards (Kibana equivalent).
    *   Fluent Bit is lightweight, performant, and well-suited for log collection in Kubernetes environments. It can be configured to parse, enrich, and forward logs to Amazon OpenSearch Service.
    *   This combination offers more powerful querying and visualization than relying solely on AWS CloudWatch Logs, especially for complex troubleshooting scenarios, while still benefiting from a managed service for the backend.
*   **Key Configuration & Operational Aspects on AWS:**
    *   Fluent Bit will be configured with appropriate input plugins for container logs, parsers for JSON logs, and output plugins for Amazon OpenSearch Service.
    *   OpenSearch Service domains will be configured with appropriate instance types, storage, and security (VPC access, fine-grained access control).
    *   Log retention policies will be configured within OpenSearch Index State Management (ISM).
    *   IAM roles will be used for secure access between Fluent Bit and OpenSearch Service.

### 3.2. Metrics & Alerting Solution

*   **Chosen Technologies:**
    *   **Metrics Collection & Storage:** Amazon Managed Service for Prometheus (AMP).
    *   **Metrics Visualization:** Amazon Managed Grafana (AMG).
    *   **Alerting Engine:** Prometheus Alertmanager (self-managed on Amazon EKS, configured with AMP as a data source).
*   **Rationale:**
    *   AMP provides a fully managed, Prometheus-compatible metrics backend, reducing the operational overhead of managing Prometheus servers, storage, and scaling. It aligns with the Prometheus decision in ADR-011.
    *   AMG offers managed Grafana, simplifying deployment, patching, and scaling of Grafana for dashboarding and visualization, as recommended in ADR-011.
    *   Alertmanager remains a flexible and powerful open-source solution for handling alert routing, grouping, and deduplication. Running it on EKS allows customization while leveraging AMP for the core metrics data.
    *   This stack maintains compatibility with the Prometheus ecosystem (exporters, client libraries, Grafana dashboards) while offloading significant operational burden to AWS.
*   **Key Configuration & Operational Aspects on AWS:**
    *   Services will be instrumented using Prometheus client libraries (e.g., `nestjs-prometheus`) to expose metrics scraped by AMP (via AWS Distro for OpenTelemetry (ADOT) Collector or Prometheus server).
    *   ADOT Collector can be used for scraping Prometheus metrics and remote-writing to AMP.
    *   AMG will be configured with AMP as a data source. Standard dashboards will be developed.
    *   Alertmanager will be deployed on EKS, configured with alerting rules, and integrated with notification channels (e.g., Slack, PagerDuty via AWS SNS).
    *   IAM roles for secure access between components (EKS, ADOT, AMP, AMG).

### 3.3. Distributed Tracing Solution

*   **Chosen Technologies:**
    *   **Instrumentation:** OpenTelemetry (OTel) SDKs for all services, as decided in ADR-017.
    *   **Trace Collection:** AWS Distro for OpenTelemetry (ADOT) Collector (deployed as sidecar or DaemonSet on EKS).
    *   **Trace Backend (Storage & Visualization):** AWS X-Ray.
*   **Rationale:**
    *   OpenTelemetry provides vendor-neutral instrumentation, allowing flexibility for future backend changes.
    *   AWS X-Ray is a fully managed distributed tracing service that integrates well with other AWS services (API Gateway, Lambda, EC2, EKS) and can ingest OTel-formatted traces via the ADOT Collector.
    *   Using X-Ray reduces the operational overhead of managing a tracing backend like Jaeger, including its storage and scaling complexities.
    *   ADOT Collector facilitates sending OTel traces to X-Ray and can also export to other backends if needed in the future.
*   **Key Configuration & Operational Aspects on AWS:**
    *   Services will use OTel SDKs for auto and manual instrumentation.
    *   ADOT Collector will be configured with OTel Protocol (OTLP) receivers and an X-Ray exporter.
    *   Sampling rules will be configured in the OTel SDKs and/or the ADOT Collector to manage trace volume and cost, with further sampling capabilities in X-Ray.
    *   IAM roles for the ADOT Collector to write traces to X-Ray.
    *   X-Ray console will be used for visualizing traces and service maps.

## 4. Integration & Correlation Strategy

To ensure a cohesive observability experience, the three pillars will be integrated:

*   **Trace IDs in Logs:** All structured logs MUST include the `trace_id` (and `span_id` where applicable) originating from OpenTelemetry. This allows direct correlation from a log entry to the corresponding trace in AWS X-Ray.
*   **Linking between Tools:**
    *   From Grafana dashboards (AMG), provide links to OpenSearch Dashboards with pre-filtered queries based on time range, service name, and `trace_id` (if available in metrics metadata or annotations).
    *   From Grafana/OpenSearch Dashboards, provide links to AWS X-Ray traces by `trace_id`.
    *   Explore capabilities of OpenSearch Dashboards and Grafana to embed or link to X-Ray trace views directly.
*   **Unified Tagging:** Consistent tagging strategies for services and resources across AWS will help filter and correlate data in all observability tools.

## 5. Operational Considerations on AWS

*   **Identity and Access Management (IAM):** Least-privilege IAM roles and policies will be strictly enforced for all components (Fluent Bit, ADOT Collector, EKS pods, etc.) to access AWS services (OpenSearch, AMP, X-Ray, etc.).
*   **Cost Management:**
    *   Monitor costs associated with Amazon OpenSearch Service (instance hours, storage, data transfer), AMP (metrics ingestion, storage, queries), AMG (user licenses), and AWS X-Ray (trace ingestion, storage).
    *   Implement data retention policies for logs, metrics, and traces.
    *   Optimize sampling strategies for traces and potentially high-cardinality metrics.
    *   Utilize AWS Cost Explorer and set up budgets/alerts for observability services.
*   **Security:**
    *   Network security: Deploy services within VPCs, use security groups and network ACLs.
    *   Encryption: Enable encryption at rest and in transit for all observability data stores and communication channels.
    *   Compliance: Ensure the chosen services and configurations meet relevant compliance requirements.
*   **Infrastructure as Code (IaC):** All observability infrastructure (OpenSearch domains, AMP workspaces, AMG workspaces, EKS configurations for collectors/Alertmanager, IAM roles) will be managed using IaC (e.g., AWS CDK, Terraform, or CloudFormation).
*   **Scalability & Resilience:** Leverage the managed nature of AWS services for scalability and resilience. Configure EKS deployments for collectors and Alertmanager with appropriate resource requests/limits and replica counts.

## 6. Future Considerations

*   **Log-based Metrics:** Explore generating metrics from logs using Amazon OpenSearch Service or CloudWatch Logs Metric Filters if specific metrics are easier to derive from log events.
*   **CloudWatch Synthetics:** For proactive end-to-end black-box monitoring of critical user flows.
*   **AWS CloudWatch Anomaly Detection:** Leverage machine learning for anomaly detection on metrics stored in CloudWatch (if a hybrid approach is used) or explore similar capabilities within AMP/AMG or OpenSearch.
*   **Service Level Indicators (SLIs) & SLOs:** Continuously refine SLIs and SLOs, and build comprehensive dashboards and alerts around them.
*   **Unified Observability Platform:** Explore if future AWS offerings or third-party solutions provide a more deeply integrated single-pane-of-glass experience across logs, metrics, and traces, building on the OpenTelemetry standard.

## 7. References

*   [ADR-010: Logging Strategy](./../adr/ADR-010-logging-strategy.md)
*   [ADR-011: Monitoring and Alerting Strategy](./../adr/ADR-011-monitoring-and-alerting-strategy.md)
*   [ADR-017: Distributed Tracing Strategy](./../adr/ADR-017-distributed-tracing-strategy.md)
*   [Amazon OpenSearch Service Documentation](https://aws.amazon.com/opensearch-service/)
*   [Amazon Managed Service for Prometheus (AMP) Documentation](https://aws.amazon.com/prometheus/)
*   [Amazon Managed Grafana (AMG) Documentation](https://aws.amazon.com/grafana/)
*   [AWS X-Ray Documentation](https://aws.amazon.com/xray/)
*   [AWS Distro for OpenTelemetry (ADOT) Documentation](https://aws-otel.github.io/)
*   [Fluent Bit Documentation](https://fluentbit.io/)
*   [OpenTelemetry Documentation](https://opentelemetry.io/)
