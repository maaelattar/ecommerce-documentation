# Core Service Components - Overview

This section details the core internal components of the User Service. These components encapsulate the primary business logic and functionalities of the service.

We will document the following key components:

1.  **`AuthService`**:
    *   Handles user registration, login (authentication), password management (hashing, reset, change), and token generation (JWT).
    *   Manages Multi-Factor Authentication (MFA) logic.

2.  **`UserService` (or `UserAccountService`)**:
    *   Manages core user account information (CRUD operations on the `User` entity).
    *   Handles account status changes (activation, suspension, deletion).

3.  **`UserProfileService`**:
    *   Manages user profile data (CRUD operations on the `UserProfile` and `Address` entities).
    *   Handles user preferences and settings.

4.  **`RoleService`**:
    *   Manages roles within the system (CRUD operations on the `Role` entity).
    *   Links roles to users.

5.  **`PermissionService`**:
    *   Manages permissions (CRUD operations on the `Permission` entity).
    *   Potentially handles checking if a user/role has a specific permission (though this might also be part of an `AuthorizationService`).

6.  **`AuthorizationService`**:
    *   Determines if a user has the necessary permissions to perform an action or access a resource.
    *   Works in conjunction with `RoleService` and `PermissionService`.
    *   Implements RBAC (Role-Based Access Control) and potentially ABAC (Attribute-Based Access Control) policies.

7.  **`UserEventPublisher` (or integrated within other services)**:
    *   Responsible for publishing events related to user actions (e.g., `UserCreated`, `UserUpdated`, `PasswordChanged`).

8.  **`PasswordPolicyService`**:
    *   Enforces password complexity rules, expiration, and history.
    *   Validates new passwords against these policies.

9.  **`TokenService` (or integrated within `AuthService`)**:
    *   Specifically handles the creation, validation, and revocation of various token types (e.g., JWT access tokens, refresh tokens, password reset tokens, email verification tokens).

10. **`DataValidationService` (or using NestJS Pipes)**:
    *   Ensures the integrity and correctness of incoming data for all service operations using DTOs and validation rules.

Each component will be detailed in its own markdown file, outlining its responsibilities, key methods, interactions with other components and entities, and any specific design considerations or patterns employed.
