# 02 - User Account Management Endpoints

This document details API endpoints for managing user account information, both for the authenticated user themselves and for administrative purposes.

## Current Authenticated User Operations

These endpoints are typically prefixed with something like `/users/me` or operate based on the authenticated user's context from the JWT.

### 1. Retrieve Current Authenticated User's Details

*   **Endpoint**: `GET /users/me`
*   **Description**: Fetches the complete account details for the currently logged-in user.
*   **Request Body**: None.
*   **Success Response (200 OK)**:
    *   Body: Sanitized `User` object and potentially `UserProfile` details (excluding sensitive data like password hash).
    ```json
    // Example Response
    {
      "id": "user-uuid-123",
      "email": "currentuser@example.com",
      "firstName": "Current",
      "lastName": "User",
      "status": "active",
      "roles": ["customer", "beta-tester"],
      "createdAt": "2023-10-27T10:00:00Z",
      "updatedAt": "2023-10-27T10:01:00Z",
      "lastLoginAt": "2023-10-28T09:00:00Z",
      "profile": {
        "id": "profile-uuid-abc",
        "bio": "Loves coding!",
        "dateOfBirth": "1990-01-01",
        "phoneNumber": "+15551234567"
      }
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized`: User not authenticated.
*   **Authentication**: Required (valid access token).
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Get('me')
    async getMyAccountDetails(@Req() request): Promise<UserDetailResponseDto> {
      // request.user.sub contains the userId from the JWT
      const user = await this.userService.findUserDetailsById(request.user.sub);
      if (!user) throw new NotFoundException('User details not found.');
      return mapUserToDetailResponseDto(user);
    }
    ```

### 2. Update Current Authenticated User's Core Account Details

*   **Endpoint**: `PATCH /users/me`
*   **Description**: Allows the authenticated user to update their core account information (e.g., email, non-profile personal details if stored on User entity). Email changes typically trigger a re-verification process.
*   **Request Body**: `UpdateUserDto` (subset of fields allowed for self-update)
    ```json
    // Example Request (changing email)
    {
      "email": "new.email@example.com",
      "username": "newUsername"
    }
    ```
*   **Success Response (200 OK)**:
    *   Body: Updated and sanitized `User` object.
    ```json
    // Example Response
    {
      "id": "user-uuid-123",
      "email": "new.email@example.com", // May still be old email if verification is pending
      "username": "newUsername",
      "status": "pending_email_verification", // If email changed and verification needed
      // ... other fields
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Validation errors.
    *   `401 Unauthorized`: User not authenticated.
    *   `409 Conflict`: New email or username already in use.
*   **Authentication**: Required.
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Patch('me')
    async updateMyAccount(
      @Req() request,
      @Body() updateUserDto: UpdateSelfUserDto, // A specific DTO for self-update
    ): Promise<UserResponseDto> {
      const updatedUser = await this.userService.updateUser(request.user.sub, updateUserDto);
      return mapUserToResponseDto(updatedUser);
    }
    ```

### 3. Close/Delete Current Authenticated User's Account

*   **Endpoint**: `DELETE /users/me`
*   **Description**: Allows the authenticated user to initiate the deletion of their own account. This might be a soft delete or start an anonymization process.
*   **Request Body**: (Optional, may require password confirmation).
    ```json
    // Example Request (if password confirmation is required)
    {
      "password": "CurrentUserPassword123!"
    }
    ```
*   **Success Response (200 OK or 204 No Content)**:
    ```json
    // Example (200 OK)
    {
      "message": "Account deletion process initiated."
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized`: User not authenticated or password confirmation failed.
    *   `400 Bad Request`: If other conditions prevent deletion.
*   **Authentication**: Required.
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Delete('me')
    async deleteMyAccount(
      @Req() request,
      @Body() deleteAccountDto?: DeleteAccountDto, // Optional DTO for password confirmation
    ): Promise<{ message: string }> {
      // Add password verification logic if deleteAccountDto.password is present
      await this.userService.deleteUser(request.user.sub); // Soft delete by default
      // Logout user immediately by revoking tokens
      await this.authService.logout(request.user.sub, request.user.jti, /* refreshToken if available */);
      return { message: "Account deletion process initiated and you have been logged out." };
    }
    ```

## Administrative User Operations

These endpoints are intended for users with administrative privileges and are typically prefixed with `/admin/users` or similar, protected by role/permission-based guards.

### 4. (Admin) List All Users

*   **Endpoint**: `GET /admin/users`
*   **Description**: Retrieves a paginated list of all users in the system. Supports filtering and sorting.
*   **Query Parameters**:
    *   `page` (number, optional, default: 1)
    *   `limit` (number, optional, default: 10)
    *   `sortBy` (string, optional, e.g., `createdAt`)
    *   `sortOrder` (`asc` | `desc`, optional, default: `desc`)
    *   `email` (string, optional, filter by email contains)
    *   `status` (string, optional, filter by `UserStatus`)
    *   `role` (string, optional, filter by role name or ID)
*   **Success Response (200 OK)**:
    ```json
    {
      "data": [
        { "id": "user-uuid-001", "email": "admin@example.com", "status": "active", ... },
        { "id": "user-uuid-002", "email": "user1@example.com", "status": "suspended", ... }
      ],
      "meta": {
        "totalItems": 150,
        "itemCount": 10,
        "itemsPerPage": 10,
        "totalPages": 15,
        "currentPage": 1
      }
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized`: Admin not authenticated.
    *   `403 Forbidden`: Admin does not have required permissions (e.g., `user:read_all`).
*   **Authentication**: Required.
*   **Permissions**: Required (e.g., `users:list`, `user:read_all`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('users:list')
    @Get()
    async listUsers(@Query() queryParams: UserListQueryDto): Promise<PaginatedUserResponseDto> {
      return this.userService.findAllUsers(queryParams);
    }
    ```

### 5. (Admin) Retrieve a Specific User's Details by ID

*   **Endpoint**: `GET /admin/users/{userId}`
*   **Description**: Fetches complete details for a specific user by their ID.
*   **Path Parameters**: `userId` (string, typically UUID).
*   **Success Response (200 OK)**: Same format as `GET /users/me`.
*   **Error Responses**:
    *   `401 Unauthorized` / `403 Forbidden`.
    *   `404 Not Found`: User with the given ID does not exist.
*   **Authentication**: Required.
*   **Permissions**: Required (e.g., `user:read_one`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('user:read_one')
    @Get(':userId')
    async getUserById(@Param('userId', ParseUUIDPipe) userId: string): Promise<UserDetailResponseDto> {
      const user = await this.userService.findUserDetailsById(userId);
      if (!user) throw new NotFoundException('User not found.');
      return mapUserToDetailResponseDto(user);
    }
    ```

### 6. (Admin) Update a Specific User's Account

*   **Endpoint**: `PATCH /admin/users/{userId}`
*   **Description**: Allows an administrator to update a specific user's account details (e.g., status, email, assign roles - though role assignment might be a separate endpoint).
*   **Path Parameters**: `userId`.
*   **Request Body**: `AdminUpdateUserDto` (more fields than self-update, e.g., `status`, `roles`).
    ```json
    // Example Request
    {
      "email": "updated.byadmin@example.com",
      "status": "active",
      "roleIds": ["role-uuid-customer", "role-uuid-vip"]
    }
    ```
*   **Success Response (200 OK)**: Updated `User` object.
*   **Error Responses**:
    *   `400 Bad Request`: Validation errors.
    *   `401 Unauthorized` / `403 Forbidden`.
    *   `404 Not Found`: User not found.
    *   `409 Conflict`: Email conflict if changed.
*   **Authentication**: Required.
*   **Permissions**: Required (e.g., `user:update`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('user:update')
    @Patch(':userId')
    async updateUserByAdmin(
      @Param('userId', ParseUUIDPipe) userId: string,
      @Body() adminUpdateUserDto: AdminUpdateUserDto,
    ): Promise<UserResponseDto> {
      const updatedUser = await this.userService.adminUpdateUser(userId, adminUpdateUserDto);
      return mapUserToResponseDto(updatedUser);
    }
    ```

### 7. (Admin) Delete a Specific User's Account

*   **Endpoint**: `DELETE /admin/users/{userId}`
*   **Description**: Allows an administrator to delete a user's account (soft or hard delete based on policy).
*   **Path Parameters**: `userId`.
*   **Query Parameters**: `hardDelete` (boolean, optional, default: false).
*   **Success Response (200 OK or 204 No Content)**:
    ```json
    {
      "message": "User account deleted successfully."
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized` / `403 Forbidden`.
    *   `404 Not Found`: User not found.
*   **Authentication**: Required.
*   **Permissions**: Required (e.g., `user:delete`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('user:delete')
    @Delete(':userId')
    async deleteUserByAdmin(
        @Param('userId', ParseUUIDPipe) userId: string,
        @Query('hardDelete') hardDelete?: boolean
    ): Promise<{ message: string }> {
      await this.userService.deleteUser(userId, hardDelete);
      return { message: "User account deleted successfully." };
    }
    ```

These endpoints provide comprehensive management capabilities for user accounts, catering to both individual users and administrators.
