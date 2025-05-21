# 05 - Permission Management Endpoints (Admin)

This document specifies the API endpoints for managing granular permissions within the system. These operations are typically restricted to administrators with appropriate privileges and are fundamental for the RBAC (Role-Based Access Control) mechanism.

Endpoints are usually prefixed like `/admin/permissions`.

## 1. Create a New Permission

*   **Endpoint**: `POST /admin/permissions`
*   **Description**: Creates a new permission in the system.
*   **Request Body**: `CreatePermissionDto`
    ```json
    // Example Request
    {
      "name": "product:create", // Often a combination of action:resource or verb:subject
      "action": "create",
      "subject": "product", // Or "resource": "ProductCatalog"
      "description": "Allows creating new products.",
      "conditions": { "isOwner": false } // Optional: For ABAC-like conditions
    }
    ```
*   **Success Response (201 Created)**: The created `Permission` object.
    ```json
    // Example Response
    {
      "id": "permission-uuid-123",
      "name": "product:create",
      "action": "create",
      "subject": "product",
      "description": "Allows creating new products.",
      "conditions": null,
      "createdAt": "2023-10-28T11:00:00Z",
      "updatedAt": "2023-10-28T11:00:00Z"
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Validation errors (e.g., name conflict, invalid action/subject).
    *   `401 Unauthorized` / `403 Forbidden`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `permission:create`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('permission:create')
    @Post()
    @HttpCode(HttpStatus.CREATED)
    async createPermission(@Body() createPermissionDto: CreatePermissionDto): Promise<PermissionDto> {
      const permission = await this.permissionService.createPermission(createPermissionDto);
      return mapPermissionToDto(permission);
    }
    ```

## 2. List All Permissions

*   **Endpoint**: `GET /admin/permissions`
*   **Description**: Retrieves a list of all permissions. May support pagination and filtering by subject/action.
*   **Query Parameters**: `page`, `limit`, `sortBy`, `sortOrder`, `subject`, `action` (optional).
*   **Success Response (200 OK)**: Array of `PermissionDto` or a paginated response.
    ```json
    // Example (Non-paginated)
    [
      { "id": "permission-uuid-123", "name": "product:create", ... },
      { "id": "permission-uuid-456", "name": "order:view_all", ... }
    ]
    ```
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `permission:list`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('permission:list')
    @Get()
    async findAllPermissions(@Query() queryParams: ListPermissionsQueryDto): Promise<PaginatedResponseDto<PermissionDto>> {
      return this.permissionService.findAllPermissionsPaginated(queryParams);
    }
    ```

## 3. Retrieve a Specific Permission's Details

*   **Endpoint**: `GET /admin/permissions/{permissionId}`
*   **Description**: Fetches detailed information about a specific permission.
*   **Path Parameters**: `permissionId`.
*   **Success Response (200 OK)**: `PermissionDto`.
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `permission:read_one`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('permission:read_one')
    @Get(':permissionId')
    async findPermissionById(@Param('permissionId', ParseUUIDPipe) permissionId: string): Promise<PermissionDto> {
      const permission = await this.permissionService.findPermissionById(permissionId);
      if (!permission) throw new NotFoundException('Permission not found.');
      return mapPermissionToDto(permission);
    }
    ```

## 4. Update a Permission

*   **Endpoint**: `PUT /admin/permissions/{permissionId}` or `PATCH`
*   **Description**: Updates an existing permission's properties.
*   **Path Parameters**: `permissionId`.
*   **Request Body**: `UpdatePermissionDto`.
    ```json
    {
      "description": "Allows creating new products in any category.",
      "conditions": null
    }
    ```
*   **Success Response (200 OK)**: Updated `PermissionDto`.
*   **Error Responses**: `400 Bad Request`, `401/403`, `404 Not Found`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `permission:update`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('permission:update')
    @Put(':permissionId')
    async updatePermission(
      @Param('permissionId', ParseUUIDPipe) permissionId: string,
      @Body() updatePermissionDto: UpdatePermissionDto,
    ): Promise<PermissionDto> {
      const permission = await this.permissionService.updatePermission(permissionId, updatePermissionDto);
      return mapPermissionToDto(permission);
    }
    ```

## 5. Delete a Permission

*   **Endpoint**: `DELETE /admin/permissions/{permissionId}`
*   **Description**: Deletes a permission. Caution: should check if permission is currently assigned to any roles.
*   **Path Parameters**: `permissionId`.
*   **Success Response (204 No Content)**.
*   **Error Responses**: `400 Bad Request` (e.g., permission in use), `401/403`, `404 Not Found`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `permission:delete`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('permission:delete')
    @Delete(':permissionId')
    @HttpCode(HttpStatus.NO_CONTENT)
    async deletePermission(@Param('permissionId', ParseUUIDPipe) permissionId: string): Promise<void> {
      await this.permissionService.deletePermission(permissionId);
    }
    ```

## Role-Permission Assignments (Often part of Role Management or Permission Management by Admin)

### 6. Assign Permissions to a Role

*   **Endpoint**: `POST /admin/roles/{roleId}/permissions`
*   **Description**: Assigns one or more existing permissions to a specific role.
*   **Path Parameters**: `roleId`.
*   **Request Body**:
    ```json
    {
      "permissionIds": ["permission-uuid-123", "permission-uuid-789"]
    }
    ```
*   **Success Response (200 OK)**: The updated `RoleDetailDto` with its new list of permissions.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:assign_permissions`).
*   **Conceptual Controller Method (on RoleController)**:
    ```typescript
    // In AdminRoleController.ts
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:assign_permissions')
    @Post(':roleId/permissions')
    async assignPermissionsToRole(
      @Param('roleId', ParseUUIDPipe) roleId: string,
      @Body() assignPermissionsDto: AssignPermissionsToRoleDto, // { permissionIds: string[] }
    ): Promise<RoleDetailDto> {
      return this.permissionService.assignPermissionsToRole(roleId, assignPermissionsDto.permissionIds);
    }
    ```

### 7. Remove Permissions from a Role

*   **Endpoint**: `DELETE /admin/roles/{roleId}/permissions`
*   **Description**: Removes one or more permissions from a specific role.
*   **Path Parameters**: `roleId`.
*   **Request Body**:
    ```json
    {
      "permissionIds": ["permission-uuid-123"]
    }
    ```
*   **Success Response (200 OK)**: Updated `RoleDetailDto` or simply a success message.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:remove_permissions`).
*   **Conceptual Controller Method (on RoleController)**:
    ```typescript
    // In AdminRoleController.ts
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:remove_permissions')
    @Delete(':roleId/permissions') // Using DELETE for removal
    async removePermissionsFromRole(
      @Param('roleId', ParseUUIDPipe) roleId: string,
      @Body() removePermissionsDto: RemovePermissionsFromRoleDto, // { permissionIds: string[] }
    ): Promise<RoleDetailDto> {
      return this.permissionService.removePermissionsFromRole(roleId, removePermissionsDto.permissionIds);
    }
    ```

### 8. List Permissions for a Specific Role

*   **Endpoint**: `GET /admin/roles/{roleId}/permissions`
*   **Description**: Retrieves all permissions currently assigned to a specific role.
*   **Path Parameters**: `roleId`.
*   **Success Response (200 OK)**: Array of `PermissionDto`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `role:list_permissions`).
*   **Conceptual Controller Method (on RoleController)**:
    ```typescript
    // In AdminRoleController.ts
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('role:list_permissions')
    @Get(':roleId/permissions')
    async getPermissionsForRole(@Param('roleId', ParseUUIDPipe) roleId: string): Promise<PermissionDto[]> {
      return this.permissionService.getPermissionsForRole(roleId);
    }
    ```

### 9. List Roles that have a Specific Permission

*   **Endpoint**: `GET /admin/permissions/{permissionId}/roles`
*   **Description**: Retrieves all roles that have a specific permission assigned to them.
*   **Path Parameters**: `permissionId`.
*   **Success Response (200 OK)**: Array of `RoleDto`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `permission:list_roles`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('permission:list_roles')
    @Get(':permissionId/roles')
    async getRolesForPermission(@Param('permissionId', ParseUUIDPipe) permissionId: string): Promise<RoleDto[]> {
      return this.permissionService.getRolesForPermission(permissionId);
    }
    ```

These administrative endpoints enable fine-grained control over the permissions system, which is crucial for securing application resources and actions.
