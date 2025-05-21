# User Entity (`User`)

## 1. Overview

The `User` entity is the central and most critical data entity managed by the User Service. It represents an individual who can interact with the e-commerce platform, whether as a customer, administrator, or another defined role. This entity primarily handles identification, authentication credentials, and core account status.

## 2. Attributes

| Attribute          | Type                        | Constraints & Description                                                                                                                               |
| ------------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`               | UUID / String (Primary Key) | Universally unique identifier for the user. Auto-generated.                                                                                             |
| `email`            | String                      | User's email address. Must be unique. Case-insensitive unique index recommended. Used for login and communication. Max length: 255. Format validation.  |
| `emailVerified`    | Boolean                     | Flag indicating if the user has verified their email address. Defaults to `false`.                                                                        |
| `emailVerificationToken` | String (Nullable)       | Token sent to the user for email verification. Should be unique, have an expiry, and be cleared after verification. Hashed in DB for security.         |
| `passwordHash`     | String                      | Securely hashed password using a strong algorithm (e.g., bcrypt, Argon2). Never store plaintext passwords.                                                |
| `passwordResetToken` | String (Nullable)       | Token sent to the user for password reset. Should be unique, have an expiry, and be cleared after use. Hashed in DB for security.                        |
| `passwordResetTokenExpiresAt` | DateTime (Nullable) | Expiration timestamp for the `passwordResetToken`.                                                                                                    |
| `status`           | Enum / String               | Account status. E.g., `PENDING_VERIFICATION`, `ACTIVE`, `SUSPENDED`, `DEACTIVATED`. Defaults to `PENDING_VERIFICATION` or `ACTIVE` based on signup flow. |
| `roles`            | Array of String / Relation  | List of role names or IDs assigned to the user (e.g., `["customer"]`, `["admin", "content_editor"]`). See `04-role-entity.md`. Link to Role entity. |
| `lastLoginAt`      | DateTime (Nullable)         | Timestamp of the user's last successful login.                                                                                                           |
| `failedLoginAttempts` | Integer (Nullable)        | Counter for consecutive failed login attempts. Used for account lockout logic. Defaults to 0.                                                          |
| `lockoutUntil`     | DateTime (Nullable)         | Timestamp until which the account is locked due to too many failed login attempts.                                                                      |
| `mfaEnabled`       | Boolean                     | Flag indicating if Multi-Factor Authentication is enabled for the user. Defaults to `false`.                                                            |
| `mfaSecret`        | String (Nullable, Encrypted)| Secret key for Time-based One-Time Password (TOTP) MFA. Must be encrypted at rest.                                                                      |
| `mfaBackupCodes`   | Array of String (Nullable, Encrypted/Hashed) | List of one-time backup codes for MFA recovery. Each code should be individually hashed or the array encrypted.                                |
| `createdAt`        | DateTime                    | Timestamp when the user account was created. Auto-generated.                                                                                              |
| `updatedAt`        | DateTime                    | Timestamp when the user account was last updated. Auto-generated on update.                                                                               |
| `deletedAt`        | DateTime (Nullable)         | For soft deletes. If set, the user is considered deleted but data is retained for a period or for audit purposes.                                       |

## 3. Relationships

*   **UserProfile**: One-to-One (A `User` has one `UserProfile`). The foreign key might reside in the `UserProfile` entity pointing back to `User.id`.
*   **Address**: One-to-Many (A `User` can have multiple `Address`es). Foreign key `userId` in the `Address` entity.
*   **Role**: Many-to-Many (A `User` can have multiple `Role`s). 
    *   This can be implemented as an array of role IDs/names directly on the `User` entity if the number of roles per user is small and roles are relatively static.
    *   Alternatively, a dedicated join table (`UserRoleLink`) would be used for more complex scenarios or if additional attributes are needed on the relationship.

## 4. Indexes

*   **Primary Key**: `id`.
*   **Unique Index**: `email` (case-insensitive if supported by DB, otherwise handle at application layer).
*   **Index**: `status` (for querying users by status).
*   **Index**: `emailVerificationToken` (if used for lookups, and after hashing).
*   **Index**: `passwordResetToken` (if used for lookups, and after hashing).
*   **Index**: `deletedAt` (for efficient querying of soft-deleted users).

## 5. Security and PII Considerations

*   **`email`**: Is PII. Handle with care, encrypt in transit and at rest if feasible/required.
*   **`passwordHash`**: Critical security field. Use a strong, salted, adaptive hashing algorithm (e.g., bcrypt with a work factor of 12+, or Argon2id). **Never log password hashes unless for specific, secured debugging of the hashing process itself (very rare).**
*   **`emailVerificationToken`, `passwordResetToken`**: These are sensitive tokens. While transient, they should be generated with sufficient randomness, have an expiry, and be invalidated after use. Consider hashing them in the database to protect against theft if the database is compromised (similar to password hashes, though simpler hashing might suffice if they are short-lived and single-use).
*   **`mfaSecret`**: Highly sensitive. Must be encrypted at rest using strong encryption (e.g., AES-256 GCM) with a carefully managed encryption key.
*   **`mfaBackupCodes`**: Sensitive. Each code should be individually hashed (so it can be compared upon use) or the entire array of codes encrypted.
*   **Soft Deletes (`deletedAt`)**: Useful for data recovery and audit trails. Implement a policy for eventual permanent deletion of soft-deleted PII data to comply with privacy regulations (e.g., GDPR Right to Erasure).

## 6. Data Validation Examples (Conceptual)

*   `email`: Must be a valid email format. Must be unique.
*   `password` (before hashing): Minimum length, complexity requirements (uppercase, lowercase, number, special character) enforced at the application layer during registration/password change.
*   `status`: Must be one of the predefined valid statuses.
*   `roles`: If an array of strings, each string must correspond to a valid, existing role name/ID.

## 7. Notes

*   The choice between embedding role identifiers directly in the `User` entity versus a separate join table depends on the complexity of the role system and database choice. For many common scenarios, an array of role names/IDs on the user entity is sufficient and simpler to query.
*   The exact implementation of token storage (verification, reset) might involve a separate table if more metadata per token is needed (e.g., multiple valid tokens, token type).
*   Consider separating authentication concerns (password, MFA) from core user identity if the domain becomes very complex, potentially into a related but distinct entity or service, though often they are co-located for user management simplicity.
