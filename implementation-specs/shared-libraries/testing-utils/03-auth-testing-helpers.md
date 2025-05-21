# 03: Authentication and Authorization Testing Helpers

## 1. Introduction

This document describes testing utilities within the `testing-utils` library that are designed to help test microservice endpoints protected by authentication and authorization mechanisms, specifically those using the `JwtAuthGuard` and user context decorators from the `@ecommerce-platform/auth-client-utils` library.

## 2. MockJwtAuthGuard

Services use `JwtAuthGuard` to protect routes. `MockJwtAuthGuard` provides a way to simulate the behavior of this guard during tests without actual JWT validation or needing a running User Service.

### 2.1. Purpose

*   Allow testing of protected routes by easily simulating authenticated or unauthenticated states.
*   Enable tests to define the user payload (`AuthenticatedUser`) that should be injected by the guard for an authenticated request.
*   Avoid external dependencies (like JWKS URI fetching) during unit/integration tests of route handlers.

### 2.2. Implementation Sketch

```typescript
// In @ecommerce-platform/testing-utils/src/mocks/mock-jwt-auth.guard.ts

import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Observable } from 'rxjs';
import { AuthenticatedUser } from '@ecommerce-platform/auth-client-utils'; // Assuming this interface is exported

@Injectable()
export class MockJwtAuthGuard implements CanActivate {
  // Static properties to control guard behavior for all instances in a test suite
  // or could be instance properties if the guard is provided via useValue with a specific instance.
  public static allow: boolean = true;
  public static user: AuthenticatedUser | null = {
    userId: 'test-user-123',
    username: 'testuser',
    roles: ['user'],
    permissions: ['read:profile'],
  };

  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean> {
    if (!MockJwtAuthGuard.allow) {
      return false; // Simulates 401/403, NestJS will handle the exception
    }
    if (MockJwtAuthGuard.user) {
      const request = context.switchToHttp().getRequest();
      request.user = MockJwtAuthGuard.user; // Attach the mock user to the request
    }
    return true;
  }

  // Optional: Methods to easily configure the mock guard for specific tests
  static setAllow(allow: boolean): void {
    MockJwtAuthGuard.allow = allow;
  }

  static setUser(user: AuthenticatedUser | null): void {
    MockJwtAuthGuard.user = user;
  }

  static reset(): void {
    MockJwtAuthGuard.allow = true;
    MockJwtAuthGuard.user = {
        userId: 'test-user-123',
        username: 'testuser',
        roles: ['user'],
        permissions: ['read:profile'],
    };
  }
}
```

### 2.3. Usage

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { YourProtectedController } from './your-protected.controller';
import { JwtAuthGuard, AuthenticatedUser } from '@ecommerce-platform/auth-client-utils';
import { MockJwtAuthGuard } from '@ecommerce-platform/testing-utils';
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest'; // For HTTP E2E style tests

describe('YourProtectedController', () => {
  // Example for controller/route level unit tests
  describe('Unit Tests', () => {
    let controller: YourProtectedController;

    beforeEach(async () => {
      MockJwtAuthGuard.reset(); // Reset to default mock behavior
      const module: TestingModule = await Test.createTestingModule({
        controllers: [YourProtectedController],
        providers: [
          // Provide other dependencies if YourProtectedController has them
        ],
      })
      // Override the actual guard with the mock globally or for specific modules
      .overrideGuard(JwtAuthGuard)
      .useClass(MockJwtAuthGuard)
      .compile();
      controller = module.get<YourProtectedController>(YourProtectedController);
    });

    it('should allow access and return data for authenticated user', async () => {
      MockJwtAuthGuard.setAllow(true);
      MockJwtAuthGuard.setUser({ userId: 'mock-id', roles: ['customer'] });
      // Call controller method directly, assuming @CurrentUser works due to request.user being set
      const result = await controller.getProfile({ userId: 'mock-id', roles: ['customer'] }); // Mock CurrentUser input
      expect(result).toBeDefined();
    });

    it('should deny access if guard is set to not allow', async () => {
        MockJwtAuthGuard.setAllow(false);
        // How you assert this depends on whether you test via HTTP or direct call + exception handling
        // For direct calls, you might expect an UnauthorizedException to be thrown by a real guard proxy
    });
  });

  // Example for E2E style tests with supertest
  describe('E2E Tests', () => {
    let app: INestApplication;

    beforeEach(async () => {
      MockJwtAuthGuard.reset();
      const moduleFixture: TestingModule = await Test.createTestingModule({
        controllers: [YourProtectedController],
      })
      .overrideGuard(JwtAuthGuard)
      .useClass(MockJwtAuthGuard)
      .compile();

      app = moduleFixture.createNestApplication();
      await app.init();
    });

    it('/GET protected-route (authenticated)', () => {
      MockJwtAuthGuard.setAllow(true);
      MockJwtAuthGuard.setUser({ userId: 'e2e-user', roles: ['admin'] });
      return request(app.getHttpServer())
        .get('/protected-route')
        .expect(200)
        .expect(/some data from protected route/);
    });

    it('/GET protected-route (unauthenticated)', () => {
      MockJwtAuthGuard.setAllow(false);
      return request(app.getHttpServer())
        .get('/protected-route')
        .expect(403); // Or 401, depending on how NestJS handles guard returning false
    });

    afterEach(async () => {
        await app.close();
    });
  });
});
```

## 3. TokenFactory

For tests that might need to simulate more aspects of a JWT payload or pass around token-like structures.

### 3.1. Purpose

*   Provide helper functions to easily generate mock JWT payloads or `AuthenticatedUser` objects with specific properties (userId, roles, permissions, custom claims).
*   Useful for tests where the exact structure or content of the user object passed by `@CurrentUser` is important.

### 3.2. Implementation Sketch

```typescript
// In @ecommerce-platform/testing-utils/src/factories/token.factory.ts
import { AuthenticatedUser } from '@ecommerce-platform/auth-client-utils';

export class TokenFactory {
  static createAuthenticatedUser(partialUser: Partial<AuthenticatedUser> = {}): AuthenticatedUser {
    const defaults: AuthenticatedUser = {
      userId: `test-user-${Date.now()}`,
      username: 'defaultTestUser',
      roles: ['user'],
      permissions: [],
      // any other default fields from AuthenticatedUser
    };
    return { ...defaults, ...partialUser };
  }

  // If you ever needed to generate actual (mock-signed) JWT strings for testing
  // more complex scenarios (e.g., a component that decodes tokens itself, which is rare),
  // you could add a method here using a library like `jsonwebtoken` with a test secret.
  // For most cases, just mocking AuthenticatedUser is sufficient.
}
```

### 3.3. Usage

```typescript
import { TokenFactory } from '@ecommerce-platform/testing-utils';

describe('SomeService that uses AuthenticatedUser', () => {
  it('should handle admin user correctly', () => {
    const adminUser = TokenFactory.createAuthenticatedUser({
      userId: 'admin-001',
      roles: ['admin', 'user'],
      permissions: ['manage:all'],
    });
    // ... use adminUser in your test logic
    // e.g., pass to a method, or set MockJwtAuthGuard.user = adminUser;
    MockJwtAuthGuard.setUser(adminUser);
    // ... rest of the test
  });
});
```

These authentication and authorization testing helpers will be crucial for verifying the security and behavior of protected endpoints and components.
