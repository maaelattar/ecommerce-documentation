# ADR-030: API Design Guidelines (Internal & External)

*   **Status:** Proposed
*   **Date:** 2025-05-11
*   **Deciders:** Project Team, Lead Developers
*   **Consulted:** Frontend Team, Backend Team, API Consumers (future)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

Our microservices architecture (ADR-001) relies heavily on APIs for both internal service-to-service communication and external client interactions via the API Gateway (ADR-014). While ADR-024 defines API versioning, we need consistent design guidelines to ensure our APIs are intuitive, predictable, easy to use, and maintainable. This ADR establishes these guidelines.

## Decision Drivers

*   **Developer Experience:** APIs should be easy for both producers and consumers to understand, implement, and use.
*   **Consistency:** Uniform API design across services reduces cognitive load and integration friction.
*   **Clarity & Predictability:** Consumers should have clear expectations about how APIs behave.
*   **Maintainability & Evolvability:** Well-designed APIs are easier to maintain and evolve without breaking consumers unnecessarily.
*   **Scalability & Performance:** Design choices can impact performance and how well APIs scale.

## Decision Outcome

**Chosen Approach:** Adopt a set of RESTful API design principles and conventions, primarily using JSON for request/response bodies. These guidelines apply to all HTTP-based APIs.

### 1. Resource Naming
*   **Use Nouns, Not Verbs:** Resource URIs should represent entities (nouns), not actions (verbs). E.g., `/users`, `/orders`.
*   **Plural Nouns:** Use plural nouns for collections. E.g., `/products`, `/customers/{customerId}/addresses`.
*   **Lowercase Paths:** Use lowercase letters for URI paths. Use hyphens (`-`) to separate words if needed (e.g., `/product-categories`).
*   **Hierarchy for Related Resources:** Use path hierarchy to show relationships. E.g., `/orders/{orderId}/items/{itemId}`.

### 2. HTTP Methods (Verbs)
*   Use standard HTTP methods appropriately:
    *   `GET`: Retrieve a resource or a collection of resources. (Safe, Idempotent)
    *   `POST`: Create a new resource. (Not Idempotent)
    *   `PUT`: Update an existing resource completely. (Idempotent)
    *   `PATCH`: Partially update an existing resource. (Not necessarily Idempotent, but aim for it)
    *   `DELETE`: Delete a resource. (Idempotent)
*   Avoid using `GET` or `POST` for operations that should be `PUT`, `PATCH`, or `DELETE`.

### 3. Request & Response Bodies
*   **JSON:** Use JSON for request and response bodies unless a specific use case demands otherwise (e.g., file uploads).
*   **Content-Type Header:** Always use `Content-Type: application/json` for JSON request bodies and `Accept: application/json` for requesting JSON responses.
*   **Field Naming:** Use `camelCase` for JSON field names (e.g., `firstName`, `orderTotal`).
*   **Meaningful Payloads:** Design clear and concise request and response payloads. Only include necessary data.
*   **Dates and Times:** Use ISO 8601 format for dates and times (e.g., `YYYY-MM-DDTHH:mm:ss.sssZ`).

### 4. HTTP Status Codes
*   Use standard HTTP status codes accurately to indicate the outcome of an API request.
    *   **2xx (Success):**
        *   `200 OK`: General success for `GET`, `PUT`, `PATCH`, `DELETE` (if no body returned).
        *   `201 Created`: Resource successfully created (`POST`). Include a `Location` header pointing to the new resource.
        *   `202 Accepted`: Request accepted for processing, but processing is not complete (often for asynchronous operations).
        *   `204 No Content`: Success, but no response body (e.g., for `DELETE`, or `PUT`/`PATCH` if no content is returned).
    *   **4xx (Client Errors):**
        *   `400 Bad Request`: General client-side error (e.g., malformed request, invalid syntax).
        *   `401 Unauthorized`: Authentication is required and has failed or has not yet been provided.
        *   `403 Forbidden`: Authenticated, but user does not have permission to access the resource.
        *   `404 Not Found`: Requested resource does not exist.
        *   `405 Method Not Allowed`: HTTP method used is not supported for this resource.
        *   `409 Conflict`: Request could not be processed because of a conflict in the current state of the resource (e.g., edit conflict).
        *   `422 Unprocessable Entity`: Server understands the content type, and the syntax is correct, but it was unable to process the contained instructions (e.g., validation errors).
    *   **5xx (Server Errors):**
        *   `500 Internal Server Error`: Generic server error. Avoid using this if a more specific 5xx code is applicable.
        *   `502 Bad Gateway`: Server, while acting as a gateway or proxy, received an invalid response from an upstream server.
        *   `503 Service Unavailable`: Server is currently unable to handle the request (e.g., overloaded, down for maintenance).
        *   `504 Gateway Timeout`: Server, while acting as a gateway or proxy, did not receive a timely response from an upstream server.

### 5. Error Handling
*   Provide consistent, structured JSON error responses for 4xx and 5xx status codes.
*   Include:
    *   `type` (optional): A URI identifying the error type (can link to documentation).
    *   `title`: A short, human-readable summary of the problem.
    *   `status`: The HTTP status code.
    *   `detail` (optional): A human-readable explanation specific to this occurrence of the problem.
    *   `instance` (optional): A URI that identifies the specific occurrence of the problem.
    *   `errors` (optional, for 400/422): An array of specific validation errors if applicable (e.g., field name, message).
    *   `traceId` (optional but recommended): Correlation ID for tracing (ADR-017, ADR-021).
*   Example error response for a validation failure (`422`):
    ```json
    {
      "type": "/errors/validation-failed",
      "title": "Validation Failed",
      "status": 422,
      "detail": "One or more fields submitted are invalid.",
      "instance": "/orders/123",
      "traceId": "abcdef123456",
      "errors": [
        { "field": "email", "message": "Email must be a valid email address." },
        { "field": "quantity", "message": "Quantity must be greater than 0." }
      ]
    }
    ```
*   Do NOT expose sensitive information (stack traces, internal system details) in error responses.

### 6. Filtering, Sorting, and Pagination
*   **Filtering:** Use query parameters for filtering collections. E.g., `/products?category=electronics&status=available`.
*   **Sorting:** Use a `sort` query parameter. E.g., `/products?sort=price_asc,name_desc`. Define clear field names and `_asc`/`_desc` convention.
*   **Pagination:** Use cursor-based or offset/limit pagination.
    *   **Offset/Limit (simpler):** `/products?offset=0&limit=20`.
    *   **Cursor-based (more robust for large datasets):** `/products?limit=20&cursor=opaqueCursorString`. Provide `next_cursor` in response.
    *   Include pagination metadata in the response (e.g., `total_items`, `limit`, `offset` or `next_cursor`).

### 7. HATEOAS (Hypermedia as the Engine of Application State) - Optional
*   Consider including links to related resources or available actions in responses to make APIs more discoverable. This is optional and can be adopted selectively.
    ```json
    {
      "orderId": "123",
      "status": "pending",
      "_links": {
        "self": { "href": "/orders/123" },
        "items": { "href": "/orders/123/items" },
        "cancel": { "href": "/orders/123/cancel", "method": "POST" }
      }
    }
    ```

### 8. API Documentation
*   All APIs MUST be documented using OpenAPI Specification (OAS) v3.x (formerly Swagger).
*   Documentation should be generated from code/annotations where possible and kept up-to-date.
*   Include examples for requests and responses.

### 9. Idempotency
*   Ensure `PUT`, `DELETE`, and safe `GET` operations are idempotent.
*   For `POST` operations that might be retried due to network issues, consider providing an `Idempotency-Key` header mechanism (ADR-022).

## Consequences

*   **Pros:**
    *   Improved consistency and predictability across all APIs.
    *   Enhanced developer experience for both API producers and consumers.
    *   Reduced integration time and effort.
    *   Clearer error handling and troubleshooting.
    *   Standardized documentation through OpenAPI.
*   **Cons:**
    *   Requires discipline from development teams to adhere to the guidelines.
    *   Initial effort to align existing APIs (if any) or develop new ones according to these standards.
    *   Some debates on RESTful purity (e.g., HATEOAS adoption) might arise but are addressed by making some aspects optional.
*   **Risks:**
    *   Guidelines might be ignored or inconsistently applied without proper review processes.
    *   Overly prescriptive guidelines could stifle innovation in specific edge cases where deviations are justified.

## Next Steps

*   Formally adopt these guidelines and communicate them to all development teams.
*   Update the ADR template (ADR-000) or create a separate checklist for API design reviews.
*   Provide linters or tools where possible to automatically check for adherence to some guidelines (e.g., OpenAPI linters).
*   Incorporate API design review into the development lifecycle (e.g., as part of pull request reviews or specific design review meetings for new APIs).
*   Develop a shared library or utility for consistent error response formatting.
