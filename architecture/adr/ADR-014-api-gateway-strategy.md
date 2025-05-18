# ADR-014: API Gateway Detailed Strategy and Selection

*   **Status:** Proposed
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (Lead Developers, DevOps/SRE Team, Security Team)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In our microservices architecture (ADR-001), client applications (web, mobile, third-party integrations) need a unified and secure way to access various backend services. Exposing individual microservices directly to clients can lead to several problems:
*   **Increased client-side complexity:** Clients need to know the locations and interfaces of multiple services.
*   **Chattiness:** Multiple round trips may be needed to fetch data for a single client view.
*   **Security concerns:** Exposing all services directly increases the attack surface and makes consistent security policy enforcement difficult.
*   **Cross-cutting concerns:** Implementing features like authentication/authorization (ADR-005), rate limiting, caching (ADR-009), and request logging (ADR-010) in each service leads to duplication and inconsistency.
*   **Protocol Mismatches:** Clients might prefer HTTP/REST, while internal services might use gRPC or other protocols.

An API Gateway addresses these issues by providing a single, managed entry point. This ADR focuses on defining the strategy for its use and selecting an appropriate API Gateway solution.

## Decision Drivers

*   **Simplified Client Interaction:** Provide a stable and unified API front-end for clients.
*   **Enhanced Security:** Centralize authentication, authorization, and threat protection.
*   **Improved Performance:** Enable response caching and reduce chattiness through request aggregation/composition.
*   **Operational Efficiency:** Centralize cross-cutting concerns like logging, monitoring, and rate limiting.
*   **Decoupling:** Insulate clients from backend service refactoring or changes in internal architecture.
*   **Scalability and Resilience:** The gateway itself must be scalable and resilient.
*   **Developer Productivity:** Provide tools and features that simplify API management.
*   **Cloud-Native Alignment:** Fit well with our Kubernetes-based deployment strategy (ADR-006).

## Considered Options

### Option 1: No API Gateway / Direct Client-to-Service Communication

*   **Description:** Clients communicate directly with each microservice.
*   **Pros:** Simplest initial setup for services.
*   **Cons:** Addresses none of the problems outlined in the context. Not viable for a production e-commerce platform. (Already implicitly rejected by the need for this ADR).

### Option 2: Custom-Built API Gateway

*   **Description:** Develop an in-house API Gateway tailored to specific needs.
*   **Pros:** Maximum flexibility and control.
*   **Cons:** Significant development and maintenance effort. Replicates features readily available in existing solutions. High risk and cost. Generally not recommended unless very unique requirements exist that off-the-shelf products cannot meet.

### Option 3: Managed Cloud Provider API Gateway

*   **Description:** Use a managed API Gateway service from our chosen cloud provider (e.g., AWS API Gateway, Google Cloud API Gateway, Azure API Management).
*   **Pros:**
    *   Deep integration with other cloud services (IAM, logging, monitoring).
    *   Reduced operational overhead (serverless or managed infrastructure).
    *   Pay-as-you-go pricing model.
    *   Often feature-rich.
*   **Cons:**
    *   Potential for vendor lock-in.
    *   Configuration and features might be specific to the cloud provider's ecosystem.
    *   Cost can escalate with high traffic if not managed carefully.

### Option 4: Self-Hosted Open Source or Commercial API Gateway

*   **Description:** Deploy and manage an existing API Gateway solution (open source like Kong, Tyk, Spring Cloud Gateway, Envoy-based; or commercial variants) on our Kubernetes cluster (ADR-006).
*   **Pros:**
    *   More control over the infrastructure and configuration.
    *   Often Kubernetes-native or with good Kubernetes integrations (e.g., Ingress Controllers).
    *   Can be more cost-effective at scale if managed efficiently.
    *   Portability across cloud environments (if using open source).
*   **Cons:**
    *   Higher operational overhead for deployment, scaling, and maintenance of the gateway itself.
    *   Requires expertise in the chosen gateway product.

## Decision Outcome

**Chosen Option:** Self-Hosted Open Source API Gateway, with a preference for **Kong Gateway (Open Source)** or a comparable **Envoy-based solution** running on Kubernetes. A managed cloud provider gateway will be a strong secondary consideration if initial operational capacity is limited.

**Reasoning:**

A self-hosted open-source API Gateway running on Kubernetes offers the best balance of control, flexibility, feature set, and alignment with our cloud-native strategy (ADR-006) and technology stack (Node.js/NestJS for services, which integrate well with standard REST/GraphQL APIs exposed via gateways).

*   **Kong Gateway (Open Source):**
    *   **Pros:** Mature, feature-rich (routing, plugins for authN/Z, rate limiting, transformations, logging, etc.), good performance, strong community, and good Kubernetes integration (Kong Ingress Controller). Its plugin architecture allows for extensibility.
    *   **Cons:** Can become complex to manage a large number of plugins or custom plugins.

*   **Envoy-based solutions (e.g., Contour, Emissary-ingress (formerly Ambassador Edge Stack), or Istio Gateway if a service mesh is adopted):**
    *   **Pros:** Envoy is a high-performance C++ proxy, very powerful and flexible. Solutions built on it are often highly configurable and integrate deeply with Kubernetes.
    *   **Cons:** Envoy itself can be complex to configure directly; usually managed via a control plane provided by the specific solution.

*   **Managed Cloud Provider Gateway (e.g., AWS API Gateway):** This remains a viable alternative, especially for rapid initial deployment or if the operational burden of self-hosting is too high initially. The trade-off is potential vendor lock-in and potentially higher costs at scale.

The final selection between Kong and an Envoy-based solution (or a managed service) will involve a more detailed PoC (Proof of Concept) focusing on ease of use for our primary use cases, performance, and community/enterprise support.

**Key Functions to be Leveraged:**

1.  **Request Routing:** Route incoming requests to appropriate backend services based on path, host, headers, etc.
2.  **Authentication & Authorization (Integration with ADR-005):** Offload JWT validation and potentially basic role checks. More complex authorization logic remains in services.
3.  **Rate Limiting:** Protect services from abuse and ensure fair usage.
4.  **Response Caching (Integration with ADR-009):** Cache responses from services to improve performance and reduce backend load.
5.  **Request/Response Transformation:** Adapt requests/responses if needed (e.g., protocol translation, minor data shaping). To be used sparingly to avoid tight coupling.
6.  **Logging & Monitoring (Integration with ADR-010, ADR-011):** Centralize access logs and metrics for traffic passing through the gateway.
7.  **API Schema Validation:** Optionally validate requests against OpenAPI schemas (ADR-007).

### Positive Consequences
*   Centralized API management and security enforcement.
*   Reduced complexity for client applications.
*   Improved system observability and control over API traffic.
*   Services are shielded from direct exposure, enhancing security and decoupling.

### Negative Consequences (and Mitigations)
*   **Single Point of Failure/Bottleneck:** If the gateway fails or becomes a bottleneck, all API traffic is affected.
    *   **Mitigation:** Deploy the gateway in a highly available, scalable configuration (multiple replicas in Kubernetes). Implement robust monitoring and auto-scaling for the gateway.
*   **Operational Overhead (for self-hosted):** Managing the gateway software, updates, and infrastructure.
    *   **Mitigation:** Choose a gateway with good Kubernetes operators/integrations. Invest in automation for deployment and management. Consider a managed service if overhead is a major concern.
*   **Increased Latency:** Adds an extra network hop.
    *   **Mitigation:** Choose a high-performance gateway. Optimize gateway configuration. The benefits of caching and reduced chattiness often outweigh this.
*   **Complexity:** Configuring and managing a feature-rich gateway can be complex.
    *   **Mitigation:** Start with essential features. Provide clear documentation and training. Use GitOps or IaC for managing gateway configuration.

## Links

*   [ADR-001: Adoption of Microservices Architecture](./ADR-001-adoption-of-microservices-architecture.md)
*   [ADR-005: JWT-based Authentication & Authorization](./ADR-005-jwt-based-authentication-authorization.md)
*   [ADR-006: Cloud-Native Deployment Strategy](./ADR-006-cloud-native-deployment-strategy.md)
*   [ADR-007: API-First Design Principle](./ADR-007-api-first-design-principle.md)
*   [ADR-009: Caching Strategy](./ADR-009-caching-strategy.md)
*   [ADR-010: Logging Strategy](./ADR-010-logging-strategy.md)
*   [E-commerce Platform: System Architecture Overview](../00-system-architecture-overview.md)

## Future Considerations

*   Deeper integration with a service mesh if one is adopted (e.g., Istio, Linkerd).
*   GraphQL endpoint aggregation at the gateway.
*   Web Application Firewall (WAF) capabilities.
*   PoC results for Kong vs. Envoy-based solutions.

## Rejection Criteria

*   If the chosen self-hosted solution proves too difficult to manage reliably within the team's operational capacity, a switch to a managed cloud provider gateway would be prioritized.
