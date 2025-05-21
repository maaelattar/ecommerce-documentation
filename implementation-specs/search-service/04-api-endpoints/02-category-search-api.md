# Category Search API

**Endpoint:** `GET /v1/search/categories`

## Overview

This API endpoint allows clients to search for and retrieve product categories. It can be used to fetch a hierarchy of categories, search for specific categories by name, or get categories associated with certain criteria.

## Request

### Query Parameters

| Parameter        | Type    | Required | Description                                                                                                |
| ---------------- | ------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| `q`              | string  | No       | Search query string to find categories by name or description.                                               |
| `parentId`       | string  | No       | Fetches direct subcategories of a given parent category ID. If not provided, top-level categories might be returned. |
| `slug`           | string  | No       | Fetches a specific category by its URL-friendly slug.                                                        |
| `includeChildren`| boolean | No       | If `true`, and `parentId` or `slug` is specified, includes nested child categories. Defaults to `false`.      |
| `depth`          | integer | No       | When `includeChildren` is true, specifies the maximum depth of child categories to retrieve.                 |
| `sortBy`         | string  | No       | Field to sort by (e.g., `name`, `productCount`). Defaults to `name`.                                       |
| `sortOrder`      | string  | No       | Sort order (`asc` or `desc`). Defaults to `asc`.                                                             |
| `page`           | integer | No       | Page number for pagination if searching with `q`. Defaults to `1`.                                            |
| `limit`          | integer | No       | Number of results per page if searching with `q`. Defaults to `20`, Max `100`.                              |

### Headers

| Header            | Value                                   | Description                               |
| ----------------- | --------------------------------------- | ----------------------------------------- |
| `Accept-Language` | e.g., `en-US`, `fr-FR`                  | Specifies the preferred language for category names if localization is supported. |

## Response

### Success (200 OK)

**Example 1: Searching for categories**

```json
{
  "metadata": {
    "query": "electronics",
    "totalHits": 5,
    "page": 1,
    "limit": 20,
    "totalPages": 1
  },
  "categories": [
    {
      "id": "cat_elec",
      "name": "Electronics",
      "slug": "electronics",
      "description": "All kinds of electronic gadgets and devices.",
      "parentCategoryId": null,
      "productCount": 1250,
      "imageUrl": "https://example.com/images/cat_elec.jpg",
      "childrenCount": 10, // Number of direct children
      "updatedAt": "2023-11-01T10:00:00Z"
    }
    // ... other matching categories
  ]
}
```

**Example 2: Fetching a category by slug with children** (`GET /v1/search/categories?slug=electronics&includeChildren=true&depth=2`)

```json
{
  "id": "cat_elec",
  "name": "Electronics",
  "slug": "electronics",
  "description": "All kinds of electronic gadgets and devices.",
  "parentCategoryId": null,
  "productCount": 1250,
  "imageUrl": "https://example.com/images/cat_elec.jpg",
  "updatedAt": "2023-11-01T10:00:00Z",
  "children": [
    {
      "id": "cat_laptops",
      "name": "Laptops",
      "slug": "laptops",
      "parentCategoryId": "cat_elec",
      "productCount": 300,
      "children": [
        {
          "id": "cat_gaming_laptops",
          "name": "Gaming Laptops",
          "slug": "gaming-laptops",
          "parentCategoryId": "cat_laptops",
          "productCount": 50
          // Further children omitted if depth=2 is reached
        }
      ]
    },
    {
      "id": "cat_smartphones",
      "name": "Smartphones",
      "slug": "smartphones",
      "parentCategoryId": "cat_elec",
      "productCount": 400
      // children omitted if depth=1 and they have no children, or depth=2 is reached
    }
  ]
}
```

**Example 3: Fetching top-level categories** (`GET /v1/search/categories`)

```json
{
  "metadata": {
    "totalHits": 15, // Total top-level categories
    "page": 1, // Assuming default pagination even for non-search listings
    "limit": 20,
    "totalPages": 1
  },
  "categories": [
    {
      "id": "cat_apparel",
      "name": "Apparel",
      "slug": "apparel",
      "parentCategoryId": null,
      "productCount": 2500
    },
    {
      "id": "cat_electronics",
      "name": "Electronics",
      "slug": "electronics",
      "parentCategoryId": null,
      "productCount": 1250
    }
    // ... other top-level categories
  ]
}
```

### Error Responses

*   **400 Bad Request**

    ```json
    {
      "statusCode": 400,
      "message": "Invalid query parameter: depth must be a positive integer.",
      "error": "Bad Request"
    }
    ```
*   **404 Not Found** (If a category specified by `slug` or `parentId` is not found)

    ```json
    {
      "statusCode": 404,
      "message": "Category with slug 'non-existent-category' not found.",
      "error": "Not Found"
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
import { Controller, Get, Query, Param, ParseBoolPipe, ParseIntPipe, DefaultValuePipe, Res } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiParam, ApiResponse } from '@nestjs/swagger';
import { CategorySearchService } from '../services/category-search.service';
import { CategorySearchQueryDto } from './dto/category-search-query.dto';
import { Response } from 'express';

@ApiTags('Search')
@Controller('v1/search/categories')
export class CategorySearchController {
  constructor(private readonly categorySearchService: CategorySearchService) {}

  @Get()
  @ApiOperation({
    summary: 'Search for or list product categories',
    description: 'Retrieves a list of categories, supports searching, filtering by parent, and fetching hierarchical structures.',
  })
  @ApiQuery({ name: 'q', type: String, required: false, description: 'Search query for category name/description' })
  @ApiQuery({ name: 'parentId', type: String, required: false, description: 'Parent category ID to fetch children of' })
  @ApiQuery({ name: 'slug', type: String, required: false, description: 'Category slug to fetch a specific category' })
  @ApiQuery({ name: 'includeChildren', type: Boolean, required: false, description: 'Include nested child categories', default: false })
  @ApiQuery({ name: 'depth', type: Number, required: false, description: 'Maximum depth for child categories when includeChildren is true' })
  @ApiQuery({ name: 'sortBy', type: String, required: false, enum: ['name', 'productCount'], default: 'name' })
  @ApiQuery({ name: 'sortOrder', type: String, required: false, enum: ['asc', 'desc'], default: 'asc' })
  @ApiQuery({ name: 'page', type: Number, required: false, default: 1 })
  @ApiQuery({ name: 'limit', type: Number, required: false, default: 20 })
  @ApiResponse({ status: 200, description: 'List of categories or a single category structure.' /* type: CategoryResponseDto */ })
  @ApiResponse({ status: 400, description: 'Invalid query parameters.' })
  @ApiResponse({ status: 404, description: 'Category not found.' })
  @ApiResponse({ status: 500, description: 'Internal server error.' })
  async findCategories(
    @Query() queryDto: CategorySearchQueryDto,
    // @Res() res: Response // If custom response handling is needed
  ) {
    try {
      // If slug is provided, it usually means fetching a single category possibly with children
      if (queryDto.slug) {
        const category = await this.categorySearchService.findBySlug(queryDto.slug, queryDto.includeChildren, queryDto.depth);
        if (!category) {
          // Consider throwing NotFoundException from '@nestjs/common'
          // res.status(404).send({ message: 'Category not found' });
          // return;
        }
        return category;
      }
      // Otherwise, it's a search or listing operation
      const results = await this.categorySearchService.search(queryDto);
      return results;
    } catch (error) {
      // Handle errors and throw appropriate NestJS HttpExceptions
      throw error;
    }
  }
}
```

## Security Considerations

*   **Input Validation**: Validate all query parameters, especially `depth` to prevent overly complex queries that could strain the system (e.g., fetching a very deep category tree).
*   **Rate Limiting**: Protect against excessive requests.
*   **Data Integrity**: Ensure that category data (names, slugs) are handled consistently, especially with localization.
*   **Authorization**: While typically public, ensure no sensitive category management details are exposed.

## Future Enhancements

*   Support for fetching categories associated with specific products or brands.
*   Endpoints to get a flat list of all categories or a full category tree (with caution for performance).
*   Facet counts for categories within product search results often serve related purposes.
