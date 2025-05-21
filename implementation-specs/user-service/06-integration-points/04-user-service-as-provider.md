# 04 - User Service as a Provider (Service-to-Service API Calls)

This document describes scenarios where other internal microservices directly call APIs exposed by the User Service. While event-driven communication is preferred for decoupling, direct API calls are sometimes necessary for synchronous request/response interactions where immediate user data or identity verification is required.

## 1. Guiding Principles for Exposure

*   **Well-Defined APIs**: The User Service must expose clear, well-documented, and versioned APIs for internal consumption (these are often the same APIs consumed by gateways/clients, but usage patterns might differ).
*   **Security**: All API endpoints must be secured, requiring authentication (e.g., service-to-service JWT, mTLS) and authorization (e.g., specific permissions for calling services) even for internal callers.
*   **Performance & Scalability**: Endpoints intended for high-volume internal calls must be optimized for performance and scalability.
*   **Necessity**: Direct API calls should be reserved for cases where:
    *   Data is needed synchronously and cannot be reasonably obtained via events (e.g., fetching the latest profile details before processing an order if not already available).
    *   An immediate validation or check related to a user is required (e.g., verifying user status before allowing a critical action in another service, though this can often be in JWT claims).

## 2. Potential Scenarios & Consumers

### a. Order Service / Checkout Service

*   **Scenario**: Before finalizing an order, the Order Service might need to fetch the most current shipping/billing address for a user if the address provided in the order request is just an ID or if re-validation is needed.
*   **API Call Example**:
    *   Order Service -> User Service
    *   `GET /users/{userId}/profile` or `GET /users/{userId}/addresses/{addressId}`
*   **Considerations**: This can be mitigated if the frontend provides full address details during checkout, which are then validated and stored with the order. However, fetching the *default* address might still be a use case.

### b. Customer Support Service / Admin Portal Backend

*   **Scenario**: A customer support tool or admin portal backend needs to retrieve detailed user information, including profile, addresses, account status, roles, and potentially login history (if exposed via API) to assist a user or manage their account.
*   **API Call Example**:
    *   Support Service -> User Service
    *   `GET /admin/users/{userId}`
    *   `GET /admin/users/{userId}/profile`
    *   `GET /admin/users/{userId}/roles`
*   **Considerations**: These are typically lower-volume, admin-privileged calls.

### c. Review or Content Service

*   **Scenario**: When displaying a product review or user-generated content, the Review Service might fetch basic user details (e.g., username, profile picture URL) to display alongside the content if these details are not denormalized or pushed via events.
*   **API Call Example**:
    *   Review Service -> User Service
    *   `GET /users/{userId}/public-profile` (an endpoint exposing only minimal, public-safe profile data).
*   **Considerations**: Caching this data in the Review Service or denormalizing it is often preferred for performance.

### d. Any Service Requiring User Validation (If not in JWT)

*   **Scenario**: A service needs to check if a `userId` it has received (e.g., from a request or another event) corresponds to a valid, active user before proceeding with an operation.
*   **API Call Example**:
    *   Other Service -> User Service
    *   `GET /users/{userId}/status` or a lightweight `GET /users/{userId}/validate` endpoint.
*   **Considerations**: Often, basic user status (`active`, `suspended`) can be included in JWT claims to avoid this call. This type of call should be very lightweight.

## 3. API Design for Internal Consumers

*   **Granularity**: Offer both coarse-grained endpoints (e.g., get full user details) and fine-grained ones (e.g., get only user status, get only specific address) to allow consumers to fetch only what they need.
*   **Batch Endpoints (Optional)**: For use cases where a service needs to fetch data for multiple users at once (e.g., enriching a list of user IDs with their names), consider providing batch API endpoints (e.g., `POST /users/details-batch` with a list of `userIds` in the body) to reduce chatty N+1 calls.
*   **Clear Error Codes**: Use standard HTTP status codes to indicate success, failure, and authorization issues.

## 4. Authentication & Authorization for Internal Callers

*   **Service Accounts / Client Credentials**: Internal services calling the User Service should authenticate using a non-user identity, typically via the OAuth 2.0 client credentials flow.
    *   Each calling service would have its own `client_id` and `client_secret` (or use mTLS with a service certificate).
    *   The User Service issues an access token to the calling service, which may contain specific scopes or permissions granted to that service.
*   **Permissions/Scopes**: The User Service APIs should be protected by permissions that can be assigned to these service accounts/clients.
    *   Example: Order Service might have `user_profile:read_own_addr` scope, while Admin Service has `user:read_all`.
*   **Network Policies**: In containerized environments like Kubernetes, network policies can restrict which services are allowed to even initiate connections to the User Service pods on specific ports.

## 5. Resilience and Performance

*   **Caching (Client-Side)**: Services that frequently call the User Service for relatively static data (e.g., user names, profile picture URLs) should implement caching on their side to reduce load and latency.
*   **User Service Caching**: The User Service itself may cache frequently accessed user data to speed up responses.
*   **Rate Limiting**: Even for internal service-to-service calls, consider applying fair-use rate limits to prevent any single misbehaving or compromised service from overwhelming the User Service.
*   **Timeouts and Retries (Client-Side)**: Consuming services must implement proper timeouts and retry mechanisms (with backoff) when calling User Service APIs.

## 6. Avoiding Excessive Coupling

While direct API calls are sometimes necessary, over-reliance on them can lead to tight coupling and a distributed monolith. Key strategies to mitigate this:

*   **Prioritize Events**: If data can be eventually consistent, use events.
*   **Embed Data in JWTs**: Include frequently needed, relatively stable user data (like roles, basic status) in JWT claims.
*   **Gateway Aggregation**: An API Gateway can sometimes aggregate data from the User Service and other services, providing a unified response to the original client, reducing the need for direct service-to-service calls from deeper in the call chain.

By providing secure, performant, and well-defined APIs, the User Service can effectively serve synchronous data needs of other internal microservices while encouraging event-driven patterns for most inter-service communication.
