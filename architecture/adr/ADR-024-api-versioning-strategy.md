# ADR-024: API Versioning Strategy

*   **Status:** Proposed
*   **Date:** 2025-05-11
*   **Deciders:** Project Team
*   **Consulted:** Lead Developers, API Consumers (internal/external if any)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

As our microservices evolve, their APIs (both public-facing via the API Gateway ADR-014 and internal service-to-service APIs) will inevitably change. We need a clear strategy for API versioning to manage these changes without breaking existing clients/consumers. This allows for independent evolution of services and their consumers while maintaining stability.

## Decision Drivers

*   **Client Compatibility:** Avoid breaking existing clients when APIs change.
*   **Service Evolution:** Allow services to update their APIs and introduce new features or breaking changes in a controlled manner.
*   **Clarity and Predictability:** Consumers should easily understand which version of an API they are using and when versions might be deprecated.
*   **Maintainability:** Minimize the burden of supporting multiple API versions simultaneously.
*   **Developer Experience:** Simple for both API providers and consumers to work with versions.

## Considered Options for Versioning

1.  **URI Path Versioning (e.g., `/api/v1/products`, `/api/v2/products`):**
    *   Version is part of the URL path.
    *   Pros: Visible, explicit, easy to route and cache.
    *   Cons: Can lead to URI proliferation if not managed well.

2.  **Query Parameter Versioning (e.g., `/api/products?version=1`, `/api/products?version=2`):**
    *   Version is specified as a query parameter.
    *   Pros: Simple to implement.
    *   Cons: Less clean URLs, can be ignored by caches if not configured properly.

3.  **Custom Header Versioning (e.g., `Accept-Version: v1`, `X-API-Version: 1`):**
    *   Version is specified in a custom HTTP request header.
    *   Pros: Keeps URLs clean, semantically aligns with content negotiation.
    *   Cons: Less visible to end-users, requires clients to set headers correctly.

4.  **Accept Header Content Negotiation (e.g., `Accept: application/vnd.company.v1+json`):**
    *   Uses the standard `Accept` header with custom media types to specify the version.
    *   Pros: Adheres to HTTP semantics for content negotiation, keeps URLs clean.
    *   Cons: Can be more complex for clients to implement, less discoverable.

5.  **No Explicit Versioning (Continuous Evolution / Versionless APIs):**
    *   Avoid breaking changes; only add new fields/endpoints. Deprecate old fields gradually.
    *   Pros: Simplest for clients if no breaking changes are ever made.
    *   Cons: Very difficult to maintain long-term without ever introducing breaking changes, especially in a complex system. Risks accidental breaking changes.

## Decision Outcome

**Chosen Option:** **URI Path Versioning** for major, breaking changes. Complement with non-breaking backward-compatible changes within a version.

*   **Major Versioning (Breaking Changes):**
    *   Breaking changes (e.g., removing fields, changing data types, altering endpoint behavior significantly) MUST result in a new major version of the API.
    *   The major version will be indicated in the URI path, prefixed with `v`. For example: `/api/v1/orders`, `/api/v2/orders`.
    *   This applies to both external APIs exposed via the API Gateway and internal service-to-service APIs.
    *   The API Gateway (ADR-014) will route requests based on the version in the URI to the appropriate backend service version or adapt requests if necessary.

*   **Minor/Patch Versioning (Non-Breaking Changes):**
    *   Non-breaking changes (e.g., adding new optional fields, adding new endpoints, bug fixes that don't alter contracts) SHOULD be made within the current major version.
    *   These changes should be backward-compatible. Clients using the current major version should continue to function without modification.
    *   While not explicitly in the URI for minor changes, services should track their internal semantic versions (e.g., v1.1.0, v1.2.0) for documentation and communication.

*   **Deprecation Policy:**
    *   When a new major version of an API is released, the previous version(s) will enter a deprecation period.
    *   A clear deprecation timeline (e.g., 6 months, 12 months) MUST be communicated to all consumers.
    *   During the deprecation period, the old version will continue to be supported.
    *   After the deprecation period, the old version may be decommissioned.
    *   Monitoring (ADR-021) should be used to track usage of deprecated API versions to understand impact before decommissioning.

*   **API Documentation:**
    *   API documentation (e.g., OpenAPI/Swagger specifications) MUST clearly indicate the version of the API and provide a changelog.
    *   Documentation for all supported versions should be available.

*   **Internal vs. External APIs:**
    *   The same URI path versioning strategy will be used for consistency. However, internal service-to-service APIs might have shorter deprecation cycles if all consumers are internal and can be updated more rapidly.

## Consequences

*   **Pros:**
    *   Clear and explicit for API consumers.
    *   Easy for routing and caching mechanisms (like API Gateway and CDNs) to handle.
    *   Well-understood and widely adopted approach.
    *   Allows for clean separation of breaking changes.
*   **Cons:**
    *   Can lead to multiple versions of service code being maintained and deployed simultaneously if not managed carefully.
    *   URI changes for new versions, which some consider less "RESTful" than header-based versioning (though this is debatable).
    *   Requires discipline in identifying and managing breaking vs. non-breaking changes.
*   **Risks:**
    *   Clients might be slow to adopt new versions, increasing the burden of supporting old versions.
    *   Accidental introduction of breaking changes within a major version if not carefully managed.

## Next Steps

*   Update API design guidelines to incorporate this versioning strategy.
*   Ensure CI/CD pipelines (ADR-012) can support deploying and routing multiple versions of a service.
*   Establish a process for communicating API changes and deprecation schedules to consumers.
*   Configure API Gateway (ADR-014) to handle URI path-based version routing.
*   All new services and significant API changes must follow this versioning strategy.
