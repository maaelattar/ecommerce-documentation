# 05 - PermissionService

The `PermissionService` is responsible for managing granular permissions within the system. These permissions represent specific actions or access rights (e.g., `create_product`, `view_order_details`, `manage_users`). This service handles CRUD operations for the `Permission` entity and the linkage between roles and permissions through the `RolePermissionLink` entity (or a similar mechanism).

## 1. Responsibilities

*   **Permission Management (CRUD)**:
    *   Creating new permissions (defining the action/resource, e.g., `product:create`, `user:read_all`).
    *   Retrieving permission details (by ID, name, or action/resource pair).
    *   Listing all available permissions, possibly with filtering or grouping.
    *   Updating permission properties (e.g., description, associated resource type).
    *   Deleting permissions (with caution, considering their usage in roles).
*   **Role-Permission Linkage**:
    *   Assigning one or more permissions to a specific role.
    *   Removing permissions from a role.
    *   Listing permissions assigned to a particular role.
    *   Listing roles that have a particular permission.
*   **Permission Checking Utilities (Potentially)**:
    *   While the primary responsibility for checking if a user *has* a permission usually falls to the `AuthorizationService`, the `PermissionService` might provide low-level utilities to see if a direct role-permission link exists.

## 2. Key Methods (Conceptual NestJS Example)

```typescript
import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm'; // Assuming TypeORM
import { Repository, In } from 'typeorm';
import { Permission } from '../entities/permission.entity';
import { Role } from '../entities/role.entity';
import { RolePermissionLink } from '../entities/role-permission-link.entity'; // Join entity
import { CreatePermissionDto } from '../dto/create-permission.dto';
import { UpdatePermissionDto } from '../dto/update-permission.dto';
import { RoleService } from './role.service'; // To fetch role objects
import { UserEventPublisher } from './user-event-publisher.service';

@Injectable()
export class PermissionService {
  constructor(
    @InjectRepository(Permission)
    private readonly permissionRepository: Repository<Permission>,
    @InjectRepository(RolePermissionLink)
    private readonly rolePermissionLinkRepository: Repository<RolePermissionLink>,
    private readonly roleService: RoleService, // To validate Role existence
    private readonly userEventPublisher: UserEventPublisher,
  ) {}

  async createPermission(createPermissionDto: CreatePermissionDto): Promise<Permission> {
    const { action, subject, resource } = createPermissionDto;
    const name = createPermissionDto.name || `${action}:${subject || resource}`;

    const existingPermission = await this.permissionRepository.findOne({ where: { name } });
    if (existingPermission) {
      throw new BadRequestException(`Permission with name '${name}' already exists.`);
    }
    const permission = this.permissionRepository.create({ ...createPermissionDto, name });
    const savedPermission = await this.permissionRepository.save(permission);
    // Event: this.userEventPublisher.publishPermissionCreated(savedPermission);
    return savedPermission;
  }

  async findAllPermissions(): Promise<Permission[]> {
    return this.permissionRepository.find();
  }

  async findPermissionById(id: string): Promise<Permission | null> {
    return this.permissionRepository.findOneBy({ id });
  }

  async findPermissionByName(name: string): Promise<Permission | null> {
    return this.permissionRepository.findOneBy({ name });
  }

  async updatePermission(id: string, updatePermissionDto: UpdatePermissionDto): Promise<Permission> {
    const permission = await this.findPermissionById(id);
    if (!permission) {
      throw new NotFoundException(`Permission with ID ${id} not found.`);
    }

    if (updatePermissionDto.name && updatePermissionDto.name !== permission.name) {
      const existing = await this.findPermissionByName(updatePermissionDto.name);
      if (existing) {
        throw new BadRequestException(`Permission name '${updatePermissionDto.name}' already taken.`);
      }
    }

    Object.assign(permission, updatePermissionDto);
    const updatedPermission = await this.permissionRepository.save(permission);
    // Event: this.userEventPublisher.publishPermissionUpdated(updatedPermission);
    return updatedPermission;
  }

  async deletePermission(id: string): Promise<void> {
    const permission = await this.findPermissionById(id);
    if (!permission) {
      throw new NotFoundException(`Permission with ID ${id} not found.`);
    }
    // Before deleting, ensure it's not linked to any roles or handle unlinking
    const links = await this.rolePermissionLinkRepository.count({ where: { permissionId: id }});
    if (links > 0) {
        throw new BadRequestException(`Permission ID ${id} is assigned to roles and cannot be deleted directly. Unassign first.`);
    }
    await this.permissionRepository.remove(permission);
    // Event: this.userEventPublisher.publishPermissionDeleted({ permissionId: id, name: permission.name });
  }

  // --- Role-Permission Assignments ---

  async assignPermissionsToRole(roleId: string, permissionIds: string[]): Promise<Role> {
    const role = await this.roleService.findRoleById(roleId);
    if (!role) {
      throw new NotFoundException(`Role with ID ${roleId} not found.`);
    }

    const permissions = await this.permissionRepository.findBy({ id: In(permissionIds) });
    if (permissions.length !== permissionIds.length) {
      throw new BadRequestException('One or more permission IDs are invalid.');
    }

    const links: RolePermissionLink[] = [];
    for (const permission of permissions) {
      // Check if link already exists
      const existingLink = await this.rolePermissionLinkRepository.findOneBy({ roleId, permissionId: permission.id });
      if (!existingLink) {
        links.push(this.rolePermissionLinkRepository.create({ roleId, permissionId: permission.id }));
      }
    }
    await this.rolePermissionLinkRepository.save(links);
    
    // Event: this.userEventPublisher.publishRolePermissionsUpdated(role, permissions);
    // Return the role, possibly with its updated list of permissions (requires another query or relation update)
    return this.roleService.findRoleById(roleId); // Re-fetch to get updated relations potentially
  }

  async removePermissionsFromRole(roleId: string, permissionIds: string[]): Promise<void> {
    const role = await this.roleService.findRoleById(roleId);
    if (!role) {
      throw new NotFoundException(`Role with ID ${roleId} not found.`);
    }

    await this.rolePermissionLinkRepository.delete({
      roleId: roleId,
      permissionId: In(permissionIds),
    });
    // Event: this.userEventPublisher.publishRolePermissionsUpdated(role, /* removed permissions */);
  }

  async getPermissionsForRole(roleId: string): Promise<Permission[]> {
    const role = await this.roleService.findRoleById(roleId);
    if (!role) {
      throw new NotFoundException(`Role with ID ${roleId} not found.`);
    }

    const links = await this.rolePermissionLinkRepository.find({ 
        where: { roleId },
        relations: ['permission'] 
    });
    return links.map(link => link.permission);
  }

  async getRolesForPermission(permissionId: string): Promise<Role[]> {
    const permission = await this.findPermissionById(permissionId);
    if (!permission) {
      throw new NotFoundException(`Permission with ID ${permissionId} not found.`);
    }

    const links = await this.rolePermissionLinkRepository.find({
        where: { permissionId },
        relations: ['role']
    });
    return links.map(link => link.role);
  }
}
```

## 3. Interactions

*   **`RoleService`**: `PermissionService` collaborates with `RoleService` to validate role existence when linking permissions and to retrieve role details.
*   **`AuthorizationService`**: This is the primary consumer of permission data. `AuthorizationService` would use methods from `PermissionService` (or the underlying data) to determine if a user's roles grant them a specific permission for an action.
*   **Database**: Directly interacts with the `Permission` table and the `RolePermissionLink` join table (or equivalent).
*   **`UserEventPublisher`**: Publishes events like `PermissionCreated`, `PermissionUpdated`, `PermissionDeleted`, `RolePermissionsAssigned`.
*   **Administrative Interfaces**: Admin UIs would use `PermissionService` to manage the system's permissions and their assignments to roles.

## 4. Data Management & Integrity

*   **Permission Naming Convention**: Establish a clear and consistent naming convention for permissions (e.g., `resource:action` like `product:create`, or `verb:noun` like `create:product`). This helps in understanding and managing them.
*   **Handling Permission Deletion**: Deleting a permission that is actively used by roles can break access control. The service should either prevent deletion if linked or have a clear process for unlinking.
*   **Referential Integrity**: Foreign key constraints on `RolePermissionLink` to `Role` and `Permission` tables are crucial.

## 5. Security Considerations

*   **Granularity**: Define permissions at an appropriate level of granularity. Too broad, and they don't offer fine-grained control. Too narrow, and they become difficult to manage.
*   **Control over Management**: Only highly trusted administrators should be able to create, modify, delete permissions, or assign them to roles.
*   **Auditing**: Log all permission management and assignment events.
*   **Default Permissions**: Be cautious about permissions granted by default to new roles or users.

## 6. Future Enhancements

*   **Permission Grouping/Categorization**: For easier management in UIs if the number of permissions becomes very large.
*   **Resource-Instance Level Permissions**: Extending the model to support permissions on specific instances of a resource (e.g., permission to edit *this specific document* vs. *any document*). This often requires a more complex ABAC (Attribute-Based Access Control) model.
*   **Permission Discovery**: Mechanisms for services to register the permissions they require, potentially automating some aspects of permission creation or documentation.

`PermissionService` provides the fine-grained control necessary for a robust authorization system, working hand-in-hand with `RoleService` and `AuthorizationService`.
