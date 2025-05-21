# 03: Configuration Management for Payment Service

Effective configuration management is crucial for the Payment Service to ensure consistency, reliability, and security across different environments (development, staging, production). This document outlines the strategy for managing application and infrastructure configurations.

## 1. Principles of Configuration Management

*   **Externalize Configuration:** Application configuration should be externalized from the application code (Docker image). This allows the same image to be deployed across different environments with varying configurations.
*   **Environment-Specific Configurations:** Maintain separate configuration sets for each environment (e.g., development, staging, production).
*   **IaC (Infrastructure as Code):** Manage infrastructure configurations (Kubernetes manifests, cloud resources) using code and version control (e.g., Terraform, CloudFormation, K8s YAML in Git).
*   **Secrets Management:** Sensitive configuration data (credentials, API keys) MUST be managed securely using a dedicated secrets management solution (see `02-infrastructure-requirements.md`).
*   **Immutability:** Strive for immutable configurations where possible. Changes should result in new deployments rather than modifying running systems directly.
*   **Auditability:** Track changes to configurations, especially in production.

## 2. Application Configuration

### 2.1. NestJS ConfigModule (`@nestjs/config`)

*   The Payment Service, being a NestJS application, will leverage the `@nestjs/config` module for managing application-level configurations.
*   **Environment Variables:** Primarily load configuration values from environment variables. This is a standard practice for containerized applications and aligns well with Kubernetes.
*   **.env Files (Local Development):** Use `.env` files for local development convenience. These files should NOT be committed to Git, especially if they contain sensitive defaults. A `.env.example` file can be committed to show required variables.
*   **Configuration Schema Validation:** Use Joi or class-validator (integrated with `@nestjs/config`) to define a schema for expected environment variables and validate them at application startup. This helps catch misconfigurations early.
*   **Typed Configuration:** Define a typed configuration object to provide type safety and autocompletion when accessing configuration values within the application.

### 2.2. Kubernetes ConfigMaps

*   **Purpose:** Store non-sensitive configuration data for the Payment Service pods in Kubernetes.
*   **Usage:** ConfigMaps can be used to inject configuration data into pods as:
    *   Environment variables.
    *   Command-line arguments.
    *   Files mounted into the container's filesystem.
*   **Example ConfigMap Data:**
    *   Logging level (e.g., `INFO`, `DEBUG`).
    *   External service URLs (non-sensitive parts, like base URLs for other internal services if they vary per environment in a non-secret way).
    *   Default retry attempts or timeout values.
    *   Feature flag settings (if managed via ConfigMaps).
*   **Management:** ConfigMaps are defined as YAML manifests and applied to the Kubernetes cluster. They should be version-controlled alongside other K8s manifests.

### 2.3. Kubernetes Secrets

*   **Purpose:** Store and manage sensitive configuration data for the Payment Service pods.
*   **Usage:** Secrets can be injected into pods similarly to ConfigMaps (as environment variables or mounted files).
*   **Example Secret Data:**
    *   Database credentials (username, password).
    *   API keys for payment gateways.
    *   Credentials for Kafka.
    *   Private keys or certificates.
*   **Security:**
    *   Kubernetes Secrets are base64 encoded by default, not encrypted. For stronger security, integrate with a dedicated secrets management solution like HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault.
    *   These external solutions can then securely inject secrets into pods (e.g., via CSI drivers or sidecar containers).
    *   Restrict access to Secrets using RBAC in Kubernetes.

## 3. Managing Configurations Across Environments

*   **Branching Strategy (Git):** Use environment branches (e.g., `dev`, `staging`, `main`/`prod`) or directory-based separation within a Git repository to manage environment-specific Kubernetes manifests (including ConfigMaps and potentially references to Secrets).
*   **Templating Tools:** Tools like Helm or Kustomize can be used to manage Kubernetes configurations and template out differences between environments.
    *   **Kustomize:** Allows overlaying environment-specific patches onto a common base configuration.
    *   **Helm:** A package manager for Kubernetes that uses charts (collections of pre-configured K8s resources) and allows overriding values for different environments.
*   **CI/CD Integration:** The CI/CD pipeline will be responsible for applying the correct environment-specific configurations during deployment to each environment.

## 4. Configuration Updates

*   **Application Configuration:** Changes to ConfigMaps or Secrets that are mounted as files into pods might require a pod restart to be picked up, depending on how the application reads them. NestJS `@nestjs/config` typically loads configuration at startup.
    *   Kubernetes Deployments can manage rolling updates of pods when ConfigMaps or Secrets change.
*   **Dynamic Configuration (Optional):** For certain configurations that need to change without a deployment (e.g., feature flags, tuning parameters), consider using a dynamic configuration service (e.g., Spring Cloud Config Server, HashiCorp Consul, etcd) if the complexity is justified. The Payment Service would then need to poll or subscribe to changes from this service.

By following these configuration management practices, the Payment Service can be deployed and operated consistently and securely across all environments, simplifying management and reducing the risk of errors.