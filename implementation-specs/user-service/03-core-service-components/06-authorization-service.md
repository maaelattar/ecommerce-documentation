# 06 - AuthorizationService

The `AuthorizationService` is the component responsible for making access control decisions. It determines whether a given user (or client, or system) has the necessary permissions to perform a specific action on a particular resource. It integrates information from `UserService` (to know who the user is), `RoleService` (to know the user's roles), and `PermissionService` (to understand what permissions roles have).

This service is often implemented using NestJS Guards that are applied at the controller or handler level.

## 1. Responsibilities

*   **Access Control Checks**: The primary responsibility is to answer the question: "Can User X perform Action Y on Resource Z?"
*   **Permission Aggregation**: Collect all permissions granted to a user through their assigned roles.
*   **Policy Enforcement**: Apply authorization policies (e.g., RBAC, potentially ABAC elements).
*   **Contextual Checks**: Optionally, consider the context of the request (e.g., IP address, time of day, resource attributes) if implementing more advanced ABAC policies.
*   **Deny by Default**: Typically operates on a "deny by default" principle – access is only granted if an explicit permission allows it.

## 2. Key Methods & Logic (Conceptual NestJS Example)

The `AuthorizationService` itself might not expose many public methods for direct invocation by other services. Instead, its logic is often encapsulated within NestJS Guards or similar intercepting mechanisms.

**Conceptual NestJS Guard (`RolesGuard` or `PermissionsGuard`):**

```typescript
import { Injectable, CanActivate, ExecutionContext, ForbiddenException, UnauthorizedException } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Observable } from 'rxjs';
import { RoleService } from './role.service'; // To get user's roles
import { PermissionService } from './permission.service'; // To get permissions for roles
// Assume a custom decorator like @RequiredPermissions('product:create')
export const REQUIRED_PERMISSIONS_KEY = 'requiredPermissions';
export const RequiredPermissions = (...permissions: string[]) => SetMetadata(REQUIRED_PERMISSIONS_KEY, permissions);

@Injectable()
export class PermissionsGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private roleService: RoleService, // Simplified: In reality, you might get roles from a hydrated User object
    private permissionService: PermissionService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requiredPermissions = this.reflector.getAllAndOverride<string[]>(
      REQUIRED_PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requiredPermissions || requiredPermissions.length === 0) {
      return true; // No specific permissions required, access granted
    }

    const request = context.switchToHttp().getRequest();
    const user = request.user; // Assuming user object is populated by an AuthenticationGuard

    if (!user || !user.id) {
      throw new UnauthorizedException('User not authenticated.');
    }

    // 1. Get user's roles
    // In a real app, user.roles might already be populated on the user object from JWT or session
    const userRoles = user.roles || await this.roleService.getUserRoles(user.id);
    if (!userRoles || userRoles.length === 0) {
      throw new ForbiddenException('User has no assigned roles.');
    }

    // 2. Get all permissions for those roles
    let userPermissions = new Set<string>();
    for (const role of userRoles) {
      const permissionsForRole = await this.permissionService.getPermissionsForRole(role.id);
      permissionsForRole.forEach(p => userPermissions.add(p.name)); // Assuming permission name is the string like 'product:create'
    }

    // 3. Check if the user has ALL required permissions
    const hasAllRequiredPermissions = requiredPermissions.every(rp => userPermissions.has(rp));

    if (hasAllRequiredPermissions) {
      return true;
    } else {
      throw new ForbiddenException('Insufficient permissions.');
    }
  }
}
```

**Core Logic within `AuthorizationService` (if called directly or by a guard):**

```typescript
import { Injectable } from '@nestjs/common';
import { User } from '../entities/user.entity';
import { Role } from '../entities/role.entity';
import { Permission } from '../entities/permission.entity';
import { RoleService } from './role.service';
import { PermissionService } from './permission.service';

@Injectable()
export class AuthorizationService {
  constructor(
    private readonly roleService: RoleService,
    private readonly permissionService: PermissionService,
  ) {}

  async can(user: User, action: string, resource?: string): Promise<boolean> {
    if (!user || !user.roles || user.roles.length === 0) {
      return false; // No roles, no permissions
    }

    const permissionToCheck = resource ? `${action}:${resource}` : action;

    for (const role of user.roles) {
      // In a real system, user.roles would be populated with Role entities that might have their permissions pre-loaded or fetched.
      // This is a simplified representation.
      const roleWithPermissions = await this.roleService.findRoleById(role.id); // Fetch full role if not already hydrated
      if (roleWithPermissions) {
          const permissions = await this.permissionService.getPermissionsForRole(roleWithPermissions.id);
          if (permissions.some(p => p.name === permissionToCheck)) {
            return true; // Found a role with the required permission
          }
      }
    }
    return false; // No role granted the required permission
  }

  // More complex ABAC style check
  async canAccessResource(user: User, action: string, resourceEntity: any): Promise<boolean> {
    // 1. Basic RBAC check (as above)
    const rbacAllowed = await this.can(user, action, resourceEntity.constructor.name.toLowerCase()); // e.g., 'product'
    if (!rbacAllowed) return false;

    // 2. Additional ABAC checks (example: user can only edit their own posts)
    if (action === 'edit' && resourceEntity.constructor.name.toLowerCase() === 'post') {
      if (resourceEntity.authorId !== user.id) {
        return false; // User is not the author
      }
    }
    return true;
  }
}
```

## 3. Interactions

*   **Authentication Mechanism (e.g., Passport, custom AuthGuard)**: Relies on the authentication system to identify the current user and populate `request.user`.
*   **`UserService`**: Indirectly, by relying on the `user` object provided by the authentication layer which was populated using `UserService`.
*   **`RoleService`**: To fetch the roles assigned to the current user.
*   **`PermissionService`**: To fetch the permissions associated with those roles.
*   **NestJS `Reflector` & Decorators**: Used in guards to read metadata (like `@RequiredPermissions()`) from route handlers or controllers.
*   **Controllers/Resolvers**: Authorization logic (typically via Guards) is applied to protect routes and operations.

## 4. Policy Decision Point (PDP)

The `AuthorizationService` (or the guards it empowers) acts as the Policy Decision Point (PDP) in the access control architecture. It evaluates requests against defined policies (permissions and roles) and makes a decision (grant or deny access).

## 5. Security Considerations

*   **Correctness of Logic**: Bugs in the authorization logic can lead to severe security vulnerabilities (either denying access to legitimate users or granting access to unauthorized users).
*   **Performance**: Authorization checks are performed on many requests. The process of fetching roles and permissions should be efficient. Caching strategies might be employed for user roles/permissions, with appropriate cache invalidation when they change.
*   **Centralization**: Centralizing authorization logic makes it easier to manage, audit, and update policies.
*   **Clarity of Permissions**: Ensure that permission names and their meanings are clear and unambiguous.
*   **Testing**: Thoroughly test authorization logic with various user types, roles, and scenarios.
*   **Fail-Safe**: Ensure that if any part of the authorization check fails (e.g., database error while fetching roles), access is denied by default.

## 6. Future Enhancements

*   **Attribute-Based Access Control (ABAC)**: Extend beyond simple RBAC to include policies based on user attributes, resource attributes, and environmental conditions (e.g., user can only access financial data during business hours from a corporate IP).
*   **Policy Definition Language/Engine**: For very complex scenarios, integrate a dedicated policy engine (e.g., Open Policy Agent - OPA) that allows policies to be defined in a specialized language (like Rego).
*   **Real-time Updates**: Mechanisms for real-time propagation of changes in roles/permissions to active sessions (e.g., if an admin revokes a permission, it should take effect immediately, potentially by invalidating tokens or sessions).
*   **Just-In-Time (JIT) Permission Checks**: Evaluating permissions at the very moment they are needed, potentially involving more dynamic data.

The `AuthorizationService` is a cornerstone of application security, ensuring that users can only perform actions and access data for which they have explicit permission.
