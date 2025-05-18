# ADR-016: Configuration Management Strategy

*   **Status:** Proposed
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (Lead Developers, DevOps/SRE Team, Security Team)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

Microservices in our e-commerce platform require various configuration parameters to operate correctly. These include database connection strings (ADR-004), external service URLs, API keys for third-party services (e.g., payment gateways, shipping providers), feature flags, logging levels (ADR-010), cache settings (ADR-009), and other operational tunables. These configurations often vary across different deployment environments (development, testing, staging, production).

A robust configuration management strategy is needed to:
*   Securely store and manage sensitive configuration data (secrets).
*   Provide a consistent way for services to access their configuration.
*   Allow for environment-specific configurations.
*   Support easy updates to configurations without necessarily redeploying services.
*   Integrate with our CI/CD (ADR-012) and Kubernetes (ADR-006) infrastructure.

## Decision Drivers

*   **Security:** Protect sensitive data like API keys, passwords, and certificates.
*   **Consistency:** Ensure a standardized approach to configuration across all services.
*   **Manageability:** Simplify the process of updating and versioning configurations.
*   **Environment Parity:** Make it easy to promote configurations across environments while overriding specific values.
*   **Auditability:** Track changes to configurations.
*   **Developer Experience:** Make it straightforward for developers to work with configurations locally and in deployed environments.
*   **Dynamic Updates:** Allow some configurations to be updated at runtime without service restarts where appropriate and safe.

## Considered Options

### Option 1: Configuration Files Packaged with Service Artifacts

*   **Description:** Embed configuration files (e.g., JSON, YAML, .env) directly into the service's deployment artifact (e.g., Docker image).
*   **Pros:** Simple to get started. Configuration is versioned with the code.
*   **Cons:**
    *   Requires rebuilding and redeploying the service for every configuration change.
    *   Secrets are baked into images, which is a security risk if images are compromised or inappropriately shared.
    *   Poor for managing environment-specific overrides securely.

### Option 2: Environment Variables

*   **Description:** Configure services primarily through environment variables injected at runtime by the orchestration platform (Kubernetes).
*   **Pros:**
    *   Standard 12-factor app approach.
    *   Supported by virtually all languages/frameworks.
    *   Kubernetes provides mechanisms (ConfigMaps, Secrets) to inject them.
*   **Cons:**
    *   Can become unwieldy for a large number of configuration parameters.
    *   Not ideal for complex or hierarchical configuration structures.
    *   Secrets are still visible as environment variables within the running container (though better than baked into images).
    *   Limited support for dynamic updates without pod restarts (though some tools can help).

### Option 3: Kubernetes ConfigMaps and Secrets

*   **Description:** Use Kubernetes `ConfigMaps` for non-sensitive configuration data and `Secrets` for sensitive data. These can be mounted as files into pods or exposed as environment variables.
*   **Pros:**
    *   Native Kubernetes solution, integrates well with ADR-006.
    *   Separates configuration from application code/artifacts.
    *   Supports versioning and rollouts of ConfigMaps/Secrets.
    *   Secrets are stored encrypted at rest by Kubernetes (etcd encryption).
    *   Can be managed via GitOps (e.g., FluxCD, ArgoCD) alongside application manifests.
*   **Cons:**
    *   ConfigMaps and Secrets are scoped to a Kubernetes namespace.
    *   By default, updates to ConfigMaps/Secrets mounted as files can be dynamic, but those injected as environment variables require pod restarts. Tools like `Reloader` can monitor changes and trigger rolling updates.
    *   While Secrets are encrypted at rest in etcd, access control (RBAC) is crucial to protect them within the cluster. Base64 encoding for Secrets is for transport, not true encryption in terms of visibility within Kubernetes manifests.

### Option 4: External Centralized Configuration Store

*   **Description:** Use a dedicated external system for managing configurations (e.g., HashiCorp Consul KV, HashiCorp Vault, Spring Cloud Config Server, AWS Parameter Store, Azure App Configuration). Services fetch their configuration from this store at startup or runtime.
*   **Pros:**
    *   Centralized management of all configurations.
    *   Often provide advanced features like UI, versioning, auditing, dynamic updates, fine-grained access control.
    *   Vault is specifically designed for secrets management with strong encryption and access control features.
*   **Cons:**
    *   Adds another piece of infrastructure to manage, unless using a cloud provider's managed service.
    *   Services need client libraries or mechanisms to fetch configuration.
    *   Potential for increased startup latency if the config store is slow or unavailable (mitigated by caching).

## Decision Outcome

**Chosen Option:** A hybrid approach, primarily leveraging **Kubernetes ConfigMaps and Secrets**, with the potential to integrate a dedicated **Secrets Management solution like HashiCorp Vault** for more advanced secrets management as complexity grows or for ultra-sensitive material.

**Reasoning:**

1.  **Kubernetes ConfigMaps and Secrets (Primary):**
    *   This is the most Kubernetes-native approach and aligns well with our existing decisions (ADR-006, ADR-012 for GitOps).
    *   It provides good separation of concerns, handles both non-sensitive and sensitive data, and can be managed declaratively.
    *   Tools like `Reloader` can be used to monitor changes in ConfigMaps/Secrets and trigger automatic rolling updates of deployments, providing a degree of dynamic configuration.
    *   For most services and configuration types, this offers a good balance of features, security, and operational simplicity within the Kubernetes ecosystem.

2.  **HashiCorp Vault (Secondary, for advanced/ultra-sensitive secrets):**
    *   For secrets requiring stricter access controls, dynamic generation, leasing, or a more robust audit trail than Kubernetes Secrets offer by default, integrating Vault is a strong option.
    *   Vault can integrate with Kubernetes (e.g., Vault Agent Injector, CSI provider) to securely inject secrets into pods.
    *   This allows us to start with the simpler Kubernetes-native approach and graduate to Vault for specific use cases without a full paradigm shift for all configurations.

**Key Implementation Details:**

1.  **Non-Sensitive Configuration:**
    *   Stored in Kubernetes `ConfigMaps`.
    *   Organized per-service and per-environment (e.g., `user-service-config-dev`, `user-service-config-prod`).
    *   Mounted as files into service pods or injected as environment variables.
    *   Managed via Kustomize or Helm charts in our GitOps repository.
2.  **Sensitive Configuration (Secrets):**
    *   Stored in Kubernetes `Secrets`.
    *   Managed similarly to ConfigMaps (per-service, per-environment, via GitOps).
    *   **Crucially, raw secrets will NOT be committed directly to Git.** Instead, use a sealed secrets solution (e.g., Bitnami Sealed Secrets, Mozilla SOPS) or a GitOps-friendly secrets management tool that allows committing encrypted secrets to Git, which are then decrypted by a controller running in the cluster. This keeps Git as the source of truth while protecting secrets.
    *   Strict RBAC will be applied to limit access to Secrets within the cluster.
    *   Consider enabling etcd encryption for an additional layer of security at rest.
3.  **Dynamic Updates:**
    *   Where appropriate (e.g., feature flags, log levels), services should be designed to reload configuration from mounted ConfigMap/Secret files.
    *   Utilize tools like `Stakater Reloader` to watch for changes in ConfigMaps or Secrets and automatically trigger rolling restarts of associated Deployments/StatefulSets if services cannot reload configuration dynamically.
4.  **Local Development:**
    *   Developers will use local `.env` files or similar mechanisms that mirror the structure of ConfigMaps/Secrets for local development, but these files will NOT be committed to Git (except for non-sensitive, template/example files).
5.  **Vault Integration (Future/Advanced):**
    *   If/when Vault is introduced, services will use the Vault Agent sidecar or CSI driver to fetch secrets. Kubernetes service accounts will be used for authentication to Vault.

### Positive Consequences
*   Clear separation of configuration from code.
*   Secure management of secrets.
*   Configuration can be versioned and managed via GitOps.
*   Relatively simple for developers to work with, especially with Kubernetes-native tools.
*   Scalable approach that can evolve with the integration of more advanced tools like Vault.

### Negative Consequences (and Mitigations)
*   **Complexity of Sealed Secrets/GitOps Secrets:** Managing encrypted secrets in Git requires an additional controller and process.
    *   **Mitigation:** Choose a well-supported solution and document the process clearly. The security benefits outweigh this initial setup complexity.
*   **RBAC Configuration:** Requires careful setup of Kubernetes RBAC to protect ConfigMaps and Secrets.
    *   **Mitigation:** Follow the principle of least privilege. Regularly audit RBAC policies.
*   **Boilerplate for Mounting/Injecting:** Can lead to verbose Kubernetes manifests.
    *   **Mitigation:** Use Helm or Kustomize to template and manage this.
*   **Operational Overhead for Vault (if adopted):** Running and maintaining a Vault cluster.
    *   **Mitigation:** Start with Kubernetes Secrets and only adopt Vault when clear benefits for specific use cases are identified. Consider managed Vault offerings if self-hosting is too burdensome.

## Links

*   [ADR-004: PostgreSQL for Relational Data](./ADR-004-postgresql-for-relational-data.md)
*   [ADR-006: Cloud-Native Deployment Strategy](./ADR-006-cloud-native-deployment-strategy.md)
*   [ADR-009: Caching Strategy](./ADR-009-caching-strategy.md)
*   [ADR-010: Logging Strategy](./ADR-010-logging-strategy.md)
*   [ADR-012: CI/CD Strategy](./ADR-012-cicd-strategy.md)
*   [Kubernetes Documentation: ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
*   [Kubernetes Documentation: Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
*   [Bitnami Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
*   [HashiCorp Vault](https://www.vaultproject.io/)
*   [Stakater Reloader](https://github.com/stakater/Reloader)

## Future Considerations

*   Fully adopting GitOps for managing ConfigMap/Secret changes.
*   Integrating a dedicated feature flagging system if requirements become very complex.
*   Broader adoption of HashiCorp Vault for all secrets management.

## Rejection Criteria

*   If managing secrets securely via Kubernetes Secrets and a sealed secrets solution proves too cumbersome or insecure for our needs early on, the adoption of a full-fledged secrets management solution like Vault will be accelerated.
