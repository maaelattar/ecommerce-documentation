# 01 - API Consumption by Clients/Gateways

This document describes how client applications (e.g., web frontends, mobile apps) and API Gateways interact with the User Service's exposed APIs. The User Service provides the core functionalities for user identity, authentication, and profile management.

## 1. Primary Consumers

*   **Frontend Applications (Web/Mobile)**: These are the primary direct or indirect consumers of User Service APIs. They initiate actions like registration, login, password reset, profile updates, etc.
*   **API Gateway**: An API Gateway often sits in front of the User Service (and other microservices). It can handle:
    *   Request routing to the User Service.
    *   Centralized authentication (validating JWTs issued by the User Service).
    *   Rate limiting and DDoS protection.
    *   Request/response transformations (less common for User Service pass-through).
    *   Aggregating calls if a client needs data from multiple services (though User Service calls are often standalone for auth/profile).
*   **Backend-for-Frontend (BFF) Services**: A BFF might consume User Service APIs to tailor data or authentication flows specifically for a particular frontend experience (e.g., a BFF for a mobile app vs. a web app).

## 2. Key API Interaction Flows

Refer to the `ecommerce-documentation/implementation-specs/user-service/04-api-endpoints/` directory for detailed endpoint specifications. Common flows include:

*   **User Registration**: `POST /auth/register`
    *   Client sends user details; User Service creates account.
*   **User Login**: `POST /auth/login`
    *   Client sends credentials; User Service validates and returns JWT access/refresh tokens.
    *   Client securely stores these tokens (e.g., HttpOnly cookies for web, secure storage for mobile).
*   **Authenticated Requests**: For subsequent requests to any protected microservice (including further User Service calls like profile updates):
    *   Client includes the JWT access token in the `Authorization: Bearer <token>` header.
    *   The API Gateway (or the User Service itself if called directly) validates the token.
*   **Token Refresh**: `POST /auth/refresh-token`
    *   When an access token expires, the client uses its stored refresh token to request a new access token from the User Service.
*   **Profile Management**: `GET /users/me/profile`, `PUT /users/me/profile`, etc.
    *   Client uses these to display and allow users to update their profile information.
*   **Password Management**: `POST /auth/request-password-reset`, `POST /auth/reset-password`, `POST /auth/change-password`.
    *   Client facilitates these user-initiated password operations.
*   **Logout**: `POST /auth/logout`
    *   Client calls this to invalidate the user's session. Client also clears its stored tokens.

## 3. Communication Protocol

*   **HTTPS**: All communication between clients/gateways and the User Service APIs MUST be over HTTPS to ensure data confidentiality and integrity.
*   **RESTful Principles**: APIs are designed following RESTful principles, using standard HTTP methods (GET, POST, PUT, PATCH, DELETE) and status codes.
*   **JSON Payloads**: Request and response bodies are primarily in JSON format.

## 4. Authentication and Authorization

*   **Token-Based Authentication (JWT)**: The User Service issues JWTs. Clients include these tokens in requests to prove their identity and authentication status.
*   **API Gateway Role**: The API Gateway can offload JWT validation from individual microservices. It verifies the token signature and basic claims before forwarding the request, potentially injecting user identity information (e.g., `userId`, roles) into request headers for downstream services.
*   **User Service Role**: If called directly, or for its own protected endpoints, the User Service validates JWTs using its configured secrets/keys.
*   **Permissions**: Specific administrative User Service APIs (e.g., `/admin/users`) will require the JWT to contain claims indicating the user has the necessary roles/permissions. These are checked by guards within the User Service.

## 5. Error Handling by Clients

*   Clients should be prepared to handle standard HTTP error codes returned by the User Service:
    *   `400 Bad Request`: Invalid input, missing parameters (client should display specific validation messages if provided in the response body).
    *   `401 Unauthorized`: Missing/invalid token, incorrect credentials, MFA required.
    *   `403 Forbidden`: Authenticated user does not have permission for the action.
    *   `404 Not Found`: Resource not found (e.g., trying to get a profile for a non-existent user ID).
    *   `409 Conflict`: Resource already exists (e.g., trying to register an email that's taken).
    *   `429 Too Many Requests`: If rate limiting is applied and an API is called too frequently.
    *   `5xx Server Error`: Clients should handle these gracefully, possibly with retry mechanisms (with backoff) for transient issues or by displaying a generic error message.

## 6. Security Considerations for Clients/Gateways

*   **Secure Token Storage**: Clients (especially frontends) must store JWTs securely to prevent XSS or other attacks from stealing tokens.
    *   Web: HttpOnly, Secure cookies are preferred for refresh tokens. Access tokens can be in memory or Local Storage (with XSS mitigation).
    *   Mobile: Use platform-provided secure storage mechanisms.
*   **CSRF Protection**: For web applications, if using cookies for session management or tokens, CSRF protection mechanisms (e.g., anti-CSRF tokens) are essential.
*   **Input Validation (Client-Side)**: While the User Service performs robust server-side validation, client-side validation provides a better UX by giving immediate feedback.
*   **API Gateway Security**: The API Gateway should be hardened with security best practices (WAF, rate limiting, bot detection, etc.).

This integration pattern ensures that clients and gateways can securely and effectively utilize the User Service for all identity and user management needs.
