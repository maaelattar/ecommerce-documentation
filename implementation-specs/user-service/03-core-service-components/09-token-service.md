# 09 - TokenService

The `TokenService` is a specialized component responsible for the generation, validation, and management of various types of tokens used within the User Service and potentially by other services that rely on its authentication. This typically includes JWT access tokens, refresh tokens, password reset tokens, email verification tokens, etc.

While `@nestjs/jwt` (`JwtService`) provides core JWT functionalities, `TokenService` encapsulates higher-level logic, specific configurations, and management of different token types and their lifecycles.

## 1. Responsibilities

*   **Access Token Generation**: Creating JWT access tokens with appropriate claims (e.g., `userId`, `username`, `roles`, `permissions`, `sessionId`) and expiration.
*   **Refresh Token Generation & Management**:
    *   Creating secure, opaque refresh tokens.
    *   Storing refresh tokens securely (e.g., in a database, potentially hashed, linked to a user and/or device).
    *   Validating refresh tokens.
    *   Implementing refresh token rotation (issuing a new refresh token when an old one is used).
    *   Handling refresh token revocation.
*   **Specific-Purpose Token Generation & Management**:
    *   Creating tokens for password resets, email verifications, MFA setup, etc.
    *   Ensuring these tokens are short-lived and single-use.
    *   Storing and validating these tokens, often with an associated user ID and expiration.
*   **Token Validation**: Verifying the signature, expiration, and claims of incoming tokens (primarily access tokens, but also other types).
*   **Token Revocation (Blacklisting/Blocklisting)**:
    *   Implementing mechanisms to invalidate tokens before their natural expiry (e.g., upon logout, password change, or detected security incident).
    *   This might involve a blacklist (e.g., in Redis or a database) storing JTI (JWT ID) or user/session identifiers of revoked tokens.
*   **Configuration Management**: Centralizing token-related configurations like secret keys, algorithms, issuers, audiences, and default expiry times for different token types.

## 2. Key Methods (Conceptual NestJS Example)

```typescript
import { Injectable, UnauthorizedException, BadRequestException, InternalServerErrorException } from '@nestjs/common';
import { JwtService, JwtSignOptions, JwtVerifyOptions } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config'; // For accessing configuration
import { User } from '../entities/user.entity';
import * as crypto from 'crypto';
// Assume a RefreshToken entity/store and a RevokedToken entity/store
// For example, using TypeORM or a Redis client

export interface AccessTokenPayload {
  sub: string; // Subject (user ID)
  username?: string;
  roles?: string[];
  jti?: string; // JWT ID, useful for revocation
  // ... other claims
}

export interface RefreshTokenPayload {
  sub: string; // User ID
  jti: string; // Unique ID for the refresh token itself
  // Potentially device ID or session ID
}

export interface SpecificPurposeTokenPayload {
  sub: string; // User ID
  type: 'password_reset' | 'email_verification' | 'mfa_setup';
  exp?: number; // Expiration timestamp
  nonce?: string; // For single use guarantee
}

@Injectable()
export class TokenService {
  constructor(
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
    // @InjectRepository(RefreshTokenEntity) // Example for DB-backed refresh tokens
    // private refreshTokenRepository: Repository<RefreshTokenEntity>,
    // @Inject('REDIS_CLIENT') private redisClient: Redis, // Example for blacklist
  ) {}

  // --- Access Tokens ---
  async generateAccessToken(user: User): Promise<string> {
    const payload: AccessTokenPayload = {
      sub: user.id,
      username: user.username, // If applicable
      roles: user.roles?.map(role => role.name), // Assuming roles are populated
      jti: crypto.randomBytes(16).toString('hex'), // Unique JWT ID
    };
    const secret = this.configService.get<string>('JWT_ACCESS_SECRET');
    const expiresIn = this.configService.get<string>('JWT_ACCESS_EXPIRATION');

    if (!secret || !expiresIn) {
        throw new InternalServerErrorException('JWT Access configuration missing.');
    }
    return this.jwtService.sign(payload, { secret, expiresIn });
  }

  async verifyAccessToken(token: string): Promise<AccessTokenPayload> {
    const secret = this.configService.get<string>('JWT_ACCESS_SECRET');
    try {
      const payload = this.jwtService.verify<AccessTokenPayload>(token, { secret });
      // Check if token is revoked (if blacklist is implemented)
      // if (await this.isTokenRevoked(payload.jti)) {
      //   throw new UnauthorizedException('Token has been revoked.');
      // }
      return payload;
    } catch (error) {
      throw new UnauthorizedException(`Invalid access token: ${error.message}`);
    }
  }

  // --- Refresh Tokens ---
  async generateRefreshToken(user: User, oldRefreshTokenId?: string): Promise<string> {
    const tokenId = crypto.randomBytes(32).toString('hex');
    const payload: RefreshTokenPayload = { sub: user.id, jti: tokenId };
    const secret = this.configService.get<string>('JWT_REFRESH_SECRET');
    const expiresIn = this.configService.get<string>('JWT_REFRESH_EXPIRATION');

    if (!secret || !expiresIn) {
        throw new InternalServerErrorException('JWT Refresh configuration missing.');
    }

    const token = this.jwtService.sign(payload, { secret, expiresIn });

    // Store the new refresh token (e.g., hashed, linked to user, expiry)
    // await this.storeRefreshToken(user.id, tokenId, expiresIn, oldRefreshTokenId);
    // The oldRefreshTokenId is used for rotation: delete the old one when issuing a new one.

    return token;
  }

  async verifyRefreshToken(token: string): Promise<RefreshTokenPayload> {
    const secret = this.configService.get<string>('JWT_REFRESH_SECRET');
    try {
      const payload = this.jwtService.verify<RefreshTokenPayload>(token, { secret });
      // Additionally, check if it's valid in the store (not revoked, not expired beyond JWT claim)
      // const storedToken = await this.getStoredRefreshToken(payload.jti);
      // if (!storedToken || storedToken.userId !== payload.sub) { ... }
      return payload;
    } catch (error) {
      throw new UnauthorizedException(`Invalid refresh token: ${error.message}`);
    }
  }

  async revokeRefreshToken(jti: string): Promise<void> {
    // Remove from DB or add to a refresh token blacklist
    // await this.refreshTokenRepository.delete({ jti });
    console.log(`Refresh token ${jti} marked for revocation.`);
  }

  // --- Specific-Purpose Tokens (e.g., Password Reset) ---
  async generatePasswordResetToken(userId: string): Promise<string> {
    const nonce = crypto.randomBytes(16).toString('hex');
    const payload: SpecificPurposeTokenPayload = {
      sub: userId,
      type: 'password_reset',
      nonce: nonce, // To ensure single use
    };
    const secret = this.configService.get<string>('JWT_PASSWORD_RESET_SECRET');
    const expiresIn = this.configService.get<string>('JWT_PASSWORD_RESET_EXPIRATION', '15m');
    if (!secret) throw new InternalServerErrorException('Password reset token secret missing.');

    const token = this.jwtService.sign(payload, { secret, expiresIn });
    // Store nonce or a hash of the token to ensure it's used only once
    // E.g., await this.storeOneTimeToken(userId, 'password_reset', nonce, expiresIn);
    return token;
  }

  async verifyPasswordResetToken(token: string): Promise<SpecificPurposeTokenPayload> {
    const secret = this.configService.get<string>('JWT_PASSWORD_RESET_SECRET');
    try {
      const payload = this.jwtService.verify<SpecificPurposeTokenPayload>(token, { secret });
      if (payload.type !== 'password_reset') {
        throw new BadRequestException('Invalid token type.');
      }
      // Check if nonce is still valid (not used yet)
      // if (!await this.isOneTimeTokenValid(payload.sub, 'password_reset', payload.nonce)) {
      //   throw new BadRequestException('Token already used or expired.');
      // }
      return payload;
    } catch (error) {
      throw new UnauthorizedException(`Invalid password reset token: ${error.message}`);
    }
  }

  async invalidateOneTimeToken(userId: string, type: 'password_reset' | 'email_verification', nonce: string): Promise<void> {
    // Mark the nonce as used in your store
    console.log(`One-time token ${type} for user ${userId} with nonce ${nonce} invalidated.`);
  }

  // --- Token Revocation (Blacklist Example) ---
  async revokeAccessToken(jti: string, expiresIn: number): Promise<void> {
    // Store JTI in Redis with an expiry matching the token's remaining validity
    // await this.redisClient.set(`revoked_jti:${jti}`, 'revoked', 'EX', expiresIn);
    console.log(`Access token JTI ${jti} added to blacklist.`);
  }

  async isTokenRevoked(jti: string): Promise<boolean> {
    // const result = await this.redisClient.get(`revoked_jti:${jti}`);
    // return !!result;
    return false; // Placeholder
  }
}
```

## 3. Interactions

*   **`AuthService`**: The primary consumer. It calls `TokenService` to:
    *   Generate access and refresh tokens upon successful login.
    *   Verify access tokens for protected resources (though this might be done by an `AuthGuard` that uses `TokenService`).
    *   Process refresh token requests.
    *   Generate and verify password reset, email verification tokens.
    *   Request token revocation (e.g., on logout).
*   **`ConfigService` (`@nestjs/config`)**: To retrieve secrets, expiration times, and other token-related configurations.
*   **`JwtService` (`@nestjs/jwt`)**: The underlying library used for JWT signing and verification operations.
*   **Database/Cache (e.g., PostgreSQL, Redis)**: For storing refresh tokens, token blacklists (revoked JTIs), or nonces for single-use tokens.
*   **NestJS Guards (e.g., `AuthGuard`)**: Guards protecting API endpoints would use `TokenService.verifyAccessToken()` to validate incoming tokens.

## 4. Token Security Best Practices

*   **Strong Secrets**: Use long, random, and unique secrets for signing different types of tokens. Store them securely (e.g., environment variables, secrets manager).
*   **HTTPS Everywhere**: All communication involving tokens must be over HTTPS.
*   **Algorithm Choice**: Prefer asymmetric algorithms (RS256, ES256) if tokens need to be verified by multiple services that don't share a common secret. Symmetric (HS256) is simpler if only one service (User Service) issues and verifies.
*   **Short-Lived Access Tokens**: Keep access token expiration times short (e.g., 5-60 minutes).
*   **Secure Refresh Tokens**: Treat refresh tokens as highly sensitive credentials. Store them securely (hashed if in DB), make them HttpOnly and Secure if used in cookies, and implement rotation.
*   **Token Revocation**: Implement a reliable revocation mechanism for immediate invalidation when needed.
*   **Minimum Necessary Claims**: Include only essential information in token payloads.
*   **`jti` (JWT ID) Claim**: Useful for tracking and revoking individual tokens.
*   **`aud` (Audience) and `iss` (Issuer) Claims**: Use these to scope tokens to specific services or purposes.

## 5. Configuration

Token secrets, algorithms, and expiration times should be externalized via a configuration management system (`@nestjs/config`) and not hardcoded.

Example configuration keys:
*   `JWT_ACCESS_SECRET`
*   `JWT_ACCESS_EXPIRATION` (e.g., '15m')
*   `JWT_REFRESH_SECRET`
*   `JWT_REFRESH_EXPIRATION` (e.g., '7d')
*   `JWT_PASSWORD_RESET_SECRET`
*   `JWT_PASSWORD_RESET_EXPIRATION` (e.g., '1h')
*   `JWT_ISSUER`
*   `JWT_AUDIENCE`

## 6. Future Enhancements

*   **Key Rotation**: Implementing automated rotation of signing keys/secrets.
*   **More Sophisticated Revocation**: Advanced revocation strategies like global logout or session management linked to tokens.
*   **Hardware Security Modules (HSMs)**: For storing and using signing keys in highly secure environments.

`TokenService` is a vital security component, centralizing the complex logic of token management and helping to protect user sessions and sensitive operations.
