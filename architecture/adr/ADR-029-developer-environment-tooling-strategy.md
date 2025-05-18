# ADR-029: Developer Environment and Tooling Strategy

*   **Status:** Proposed
*   **Date:** 2025-05-11
*   **Deciders:** Project Team, Lead Developers
*   **Consulted:** Development Team, DevOps/SRE Team
*   **Informed:** All technical stakeholders

## Context and Problem Statement

To ensure developer productivity, consistency, and a smooth onboarding experience for our microservices architecture (ADR-001), we need a well-defined strategy for local development environments and common tooling. This ADR outlines the approach to standardizing how developers build, test, and run services locally before pushing to shared environments managed by our CI/CD pipeline (ADR-012).

## Decision Drivers

*   **Developer Productivity:** Minimize setup time and provide a fast feedback loop for local development and testing.
*   **Consistency:** Ensure all developers use a similar environment to reduce "works on my machine" issues.
*   **Ease of Onboarding:** New developers should be able to set up their environment quickly.
*   **Resource Efficiency:** Optimize local environments to run efficiently on developer machines.
*   **Isolation:** Allow developers to work on individual services or a subset of services without interference.
*   **Integration with CI/CD:** Local development practices should align with the CI/CD pipeline (ADR-012) and Kubernetes (ADR-006) deployments.

## Considered Options

1.  **Fully Local Docker Compose:** Use Docker Compose to define and run all required services locally.
2.  **Local Kubernetes (e.g., Minikube, Kind, Docker Desktop Kubernetes):** Run a lightweight Kubernetes cluster locally for higher fidelity with production.
3.  **Hybrid Approach (Local Services + Cloud/Shared Dev Services):** Develop primary service(s) locally and connect to shared instances of other dependent services deployed in a common development environment.
4.  **Cloud-Based Development Environments (e.g., Gitpod, GitHub Codespaces):** Entire development environment runs in the cloud, accessed via a browser or thin client.

## Decision Outcome

**Chosen Approach:** A **Hybrid Approach** centered around **Local Kubernetes (Kind or Minikube)** for running the primary service(s) under development and their immediate dependencies, complemented by the ability to connect to shared development instances for other services. We will also heavily leverage **Docker and Skaffold** for local containerized development and iteration.

*   **Local Service Development & Execution:**
    *   **Containerization:** All services MUST be containerized using Docker (as per ADR-005).
    *   **Local Kubernetes Cluster:** Developers will use a local Kubernetes distribution like **Kind (Kubernetes IN Docker)** or **Minikube**. This provides a high-fidelity environment similar to production (ADR-006).
    *   **Skaffold:** We will adopt **Skaffold** for automating the build, push (to local cluster), and deploy workflow for local development. Skaffold enables rapid iteration by watching for code changes and automatically rebuilding/redeploying to the local Kubernetes cluster.
    *   Developers should be able to easily run and debug one or more services they are actively working on within their local Kubernetes cluster.

*   **Managing Dependencies Locally:**
    *   **Service Stubs/Mocks:** For distant or complex dependencies not directly being worked on, developers should use service stubs or mocks (e.g., using tools like WireMock, or simple in-code mocks) to simulate their behavior. This is particularly important for unit and local integration tests.
    *   **Running Subset of Services:** The local Kubernetes setup should allow developers to easily deploy a subset of core dependent services (e.g., a local database instance, a local message broker instance - ADR-018 if needed for the feature).
    *   **Connecting to Shared Dev Environment:** For broader integration testing or when a full suite of dependencies is needed, developers will be able to configure their locally running services to connect to other services deployed in a shared, stable `development` Kubernetes namespace/cluster.

*   **Standardized Tooling:**
    *   **IDE:** While developers can choose their preferred IDE (VS Code, IntelliJ IDEA, etc.), we will provide standardized configurations, plugins, and extensions for common tasks (e.g., debugging, Kubernetes interaction, Skaffold integration).
    *   **Version Control:** Git (with branching strategy defined in ADR-011).
    *   **Build Tool:** Node.js/npm/yarn for our primary stack (ADR-003), with consistent versioning managed via `.nvmrc` or similar.
    *   **Task Runners/Linters/Formatters:** Standardize on tools like ESLint, Prettier to maintain code quality and consistency.
    *   **Command Line Tools:** `kubectl`, `helm`, `skaffold`, Docker CLI, cloud provider CLIs.

*   **Configuration Management (Local):**
    *   Local development configurations (e.g., connection strings for local databases or shared dev services) should be managed using environment variables or local-only configuration files (e.g., `.env` files, local Kubernetes ConfigMaps/Secrets) and MUST NOT be committed to version control.

*   **Documentation:**
    *   Clear documentation for setting up the local development environment, including required tools, versions, and common troubleshooting tips.
    *   Scripts to automate parts of the setup process.

## Consequences

*   **Pros:**
    *   Provides a good balance between local development speed and fidelity with production (Kubernetes).
    *   Skaffold significantly improves the inner-loop development experience (code, build, deploy, test cycle).
    *   Reduces "works on my machine" issues by using containers and Kubernetes locally.
    *   Facilitates easier onboarding of new developers with a standardized setup.
    *   Hybrid approach offers flexibility in managing dependencies.
*   **Cons:**
    *   Local Kubernetes and Skaffold have a learning curve.
    *   Running a local Kubernetes cluster can be resource-intensive on developer machines (CPU, RAM).
    *   Managing configurations for connecting to shared dev services can sometimes be complex.
    *   Cloud-based development environments, while not chosen as primary, might offer simpler setup for some but come with their own costs and limitations.
*   **Risks:**
    *   Inconsistent adoption of tools or practices if not well-documented or enforced.
    *   Performance issues on underpowered developer machines.
    *   Drift between local environment setup and shared/production environments if not actively managed.

## Next Steps

*   Create starter packs or templates for new services including Dockerfile, Skaffold configuration, and local Kubernetes manifests.
*   Develop and document the standard procedure for setting up Kind/Minikube with Skaffold.
*   Provide recommended IDE extensions and configurations.
*   Establish guidelines for when to use local mocks vs. shared dev services for dependencies.
*   Create a repository for shared development scripts and tools.
*   Solicit feedback from the development team during initial rollout and iterate on the setup.
