# User Profile Entity (`UserProfile`)

## 1. Overview

The `UserProfile` entity stores extended, non-authentication-critical information about a user. This data typically includes personal details, contact information (other than primary email), and user preferences that enhance their experience on the platform but are not directly involved in the login or core account security processes.

Separating profile information from the core `User` entity can be beneficial for organizational clarity, performance (as profile data might be accessed less frequently than core user data for auth), and potentially for different access patterns or data lifecycle management.

## 2. Attributes

| Attribute         | Type                        | Constraints & Description                                                                                                                             |
| ----------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`              | UUID / String (Primary Key) | Universally unique identifier for the user profile. Auto-generated.                                                                                   |
| `userId`          | UUID / String (Foreign Key) | Foreign key referencing `User.id`. Establishes a One-to-One relationship. Must be unique to ensure one profile per user.                              |
| `firstName`       | String (Nullable)           | User's first name. Max length: 100.                                                                                                                   |
| `lastName`        | String (Nullable)           | User's last name. Max length: 100.                                                                                                                    |
| `displayName`     | String (Nullable)           | A publicly visible display name or nickname. Max length: 100. Could default to `firstName` + `lastName` or email if not set.                          |
| `phoneNumber`     | String (Nullable)           | User's phone number. Format validation (e.g., E.164). Max length: 30.                                                                                 |
| `phoneVerified`   | Boolean                     | Flag indicating if the user has verified their phone number. Defaults to `false`.                                                                     |
| `dateOfBirth`     | Date (Nullable)             | User's date of birth. For age verification or personalization.                                                                                       |
| `gender`          | Enum / String (Nullable)    | User's gender (e.g., `MALE`, `FEMALE`, `NON_BINARY`, `PREFER_NOT_TO_SAY`).                                                                              |
| `profilePictureUrl`| String (Nullable)           | URL to the user's profile picture. Max length: 2048 (URL length).                                                                                     |
| `bio`             | Text / String (Nullable)    | A short biography or description provided by the user. Max length: 500.                                                                               |
| `languagePreference` | String (Nullable)        | User's preferred language for the platform (e.g., `en-US`, `fr-FR`). Defaults to platform default.                                                     |
| `timezonePreference` | String (Nullable)        | User's preferred timezone (e.g., `America/New_York`, `Europe/London`). Defaults to platform default or auto-detected.                                    |
| `communicationPreferences` | JSON / Object (Nullable) | User's preferences for receiving communications (e.g., newsletters, promotional emails, push notifications). Example: `{"newsletterOptIn": true}`. |
| `createdAt`       | DateTime                    | Timestamp when the user profile was created. Auto-generated (often same as user creation).                                                              |
| `updatedAt`       | DateTime                    | Timestamp when the user profile was last updated. Auto-generated on update.                                                                             |

## 3. Relationships

*   **User**: One-to-One (A `UserProfile` belongs to one `User`). This is typically enforced by `userId` being both a foreign key and unique.

## 4. Indexes

*   **Primary Key**: `id`.
*   **Unique Index**: `userId` (to enforce the one-to-one relationship).
*   **Index (Optional)**: `displayName` (if frequently searched by).
*   **Index (Optional)**: `phoneNumber` (if used for lookups, after normalization/sanitization).

## 5. Security and PII Considerations

*   **PII**: Almost all fields in `UserProfile` can be considered PII (`firstName`, `lastName`, `displayName`, `phoneNumber`, `dateOfBirth`, `gender`, `profilePictureUrl`, potentially `bio` and preferences).
*   **Data Protection**: This data must be handled with strict adherence to privacy regulations (GDPR, CCPA, etc.).
    *   Encrypt in transit (TLS/SSL).
    *   Consider encryption at rest for the entire table or specific sensitive fields.
*   **Access Control**: Ensure that only the user themselves or authorized administrators can modify profile data. Other services should only have read access to necessary fields based on clear use cases and authorization.
*   **Profile Picture**: If hosting profile pictures, consider security implications (e.g., content moderation if publicly visible, secure storage).
*   **Preferences**: Communication preferences must be honored to comply with anti-spam laws and user consent.

## 6. Data Validation Examples (Conceptual)

*   `firstName`, `lastName`: Should not contain special characters beyond those typical for names. Max length checks.
*   `phoneNumber`: Validate against E.164 or other chosen phone number formats.
*   `dateOfBirth`: Ensure it's a valid date and potentially within a reasonable range (e.g., not in the future, not more than 120 years ago).
*   `languagePreference`: Must be a valid IETF language tag.
*   `timezonePreference`: Must be a valid IANA timezone identifier.

## 7. Notes

*   The level of detail in a user profile can vary greatly. Start with essential fields and add more as specific features require them.
*   Some preferences (e.g., `communicationPreferences`) are modeled as JSON/Object for flexibility. If these preferences become very complex or have their own lifecycle, they might be broken out into separate related entities.
*   The `UserProfile` is often created automatically when a `User` account is created, possibly with some fields populated from registration data or left null to be filled in later by the user.
