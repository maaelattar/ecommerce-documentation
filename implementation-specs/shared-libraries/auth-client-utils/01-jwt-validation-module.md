# 01: JWT Validation Module and Guard

## 1. Introduction

This document details the `JwtAuthModule` and `JwtAuthGuard`, which are central components of the `auth-client-utils` library. Their primary purpose is to provide a reusable and configurable mechanism for NestJS microservices to protect their endpoints by validating JSON Web Tokens (JWTs) issued by the central User Service.

## 2. JwtAuthModule

The `JwtAuthModule` is a dynamic NestJS module responsible for configuring the Passport.js JWT strategy (`passport-jwt`).

### 2.1. Configuration (`JwtAuthModuleOptions`)

The module will be configured using a `JwtAuthModuleOptions` object, typically provided via a `.forRoot()` or `.forRootAsync()` static method to allow for asynchronous configuration (e.g., fetching options from `ConfigService`).

Key configuration options will include:

```typescript
interface JwtAuthModuleOptions {
  jwksUri?: string; // URI for fetching JSON Web Key Set (JWKS) - preferred method
  publicKey?: string; // Static public key (PEM format) - alternative if JWKS is not available
  secretOrKeyProvider?: (request: any, rawJwtToken: any, done: (err: any, secretOrKey: string | Buffer) => void) => void; // For more complex key provision
  jwtFromRequest?: JwtFromRequestFunction; // Function to extract JWT from request (e.g., fromAuthHeaderAsBearerToken())
  issuer?: string; // Expected issuer claim (e.g., 'https://auth.your-ecommerce.com')
  audience?: string | string[]; // Expected audience claim(s)
  algorithms?: string[]; // Supported signing algorithms (e.g., ['RS256'])
  ignoreExpiration?: boolean; // Default: false
  // ... other relevant options from passport-jwt StrategyOptions
}

// Example: For use with @nestjs/config
interface JwtAuthModuleAsyncOptions extends Pick<ModuleMetadata, 'imports'> {
  useExisting?: Type<JwtAuthModuleOptionsFactory>;
  useClass?: Type<JwtAuthModuleOptionsFactory>;
  useFactory?: (
    ...args: any[]
  ) => Promise<JwtAuthModuleOptions> | JwtAuthModuleOptions;
  inject?: any[];
}

interface JwtAuthModuleOptionsFactory {
  createJwtAuthOptions(): Promise<JwtAuthModuleOptions> | JwtAuthModuleOptions;
}
```

*   **`jwksUri` (Recommended):** The endpoint provided by the User Service where public keys can be fetched (e.g., `https://user-service/.well-known/jwks.json`). The module will use a library like `jwks-rsa` to retrieve the appropriate signing key based on the `kid` in the JWT header.
*   **`publicKey`:** If JWKS is not available, a static public key can be provided.
*   **`secretOrKeyProvider`**: Allows for custom logic to provide the secret or key.
*   **`jwtFromRequest`:** Defaults to `ExtractJwt.fromAuthHeaderAsBearerToken()`.
*   **`issuer`, `audience`, `algorithms`:** Standard JWT claims to validate against.
*   **`ignoreExpiration`:** Should generally be `false` for security.

### 2.2. Registration

Services will import and configure `JwtAuthModule` in their root module:

```typescript
// In a service's app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { JwtAuthModule } from '@your-org/auth-client-utils'; // Assuming published package

@Module({
  imports: [
    ConfigModule.forRoot(/* ... */),
    JwtAuthModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        jwksUri: configService.get<string>('AUTH_JWKS_URI'),
        issuer: configService.get<string>('AUTH_JWT_ISSUER'),
        audience: configService.get<string>('AUTH_JWT_AUDIENCE'),
        algorithms: ['RS256'], // Example
      }),
      inject: [ConfigService],
    }),
    // ... other modules
  ],
})
export class AppModule {}
```

### 2.3. JWT Strategy Implementation

Internally, `JwtAuthModule` will set up the `passport-jwt` strategy. The strategy's `validate` function will be responsible for taking the decoded JWT payload and returning a user object (or a simplified representation) that will be attached to the `Request` object by Passport.

```typescript
// Simplified internal strategy logic within the module
import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { JwksClient } from 'jwks-rsa';

// ... (assuming options are injected or available)

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(/* injected options from JwtAuthModule */) {
    super({
      // ... configuration passed from JwtAuthModuleOptions
      // Example for JWKS:
      secretOrKeyProvider: (request, rawJwtToken, done) => {
        const client = new JwksClient({ jwksUri: /* options.jwksUri */ });
        const decodedToken = // decode rawJwtToken to get header.kid (careful with jwt.decode without verification first)
        client.getSigningKey(/* decodedToken.header.kid */, (err, key) => {
          if (err) {
            return done(err);
          }
          const signingKey = key.getPublicKey();
          done(null, signingKey);
        });
      },
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(), // or options.jwtFromRequest
      issuer: /* options.issuer */,
      audience: /* options.audience */,
      algorithms: /* options.algorithms */,
      ignoreExpiration: false, // or options.ignoreExpiration
    });
  }

  async validate(payload: any) {
    // `payload` is the decoded JWT payload.
    // This function should return the user object or a subset of it.
    // For example, if roles/permissions are directly in the token:
    return { 
      userId: payload.sub, // standard 'sub' claim for user ID
      username: payload.username,
      roles: payload.roles, 
      permissions: payload.permissions 
      // ... any other relevant fields from the token payload
    };
  }
}
```

## 3. JwtAuthGuard

The `JwtAuthGuard` is a NestJS Guard that leverages the configured Passport JWT strategy to protect routes.

### 3.1. Usage

It can be applied at the controller level or route level:

```typescript
import { Controller, Get, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '@your-org/auth-client-utils';

@Controller('protected-resource')
@UseGuards(JwtAuthGuard) // Apply to all routes in this controller
export class ProtectedResourceController {
  @Get()
  getProtectedData() {
    // This route is now protected. 
    // If a valid JWT is not provided, or if it's invalid/expired,
    // Passport will automatically return a 401 Unauthorized.
    return { message: 'This is protected data!' };
  }

  @Get('specific')
  @UseGuards(JwtAuthGuard) // Can also be applied to specific routes
  getSpecificProtectedData() {
    return { message: 'Specific protected data.' };
  }
}
```

### 3.2. Behavior

*   If the JWT is valid (signature verified, claims like `iss`, `aud`, `exp` are okay), the guard allows the request to proceed. The user object returned by the `JwtStrategy.validate()` method will be available on `request.user`.
*   If the JWT is missing, malformed, invalid, or expired, the guard will automatically trigger a `401 Unauthorized` response.
*   It integrates with standard NestJS exception handling.

## 4. Key Considerations

*   **Security of JWKS Endpoint:** If using `jwksUri`, the User Service must secure this endpoint and ensure keys are rotated appropriately.
*   **Token Content:** The consuming services rely on the content of the JWT issued by the User Service. The `validate` function in the strategy should be tailored to extract the necessary information (e.g., user ID, roles, permissions) that services need.
*   **Error Handling:** While `JwtAuthGuard` provides a default 401, services might want to customize error responses using global exception filters (potentially provided by `nestjs-core-utils`).

This module and guard aim to provide a robust and easy-to-use foundation for token-based authentication in the microservices architecture.
