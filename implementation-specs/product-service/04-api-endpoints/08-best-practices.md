# API Best Practices

## Overview
This document outlines best practices for designing, implementing, and maintaining the Product Service APIs, ensuring consistency, reliability, and security.

## Versioning
- Use URI versioning (e.g., `/api/v1/products`)
- Increment major version for breaking changes
- Deprecate old versions with clear communication

## Pagination
- Use `page` and `limit` query parameters
- Return total count, current page, and limit in response
- Example:
```json
{
  "items": [ /* ... */ ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

## Filtering & Sorting
- Support filtering by key fields (e.g., `status`, `brand`, `categoryId`)
- Use query parameters for filters (e.g., `?status=active&brand=Nike`)
- Support sorting by fields (e.g., `?sort=name,-createdAt`)

## Rate Limiting
- Apply rate limits to prevent abuse (e.g., 100 requests/minute per user)
- Return `429 Too Many Requests` with `Retry-After` header

## Idempotency
- Ensure idempotency for safe methods (e.g., `PUT`, `DELETE`)
- Support idempotency keys for POST where needed (e.g., order creation)

## Security
- Require HTTPS for all endpoints
- Use JWT/OAuth2 for authentication
- Enforce RBAC for authorization
- Validate and sanitize all input
- Set security headers (CORS, X-Frame-Options, etc.)
- Log and monitor all access and errors

## Documentation
- Maintain up-to-date OpenAPI/Swagger docs
- Document all endpoints, parameters, request/response schemas, and error codes
- Provide examples for requests and responses
- Use consistent naming and conventions

## Error Handling
- Use standard error response structure
- Map errors to appropriate HTTP status codes
- Avoid exposing sensitive internal details

## Deprecation Policy
- Announce deprecated endpoints in advance
- Provide migration guides for breaking changes
- Remove deprecated endpoints after a grace period

## References
- [RESTful API Design](https://restfulapi.net/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [JSON:API Specification](https://jsonapi.org/) 