# 03 - User Profile Events

This document details the domain events published by the User Service related to user profile modifications, including changes to personal details, preferences, and addresses.

Events adhere to the common event envelope (`StandardMessage<T>`) defined in `01-event-publishing-mechanism.md` and provided by the `@ecommerce-platform/rabbitmq-event-utils` library.
For routing, events will be published to a designated exchange (e.g., `user.events`) with a routing key reflecting the event type (e.g., `user.profile.updated.v1`). The `userId` (associated with the profile or address) will be included in the event payload and can also be populated in the `partitionKey` field of the `StandardMessage<T>` envelope if specific consumers require it for ordering or sharding.

## 1. `UserProfileUpdatedEventV1`

*   **Description**: Published when a user's profile information (e.g., name, bio, contact details other than primary email, preferences, profile picture) is updated.
*   **`eventType`**: `UserProfileUpdatedEventV1`
*   **Trigger**: After `UserProfileService.updateProfileByUserId()` or `upsertProfileForUser()` successfully modifies profile data.
*   **Payload Fields**:
    *   `userId` (string, UUID): The identifier of the user whose profile was updated.
    *   `profileId` (string, UUID): The identifier of the `UserProfile` entity.
    *   `updatedFields` (array of strings or object): Specifies which profile fields were updated. Can list keys of changed fields, or include old/new values for specific critical fields if necessary (balance verbosity with utility).
        *   Example (keys only): `["bio", "phoneNumber", "preferences.theme"]`
        *   Example (with values): `{"bio": {"old": "Old bio", "new": "New bio"}, "phoneNumber": "+15551234567"}` (Use with caution for PII)
    *   `updateTimestamp` (string, ISO 8601): Timestamp of the profile update.
*   **Example Payload (keys only)**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "profileId": "p1q2r3s4-t5u6-7890-1234-567890uvwxyz",
      "updatedFields": ["firstName", "lastName", "bio", "preferences.theme"],
      "updateTimestamp": "2023-10-29T15:30:00.000Z"
    }
    ```
*   **Potential Consumers**: Search Service (if profile data is indexed), Personalization Service, Notification Service (e.g., if a significant profile change warrants a notification), Customer Support Systems.

## 2. `UserAddressAddedEventV1`

*   **Description**: Published when a new address is successfully added to a user's profile.
*   **`eventType`**: `UserAddressAddedEventV1`
*   **Trigger**: After `UserProfileService.addAddress()`.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `profileId` (string, UUID): The profile to which the address was added.
    *   `addressId` (string, UUID): The unique identifier for the newly added address.
    *   `addressType` (string, enum): Type of address (e.g., `shipping`, `billing`).
    *   `isDefaultShipping` (boolean): Whether this address was set as the default shipping address.
    *   `isDefaultBilling` (boolean): Whether this address was set as the default billing address.
    *   `country` (string): Country of the address (useful for segmentation/analytics).
    *   `addTimestamp` (string, ISO 8601): Timestamp of when the address was added.
    *   `fullAddress` (object, optional but recommended): The complete address details. Avoids immediate callback if consumers need the address.
        ```json
        "fullAddress": {
            "streetLine1": "123 New Rd",
            "city": "Newville",
            "postalCode": "54321",
            "country": "US"
            // ... other address fields
        }
        ```
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "profileId": "p1q2r3s4-t5u6-7890-1234-567890uvwxyz",
      "addressId": "addr-uuid-789",
      "addressType": "shipping",
      "isDefaultShipping": true,
      "isDefaultBilling": false,
      "country": "US",
      "addTimestamp": "2023-10-29T16:00:00.000Z",
      "fullAddress": {
          "streetLine1": "123 New Rd",
          "city": "Newville",
          "postalCode": "54321",
          "country": "US"
      }
    }
    ```
*   **Potential Consumers**: Order Service, Shipping Service, Notification Service (address confirmation), Fraud Detection Service, Analytics.

## 3. `UserAddressUpdatedEventV1`

*   **Description**: Published when an existing address in a user's profile is successfully updated.
*   **`eventType`**: `UserAddressUpdatedEventV1`
*   **Trigger**: After `UserProfileService.updateAddress()`.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `profileId` (string, UUID): The profile to which the address belongs.
    *   `addressId` (string, UUID): The identifier of the updated address.
    *   `updatedFields` (array of strings or object): Specifies which address fields were updated (similar to `UserProfileUpdatedEventV1`).
    *   `updateTimestamp` (string, ISO 8601): Timestamp of the address update.
    *   `fullAddress` (object, optional but recommended): The complete updated address details.
*   **Example Payload (showing updated fields and full address)**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "profileId": "p1q2r3s4-t5u6-7890-1234-567890uvwxyz",
      "addressId": "addr-uuid-789",
      "updatedFields": ["streetLine1", "city"],
      "updateTimestamp": "2023-10-29T16:30:00.000Z",
      "fullAddress": {
          "streetLine1": "123 Updated Rd",
          "city": "Updatedville",
          "postalCode": "54321", // Assuming postal code didn't change
          "country": "US"
          // ... other address fields
      }
    }
    ```
*   **Potential Consumers**: Order Service (if affects open orders), Shipping Service, Notification Service, Fraud Detection Service.

## 4. `UserAddressDeletedEventV1`

*   **Description**: Published when an address is successfully deleted from a user's profile.
*   **`eventType`**: `UserAddressDeletedEventV1`
*   **Trigger**: After `UserProfileService.deleteAddress()`.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `profileId` (string, UUID): The profile from which the address was deleted.
    *   `addressId` (string, UUID): The identifier of the deleted address.
    *   `deleteTimestamp` (string, ISO 8601): Timestamp of the address deletion.
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "profileId": "p1q2r3s4-t5u6-7890-1234-567890uvwxyz",
      "addressId": "addr-uuid-789",
      "deleteTimestamp": "2023-10-29T17:00:00.000Z"
    }
    ```
*   **Potential Consumers**: Order Service, Shipping Service, any service that might have referenced the deleted address.

## 5. `UserProfileDefaultAddressChangedEventV1`

*   **Description**: Published when a user's default shipping or billing address is changed.
*   **`eventType`**: `UserProfileDefaultAddressChangedEventV1`
*   **Trigger**: After `UserProfileService.setDefaultAddress()`.
*   **Payload Fields**:
    *   `userId` (string, UUID): The user's identifier.
    *   `profileId` (string, UUID): The user's profile identifier.
    *   `defaultShippingAddressId` (string, UUID, nullable): The new default shipping address ID.
    *   `defaultBillingAddressId` (string, UUID, nullable): The new default billing address ID.
    *   `changeTimestamp` (string, ISO 8601): Timestamp of the change.
*   **Example Payload**:
    ```json
    {
      "userId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "profileId": "p1q2r3s4-t5u6-7890-1234-567890uvwxyz",
      "defaultShippingAddressId": "addr-uuid-new-default",
      "defaultBillingAddressId": "addr-uuid-billing-default",
      "changeTimestamp": "2023-10-29T17:30:00.000Z"
    }
    ```
*   **Potential Consumers**: Order Service (for pre-filling orders), Checkout UI, Notification Service.

These events allow other parts of the e-commerce system to stay synchronized with the user's profile and address information, facilitating accurate order processing, shipping, and personalized experiences.
