# ADR-015: Service Discovery Mechanism

*   **Status:** Proposed
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (Lead Developers, DevOps/SRE Team)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In our microservices architecture (ADR-001), deployed on Kubernetes (ADR-006), services need to discover and communicate with each other. Service instances are ephemeral; they can be scaled up or down, restarted, or rescheduled, meaning their network locations (IP addresses and ports) are dynamic. Hardcoding these locations is not feasible and would lead to a brittle system. A robust service discovery mechanism is required to allow services to find each other reliably without manual intervention.

## Decision Drivers

*   **Reliability:** Ensure dependable communication between services even as instances change.
*   **Dynamic Scaling:** Support automatic discovery of new service instances as they scale.
*   **Decoupling:** Services should not need to be aware of the specific physical locations of other services.
*   **Simplicity:** The chosen mechanism should be as simple as possible to use and manage.
*   **Integration with Orchestration:** Leverage capabilities provided by our chosen orchestration platform (Kubernetes).
*   **Performance:** Discovery lookups should be fast and efficient.

## Considered Options

### Option 1: Static Configuration (IPs/DNS names in config files)

*   **Description:** Manually configure the network locations of dependent services in each service's configuration.
*   **Pros:** Extremely simple for a very small, static number of services.
*   **Cons:** Completely unmanageable and brittle in a dynamic microservices environment. Does not support auto-scaling or instance failures. Unsuitable.

### Option 2: Client-Side Discovery

*   **Description:** Clients (services making requests) query a central service registry (e.g., Netflix Eureka, HashiCorp Consul) to get a list of available instances for a target service, then perform client-side load balancing.
*   **Pros:** Gives clients more control over load balancing.
*   **Cons:**
    *   Requires a discovery library/logic in each client service, potentially for multiple languages.
    *   Increases client complexity.
    *   Requires managing a separate service registry infrastructure unless provided by the platform.

### Option 3: Server-Side Discovery (Platform-Provided)

*   **Description:** The underlying platform (e.g., Kubernetes) provides a built-in service discovery mechanism. Clients typically make requests to a stable virtual IP or DNS name managed by the platform, which then load balances requests to available service instances.
*   **Pros:**
    *   Leverages existing platform capabilities, reducing extra infrastructure.
    *   Simplifies client logic as they only need to know a stable service name.
    *   Often well-integrated with the platform's networking and health checking.
*   **Cons:** Relies on the specific platform's implementation; less portable if moving off that platform (though a common pattern).

### Option 4: Dedicated External Service Discovery Tool (e.g., HashiCorp Consul, Apache Zookeeper, CoreDNS as a standalone)

*   **Description:** Implement and manage a dedicated service discovery tool, separate from or integrated with Kubernetes. Services register themselves with this tool and query it to find other services.
*   **Pros:**
    *   Can offer advanced features like health checking, distributed key-value store, etc.
    *   Can work across different environments or clusters if needed.
*   **Cons:**
    *   Adds another piece of infrastructure to manage, monitor, and scale.
    *   Can be redundant if the orchestration platform already provides good-enough service discovery (like Kubernetes).
    *   Requires services to integrate with the tool's client libraries or APIs.

## Decision Outcome

**Chosen Option:** Server-Side Discovery provided by **Kubernetes-native Service Discovery**.

**Reasoning:**
Given our commitment to Kubernetes for cloud-native deployment (ADR-006), leveraging its built-in service discovery mechanism is the most straightforward, integrated, and operationally efficient approach. Kubernetes Services provide stable virtual IPs and DNS names that automatically load balance traffic to healthy pods (service instances). This abstracts the dynamic nature of pod IPs and ports from client services.

This approach aligns with the principle of leveraging platform capabilities where they meet our needs, minimizing the need for additional complex components.

**Key Implementation Details:**

1.  **Kubernetes Services:**
    *   Each microservice deployment will be exposed internally within the cluster via a Kubernetes `Service` of type `ClusterIP`. This provides a stable internal IP address and DNS name.
    *   The DNS name will follow the Kubernetes standard: `<service-name>.<namespace>.svc.cluster.local`. Services will typically use the short form `<service-name>` if communicating within the same namespace, or `<service-name>.<namespace>` if in different namespaces.
2.  **DNS Resolution:** Kubernetes provides internal DNS (usually CoreDNS) that resolves these service names to the `ClusterIP` of the Service.
3.  **Kube-proxy:** Kube-proxy, running on each node, programs `iptables` (or IPVS) rules to transparently route traffic destined for a Service's `ClusterIP` and port to one of the healthy backend Pods selected by the Service's selector.
4.  **Selectors and Labels:** Kubernetes Services use selectors and labels to dynamically identify the set of Pods that provide a particular service.
5.  **Health Checks:** Kubernetes readiness and liveness probes will be configured for each service (Pod) to ensure traffic is only routed to healthy instances.
6.  **Configuration:** Services will be configured to address their dependencies using these stable Kubernetes DNS service names.

### Positive Consequences
*   **Simplicity:** No extra service discovery components to install or manage beyond Kubernetes itself.
*   **Reliability:** Leverages Kubernetes' robust mechanisms for service exposure and load balancing.
*   **Dynamic:** Automatically adapts to scaling events, deployments, and failures.
*   **Standardization:** Uses a well-understood and standard Kubernetes pattern.
*   **Developer Experience:** Developers only need to know the service DNS name, not worry about instance IPs.

### Negative Consequences (and Mitigations)
*   **Platform Lock-in (to Kubernetes):** This specific mechanism is tied to Kubernetes.
    *   **Mitigation:** This is an acceptable trade-off given our strategic decision to use Kubernetes (ADR-006). If we ever migrated off Kubernetes, service discovery would need to be re-evaluated.
*   **DNS Caching Issues (Rare):** Standard DNS caching behaviors can sometimes cause delays in picking up changes if not configured properly within application runtimes.
    *   **Mitigation:** Most modern HTTP clients and gRPC libraries used within Kubernetes are aware of this and handle DNS resolution appropriately for service discovery. Ensure application stacks respect DNS TTLs or use clients designed for Kubernetes environments.

## Links

*   [ADR-001: Adoption of Microservices Architecture](./ADR-001-adoption-of-microservices-architecture.md)
*   [ADR-006: Cloud-Native Deployment Strategy](./ADR-006-cloud-native-deployment-strategy.md)
*   [Kubernetes Documentation: Service](https://kubernetes.io/docs/concepts/services-networking/service/)
*   [Kubernetes Documentation: DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)

## Future Considerations

*   **Service Mesh:** If a service mesh (e.g., Istio, Linkerd) is adopted in the future for more advanced traffic management, security, or observability, it will typically integrate with or enhance Kubernetes service discovery, often providing its own more sophisticated mechanisms on top. This ADR would then be revisited or superseded by an ADR for the service mesh.
*   **Cross-Cluster Service Discovery:** If the application needs to span multiple Kubernetes clusters, a more advanced solution might be required (e.g., Submariner, KubeFed, or specific service mesh capabilities). This is not an immediate requirement.

## Rejection Criteria

*   If basic Kubernetes service discovery proves insufficient for complex routing needs that cannot be addressed by an API Gateway (ADR-014) or Ingress controllers, and a service mesh is not yet justified, other options might be revisited. This is considered unlikely for initial requirements.
