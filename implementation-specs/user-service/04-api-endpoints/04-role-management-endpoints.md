# 04 - Role Management Endpoints (Admin)

This document specifies the API endpoints for managing roles within the system. These operations are typically restricted to administrators with appropriate permissions.

Endpoints are usually prefixed like `/admin/roles`.

## 1. Create a New Role

*   **Endpoint**: `POST /admin/roles`
*   **Description**: Creates a new role in the system.
*   **Request Body**: `CreateRoleDto`
    ```json
    // Example Request
    {
      "name": "editor",
      "description": "Can edit content and manage articles.",
      "permissions": ["permission-uuid-001", "permission-uuid-002"] // Optional: Assign permissions on creation
    }
    ```
*   **Success Response (201 Created)**: The created `Role` object, potentially with assigned permissions.
    ```json
    // Example Response
    {
      "id": "role-uuid-xyz",
      "name": "editor",
      "description": "Can edit content and manage articles.",
      "createdAt": "2023-10-28T10:00:00Z",
      "updatedAt": "2023-10-28T10:00:00Z",
      "permissions": [
        { "id": "permission-uuid-001", "name": "article:create", ... },
        { "id": "permission-uuid-002", "name": "article:edit_own", ... }
      ]
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Validation errors (e.g., name conflict, invalid permission IDs).
    *   `401 Unauthorized` / `403 Forbidden`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:create`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:create')
    @Post()
    @HttpCode(HttpStatus.CREATED)
    async createRole(@Body() createRoleDto: CreateRoleDto): Promise<RoleDetailDto> {
      const role = await this.roleService.createRole(createRoleDto);
      // If permissions are assigned during creation, RoleService handles that logic
      return mapRoleToDetailDto(role); // Includes permissions
    }
    ```

## 2. List All Roles

*   **Endpoint**: `GET /admin/roles`
*   **Description**: Retrieves a list of all roles in the system. May support pagination.
*   **Query Parameters**: `page`, `limit`, `sortBy`, `sortOrder` (optional).
*   **Success Response (200 OK)**: Array of `RoleDto` or a paginated response object.
    ```json
    // Example (Non-paginated)
    [
      { "id": "role-uuid-abc", "name": "administrator", "description": "Full system access" },
      { "id": "role-uuid-xyz", "name": "editor", "description": "Can edit content..." }
    ]
    // Example (Paginated)
    {
        "data": [
            { "id": "role-uuid-abc", "name": "administrator", ... },
            { "id": "role-uuid-xyz", "name": "editor", ... }
        ],
        "meta": { "totalItems": 2, ... }
    }
    ```
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:list`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:list')
    @Get()
    async findAllRoles(@Query() queryParams: ListQueryDto): Promise<PaginatedResponseDto<RoleDto>> {
      return this.roleService.findAllRolesPaginated(queryParams);
    }
    ```

## 3. Retrieve a Specific Role's Details

*   **Endpoint**: `GET /admin/roles/{roleId}`
*   **Description**: Fetches detailed information about a specific role, including its assigned permissions.
*   **Path Parameters**: `roleId`.
*   **Success Response (200 OK)**: `RoleDetailDto` (same format as create response).
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:read_one`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:read_one')
    @Get(':roleId')
    async findRoleById(@Param('roleId', ParseUUIDPipe) roleId: string): Promise<RoleDetailDto> {
      const role = await this.roleService.findRoleWithPermissions(roleId);
      if (!role) throw new NotFoundException('Role not found.');
      return mapRoleToDetailDto(role);
    }
    ```

## 4. Update a Role

*   **Endpoint**: `PUT /admin/roles/{roleId}` or `PATCH /admin/roles/{roleId}`
*   **Description**: Updates an existing role's properties (name, description).
*   **Path Parameters**: `roleId`.
*   **Request Body**: `UpdateRoleDto`
    ```json
    {
      "name": "content_editor",
      "description": "Can edit and publish articles."
    }
    ```
*   **Success Response (200 OK)**: Updated `RoleDetailDto`.
*   **Error Responses**: `400 Bad Request` (validation, name conflict), `401/403`, `404 Not Found`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:update`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:update')
    @Put(':roleId') // Or @Patch for partial updates
    async updateRole(
      @Param('roleId', ParseUUIDPipe) roleId: string,
      @Body() updateRoleDto: UpdateRoleDto,
    ): Promise<RoleDetailDto> {
      const role = await this.roleService.updateRole(roleId, updateRoleDto);
      return mapRoleToDetailDto(role);
    }
    ```

## 5. Delete a Role

*   **Endpoint**: `DELETE /admin/roles/{roleId}`
*   **Description**: Deletes a role from the system. Behavior when role is in use (assigned to users) should be considered (e.g., prevent deletion, unassign users).
*   **Path Parameters**: `roleId`.
*   **Success Response (204 No Content)**.
*   **Error Responses**: `400 Bad Request` (e.g., role in use), `401/403`, `404 Not Found`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:delete`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:delete')
    @Delete(':roleId')
    @HttpCode(HttpStatus.NO_CONTENT)
    async deleteRole(@Param('roleId', ParseUUIDPipe) roleId: string): Promise<void> {
      await this.roleService.deleteRole(roleId);
    }
    ```

## User-Role Assignments (Often part of Role Management or User Management by Admin)

### 6. Assign Roles to a User

*   **Endpoint**: `POST /admin/users/{userId}/roles` (Could also be `/admin/roles/{roleId}/users`)
*   **Description**: Assigns one or more existing roles to a specific user.
*   **Path Parameters**: `userId`.
*   **Request Body**:
    ```json
    {
      "roleIds": ["role-uuid-editor", "role-uuid-contributor"]
    }
    ```
*   **Success Response (200 OK)**: List of roles now assigned to the user or the updated User object.
    ```json
    // Example: Updated User DTO with roles
    {
        "id": "user-uuid-123",
        "email": "someuser@example.com",
        "roles": [
            { "id": "role-uuid-editor", "name": "editor" },
            { "id": "role-uuid-contributor", "name": "contributor" }
        ]
        // ... other user fields
    }
    ```
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `user:assign_roles`).
*   **Conceptual Controller Method (on UserController)**:
    ```typescript
    // In AdminUserController.ts
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('user:assign_roles')
    @Post(':userId/roles')
    async assignRolesToUser(
      @Param('userId', ParseUUIDPipe) userId: string,
      @Body() assignRolesDto: AssignRolesToUserDto, // { roleIds: string[] }
    ): Promise<UserWithRolesDto> {
      return this.roleService.assignRolesToUser(userId, assignRolesDto.roleIds);
    }
    ```

### 7. Remove Roles from a User

*   **Endpoint**: `DELETE /admin/users/{userId}/roles`
*   **Description**: Removes one or more roles from a specific user.
*   **Path Parameters**: `userId`.
*   **Request Body**:
    ```json
    {
      "roleIds": ["role-uuid-contributor"]
    }
    ```
*   **Success Response (200 OK)**: Updated list of user's roles or updated User object.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `user:remove_roles`).
*   **Conceptual Controller Method (on UserController)**:
    ```typescript
    // In AdminUserController.ts
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('user:remove_roles')
    @Delete(':userId/roles') // Using DELETE method for removal
    async removeRolesFromUser(
      @Param('userId', ParseUUIDPipe) userId: string,
      @Body() removeRolesDto: RemoveRolesFromUserDto, // { roleIds: string[] }
    ): Promise<UserWithRolesDto> {
      return this.roleService.removeRolesFromUser(userId, removeRolesDto.roleIds);
    }
    ```

### 8. List Users in a Specific Role

*   **Endpoint**: `GET /admin/roles/{roleId}/users`
*   **Description**: Retrieves a paginated list of users who are assigned a specific role.
*   **Path Parameters**: `roleId`.
*   **Query Parameters**: `page`, `limit`.
*   **Success Response (200 OK)**: Paginated list of `UserDto`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:list_users`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:list_users')
    @Get(':roleId/users')
    async findUsersInRole(
      @Param('roleId', ParseUUIDPipe) roleId: string,
      @Query() queryParams: ListQueryDto,
    ): Promise<PaginatedResponseDto<UserDto>> {
      return this.roleService.findUsersByRole(roleId, queryParams);
    }
    ```

### 9. List Roles for a Specific User

*   **Endpoint**: `GET /admin/users/{userId}/roles`
*   **Description**: Retrieves all roles assigned to a specific user.
*   **Path Parameters**: `userId`.
*   **Success Response (200 OK)**: Array of `RoleDto`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `user:list_roles`).
*   **Conceptual Controller Method (on UserController)**:
    ```typescript
    // In AdminUserController.ts
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('user:list_roles')
    @Get(':userId/roles')
    async getUserRoles(@Param('userId', ParseUUIDPipe) userId: string): Promise<RoleDto[]> {
      return this.roleService.getUserRoles(userId);
    }
    ```

These administrative endpoints provide comprehensive control over role definitions and their assignments to users, forming a key part of the RBAC system.
