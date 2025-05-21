# 03: Role/Permission-Based Access Control (RBAC) Utilities (Future Consideration)

## 1. Introduction

This document outlines potential future enhancements to the `auth-client-utils` library, specifically focusing on Role-Based Access Control (RBAC) and permission-checking utilities. These features are currently considered optional and would be developed based on emerging common needs across multiple microservices.

While the `JwtAuthGuard` ensures a user is authenticated, and `@CurrentUser` provides user context (which may include roles/permissions claims from the JWT), dedicated RBAC utilities could further simplify authorization logic within route handlers.

## 2. Potential Scope

If implemented, these utilities might include:

*   **`@Roles(...roles: string[])` Decorator/Guard:**
    *   A decorator that could be applied to route handlers or controllers to restrict access to users possessing one or more specified roles.
    *   Example: `@Roles('admin', 'editor')` would allow access if the authenticated user (from `request.user` populated by `JwtStrategy`) has either the `admin` OR `editor` role in their JWT claims.
    *   This would likely be implemented as a NestJS Guard that inspects the `roles` array on the `AuthenticatedUser` object.

*   **`@Permissions(...permissions: string[])` Decorator/Guard:**
    *   Similar to `@Roles`, but for checking fine-grained permissions.
    *   Example: `@Permissions('product:create', 'product:edit')` would require the user to have *all* specified permissions (or define it as *any* based on desired logic).
    *   This would inspect a `permissions` array on the `AuthenticatedUser` object.

## 3. Design Considerations

*   **Source of Truth:** Roles and permissions would be expected to be part of the JWT payload, issued by the User Service.
*   **Complexity:** The initial implementation would likely focus on simple direct role/permission checks. More complex scenarios (e.g., hierarchical roles, resource-based permissions beyond what's in the token) might require more advanced solutions or be handled within individual services.
*   **Flexibility:** The decorators/guards should be flexible enough to handle common use cases (e.g., require one of many roles, require all of many permissions).
*   **Integration:** These would seamlessly integrate with the existing `JwtAuthGuard` and `CurrentUser` decorator.

## 4. Current Status

*   **Not Implemented:** These RBAC utilities are not part of the current version of `auth-client-utils`.
*   **Future Consideration:** Their development will be evaluated based on the recurring need for such declarative authorization checks across the platform's microservices.

If these features are prioritized, this document will be updated with detailed design and usage specifications.
