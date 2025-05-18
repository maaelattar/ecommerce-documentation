# ADR-023: Deployment Strategy for Microservices

*   **Status:** Proposed
*   **Date:** 2025-05-11
*   **Deciders:** Project Team
*   **Consulted:** DevOps/SRE Team, Lead Developers
*   **Informed:** All technical stakeholders

## Context and Problem Statement

With a microservices architecture (ADR-001) and a CI/CD pipeline (ADR-012), we need a well-defined strategy for deploying new versions of services to production. The goal is to achieve zero-downtime deployments, minimize risk, allow for quick rollbacks, and enable progressive rollouts where appropriate. This strategy must leverage our Kubernetes (ADR-006) container orchestration platform.

## Decision Drivers

*   **Zero Downtime:** Deployments should not cause service interruptions for users.
*   **Risk Mitigation:** Minimize the impact of a faulty deployment.
*   **Speed of Delivery:** Enable frequent and reliable releases.
*   **Rollback Capability:** Quickly revert to a previous stable version if issues arise.
*   **Progressive Rollout:** Ability to release new versions to a subset of users/traffic before a full rollout.
*   **Resource Efficiency:** Optimize resource usage during deployments.
*   **Automation:** Deployment strategies should be fully automated within the CI/CD pipeline.

## Considered Deployment Strategies (on Kubernetes)

1.  **Recreate:** Terminate all old instances before starting new ones. (Results in downtime, not suitable for production).
2.  **Rolling Update:** Gradually replace old instances with new ones, one by one or in batches. Kubernetes default strategy.
3.  **Blue/Green Deployment:** Deploy the new version (Green) alongside the old version (Blue). Switch traffic to Green when ready. Allows for instant rollback by switching traffic back to Blue.
4.  **Canary Deployment:** Route a small percentage of traffic to the new version. Monitor its performance and gradually increase traffic if it's stable. Allows for testing in production with minimal impact.
5.  **A/B Testing (Feature Toggling):** Not strictly a deployment strategy, but related. Deploy new code with feature flags, allowing features to be enabled/disabled for specific users or segments, independent of deployment. Often used in conjunction with Canary or Blue/Green.

## Decision Outcome

**Chosen Approach:** A hybrid approach, with **Rolling Update** as the default, and **Canary Deployments** for high-impact or risky changes, facilitated by Kubernetes and potentially service mesh capabilities.

*   **Default Strategy: Rolling Update (Kubernetes Native)**
    *   Kubernetes' `RollingUpdate` deployment strategy will be the default for most microservice deployments.
    *   Configure `maxUnavailable` and `maxSurge` parameters appropriately to ensure zero downtime and manage resource consumption during updates.
    *   Requires robust liveness and readiness probes (ADR-006, ADR-022) to ensure new pods are healthy before traffic is routed to them.

*   **High-Impact/Risky Changes: Canary Deployment**
    *   For services undergoing significant changes, or for critical services where impact of failure is high, Canary Deployments will be used.
    *   This involves deploying the new version alongside the stable version and directing a small percentage of traffic (e.g., 1%, 5%, 10%) to the canary.
    *   Implementation can be achieved using Kubernetes features (e.g., multiple Deployments with different labels and a Service selecting both, adjusting pod counts or using Ingress controllers with traffic splitting capabilities) or more advanced traffic management tools like a service mesh (Istio, Linkerd) or dedicated Canary deployment tools (e.g., Flagger, Argo Rollouts).
    *   Automated monitoring (ADR-021) of key metrics (error rates, latency, business KPIs) for the canary version is crucial. If metrics are healthy, traffic is gradually shifted; otherwise, a rollback is initiated.

*   **Blue/Green Deployment (Considered for specific scenarios):**
    *   While not the default, Blue/Green deployments may be considered for situations requiring an all-or-nothing switch with instant rollback capabilities, or for stateful services where parallel running during a rolling update is complex.
    *   Requires careful management of infrastructure resources (potentially doubling capacity temporarily) and data schema compatibility if databases are involved.

*   **Rollback Strategy:**
    *   Kubernetes `deployment.spec.rollbackTo` or `kubectl rollout undo deployment` for Rolling Updates.
    *   For Canary, shift 100% traffic back to the stable version and scale down the canary.
    *   For Blue/Green, switch traffic back to the Blue environment.
    *   Automated rollback triggers based on monitoring alerts should be implemented.

*   **Database Schema Migrations:**
    *   Must be handled carefully to be backward and forward compatible to support both old and new versions of the application running simultaneously during Rolling Updates or Canary deployments (e.g., expand-contract pattern).

*   **CI/CD Integration (ADR-012):**
    *   The CI/CD pipeline will automate the chosen deployment strategy.
    *   Integration with monitoring tools to automate canary analysis and promotion/rollback decisions.

## Consequences

*   **Pros:**
    *   Rolling Update is simple, efficient, and well-supported by Kubernetes.
    *   Canary deployments provide excellent risk mitigation for critical changes.
    *   Enables progressive delivery and learning from production traffic.
    *   Supports zero-downtime deployments.
*   **Cons:**
    *   Canary deployments add complexity to the deployment process and require sophisticated monitoring and traffic management.
    *   Managing database schema changes with zero-downtime deployments can be complex and requires careful planning to ensure backward and forward compatibility.
    *   If not using a service mesh, implementing advanced canary traffic splitting might require manual configuration or custom tooling.
*   **Risks:**
    *   Bugs in new versions might affect a subset of users during canary deployments.
    *   Insufficient monitoring or poorly defined success metrics for canaries can lead to promoting faulty versions.
    *   Rollbacks, while possible, might still incur some user impact or data consistency challenges if not handled correctly.

## Next Steps

*   Configure default Rolling Update parameters for Kubernetes Deployments in our Helm charts or Kustomize bases.
*   Choose and implement a tool/method for Canary deployments (e.g., Istio, Flagger, or Kubernetes native traffic splitting with Ingress).
*   Integrate deployment strategies into the CI/CD pipeline (ADR-012).
*   Develop clear guidelines for when to use Canary vs. Rolling Update.
*   Establish procedures for database schema migration that support zero-downtime deployments.
*   Define standard metrics and dashboards (ADR-021) for monitoring canary deployments.
