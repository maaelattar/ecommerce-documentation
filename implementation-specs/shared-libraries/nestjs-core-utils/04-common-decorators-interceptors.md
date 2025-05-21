# 04: Common Decorators & Interceptors

## 1. Purpose

This section of the `nestjs-core-utils` library will house a collection of reusable NestJS decorators and interceptors. These components aim to simplify common tasks, reduce boilerplate code in services, and enforce consistent patterns for request handling, response manipulation, and context extraction.

Key objectives:
*   Provide convenient decorators for accessing request-scoped data (e.g., current user, correlation ID).
*   Offer interceptors for common request/response transformations or logging aspects not covered by the main `LoggingModule` interceptor.
*   Ensure these components are well-tested and follow NestJS best practices.

## 2. Potential Decorators

### 2.1. `@CurrentUser()` Decorator

*   **Purpose:** To easily inject a deserialized user object (or just user ID) into route handlers or services. This user object is typically populated by an authentication guard (e.g., `JwtAuthGuard` from an auth-specific shared library or the User Service client).
*   **Implementation:** A custom parameter decorator that extracts user information from the `request` object (e.g., `request.user`).
    ```typescript
    // current-user.decorator.ts
    import { createParamDecorator, ExecutionContext } from '@nestjs/common';

    export interface AuthenticatedUser {
      id: string; // or number, depending on your user ID type
      roles: string[];
      // other relevant fields like email, username, etc.
    }

    export const CurrentUser = createParamDecorator(
      (data: keyof AuthenticatedUser | undefined, ctx: ExecutionContext): AuthenticatedUser | AuthenticatedUser[keyof AuthenticatedUser] | undefined => {
        const request = ctx.switchToHttp().getRequest();
        const user = request.user as AuthenticatedUser; // Assuming passport or a similar guard populates req.user
        return data ? user?.[data] : user;
      },
    );
    ```
*   **Usage:**
    ```typescript
    @Get('profile')
    @UseGuards(JwtAuthGuard) // Example guard
    async getProfile(@CurrentUser() user: AuthenticatedUser) {
      return this.userService.findProfile(user.id);
    }

    @Get('my-id')
    @UseGuards(JwtAuthGuard)
    async getMyId(@CurrentUser('id') userId: string) {
      return { yourIdIs: userId };
    }
    ```

### 2.2. `@CorrelationId()` Decorator

*   **Purpose:** To easily inject the current request's correlation ID (e.g., `x-correlation-id` header) into route handlers or services for logging or propagation.
*   **Implementation:** A custom parameter decorator that extracts the ID from request headers.
    ```typescript
    // correlation-id.decorator.ts
    import { createParamDecorator, ExecutionContext } from '@nestjs/common';
    import { v4 as uuidv4 } from 'uuid'; // Or use a header from upstream like API Gateway

    export const CorrelationId = createParamDecorator(
      (data: unknown, ctx: ExecutionContext): string => {
        const request = ctx.switchToHttp().getRequest();
        let correlationId = request.headers['x-correlation-id'] as string;
        if (!correlationId) {
          correlationId = uuidv4(); // Generate one if not present
          request.headers['x-correlation-id'] = correlationId; // Optional: set it back for downstream if generated here
        }
        return correlationId;
      },
    );
    ```
*   **Usage:**
    ```typescript
    @Post('process')
    async processData(@Body() data: any, @CorrelationId() corrId: string) {
      this.logger.log('Processing data with correlation ID', corrId);
      // ...
    }
    ```

## 3. Potential Interceptors

### 3.1. `ResponseTransformInterceptor` (Example)

*   **Purpose:** To consistently wrap API responses in a standard structure if desired (e.g., `{ "data": ... }`). This is an opinionated choice and might not be universally adopted.
*   **Implementation:**
    ```typescript
    // response-transform.interceptor.ts
    import { Injectable, NestInterceptor, ExecutionContext, CallHandler } from '@nestjs/common';
    import { Observable } from 'rxjs';
    import { map } from 'rxjs/operators';

    export interface StandardResponse<T> {
      data: T;
      // statusCode?: number; // Could be added by a global filter or here
      // timestamp?: string;
    }

    @Injectable()
    export class ResponseTransformInterceptor<T> implements NestInterceptor<T, StandardResponse<T>> {
      intercept(context: ExecutionContext, next: CallHandler): Observable<StandardResponse<T>> {
        return next.handle().pipe(map(data => ({ data })));
      }
    }
    ```
*   **Usage:** Can be applied globally or to specific controllers/routes.

### 3.2. `SanitizeResponseInterceptor` (Example for specific use cases)

*   **Purpose:** To remove or mask sensitive fields from responses before they are sent to the client. This is highly context-dependent and should be used carefully.
*   **Implementation:** Would involve inspecting the response data and removing/transforming fields based on predefined rules or decorators on DTOs.
*   **Note:** Often, it's better to ensure DTOs used for responses *only* contain the fields that are safe to send, rather than relying on an interceptor to strip them out. However, for generic handlers or certain ORM entities returned directly (not always a good practice), it might have a niche use.

### 3.3. `TimeoutInterceptor` (If not handled at Gateway/LB level)

*   **Purpose:** To enforce a server-side timeout on requests. If a request handler takes too long, the interceptor would terminate it and return a timeout error (e.g., 504 Gateway Timeout).
*   **Implementation:** Uses `rxjs` `timeout` operator.
    ```typescript
    // timeout.interceptor.ts
    import { Injectable, NestInterceptor, ExecutionContext, CallHandler, RequestTimeoutException } from '@nestjs/common';
    import { Observable, throwError } from 'rxjs';
    import { timeout, catchError } from 'rxjs/operators';

    @Injectable()
    export class TimeoutInterceptor implements NestInterceptor {
      constructor(private readonly defaultTimeout: number = 5000) {} // Default 5s

      intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
        return next.handle().pipe(
          timeout(this.defaultTimeout),
          catchError(err => {
            if (err.name === 'TimeoutError') { // Check for RxJS TimeoutError
              return throwError(() => new RequestTimeoutException());
            }
            return throwError(() => err);
          }),
        );
      }
    }
    ```
*   **Usage:** Can be applied globally with a default timeout, or per-controller/route with specific timeouts.

## 4. Considerations

*   **Overhead:** Interceptors add processing overhead. They should be used judiciously and their performance impact considered, especially if applied globally to high-throughput endpoints.
*   **Ordering:** The order in which interceptors are applied matters. This should be documented for users of the shared library.
*   **Specificity:** Decide if an interceptor is truly generic enough for the shared library or if it's better implemented within a specific service that needs its behavior.
*   **Testing:** All decorators and interceptors must be thoroughly unit-tested.

This collection of decorators and interceptors will grow organically as common patterns and needs are identified across services. The initial set will focus on high-impact utilities like `@CurrentUser` and potentially a `TimeoutInterceptor` or a basic `ResponseTransformInterceptor` if a standard response wrapper is desired.