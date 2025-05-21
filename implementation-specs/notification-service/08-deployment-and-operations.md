# Notification Service - Deployment and Operations

## 1. Overview

This document outlines the deployment strategy, operational considerations, monitoring, and maintenance aspects for the Notification Service.

## 2. Deployment Strategy

*   **Containerization**: The Notification Service will be packaged as a **Docker container**.
    *   A `Dockerfile` will define the image build process, including:
        *   Base Node.js image (e.g., `node:18-alpine` or a specific version used by the platform).
        *   Copying `package.json` and `package-lock.json`, installing dependencies (`npm ci`).
        *   Copying compiled application code (from `dist` directory).
        *   Exposing the application port (e.g., `300X`).
        *   Setting the default command to run the NestJS application (`node dist/main.js`).
*   **Orchestration**: Deployed on **Kubernetes** (e.g., Amazon EKS) along with other platform microservices.
    *   Kubernetes manifests (`Deployment`, `Service`, `ConfigMap`, `Secret`, `HorizontalPodAutoscaler`) will define its deployment.
*   **CI/CD Pipeline**: An automated CI/CD pipeline (e.g., Jenkins, GitLab CI, AWS CodePipeline) will handle:
    *   Linting and static analysis.
    *   Running unit and integration tests.
    *   Building the Docker image.
    *   Pushing the image to a container registry (e.g., Amazon ECR, Docker Hub).
    *   Deploying the new version to Kubernetes environments (dev, staging, prod) with appropriate approval gates.
*   **Configuration Management**: 
    *   Environment-specific configurations (database URLs, RabbitMQ connections, provider API keys, log levels) will be managed via Kubernetes `ConfigMaps` and `Secrets`.
    *   Secrets will be sourced from a secure secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault).
    *   The `@ecommerce-platform/nestjs-core-utils` `ConfigModule` will load these at runtime.

## 3. Infrastructure Requirements

*   **Kubernetes Cluster**: Access to the platform's EKS cluster.
*   **Database**: PostgreSQL instance (e.g., Amazon RDS).
*   **Message Broker**: RabbitMQ instance (e.g., Amazon MQ for RabbitMQ).
*   **Container Registry**: Amazon ECR or similar.
*   **Logging & Monitoring Stack**: 
    *   Centralized logging (e.g., ELK Stack - Elasticsearch, Logstash, Kibana; or AWS CloudWatch Logs).
    *   Metrics collection (e.g., Prometheus).
    *   Dashboarding and Alerting (e.g., Grafana, AWS CloudWatch Dashboards/Alarms).
*   **Secrets Management**: AWS Secrets Manager or HashiCorp Vault.

## 4. Operational Considerations

### 4.1. Scaling
*   The Notification Service will be designed to be stateless to allow for horizontal scaling using Kubernetes `HorizontalPodAutoscaler` (HPA).
*   HPA will be configured based on metrics like CPU utilization, memory usage, or custom metrics (e.g., number of messages in RabbitMQ queues it consumes, or active notification processing jobs).
*   Database and RabbitMQ scaling will be handled separately as per their respective best practices.

### 4.2. High Availability & Resilience
*   Multiple replicas of the Notification Service pods will run across different Kubernetes nodes/availability zones.
*   RabbitMQ queues should be configured for high availability (e.g., mirrored queues).
*   Database (RDS) should be configured with Multi-AZ deployment.
*   Resilience patterns (retries, timeouts, circuit breakers for external provider calls) will be implemented within the application code (some provided by `@ecommerce-platform/nestjs-core-utils` or provider SDKs).

### 4.3. Security
*   **Network Security**: Kubernetes Network Policies to restrict traffic to/from the Notification Service pods.
*   **Secrets Management**: Securely store and inject API keys for notification providers.
*   **Input Validation**: Rigorous validation of all incoming event payloads and API requests.
*   **Authentication/Authorization**: Exposed APIs secured via JWT (using `@ecommerce-platform/auth-client-utils`).
*   **Provider Webhook Security**: Implement signature verification for incoming webhooks from providers (e.g., AWS SNS, Twilio).
*   Regular security patching of base images and dependencies.

### 4.4. Third-Party Provider Management
*   **API Key Rotation**: Establish a process for regularly rotating API keys for external providers.
*   **Rate Limits & Quotas**: Monitor and manage usage against provider rate limits and quotas. Implement application-side throttling if necessary.
*   **Cost Management**: Track costs associated with third-party notification providers.

## 5. Monitoring and Alerting

Key metrics and aspects to monitor:

*   **Application Health**: 
    *   Standard health check endpoint (`/health/liveness`, `/health/readiness`) via `@ecommerce-platform/nestjs-core-utils`.
    *   Pod status, restarts, CPU/memory utilization.
*   **Event Consumption**: 
    *   Number of messages in consumed RabbitMQ queues.
    *   Processing rate of consumed events.
    *   Error rates during event processing.
    *   DLQ sizes.
*   **Event Publishing (if service publishes events)**:
    *   `notification_event_outbox` table depth and processing rate.
    *   Error rates during publishing from outbox.
*   **Notification Dispatch**: 
    *   Number of notifications sent per channel (email, SMS, push).
    *   Success rates for dispatching to providers.
    *   Failure rates (transient and permanent) for provider dispatch.
    *   Latency for sending notifications.
*   **Delivery Status**: 
    *   Rates of delivered, bounced, failed, opened, clicked notifications (based on provider callbacks).
*   **External Provider API Calls**: 
    *   Error rates and latencies for API calls to AWS SES, Twilio, FCM, etc.
*   **Database Performance**: Query latency, connection pool usage.

**Alerting**: Set up alerts for critical conditions:
*   High error rates in event consumption or dispatch.
*   Significant delays in processing notifications.
*   Critical provider API failures.
*   Large number of messages in DLQs or outbox.
*   Service unavailability (failed health checks).
*   Approaching provider rate limits.

## 6. Logging

*   Structured JSON logging (via `@ecommerce-platform/nestjs-core-utils` logger).
*   Logs should include correlation IDs, `messageId` (for events), `userId` (where applicable), `notificationId` to trace a request/notification through the system.
*   Key log points:
    *   Event received.
    *   Preference check outcome.
    *   Template rendering success/failure.
    *   Dispatch attempt to provider (including request details, sanitized).
    *   Provider response (success/failure, external message ID).
    *   Delivery status callback received.
    *   Errors and exceptions with stack traces.
*   Logs will be shipped to a centralized logging system for analysis and troubleshooting.

## 7. Maintenance

*   **Dependency Updates**: Regularly update Node.js, NestJS, third-party libraries, and base Docker images for security patches and bug fixes.
*   **Template Management**: Process for updating, versioning, and testing notification templates.
*   **Database Maintenance**: Standard PostgreSQL maintenance (backups, vacuuming, monitoring performance).
*   **Log Archival/Purging**: Implement strategy for managing `NotificationLog` growth.
