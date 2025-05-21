# 09 - Security Service Integration

This document outlines how the User Service integrates with a centralized Security Service or Security Information and Event Management (SIEM) system. Such integration is vital for comprehensive security monitoring, threat detection, incident response, and audit logging across the platform.

## 1. Purpose of Integration

*   **Centralized Security Auditing**: To send detailed, security-relevant audit logs from the User Service to a central system for storage, analysis, and compliance reporting.
*   **Threat Detection**: To feed security events into a SIEM or Security Service that can correlate events from multiple sources (including the User Service) to detect suspicious patterns, anomalies, or potential attacks (e.g., brute-force attempts, credential stuffing, privilege escalation).
*   **Incident Response**: To provide security operations teams with the necessary data from the User Service to investigate and respond to security incidents.
*   **Receiving Security Directives (Less Common)**: In some advanced scenarios, the User Service might receive directives from a Security Service (e.g., to temporarily block an IP range, force MFA for a user group, or adjust security policies based on global threat levels).

## 2. Key Security Events from User Service to Security Service/SIEM

Many of the domain events published to Kafka for general inter-service communication (detailed in `05-event-publishing/`) are also highly relevant for security. The Security Service/SIEM would be a consumer of these events. Additionally, more granular audit logs might be sent directly or via a separate mechanism.

*   **Events Consumed from Kafka `user.events` topic**:
    *   `UserRegisteredEventV1` (new account creation)
    *   `UserLoggedInEventV1` (successful logins, including IP, user-agent)
    *   `UserLoginFailedEventV1` (failed login attempts, reason, IP, user-agent)
    *   `UserPasswordChangedEventV1` (password changes)
    *   `UserPasswordResetRequestedEventV1` (password reset initiations)
    *   `UserAccountStatusChangedEventV1` (suspensions, bans, activations)
    *   `MfaStatusChangedEventV1` (MFA enabled/disabled)
    *   `MfaChallengeFailedEventV1` (if published)
    *   `RoleCreatedEventV1`, `RoleUpdatedEventV1`, `RoleDeletedEventV1`
    *   `UserRoleAssignedEventV1`, `UserRoleRemovedEventV1`
    *   `PermissionCreatedEventV1`, `PermissionDeletedEventV1`
    *   `PermissionAssignedToRoleEventV1`, `PermissionRemovedFromRoleEventV1`

*   **Dedicated Audit Logs (Potentially more granular or different format)**:
    *   Attempts to access unauthorized resources (403 Forbidden responses).
    *   Admin actions performed via User Service APIs (e.g., an admin viewed user X's profile, an admin changed user Y's status).
    *   Changes to User Service configuration if done dynamically (e.g., password policy updates).
    *   Token validation failures at User Service API endpoints.

## 3. Integration Mechanisms

### a. Consuming Kafka Events

*   **Mechanism**: The Security Service / SIEM's data ingestion pipeline acts as a Kafka consumer, subscribing to the `user.events` topic (and other relevant topics from other services).
*   **Data Format**: Consumes the standard JSON events.
*   **Enrichment**: The Security Service might enrich these events with additional context (e.g., geolocation of IP addresses, threat intelligence feeds).

### b. Direct Log Shipping / API Push for Audit Logs

*   **Mechanism (Log Shipping)**: If User Service generates specific audit logs in a particular format (e.g., CEF - Common Event Format), a log shipper agent (like Filebeat with specific modules, or a custom agent) could be configured to collect these audit logs and send them directly to the SIEM.
*   **Mechanism (API Push)**: Less common for high volume, but the User Service could theoretically push critical audit events directly to an API exposed by the Security Service/SIEM. This creates a tighter coupling.
*   **User Service Approach**: Primarily rely on the Security Service/SIEM consuming the rich domain events from Kafka. Specific, highly critical audit data not suitable for the general event stream might be logged to a specific file that is then shipped, or if an internal audit service API exists, it could be called.

## 4. Data Sent to Security Service/SIEM

*   **Event Type/Name**
*   **Timestamp**
*   **Source Service** (`UserService`)
*   **Correlation ID** (to trace requests across services)
*   **User Identifiers** (`userId`, `email`, `username` - as appropriate and balanced with privacy for the security context).
*   **IP Addresses** and **User Agents** (for login, failed login, etc.)
*   **Action Performed** (e.g., `login_attempt`, `password_change`, `role_created`).
*   **Subject of Action** (e.g., target `userId`, target `roleId`).
*   **Outcome** (e.g., `success`, `failure`).
*   **Reason for Outcome** (e.g., `invalid_credentials`, `permission_denied`).
*   **Actor/Perpetrator** (e.g., `userId` of user performing action, `adminId` if admin action, `service_name` if system action).
*   **Critical Changes**: Details of what was changed (e.g., for `RoleUpdatedEventV1`, the old and new description if relevant for security policy changes).

## 5. Security of the Integration Itself

*   **Secure Channel to Kafka**: If consuming via Kafka, the Security Service consumer must connect securely (TLS, SASL authentication, authorized via ACLs) as per `10-event-security.md`.
*   **Secure Log Shipping**: If using direct log shipping, the channel between the User Service environment and the SIEM must be encrypted and authenticated.
*   **API Security (if applicable)**: If User Service pushes to a Security Service API, that API must be secured (mTLS, OAuth2, etc.).

## 6. Receiving Directives from Security Service (Conceptual)

This is an advanced and less common integration pattern.

*   **Scenario**: A central Security Service detects a large-scale attack or a compromised user account and needs to instruct the User Service to take immediate action.
*   **Mechanism**:
    *   The Security Service might call a specific, highly secured administrative API on the User Service.
    *   Example: `POST /admin/security-actions/block-user` with payload `{"userId": "user-to-block", "reason": "Compromised account detected"}`.
    *   Alternatively, User Service could subscribe to a specific Kafka topic where the Security Service publishes actionable directives.
*   **Actions**: Block user, force logout, require MFA for all users in a group, block IP range (though IP blocking is often better at gateway/WAF level).
*   **Security**: This requires extreme trust and robust authentication/authorization for the Security Service principal calling the User Service. The APIs must be narrowly scoped.

Integration with a Security Service/SIEM is non-negotiable for a production-grade User Service, providing essential visibility into security posture and enabling effective incident response.
