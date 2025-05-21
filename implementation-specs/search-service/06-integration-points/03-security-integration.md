# Search Service Security Integration

## Overview

Security is paramount for all microservices, including the Search Service. This document outlines how the Search Service integrates with platform-wide security mechanisms for authentication and authorization, both for its exposed APIs and for any calls it might make to other services.

## Securing Exposed Search Service APIs

The Search Service exposes several types of APIs (product search, category search, suggestions, admin APIs for indexing) which have different security requirements.

1.  **Public-Facing Search APIs (e.g., `/v1/search/products`, `/v1/search/suggest`)**:
    *   **Authentication**: These APIs are often publicly accessible for anonymous users (e.g., browsing an e-commerce site). However, they might also accept optional authentication (e.g., a JWT bearer token for a logged-in user) to enable personalized results or access to user-specific search history/preferences.
    *   **Authorization**: For anonymous access, no specific authorization is needed beyond basic access. If authenticated, user roles or scopes might influence results (e.g., visibility of certain products if B2B features are active, though this is often handled by filtering within the search query based on user context provided by an API Gateway or the client).
    *   **Rate Limiting & Bot Protection**: Essential to prevent abuse. Often handled at an API Gateway level but can also be implemented within the service.

2.  **Administrative APIs (e.g., `/v1/admin/search/indexing/*`)**:
    *   **Authentication**: MUST be strictly authenticated. Only authorized administrators or internal system processes should be able to access these.
        *   **Mechanism**: OAuth 2.0 client credentials flow for service-to-service calls, or JWT Bearer tokens for human administrators with specific admin roles/scopes.
    *   **Authorization**: Granular permissions should be enforced. For example, a role might allow triggering re-indexing but not deleting an index directly.
        *   **Mechanism**: Role-Based Access Control (RBAC) based on scopes or roles present in the authenticated token.

### Integration with Authentication Service (e.g., Auth0, Keycloak, Custom IAM)

*   **Token Validation**: The Search Service (or an upstream API Gateway) will validate JWTs (JSON Web Tokens) received in the `Authorization` header.
    *   This involves fetching public keys from the Identity Provider (IdP) to verify the token signature.
    *   Checking token expiration (`exp`), issuer (`iss`), and audience (`aud`).
*   **NestJS Implementation**: `passport` library with strategies like `passport-jwt` is commonly used.

    ```typescript
    // Conceptual: src/auth/jwt.strategy.ts
    import { Injectable } from '@nestjs/common';
    import { PassportStrategy } from '@nestjs/passport';
    import { ExtractJwt, Strategy } from 'passport-jwt';
    import { ConfigService } from '@nestjs/config';
    // import { JwksClient } from 'jwks-rsa'; // For fetching public keys from JWKS URI

    @Injectable()
    export class JwtStrategy extends PassportStrategy(Strategy) {
      constructor(private readonly configService: ConfigService) {
        super({
          jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
          ignoreExpiration: false,
          secretOrKeyProvider: (request, rawJwtToken, done) => {
            // Example: Fetch public key from a JWKS endpoint
            // const client = new JwksClient({ jwksUri: configService.get('auth.jwksUri') });
            // client.getSigningKey(decodedHeader.kid, (err, key) => {
            //   if (err) return done(err);
            //   const signingKey = key.getPublicKey();
            //   done(null, signingKey);
            // });
            // Or use a simple secret if symmetric keys are used (less common for microservices)
            done(null, configService.get('auth.jwtSecret'));
          },
          // audience: configService.get('auth.audience'),
          // issuer: configService.get('auth.issuer'),
        });
      }

      async validate(payload: any) {
        // Payload is the decoded JWT. Return user object or claims to be attached to request.user
        // e.g., return { userId: payload.sub, username: payload.username, roles: payload.roles };
        return payload; 
      }
    }
    ```
*   **Guards**: Use `@UseGuards(AuthGuard('jwt'))` (or custom guards for role/scope checks) on controllers/handlers that require authentication/authorization.

    ```typescript
    // Conceptual: src/search.controller.ts
    import { Controller, Get, UseGuards, Req } from '@nestjs/common';
    import { AuthGuard } from '@nestjs/passport';
    // import { RolesGuard } from '../auth/guards/roles.guard';
    // import { Roles } from '../auth/decorators/roles.decorator';

    @Controller('v1/search')
    export class SearchController {
      @Get('products')
      // @UseGuards(AuthGuard('jwt')) // Optional for public search, required if personalized
      // @Roles('user', 'admin') // Example custom roles guard
      searchProducts(@Req() request) {
        const userId = request.user?.sub; // Access user info if token was provided and validated
        // ... search logic, potentially using userId for personalization
      }

      @Get('admin/status')
      @UseGuards(AuthGuard('jwt'))
      // @Roles('admin_search')
      getAdminStatus() {
        // ... admin logic
      }
    }
    ```

## Search Service as a Client to Other Services

The Search Service typically does not make many outbound authenticated calls, as its primary role during indexing is to consume events (which are inherently trusted from the message broker within the internal network) or perform batch loads (where credentials for source DBs are configured).

However, if it *were* to call another secured service (e.g., an enrichment service, or if it actively fetched data via API instead of events):

*   **Client Credentials Flow**: For service-to-service communication, the Search Service would use the OAuth 2.0 client credentials flow to obtain an access token from the Authentication Service.
    *   It would present its `client_id` and `client_secret` (securely configured) to the token endpoint.
    *   The received token would then be used as a Bearer token when calling the target service.
*   **Token Management**: Securely store and manage `client_id` and `client_secret`. Cache access tokens and refresh them before they expire.
*   **HTTP Client Configuration**: Configure the HTTP client used by the Search Service (e.g., NestJS `HttpModule` with Axios) to automatically attach the bearer token to outgoing requests to specific services.

## Security Considerations for Event Consumption

*   **Network Security**: Kafka brokers should reside within a secured network zone.
*   **Topic ACLs (Kafka)**: Use Kafka Access Control Lists (ACLs) to ensure the Search Service consumer group only has permission to read from the specific topics it needs.
*   **Message Integrity/Encryption (Optional, Advanced)**: While often relying on network-level security (TLS for Kafka communication), message-level encryption or signing can be implemented for extremely sensitive event data, though this adds complexity.

## Data Security within Elasticsearch

*   **Authentication**: Elasticsearch itself should be secured, requiring authentication for any client connections (including from the Search Service).
    *   Typically username/password or API key based.
*   **Authorization**: Use Elasticsearch roles and privileges to ensure the Search Service's Elasticsearch user has only the necessary permissions (e.g., create, read, write, delete for its specific indexes, but not manage cluster settings).
*   **Encryption at Rest**: Ensure data stored in Elasticsearch is encrypted at rest.
*   **Encryption in Transit**: Use HTTPS/TLS for all communication with Elasticsearch.
*   **Field-Level Security (FLS) / Document-Level Security (DLS)**: If the Search Service indexes data with varying access levels (e.g., some documents only visible to certain users), Elasticsearch DLS/FLS features can be used, though this often complicates query logic and is usually managed by filtering queries at the application layer before they hit Elasticsearch.

## General Security Best Practices

*   **Least Privilege**: Grant only necessary permissions to the Search Service, its API clients, and its users within other systems (Kafka, Elasticsearch, databases).
*   **Secure Configuration Management**: Protect sensitive configurations like API keys, database credentials, and JWT secrets using tools like HashiCorp Vault, AWS Secrets Manager, or environment variable injection in secure orchestrators.
*   **Regular Security Audits and Updates**: Keep dependencies (OS, libraries, Elasticsearch, Kafka) patched and conduct regular security reviews.
*   **Input Validation**: Rigorously validate all inputs to APIs and event handlers to prevent injection attacks or other vulnerabilities, as also covered in API and event handling docs.

This document provides a high-level overview. Specific implementation details will depend on the chosen platform-wide security tools and policies.
