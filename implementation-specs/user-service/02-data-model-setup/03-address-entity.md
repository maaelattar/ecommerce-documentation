# Address Entity (`Address`)

## 1. Overview

The `Address` entity stores physical address information associated with a user. Users can typically have multiple addresses (e.g., for shipping, billing) and designate default addresses for different purposes. This entity is crucial for order fulfillment and other location-based functionalities.

## 2. Attributes

| Attribute        | Type                        | Constraints & Description                                                                                                                               |
| ---------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`             | UUID / String (Primary Key) | Universally unique identifier for the address. Auto-generated.                                                                                          |
| `userId`         | UUID / String (Foreign Key) | Foreign key referencing `User.id`. Links the address to a specific user.                                                                                |
| `addressLine1`   | String                      | First line of the street address (e.g., "123 Main St"). Max length: 255. Required.                                                                      |
| `addressLine2`   | String (Nullable)           | Second line of the street address (e.g., "Apt 4B", "Suite 100"). Max length: 255.                                                                      |
| `city`           | String                      | City or locality. Max length: 100. Required.                                                                                                            |
| `stateOrProvince`| String                      | State, province, or region. Max length: 100. Required for countries that use this (e.g., US, CA).                                                        |
| `postalCode`     | String                      | Postal code (e.g., ZIP code). Max length: 20. Required for countries that use this. Format validation based on country.                                  |
| `countryCode`    | String                      | Two-letter ISO 3166-1 alpha-2 country code (e.g., "US", "CA", "GB"). Required.                                                                          |
| `addressType`    | Enum / String (Nullable)    | Type of address (e.g., `SHIPPING`, `BILLING`, `HOME`, `WORK`). Users might have multiple addresses of the same type.                                        |
| `isDefaultShipping`| Boolean                   | Flag indicating if this is the user's default shipping address. A user should ideally have only one default shipping address. Defaults to `false`.       |
| `isDefaultBilling`| Boolean                    | Flag indicating if this is the user's default billing address. A user should ideally have only one default billing address. Defaults to `false`.         |
| `contactName`    | String (Nullable)           | Name of the person associated with this address (if different from the user's main name, e.g., for gifts). Max length: 200.                            |
| `contactPhone`   | String (Nullable)           | Phone number associated with this address (for delivery purposes). Max length: 30.                                                                        |
| `companyName`    | String (Nullable)           | Company name, if the address is a business address. Max length: 150.                                                                                    |
| `additionalNotes`| Text / String (Nullable)    | Any additional instructions or notes for delivery or related to the address. Max length: 500.                                                         |
| `createdAt`      | DateTime                    | Timestamp when the address was created. Auto-generated.                                                                                                 |
| `updatedAt`      | DateTime                    | Timestamp when the address was last updated. Auto-generated on update.                                                                                  |

## 3. Relationships

*   **User**: Many-to-One (An `Address` belongs to one `User`). The `userId` attribute serves as the foreign key.

## 4. Indexes

*   **Primary Key**: `id`.
*   **Index**: `userId` (for quickly retrieving all addresses for a user).
*   **Index (Optional)**: `userId`, `isDefaultShipping` (if frequently querying for default shipping address).
*   **Index (Optional)**: `userId`, `isDefaultBilling` (if frequently querying for default billing address).
*   **Index (Optional)**: `countryCode`, `postalCode` (if address lookups by these fields are common, though this is less typical for user-specific addresses).

## 5. Security and PII Considerations

*   **PII**: All address fields (`addressLine1`, `addressLine2`, `city`, `stateOrProvince`, `postalCode`, `countryCode`, `contactName`, `contactPhone`, `companyName`) are considered PII.
*   **Data Protection**: Handle with extreme care according to privacy regulations (GDPR, CCPA).
    *   Encrypt in transit (TLS/SSL).
    *   Consider encryption at rest for the entire table or specific sensitive fields.
*   **Access Control**: Only the owning user and authorized administrators (e.g., for order fulfillment support) should be able to view or modify addresses. Other services should access address information through well-defined APIs and only when necessary (e.g., Order Service needing a shipping address).
*   **Address Validation**: Consider integrating with an address validation service (external or internal) to verify and standardize addresses upon entry. This improves data quality and delivery accuracy but should be done carefully (see `../06-integration-points/05-external-enrichment-services.md` if external).

## 6. Data Validation Examples (Conceptual)

*   `addressLine1`, `city`, `stateOrProvince`, `countryCode`, `postalCode`: Required based on country rules.
*   `countryCode`: Must be a valid ISO 3166-1 alpha-2 code.
*   `postalCode`: Validate format based on `countryCode`.
*   `isDefaultShipping` / `isDefaultBilling`: Application logic should ensure that a user can only have one of each default type at a time (e.g., when setting one as default, unset others of the same type for that user).

## 7. Notes

*   The `addressType` can be useful for users to label their addresses. However, `isDefaultShipping` and `isDefaultBilling` are more direct flags for specific e-commerce functions.
*   The structure of address fields can vary significantly by country. While this model attempts a common representation, more complex internationalization might require a more flexible schema or integration with specialized address management libraries/services.
*   For order fulfillment, a snapshot of the chosen shipping/billing address is often taken and stored with the order to ensure that subsequent changes to the user's address book do not affect historical orders.
