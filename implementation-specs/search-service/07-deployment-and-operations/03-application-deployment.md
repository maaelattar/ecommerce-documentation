# Search Service Application Deployment

## Overview

This document details the deployment process for the Search Service application (the NestJS service itself), distinct from the management of its primary dependency, Elasticsearch (covered in `02-elasticsearch-cluster-management.md`). It focuses on how the containerized application is deployed, configured for different environments, scaled, and updated with zero or minimal downtime.

Building upon `01-deployment-environment.md`, we assume a Kubernetes environment and Docker containerization.

## Deployment Artifacts

*   **Docker Image**: The primary artifact, built by the CI/CD pipeline and stored in a container registry (e.g., AWS ECR, GCR, Docker Hub).
*   **Kubernetes Manifests**: YAML files defining the desired state of the application in Kubernetes. These are managed using Infrastructure as Code (IaC) principles.
    *   `Deployment` or `StatefulSet`: Manages the application pods.
        *   A `Deployment` is suitable for stateless parts of the application (like the API handlers).
        *   If the Search Service had stateful components directly managed by K8s (uncommon for this type of service, as state is in Kafka/ES), a `StatefulSet` might be considered.
    *   `Service`: Provides a stable network endpoint (ClusterIP, LoadBalancer) for accessing the application.
    *   `ConfigMap`: Stores non-sensitive configuration data (e.g., log levels, default timeouts, feature flags).
    *   `Secret`: Stores sensitive configuration data (e.g., API keys for external services it might call, database credentials if it had its own DB - though Search Service typically doesn't).
    *   `HorizontalPodAutoscaler (HPA)`: Automatically scales the number of application pods based on metrics like CPU utilization or custom metrics (e.g., Kafka consumer lag, request queue length).
    *   `PodDisruptionBudget (PDB)`: Ensures a minimum number of pods remain running during voluntary disruptions (e.g., node maintenance, deployments).
    *   `Ingress` (Optional): If exposing the Search API externally without a dedicated API Gateway, an Ingress controller and Ingress resource would manage external access.

## Configuration Management

Configuration for the Search Service application will vary between environments (dev, staging, production).

*   **Mechanism**: Primarily through environment variables injected into the containers by Kubernetes.
*   **Sources**: 
    *   `ConfigMap`s for non-sensitive data.
    *   `Secret`s for sensitive data (e.g., credentials for Kafka if SASL is used, Elasticsearch credentials).
*   **NestJS `@nestjs/config`**: The application uses this module to load and access configuration values from environment variables.
*   **Key Configuration Parameters**: 
    *   `NODE_ENV`: (development, production, test)
    *   `PORT`: HTTP port the service listens on.
    *   `KAFKA_BROKERS`: Comma-separated list of Kafka broker addresses.
    *   `KAFKA_CONSUMER_GROUP_ID`: Consumer group ID for Kafka.
    *   `KAFKA_TOPICS_PRODUCT`, `KAFKA_TOPICS_CATEGORY`, etc.: Names of Kafka topics to consume.
    *   `ELASTICSEARCH_NODE`: Elasticsearch node URL(s).
    *   `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD` (or API Key).
    *   `LOG_LEVEL`: (info, debug, warn, error).
    *   `JWT_SECRET` or `JWKS_URI` (if validating JWTs itself for admin APIs).
    *   Feature flags.
    *   Timeouts, retry settings.

## Scaling Strategies

*   **Horizontal Scaling (Primary)**: The Search Service application is designed to be stateless (or manage state externally in Kafka/Elasticsearch/Redis), allowing for horizontal scaling by increasing the number of pods (replicas) in the Kubernetes `Deployment`.
*   **Horizontal Pod Autoscaler (HPA)**:
    *   Configure HPA to automatically adjust the number of replicas based on observed metrics.
    *   **Metrics for Scaling**: 
        *   CPU Utilization (common starting point).
        *   Memory Utilization (less common for scaling unless memory is a primary constraint).
        *   Custom Metrics (more advanced and often more effective for event-driven services):
            *   Kafka Consumer Lag: Scale up if lag on consumed topics exceeds a threshold.
            *   Active Connections or Request Rate (for API serving pods).
            *   Queue length of an internal processing queue.
*   **Vertical Scaling**: Increasing resources (CPU, memory) allocated to individual pods. This is usually a secondary scaling dimension, done by adjusting resource requests/limits in the Kubernetes `Deployment` manifest. HPA typically handles horizontal scaling first.

## Zero-Downtime Deployments

Ensuring service availability during updates is critical.

*   **Kubernetes Rolling Updates (Default `Deployment` Strategy)**:
    *   Gradually replaces old pods with new ones.
    *   `maxSurge`: Number of pods that can be created above the desired count during an update.
    *   `maxUnavailable`: Number of pods that can be unavailable during an update.
    *   Combined with readiness and liveness probes, this ensures traffic is only routed to healthy new pods.
*   **Blue/Green Deployments**:
    *   Deploy the new version (`green`) alongside the old version (`blue`).
    *   Test the `green` environment.
    *   Switch traffic from `blue` to `green` (e.g., by updating a Kubernetes `Service` selector or Ingress routing).
    *   Keep `blue` running for quick rollback if issues arise.
    *   More resource-intensive but provides safer rollback.
*   **Canary Deployments**:
    *   Route a small percentage of traffic to the new version.
    *   Monitor performance and error rates.
    *   Gradually increase traffic to the new version if it's stable.
    *   More complex to set up, often requiring service mesh tools (e.g., Istio, Linkerd) or advanced Ingress controllers for fine-grained traffic splitting.

**Readiness and Liveness Probes**: Essential for zero-downtime deployments. Kubernetes uses these to know when a new pod is ready to accept traffic and when an existing pod is unhealthy and needs to be restarted or removed from service.
*   **Liveness Probe**: Checks if the application is running (e.g., basic HTTP endpoint responding).
*   **Readiness Probe**: Checks if the application is ready to handle requests (e.g., connected to Kafka, Elasticsearch, and other dependencies are healthy). See `../06-integration-points/04-service-discovery-registration.md` for an example health controller.

## CI/CD Integration for Deployment

(As detailed in `01-deployment-environment.md`)
*   The CD pipeline automates the deployment of new versions to different environments.
*   It applies Kubernetes manifests (`kubectl apply -f ...`, Helm, Kustomize, Argo CD).
*   It updates the image tag in the `Deployment` manifest to trigger a rollout.

## Rollback Strategy

*   **Kubernetes Rollouts**: `kubectl rollout undo deployment/<deployment-name>` can revert to the previous revision of a `Deployment`.
*   For Blue/Green, switch traffic back to the `blue` environment.
*   For Canary, shift all traffic back to the old version.
*   Automate rollback as much as possible based on monitoring alerts post-deployment.

## Key Operational Tasks for Application Deployment

*   Monitoring deployment status and health of new pods.
*   Reviewing logs from new pods for any startup errors.
*   Verifying configuration is correctly applied in each environment.
*   Ensuring HPA is functioning correctly and scaling as expected.
*   Managing `PodDisruptionBudgets` to ensure availability during planned disruptions (like cluster upgrades).

By implementing these deployment strategies, the Search Service application can be managed effectively, scaled to meet demand, and updated with high availability.
