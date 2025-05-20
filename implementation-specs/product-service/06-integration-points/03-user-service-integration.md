# Product Service Integration with User Service (Potential)

## 1. Overview

This document outlines potential integration points between the **Product Service** and a **User Service**. The primary approach for such integrations should be **asynchronous and event-driven** to maintain loose coupling and resilience. Synchronous API calls should be exceptional and clearly justified.

Interactions might include:

- **Product Service needing User Information**: e.g., for personalization based on user preferences, or validating user roles/permissions for administrative actions (if not handled by a central API gateway or identity provider).
- **User Service needing Product Information**: e.g., for features like user wishlists, recently viewed products, or displaying product details within a user-centric context.

## 2. Asynchronous Integration Patterns (Preferred)

### 2.1. User Data for Product Service Needs

- **Scenario**: Product Service requires user preferences for personalization.
  - **Event-Driven Approach**: User Service publishes `UserPreferenceChanged` events (e.g., `preferredCategories`, `preferredBrands`). Product Service (or a dedicated Personalization Service) consumes these to build or update models/rules for personalizing product displays or search results.
- **Scenario**: Product Service needs to check user roles/permissions for an internal administrative action.
  - **Event-Driven Approach (Potentially)**: If roles change infrequently, User Service could publish `UserRoleUpdated` events. Product Service could consume these to maintain an internal cache of roles for users who interact with its admin functions. (More commonly, this is handled by API Gateway + IdP at request time).

### 2.2. Product Data for User Service Needs

- **Scenario**: User Service manages wishlists or recently viewed product lists.
  - **Event-Driven Approach**: User Service consumes `ProductCreated`, `ProductUpdated`, `ProductPriceChanged`, `ProductStatusChanged`, and `ProductDeleted` events from Product Service. This allows User Service to maintain its own eventually consistent local projection of relevant product details (name, image, current price, status) for products in users' lists.
  - For "recently viewed," a frontend or API gateway might publish a `ProductViewed(userId, productId)` event that User Service consumes.
- **Scenario**: User Service displays product recommendations.
  - **Event-Driven Approach**: A Recommendation Service (which could be part of User Service or separate) would consume product events and user interaction events to generate recommendations. These recommendations (list of product IDs) are then stored by User Service. User Service then uses its event-sourced local product cache to enrich these recommendations with details.

## 3. Exceptional Synchronous API Calls

Synchronous calls should only be considered if an event-driven approach is insufficient for a critical, real-time requirement. Adherence to [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md) (for the calling service) and [Exposing Product Service APIs](./08-exposing-product-service-apis.md) (for the called service) is mandatory.

### 3.1. Product Service Calls User Service (Hypothetical Examples)

- **Purpose**: Fetching immediate, authoritative user data not available via events or local cache.
- **Example Justification**: For a critical, real-time administrative action within Product Service, needing to verify the latest `isAdmin` status of a user _right now_ before proceeding, if this cannot be reliably determined from the auth token or an event-sourced cache due to extreme sensitivity or timing.
- **User Service Endpoint(s)**: e.g., `GET /users/{userId}/permissions`
- **Request/Response**: Specific to User Service API.

### 3.2. User Service Calls Product Service (Hypothetical Examples)

- **Purpose**: Fetching immediate, authoritative product data not suitable for User Service's local cache.
- **Example Justification**: When a user adds an item to a wishlist, User Service might synchronously call Product Service (`GET /products/variants/by-id/{variantId}`) to validate the `variantId` exists and is active _at that precise moment_ before accepting it into the wishlist, especially if the local product cache is known to have some replication lag and a stricter consistency is desired for this specific write operation.
- **Product Service Endpoint(s) Consumed**: e.g., `GET /products/variants/by-id/{variantId}`
- **Key Information Used**: Product `name`, `status`, current `price` (if displaying on wishlist action confirmation).

## 4. Considerations

- The necessity and nature of any integration (especially synchronous) will heavily depend on the specific feature set and how responsibilities are divided.
- Always evaluate if the required information can be obtained through event consumption and eventual consistency before opting for a synchronous API call.
- For functionalities like permissions/roles, these are often best handled by an API Gateway integrating with an Identity Provider, rather than direct service-to-service calls for this info.

## 5. References

- [Product Service OpenAPI Specification](../../openapi/product-service.yaml)
- [User Service OpenAPI Specification](../../../user-service/openapi/user-service.yaml) _(Assumed path)_
- [Product Service - Phase 5 Event Publishing](../../05-event-publishing/)
- [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md)
- [Exposing Product Service APIs](./08-exposing-product-service-apis.md)
