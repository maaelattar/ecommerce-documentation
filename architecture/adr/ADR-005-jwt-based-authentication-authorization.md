# ADR: Authentication and Authorization Strategy (JWT-based)

*   **Status:** Accepted
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (N/A - can be updated with security SMEs if applicable)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

In a distributed microservices architecture, a robust and scalable strategy is required for authenticating users and services, and for authorizing access to protected resources. The system needs to ensure that only legitimate users and services can access specific APIs and data, and that their permissions are correctly enforced. The strategy should support statelessness where possible to enhance scalability and simplify service design.

## Decision Drivers

*   **Security:** Strong protection against unauthorized access.
*   **Statelessness:** Ability for services to validate credentials without relying on a shared session store.
*   **Scalability:** The authentication/authorization mechanism should not become a bottleneck as the system scales.
*   **Interoperability:** Standardized way for services to exchange and verify identity and permission information.
*   **Developer Experience:** Ease of implementation and integration within services.
*   **Standardization:** Preference for widely adopted standards.

## Considered Options

### Option 1: JSON Web Tokens (JWT) for Bearer Authentication

*   **Description:** Use JWTs as bearer tokens. An authentication service (or Identity Provider - IdP) issues signed JWTs upon successful user login. These tokens contain claims about the user's identity and potentially their roles/permissions. Services validate the JWT signature and extract claims to make authorization decisions.
*   **Pros:**
    *   **Stateless Verification:** Services can verify JWTs independently using a public key or shared secret, without needing to call back to the issuing authority (for signature validation).
    *   **Widely Adopted Standard (RFC 7519):** Good library support in many languages (including Node.js/TypeScript).
    *   **Self-Contained:** Claims (identity, permissions) can be embedded directly in the token.
    *   **Suitable for Microservices:** Works well in distributed environments.
    *   **Can be used with OAuth 2.0/OpenID Connect:** JWTs are a common token format in OIDC flows.
*   **Cons:**
    *   **Token Size:** Embedding many claims can increase token size.
    *   **Revocation:** Stateless JWTs are harder to revoke immediately before their expiry. Revocation lists or short expiry times with refresh tokens are common mitigation strategies.
    *   **Security:** Tokens must be transmitted securely (HTTPS). If a token is stolen, it can be used until it expires unless a revocation mechanism is effective.
    *   **Key Management:** Secure management of signing keys is crucial.

### Option 2: Traditional Session-Based Authentication (Cookies)

*   **Description:** Upon login, a session ID is created, stored server-side (e.g., in Redis or a database), and sent to the client as a cookie. Subsequent requests include the cookie, and the server validates the session by looking it up.
*   **Pros:**
    *   **Mature Approach:** Well-understood.
    *   **Easy Revocation:** Sessions can be invalidated server-side immediately.
    *   **Smaller Token (Cookie):** Session IDs are typically small.
*   **Cons:**
    *   **Stateful:** Requires a shared session store, which can be a scalability bottleneck or single point of failure if not designed carefully.
    *   **Not Ideal for Service-to-Service Communication:** Primarily designed for browser-client interactions.
    *   **Cross-Origin Resource Sharing (CORS) Complexity:** Can be more complex to manage with cookies in a microservices environment with different domains/ports.

### Option 3: API Keys

*   **Description:** Pre-shared static keys assigned to clients or services for authentication.
*   **Pros:**
    *   **Simple to Implement for Specific Use Cases:** Suitable for server-to-server authentication or third-party integrations where a user is not directly involved.
*   **Cons:**
    *   **Static Credentials:** If compromised, they remain compromised until revoked and reissued.
    *   **No Inherent User Context:** Not suitable for user authentication.
    *   **Manual Management:** Key distribution and revocation can be manual and cumbersome.
    *   **Does not typically carry authorization information beyond the identity of the client.**

### Option 4: Full OAuth 2.0 / OpenID Connect (OIDC) Implementation

*   **Description:** Implementing a full OAuth 2.0 authorization server and OIDC for identity. JWTs are typically used as the access and ID tokens within this framework.
*   **Pros:**
    *   **Comprehensive Standard:** Covers many different authentication and authorization flows (e.g., authorization code grant, client credentials grant).
    *   **Well-defined Roles and Responsibilities.**
    *   **Secure and Widely Adopted for Delegated Access.**
*   **Cons:**
    *   **Complexity:** Can be complex to implement and manage a full OAuth 2.0/OIDC server from scratch. Often better to use a managed IdP.
    *   **Overhead:** Might be overkill if only simple token-based authentication is needed internally.

## Decision Outcome

**Chosen Option:** JSON Web Tokens (JWT) for Bearer Authentication, operating within an OAuth 2.0 / OpenID Connect (OIDC) compliant framework.

**Reasoning:**
JWTs provide a good balance of security, statelessness, and scalability for a microservices architecture. They allow services to make authentication and authorization decisions independently by verifying the token's signature and inspecting its claims.

This will be implemented by having a dedicated **Identity Provider (IdP)** service (which could be an existing third-party OIDC-compliant provider like Auth0, Keycloak, Okta, or a self-built service adhering to OIDC standards). This IdP will be responsible for:
1.  Authenticating users (e.g., via username/password, social logins).
2.  Issuing JWT-based ID Tokens (containing user identity information) and Access Tokens (containing scopes/permissions for accessing resources).

Services will then:
1.  Expect an Access Token (JWT) in the `Authorization` header (Bearer scheme).
2.  Validate the token's signature against the IdP's public keys.
3.  Extract claims to identify the user and their permissions/roles to make authorization decisions.
4.  For service-to-service communication, the OAuth 2.0 client credentials grant flow can be used, where services obtain JWTs to securely call each other.

This approach leverages the benefits of JWTs while fitting into a standard, robust framework like OIDC, which handles many complexities of token issuance and management.

### Positive Consequences
*   **Stateless Authentication:** Services do not need to maintain session state for authentication.
*   **Scalability:** Reduced load on a central authentication store for each request.
*   **Standardized:** Adherence to JWT, OAuth 2.0, and OIDC standards promotes interoperability and allows leveraging existing libraries and tools.
*   **Self-Contained Tokens:** User identity and permissions can be included in tokens, reducing the need for separate lookups.
*   **Decoupling:** Services are decoupled from the authentication mechanism beyond token validation.

### Negative Consequences (and Mitigations)
*   **Token Revocation Complexity:** Stateless JWTs are hard to revoke instantly.
    *   **Mitigation:**
        *   **Short-Lived Access Tokens:** Use relatively short expiry times (e.g., 5-15 minutes).
        *   **Refresh Tokens:** Use long-lived refresh tokens (stored securely, e.g., `HttpOnly` cookie for web clients, or secure storage for mobile) to obtain new access tokens without re-authenticating. Refresh tokens can be revoked.
        *   **Token Blocklist/Denylist:** For critical revocations, a lightweight, fast-checking denylist (e.g., in Redis) can be consulted by services or an API gateway, though this reintroduces some state.
*   **Token Security:** If an access token is compromised, it's valid until expiry.
    *   **Mitigation:** Enforce HTTPS everywhere. Implement robust XSS/CSRF protection for web clients. Educate users about phishing.
*   **Key Management:** Securely managing the IdP's signing keys is critical.
    *   **Mitigation:** Use strong key generation practices, secure storage (e.g., HSM, managed KMS), and implement key rotation policies.
*   **Initial Setup Complexity:** Setting up or integrating with an IdP.
    *   **Mitigation:** Leverage well-documented third-party IdPs or mature open-source solutions like Keycloak to reduce implementation burden.

## Links

*   [ADR-001: Adoption of Microservices Architecture](./ADR-001-adoption-of-microservices-architecture.md)
*   [E-commerce Platform: System Architecture Overview](../00-system-architecture-overview.md)
*   (Potentially: Security Guidelines document)

## Future Considerations

*   Detailed selection or implementation plan for the Identity Provider (IdP).
*   Define specific OAuth 2.0 flows to be supported (e.g., Authorization Code Grant with PKCE for public clients, Client Credentials for service-to-service).
*   Establish a clear strategy for managing roles and permissions and how they are represented as claims in JWTs.
*   Develop libraries/middleware for NestJS services to standardize JWT validation and claims extraction.

## Rejection Criteria

*   If the operational complexity of managing JWT lifecycles (especially revocation and refresh tokens) proves too burdensome for the majority of services and outweighs the benefits of statelessness.
*   If a simpler, equally secure mechanism becomes viable that better suits the platform's needs without the complexities of JWTs/OIDC.
