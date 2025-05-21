# 04 - RoleService

The `RoleService` is responsible for managing roles within the system as part of Role-Based Access Control (RBAC). It handles the CRUD operations for the `Role` entity and provides mechanisms to assign roles to users and potentially link roles to permissions (though the latter might be managed by `PermissionService` or `AuthorizationService`).

## 1. Responsibilities

*   **Role Management (CRUD)**:
    *   Creating new roles (e.g., `admin`, `editor`, `customer`, `support_agent`).
    *   Retrieving role details (by ID or name).
    *   Listing all available roles.
    *   Updating role properties (e.g., name, description).
    *   Deleting roles (with consideration for users currently assigned that role).
*   **Role Assignment to Users**:
    *   Assigning one or more roles to a specific user.
    *   Removing roles from a user.
    *   Listing roles assigned to a particular user.
    *   Listing users assigned to a particular role.
*   **Role-Permission Linkage (Potentially)**:
    *   While the direct linking of roles to permissions might be handled by a `RolePermissionLink` entity and managed by `PermissionService` or `AuthorizationService`, `RoleService` might offer utility methods to view permissions associated with a role.

## 2. Key Methods (Conceptual NestJS Example)

```typescript
import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm'; // Assuming TypeORM
import { Repository, In } from 'typeorm';
import { Role } from '../entities/role.entity';
import { User } from '../entities/user.entity'; // User entity
import { CreateRoleDto } from '../dto/create-role.dto';
import { UpdateRoleDto } from '../dto/update-role.dto';
// Assuming a UserToRole join entity or direct ManyToMany in User entity
// For simplicity, let's assume User entity has a `roles: Role[]` property managed by TypeORM
import { UserService } from './user.service'; // To fetch user objects
import { UserEventPublisher } from './user-event-publisher.service';

@Injectable()
export class RoleService {
  constructor(
    @InjectRepository(Role)
    private readonly roleRepository: Repository<Role>,
    private readonly userService: UserService, // For managing user-role assignments
    private readonly userEventPublisher: UserEventPublisher, 
  ) {}

  async createRole(createRoleDto: CreateRoleDto): Promise<Role> {
    const existingRole = await this.roleRepository.findOne({ where: { name: createRoleDto.name } });
    if (existingRole) {
      throw new BadRequestException(`Role with name '${createRoleDto.name}' already exists.`);
    }
    const role = this.roleRepository.create(createRoleDto);
    const savedRole = await this.roleRepository.save(role);
    // Event: this.userEventPublisher.publishRoleCreated(savedRole);
    return savedRole;
  }

  async findAllRoles(): Promise<Role[]> {
    return this.roleRepository.find();
  }

  async findRoleById(id: string): Promise<Role | null> {
    return this.roleRepository.findOneBy({ id });
  }

  async findRoleByName(name: string): Promise<Role | null> {
    return this.roleRepository.findOneBy({ name });
  }

  async updateRole(id: string, updateRoleDto: UpdateRoleDto): Promise<Role> {
    const role = await this.findRoleById(id);
    if (!role) {
      throw new NotFoundException(`Role with ID ${id} not found.`);
    }
    // Check if new name conflicts if it's being changed
    if (updateRoleDto.name && updateRoleDto.name !== role.name) {
      const existingRole = await this.roleRepository.findOne({ where: { name: updateRoleDto.name } });
      if (existingRole) {
        throw new BadRequestException(`Role with name '${updateRoleDto.name}' already exists.`);
      }
    }

    Object.assign(role, updateRoleDto);
    const updatedRole = await this.roleRepository.save(role);
    // Event: this.userEventPublisher.publishRoleUpdated(updatedRole);
    return updatedRole;
  }

  async deleteRole(id: string): Promise<void> {
    const role = await this.findRoleById(id);
    if (!role) {
      throw new NotFoundException(`Role with ID ${id} not found.`);
    }
    // Add logic to handle users with this role: disallow deletion, unassign, or set to a default role.
    // For example, check if any user has this role before deletion.
    // const usersWithRole = await this.userService.findUsersByRoleId(id); // Conceptual
    // if (usersWithRole.length > 0) {
    //   throw new BadRequestException(`Role ID ${id} is assigned to users and cannot be deleted.`);
    // }
    await this.roleRepository.remove(role);
    // Event: this.userEventPublisher.publishRoleDeleted({ roleId: id, roleName: role.name });
  }

  // --- User-Role Assignments ---

  async assignRolesToUser(userId: string, roleIds: string[]): Promise<User> {
    const user = await this.userService.findById(userId);
    if (!user) {
      throw new NotFoundException(`User with ID ${userId} not found.`);
    }

    const roles = await this.roleRepository.findBy({ id: In(roleIds) });
    if (roles.length !== roleIds.length) {
      throw new BadRequestException('One or more role IDs are invalid.');
    }

    // Assuming User entity has a `roles` ManyToMany relation
    // This might be `user.roles = [...user.roles, ...roles]` or a more sophisticated merge
    // For TypeORM, often you just assign the array of entities
    user.roles = roles; // Or merge with existing roles if that's the desired behavior
    const updatedUser = await this.userService.saveUser(user); // Assume UserService has a save method

    await this.userEventPublisher.publishUserRolesUpdated(updatedUser, roles);
    return updatedUser;
  }

  async removeRolesFromUser(userId: string, roleIds: string[]): Promise<User> {
    const user = await this.userService.findById(userId);
    if (!user) {
      throw new NotFoundException(`User with ID ${userId} not found.`);
    }
    if (!user.roles) {
        return user; // No roles to remove
    }

    user.roles = user.roles.filter(role => !roleIds.includes(role.id));
    const updatedUser = await this.userService.saveUser(user); // Assume UserService has a save method

    // Find the Role objects that were removed for event publishing if needed
    // await this.userEventPublisher.publishUserRolesUpdated(updatedUser, /* removed roles */);
    return updatedUser;
  }

  async getUserRoles(userId: string): Promise<Role[]> {
    const user = await this.userService.findById(userId);
    if (!user) {
      throw new NotFoundException(`User with ID ${userId} not found.`);
    }
    // Assuming `user.roles` is populated (e.g. via relations in findById or lazy loading)
    return user.roles || [];
  }

  async findUsersByRole(roleId: string): Promise<User[]> {
    const role = await this.findRoleById(roleId);
    if (!role) {
      throw new NotFoundException(`Role with ID ${roleId} not found.`);
    }
    // This requires a query on the User entity or join table
    // return this.userService.findUsersByCriteria({ roles: { id: roleId } }); // Conceptual
    // Example with TypeORM if User has a many-to-many with Role:
    const users = await this.userService.findUsersByQuery({
        where: { roles: { id: roleId } },
        relations: ['roles'] // Ensure roles are loaded if needed for further processing
    });
    return users;
  }
}
```

## 3. Interactions

*   **`UserService`**: `RoleService` collaborates with `UserService` to fetch user details and to update the roles assigned to a user. The `User` entity would typically have a relationship (e.g., ManyToMany) with the `Role` entity.
*   **`PermissionService` / `AuthorizationService`**: These services would consume role information from `RoleService` to determine a user's permissions. They might also manage the link between roles and specific permissions.
*   **Database**: Directly interacts with the `Role` table and potentially a join table for user-role assignments (e.g., `user_roles`) if not handled by ORM relations on the `User` entity directly.
*   **`UserEventPublisher`**: To publish events like `RoleCreated`, `RoleUpdated`, `RoleDeleted`, `UserRolesAssigned`.
*   **Administrative Interfaces**: Admin UIs would use `RoleService` to manage roles and their assignments to users.

## 4. Data Management & Integrity

*   **Role Name Uniqueness**: Role names should typically be unique within the system.
*   **Handling Role Deletion**: Define a clear strategy for what happens if a role is deleted:
    *   Disallow deletion if users are assigned to it.
    *   Automatically unassign users from the role.
    *   Assign users to a default or less privileged role.
*   **Referential Integrity**: Foreign key constraints should be in place for user-role assignments.

## 5. Security Considerations

*   **Privilege Escalation**: Carefully control who can create, modify, or assign roles. Only highly trusted administrators should have this capability.
*   **Least Privilege for Roles**: Define roles based on the principle of least privilege – grant only the permissions necessary for the functions associated with the role.
*   **Role Immutability (for core roles)**: Consider making certain system-critical roles (e.g., a super-admin role) non-deletable or their names non-modifiable through the standard service methods to prevent accidental lockout or system instability.
*   **Auditing**: Log all role creation, modification, deletion, and assignment/unassignment events for security auditing.

## 6. Future Enhancements

*   **Role Hierarchy**: Support for role inheritance (e.g., an `admin` role inherits all permissions of an `editor` role).
*   **Dynamic Roles/Attribute-Based Roles**: Roles that are assigned based on user attributes rather than explicit assignment (though this leans more towards Attribute-Based Access Control - ABAC).
*   **Scoped Roles**: Roles that are only valid within a specific context or organizational unit (e.g., `project_manager` for Project X).

`RoleService` is a fundamental building block for implementing RBAC, providing a structured way to group permissions and manage user access at a coarse-grained level.
