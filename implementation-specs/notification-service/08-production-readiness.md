# Notification Service: Production Readiness Checklist

## 1. Introduction

*   **Purpose**: This document serves as a comprehensive checklist to ensure that the Notification Service meets all necessary operational, performance, security, and reliability standards before being deployed to and maintained in the production environment. Given its critical role in user and system communication, thorough readiness is paramount.
    *   Status: `[ ] TODO`

---

## 2. Monitoring & Alerting (Ref: ADR-011 Monitoring and Observability, ADR-021 Logging Strategy)

**Overall Status**: `[ ] TODO`

### 2.1. Key Metrics to Monitor

*   **Event Consumption Metrics**:
    *   `[ ]` Event Processing Rate: Number of events consumed per unit of time (e.g., per minute/second), per event type.
    *   `[ ]` Event Processing Error Rate: Percentage of consumed events that result in a processing error before hand-off to a channel, per event type.
    *   `[ ]` Average Event Processing Time: Time taken from event consumption to successful hand-off to a channel integrator or to a DLQ, per event type.
    *   `[ ]` Incoming Event Queue Length: Number of messages in the RabbitMQ queue(s) feeding the Notification Service.
*   **API Metrics (if any, as per `04-api-layer.md`)**:
    *   `[ ]` Request Rate (per endpoint, overall).
    *   `[ ]` Error Rate (4xx, 5xx, per endpoint, overall).
    *   `[ ]` Latency (average, 95th percentile, 99th percentile, per endpoint, overall).
*   **Channel Integration Metrics (per channel: Email/AWS SES, SMS/Twilio, Push/AWS SNS)**:
    *   `[ ]` Number of Notifications Attempted (per channel).
    *   `[ ]` Number of Notifications Successfully Sent to Provider (per channel).
    *   `[ ]` Notification Success Rate (Sent to Provider / Attempted, per channel).
    *   `[ ]` Number of Notifications Failed by Provider (per channel, based on synchronous errors or feedback).
    *   `[ ]` Notification Failure Rate (Failed by Provider / Attempted, per channel).
    *   `[ ]` Latency to Third-Party Provider APIs: Time taken for API calls to SES, Twilio, SNS (average, 95th, 99th).
    *   `[ ]` AWS SES Specific: Bounce Rate.
    *   `[ ]` AWS SES Specific: Complaint Rate.
    *   `[ ]` Twilio Specific: Delivery Rate (if DLRs are actively tracked and aggregated).
    *   `[ ]` AWS SNS Specific: Delivery Rate to platforms (FCM/APNS), Platform Endpoint disabled rate.
*   **Service Health**:
    *   `[ ]` CPU Usage (per instance, aggregate).
    *   `[ ]` Memory Usage (per instance, aggregate).
    *   `[ ]` Container Restarts / Pod Restarts.
    *   `[ ]` Number of running instances/replicas.
*   **Database Metrics (if storing templates/history, as per ADR-004)**:
    *   `[ ]` Query Latency (average, 95th percentile for key queries, e.g., fetching templates, writing logs).
    *   `[ ]` Active Database Connections / Connection Pool Usage.
    *   `[ ]` Database CPU/Memory/Storage.

### 2.2. Dashboards

*   `[ ]` **Service Overview Dashboard**: Aggregating key health metrics (CPU, memory), overall event processing rates/errors, API metrics (if any).
*   `[ ]` **Event Processing Dashboard**: Detailed breakdown of event consumption (rates, errors, processing times per event type), input queue lengths.
*   `[ ]` **Email (AWS SES) Channel Dashboard**: Tracks SES send rates, success/failure rates, bounce rates, complaint rates, API latencies to SES.
*   `[ ]` **SMS (Twilio) Channel Dashboard**: Tracks Twilio send rates, success/failure rates, delivery rates (if DLRs aggregated), API latencies to Twilio.
*   `[ ]` **Push (AWS SNS) Channel Dashboard**: Tracks SNS publish rates (per platform), success/failure rates to endpoints, API latencies to SNS.
*   `[ ]` Database Performance Dashboard (if applicable).

### 2.3. Alerting

*   **Critical Alerts (High Priority - immediate notification to on-call)**:
    *   `[ ]` Event processing error rate exceeds X% over Y minutes for any critical event type.
    *   `[ ]` Significant drop in notification success rate for any channel (e.g., <90% for SES, <80% for Twilio over Z minutes).
    *   `[ ]` Critical errors from channel providers (e.g., authentication failures, permission issues with AWS SES/SNS/Twilio).
    *   `[ ]` Incoming event queue length exceeds critical threshold for X duration (indicates processing backlog).
    *   `[ ]` API error rate (if API exists) exceeds X% for Y minutes.
    *   `[ ]` Service unavailable (health checks failing consistently).
    *   `[ ]` Database unavailable or critical error (if applicable).
*   **Warning Alerts (Medium Priority - notification, may not require immediate page)**:
    *   `[ ]` Increased latency in event processing or calls to provider APIs.
    *   `[ ]` Sustained rise in non-critical errors from providers.
    *   `[ ]` AWS SES bounce rate exceeds X%.
    *   `[ ]` AWS SES complaint rate exceeds Y%.
    *   `[ ]` Resource utilization (CPU, memory) consistently high.
    *   `[ ]` Incoming event queue length consistently above normal levels.
*   `[ ]` Notification channels for alerts defined (PagerDuty, Slack, Email).
*   `[ ]` Alert escalation paths understood by the team.

---

## 3. Logging (Ref: ADR-010 Structured Logging, ADR-021 Logging Strategy)

**Overall Status**: `[ ] TODO`

*   `[ ]` **Structured Logging**: All logs are in JSON format.
*   **Key Information Logged**:
    *   `[ ]` Processed Event Details: Unique event ID, event type, source service, timestamp of consumption.
    *   `[ ]` Notification Details: Recipient identifier (e.g., masked email, user ID, masked phone number), template name/key used, channels selected for delivery.
    *   `[ ]` Channel Provider Interactions:
        *   Request made to provider (service name, operation).
        *   Success or failure of the provider API call.
        *   Message ID or request ID returned by the provider.
        *   Key error codes or messages from the provider in case of failure.
    *   `[ ]` Correlation IDs: Present in all logs, linking event consumption to notification dispatch and provider interaction.
    *   `[ ]` General service activity, errors, warnings with stack traces.
*   `[ ]` **Sensitive Data Masking**:
    *   Full PII from event payloads (e.g., full name, street address if present) is NOT logged unless explicitly required and risk-assessed. User IDs or masked identifiers preferred.
    *   API keys, tokens, or other secrets are NEVER logged.
    *   Full email addresses and phone numbers should be masked in general logs if possible, or logged at DEBUG level only if essential for specific troubleshooting.
*   `[ ]` **Log Levels**: Appropriate use of DEBUG, INFO, WARN, ERROR. Production default is INFO.
*   `[ ]` **Log Aggregation**: Logs are shipped to a central log management system (e.g., ELK Stack, CloudWatch Logs, Splunk).
*   `[ ]` **Searchability**: Logs are easily searchable and filterable in the aggregation tool using correlation IDs, event IDs, user IDs, etc.

---

## 4. Scalability & Performance (Ref: ADR-027 Scalability and Performance Testing)

**Overall Status**: `[ ] TODO`

*   `[ ]` **Performance Testing**:
    *   Load testing conducted for expected peak event volume (e.g., during sales events).
    *   Load testing conducted for API endpoints (if any) for their expected load.
    *   Latency of event processing and notification dispatch measured under load.
    *   Sustainable throughput (events/sec, notifications/sec per channel) determined.
*   `[ ]` **Scalability Configuration**:
    *   Horizontal Pod Autoscaler (HPA) or equivalent configured with appropriate metrics (e.g., CPU utilization, custom metric like queue length if applicable).
    *   Minimum and maximum number of service replicas defined based on baseline load and peak load test results.
*   `[ ]` **Concurrency Management**:
    *   Strategy for managing concurrent calls to external providers is defined and tested (e.g., limiting concurrent outbound requests per provider, using appropriate asynchronous patterns like `Promise.allSettled` with batching).
    *   Connection limits or client pool sizes for provider SDKs are configured appropriately if applicable.
*   `[ ]` **Resource Requests and Limits**:
    *   Container CPU and memory requests and limits are defined in deployment configurations (Kubernetes, ECS).
    *   Requests are set based on typical usage; limits are set to prevent resource starvation.

---

## 5. Security (Ref: ADR-005 Authentication and Authorization, ADR-016 Configuration Management, ADR-019 API Gateway and Service Mesh Security, ADR-026 Security Best Practices)

**Overall Status**: `[ ] TODO`

*   `[ ]` **Credentials Management (ADR-016)**:
    *   All third-party provider API keys, tokens, and other secrets are securely stored (e.g., AWS Secrets Manager, HashiCorp Vault).
    *   Secrets are injected into the application environment, not hardcoded in code or version control.
*   `[ ]` **Input Validation**:
    *   Incoming event payloads are validated for required fields and basic data types.
    *   API request data (if API exists) is thoroughly validated (DTOs with `class-validator`).
*   `[ ]` **Permissions (Least Privilege)**:
    *   IAM roles for AWS services (SES, SNS, and the service's own execution role if on AWS - ADR-042) grant only the minimum necessary permissions.
*   `[ ]` **Webhook Security (if receiving delivery reports/bounces via webhooks)**:
    *   Endpoints are secured using HTTPS.
    *   Provider-specific signature verification mechanisms are implemented (e.g., Twilio request validation, AWS SNS subscription confirmation and signature validation).
    *   Consider IP whitelisting if provider IPs are stable and documented.
*   `[ ]` **Dependency Vulnerabilities**:
    *   Regular scans for known vulnerabilities in third-party libraries (`npm audit`, Snyk, Trivy).
    *   Process in place to update vulnerable dependencies promptly.
*   `[ ]` **Container Security**:
    *   Base Docker image is from a trusted source and regularly updated.
    *   Container image scanned for vulnerabilities.
    *   Application runs with a non-root user inside the container.
    *   No unnecessary tools or packages in the final image.
*   `[ ]` API Endpoints (if any) are protected by authentication and authorization (as per ADR-005, ADR-019).

---

## 6. Configuration Management (Ref: ADR-016 Configuration Management)

**Overall Status**: `[ ] TODO`

*   `[ ]` **Externalized Configuration**: All environment-specific configurations (provider keys/secrets references, sender details, retry settings, template paths if filesystem-based, DLQ names, default logging level) are externalized from the application code.
*   `[ ]` **Configuration Source**: Configurations managed via environment variables, Kubernetes ConfigMaps/Secrets, or a dedicated configuration service.
*   `[ ]` **Environment-Specific Configurations**: Separate and validated configurations exist for development, staging, and production environments.
*   `[ ]` **Sensitive Data Handling**: Configuration containing sensitive data is treated as secret and managed through secure mechanisms.

---

## 7. Third-Party Provider Management

**Overall Status**: `[ ] TODO`

*   `[ ]` **Account Setup**: Accounts are properly set up with AWS (for SES, SNS) and Twilio. Billing and administrative contacts are defined.
*   `[ ]` **Spending Limits/Alerts**:
    *   Billing alerts configured in AWS to monitor costs for SES and SNS.
    *   Spending limits or balance alerts configured in Twilio dashboard if available and appropriate.
*   `[ ]` **Quotas/Limits Understood & Managed**:
    *   AWS SES sending limits (daily quota, send rate) checked for the account in the production region. Process for requesting increases understood if needed.
    *   Twilio message throughput limits (MPS) for sender numbers/services understood.
    *   AWS SNS quotas (e.g., payload size, publish rate) reviewed.
*   `[ ]` **Feedback Mechanisms Configured**:
    *   **AWS SES**: Bounce, complaint, and delivery notifications configured (e.g., via SNS topics and SQS queues) for monitoring and list hygiene.
    *   **Twilio**: Webhooks for delivery reports (DLRs) and inbound messages (e.g., STOP replies) configured and tested.
    *   **AWS SNS**: Feedback for platform application endpoints (e.g., disabled tokens) configured for FCM and APNS to manage token lifecycle.
*   `[ ]` **Terms of Service (ToS)**: Relevant ToS for each provider reviewed for compliance, especially regarding message content, consent (for SMS), and data handling.
*   `[ ]` **Sender Identities Verified**:
    *   Email addresses/domains verified in AWS SES. DKIM and SPF records are correctly set up.
    *   Phone numbers/short codes properly provisioned and configured in Twilio. Any required sender ID registration for specific countries completed.

---

## 8. Data Management & Backup (if applicable, Ref: ADR-004 Database Selection, ADR-020 Database-per-Service, ADR-025 Data Backup and Recovery)

**Overall Status**: `[ ] TODO` (Mark N/A if no persistent storage owned by the service)

*   `[ ]` **Database Backup (if service uses its own DB for templates/logs)**:
    *   Automated backups configured (e.g., RDS snapshots).
    *   Backup frequency and retention period defined and meet RPO/RTO.
*   `[ ]` **Restore Procedures Tested (if applicable)**: Database restore procedures documented and tested.
*   `[ ]` **Data Retention Policies (if applicable)**:
    *   Defined for notification history logs or stored templates.
    *   Mechanism for archiving or purging old data in place if necessary and compliant with data privacy regulations.

---

## 9. Resilience & Fault Tolerance (Ref: ADR-022 Fault Tolerance and Resilience)

**Overall Status**: `[ ] TODO`

*   `[ ]` **Health Check Endpoints**:
    *   Liveness endpoint (`/health/live`) implemented.
    *   Readiness endpoint (`/health/ready`) implemented (checks connectivity to critical dependencies like message broker, database if applicable).
    *   Kubernetes/ECS liveness and readiness probes configured.
*   `[ ]` **Retry Mechanisms**:
    *   Retry logic for transient errors when calling external provider APIs is implemented and tested (using exponential backoff with jitter).
    *   Configurable number of retry attempts.
*   `[ ]` **Graceful Shutdown**: Service handles `SIGTERM` to shut down gracefully (finish processing in-flight messages within a timeout, close connections). Kubernetes `terminationGracePeriodSeconds` set appropriately.
*   `[ ]` **Dead-Letter Queue (DLQ) Strategy**:
    *   Unprocessable events (after retries, or due to malformed data) are routed to a DLQ in RabbitMQ.
    *   Process for monitoring and re-processing/discarding messages from the DLQ is defined.
*   `[ ]` **Provider Outage Contingency**: Basic understanding of behavior if a primary channel provider has an extended outage (e.g., logging, potential manual switch to an alternative if pre-configured, though not required for MVP).

---

## 10. Documentation

**Overall Status**: `[ ] TODO`

*   `[ ]` **API Documentation (if API exists)**: OpenAPI specification (`10-openapi-specification.md`) is up-to-date and accessible.
*   `[ ]` **Runbooks**:
    *   Troubleshooting steps for common issues (e.g., high event queue, provider API errors, high bounce rates).
    *   Procedure for checking notification status for a specific user/event (if feasible).
    *   Steps for handling DLQ messages.
    *   Contact information for third-party provider support.
*   `[ ]` **This Production Readiness Checklist**: Completed, reviewed, and signed off.
*   `[ ]` **Key ADRs**: Easily accessible and understood by the team.
*   `[ ]` **Onboarding Documentation**: Sufficient for new team members to understand the service's architecture, operation, and critical configurations.

---

## 11. Team & Operations

**Overall Status**: `[ ] TODO`

*   `[ ]` **Team Familiarity**: Development team members are familiar with the service architecture, common troubleshooting, monitoring dashboards, and log analysis.
*   `[ ]` **On-Call Plan**:
    *   On-call rotation schedule established and communicated.
    *   Primary and secondary on-call personnel defined.
    *   Access to all necessary tools (monitoring, logs, provider dashboards, infrastructure) for on-call personnel confirmed.
*   `[ ]` **Incident Response Plan**: Basic incident response procedures understood by the team (communication channels, escalation, post-mortem process).
*   `[ ]` **Dependencies Understood**: Team understands dependencies on other internal services (event sources) and external providers, including their SLAs or reliability characteristics.

---

**Final Review & Sign-off**:

*   `[ ]` Lead Developer:
*   `[ ]` Operations Lead/SRE:
*   `[ ]` Product Owner (if applicable):
*   `[ ]` Security Team Representative (if applicable):

Date: ______________
