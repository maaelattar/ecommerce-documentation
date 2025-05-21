# 05 - Authentication and Authorization Integration

This document details how other microservices and API Gateways integrate with the User Service for authentication (AuthN) and authorization (AuthZ) purposes. The User Service is the source of truth for user identity and issues the tokens used to secure the platform. It also manages the roles and permissions that form the basis of the authorization model.

## 1. Authentication Integration (JWT Verification)

*   **JWTs as Bearer Tokens**: The User Service issues JSON Web Tokens (JWTs) upon successful user login. These access tokens are used as bearer tokens by clients when making requests to other microservices.
*   **Token Issuance**: Only the User Service is responsible for issuing access and refresh tokens.

*   **Token Verification by Other Services/Gateways**:
    *   **API Gateway**: The primary point of JWT validation. The API Gateway intercepts incoming requests, inspects the `Authorization: Bearer <token>` header, and validates the access token.
        *   **Signature Verification**: Gateway verifies the JWT signature using the public key (if using asymmetric algorithms like RS256/ES256) or the shared secret (if using symmetric HS256, though less ideal for distributed verification).
        *   **Claims Validation**: Gateway checks standard claims like `exp` (expiration), `nbf` (not before), `iss` (issuer), `aud` (audience).
        *   **Outcome**: If valid, the gateway may pass along user information (e.g., `userId`, `roles` from token claims) to the upstream service, often via request headers (e.g., `X-User-Id`, `X-User-Roles`). If invalid, the gateway rejects the request (e.g., 401 Unauthorized).
    *   **Individual Microservices**: If a microservice is called directly (not via a gateway that handles auth) or if deeper validation is needed, it must also be capable of validating JWTs.
        *   Services would need access to the User Service's public key (for asymmetric) or the relevant secret (for symmetric).
        *   They would use a standard JWT library to perform validation.
    *   **JWKS (JSON Web Key Set)**: For asymmetric keys (RS256/ES256), the User Service should expose a JWKS endpoint (e.g., `/.well-known/jwks.json`). This endpoint provides the public keys that other services and the API Gateway can use to verify JWT signatures. This allows for key rotation without needing to redeploy all consuming services with new static public keys.

*   **Token Revocation Check (Optional at Gateway/Service Level)**:
    *   If the User Service implements a token blacklist (see `TokenService`), the API Gateway or individual services might, for highly sensitive operations, make a call to the User Service (or a shared cache like Redis) to check if the JTI (JWT ID) of the incoming token has been revoked. This adds latency and is often reserved for critical actions.

## 2. Authorization Integration

Once a user is authenticated (identity verified via JWT), authorization determines what actions they are allowed to perform.

*   **Roles and Permissions from User Service**: The User Service is the master source for role definitions, permission definitions, and the assignment of roles to users and permissions to roles.

*   **Option 1: Roles/Permissions Embedded in JWT**:
    *   **Mechanism**: The User Service can embed a user's roles and/or a summarized list of their direct/effective permissions as custom claims within the JWT access token.
    *   **Pros**: Fast authorization decisions by API Gateway or microservices as they can inspect the token locally without calling the User Service.
    *   **Cons**: JWT size can become large if there are many roles/permissions. Token data can become stale if roles/permissions change frequently (until token refresh). Not suitable for highly dynamic or resource-specific permissions (ABAC).
    *   **Implementation**: The API Gateway or individual services would extract these claims and use them to make authorization decisions (e.g., a NestJS guard checking if `request.user.roles` from the JWT includes `admin`).

*   **Option 2: Centralized Authorization Check (via User Service or Dedicated Policy Engine)**:
    *   **Mechanism**: The API Gateway or microservice calls an endpoint on the User Service (or a dedicated Policy Decision Point - PDP like Open Policy Agent) to check if the authenticated user has permission for the requested action/resource.
        *   Example: `POST /auth/check-permissions` (see `06-authorization-query-endpoints.md`).
    *   **Pros**: Always uses the latest roles/permissions. Can support more complex ABAC policies.
    *   **Cons**: Adds latency due to the extra network call. Creates a runtime dependency on the User Service/PDP for authorization decisions.

*   **Option 3: Hybrid Approach (Common)**:
    *   Embed coarse-grained roles in the JWT for quick checks on common access levels.
    *   For fine-grained or highly sensitive operations, the service makes a call to the User Service/PDP for a definitive authorization check.

*   **API Gateway Enforcement**: The API Gateway can enforce some authorization rules based on JWT claims (e.g., user must have `admin` role to access `/admin/*` paths) or by calling an authorization service.

*   **Microservice-Level Enforcement (Guards)**:
    *   Within each microservice, NestJS Guards (or similar interceptors) are used on controllers/handlers to perform authorization.
    *   These guards can:
        *   Inspect JWT claims (roles, permissions) passed by the gateway.
        *   Call the User Service (or a local `AuthorizationService` that might itself call the main User Service) to verify permissions if not available in the token or if a more dynamic check is needed.
        *   Implement resource-specific checks (e.g., "is this user the owner of the requested document?").

## 3. Service-to-Service Authentication/Authorization

*   When microservices call each other (e.g., Order Service calls User Service), they also need to authenticate.
*   **Client Credentials Grant**: Services typically use the OAuth 2.0 client credentials grant type. The User Service (or a dedicated Auth Server component) would issue access tokens to services themselves (not users).
*   **Scopes/Permissions for Services**: These service tokens would contain scopes or permissions defining what actions the calling service is authorized to perform on the target service (e.g., Order Service might have `user_profile:read` scope to call User Service).

## 4. Flow Example (Authenticated Request with JWT and RBAC)

1.  **Client**: Makes a request to `/api/products` with `Authorization: Bearer <user_jwt>`.
2.  **API Gateway**:
    *   Receives the request.
    *   Validates the JWT signature and claims (using JWKS from User Service).
    *   Extracts `userId` and `roles: ["editor"]` from JWT claims.
    *   (Optional) If path `/api/products` requires `editor` role, gateway checks this. If not, forwards.
    *   Forwards request to Product Service, adding `X-User-Id: user123` and `X-User-Roles: editor` headers.
3.  **Product Service**:
    *   Receives request with user identity headers.
    *   A `PermissionsGuard` on the specific handler (e.g., for `POST /api/products`) checks if the action `product:create` is allowed.
        *   It might look up permissions for the `editor` role (either from a local cache synced from User Service events or by calling User Service if JWT doesn't have fine-grained perms).
    *   If authorized, processes the request. If not, returns 403 Forbidden.

This integration ensures that authentication is consistently handled and authorization policies managed by the User Service are enforced across the platform.
