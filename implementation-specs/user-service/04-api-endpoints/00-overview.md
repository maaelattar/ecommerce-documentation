# API Endpoints - Overview

This section provides detailed specifications for the API endpoints exposed by the User Service. These endpoints allow clients (e.g., frontend applications, other microservices) to interact with user data, manage authentication, profiles, roles, and permissions.

Each group of related endpoints will be detailed in its own markdown file, covering:

*   Endpoint URL and HTTP method.
*   Brief description of functionality.
*   Request parameters (path, query, body with DTOs).
*   Example request payloads.
*   Response formats (success and error cases).
*   Example response payloads.
*   Required permissions or authentication level.
*   Relevant NestJS controller and method signatures (conceptual).

Key categories of API endpoints to be documented include:

1.  **Authentication Endpoints**:
    *   User registration.
    *   Login (credential-based).
    *   Logout.
    *   Token refresh.
    *   Password management (request reset, reset password, change password).
    *   MFA setup and verification.
    *   Email verification (request and confirm).

2.  **User Account Management Endpoints**:
    *   Retrieve current authenticated user's details.
    *   Update current authenticated user's core account details (e.g., email - may trigger verification).
    *   Close/delete current authenticated user's account.
    *   (Admin) List all users (with pagination, filtering).
    *   (Admin) Retrieve a specific user's details by ID.
    *   (Admin) Update a specific user's account (e.g., status, email).
    *   (Admin) Delete a specific user's account.

3.  **User Profile Management Endpoints**:
    *   Retrieve current authenticated user's profile.
    *   Create/update current authenticated user's profile.
    *   Manage addresses for the current user (CRUD).
    *   Set default shipping/billing address for the current user.
    *   (Admin) Retrieve a specific user's profile by user ID.
    *   (Admin) Update a specific user's profile.

4.  **Role Management Endpoints (Admin)**:
    *   Create a new role.
    *   List all roles.
    *   Retrieve a specific role's details.
    *   Update a role.
    *   Delete a role.
    *   Assign roles to a user.
    *   Remove roles from a user.
    *   List users in a specific role.
    *   List roles for a specific user.

5.  **Permission Management Endpoints (Admin)**:
    *   Create a new permission.
    *   List all permissions.
    *   Retrieve a specific permission's details.
    *   Update a permission.
    *   Delete a permission.
    *   Assign permissions to a role.
    *   Remove permissions from a role.
    *   List permissions for a specific role.
    *   List roles that have a specific permission.

6.  **Authorization Query Endpoints (Optional/Internal)**:
    *   Endpoints to check if a user has a specific permission (potentially for other services, though direct service-to-service calls for authorization checks should be carefully considered for performance and coupling).

Each of these will be broken down into individual markdown files for clarity and detail.
