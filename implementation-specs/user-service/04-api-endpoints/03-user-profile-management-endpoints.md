# 03 - User Profile Management Endpoints

This document outlines the API endpoints for managing user profiles, including personal details, contact information, preferences, and addresses. Operations are available for authenticated users to manage their own profiles and for administrators to manage any user's profile.

## Current Authenticated User's Profile Operations

Endpoints typically prefixed with `/users/me/profile` or `/profile/me`.

### 1. Retrieve Current Authenticated User's Profile

*   **Endpoint**: `GET /users/me/profile`
*   **Description**: Fetches the profile information for the currently logged-in user, including addresses.
*   **Request Body**: None.
*   **Success Response (200 OK)**:
    ```json
    // Example Response
    {
      "id": "profile-uuid-abc",
      "userId": "user-uuid-123",
      "firstName": "Current", // Potentially from User entity, or duplicated/synced here
      "lastName": "User",    // Potentially from User entity
      "bio": "Loves building amazing things with NestJS!",
      "dateOfBirth": "1990-05-15",
      "phoneNumber": "+15551237890",
      "profilePictureUrl": "https://example.com/path/to/profile.jpg",
      "preferences": {
        "receiveNewsletter": true,
        "theme": "dark"
      },
      "addresses": [
        {
          "id": "address-uuid-001",
          "type": "shipping",
          "streetLine1": "123 Main St",
          "city": "Anytown",
          "postalCode": "12345",
          "country": "US",
          "isDefaultShipping": true,
          "isDefaultBilling": false
        }
      ],
      "defaultShippingAddressId": "address-uuid-001",
      "defaultBillingAddressId": null,
      "createdAt": "2023-10-27T11:00:00Z",
      "updatedAt": "2023-10-28T12:00:00Z"
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized`: User not authenticated.
    *   `404 Not Found`: Profile does not exist for the user (should be rare if created on registration).
*   **Authentication**: Required.
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Get('me/profile')
    async getMyProfile(@Req() request): Promise<UserProfileDetailDto> {
      const profile = await this.userProfileService.getProfileByUserId(request.user.sub);
      if (!profile) throw new NotFoundException('Profile not found.');
      return mapProfileToDetailDto(profile); // Includes addresses
    }
    ```

### 2. Create/Update Current Authenticated User's Profile

*   **Endpoint**: `PUT /users/me/profile` (or `POST` if creation is separate, `PATCH` for partial updates)
*   **Description**: Allows the authenticated user to create or update their profile information.
*   **Request Body**: `UpdateUserProfileDto`
    ```json
    // Example Request
    {
      "firstName": "CurrentUpdated",
      "lastName": "UserChanged",
      "bio": "Updated bio.",
      "dateOfBirth": "1990-05-16",
      "phoneNumber": "+15551237891",
      "profilePictureUrl": "https://example.com/new/profile.jpg",
      "preferences": {
        "receiveNewsletter": false,
        "theme": "light"
      }
    }
    ```
*   **Success Response (200 OK)**: Updated `UserProfileDetailDto`.
*   **Error Responses**:
    *   `400 Bad Request`: Validation errors.
    *   `401 Unauthorized`: User not authenticated.
*   **Authentication**: Required.
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method (PUT for create/replace)**:
    ```typescript
    @UseGuards(AuthGuard)
    @Put('me/profile')
    async upsertMyProfile(
      @Req() request,
      @Body() updateUserProfileDto: UpdateUserProfileDto,
    ): Promise<UserProfileDetailDto> {
      // UserProfileService.createOrUpdateProfile would handle logic
      const profile = await this.userProfileService.upsertProfileForUser(request.user.sub, updateUserProfileDto);
      return mapProfileToDetailDto(profile);
    }
    ```

## Address Management for Current User

Endpoints typically `/users/me/addresses`.

### 3. Add New Address for Current User

*   **Endpoint**: `POST /users/me/addresses`
*   **Description**: Adds a new address (shipping or billing) to the authenticated user's profile.
*   **Request Body**: `CreateAddressDto`
    ```json
    {
      "type": "billing",
      "streetLine1": "456 Business Rd",
      "streetLine2": "Suite 100",
      "city": "Businesstown",
      "state": "CA",
      "postalCode": "90210",
      "country": "US",
      "isDefaultShipping": false,
      "isDefaultBilling": true
    }
    ```
*   **Success Response (201 Created)**: The created `Address` object.
    ```json
    {
      "id": "address-uuid-002",
      "type": "billing",
      // ... other fields ...
      "isDefaultBilling": true
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Validation errors.
    *   `401 Unauthorized`.
*   **Authentication**: Required.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Post('me/addresses')
    @HttpCode(HttpStatus.CREATED)
    async addMyAddress(
      @Req() request,
      @Body() createAddressDto: CreateAddressDto,
    ): Promise<AddressDto> {
      const address = await this.userProfileService.addAddress(request.user.sub, createAddressDto);
      return mapAddressToDto(address);
    }
    ```

### 4. List Addresses for Current User

*   **Endpoint**: `GET /users/me/addresses`
*   **Description**: Retrieves all addresses associated with the authenticated user's profile.
*   **Success Response (200 OK)**: Array of `AddressDto`.
    ```json
    [
      { "id": "address-uuid-001", "type": "shipping", ... },
      { "id": "address-uuid-002", "type": "billing", ... }
    ]
    ```
*   **Authentication**: Required.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Get('me/addresses')
    async getMyAddresses(@Req() request): Promise<AddressDto[]> {
      const addresses = await this.userProfileService.getAddressesByUserId(request.user.sub);
      return addresses.map(mapAddressToDto);
    }
    ```

### 5. Update Address for Current User

*   **Endpoint**: `PUT /users/me/addresses/{addressId}`
*   **Description**: Updates an existing address for the authenticated user.
*   **Path Parameters**: `addressId`.
*   **Request Body**: `UpdateAddressDto`.
*   **Success Response (200 OK)**: Updated `AddressDto`.
*   **Error Responses**:
    *   `400 Bad Request`, `401 Unauthorized`, `404 Not Found` (if address doesn't exist or belong to user).
*   **Authentication**: Required.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Put('me/addresses/:addressId')
    async updateMyAddress(
      @Req() request,
      @Param('addressId', ParseUUIDPipe) addressId: string,
      @Body() updateAddressDto: UpdateAddressDto,
    ): Promise<AddressDto> {
      const address = await this.userProfileService.updateAddress(addressId, request.user.sub, updateAddressDto);
      return mapAddressToDto(address);
    }
    ```

### 6. Delete Address for Current User

*   **Endpoint**: `DELETE /users/me/addresses/{addressId}`
*   **Success Response (204 No Content)**.
*   **Authentication**: Required.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Delete('me/addresses/:addressId')
    @HttpCode(HttpStatus.NO_CONTENT)
    async deleteMyAddress(
      @Req() request,
      @Param('addressId', ParseUUIDPipe) addressId: string,
    ): Promise<void> {
      await this.userProfileService.deleteAddress(addressId, request.user.sub);
    }
    ```

### 7. Set Default Shipping/Billing Address

*   **Endpoint**: `PATCH /users/me/addresses/{addressId}/default`
*   **Description**: Sets a specific address as the default shipping or billing address.
*   **Path Parameters**: `addressId`.
*   **Request Body**:
    ```json
    {
      "type": "shipping" // or "billing"
    }
    ```
*   **Success Response (200 OK)**: Updated `UserProfileDetailDto` (showing new default IDs).
*   **Authentication**: Required.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Patch('me/addresses/:addressId/default')
    async setDefaultAddress(
      @Req() request,
      @Param('addressId', ParseUUIDPipe) addressId: string,
      @Body('type') type: 'shipping' | 'billing',
    ): Promise<UserProfileDetailDto> {
      const profile = await this.userProfileService.setDefaultAddress(request.user.sub, addressId, type);
      return mapProfileToDetailDto(profile);
    }
    ```

## Administrative Profile Operations

Endpoints typically `/admin/users/{userId}/profile`.

### 8. (Admin) Retrieve a Specific User's Profile

*   **Endpoint**: `GET /admin/users/{userId}/profile`
*   **Description**: Fetches the profile for a specific user by their user ID.
*   **Path Parameters**: `userId`.
*   **Success Response (200 OK)**: `UserProfileDetailDto` (same format as `GET /users/me/profile`).
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `user_profile:read_any`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('user_profile:read_any') // Example permission
    @Get(':userId/profile')
    async getUserProfileByAdmin(@Param('userId', ParseUUIDPipe) userId: string): Promise<UserProfileDetailDto> {
      const profile = await this.userProfileService.getProfileByUserId(userId);
      if (!profile) throw new NotFoundException('Profile not found for the specified user.');
      return mapProfileToDetailDto(profile);
    }
    ```

### 9. (Admin) Update a Specific User's Profile

*   **Endpoint**: `PUT /admin/users/{userId}/profile`
*   **Description**: Allows an administrator to update a specific user's profile.
*   **Path Parameters**: `userId`.
*   **Request Body**: `AdminUpdateUserProfileDto` (may have more fields than self-update).
*   **Success Response (200 OK)**: Updated `UserProfileDetailDto`.
*   **Authentication**: Required (Admin).
*   **Permissions**: Required (e.g., `user_profile:update_any`).
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard, PermissionsGuard)
    @RequiredPermissions('user_profile:update_any')
    @Put(':userId/profile')
    async updateUserProfileByAdmin(
      @Param('userId', ParseUUIDPipe) userId: string,
      @Body() adminUpdateProfileDto: AdminUpdateUserProfileDto,
    ): Promise<UserProfileDetailDto> {
      const profile = await this.userProfileService.updateProfileByUserId(userId, adminUpdateProfileDto);
      return mapProfileToDetailDto(profile);
    }
    ```

These endpoints provide full CRUD capabilities for user profiles and their associated addresses, respecting user and administrator roles.
