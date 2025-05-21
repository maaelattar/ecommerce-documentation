# Autocomplete/Suggestions API

**Endpoint:** `GET /v1/search/suggest`

## Overview

This API endpoint provides type-ahead search suggestions (autocomplete) to enhance the user experience. As a user types into a search box, this API can be called to fetch relevant suggestions for products, categories, keywords, or even popular search queries.

## Request

### Query Parameters

| Parameter   | Type    | Required | Description                                                                                                                               |
| ----------- | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `q`         | string  | Yes      | The partial query string entered by the user.                                                                                               |
| `type`      | string  | No       | Comma-separated list of suggestion types to include (e.g., `product`, `category`, `keyword`, `query`). Defaults to all applicable types. |
| `limit`     | integer | No       | Maximum number of suggestions to return for each type. Defaults to `5` per type. Max `10`.                                                  |
| `context`   | string  | No       | Optional context for suggestions (e.g., `homepage_search`, `product_listing_filter`). Can be used for analytics or tailored suggestions.      |
| `categoryId`| string  | No       | If suggesting products, this can scope suggestions to a particular category.                                                              |

### Headers

| Header            | Value                                   | Description                               |
| ----------------- | --------------------------------------- | ----------------------------------------- |
| `Accept-Language` | e.g., `en-US`, `fr-FR`                  | Specifies the preferred language for suggestions if localization is supported. |
| `X-User-Id`       | e.g., `user-123` (if applicable)      | Optional. User ID for personalized suggestions or analytics. |

## Response

### Success (200 OK)

```json
{
  "query": "lapto",
  "suggestions": {
    "products": [
      {
        "id": "prod_456",
        "name": "Laptop Pro 15 inch",
        "thumbnailUrl": "https://example.com/images/prod_456_thumb.jpg",
        "price": {
          "amount": 1299.99,
          "currency": "USD"
        },
        "categoryName": "Laptops"
      },
      {
        "id": "prod_789",
        "name": "Laptop Air Ultra-thin",
        "thumbnailUrl": "https://example.com/images/prod_789_thumb.jpg",
        "price": {
          "amount": 999.00,
          "currency": "USD"
        },
        "categoryName": "Laptops"
      }
    ],
    "categories": [
      {
        "id": "cat_laptops",
        "name": "Laptops",
        "productCount": 300
      },
      {
        "id": "cat_laptop_accessories",
        "name": "Laptop Accessories",
        "productCount": 150
      }
    ],
    "keywords": [
      {"term": "laptop charger", "relevance": 0.8},
      {"term": "laptop sleeve", "relevance": 0.7}
    ],
    "queries": [
      // Popular queries starting with "lapto"
      {"text": "laptop deals", "popularity": 0.9},
      {"text": "laptop for students", "popularity": 0.85}
    ]
  }
}
```

**Notes on Response Structure:**

*   The `suggestions` object contains keys for different types of suggestions requested (e.g., `products`, `categories`, `keywords`, `queries`).
*   If a type is not requested or no suggestions are found for it, the key might be omitted or its value might be an empty array.
*   The structure within each type can vary based on what information is most useful for that suggestion type.

### Error Responses

*   **400 Bad Request**

    ```json
    {
      "statusCode": 400,
      "message": "Query parameter 'q' is required.",
      "error": "Bad Request"
    }
    ```
*   **500 Internal Server Error**

    ```json
    {
      "statusCode": 500,
      "message": "An unexpected error occurred while fetching suggestions.",
      "error": "Internal Server Error"
    }
    ```

## NestJS Controller Example (Conceptual)

```typescript
import { Controller, Get, Query, Headers } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiResponse, ApiHeader } from '@nestjs/swagger';
import { AutocompleteService } from '../services/autocomplete.service';
import { AutocompleteQueryDto } from './dto/autocomplete-query.dto';

@ApiTags('Search')
@Controller('v1/search/suggest')
export class AutocompleteController {
  constructor(private readonly autocompleteService: AutocompleteService) {}

  @Get()
  @ApiOperation({
    summary: 'Get search suggestions (autocomplete)',
    description: 'Provides type-ahead suggestions for products, categories, keywords, etc., based on a partial query.',
  })
  @ApiQuery({ name: 'q', type: String, required: true, description: 'Partial query string' })
  @ApiQuery({ name: 'type', type: String, required: false, description: 'Comma-separated suggestion types (e.g., product,category)' })
  @ApiQuery({ name: 'limit', type: Number, required: false, description: 'Max suggestions per type', default: 5 })
  @ApiQuery({ name: 'context', type: String, required: false, description: 'Context for suggestions (e.g., homepage_search)' })
  @ApiQuery({ name: 'categoryId', type: String, required: false, description: 'Category ID to scope product suggestions' })
  @ApiHeader({ name: 'Accept-Language', required: false, description: 'Preferred language for suggestions' })
  @ApiHeader({ name: 'X-User-Id', required: false, description: 'User ID for personalized suggestions' })
  @ApiResponse({ status: 200, description: 'Search suggestions based on the query.' /* type: AutocompleteResponseDto */ })
  @ApiResponse({ status: 400, description: 'Invalid query parameters.' })
  @ApiResponse({ status: 500, description: 'Internal server error.' })
  async getSuggestions(
    @Query() queryDto: AutocompleteQueryDto,
    @Headers('Accept-Language') acceptLanguage?: string,
    @Headers('X-User-Id') userId?: string,
  ) {
    try {
      // DTO might handle splitting 'type' string into an array
      const results = await this.autocompleteService.getSuggestions(queryDto, { acceptLanguage, userId });
      return results;
    } catch (error) {
      // Handle errors
      throw error;
    }
  }
}
```

## Security Considerations

*   **Input Validation**: Sanitize and validate the `q` parameter to prevent any potential issues if the suggestion mechanism involves complex query parsing.
*   **Rate Limiting**: Essential for this endpoint as it can be called frequently during user typing.
*   **Performance**: This API needs to be extremely fast. Optimize suggestion generation (e.g., using Elasticsearch suggesters, dedicated prefix indexes, or cached popular queries).
*   **Data Exposure**: Ensure that suggestions do not inadvertently expose sensitive information (e.g., private product names if not authorized).
*   **Throttling**: Consider client-side throttling to avoid excessive API calls on every keystroke.

## Future Enhancements

*   More sophisticated ranking of suggestions (e.g., based on popularity, user history, conversion rates).
*   Support for fuzzy matching and typo correction in suggestions.
*   Visual cues in suggestions (e.g., product images, category icons).
*   "Did you mean?" functionality for broader query corrections.
