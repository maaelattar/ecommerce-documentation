# 08: Maintenance and Upgrades

Regular maintenance and seamless upgrades are essential for the long-term health, security, and evolution of the User Service. This document outlines procedures and strategies for these activities, with a strong emphasis on minimizing downtime.

## 1. Patch Management

*   **Operating System (Container Base Image)**:
    *   Regularly update the base Docker image (e.g., `node:18-alpine`) to include the latest OS security patches.
    *   This should be part of a routine image rebuilding and redeployment process, triggered by upstream image updates or a scheduled review.
*   **Application Dependencies (Node.js Packages)**:
    *   Continuously monitor application dependencies for security vulnerabilities (using tools like `npm audit`, Snyk, Dependabot).
    *   Apply patches for vulnerable dependencies promptly, test thoroughly, and deploy.
    *   Regularly update to newer minor/patch versions of dependencies to stay current and reduce the risk of falling far behind major releases.
*   **Database Engine**: If using a managed database service, the cloud provider typically handles OS and database engine patching during scheduled maintenance windows. Understand the provider's patching process and configure maintenance windows appropriately.
*   **Kafka Cluster**: Similar to databases, managed Kafka services usually handle broker OS and Kafka software patching. For self-managed clusters, a clear patching plan is needed.
*   **Kubernetes**: Kubernetes control plane and node patching is typically managed by the cloud provider (for managed K8s services like EKS, GKE, AKS) or by the platform team.

## 2. Application Upgrade Process

*   **Goal**: Achieve zero-downtime deployments for new versions of the User Service.
*   **Deployment Strategy (Kubernetes)**: Use rolling updates, which is the default strategy for Kubernetes Deployments.
    *   **`maxUnavailable`**: Defines the maximum number of pods that can be unavailable during the update (e.g., 25% or a fixed number).
    *   **`maxSurge`**: Defines the maximum number of pods that can be created over the desired number of pods (e.g., 25% or a fixed number).
    *   Kubernetes gradually replaces old pods with new ones, ensuring service availability throughout the process.
*   **Blue/Green or Canary Deployments**: As detailed in `01-deployment-strategy.md`, these advanced strategies can also be used for more controlled rollouts and easier rollbacks, further minimizing risk.
*   **CI/CD Integration**: Upgrades should be fully automated through the CI/CD pipeline.
*   **Health Checks**: Robust liveness and readiness probes are crucial for Kubernetes to correctly manage rolling updates. New pods must pass these checks before old pods are terminated.
*   **Backward Compatibility**: For significant changes, especially API changes, ensure backward compatibility or version APIs to allow consumers to migrate gradually. (Refer to API versioning practices).

## 3. Database Schema Migration Management

Database schema changes are often the most challenging part of an upgrade.

*   **Tooling**: Use a database migration tool like TypeORM Migrations (as recommended in `02-data-model-setup/08-orm-migrations.md`), Flyway, or Liquibase.
*   **Migration Scripts**: Write migration scripts for every schema change. These scripts should be version-controlled alongside the application code.
*   **Idempotency**: Migration scripts should be idempotent (i.e., running them multiple times should have the same effect as running them once).
*   **Backward and Forward Compatibility (Expand/Contract Pattern)**:
    *   For complex changes that cannot be applied atomically without downtime or risk, use an expand/contract pattern (also known as parallel change or additive change).
    *   **Phase 1 (Expand)**: Make backward-compatible schema changes. For example, add new nullable columns, new tables. Deploy application code that can work with both the old and new schema (e.g., writes to both old and new columns/tables, reads from old and falls back to new or vice-versa).
    *   **Phase 2 (Migrate/Verify)**: Once the new application code is stable, run data migration scripts to populate new schema elements from old ones if necessary. Verify data integrity.
    *   **Phase 3 (Contract)**: Deploy new application code that solely relies on the new schema. Remove old schema elements (e.g., drop old columns/tables) in a subsequent migration script.
*   **CI/CD Integration**: Integrate schema migration execution into the CI/CD pipeline.
    *   Typically, migrations are run just before the new application version is deployed or as a separate step controlled by the deployment process.
    *   Careful sequencing is required: ensure the database schema is compatible with the application version being deployed.
*   **Testing**: Thoroughly test schema migrations in staging environments.
*   **Backup**: Always ensure a recent database backup exists before applying schema migrations in production.
*   **Rollback Plan**: Have a plan for rolling back schema migrations if issues occur. This can be complex; often, it involves restoring from a backup or applying a "down" migration script (if feasible and safe).

## 4. Zero-Downtime Deployment (ZDD) Goals

Achieving true zero-downtime requires a combination of the above strategies:

*   Stateless application design.
*   Rolling updates or Blue/Green/Canary deployments for the application.
*   Careful management of database schema migrations (expand/contract).
*   Robust health checks.
*   Connection draining on load balancers to allow existing requests to complete before pods are terminated.
*   No breaking API changes without versioning.

## 5. Maintenance Windows

*   While striving for ZDD, some underlying infrastructure maintenance (e.g., by cloud providers for managed services) might still require scheduled maintenance windows.
*   Communicate these windows to users/stakeholders if they are expected to cause any noticeable impact (even if minimal).
*   Configure maintenance windows in cloud provider settings to occur during off-peak hours.

By adhering to these maintenance and upgrade procedures, the User Service can evolve with new features and security updates while maintaining high availability and stability for users.
