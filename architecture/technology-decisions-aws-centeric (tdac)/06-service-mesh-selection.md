# Technology Decision: Service Mesh Selection

*   **Status:** Approved
*   **Date:** 2025-05-12 (Updated)
*   **Deciders:** Architecture Team, Lead Developers
*   **Consulted:** DevOps Team, Security Team
*   **Informed:** All Engineering Teams

## 1. Context & Scope

This document details the selection process for a specific service mesh technology for the e-commerce platform. The decision to adopt a service mesh was established in [ADR-040: Service Mesh & Network Policy](./../adr/ADR-040-service-mesh-network-policy.md).

The goal of this document is to evaluate leading service mesh solutions and choose the one that best fits the platform's requirements for secure, observable, and manageable inter-service communication within the Kubernetes environment.

Key benefits sought from the service mesh include:
*   Automated mTLS for secure service-to-service communication.
*   Fine-grained traffic management (e.g., routing, retries, timeouts, circuit breaking, canary deployments).
*   Enhanced observability (metrics, logs, traces) for microservice interactions.
*   Consistent enforcement of security and network policies.
*   Decoupling of network concerns from application code.

## 2. Decision Drivers for Specific Service Mesh Selection

The selection of a specific service mesh will be guided by the following drivers:

*   **Feature Set & Richness:** Comprehensive support for mTLS, advanced traffic routing (splitting, mirroring), resilience patterns (retries, circuit breakers, timeouts), rate limiting, and policy enforcement.
*   **Performance & Resource Overhead:** Impact on service latency and resource consumption (CPU, memory) of the control plane and data plane proxies.
*   **Ease of Installation, Configuration & Operation:** Simplicity of deployment on Kubernetes, quality of CLI and/or UI tools, clarity of documentation, and availability of managed service offerings or robust operator support.
*   **Community Support, Maturity & Adoption:** Size and activity of the open-source community, stability and maturity of the project, and breadth of adoption in the industry.
*   **Observability Integration:** Seamless integration with the platform's existing and planned observability stack (e.g., Prometheus for metrics, Grafana for dashboards, Jaeger/Zipkin for tracing, Elasticsearch/Fluent Bit for logs).
*   **Security Capabilities:** Strength of mTLS implementation, granularity of authorization policies, integration with external identity providers (e.g., Keycloak via OIDC), and overall security posture.
*   **Extensibility & Customization:** Ability to extend or customize functionality (e.g., custom Wasm plugins for Envoy-based meshes).
*   **Scalability:** Ability of the control plane and data plane to scale with the growth of services and traffic.

## 3. Considered Service Mesh Technologies

Based on ADR-040, the primary candidates considered are:

*   **Istio:** A feature-rich and widely adopted open-source service mesh. Provides extensive capabilities for traffic management, security, and observability.
*   **Linkerd:** Known for its simplicity, performance, and focus on essentials. Also a CNCF graduated project.
*   **AWS App Mesh:** A fully managed service mesh that provides application-level networking for microservices.

## 4. Decision Outcome

**Chosen Technology: AWS App Mesh**

After careful consideration and alignment with our platform's long-term requirements for secure, observable, and manageable inter-service communication within the AWS ecosystem, **AWS App Mesh** has been selected as the service mesh for our e-commerce platform.

## 5. Decision Rationale

AWS App Mesh is chosen over Istio and Linkerd due to the following key factors:

*   **Managed Control Plane:** AWS handles the provisioning, scaling, and patching of the App Mesh control plane, significantly reducing operational overhead compared to self-managing Istio or Linkerd. This aligns perfectly with our AWS-centric strategy ([ADR-006](./../adr/ADR-006-cloud-native-deployment-strategy.md)).
*   **AWS Ecosystem Integration:** App Mesh offers seamless integration with EKS, ECS, Fargate, Cloud Map, CloudWatch, X-Ray, and ACM, simplifying service discovery, observability, and certificate management within our chosen environment.
*   **Core Feature Set:** It provides the essential service mesh capabilities required by the platform, including mTLS, traffic routing (e.g., weighted targets for canary releases), resilience features (retries, timeouts - via Envoy configuration), and observability hooks.
*   **Envoy Data Plane:** Utilizes the battle-tested and performant Envoy proxy, consistent with other leading service meshes like Istio.
*   **Adequate for Needs:** The feature set is sufficient for the platform's current and foreseeable requirements for secure and observable inter-service communication.

## 6. Implementation & Operational Considerations

*   **Deployment:** App Mesh resources (Mesh, Virtual Nodes, Virtual Routers, Routes, Virtual Services) will be defined and managed using Infrastructure as Code (IaC) tools (e.g., AWS CDK, CloudFormation, or Terraform).
*   **Envoy Proxy Injection:** The App Mesh controller on EKS (or agent for ECS/EC2) will handle the automatic injection of the Envoy sidecar proxy into application pods/tasks based on namespace labeling or task definition configuration.
*   **Configuration:** Traffic routing, mTLS policies, and observability settings will be configured through App Mesh API objects.
*   **Observability:** Integrate App Mesh metrics with Amazon CloudWatch and Prometheus/Grafana, and traces with AWS X-Ray.
*   **Certificate Management:** Utilize AWS Certificate Manager (ACM) Private Certificate Authority or App Mesh's self-signed certificates for managing mTLS.
*   **Onboarding:** Services will be incrementally onboarded onto the mesh.

## 7. Alternatives Considered

*   **Istio:** Rejected due to the high operational overhead of managing the control plane, which conflicts with the managed services strategy.
*   **Linkerd:** Rejected as AWS App Mesh provides a managed control plane within the AWS ecosystem, offering a better strategic fit despite Linkerd's simplicity advantages over Istio.
*   **No Service Mesh:** Rejected as the benefits of standardized mTLS, traffic management, and observability provided by a mesh are deemed crucial for the platform's scale and complexity (as per ADR-040).

## 8. Consequences

*   **Benefits:**
    *   Reduced operational overhead for managing the service mesh control plane.
    *   Simplified integration with AWS observability and security services.
    *   Standardized approach to mTLS, traffic control, and service communication observability across EKS/ECS.
    *   Application developers are largely decoupled from network concerns.
*   **Drawbacks/Risks:**
    *   Vendor lock-in to AWS for the service mesh control plane (though the data plane uses Envoy).
    *   App Mesh feature set might evolve at a different pace than open-source alternatives like Istio.
    *   Requires learning the App Mesh API and concepts.

## 9. Open Issues & Future Considerations

*   Define standard IaC patterns for App Mesh resources.
*   Develop detailed onboarding guides for service teams.
*   Monitor performance overhead of the Envoy sidecars.
*   Evaluate advanced App Mesh features (e.g., Gateway Routes) as needed.

## 10. References

*   [ADR-006: Cloud Native Deployment Strategy](./../adr/ADR-006-cloud-native-deployment-strategy.md)
*   [ADR-040: Service Mesh & Network Policy](./../adr/ADR-040-service-mesh-network-policy.md)
*   [AWS App Mesh Documentation](https://aws.amazon.com/app-mesh/)
*   [AWS App Mesh User Guide](https://docs.aws.amazon.com/app-mesh/latest/userguide/what-is-app-mesh.html)
*   [Envoy Proxy Documentation](https://www.envoyproxy.io/docs/envoy/latest/)
