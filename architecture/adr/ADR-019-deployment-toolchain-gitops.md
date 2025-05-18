# ADR-019: Deployment Toolchain and GitOps Implementation

*   **Status:** Proposed
*   **Date:** 2025-05-12
*   **Deciders:** Architecture Team, Lead Developers, DevOps/Platform Team

## Context

We have established several foundational architectural decisions:
*   Microservices Architecture (ADR-001)
*   Cloud-Native Deployment on Kubernetes (AWS EKS) (ADR-006)
*   Centralized CI/CD platform using GitHub Actions (ADR-012)
*   Configuration Management Strategy compatible with GitOps (ADR-016)
*   Leveraging AWS Managed Services where appropriate (various Technology Decision documents)

While these ADRs define the *strategy*, they don't explicitly standardize the core *tooling* required to implement consistent, automated, and declarative deployments and infrastructure management, particularly concerning Kubernetes application packaging, continuous delivery synchronization (GitOps), and Infrastructure as Code (IaC).

## Problem Statement

How do we ensure consistent, repeatable, automated, and declarative management and deployment of:
1.  Kubernetes application manifests and configurations?
2.  Underlying cloud infrastructure resources (VPC, EKS Clusters, Databases, Load Balancers, IAM Roles, etc.)?

We need a standardized toolchain that aligns with our microservices, Kubernetes, CI/CD, and AWS-centric strategies, promotes GitOps principles (using Git as the single source of truth), and provides a good developer and operator experience.

## Decision Drivers

*   **Consistency & Repeatability:** Ensure applications and infrastructure are deployed and managed uniformly across all environments.
*   **Automation:** Minimize manual steps in deployment and infrastructure provisioning processes.
*   **Declarative Configuration:** Define desired state in code/configuration, allowing tools to reconcile reality with the desired state.
*   **GitOps Principles:** Use Git repositories as the source of truth for both application configuration and infrastructure definition. Changes are driven through Git workflows (PRs, reviews, merges).
*   **Developer Experience (DevEx):** Provide tools that are relatively easy for developers and operators to learn and use effectively.
*   **Operational Efficiency:** Reduce the burden of managing deployments and infrastructure.
*   **Ecosystem Integration:** Tools should integrate well with Kubernetes, AWS, and GitHub Actions.
*   **Community Support & Maturity:** Prefer well-established tools with strong community backing and proven track records.
*   **Visibility:** Provide mechanisms to understand the state of deployments and infrastructure.

## Considered Options

### 1. Kubernetes Manifest Packaging/Templating
    *   **Helm:** Mature package manager for Kubernetes, uses templating for customization, large community repository of charts.
    *   **Kustomize:** Template-free way to customize manifests, built into `kubectl`, good for overlaying environment-specific configurations.
    *   **Raw YAML:** Direct definition, simple for small cases but becomes hard to manage and reuse at scale.

### 2. GitOps Controller / Continuous Delivery Tool
    *   **Argo CD:** Popular GitOps controller, focuses on application deployment, provides a UI for visibility, integrates well with Helm/Kustomize. Pull-based model.
    *   **Flux CD:** Another popular GitOps controller (CNCF graduated project), also pull-based, strong on cluster bootstrapping and infrastructure reconciliation capabilities alongside applications.
    *   **GitHub Actions Only:** Use GitHub Actions workflows to directly apply manifests (`kubectl apply`). Lacks continuous reconciliation and the visibility/control features of dedicated controllers. Push-based model.

### 3. Infrastructure as Code (IaC) Tool
    *   **AWS Cloud Development Kit (CDK):** Define cloud infrastructure using familiar programming languages (TypeScript, Python, etc.), leverages CloudFormation underneath, strong typing and IDE support, good for complex logic.
    *   **Terraform:** Mature, declarative IaC tool, widely used, large provider ecosystem (including AWS), state management is crucial. HCL language.
    *   **AWS CloudFormation:** Native AWS IaC service, declarative (JSON/YAML templates), directly integrated with AWS services. Can be verbose.
    *   **Pulumi:** Define infrastructure using familiar programming languages (similar to CDK), multi-cloud support.

## Decision Outcome

We will adopt the following standardized toolchain for deployment and infrastructure management:

1.  **Kubernetes Packaging/Templating:** **Helm** will be the standard tool for packaging, templating, and managing the lifecycle of our Kubernetes applications.
2.  **GitOps Controller:** **Argo CD** will be deployed to our EKS clusters as the GitOps controller, responsible for continuously synchronizing the application state defined in Git (via Helm charts/values) with the running state in Kubernetes.
3.  **Infrastructure as Code:** **AWS Cloud Development Kit (CDK)** using **TypeScript** will be the primary standard for defining and provisioning AWS infrastructure resources. Terraform may be considered for specific use cases where CDK has limitations (e.g., managing certain non-AWS resources if needed in the future), but CDK is the default.

### 4. Supporting Tooling Decisions

To complete the end-to-end workflow facilitated by the core toolchain, we also standardize on the following supporting tools:

*   **Container Registry:** **AWS Elastic Container Registry (ECR)** will be used to store all container images built by our CI process.
*   **Helm Chart Repository:** **AWS ECR** will also be used as the repository for storing our versioned Helm charts, leveraging its support for OCI artifacts. This co-locates images and charts within the same managed AWS service.
*   **GitOps-Compatible Secret Management:** **Bitnami Sealed Secrets** controller will be installed in our EKS clusters. Developers will use the corresponding `kubeseal` CLI tool to encrypt Kubernetes `Secret` manifests before committing them to Git. Argo CD will deploy the `SealedSecret` custom resources, and the controller will decrypt them into standard `Secret` objects within the cluster.

## Rationale

*   **Helm:** Provides powerful templating capabilities needed for managing application configurations across different environments (dev, staging, prod). Its widespread adoption ensures ample community support, readily available charts for third-party software, and good integration with CI/CD and GitOps tools like Argo CD.
*   **Argo CD:** Offers a robust implementation of the GitOps pull model, continuously ensuring the cluster state matches the Git repository. Its UI provides valuable visibility into application sync status and deployment history, improving operational insight. It integrates seamlessly with Helm for deploying applications packaged as charts. It aligns strongly with our declarative and Git-centric principles.
*   **AWS CDK (TypeScript):** Leverages familiar programming languages (TypeScript aligns well if backend services use Node.js/NestJS), enabling developers to use constructs like loops, conditionals, and composition naturally. Strong typing and IDE integration improve the development experience and reduce errors. It synthesizes CloudFormation, ensuring reliable provisioning on AWS. It allows for creating reusable infrastructure components (Constructs), promoting consistency. While Terraform is also excellent, CDK's potential for better integration with application developer workflows makes it slightly preferable as the primary standard for our AWS-centric project.
*   **Synergy:** This toolchain works cohesively:
    *   Developers build container images and Helm charts.
    *   GitHub Actions (CI) runs tests, builds images, potentially updates Helm chart versions/values in a Git repository.
    *   Argo CD (CD) detects changes in the Git repository and automatically syncs the corresponding Helm release to the EKS cluster.
    *   AWS CDK defines the underlying EKS cluster, databases, IAM roles, Argo CD deployment itself, etc., managed via separate Git repositories and potentially triggered by GitHub Actions.

## Consequences

### Positive
*   Standardized, automated deployment process across all services and environments.
*   Increased deployment velocity and reliability.
*   Improved visibility into application deployment status (Argo CD UI).
*   Infrastructure managed consistently and declaratively via code (CDK).
*   Strong alignment with GitOps principles, improving auditability and rollback capabilities.
*   Potentially enhanced developer experience using familiar languages for IaC (CDK).

### Negative / Risks
*   **Learning Curve:** Teams need to learn Helm, Argo CD, and AWS CDK.
*   **Tooling Overhead:** Argo CD itself needs to be deployed, managed, and monitored within the cluster.
*   **Complexity:** Managing Git repository structures, Helm chart dependencies, and CDK stacks requires discipline.
*   **CDK State:** While CDK uses CloudFormation, understanding how CDK synthesizes templates and manages state is important.
*   **Potential for "Drift":** Strict adherence to GitOps workflows is required to prevent manual changes causing drift (though Argo CD helps detect this).

### Mitigations
*   Provide training, documentation, and internal support/mentorship for the chosen tools.
*   Establish clear Git branching strategies and PR processes for application manifests and infrastructure code.
*   Develop reusable Helm chart templates and CDK constructs ("golden paths").
*   Implement automated security scanning within CI pipelines for container images, Helm charts, and potentially CDK code.
*   Use Argo CD's features for drift detection.

## Links

*   [ADR-006: Cloud-Native Deployment Strategy](./ADR-006-cloud-native-deployment-strategy.md)
*   [ADR-012: CI/CD Strategy](./ADR-012-cicd-strategy.md)
*   [ADR-016: Configuration Management Strategy](./ADR-016-configuration-management-strategy.md)

## Further Considerations (Not decided here)

*   Specific Git repository structure for application manifests vs. infrastructure code.
*   Helm chart repository solution (e.g., GitHub Packages, ChartMuseum, AWS ECR OCI support).
*   Bootstrapping process for Argo CD itself.
*   Integration of automated testing results into the GitOps workflow (e.g., promotion between environments).
*   Versioning strategy for Helm charts and CDK constructs.
