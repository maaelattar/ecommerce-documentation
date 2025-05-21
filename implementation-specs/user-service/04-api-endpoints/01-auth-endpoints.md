# 01 - Authentication Endpoints

This document details the API endpoints related to user authentication, registration, session management, and credential recovery.

## 1. User Registration

*   **Endpoint**: `POST /auth/register`
*   **Description**: Allows a new user to create an account.
*   **Request Body**: `CreateUserDto` (defined in User Service DTOs)
    ```json
    // Example Request
    {
      "email": "newuser@example.com",
      "password": "Password123!",
      "firstName": "John",
      "lastName": "Doe"
    }
    ```
*   **Success Response (201 Created)**:
    *   Body: Sanitized `User` object (excluding password).
    ```json
    // Example Response
    {
      "id": "user-uuid-123",
      "email": "newuser@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "status": "pending_verification", // Or 'active' if no verification step
      "createdAt": "2023-10-27T10:00:00Z",
      "updatedAt": "2023-10-27T10:00:00Z"
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Validation errors (e.g., invalid email, weak password, missing fields). Body contains detailed error messages.
    *   `409 Conflict`: Email already exists.
*   **Authentication**: None required.
*   **Permissions**: None required.
*   **Conceptual Controller Method**:
    ```typescript
    @Post('register')
    @HttpCode(HttpStatus.CREATED)
    async register(@Body() createUserDto: CreateUserDto): Promise<UserResponseDto> {
      const user = await this.authService.register(createUserDto);
      return mapUserToResponseDto(user); // Utility to sanitize user data
    }
    ```

## 2. User Login

*   **Endpoint**: `POST /auth/login`
*   **Description**: Authenticates a user and returns access and refresh tokens.
*   **Request Body**: `LoginDto`
    ```json
    // Example Request
    {
      "email": "user@example.com",
      "password": "Password123!"
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    // Example Response
    {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "anotherLongOpaqueToken...",
      "user": {
          "id": "user-uuid-456",
          "email": "user@example.com",
          "firstName": "Jane",
          "roles": ["customer"]
      }
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Validation errors (missing fields).
    *   `401 Unauthorized`: Invalid credentials, inactive account, MFA required but not provided.
*   **Authentication**: None required.
*   **Permissions**: None required.
*   **Conceptual Controller Method**:
    ```typescript
    @Post('login')
    async login(@Body() loginDto: LoginDto): Promise<LoginResponseDto> {
      return this.authService.login(loginDto);
    }
    ```

## 3. User Logout

*   **Endpoint**: `POST /auth/logout`
*   **Description**: Invalidates the user's current session/tokens.
*   **Request Body**: (Optional, might include refresh token if needed for server-side invalidation).
    ```json
    // Example Request (if refresh token is sent in body)
    {
      "refreshToken": "userRefreshTokenHere"
    }
    ```
*   **Success Response (200 OK or 204 No Content)**:
    ```json
    // Example Response (200 OK)
    {
      "message": "Logout successful"
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized`: If no valid session/token was found to log out.
*   **Authentication**: Required (valid access token in Authorization header).
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard) // Or your specific JWT guard
    @Post('logout')
    async logout(@Req() request): Promise<{ message: string }> {
      const accessTokenJti = request.user.jti; // Assuming JTI is in payload
      const refreshToken = request.body.refreshToken; // If applicable
      await this.authService.logout(request.user.sub, accessTokenJti, refreshToken);
      return { message: 'Logout successful' };
    }
    ```

## 4. Token Refresh

*   **Endpoint**: `POST /auth/refresh-token`
*   **Description**: Obtains a new access token using a valid refresh token.
*   **Request Body**:
    ```json
    // Example Request
    {
      "refreshToken": "userValidRefreshTokenHere"
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    // Example Response
    {
      "accessToken": "newGeneratedAccessToken...",
      "refreshToken": "potentiallyNewRefreshTokenIfRotated..." // Optional: if refresh token rotation is used
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized`: Invalid or expired refresh token.
*   **Authentication**: None required (refresh token itself is the authentication).
*   **Permissions**: None required.
*   **Conceptual Controller Method**:
    ```typescript
    @Post('refresh-token')
    async refreshToken(@Body('refreshToken') refreshToken: string): Promise<RefreshTokenResponseDto> {
      return this.authService.refreshToken(refreshToken);
    }
    ```

## 5. Request Password Reset

*   **Endpoint**: `POST /auth/request-password-reset`
*   **Description**: Initiates the password reset process for a user (e.g., sends an email with a reset link/token).
*   **Request Body**:
    ```json
    // Example Request
    {
      "email": "user@example.com"
    }
    ```
*   **Success Response (200 OK or 202 Accepted)**:
    *   Response is generic to prevent email enumeration.
    ```json
    // Example Response
    {
      "message": "If an account with that email exists, a password reset link has been sent."
    }
    ```
*   **Error Responses**: (Usually, no specific errors are returned to prevent enumeration, but validation errors on email format might occur).
    *   `400 Bad Request`: Invalid email format.
*   **Authentication**: None required.
*   **Permissions**: None required.
*   **Conceptual Controller Method**:
    ```typescript
    @Post('request-password-reset')
    async requestPasswordReset(@Body('email') email: string): Promise<{ message: string }> {
      await this.authService.requestPasswordReset(email);
      return { message: "If an account with that email exists, a password reset link has been sent." };
    }
    ```

## 6. Reset Password

*   **Endpoint**: `POST /auth/reset-password`
*   **Description**: Allows a user to set a new password using a valid password reset token.
*   **Request Body**: `ResetPasswordDto`
    ```json
    // Example Request
    {
      "resetToken": "validPasswordResetTokenFromEmail",
      "newPassword": "NewStrongPassword123!"
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    // Example Response
    {
      "message": "Password has been reset successfully."
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Invalid or expired token, new password does not meet policy.
*   **Authentication**: None required (reset token is the authentication).
*   **Permissions**: None required.
*   **Conceptual Controller Method**:
    ```typescript
    @Post('reset-password')
    async resetPassword(@Body() resetPasswordDto: ResetPasswordDto): Promise<{ message: string }> {
      await this.authService.resetPassword(resetPasswordDto.resetToken, resetPasswordDto.newPassword);
      return { message: "Password has been reset successfully." };
    }
    ```

## 7. Change Password (Authenticated User)

*   **Endpoint**: `POST /auth/change-password`
*   **Description**: Allows an authenticated user to change their current password.
*   **Request Body**: `ChangePasswordDto`
    ```json
    // Example Request
    {
      "currentPassword": "OldPassword123!",
      "newPassword": "NewStrongerPassword456!"
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    // Example Response
    {
      "message": "Password changed successfully."
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: New password does not meet policy.
    *   `401 Unauthorized`: Current password incorrect.
*   **Authentication**: Required.
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Post('change-password')
    async changePassword(@Req() request, @Body() changePasswordDto: ChangePasswordDto): Promise<{ message: string }> {
      await this.authService.changePassword(request.user.sub, changePasswordDto.currentPassword, changePasswordDto.newPassword);
      return { message: "Password changed successfully." };
    }
    ```

## 8. Request Email Verification

*   **Endpoint**: `POST /auth/request-email-verification`
*   **Description**: Sends (or re-sends) an email verification link to the authenticated user's email address.
*   **Request Body**: None.
*   **Success Response (200 OK or 202 Accepted)**:
    ```json
    {
      "message": "Verification email sent. Please check your inbox."
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized`: User not authenticated.
    *   `409 Conflict`: Email already verified or recent request already sent.
*   **Authentication**: Required.
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Post('request-email-verification')
    async requestEmailVerification(@Req() request): Promise<{ message: string }> {
      await this.authService.requestEmailVerification(request.user.sub);
      return { message: "Verification email sent. Please check your inbox." };
    }
    ```

## 9. Verify Email

*   **Endpoint**: `GET /auth/verify-email?token={verificationToken}` or `POST /auth/verify-email`
*   **Description**: Verifies a user's email address using a token sent to them.
*   **Request Parameter (GET)** or **Request Body (POST)**:
    ```json
    // Example Request (POST body)
    {
      "verificationToken": "userEmailVerificationToken"
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    {
      "message": "Email verified successfully."
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Invalid or expired token.
*   **Authentication**: Usually none (token is the auth). Sometimes done by authenticated user if token is short-lived and link clicked in same session.
*   **Permissions**: None required.
*   **Conceptual Controller Method (POST example)**:
    ```typescript
    @Post('verify-email')
    async verifyEmail(@Body('verificationToken') token: string): Promise<{ message: string }> {
      await this.authService.verifyEmail(token);
      return { message: "Email verified successfully." };
    }
    ```

## 10. MFA Setup (Initiate)

*   **Endpoint**: `POST /auth/mfa/setup`
*   **Description**: Initiates the setup process for an MFA method (e.g., TOTP). Returns data needed for the user to configure their authenticator app (like a QR code URI).
*   **Request Body**: (May specify MFA type if multiple are supported)
*   **Success Response (200 OK)**:
    ```json
    // Example for TOTP
    {
      "otpAuthUrl": "otpauth://totp/MyApp:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MyApp",
      "secret": "JBSWY3DPEHPK3PXP" // Base32 encoded secret for manual entry
    }
    ```
*   **Error Responses**:
    *   `401 Unauthorized`: User not authenticated.
    *   `409 Conflict`: MFA already enabled or setup in progress.
*   **Authentication**: Required.
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Post('mfa/setup')
    async setupMfa(@Req() request): Promise<MfaSetupResponseDto> {
      return this.authService.setupMfa(request.user.sub);
    }
    ```

## 11. MFA Verification (Enable)

*   **Endpoint**: `POST /auth/mfa/verify`
*   **Description**: Verifies an MFA code provided by the user during setup and enables MFA for their account.
*   **Request Body**:
    ```json
    {
      "mfaToken": "123456" // Code from authenticator app
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    {
      "message": "MFA enabled successfully.",
      "recoveryCodes": ["code1", "code2", ...] // Optional: one-time recovery codes
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Invalid MFA token.
    *   `401 Unauthorized`: User not authenticated or MFA setup not initiated.
*   **Authentication**: Required.
*   **Permissions**: None required beyond being authenticated.
*   **Conceptual Controller Method**:
    ```typescript
    @UseGuards(AuthGuard)
    @Post('mfa/verify')
    async verifyMfa(@Req() request, @Body('mfaToken') mfaToken: string): Promise<MfaVerifyResponseDto> {
      return this.authService.verifyAndEnableMfa(request.user.sub, mfaToken);
    }
    ```

## 12. MFA Challenge (During Login)

*   This is not a direct endpoint but a step in the login flow if MFA is enabled.
*   After primary credential validation, if MFA is required, the `/auth/login` endpoint might return a specific response indicating MFA is needed (e.g., a `202 Accepted` with a `mfaRequired: true` field and a temporary MFA session token).
*   A subsequent call would then be made to a dedicated MFA challenge verification endpoint.
*   **Endpoint**: `POST /auth/mfa/challenge`
*   **Request Body**:
    ```json
    {
      "mfaSessionToken": "temporaryTokenFromLoginStep", // Or use userId from primary auth context
      "mfaToken": "123456"
    }
    ```
*   **Success Response (200 OK)**: Returns standard login success response with access/refresh tokens.
*   **Error Responses**:
    *   `400 Bad Request`: Invalid MFA token or session token.
*   **Conceptual Controller Method**:
    ```typescript
    @Post('mfa/challenge')
    async mfaChallenge(@Body() mfaChallengeDto: MfaChallengeDto): Promise<LoginResponseDto> {
      return this.authService.verifyMfaChallenge(mfaChallengeDto);
    }
    ```

These endpoints form the core of the User Service's authentication capabilities.
