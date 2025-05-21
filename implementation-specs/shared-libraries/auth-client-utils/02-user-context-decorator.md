# 02: User Context Decorator (`@CurrentUser`)

## 1. Introduction

Following the successful validation of a JWT by the `JwtAuthGuard` (detailed in `01-jwt-validation-module.md`), the payload of the token, processed by the `JwtStrategy`'s `validate` method, is attached to the NestJS `Request` object (typically as `request.user`).

The `@CurrentUser` decorator provides a clean, type-safe, and convenient way to access this user information directly within your controller route handlers, abstracting away the need to manually access `request.user`.

## 2. Purpose

*   **Simplify Access:** Provide a simple decorator to inject the authenticated user object or specific properties of it into route handlers.
*   **Improve Readability:** Make controller methods cleaner and more declarative.
*   **Type Safety:** Allow for better type inference of the user object in handlers when used with TypeScript.

## 3. Implementation

The `@CurrentUser` decorator will be a custom NestJS parameter decorator created using `createParamDecorator`.

```typescript
// In @your-org/auth-client-utils/src/decorators/current-user.decorator.ts

import { createParamDecorator, ExecutionContext } from '@nestjs/common';

/**
 * Interface for the expected user object structure attached by JwtStrategy.
 * This should be defined or imported from a common types location if shared
 * across the auth library and potentially consuming services for consistency.
 */
export interface AuthenticatedUser {
  userId: string | number; // Or whatever type 'sub' claim is
  username?: string;
  roles?: string[];
  permissions?: string[];
  // ... any other fields returned by JwtStrategy.validate()
}

export const CurrentUser = createParamDecorator(
  (data: keyof AuthenticatedUser | undefined, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    const user = request.user as AuthenticatedUser;

    if (!user) {
      // This case should ideally not be hit if JwtAuthGuard is applied correctly,
      // as the guard would throw an UnauthorizedException if no user is present.
      // However, it's a good practice for robustness.
      // Depending on strictness, you might throw an error or return undefined.
      console.warn('CurrentUser decorator used without a valid user on the request. Ensure JwtAuthGuard is active.');
      return undefined; 
    }

    return data ? user?.[data] : user;
  },
);
```

### 3.1. Key Aspects of Implementation

*   **`createParamDecorator`:** The core NestJS function for creating custom parameter decorators.
*   **`ExecutionContext`:** Used to access the underlying HTTP request.
*   **`request.user`:** The decorator retrieves the user object that `passport` (via `JwtAuthGuard` and `JwtStrategy`) attaches to the request.
*   **`AuthenticatedUser` Interface:** Defines the expected shape of the user object. This is crucial for type safety. This interface should align with what the `JwtStrategy.validate()` method returns.
*   **`data` Parameter:** The `data` argument passed to the decorator (e.g., `@CurrentUser('userId')`) allows for extracting a specific property from the user object. If `data` is undefined (i.e., `@CurrentUser()`), the entire user object is returned.
*   **Robustness:** Includes a check for the existence of `request.user`, though in a typical flow with `JwtAuthGuard`, this guard should prevent access if `user` is not populated.

## 4. Usage

Once `JwtAuthGuard` has successfully authenticated a request, the `@CurrentUser` decorator can be used in any route handler method as follows:

```typescript
import { Controller, Get, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../guards/jwt-auth.guard'; // Adjust path as necessary
import { CurrentUser, AuthenticatedUser } from './current-user.decorator'; // Adjust path

@Controller('profile')
@UseGuards(JwtAuthGuard)
export class ProfileController {

  // Inject the entire user object
  @Get()
  getProfile(@CurrentUser() user: AuthenticatedUser) {
    console.log('Authenticated user:', user);
    return { message: 'Your profile data', userDetails: user };
  }

  // Inject a specific property of the user object (e.g., userId)
  @Get('id')
  getUserId(@CurrentUser('userId') userId: string | number) {
    console.log('Authenticated user ID:', userId);
    return { message: 'Your user ID', id: userId };
  }

  // Example with roles, if present in AuthenticatedUser
  @Get('roles')
  getUserRoles(@CurrentUser('roles') roles: string[]) {
    if (roles && roles.includes('admin')) {
      return { message: 'Welcome Admin! You have special privileges.', yourRoles: roles };
    }
    return { message: 'Your roles', yourRoles: roles };
  }
}
```

## 5. Benefits

*   **Cleanliness:** Reduces the need to write `req.user` repeatedly and cast types.
*   **Testability:** Makes controller methods easier to test as the user object can be easily mocked when testing the handler in isolation.
*   **Declarative Style:** Aligns with NestJS's declarative programming model.

By providing this decorator, `auth-client-utils` further simplifies secure API development within the e-commerce platform.
