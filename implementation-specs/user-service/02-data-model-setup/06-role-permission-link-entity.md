# Role-Permission Link Entity (`RolePermissionLink`)

## 1. Overview

The `RolePermissionLink` entity (also known as a join table or associative entity) serves to establish the many-to-many relationship between `Role`s and `Permission`s. Each record in this table signifies that a specific permission is granted to a particular role.

## 2. Attributes

| Attribute      | Type                        | Constraints & Description                                                                                                  |
| -------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `id`           | UUID / String (Primary Key) | Universally unique identifier for the link itself (optional, a composite primary key on `roleId` and `permissionId` is common). |
| `roleId`       | UUID / String (Foreign Key) | Foreign key referencing `Role.id`. Part of a composite primary key. Required.                                               |
| `permissionId` | UUID / String (Foreign Key) | Foreign key referencing `Permission.id`. Part of a composite primary key. Required.                                         |
| `createdAt`    | DateTime                    | Timestamp when the permission was granted to the role. Auto-generated.                                                    |
| `assignedBy`   | UUID / String (Nullable)    | Optional: Identifier of the user or system process that assigned this permission to the role (for auditing).                 |

## 3. Relationships

*   **Role**: Many-to-One. Each `RolePermissionLink` record belongs to one `Role`.
*   **Permission**: Many-to-One. Each `RolePermissionLink` record grants one `Permission`.

Effectively, this table models the `Role` *has* `Permission` relationship.

## 4. Indexes

*   **Primary Key**: Typically a composite primary key on (`roleId`, `permissionId`) to ensure a permission is assigned to a role only once.
    *   If a separate `id` is used as PK, then a unique composite index on (`roleId`, `permissionId`) is essential.
*   **Index**: `permissionId` (to quickly find all roles that have a specific permission, if needed, though querying by `roleId` is more common for checking a role's permissions).

## 5. Security Considerations

*   **Integrity**: The integrity of this table is crucial for the correctness of the RBAC system. Foreign key constraints should be strictly enforced to prevent orphaned links.
*   **Auditing**: While `assignedBy` and `createdAt` provide some auditability, more comprehensive auditing of changes to role-permission assignments (who granted/revoked what, when) should be implemented at the application/service layer that modifies this table.

## 6. Data Validation Examples (Conceptual)

*   `roleId`: Must refer to an existing `Role`.
*   `permissionId`: Must refer to an existing `Permission`.
*   The combination of `roleId` and `permissionId` must be unique.

## 7. Notes

*   This entity is purely structural to resolve the many-to-many relationship. It usually doesn't have much business logic directly associated with it, other than creation and deletion of links.
*   When checking a user's permissions, the application would typically:
    1.  Get the user's roles.
    2.  For each role, retrieve all associated permission IDs/names from this `RolePermissionLink` table.
    3.  Aggregate the unique set of permissions.
*   For performance, the set of permissions for a role is often cached or included in a JWT if the number of permissions is manageable.
*   The actual management (granting/revoking permissions from roles) is an administrative function handled via specific APIs in the User Service.
