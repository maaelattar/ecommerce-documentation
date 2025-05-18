# ADR-017: Distributed Tracing Strategy

*   **Status:** Proposed
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (Lead Developers, DevOps/SRE Team)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In our microservices architecture (ADR-001), a single client request (e.g., placing an order, searching for products) can trigger a chain of calls across multiple internal services. When issues arise, such as high latency or errors, it becomes challenging to pinpoint the exact service or operation causing the problem. Traditional logging (ADR-010) and metrics (ADR-011) provide valuable insights into individual services but may not easily show the end-to-end flow and inter-service dependencies for a specific request.

Distributed tracing provides a way to track the progression of a single request as it moves through the various services, assigning unique IDs to requests and their sub-operations (spans) to reconstruct the entire call graph. This ADR aims to define our strategy for implementing distributed tracing.

## Decision Drivers

*   **Improved Debugging:** Quickly identify bottlenecks and sources of errors in distributed workflows.
*   **Performance Analysis:** Understand latency contributions from different services and network hops.
*   **Dependency Visualization:** Gain insights into service interactions and dependencies.
*   **Root Cause Analysis:** More effectively determine the root cause of failures in complex distributed systems.
*   **Enhanced Observability:** Complement logging and metrics to provide a comprehensive view of system behavior.
*   **Developer Productivity:** Reduce the time spent diagnosing issues in microservices.

## Considered Options

### Option 1: No Distributed Tracing

*   **Description:** Rely solely on logs and metrics for debugging and performance analysis.
*   **Pros:** No additional instrumentation or infrastructure setup required.
*   **Cons:** Extremely difficult to trace requests across multiple services. Time-consuming to correlate logs from different services. Poor visibility into end-to-end latency and dependencies. Not suitable for a complex microservices platform.

### Option 2: Custom Tracing Implementation

*   **Description:** Develop an in-house solution for generating, propagating, and collecting trace data.
*   **Pros:** Full control over the implementation.
*   **Cons:** Extremely complex and resource-intensive to build and maintain. Replicates functionality available in mature open-source and commercial solutions. High risk of an incomplete or inefficient solution.

### Option 3: Adopt an Open Standard and Open Source Tooling

*   **Description:** Standardize on an open tracing specification like **OpenTelemetry (OTel)** and use compatible open-source backend systems for collecting, storing, and visualizing traces (e.g., **Jaeger**, **Zipkin**).
    *   **OpenTelemetry:** Provides a vendor-neutral set of APIs, SDKs, and tools for generating, collecting, and exporting telemetry data (traces, metrics, logs). It supports auto-instrumentation for many popular frameworks and libraries.
    *   **Jaeger:** An open-source, end-to-end distributed tracing system, graduated CNCF project.
    *   **Zipkin:** Another popular open-source distributed tracing system.
*   **Pros:**
    *   Vendor-neutrality and broad industry support (OpenTelemetry).
    *   Rich ecosystem of instrumentation libraries and integrations.
    *   Mature and feature-rich backend systems (Jaeger, Zipkin).
    *   Active communities and good documentation.
    *   Avoids vendor lock-in for instrumentation.
*   **Cons:**
    *   Requires deploying and managing the chosen backend tracing system (unless a managed service is used).
    *   Instrumentation effort is still required, though OpenTelemetry auto-instrumentation helps.

### Option 4: Vendor-Specific APM Solution with Tracing

*   **Description:** Use a commercial Application Performance Monitoring (APM) solution (e.g., Datadog, Dynatrace, New Relic, Elastic APM) that includes distributed tracing capabilities.
*   **Pros:**
    *   Often provides a more integrated and polished user experience.
    *   May offer advanced analytics and AI-powered insights.
    *   Managed service, reducing operational overhead for the tracing backend.
    *   Usually includes support for logs and metrics as well, providing a unified observability platform.
*   **Cons:**
    *   Can be expensive, especially at scale.
    *   Potential for vendor lock-in (instrumentation might be proprietary or heavily tied to the vendor's agent).
    *   Less flexibility if specific customization is needed.

## Decision Outcome

**Chosen Option:** Adopt **OpenTelemetry (OTel)** for instrumentation and initially use **Jaeger** as the open-source backend for trace collection, storage, and visualization.

**Reasoning:**

*   **OpenTelemetry (Instrumentation):**
    *   Standardizing on OpenTelemetry for generating trace data provides maximum flexibility and avoids vendor lock-in at the instrumentation layer. Its auto-instrumentation capabilities for Node.js/NestJS (ADR-003) and other common libraries will accelerate adoption.
    *   OTel allows us to export data to various backends, so if we decide to switch from Jaeger to another system (open source or commercial) in the future, the instrumentation in our services can remain largely unchanged.
*   **Jaeger (Backend):**
    *   Jaeger is a mature, CNCF-graduated project with a rich feature set for distributed tracing.
    *   It integrates well with Kubernetes (ADR-006) and is commonly used with OpenTelemetry.
    *   It can be self-hosted, giving us control, or some cloud providers offer managed Jaeger instances.
    *   Starting with an open-source backend like Jaeger allows us to gain experience with distributed tracing and understand our needs before committing to potentially expensive commercial solutions.

**Key Implementation Details:**

1.  **Instrumentation with OpenTelemetry:**
    *   All microservices will be instrumented using OpenTelemetry SDKs.
    *   Leverage auto-instrumentation for common frameworks (e.g., Express.js within NestJS, HTTP clients, database clients) where available and effective.
    *   Manual instrumentation will be added for custom business logic or to enrich spans with relevant attributes (e.g., user ID, order ID).
    *   Trace context (trace ID, span ID) will be propagated across service boundaries (e.g., via HTTP headers like W3C Trace Context). The API Gateway (ADR-014) will also participate in trace propagation.
2.  **Trace Collection:**
    *   The OpenTelemetry Collector will be deployed (likely as a sidecar or daemonset in Kubernetes) to receive trace data from services and export it to Jaeger. The collector can also be used for batching, filtering, and retrying exports.
3.  **Jaeger Deployment:**
    *   A Jaeger backend (Collector, Query Service, UI, and storage like Elasticsearch or Cassandra) will be deployed within our Kubernetes cluster.
    *   For initial deployment, an all-in-one Jaeger deployment might be used for simplicity, graduating to a more scalable, production-grade deployment as needed.
4.  **Sampling:**
    *   Initially, a probabilistic head-based sampling strategy (e.g., trace 1% or 10% of requests) will be configured in the OpenTelemetry SDKs or Collector to manage the volume of trace data.
    *   As we gain experience, more sophisticated sampling strategies (e.g., adaptive sampling, tail-based sampling if supported by chosen components) may be considered.
5.  **Integration with Logging & Monitoring:**
    *   Trace IDs will be included in structured logs (ADR-010) to allow correlation between traces and logs.
    *   Metrics from services (ADR-011) can be correlated with trace data to provide deeper insights.
6.  **Developer Training:** Developers will be trained on how to use OpenTelemetry for instrumentation and Jaeger for analyzing traces.

### Positive Consequences
*   Significantly improved ability to debug and troubleshoot issues in the distributed system.
*   Better understanding of system performance and inter-service dependencies.
*   Reduced mean time to resolution (MTTR) for incidents.
*   Standardized approach to tracing instrumentation.

### Negative Consequences (and Mitigations)
*   **Instrumentation Effort:** Instrumenting all services requires developer effort.
    *   **Mitigation:** Prioritize instrumentation for critical services and flows. Maximize use of auto-instrumentation. Provide clear guidelines and examples.
*   **Performance Overhead:** Collecting and processing trace data can add some performance overhead.
    *   **Mitigation:** Use efficient OpenTelemetry SDKs and Collector configurations. Implement appropriate sampling to reduce data volume. Monitor the overhead.
*   **Operational Overhead for Jaeger:** Self-hosting Jaeger requires managing its deployment, scaling, and data storage.
    *   **Mitigation:** Start with a simpler Jaeger deployment. Automate its deployment and management using Kubernetes operators or Helm charts. Consider a managed Jaeger service if self-hosting becomes too burdensome.
*   **Data Storage Costs:** Storing trace data can consume significant storage.
    *   **Mitigation:** Implement effective sampling. Configure appropriate data retention policies in Jaeger. Choose a cost-effective storage backend for Jaeger.

## Links

*   [ADR-001: Adoption of Microservices Architecture](./ADR-001-adoption-of-microservices-architecture.md)
*   [ADR-003: Node.js with NestJS for Initial Services](./ADR-003-nodejs-nestjs-for-initial-services.md)
*   [ADR-006: Cloud-Native Deployment Strategy](./ADR-006-cloud-native-deployment-strategy.md)
*   [ADR-010: Logging Strategy](./ADR-010-logging-strategy.md) (Trace IDs included in logs)
*   [ADR-032: System-Wide Error Handling and Propagation Strategy](./ADR-032-system-wide-error-handling-propagation.md) (Exposing Trace ID in error responses)
*   [ADR-011: Monitoring and Alerting Strategy](./ADR-011-monitoring-and-alerting-strategy.md)
*   [ADR-014: API Gateway Detailed Strategy and Selection](./ADR-014-api-gateway-strategy.md)
*   [OpenTelemetry](https://opentelemetry.io/)
*   [Jaeger Tracing](https://www.jaegertracing.io/)
*   [W3C Trace Context](https://www.w3.org/TR/trace-context/)

## Future Considerations

*   Adopting tail-based sampling for more intelligent capture of interesting traces.
*   Integrating metrics and logs more deeply within the tracing UI (e.g., Jaeger UI linking to logs/metrics for a given trace).
*   Exploring commercial APM solutions if the benefits outweigh the costs and operational efforts of self-managed tools, leveraging our OTel instrumentation.

## Rejection Criteria

*   If the operational overhead of self-hosting Jaeger proves too high before significant value is demonstrated, or if performance overhead is unacceptable, a managed tracing solution or a different open-source backend might be evaluated sooner.
