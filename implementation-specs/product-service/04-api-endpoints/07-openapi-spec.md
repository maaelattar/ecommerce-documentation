# OpenAPI Specification Documentation

## Overview
This document summarizes the OpenAPI (Swagger) specification approach for the Product Service APIs, including versioning, documentation links, and best practices.

## OpenAPI/Swagger
- All Product Service APIs are documented using OpenAPI 3.0+ (Swagger)
- OpenAPI YAML/JSON files are maintained in the repository (e.g., `openapi/product-service.yaml`)
- Interactive API docs are available via Swagger UI at `/docs` endpoint in each environment

## Versioning
- API version is included in the base path (e.g., `/api/v1/products`)
- Major version changes are backward-incompatible and require a new base path (e.g., `/api/v2/...`)
- Minor/patch changes are backward-compatible (additive)

## Documentation Links
- [Product Service OpenAPI YAML](../openapi/product-service.yaml) (example path)
- [Swagger UI](http://localhost:3000/docs) (local dev)
- [Swagger Editor](https://editor.swagger.io/)

## OpenAPI Best Practices
- Use descriptive operation summaries and tags
- Document all request/response schemas and error responses
- Use `components` for reusable schemas, parameters, and responses
- Document authentication (JWT/OAuth2) and security schemes
- Include examples for all endpoints
- Use enums and formats for fields (e.g., `status`, `date-time`)
- Keep OpenAPI docs up to date with code changes

## Example OpenAPI Snippet
```yaml
openapi: 3.0.3
info:
  title: Product Service API
  version: 1.0.0
paths:
  /products:
    get:
      summary: List products
      tags: [Products]
      parameters:
        - in: query
          name: page
          schema:
            type: integer
        - in: query
          name: limit
          schema:
            type: integer
      responses:
        '200':
          description: List of products
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProductListResponse'
components:
  schemas:
    ProductListResponse:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Product'
        total:
          type: integer
        page:
          type: integer
        limit:
          type: integer
    Product:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        brand:
          type: string
        status:
          type: string
        createdAt:
          type: string
          format: date-time
```

## References
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger Editor](https://editor.swagger.io/)
- [NestJS OpenAPI Docs](https://docs.nestjs.com/openapi/introduction) 