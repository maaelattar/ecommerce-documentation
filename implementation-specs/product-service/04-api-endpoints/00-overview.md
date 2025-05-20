# API Endpoints & Controllers Overview

## Phase Objectives

This phase documents the RESTful API endpoints and controllers for the Product Service, covering all core resources (products, categories, inventory, prices, discounts) and cross-cutting concerns (authentication, error handling, best practices).

## API Design Principles
- RESTful resource-oriented endpoints
- Consistent naming, versioning, and structure
- Use of standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Clear request/response schemas (JSON)
- Proper use of status codes and error messages
- Secure endpoints with authentication and RBAC
- Support for pagination, filtering, and sorting
- OpenAPI/Swagger documentation for all endpoints

## Documentation Structure

1. [Product API](01-product-api.md)
2. [Category API](02-category-api.md)
3. [Inventory API](03-inventory-api.md)
4. [Price & Discount API](04-price-discount-api.md)
5. [Authentication & Authorization](05-authentication-authorization.md)
6. [Error Handling](06-error-handling.md)
7. [OpenAPI Specification](07-openapi-spec.md)
8. [API Best Practices](08-best-practices.md)

## Next Steps
- Document each resource's endpoints, request/response schemas, and security requirements
- Provide example requests and responses
- Link to relevant service/component specifications
- Ensure all APIs are covered by OpenAPI/Swagger

## References
- [RESTful API Design](https://restfulapi.net/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [JSON:API Specification](https://jsonapi.org/) 