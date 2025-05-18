# ADR-047: Secrets Management Strategy for Kubernetes Applications

*   **Status:** Proposed
*   **Date:** 2025-05-19
*   **Deciders:** [Architecture Review Board, Lead Developers] (Placeholder, can be confirmed)
*   **Consulted:** [Relevant stakeholders, e.g., Security Team, DevOps Team] (Placeholder)
*   **Informed:** [Wider engineering team] (Placeholder)

## Context and Problem Statement

The e-commerce platform, built on a microservices architecture (ADR-001) and deployed to Kubernetes on AWS (ADR-006), requires a robust and secure method for managing application secrets. These secrets include database credentials, API keys for third-party services, internal service-to-service authentication tokens, and other sensitive configuration data.

Currently, there is no formally adopted platform-wide strategy for managing these secrets in a way that is:
*   Highly secure (encrypted at rest and in transit, with strong access controls).
*   Compatible with GitOps principles (ADR-012), where configurations are declaratively managed in Git.
*   Scalable for a growing number of microservices and secrets.
*   Supportive of secret lifecycle management, including rotation and auditing.
*   Easy for developers to use correctly and consistently.

Managing secrets directly as unencrypted Kubernetes `Secret` manifests in Git is insecure. Relying solely on native Kubernetes `Secret` objects without a higher-level management system means secrets are typically Base64 encoded (not truly encrypted at rest within etcd without further cluster configuration) and lacks features like rotation, versioning, and fine-grained audit trails. A standardized solution is needed to address these challenges and ensure a secure and auditable secrets management practice.

## Decision Drivers

The selection of a secrets management strategy will be guided by the following key drivers:

*   **Security:** Strength of encryption (at rest, in transit), robust access control mechanisms (enforcing least privilege), protection against unauthorized disclosure, and overall contribution to the platform's security posture.
*   **GitOps Compatibility:** Seamless integration with a GitOps workflow, allowing secrets (or references to them) to be declaratively managed and version-controlled in Git, enabling automated and auditable deployment via tools like Argo CD.
*   **Ease of Use & Developer Experience:** Simplicity for developers to securely access secrets required by their applications, and for operators to manage the secrets infrastructure with minimal friction in daily workflows.
*   **Centralized Management & Auditability:** Ability to manage secrets from a central point, track versions, monitor access, and provide comprehensive audit trails for security analysis and compliance reporting.
*   **Secret Lifecycle Management:** Native or easily integrable support for the complete lifecycle of secrets, including secure generation, distribution, rotation (automated where possible), and revocation.
*   **Integration with AWS Ecosystem:** Effective leverage of and integration with existing AWS services such as IAM (for authentication/authorization), KMS (for envelope encryption), and CloudTrail (for auditing), aligning with the platform's AWS foundation.
*   **Scalability:** The solution must scale to support a growing number of microservices, secrets, and access requests without significant performance degradation or operational burden.
*   **Cost-Effectiveness:** Consideration of the total cost of ownership, including software licenses (if any), infrastructure requirements, operational effort, and any associated cloud service fees.
*   **Maturity & Community Support:** Preference for well-established, stable solutions with strong community backing, comprehensive documentation, and readily available support channels.

## Considered Options

Several options were considered for managing secrets within the Kubernetes environment:

### 1. Kubernetes Native Secrets with Manual/Git-based Management

*   **Description:** Storing Kubernetes `Secret` manifests directly in Git, potentially with values Base64 encoded. Secrets are applied via `kubectl apply` or a GitOps controller.
*   **Pros:**
    *   Simple to understand for basic Kubernetes users.
    *   No additional tooling required beyond `kubectl` and Git.
*   **Cons:**
    *   **Security:** Base64 encoding is not encryption; secret values are effectively plaintext in Git if not externally encrypted. Secrets are unencrypted at rest in etcd by default unless etcd encryption is specifically configured.
    *   **GitOps Compatibility:** Poor, as plaintext secrets should not be in Git.
    *   **Lifecycle Management:** No built-in support for rotation, versioning, or fine-grained auditing beyond Git history.
    *   **Developer Experience:** Prone to accidental exposure of secrets.
    *   **Centralized Management:** Lacks a central point of control or audit outside of K8s itself.

### 2. Bitnami Sealed Secrets

*   **Description:** A Kubernetes controller and a CLI tool (`kubeseal`) that encrypt Kubernetes `Secret` manifests into a `SealedSecret` Custom Resource. The `SealedSecret` (containing encrypted data) is safe to store in Git. The in-cluster controller decrypts the `SealedSecret` into a native Kubernetes `Secret` using a private key stored securely within the cluster.
*   **Pros:**
    *   **GitOps Compatibility:** Excellent; designed specifically for storing encrypted secrets in Git.
    *   **Security:** Strong encryption of secret data intended for Git.
    *   **Ease of Use:** Relatively simple to understand and integrate into a GitOps workflow for K8s-specific secrets.
    *   **Kubernetes-Native:** Works by extending Kubernetes with a CRD.
*   **Cons:**
    *   **Lifecycle Management:** Does not inherently provide advanced features like automatic secret rotation, versioning (beyond Git history of the `SealedSecret`), or complex access policies for the secrets themselves (relies on K8s RBAC for the controller's key).
    *   **Centralized Management:** Management is decentralized (per `SealedSecret` file); auditing is primarily via Git and K8s events.
    *   **Scope:** Primarily focused on secrets consumed *within* the Kubernetes cluster. Less direct integration for secrets needed by external AWS services.
    *   **Key Management:** The security of the controller's private key is paramount; requires careful backup and recovery strategy.

### 3. AWS Secrets Manager with External Secrets Operator (ESO)

*   **Description:** AWS Secrets Manager is a managed AWS service for storing, managing, and rotating secrets. The External Secrets Operator (ESO) is a Kubernetes operator that synchronizes secrets from AWS Secrets Manager (and other external providers) into native Kubernetes `Secret` objects. Developers define an `ExternalSecret` CRD in Git, which tells ESO where to fetch the secret data from AWS Secrets Manager.
*   **Pros:**
    *   **Security:** Leverages AWS's robust security infrastructure, including IAM for access control, KMS for encryption, and CloudTrail for auditing. Secrets are not stored in Git.
    *   **Centralized Management & Auditability:** Provides a central dashboard for managing secrets, their versions, and access policies, with detailed audit logs via CloudTrail.
    *   **Lifecycle Management:** Strong support for automatic secret rotation (especially for AWS services like RDS) and versioning.
    *   **Integration with AWS Ecosystem:** Native integration with other AWS services. Secrets stored can be consumed by both K8s and non-K8s AWS resources.
    *   **GitOps Compatibility:** `ExternalSecret` CRDs are declarative and can be stored in Git, aligning with GitOps.
    *   **Scalability:** Managed service designed for scalability and reliability.
*   **Cons:**
    *   **AWS Dependency:** Tightly coupled to the AWS ecosystem and AWS Secrets Manager.
    *   **Complexity:** Requires deploying and managing ESO in the cluster. Initial setup involves configuring IAM roles (e.g., IRSA).
    *   **Cost:** Incurs costs for AWS Secrets Manager usage (per secret stored and per API call, though often modest).
    *   **Learning Curve:** Requires understanding AWS Secrets Manager, IAM policies, and the ESO CRDs.

## Decision Outcome

**Chosen Option:** **AWS Secrets Manager integrated with Kubernetes via the External Secrets Operator (ESO)** is selected as the primary secrets management strategy for applications deployed on the Kubernetes platform.

This approach involves:
1.  Storing all application secrets (e.g., database credentials, API keys, certificates) centrally within AWS Secrets Manager.
2.  Utilizing features of AWS Secrets Manager for lifecycle management, including rotation, versioning, and fine-grained access control using IAM.
3.  Deploying the External Secrets Operator (ESO) to each Kubernetes cluster.
4.  Defining `ExternalSecret` Custom Resources (CRs) within application Helm charts or Kustomize overlays. These CRs will be stored in Git and specify which secrets to fetch from AWS Secrets Manager and how to map them into native Kubernetes `Secret` objects.
5.  Applications will consume these native Kubernetes `Secret` objects in a standard way (e.g., as environment variables or mounted files).

## Reasoning

The decision to adopt AWS Secrets Manager with the External Secrets Operator is based on a comprehensive evaluation against the defined decision drivers and the specific needs of the e-commerce platform:

*   **Security:** AWS Secrets Manager provides robust security features, including encryption at rest (via KMS), encryption in transit, fine-grained access control through IAM, and detailed auditing via CloudTrail. This aligns with our top security requirements. Secrets are not stored in Git, reducing the risk of accidental exposure.
*   **Centralized Management & Auditability:** AWS Secrets Manager offers a centralized platform for managing all secrets, their versions, and access policies. CloudTrail integration provides comprehensive audit logs, crucial for compliance and security monitoring.
*   **Secret Lifecycle Management:** AWS Secrets Manager excels in managing the entire lifecycle of secrets, notably with its built-in capabilities for automatic rotation of secrets for many AWS services (like RDS) and extensibility for custom rotation logic. This significantly reduces the operational burden and improves security posture compared to options without native rotation.
*   **Integration with AWS Ecosystem:** As the platform is built on AWS (ADR-006), leveraging AWS Secrets Manager allows for seamless integration with other AWS services and IAM for consistent access control. This is a significant advantage.
*   **GitOps Compatibility:** The External Secrets Operator enables a strong GitOps workflow. `ExternalSecret` CRs are declarative, version-controlled in Git, and managed by Argo CD, while the actual sensitive values remain securely in AWS Secrets Manager. This strikes an excellent balance.
*   **Scalability:** AWS Secrets Manager is a managed service designed for high availability and scalability, suitable for a growing e-commerce platform.
*   **Maturity & Community Support:** Both AWS Secrets Manager and the External Secrets Operator are mature, well-documented solutions with strong community backing.

While Bitnami Sealed Secrets offers excellent GitOps compatibility for encrypting secrets directly in Git, it lacks the centralized management, advanced lifecycle features (especially rotation), and deep AWS integration that AWS Secrets Manager provides. The manual management of Kubernetes secrets was dismissed due to its inherent security risks and lack of advanced features.

The slightly higher initial complexity of setting up ESO and configuring IAM roles is considered a worthwhile trade-off for the long-term benefits in security, manageability, and scalability. The cost associated with AWS Secrets Manager is deemed acceptable for the value it provides.

## Consequences

### Positive Consequences

*   **Enhanced Security Posture:** Secrets are managed by a dedicated, secure AWS service with strong encryption, access control, and audit capabilities. Secret values are not stored in Git.
*   **Improved Compliance:** Centralized auditing via CloudTrail and clear access policies aid in meeting compliance requirements.
*   **Reduced Operational Overhead for Secret Rotation:** Automated rotation capabilities for many secrets reduce manual effort and the risk of using outdated credentials.
*   **Consistent Secret Management:** Provides a standardized way to manage and consume secrets across all Kubernetes applications and potentially other AWS services.
*   **Better Developer Experience (Long-term):** Once set up, developers can easily request access to secrets via declarative `ExternalSecret` manifests, without needing to handle raw secret values directly.
*   **Alignment with GitOps:** The use of `ExternalSecret` CRs in Git maintains the declarative nature of GitOps for application configuration.

### Negative Consequences (and Mitigations)

*   **Increased AWS Dependency:** The solution creates a strong dependency on AWS Secrets Manager and IAM.
    *   **Mitigation:** This is an accepted trade-off given the platform's existing foundation on AWS. Ensure robust AWS infrastructure and account security practices.
*   **Operational Overhead of External Secrets Operator (ESO):** ESO needs to be installed, maintained, and monitored in each Kubernetes cluster.
    *   **Mitigation:** ESO is a well-maintained operator. Standardize its deployment (e.g., via Helm) and include it in cluster monitoring and upgrade plans.
*   **Initial Setup Complexity:** Configuring AWS Secrets Manager, IAM roles for service accounts (IRSA), and deploying ESO requires initial effort and understanding of these components.
    *   **Mitigation:** Provide clear documentation, training, and potentially pre-configured modules or scripts for bootstrapping.
*   **Cost:** AWS Secrets Manager incurs costs based on the number of secrets stored and API calls.
    *   **Mitigation:** Monitor usage and optimize where possible. The costs are generally considered reasonable for the provided security and management benefits. Delete unused secrets.
*   **Potential Latency:** Fetching secrets from an external service might introduce minor latency compared to direct K8s secret access, though usually negligible.
    *   **Mitigation:** ESO caches secrets and updates them periodically; applications typically read from local K8s secrets once synced.

### Neutral Consequences

*   **Shift in Secret Handling:** Developers will need to learn about `ExternalSecret` CRs instead of directly managing Kubernetes `Secret` manifests for application-specific secrets.
*   **Requires Network Connectivity:** ESO requires network access from the Kubernetes cluster to AWS Secrets Manager endpoints.

## Links

*   [AWS Secrets Manager Documentation](https://aws.amazon.com/secrets-manager/faqs/)
*   [External Secrets Operator Documentation](https://external-secrets.io/latest/)
*   [ADR-001: Adoption of Microservices Architecture](/ecommerce-documentation/architecture/adr/ADR-001-adoption-of-microservices-architecture.md)
*   [ADR-006: Cloud Native Deployment Strategy](/ecommerce-documentation/architecture/adr/ADR-006-cloud-native-deployment-strategy.md)
*   [ADR-012: CI/CD Strategy](/ecommerce-documentation/architecture/adr/ADR-012-cicd-strategy.md)
