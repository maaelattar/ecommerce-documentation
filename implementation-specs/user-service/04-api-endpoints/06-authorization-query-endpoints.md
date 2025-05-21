# 06 - Authorization Query Endpoints (Optional/Internal)

This document outlines optional API endpoints that could be exposed by the User Service to allow other internal services to query authorization status or effective permissions for a user. Exposing such endpoints directly should be carefully considered due to potential performance implications, security risks, and increased coupling between services.

Often, it's preferred that services make authorization decisions based on information embedded in JWTs (like roles/permissions) or by calling a dedicated, highly optimized authorization service (like an OPA sidecar or a central policy decision point) rather than direct synchronous calls to the User Service for every check.

However, for certain use cases or simpler architectures, these query endpoints might be useful.

## 1. Check User Permissions

*   **Endpoint**: `POST /auth/check-permissions` (or `/authorize/check`)
*   **Description**: Allows an internal service (acting on behalf of a user or with its own identity) to check if a specific user has a set of required permissions, potentially against a specific resource or context.
*   **Request Body**:
    ```json
    // Example Request
    {
      "userId": "user-uuid-123", // The user whose permissions are being checked
      "requiredPermissions": ["product:edit", "product:publish"],
      "resourceContext": { // Optional: for ABAC-style checks
        "type": "product",
        "id": "product-uuid-abc",
        "ownerId": "user-uuid-123"
      }
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    // Example Response (Granted)
    {
      "userId": "user-uuid-123",
      "granted": true,
      "checkedPermissions": {
        "product:edit": true,
        "product:publish": true
      }
    }
    // Example Response (Denied)
    {
      "userId": "user-uuid-123",
      "granted": false,
      "reason": "Missing required permission: product:publish", // Optional detail
      "checkedPermissions": {
        "product:edit": true,
        "product:publish": false
      }
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Invalid input (e.g., missing `userId` or `requiredPermissions`).
    *   `401 Unauthorized` / `403 Forbidden`: If the calling service is not authorized to make this query.
    *   `404 Not Found`: If the `userId` does not exist.
*   **Authentication**: Required (typically service-to-service authentication, e.g., client credentials OAuth flow, mutual TLS, or a trusted internal network with API key).
*   **Permissions**: The calling service might need a specific permission like `authorization:query`.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(InternalServiceAuthGuard) // A guard for service-to-service calls
    @Post('check-permissions')
    async checkUserPermissions(@Body() checkDto: CheckPermissionsDto): Promise<CheckPermissionsResponseDto> {
      const { userId, requiredPermissions, resourceContext } = checkDto;
      const user = await this.userService.findById(userId);
      if (!user) throw new NotFoundException('User not found.');
      
      // Populate user roles if not already on the user object
      const userWithRoles = await this.roleService.populateUserRoles(user); 

      let allGranted = true;
      const checkedPermissionsResult: Record<string, boolean> = {};
      let denialReason = '';

      for (const perm of requiredPermissions) {
        // The AuthorizationService.can() method would handle the logic of checking roles and permissions
        const hasPerm = await this.authorizationService.can(userWithRoles, perm, resourceContext);
        checkedPermissionsResult[perm] = hasPerm;
        if (!hasPerm) {
          allGranted = false;
          if (!denialReason) denialReason = `Missing required permission: ${perm}`;
        }
      }

      return {
        userId,
        granted: allGranted,
        reason: denialReason,
        checkedPermissions: checkedPermissionsResult,
      };
    }
    ```

## 2. Get Effective Permissions for User

*   **Endpoint**: `GET /users/{userId}/effective-permissions`
*   **Description**: Retrieves a list of all effective permissions for a given user. This is computationally more intensive and should be used sparingly.
*   **Path Parameters**: `userId`.
*   **Query Parameters**: `resourceType` (optional, to filter permissions relevant to a specific resource type).
*   **Success Response (200 OK)**:
    ```json
    // Example Response
    {
      "userId": "user-uuid-123",
      "effectivePermissions": [
        "product:create",
        "product:view_own",
        "order:create",
        "profile:edit_own"
        // ... and so on
      ],
      "roles": ["customer", "beta-tester"]
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized` / `403 Forbidden`.
    *   `404 Not Found`: User not found.
*   **Authentication**: Required (Admin or trusted internal service).
*   **Permissions**: Required (e.g., `user:read_effective_permissions`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard) // Or InternalServiceAuthGuard
    @RequiredPermissions('user:read_effective_permissions') // Example
    @Get(':userId/effective-permissions')
    async getEffectivePermissions(
        @Param('userId', ParseUUIDPipe) userId: string,
        @Query('resourceType') resourceType?: string
    ): Promise<EffectivePermissionsResponseDto> {
      const user = await this.userService.findById(userId);
      if (!user) throw new NotFoundException('User not found.');

      const userWithRoles = await this.roleService.populateUserRoles(user);
      let allPermissions = new Set<string>();
      const roleNames: string[] = [];

      if (userWithRoles.roles) {
        for (const role of userWithRoles.roles) {
          roleNames.push(role.name);
          const permsForRole = await this.permissionService.getPermissionsForRole(role.id);
          permsForRole.forEach(p => {
            if (resourceType) {
              // Simple filter example: permission name might be like "resourceType:action"
              if (p.subject === resourceType || p.name.startsWith(resourceType + ':')) {
                allPermissions.add(p.name);
              }
            } else {
              allPermissions.add(p.name);
            }
          });
        }
      }
      
      return {
        userId,
        effectivePermissions: Array.from(allPermissions),
        roles: roleNames,
      };
    }
    ```

## Considerations for Exposing Authorization Queries:

*   **Performance**: Repeatedly querying these endpoints can be slow. Caching at the User Service (e.g., user roles/permissions) and at the client service is crucial.
*   **Security**: Ensure these endpoints are not publicly accessible and are only callable by trusted internal services with proper authentication/authorization.
*   **Coupling**: Creates a direct runtime dependency from other services to the User Service for authorization decisions. If User Service is down, other services might not be able to perform authorization.
*   **Alternative - JWT Claims**: A common pattern is to embed essential roles and/or fine-grained permissions directly into the user's JWT access token. This allows other services to inspect the JWT and make many authorization decisions locally without calling back to the User Service. The JWT payload size is a constraint here.
*   **Alternative - Centralized Policy Engine**: For complex scenarios, using a dedicated policy engine like Open Policy Agent (OPA) can be more scalable. Services query OPA, which has its policies synced or loaded, potentially including data from the User Service.

These query endpoints should be implemented with caution and only if simpler alternatives (like JWT claims) are insufficient.
