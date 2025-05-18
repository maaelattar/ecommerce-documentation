# ADR-034: API Versioning Strategy

*   **Status:** Proposed
*   **Date:** {{YYYY-MM-DD}} (Please update with current date)
*   **Deciders:** Project Team
*   **Consulted:** Lead Developers, Architects
*   **Informed:** All technical stakeholders

## Context and Problem Statement

As our e-commerce platform evolves, the APIs exposed by its microservices will inevitably change. New features will be added, existing functionalities modified, and occasionally, breaking changes will be necessary. Without a clear API versioning strategy, these changes can disrupt existing clients (frontend applications, other microservices, third-party integrations) and make it difficult to manage the API lifecycle effectively. We need a consistent approach to versioning our APIs to ensure smooth transitions, maintain backward compatibility where possible, and clearly communicate changes to consumers.

This ADR builds upon [ADR-030: API Design Guidelines (Internal & External)](./ADR-030-api-design-guidelines.md), which identifies API versioning as a key aspect requiring a defined strategy.

## Decision Drivers

*   **Client Stability:** Minimize disruption to API consumers when changes are introduced.
*   **Clear Communication:** Provide a clear and predictable way for consumers to understand and adapt to API changes.
*   **Developer Experience (DX):** Make it easy for developers to understand which version of an API they are working with and how to migrate to newer versions.
*   **Maintainability:** Allow for the evolution of APIs without creating an unmanageable web of conditional logic or breaking existing integrations.
*   **Independent Evolution:** Enable services to evolve their APIs at different paces.
*   **Tooling Support:** Leverage built-in support from our chosen framework (NestJS, as per [ADR-003](./ADR-003-nodejs-nestjs-for-initial-services.md)) and API specification standard (OpenAPI, as per [ADR-007](./ADR-007-api-first-design-principle.md)).

## Considered Options

### 1. URI Path Versioning

*   **Description:** The API version is included directly in the URI path, typically prefixed (e.g., `/api/v1/products`, `/api/v2/products`).
*   **Pros:**
    *   Highly explicit and visible to consumers.
    *   Easy to test and access different versions directly from a browser or simple HTTP clients.
    *   Well-understood and widely adopted.
    *   Good support in routing frameworks (including NestJS) and API gateways.
    *   Caching friendly as URLs are distinct.
*   **Cons:**
    *   Can lead to 'cluttered' URIs if not managed well.
    *   Technically, a new version implies a new resource URI, which some REST purists argue against (though pragmatically accepted).

### 2. Header Versioning

*   **Description:** The API version is specified in a custom HTTP request header (e.g., `X-API-Version: 1` or `Api-Version: 1`).
*   **Pros:**
    *   Keeps URIs 'clean' as they don't change with versions.
    *   Allows for default versioning if the header is absent.
    *   Supported by NestJS.
*   **Cons:**
    *   Less visible to end-users browsing an API (requires HTTP client inspection).
    *   Can be slightly more complex for clients to implement than URI versioning.
    *   Caching can be more complex as the URL remains the same for different versions; relies on `Vary` header.

### 3. Media Type / Accept Header Versioning

*   **Description:** The API version is specified as part of the `Accept` header using a custom media type (e.g., `Accept: application/vnd.mycompany.v1+json`).
*   **Pros:**
    *   Considered by some as the most 'RESTful' approach as it leverages content negotiation.
    *   Keeps URIs clean.
    *   Supported by NestJS.
*   **Cons:**
    *   Most complex for consumers to implement and test.
    *   Less commonly used and understood than URI or header versioning.
    *   Can make simple API exploration with a browser difficult.

### 4. Query Parameter Versioning

*   **Description:** The API version is specified as a query parameter (e.g., `/products?version=1`).
*   **Pros:**
    *   Relatively easy to use and implement.
*   **Cons:**
    *   Query parameters are generally for filtering or modifying a request, not defining the resource contract itself.
    *   Can be easily omitted, leading to ambiguity if a default is not well-handled.
    *   Less clean than URI or header versioning for this purpose.
    *   Can clutter analytics for resource access.

## Decision Outcome

**Chosen Option:** **URI Path Versioning**

We will adopt URI Path Versioning as the primary strategy for versioning our APIs. The version will be prefixed in the path, for example: `/api/v1/{resource}`.

**Reasoning:**

URI Path Versioning offers the best balance of explicitness, ease of use for consumers, and strong support in our technology stack (NestJS and OpenAPI). Its visibility makes it straightforward for developers to understand which version they are interacting with, simplifies testing and debugging, and aligns with common industry practices.

While Header and Media Type versioning have their merits in terms of URI purity, the practical benefits and clarity of URI Path Versioning are deemed more advantageous for our platform.

## Implementation Details

1.  **Version Format:** API versions will be major versions prefixed with 'v' (e.g., `v1`, `v2`, `v3`).
    *   Minor and patch changes (e.g., non-breaking additions, bug fixes) should be backward-compatible and will NOT result in a new URI version path. These are part of the ongoing evolution of a specific major version.
    *   Breaking changes (e.g., removing fields, changing data types, altering resource structure significantly) MUST result in a new major version.
2.  **NestJS Configuration:** API versioning will be enabled in NestJS applications using the `URI` type:
    ```typescript
    // In main.ts
    app.enableVersioning({
      type: VersioningType.URI,
      prefix: 'v', // Optional: if you want '/v1/' instead of just '/1/' in paths
      // defaultVersion: '1' // Or an array ['1', '2'] to support multiple defaults
    });
    ```
    Controllers or individual routes will then specify their version(s) (e.g., `@Controller({ path: 'users', version: '1' })` or `@Get('profile') @Version('2')`).
3.  **OpenAPI Specification:**
    *   API versions will be clearly reflected in the `paths` of the OpenAPI document (e.g., `/v1/users`, `/v2/users`).
    *   Alternatively, the `servers` object in OpenAPI can be used to define base URLs for different versions (e.g., `https://api.example.com/v1`, `https://api.example.com/v2`). The primary method should be versioned paths for clarity within a single API definition document per service version.
    *   The `info.version` field in the OpenAPI document will reflect the version of the API *specification* (e.g., `1.0.0`, `1.1.0` for non-breaking changes to the spec, `2.0.0` for a spec describing `v2` of the API paths).
4.  **Deprecation Strategy:**
    *   We will aim to support the current version (N) and the previous version (N-1) of an API.
    *   A clear deprecation schedule will be communicated to consumers well in advance of retiring an older API version. This includes API documentation updates, and potentially custom headers like `Warning` or `Deprecation` in responses from older versions.
    *   Monitoring will be in place to track usage of older API versions to inform the retirement timeline.
5.  **Default Version:** When multiple versions are active, a default version may be designated. However, clients are strongly encouraged to explicitly request the version they are compatible with.

## Positive Consequences

*   Clear and unambiguous API versions for all consumers.
*   Simplified routing logic in services and API gateways.
*   Developers can easily work with and test different API versions.
*   Facilitates a structured approach to API evolution and deprecation.
*   Improved cacheability due to distinct URIs.

## Negative Consequences (and Mitigations)

*   **URI Changes:** Each new version means a new URI. This is inherent to the chosen method.
    *   **Mitigation:** Clear documentation and communication. Hypermedia links (if used) should point to versioned URIs.
*   **Code Duplication Risk:** Managing multiple versions in the codebase could lead to duplication if not handled carefully (e.g., separate controllers or significant conditional logic).
    *   **Mitigation:** Abstract common business logic into services that can be reused by controllers handling different API versions. Use inheritance or composition patterns for controllers where appropriate.
*   **Increased Number of Endpoints:** Over time, the total number of active versioned endpoints will grow before old versions are deprecated.
    *   **Mitigation:** Adhere to a disciplined deprecation strategy (N-1 support) to limit proliferation.

## Links

*   [ADR-003: Node.js with NestJS for Initial Services](./ADR-003-nodejs-nestjs-for-initial-services.md)
*   [ADR-007: API-First Design Principle](./ADR-007-api-first-design-principle.md)
*   [ADR-030: API Design Guidelines (Internal & External)](./ADR-030-api-design-guidelines.md)
*   [NestJS Documentation - Versioning](https://docs.nestjs.com/techniques/versioning)
*   [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)

## Future Considerations

*   Tooling for automating the generation of client SDKs for specific API versions.
*   Detailed policy on what constitutes a 'breaking change' versus a 'non-breaking change'.
*   Specific communication channels and timelines for API deprecation announcements.

## Rejection Criteria

*   If managing URI-versioned routes in NestJS becomes overly complex despite mitigation strategies.
*   If a significant portion of API consumers strongly prefer and demonstrate a critical need for a different versioning scheme (e.g., due to limitations in their client technology).
