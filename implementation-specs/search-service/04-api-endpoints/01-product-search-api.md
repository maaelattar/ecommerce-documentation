# Product Search API

**Endpoint:** `GET /v1/search/products`

## Overview

This API endpoint allows clients to search for products indexed by the Search Service. It supports a variety of query parameters for filtering, sorting, and paginating results to enable rich product discovery experiences.

## Request

### Query Parameters

| Parameter         | Type   | Required | Description                                                                                                 |
| ----------------- | ------ | -------- | ----------------------------------------------------------------------------------------------------------- |
| `q`               | string | No       | The primary search query string (e.g., "red t-shirt", "laptop").                                          |
| `categoryId`      | string | No       | Filters results by a specific category ID.                                                                  |
| `brand`           | string | No       | Filters results by product brand.                                                                           |
| `minPrice`        | number | No       | Filters results by minimum product price.                                                                     |
| `maxPrice`        | number | No       | Filters results by maximum product price.                                                                     |
| `attributes`      | object | No       | A map of attribute keys and values for faceted search (e.g., `{"color": "red", "size": "M"}`). Encode as JSON string. |
| `sortBy`          | string | No       | Field to sort by (e.g., `price`, `name`, `relevance`, `createdAt`). Defaults to `relevance`.                  |
| `sortOrder`       | string | No       | Sort order (`asc` or `desc`). Defaults to `desc` for `relevance` and `price`, `asc` for `name`.           |
| `page`            | integer| No       | Page number for pagination. Defaults to `1`.                                                                |
| `limit`           | integer| No       | Number of results per page. Defaults to `20`, Max `100`.                                                     |
| `includeFacets`   | boolean| No       | If `true`, the response will include available facets (e.g. categories, brands, attributes) for further filtering. Defaults to `false`. |

### Headers

| Header            | Value                                   | Description                               |
| ----------------- | --------------------------------------- | ----------------------------------------- |
| `Accept-Language` | e.g., `en-US`, `fr-FR`                  | Specifies the preferred language for results if localization is supported. |
| `X-User-Id`       | e.g., `user-123` (if applicable)      | Optional. User ID for personalized search results or analytics. |
| `Authorization`   | `Bearer <token>` (if applicable)      | Token for secured access, if the endpoint requires authentication. |

## Response

### Success (200 OK)

```json
{
  "metadata": {
    "query": "red t-shirt",
    "totalHits": 150,
    "page": 1,
    "limit": 20,
    "totalPages": 8,
    "sortBy": "relevance",
    "sortOrder": "desc"
  },
  "products": [
    {
      "id": "prod_123",
      "name": "Classic Red T-Shirt",
      "description": "A comfortable cotton t-shirt in vibrant red.",
      "price": {
        "amount": 19.99,
        "currency": "USD"
      },
      "categories": [
        {"id": "cat_001", "name": "Apparel"},
        {"id": "cat_005", "name": "T-Shirts"}
      ],
      "brand": "BrandX",
      "imageUrl": "https://example.com/images/prod_123.jpg",
      "attributes": {
        "color": "Red",
        "size": "M",
        "material": "Cotton"
      },
      "stock": {
        "available": true,
        "quantity": 120
      },
      "averageRating": 4.5,
      "reviewCount": 67,
      "slug": "classic-red-t-shirt",
      "tags": ["red", "t-shirt", "summer", "casual"],
      "createdAt": "2023-01-15T10:00:00Z",
      "updatedAt": "2023-10-20T14:30:00Z",
      "_score": 12.345 // Elasticsearch relevance score
    }
    // ... more products
  ],
  "facets": {
    "categories": [
      {"id": "cat_001", "name": "Apparel", "count": 100},
      {"id": "cat_005", "name": "T-Shirts", "count": 80}
      // ... other categories
    ],
    "brands": [
      {"name": "BrandX", "count": 50},
      {"name": "BrandY", "count": 30}
      // ... other brands
    ],
    "attributes": {
      "color": [
        {"value": "Red", "count": 70},
        {"value": "Blue", "count": 40}
      ],
      "size": [
        {"value": "M", "count": 60},
        {"value": "L", "count": 55}
      ]
    }
  } // Only included if includeFacets=true
}
```

### Error Responses

*   **400 Bad Request**

    ```json
    {
      "statusCode": 400,
      "message": "Invalid query parameter: minPrice must be a number.",
      "error": "Bad Request"
    }
    ```
*   **401 Unauthorized** (If authentication is required and fails)

    ```json
    {
      "statusCode": 401,
      "message": "Unauthorized",
      "error": "Unauthorized"
    }
    ```
*   **500 Internal Server Error**

    ```json
    {
      "statusCode": 500,
      "message": "An unexpected error occurred while processing your request.",
      "error": "Internal Server Error"
    }
    ```

## NestJS Controller Example (Conceptual)

```typescript
import { Controller, Get, Query, Headers, Res, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiResponse, ApiHeader } from '@nestjs/swagger';
import { ProductSearchService } from '../services/product-search.service';
import { ProductSearchQueryDto } from './dto/product-search-query.dto';
import { AuthGuard } from '@nestjs/passport'; // Example guard
import { Response } from 'express';

@ApiTags('Search')
@Controller('v1/search/products')
export class ProductSearchController {
  constructor(private readonly productSearchService: ProductSearchService) {}

  @Get()
  @ApiOperation({
    summary: 'Search for products',
    description: 'Performs a search query against the product index, supporting various filters, sorting, and pagination.',
  })
  @ApiQuery({ name: 'q', type: String, required: false, description: 'Search query string' })
  @ApiQuery({ name: 'categoryId', type: String, required: false, description: 'Category ID to filter by' })
  @ApiQuery({ name: 'brand', type: String, required: false, description: 'Brand name to filter by' })
  @ApiQuery({ name: 'minPrice', type: Number, required: false, description: 'Minimum price' })
  @ApiQuery({ name: 'maxPrice', type: Number, required: false, description: 'Maximum price' })
  @ApiQuery({ name: 'attributes', type: String, required: false, description: 'JSON string of attribute filters (e.g., `{"color":"red"}`)' })
  @ApiQuery({ name: 'sortBy', type: String, required: false, enum: ['relevance', 'price', 'name', 'createdAt'], description: 'Field to sort by' })
  @ApiQuery({ name: 'sortOrder', type: String, required: false, enum: ['asc', 'desc'], description: 'Sort order' })
  @ApiQuery({ name: 'page', type: Number, required: false, description: 'Page number', default: 1 })
  @ApiQuery({ name: 'limit', type: Number, required: false, description: 'Results per page', default: 20 })
  @ApiQuery({ name: 'includeFacets', type: Boolean, required: false, description: 'Include facets in the response', default: false })
  @ApiHeader({ name: 'Accept-Language', required: false, description: 'Preferred language for results (e.g., en-US)' })
  @ApiHeader({ name: 'X-User-Id', required: false, description: 'User ID for personalized results' })
  // @UseGuards(AuthGuard('jwt')) // Uncomment if authentication is needed
  @ApiResponse({ status: 200, description: 'Search results matching the query.' /* type: ProductSearchResultsDto */ })
  @ApiResponse({ status: 400, description: 'Invalid query parameters.' })
  @ApiResponse({ status: 500, description: 'Internal server error.' })
  async searchProducts(
    @Query() queryDto: ProductSearchQueryDto,
    @Headers('Accept-Language') acceptLanguage?: string,
    @Headers('X-User-Id') userId?: string,
    // @Res() res: Response, // If custom response handling is needed
  ) {
    try {
      // The attributes query param might need JSON.parse if it's a string
      if (typeof queryDto.attributes === 'string') {
        try {
          queryDto.attributes = JSON.parse(queryDto.attributes as string);
        } catch (error) {
          // Handle invalid JSON for attributes
          // Consider throwing a BadRequestException
        }
      }
      const results = await this.productSearchService.search(queryDto, { acceptLanguage, userId });
      return results; // NestJS handles JSON serialization and status code (200 by default)
    } catch (error) {
      // Handle specific errors and throw appropriate NestJS HttpExceptions
      // e.g., if (error instanceof SpecificDomainError) throw new BadRequestException(error.message);
      throw error; // Re-throw if not handled or use a generic error handler
    }
  }
}
```

## Security Considerations

*   **Input Validation**: Rigorously validate all query parameters to prevent injection attacks (e.g., NoSQL injection if the underlying search engine is susceptible, though Elasticsearch is generally robust against direct query injection if DSL is used correctly).
*   **Rate Limiting**: Implement rate limiting to protect against DoS attacks and abuse.
*   **Data Sanitization**: Ensure that any user-generated content displayed in search results is properly sanitized to prevent XSS attacks.
*   **Resource Limits**: Enforce maximum values for `limit` to prevent overly large requests. Consider limits on query complexity if applicable.
*   **Authentication/Authorization**: If the product catalog contains sensitive or user-specific information, ensure appropriate authentication and authorization are applied.
*   **Logging**: Log search queries (anonymized if necessary for privacy) and performance metrics for monitoring and analytics.

## Future Enhancements

*   Personalized search results based on user history or profile.
*   Support for geo-spatial search if products have location data.
*   More advanced linguistic analysis (e.g., stemming, synonyms) if not already handled by Elasticsearch configuration.
*   A/B testing capabilities for different ranking algorithms.
