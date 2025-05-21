# Role Entity (`Role`)

## 1. Overview

The `Role` entity defines a named set of responsibilities or capabilities within the e-commerce platform. Users are assigned roles, and roles are, in turn, associated with specific permissions. This provides a manageable way to implement Role-Based Access Control (RBAC).

Examples of roles include `customer`, `administrator`, `support_agent`, `content_manager`, `fulfillment_specialist`.

## 2. Attributes

| Attribute   | Type                        | Constraints & Description                                                                                                                            |
| ----------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`        | UUID / String (Primary Key) | Universally unique identifier for the role. Auto-generated or a human-readable unique string (e.g., `admin`, `customer`).                                 |
| `name`      | String                      | Unique, human-readable name for the role (e.g., "Administrator", "Customer Account", "Product Manager"). Max length: 100. Required. Case-insensitive unique. |
| `description` | String (Nullable)           | A brief description of what the role entails or its purpose. Max length: 255.                                                                      |
| `isSystemRole`| Boolean                   | Flag indicating if this is a core system role that cannot be deleted or (easily) modified (e.g., `SUPER_ADMIN`). Defaults to `false`.                   |
| `createdAt` | DateTime                    | Timestamp when the role was created. Auto-generated.                                                                                                 |
| `updatedAt` | DateTime                    | Timestamp when the role was last updated. Auto-generated on update.                                                                                  |

## 3. Relationships

*   **User**: Many-to-Many. A `Role` can be assigned to many `User`s, and a `User` can have many `Role`s.
    *   This relationship is often managed by an array of role IDs/names on the `User` entity itself, or through a dedicated join table (`UserRoleLink`) if more attributes are needed for the assignment (e.g., assigned_by, assignment_date).
*   **Permission**: Many-to-Many. A `Role` can have many `Permission`s, and a `Permission` can belong to many `Role`s.
    *   This is typically implemented via a join table: `RolePermissionLink` (see `06-role-permission-link-entity.md`).

## 4. Indexes

*   **Primary Key**: `id`.
*   **Unique Index**: `name` (case-insensitive recommended).
*   **Index**: `isSystemRole`.

## 5. Security Considerations

*   **Privilege Escalation**: Care must be taken when defining roles and assigning permissions to prevent unintended privilege escalation paths.
*   **Role Immutability**: Critical system roles (e.g., a super administrator) might be marked as `isSystemRole` and have restrictions on their modification or deletion to protect system integrity.
*   **Auditing**: Changes to roles (creation, deletion, modification of assigned permissions) should be audited.

## 6. Data Validation Examples (Conceptual)

*   `name`: Required, must be unique. Should not contain overly special characters.
*   `description`: Max length check.

## 7. Notes

*   The choice of `id` type (UUID vs. human-readable unique string like `admin_role`) depends on preference. UUIDs are guaranteed unique globally. Human-readable IDs can be easier for developers/admins but require careful management of uniqueness and naming conventions.
*   Roles form the cornerstone of the RBAC system. Their granularity and definition should align with the actual operational and access control needs of the platform.
*   Consider if a hierarchy of roles is needed (e.g., a role inheriting permissions from another). This adds complexity and might involve an adjacency list (`parentRoleId` on the `Role` entity) or a nested set model if the hierarchy is deep and queries for inherited permissions are frequent.
*   The initial set of roles is often seeded into the database during application deployment.
