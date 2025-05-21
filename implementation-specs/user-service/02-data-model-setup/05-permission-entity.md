# Permission Entity (`Permission`)

## 1. Overview

The `Permission` entity represents a granular authorization to perform a specific action or access a particular resource within the e-commerce platform. Permissions are assigned to Roles, and Users inherit permissions through their assigned Roles. This allows for fine-grained control over system access.

Examples of permissions: `view_product_catalog`, `edit_product`, `create_order`, `cancel_order`, `manage_users`, `view_admin_dashboard`, `publish_content`.

## 2. Attributes

| Attribute   | Type                        | Constraints & Description                                                                                                                                 |
| ----------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`        | UUID / String (Primary Key) | Universally unique identifier for the permission. Auto-generated or a unique, descriptive string (e.g., `product:edit`, `order:view_all`).                 |
| `action`    | String                      | The action being permitted (e.g., `create`, `read`, `update`, `delete`, `list`, `publish`, `impersonate`). Required. Combined with `resource` for uniqueness. |
| `resource`  | String                      | The resource or domain to which the action applies (e.g., `product`, `order`, `user`, `settings`, `all`). Required. Combined with `action` for uniqueness. |
| `description`| String (Nullable)           | A brief description of what the permission allows. Max length: 255.                                                                                     |
| `isSystemPermission` | Boolean              | Flag indicating if this is a core system permission that should not be easily deleted or modified. Defaults to `false`.                                  |
| `groupName` | String (Nullable)           | Optional grouping name for UI display or organization (e.g., "Product Management", "Order Fulfillment"). Max length: 100.                              |
| `createdAt` | DateTime                    | Timestamp when the permission was created. Auto-generated.                                                                                                |
| `updatedAt` | DateTime                    | Timestamp when the permission was last updated. Auto-generated on update.                                                                                 |

## 3. Relationships

*   **Role**: Many-to-Many. A `Permission` can be granted to many `Role`s, and a `Role` can have many `Permission`s.
    *   This relationship is implemented via a join table: `RolePermissionLink` (see `06-role-permission-link-entity.md`).

## 4. Indexes

*   **Primary Key**: `id`.
*   **Unique Composite Index**: `action`, `resource` (to ensure a permission like "edit product" is defined only once).
*   **Index**: `groupName` (if used for filtering/display).
*   **Index**: `isSystemPermission`.

## 5. Security Considerations

*   **Granularity**: Permissions should be as granular as reasonably possible to enforce the Principle of Least Privilege. Overly broad permissions can create security risks.
*   **Naming Convention**: A consistent naming convention for `action` and `resource` (e.g., `resource:action` or `verb_noun`) is highly recommended for clarity and manageability.
    *   Example: `product:create`, `product:edit`, `product:view_details`, `user:manage_roles`.
*   **Auditing**: Changes to permission definitions or their assignments to roles should be audited.
*   **Avoid Hardcoding Permissions**: Application code should ideally check for permissions by querying the User Service or by inspecting claims in a JWT, rather than hardcoding permission checks based on role names directly (though roles are often used for coarse-grained checks).

## 6. Data Validation Examples (Conceptual)

*   `action`: Required. Might be constrained to a predefined list of common actions.
*   `resource`: Required. Might be constrained to a predefined list of known system resources/domains.
*   The combination of `action` and `resource` must be unique.

## 7. Notes

*   The `id` can be a UUID or a descriptive string combining action and resource (e.g., `product:edit`). A descriptive string ID can be more readable and easier to reference in code or configuration if carefully managed for uniqueness and stability.
*   The initial set of permissions is often seeded into the database during application deployment, corresponding to the functionalities offered by different microservices.
*   Permissions define *what* can be done. Roles define *who* (as a group) can do it. Users are assigned to roles.
*   Wildcard permissions (e.g., `product:*` or `*:admin`) can be powerful but should be used with extreme caution as they grant broad access.
