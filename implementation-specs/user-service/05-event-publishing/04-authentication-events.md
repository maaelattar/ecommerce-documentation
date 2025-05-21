# 04 - Authentication Events

This document details domain events published by the User Service related to user authentication activities, including login attempts, session changes, and Multi-Factor Authentication (MFA) status updates.

Events adhere to the common event envelope (`StandardMessage<T>`) defined in `01-event-publishing-mechanism.md` and provided by the `@ecommerce-platform/rabbitmq-event-utils` library.
For routing, events will be published to a designated exchange (e.g., `user.events` or `auth.events`) with a routing key reflecting the event type (e.g., `auth.logged.in.v1`). The `userId` (if available) or other relevant identifiers will be included in the event payload and can also be populated in the `partitionKey` field of the `StandardMessage<T>` envelope if specific consumers require it for ordering or sharding.

## 1. `UserLoggedInEventV1`

*   **Description**: Published when a user successfully authenticates and a new session (or token set) is established.
*   **`eventType`**: `UserLoggedInEventV1`
*   **Trigger**: After `AuthService.login()` successfully validates credentials (and MFA, if applicable) and issues tokens.
*   **Payload Fields**:
    *   `userId` (string, UUID): The identifier of the logged-in user.
    *   `sessionId` (string, UUID, optional): A unique identifier for this specific session, if session management is stateful or if JWTs have a JTI used as a session ID.
    *   `loginTimestamp` (string, ISO 8601): Timestamp of the login event.
    *   `ipAddress` (string, optional): IP address from which the login occurred.
    *   `userAgent` (string, optional): User-Agent string of the client.
    *   `mfaVerified` (boolean, optional): True if MFA was challenged and successfully verified for this login.
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "sessionId": "s1s2s3s4-t5t6-7890-1234-567890ghijkl",
      "loginTimestamp": "2023-10-30T09:00:00.000Z",
      "ipAddress": "192.168.1.100",
      "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
      "mfaVerified": true
    }
    ```
*   **Potential Consumers**: Audit Log Service, Security Monitoring (for anomaly detection), User Service itself (e.g., update `lastLoginAt`), Analytics Service, Notification Service (optional login alert).

## 2. `UserLoginFailedEventV1`

*   **Description**: Published when a login attempt fails due to invalid credentials, inactive account, or other authentication errors (excluding MFA failure if handled separately).
*   **`eventType`**: `UserLoginFailedEventV1`
*   **Trigger**: Within `AuthService.login()` when primary credential validation fails.
*   **Payload Fields**:
    *   `attemptedEmail` (string, optional): The email address used in the login attempt. (Use `attemptedUsername` if username is used for login).
    *   `attemptedUserId` (string, UUID, optional): User ID if the user was identified but password failed.
    *   `failureTimestamp` (string, ISO 8601): Timestamp of the failed attempt.
    *   `reason` (string, enum): Reason for failure (e.g., `invalid_credentials`, `account_inactive`, `account_locked`, `user_not_found`).
    *   `ipAddress` (string, optional): IP address from which the attempt occurred.
    *   `userAgent` (string, optional): User-Agent string of the client.
*   **Example Payload**:
    ```json
    {
      "attemptedEmail": "user@example.com",
      "failureTimestamp": "2023-10-30T09:05:00.000Z",
      "reason": "invalid_credentials",
      "ipAddress": "203.0.113.45",
      "userAgent": "Mozilla/5.0 ..."
    }
    ```
*   **Potential Consumers**: Security Monitoring (for brute-force detection, account lockout logic), Audit Log Service.

## 3. `UserLoggedOutEventV1`

*   **Description**: Published when a user explicitly logs out or their session/tokens are intentionally invalidated.
*   **`eventType`**: `UserLoggedOutEventV1`
*   **Trigger**: After `AuthService.logout()` successfully invalidates tokens/session.
*   **Payload Fields**:
    *   `userId` (string, UUID): The identifier of the user who logged out.
    *   `sessionId` (string, UUID, optional): The specific session ID that was terminated, if applicable.
    *   `logoutTimestamp` (string, ISO 8601): Timestamp of the logout event.
    *   `revokedTokenJtis` (array of strings, optional): JTIs of access/refresh tokens that were revoked.
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "sessionId": "s1s2s3s4-t5t6-7890-1234-567890ghijkl",
      "logoutTimestamp": "2023-10-30T10:00:00.000Z",
      "revokedTokenJtis": ["jti-access-xyz", "jti-refresh-abc"]
    }
    ```
*   **Potential Consumers**: Audit Log Service, User Service (e.g., for clearing session-related data if any), Analytics.

## 4. `MfaStatusChangedEventV1`

*   **Description**: Published when a user's Multi-Factor Authentication (MFA) status changes (e.g., MFA enabled, MFA disabled, MFA method changed).
*   **`eventType`**: `MfaStatusChangedEventV1`
*   **Trigger**: After `AuthService.verifyAndEnableMfa()`, `AuthService.disableMfa()`, etc.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `mfaEnabled` (boolean): The new MFA status (true if enabled, false if disabled).
    *   `mfaMethod` (string, optional): The MFA method involved (e.g., `TOTP`, `SMS`, `U2F`), if applicable.
    *   `changeTimestamp` (string, ISO 8601): Timestamp of the MFA status change.
    *   `changedBy` (string, optional): `user` or `admin` (if admin can manage MFA settings).
*   **Example Payload (MFA Enabled)**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "mfaEnabled": true,
      "mfaMethod": "TOTP",
      "changeTimestamp": "2023-10-30T11:00:00.000Z",
      "changedBy": "user"
    }
    ```
*   **Potential Consumers**: Notification Service (to inform the user of MFA status changes), Audit Log Service, Auth Service (to adjust login flow based on MFA status).

## 5. `MfaChallengeFailedEventV1` (Optional)

*   **Description**: Published when an MFA challenge fails during login.
*   **`eventType`**: `MfaChallengeFailedEventV1`
*   **Trigger**: Within `AuthService.verifyMfaChallenge()` or similar logic when an MFA code is incorrect.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user attempting the MFA challenge.
    *   `failureTimestamp` (string, ISO 8601): Timestamp of the failed attempt.
    *   `mfaMethod` (string, optional): The MFA method that was challenged.
    *   `ipAddress` (string, optional): IP address from which the attempt occurred.
    *   `userAgent` (string, optional): User-Agent string of the client.
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "failureTimestamp": "2023-10-30T09:02:00.000Z",
      "mfaMethod": "TOTP",
      "ipAddress": "203.0.113.45",
      "userAgent": "Mozilla/5.0 ..."
    }
    ```
*   **Potential Consumers**: Security Monitoring (for repeated MFA failures), Audit Log Service.

These authentication-related events provide critical signals for security monitoring, auditing, and ensuring consistent user session state awareness across the platform.
