# API Design Standards

## 1. Overview

This document defines the standards and best practices for designing, implementing, and maintaining APIs across the e-commerce platform. These standards ensure consistency, usability, and maintainability of all service APIs, whether they are public-facing or internal service-to-service APIs.

## 2. Core Principles

### 2.1. API-First Development

- APIs should be designed before implementation begins
- API contracts should be defined using OpenAPI Specification (OAS)
- API design reviews should be conducted before implementation
- Mock APIs should be available for early integration testing

### 2.2. RESTful Design

- APIs should follow RESTful principles where appropriate
- Resource-oriented design with proper use of HTTP methods
- Consistent URL structure and naming conventions
- Proper use of HTTP status codes

### 2.3. Evolvability

- APIs should be designed to evolve without breaking existing clients
- Changes should be backward compatible when possible
- Breaking changes should follow proper versioning and deprecation policies
- New functionality should be added in a way that doesn't impact existing clients

## 3. URL Structure and Naming

### 3.1. Base URL Format

```
https://{environment}.{service-name}.ecommerce.example.com/api/v{version}/{resource}
```

Examples:

- `https://prod.order-service.ecommerce.example.com/api/v1/orders`
- `https://dev.product-service.ecommerce.example.com/api/v2/products`

### 3.2. Resource Naming

- Use plural nouns for resource collections (e.g., `/orders`, `/products`)
- Use kebab-case for multi-word resource names (e.g., `/order-items`)
- Avoid verbs in resource paths except for special actions
- Nest resources to represent relationships (e.g., `/orders/{id}/items`)

### 3.3. Query Parameters

- Use for filtering, sorting, pagination, and field selection
- Follow consistent naming convention: `camelCase`
- Common parameters:
  - `page` and `limit` for pagination
  - `sort` and `order` for sorting
  - `fields` for sparse fieldsets
  - `filter[fieldName]` for filtering

## 4. Request/Response Format

### 4.1. Content Types

- JSON (`application/json`) should be the primary content type
- Support content negotiation when multiple formats are available
- Specify charset in Content-Type header (`application/json; charset=utf-8`)

### 4.2. Response Structure

Standard success response:

```json
{
  "data": {
    // Resource representation or collection
  },
  "meta": {
    "timestamp": "2023-07-22T14:30:15Z",
    "requestId": "req-123456",
    "pagination": {
      "page": 1,
      "limit": 20,
      "totalItems": 100,
      "totalPages": 5
    }
  },
  "links": {
    "self": "https://api.example.com/v1/resource?page=1&limit=20",
    "next": "https://api.example.com/v1/resource?page=2&limit=20",
    "prev": null
  }
}
```

### 4.3. Error Response Structure

Standard error response:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid parameters",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      },
      {
        "field": "password",
        "message": "Must be at least 8 characters long"
      }
    ],
    "requestId": "req-123456",
    "timestamp": "2023-07-22T14:30:15Z"
  }
}
```

### 4.4. HTTP Status Codes

- `200 OK`: Successful request with response body
- `201 Created`: Resource successfully created
- `204 No Content`: Successful request with no response body
- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Authentication succeeded but not authorized
- `404 Not Found`: Resource not found
- `409 Conflict`: Request conflicts with current state
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Unexpected server error
- `503 Service Unavailable`: Service temporarily unavailable

## 5. API Versioning

### 5.1. Versioning Strategy

- Major versions in the URL path: `/api/v1/resource`
- Minor, non-breaking changes should not require a version change
- Support at least one previous major version during transition periods
- Set clear deprecation timelines for older versions

### 5.2. Deprecation Policy

- Mark deprecated endpoints with `Deprecated` header
- Add `Sunset` header with date when endpoint will be removed
- Document deprecation in API documentation
- Notify clients through developer communications
- Monitor usage of deprecated endpoints

### 5.3. Backwards Compatibility Rules

- Adding new fields should not break existing clients
- Never remove or rename fields without versioning
- Never change field types or semantics without versioning
- New optional request parameters are backward compatible
- New response fields are backward compatible

## 6. Authentication and Authorization

### 6.1. Authentication Methods

- JWT (JSON Web Tokens) for user authentication
- API keys for third-party integrations
- Client certificates for service-to-service communication
- OAuth 2.0 for delegated authorization

### 6.2. JWT Standards

- Use short expiration times (15-60 minutes)
- Implement refresh token rotation
- Include standard claims: `iss`, `sub`, `exp`, `iat`, `jti`
- Sign tokens with RS256 (asymmetric) or HS256 (symmetric) algorithms
- Validate all claims on the server side

### 6.3. Authorization

- Role-based access control (RBAC) for coarse-grained permissions
- Attribute-based access control (ABAC) for fine-grained permissions
- Document permission requirements for each endpoint
- Return appropriate status codes: `401 Unauthorized` vs `403 Forbidden`

## 7. Rate Limiting and Throttling

### 7.1. Rate Limit Headers

Include standard rate limit headers:

- `X-RateLimit-Limit`: Requests allowed in period
- `X-RateLimit-Remaining`: Requests remaining in period
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

### 7.2. Throttling Strategy

- Implement tiered rate limits based on client type
- Use token bucket algorithm for rate limiting
- Return `429 Too Many Requests` with `Retry-After` header when limit exceeded
- Configure separate limits for read and write operations

## 8. Pagination, Filtering, and Sorting

### 8.1. Pagination

- Use page-based pagination with `page` and `limit` parameters
- Include pagination metadata in response
- Provide links to first, previous, next, and last pages
- Default page size should be reasonable (20-50 items)

Example:

```
GET /api/v1/products?page=2&limit=20
```

### 8.2. Filtering

- Use consistent parameter naming for filters
- Support multiple filter values with comma separation
- Support range filters with brackets notation
- Support complex filters with JSON-encoded values

Examples:

```
GET /api/v1/orders?status=PROCESSING,SHIPPED
GET /api/v1/products?price[min]=10&price[max]=50
GET /api/v1/users?filter={"age":{"$gt":18}}
```

### 8.3. Sorting

- Use `sort` parameter with comma-separated fields
- Use `-` prefix for descending order
- Default sort order should be documented

Example:

```
GET /api/v1/products?sort=-createdAt,name
```

### 8.4. Field Selection

- Use `fields` parameter for sparse fieldsets
- Support comma-separated fields or JSON path notation
- Reduce payload size for mobile clients

Example:

```
GET /api/v1/products?fields=id,name,price
```

## 9. Documentation Standards

### 9.1. OpenAPI Specification

- All APIs must be documented using OpenAPI Specification
- OpenAPI documents must be version controlled
- Generated documentation should be accessible to developers
- Examples should be provided for all operations

### 9.2. Required Documentation Elements

- Purpose and scope of the API
- Authentication and authorization requirements
- All available endpoints with method, path, and description
- Request parameters, body schema, and examples
- Response schema, status codes, and examples
- Error codes and handling
- Rate limits and other constraints

### 9.3. API Reference Documentation

Generated documentation should include:

- Interactive API explorer
- SDK usage examples
- Code snippets in multiple languages
- Changelog and version history
- Migration guides between versions

## 10. Security Standards

### 10.1. Input Validation

- Validate all request parameters and body
- Use schema validation for request bodies (JSON Schema)
- Implement strict type checking
- Sanitize inputs to prevent injection attacks
- Validate content types and character encodings

### 10.2. Output Encoding

- Encode all output to prevent XSS and injection attacks
- Set appropriate Content-Type and charset headers
- Implement proper JSON encoding
- Never include sensitive data in responses

### 10.3. Security Headers

Include the following security headers in all responses:

- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Cache-Control` with appropriate values

### 10.4. Sensitive Data Handling

- Never expose sensitive data in URLs
- Use appropriate authorization for sensitive endpoints
- Mask sensitive data in logs
- Implement secure deletion of sensitive data
- Encrypt sensitive data in transit and at rest

## 11. Monitoring and Observability

### 11.1. API Metrics

Capture the following metrics for all API endpoints:

- Request count
- Response time (min, max, average, percentiles)
- Error rate (by status code)
- Request size
- Response size

### 11.2. Request Tracing

- Generate unique request ID for each request
- Include request ID in all logs
- Implement distributed tracing for request flows across services
- Provide correlation ID header for client-initiated tracing

### 11.3. Health Checks

- Implement `/health` endpoint for service health checks
- Return appropriate status codes based on service health
- Include dependency health status
- Support detailed health checks for internal monitoring

## 12. Implementation Examples

### 12.1. Controller Implementation

```typescript
@Controller("api/v1/products")
@ApiTags("products")
export class ProductController {
  constructor(
    private readonly productService: ProductService,
    private readonly logger: Logger
  ) {}

  @Get()
  @ApiOperation({ summary: "Get products with pagination and filtering" })
  @ApiResponse({
    status: 200,
    description: "Products found",
    type: ProductResponseDto,
  })
  @UseGuards(JwtAuthGuard)
  async getProducts(
    @Query() queryParams: ProductQueryParamsDto,
    @User() user: UserDto
  ): Promise<ApiResponse<ProductResponseDto[]>> {
    this.logger.log(
      `Get products request received with params: ${JSON.stringify(
        queryParams
      )}`
    );

    try {
      const [products, totalCount] = await this.productService.findProducts(
        queryParams
      );
      const productDtos = products.map((product) => this.mapToDto(product));

      return {
        data: productDtos,
        meta: {
          timestamp: new Date().toISOString(),
          requestId: request.id,
          pagination: {
            page: queryParams.page || 1,
            limit: queryParams.limit || 20,
            totalItems: totalCount,
            totalPages: Math.ceil(totalCount / (queryParams.limit || 20)),
          },
        },
        links: this.generatePaginationLinks(queryParams, totalCount),
      };
    } catch (error) {
      this.logger.error(
        `Error retrieving products: ${error.message}`,
        error.stack
      );
      throw error;
    }
  }
}
```

### 12.2. OpenAPI Documentation

```typescript
const options = new DocumentBuilder()
  .setTitle("E-Commerce Product API")
  .setDescription("API for managing products in the e-commerce platform")
  .setVersion("1.0")
  .addTag("products")
  .addBearerAuth()
  .build();

const document = SwaggerModule.createDocument(app, options, {
  deepScanRoutes: true,
  extraModels: [ProductDto, ProductResponseDto, ErrorResponseDto],
});

SwaggerModule.setup("api/docs", app, document, {
  swaggerOptions: {
    persistAuthorization: true,
  },
});
```

## 13. References

- [RESTful API Design Guidelines](../../development-guidelines/api-guidelines.md)
- [API Security Checklist](../../security/api-security-checklist.md)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)
- [JSON API Specification](https://jsonapi.org/format/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
