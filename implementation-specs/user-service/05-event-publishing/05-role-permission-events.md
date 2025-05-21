# 05 - Role & Permission Events (Admin Context)

This document details domain events published by the User Service related to the management of roles and permissions. These events are typically triggered by administrative actions and are important for auditing security configuration changes and potentially for other services that need to react to authorization model updates.

Events adhere to the common event envelope (`StandardMessage<T>`) defined in `01-event-publishing-mechanism.md` and provided by the `@ecommerce-platform/rabbitmq-event-utils` library.
For routing, events will be published to a designated exchange (e.g., `auth.events` or `iam.events`) with a routing key reflecting the event type (e.g., `iam.role.created.v1`, `iam.user.role.assigned.v1`). Relevant identifiers like `roleId`, `permissionId`, or `userId` will be included in the event payload and can also be populated in the `partitionKey` field of the `StandardMessage<T>` envelope if specific consumers require it for ordering or sharding.

## Role Events

### 1. `RoleCreatedEventV1`

*   **Description**: Published when a new role is successfully created by an administrator.
*   **`eventType`**: `RoleCreatedEventV1`
*   **Trigger**: After `RoleService.createRole()`.
*   **Payload Fields**:
    *   `roleId` (string, UUID): The unique identifier for the new role.
    *   `roleName` (string): The name of the role (e.g., `editor`, `support_agent`).
    *   `description` (string, optional): Description of the role.
    *   `createdBy` (string, UUID): Identifier of the administrator who created the role.
    *   `creationTimestamp` (string, ISO 8601): Timestamp of role creation.
    *   `initialPermissionIds` (array of string, UUIDs, optional): IDs of permissions assigned at creation.
*   **Example Payload**:
    ```json
    {
      "roleId": "role-uuid-new-editor",
      "roleName": "new_editor_role",
      "description": "Manages blog content.",
      "createdBy": "admin-user-id-001",
      "creationTimestamp": "2023-10-30T14:00:00.000Z",
      "initialPermissionIds": ["perm-uuid-blog-write", "perm-uuid-blog-publish"]
    }
    ```
*   **Potential Consumers**: Audit Log Service, Authorization Service (if it caches role/permission data and needs to update), other systems managing access control configurations.

### 2. `RoleUpdatedEventV1`

*   **Description**: Published when an existing role's details (e.g., name, description) are updated.
*   **`eventType`**: `RoleUpdatedEventV1`
*   **Trigger**: After `RoleService.updateRole()`.
*   **Payload Fields**:
    *   `roleId` (string, UUID): The identifier of the updated role.
    *   `updatedFields` (array of strings or object): Specifies which role fields were updated (e.g., `["description", "name"]`).
    *   `oldValues` (object, optional): Previous values of updated fields for auditing.
    *   `newValues` (object): New values of updated fields.
    *   `updatedBy` (string, UUID): Identifier of the administrator who updated the role.
    *   `updateTimestamp` (string, ISO 8601): Timestamp of the update.
*   **Example Payload**:
    ```json
    {
      "roleId": "role-uuid-new-editor",
      "updatedFields": ["description"],
      "oldValues": { "description": "Manages blog content." },
      "newValues": { "description": "Manages all website blog content and related media." },
      "updatedBy": "admin-user-id-002",
      "updateTimestamp": "2023-10-30T14:30:00.000Z"
    }
    ```
*   **Potential Consumers**: Audit Log Service, Authorization Service cache.

### 3. `RoleDeletedEventV1`

*   **Description**: Published when a role is successfully deleted.
*   **`eventType`**: `RoleDeletedEventV1`
*   **Trigger**: After `RoleService.deleteRole()`.
*   **Payload Fields**:
    *   `roleId` (string, UUID): The identifier of the deleted role.
    *   `roleName` (string): The name of the deleted role.
    *   `deletedBy` (string, UUID): Identifier of the administrator who deleted the role.
    *   `deletionTimestamp` (string, ISO 8601): Timestamp of deletion.
*   **Example Payload**:
    ```json
    {
      "roleId": "role-uuid-old-role",
      "roleName": "obsolete_viewer",
      "deletedBy": "admin-user-id-001",
      "deletionTimestamp": "2023-10-30T15:00:00.000Z"
    }
    ```
*   **Potential Consumers**: Audit Log Service, Authorization Service cache, systems that might need to handle users who previously had this role.

### 4. `UserRoleAssignedEventV1`

*   **Description**: Published when a role is assigned to a user.
*   **`eventType`**: `UserRoleAssignedEventV1`
*   **Trigger**: After `RoleService.assignRolesToUser()` (or similar method in `UserService`).
*   **Payload Fields**:
    *   `userId` (string, UUID): The user to whom the role was assigned.
    *   `roleId` (string, UUID): The role that was assigned.
    *   `roleName` (string): The name of the assigned role.
    *   `assignedBy` (string, UUID): Identifier of the administrator who assigned the role.
    *   `assignmentTimestamp` (string, ISO 8601): Timestamp of assignment.
*   **Example Payload**:
    ```json
    {
      "userId": "user-uuid-abc",
      "roleId": "role-uuid-new-editor",
      "roleName": "new_editor_role",
      "assignedBy": "admin-user-id-001",
      "assignmentTimestamp": "2023-10-30T15:30:00.000Z"
    }
    ```
*   **Potential Consumers**: Audit Log Service, Authorization Service (to update user's effective permissions), Notification Service (optional, to inform user or admin).

### 5. `UserRoleRemovedEventV1`

*   **Description**: Published when a role is removed from a user.
*   **`eventType`**: `UserRoleRemovedEventV1`
*   **Trigger**: After `RoleService.removeRolesFromUser()` (or similar).
*   **Payload Fields**:
    *   `userId` (string, UUID): The user from whom the role was removed.
    *   `roleId` (string, UUID): The role that was removed.
    *   `roleName` (string): The name of the removed role.
    *   `removedBy` (string, UUID): Identifier of the administrator who removed the role.
    *   `removalTimestamp` (string, ISO 8601): Timestamp of removal.
*   **Example Payload**:
    ```json
    {
      "userId": "user-uuid-abc",
      "roleId": "role-uuid-old-role",
      "roleName": "obsolete_viewer",
      "removedBy": "admin-user-id-001",
      "removalTimestamp": "2023-10-30T16:00:00.000Z"
    }
    ```
*   **Potential Consumers**: Audit Log Service, Authorization Service.

## Permission Events

### 6. `PermissionCreatedEventV1`

*   **Description**: Published when a new permission is defined in the system.
*   **`eventType`**: `PermissionCreatedEventV1`
*   **Trigger**: After `PermissionService.createPermission()`.
*   **Payload Fields**:
    *   `permissionId` (string, UUID): The unique identifier for the new permission.
    *   `permissionName` (string): The name of the permission (e.g., `product:edit_all`).
    *   `action` (string, optional): The action part of the permission.
    *   `subject` (string, optional): The subject/resource part of the permission.
    *   `description` (string, optional): Description of the permission.
    *   `createdBy` (string, UUID): Identifier of the administrator who created it.
    *   `creationTimestamp` (string, ISO 8601).
*   **Example Payload**:
    ```json
    {
      "permissionId": "perm-uuid-product-delete",
      "permissionName": "product:delete_any",
      "action": "delete_any",
      "subject": "product",
      "description": "Allows deleting any product.",
      "createdBy": "admin-user-id-001",
      "creationTimestamp": "2023-10-30T16:30:00.000Z"
    }
    ```
*   **Potential Consumers**: Audit Log Service, Authorization Service cache.

### 7. `PermissionUpdatedEventV1` (Less Common)

*   **Description**: Published if a permission's definition (e.g., description, conditions) is updated. Names are usually immutable.
*   **`eventType`**: `PermissionUpdatedEventV1`
*   **Payload Fields**: Similar to `RoleUpdatedEventV1` (ID, updated fields, old/new values, updatedBy, timestamp).
*   **Potential Consumers**: Audit Log Service, Authorization Service cache.

### 8. `PermissionDeletedEventV1`

*   **Description**: Published when a permission is deleted from the system.
*   **`eventType`**: `PermissionDeletedEventV1`
*   **Trigger**: After `PermissionService.deletePermission()`.
*   **Payload Fields**:
    *   `permissionId` (string, UUID): Identifier of the deleted permission.
    *   `permissionName` (string): Name of the deleted permission.
    *   `deletedBy` (string, UUID): Administrator who deleted it.
    *   `deletionTimestamp` (string, ISO 8601).
*   **Potential Consumers**: Audit Log Service, Authorization Service cache.

### 9. `PermissionAssignedToRoleEventV1`

*   **Description**: Published when a permission is granted to a role.
*   **`eventType`**: `PermissionAssignedToRoleEventV1`
*   **Trigger**: After `PermissionService.assignPermissionsToRole()`.
*   **Payload Fields**:
    *   `roleId` (string, UUID): The role that received the permission.
    *   `permissionId` (string, UUID): The permission that was granted.
    *   `permissionName` (string): Name of the granted permission.
    *   `assignedBy` (string, UUID): Administrator who made the assignment.
    *   `assignmentTimestamp` (string, ISO 8601).
*   **Potential Consumers**: Audit Log Service, Authorization Service cache.

### 10. `PermissionRemovedFromRoleEventV1`

*   **Description**: Published when a permission is revoked from a role.
*   **`eventType`**: `PermissionRemovedFromRoleEventV1`
*   **Trigger**: After `PermissionService.removePermissionsFromRole()`.
*   **Payload Fields**:
    *   `roleId` (string, UUID): The role from which the permission was revoked.
    *   `permissionId` (string, UUID): The permission that was revoked.
    *   `permissionName` (string): Name of the revoked permission.
    *   `removedBy` (string, UUID): Administrator who made the change.
    *   `removalTimestamp` (string, ISO 8601).
*   **Potential Consumers**: Audit Log Service, Authorization Service cache.

These events ensure that changes to the authorization model are auditable and can be propagated to relevant systems.
