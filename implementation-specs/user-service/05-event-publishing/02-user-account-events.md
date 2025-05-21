# 02 - User Account Events

This document details the key domain events published by the User Service related to core user account lifecycle and management. These events are crucial for other services to react to changes in user status, identity, and existence.

Events adhere to the common event envelope (`StandardMessage<T>`) defined in `01-event-publishing-mechanism.md` and provided by the `@ecommerce-platform/rabbitmq-event-utils` library.
For routing, events will be published to a designated exchange (e.g., `user.events`) with a routing key reflecting the event type (e.g., `user.registered.v1`). The `userId` will be included in the event payload and can also be populated in the `partitionKey` field of the `StandardMessage<T>` envelope if specific consumers require it for ordering or sharding.

## 1. `UserRegisteredEventV1`

*   **Description**: Published when a new user successfully completes the registration process and their core account record is created.
*   **`eventType`**: `UserRegisteredEventV1`
*   **Trigger**: After successful user creation in `AuthService.register()` or `UserService.createUser()`.
*   **Payload Fields**:
    *   `userId` (string, UUID): The unique identifier for the new user.
    *   `email` (string): The user's registered email address.
    *   `username` (string, optional): The user's chosen username, if applicable.
    *   `firstName` (string, optional): User's first name, if provided during registration.
    *   `lastName` (string, optional): User's last name, if provided during registration.
    *   `status` (string, enum): The initial status of the user account (e.g., `pending_verification`, `active`).
    *   `registrationTimestamp` (string, ISO 8601): Timestamp of when the registration occurred.
    *   `source` (string, optional): How the user registered (e.g., `direct`, `google_oauth`).
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "email": "newuser@example.com",
      "username": "newbie23",
      "firstName": "John",
      "lastName": "Doe",
      "status": "pending_verification",
      "registrationTimestamp": "2023-10-28T12:05:00.000Z",
      "source": "direct"
    }
    ```
*   **Potential Consumers**: Notification Service (welcome email, verification email), Search Service (to index user if searchable), Analytics Service.

## 2. `UserEmailVerifiedEventV1`

*   **Description**: Published when a user successfully verifies their email address through a verification link or code.
*   **`eventType`**: `UserEmailVerifiedEventV1`
*   **Trigger**: After `AuthService.verifyEmail()` successfully validates an email verification token.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `email` (string): The email address that was verified.
    *   `verificationTimestamp` (string, ISO 8601): Timestamp of when the email was verified.
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "email": "newuser@example.com",
      "verificationTimestamp": "2023-10-28T14:30:00.000Z"
    }
    ```
*   **Potential Consumers**: User Service itself (to update user status), Notification Service (confirmation email), other services that unlock features upon email verification.

## 3. `UserPasswordChangedEventV1`

*   **Description**: Published when a user successfully changes their password (either through self-service change or administrative reset completion).
*   **`eventType`**: `UserPasswordChangedEventV1`
*   **Trigger**: After `AuthService.changePassword()` or `AuthService.resetPassword()` successfully updates the password.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `changeTimestamp` (string, ISO 8601): Timestamp of when the password was changed.
    *   `changeType` (string, enum): `self_initiated` or `reset_completed`.
*   **Important**: The event payload **MUST NOT** contain any password data (new or old).
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "changeTimestamp": "2023-10-29T09:15:00.000Z",
      "changeType": "self_initiated"
    }
    ```
*   **Potential Consumers**: Notification Service (security alert email), Auth Service (to invalidate older sessions/tokens associated with this user).

## 4. `UserPasswordResetRequestedEventV1`

*   **Description**: Published when a user initiates a password reset request.
*   **`eventType`**: `UserPasswordResetRequestedEventV1`
*   **Trigger**: After `AuthService.requestPasswordReset()`.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `email` (string): The email address for which the reset was requested.
    *   `requestTimestamp` (string, ISO 8601): Timestamp of the request.
    *   `resetTokenIdentifier` (string, optional): A non-sensitive identifier for the token if needed for tracking, but not the token itself.
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "email": "user@example.com",
      "requestTimestamp": "2023-10-29T08:00:00.000Z"
    }
    ```
*   **Potential Consumers**: Notification Service (to send the password reset email), Audit Log Service.

## 5. `UserAccountStatusChangedEventV1`

*   **Description**: Published when a user's account status changes (e.g., activated, suspended, banned, marked for deletion).
*   **`eventType`**: `UserAccountStatusChangedEventV1`
*   **Trigger**: After `UserService.changeUserStatus()` or similar administrative actions.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `newStatus` (string, enum): The new status of the account (e.g., `active`, `suspended`, `banned`, `deleted`).
    *   `previousStatus` (string, enum): The previous status of the account.
    *   `changeTimestamp` (string, ISO 8601): Timestamp of the status change.
    *   `reason` (string, optional): Reason for the status change, if applicable (especially for suspension/banning).
    *   `changedBy` (string, optional): Identifier of the admin or system process that initiated the change.
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "newStatus": "suspended",
      "previousStatus": "active",
      "changeTimestamp": "2023-10-29T10:00:00.000Z",
      "reason": "Violation of terms of service.",
      "changedBy": "admin-user-xyz"
    }
    ```
*   **Potential Consumers**: Auth Service (to deny login for suspended/banned users), Notification Service (to inform user), other services that need to react to account status.

## 6. `UserUpdatedEventV1`

*   **Description**: Published when core, non-sensitive user account information (e.g., username, non-primary email if supported) is updated. This is distinct from profile updates or sensitive changes like password or primary email if it requires verification.
*   **`eventType`**: `UserUpdatedEventV1`
*   **Trigger**: After `UserService.updateUser()` for relevant fields.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `updatedFields` (object or array of strings): Specifies which fields were updated. Can include old and new values if necessary and not too verbose, or just the new state of changed fields.
        *   Example: `{"username": "new_username"}` or `["username", "secondaryEmail"]`
    *   `updateTimestamp` (string, ISO 8601): Timestamp of the update.
*   **Example Payload (showing changed fields with new values)**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "updatedFields": {
        "username": "brandNewName2024"
      },
      "updateTimestamp": "2023-10-29T11:00:00.000Z"
    }
    ```
*   **Potential Consumers**: Search Service (if user details are indexed), Analytics, other services displaying user information.

## 7. `UserDeletedEventV1`

*   **Description**: Published when a user's account is deleted (either soft or hard delete).
*   **`eventType`**: `UserDeletedEventV1`
*   **Trigger**: After `UserService.deleteUser()`.
*   **Payload Fields**:
    *   `userId` (string, UUID): The identifier of the deleted user.
    *   `email` (string): The email of the deleted user (important for cleanup in other systems if `userId` is not the primary key there).
    *   `deletionType` (string, enum): `soft` or `hard`.
    *   `deletionTimestamp` (string, ISO 8601): Timestamp of the deletion.
    *   `anonymized` (boolean, optional): True if user data was anonymized rather than fully removed (common with soft delete).
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "email": "deleteduser@example.com",
      "deletionType": "soft",
      "deletionTimestamp": "2023-10-29T18:00:00.000Z",
      "anonymized": true
    }
    ```
*   **Potential Consumers**: All services that store user-specific data, for cleanup, anonymization, or marking records as belonging to a deleted user. Search Service (to de-index). Notification Service (final confirmation or related communication).

These events cover the fundamental lifecycle of a user account. Other, more specific events (like MFA status changes) will be detailed separately if they are considered part of the core account rather than just authentication flow.
