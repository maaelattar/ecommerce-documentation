# 01 - AuthService

The `AuthService` is a critical component within the User Service, responsible for managing all aspects of user authentication and session management.

## 1. Responsibilities

*   **User Registration**:
    *   Validating registration data (email, password, etc.).
    *   Hashing passwords securely before storage.
    *   Creating new user records.
    *   Potentially initiating an email verification process.
*   **User Login (Authentication)**:
    *   Verifying user credentials (e.g., email/username and password).
    *   Checking account status (e.g., active, suspended, locked).
    *   Generating access tokens (e.g., JWT) and refresh tokens upon successful authentication.
*   **Password Management**:
    *   Securely hashing and storing user passwords (e.g., using bcrypt or Argon2).
    *   Implementing password change functionality (requiring current password).
    *   Implementing password reset functionality (e.g., via email link with a temporary token).
    *   Enforcing password policies (complexity, expiration) via `PasswordPolicyService`.
*   **Token Management**:
    *   Generating JWT access tokens with appropriate claims (user ID, roles, permissions).
    *   Generating secure refresh tokens for obtaining new access tokens.
    *   Managing token expiration and revocation (e.g., via a blacklist or versioning).
    *   Validating incoming tokens.
*   **Multi-Factor Authentication (MFA)**:
    *   Managing MFA setup for users (e.g., TOTP - Time-based One-Time Password).
    *   Verifying MFA codes during login.
    *   Handling MFA recovery options.
*   **Logout**:
    *   Invalidating tokens (if using a server-side mechanism like a blacklist for JWTs or if session-based).
    *   Clearing any relevant session data.

## 2. Key Methods (Conceptual NestJS Example)

```typescript
import { Injectable, UnauthorizedException, BadRequestException } from '@nestjs/common';
import { UserService } from './user.service'; // Assuming a UserService for user data
import { JwtService } from '@nestjs/jwt'; // Standard NestJS JWT module
import { PasswordService } from './password.service'; // For hashing and policy
import { TokenService } from './token.service'; // For detailed token logic
import { User } from '../entities/user.entity'; // User entity
import { CreateUserDto } from '../dto/create-user.dto';
import { LoginDto } from '../dto/login.dto';

@Injectable()
export class AuthService {
  constructor(
    private readonly userService: UserService,
    private readonly jwtService: JwtService,
    private readonly passwordService: PasswordService,
    private readonly tokenService: TokenService,
  ) {}

  async register(createUserDto: CreateUserDto): Promise<User> {
    // 1. Check if user already exists
    const existingUser = await this.userService.findByEmail(createUserDto.email);
    if (existingUser) {
      throw new BadRequestException('Email already in use.');
    }

    // 2. Validate password against policy
    if (!this.passwordService.isPasswordStrong(createUserDto.password)) {
        throw new BadRequestException('Password does not meet policy requirements.');
    }

    // 3. Hash password
    const hashedPassword = await this.passwordService.hashPassword(createUserDto.password);

    // 4. Create user
    const newUser = await this.userService.createUser({
      ...createUserDto,
      password: hashedPassword,
    });

    // 5. Optional: Send verification email (not shown here)

    return newUser; // Or a sanitized user object
  }

  async login(loginDto: LoginDto): Promise<{ accessToken: string; refreshToken: string }> {
    const { email, password } = loginDto;
    const user = await this.userService.findByEmail(email);

    if (!user || !(await this.passwordService.comparePasswords(password, user.password))) {
      throw new UnauthorizedException('Invalid credentials.');
    }

    if (user.status !== 'active') {
      throw new UnauthorizedException('User account is not active.');
    }

    // MFA check would go here if enabled for the user

    const accessToken = await this.tokenService.generateAccessToken(user);
    const refreshToken = await this.tokenService.generateRefreshToken(user);

    // Optional: Store refresh token securely (e.g., in DB associated with user)

    return { accessToken, refreshToken };
  }

  async validateUserById(userId: string): Promise<User | null> {
    return this.userService.findById(userId);
  }

  async refreshToken(oldRefreshToken: string): Promise<{ accessToken: string }> {
    const decodedToken = await this.tokenService.verifyRefreshToken(oldRefreshToken);
    if (!decodedToken || !decodedToken.userId) {
        throw new UnauthorizedException('Invalid refresh token.');
    }
    // Additional checks: e.g., if refresh token is revoked or expired

    const user = await this.userService.findById(decodedToken.userId);
    if (!user) {
        throw new UnauthorizedException('User not found for refresh token.');
    }

    const accessToken = await this.tokenService.generateAccessToken(user);
    return { accessToken };
  }

  async logout(userId: string, token: string): Promise<void> {
    // If using a token blacklist or server-side session management
    await this.tokenService.revokeToken(token); // Conceptual
    // Or simply rely on client-side token deletion for stateless JWTs
    return;
  }

  async requestPasswordReset(email: string): Promise<void> {
    const user = await this.userService.findByEmail(email);
    if (!user) {
      // Still return success to prevent email enumeration
      return;
    }
    const resetToken = await this.tokenService.generatePasswordResetToken(user.id);
    // Send email with resetToken (not shown here)
    // e.g., mailerService.sendPasswordResetEmail(user.email, resetToken);
  }

  async resetPassword(resetToken: string, newPassword: string): Promise<void> {
    const decoded = await this.tokenService.verifyPasswordResetToken(resetToken);
    if (!decoded || !decoded.userId) {
      throw new BadRequestException('Invalid or expired password reset token.');
    }

    if (!this.passwordService.isPasswordStrong(newPassword)) {
        throw new BadRequestException('New password does not meet policy requirements.');
    }

    const hashedPassword = await this.passwordService.hashPassword(newPassword);
    await this.userService.updatePassword(decoded.userId, hashedPassword);
    await this.tokenService.revokePasswordResetToken(resetToken); // Ensure single use
  }

  // ... other methods like changePassword, setupMfa, verifyMfaCode
}
```

## 3. Interactions

*   **`UserService`**: To fetch user details, create new users, and update user records (e.g., password, status).
*   **`PasswordService` / `PasswordPolicyService`**: For hashing passwords, comparing them, and enforcing password policies.
*   **`TokenService`**: For generating, validating, and managing the lifecycle of JWTs, refresh tokens, and other specific-purpose tokens (password reset, email verification).
*   **`UserEventPublisher`**: To publish events like `UserRegistered`, `UserLoggedIn`, `PasswordChanged`, `PasswordResetRequested`.
*   **Database**: Indirectly via `UserService` and potentially `TokenService` (if refresh tokens or token blacklists are stored).
*   **Notification Service (External)**: To send emails for verification, password resets, etc.

## 4. Security Considerations

*   **Password Hashing**: Use strong, adaptive hashing algorithms (e.g., Argon2id, scrypt, bcrypt) with appropriate work factors (salt rounds). Never store passwords in plain text or using reversible encryption.
*   **Token Security**:
    *   Use HTTPS for all communication.
    *   JWTs should be signed with strong secrets (e.g., RS256 or ES256 using asymmetric keys).
    *   Keep token payloads minimal.
    *   Set short expiry times for access tokens (e.g., 5-15 minutes).
    *   Implement secure refresh token rotation and storage (e.g., HttpOnly, Secure cookies for web clients; secure storage for mobile).
    *   Consider token revocation mechanisms (e.g., blacklist, versioning) for sensitive operations like password changes or logout.
*   **Input Validation**: Rigorously validate all inputs (email formats, password length/complexity before hitting policy service) to prevent injection attacks and malformed data.
*   **Rate Limiting**: Apply rate limiting to login, registration, and password reset endpoints to protect against brute-force and denial-of-service attacks.
*   **MFA**: Encourage or enforce MFA for enhanced security.
*   **Protection against Credential Stuffing**: Use techniques like breached password detection (e.g., Have I Been Pwned API).
*   **Secure Password Reset**: Ensure password reset tokens are short-lived, single-use, and sent securely. Do not leak information about whether an email exists in the system during this process.
*   **Logging**: Log security-relevant events (logins, failed logins, password changes/resets, MFA attempts) for auditing and threat detection, but avoid logging sensitive data like passwords or tokens.

## 5. Future Enhancements

*   **Social Logins (OAuth/OpenID Connect)**: Integration with third-party identity providers (Google, Facebook, etc.).
*   **Single Sign-On (SSO)**: Integration with SAML or other SSO protocols.
*   **Magic Links**: Passwordless login using time-sensitive, single-use links sent via email.
*   **Device Fingerprinting/Biometrics**: For advanced authentication and fraud detection.
*   **CAPCHA Integration**: To protect against bot-driven attacks on registration and login.

This `AuthService` forms the first line of defense and user interaction management, making its correct and secure implementation paramount for the User Service.
