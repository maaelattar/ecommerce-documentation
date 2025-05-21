# Content Search API

**Endpoint:** `GET /v1/search/content`

## Overview

This API endpoint enables searching for unstructured content such as articles, blog posts, help pages, FAQs, or any other textual information indexed by the Search Service. It supports full-text search, filtering by content type or tags, and pagination.

## Request

### Query Parameters

| Parameter     | Type    | Required | Description                                                                                                |
| ------------- | ------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| `q`           | string  | Yes      | The full-text search query string.                                                                         |
| `contentType` | string  | No       | Filters results by a specific content type (e.g., `article`, `blog`, `faq`, `help-page`).                     |
| `tags`        | string  | No       | Comma-separated list of tags to filter by (e.g., `"setup,billing"`).                                      |
| `authorId`    | string  | No       | Filters content by a specific author ID.                                                                     |
| `dateFrom`    | string  | No       | Filters content published on or after this date (ISO 8601 format, e.g., `2023-01-01`).                      |
| `dateTo`      | string  | No       | Filters content published on or before this date (ISO 8601 format, e.g., `2023-12-31`).                       |
| `sortBy`      | string  | No       | Field to sort by (e.g., `relevance`, `publishDate`, `title`). Defaults to `relevance`.                       |
| `sortOrder`   | string  | No       | Sort order (`asc` or `desc`). Defaults to `desc` for `relevance` and `publishDate`.                           |
| `page`        | integer | No       | Page number for pagination. Defaults to `1`.                                                                 |
| `limit`       | integer | No       | Number of results per page. Defaults to `15`, Max `50`.                                                      |

### Headers

| Header            | Value                                   | Description                               |
| ----------------- | --------------------------------------- | ----------------------------------------- |
| `Accept-Language` | e.g., `en-US`, `fr-FR`                  | Specifies the preferred language for content if localization is supported. |

## Response

### Success (200 OK)

```json
{
  "metadata": {
    "query": "how to reset password",
    "totalHits": 5,
    "page": 1,
    "limit": 15,
    "totalPages": 1,
    "sortBy": "relevance",
    "sortOrder": "desc"
  },
  "contentItems": [
    {
      "id": "content_789",
      "title": "How to Reset Your Account Password",
      "slug": "how-to-reset-password",
      "contentType": "help-page",
      "excerpt": "Step-by-step guide on resetting your password if you've forgotten it or need to update it...",
      "url": "/help/reset-password",
      "author": {
        "id": "author_001",
        "name": "Support Team"
      },
      "tags": ["password", "account", "security"],
      "publishDate": "2023-05-20T09:00:00Z",
      "lastUpdatedDate": "2023-06-15T11:30:00Z",
      "_score": 9.876 // Elasticsearch relevance score
    },
    {
      "id": "blog_456",
      "title": "Understanding Multi-Factor Authentication",
      "slug": "understanding-mfa",
      "contentType": "blog",
      "excerpt": "Learn why Multi-Factor Authentication (MFA) is crucial for securing your online accounts...",
      "url": "/blog/understanding-mfa",
      "author": {
        "id": "author_002",
        "name": "Jane Doe"
      },
      "tags": ["security", "mfa", "best-practices"],
      "publishDate": "2023-03-10T14:00:00Z",
      "lastUpdatedDate": "2023-03-12T10:00:00Z",
      "_score": 8.123
    }
    // ... more content items
  ]
}
```

### Error Responses

*   **400 Bad Request**

    ```json
    {
      "statusCode": 400,
      "message": "Invalid query parameter: dateFrom must be a valid ISO 8601 date.",
      "error": "Bad Request"
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
import { Controller, Get, Query, Headers } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiResponse, ApiHeader } from '@nestjs/swagger';
import { ContentSearchService } from '../services/content-search.service';
import { ContentSearchQueryDto } from './dto/content-search-query.dto';

@ApiTags('Search')
@Controller('v1/search/content')
export class ContentSearchController {
  constructor(private readonly contentSearchService: ContentSearchService) {}

  @Get()
  @ApiOperation({
    summary: 'Search for content items',
    description: 'Performs a full-text search across indexed content like articles, blog posts, and help pages.',
  })
  @ApiQuery({ name: 'q', type: String, required: true, description: 'Full-text search query' })
  @ApiQuery({ name: 'contentType', type: String, required: false, description: 'Filter by content type (e.g., article, blog)' })
  @ApiQuery({ name: 'tags', type: String, required: false, description: 'Comma-separated list of tags' })
  @ApiQuery({ name: 'authorId', type: String, required: false, description: 'Filter by author ID' })
  @ApiQuery({ name: 'dateFrom', type: String, required: false, description: 'Start date for filtering (ISO 8601)' })
  @ApiQuery({ name: 'dateTo', type: String, required: false, description: 'End date for filtering (ISO 8601)' })
  @ApiQuery({ name: 'sortBy', type: String, required: false, enum: ['relevance', 'publishDate', 'title'], default: 'relevance' })
  @ApiQuery({ name: 'sortOrder', type: String, required: false, enum: ['asc', 'desc'], default: 'desc' })
  @ApiQuery({ name: 'page', type: Number, required: false, default: 1 })
  @ApiQuery({ name: 'limit', type: Number, required: false, default: 15 })
  @ApiHeader({ name: 'Accept-Language', required: false, description: 'Preferred language for results' })
  @ApiResponse({ status: 200, description: 'Search results matching the query.' /* type: ContentSearchResultsDto */ })
  @ApiResponse({ status: 400, description: 'Invalid query parameters.' })
  @ApiResponse({ status: 500, description: 'Internal server error.' })
  async searchContent(
    @Query() queryDto: ContentSearchQueryDto,
    @Headers('Accept-Language') acceptLanguage?: string,
  ) {
    try {
      // Tags might come as a comma-separated string, convert to array if necessary
      if (queryDto.tags && typeof queryDto.tags === 'string') {
        // It's good practice for DTOs to handle this transformation or use a custom pipe
        // queryDto.tags = (queryDto.tags as string).split(',').map(tag => tag.trim());
      }
      const results = await this.contentSearchService.search(queryDto, { acceptLanguage });
      return results;
    } catch (error) {
      // Handle errors and throw appropriate NestJS HttpExceptions
      throw error;
    }
  }
}
```

## Security Considerations

*   **Input Validation**: Thoroughly validate all inputs, especially the `q` parameter, to prevent any form of injection if the search engine or query construction is vulnerable. Elasticsearch DSL usage is generally safe.
*   **Rate Limiting**: Implement to prevent abuse.
*   **Output Encoding**: Ensure content excerpts and titles are properly encoded if displayed directly in HTML to prevent XSS.
*   **Access Control**: If certain content is not public, ensure that search results respect user permissions. This might involve filtering results based on the user's role or authentication status.
*   **Data Privacy**: Be mindful of searching across potentially sensitive content. Ensure compliance with privacy regulations.

## Future Enhancements

*   Highlighting search terms in results.
*   More sophisticated filtering options (e.g., by custom metadata fields).
*   Suggestions for related content or search queries.
*   Personalization of content search results based on user interests or roles.
