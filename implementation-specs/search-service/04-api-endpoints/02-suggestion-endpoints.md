# Suggestion Endpoints

## Overview

The suggestion endpoints provide autocomplete, search suggestions, and popular search terms to enhance the user search experience. These endpoints are designed to be fast and lightweight to support real-time interaction.

## Autocomplete Suggestions

### Endpoint: GET /suggestions/autocomplete

Provides real-time term completion as the user types in the search box.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Partial search query text |
| `size` | integer | No | Number of suggestions to return (default: 10, max: 20) |
| `type` | string | No | Type of suggestions: `term` (default), `product`, or `category` |
| `context` | string | No | Context for suggestions (e.g., a category ID to limit scope) |
| `locale` | string | No | Locale for suggestions (default: en-US) |

#### Example Request

```http
GET /search/v1/suggestions/autocomplete?query=bluet&size=5&type=term
```

#### Response

```json
{
  "data": [
    {
      "text": "bluetooth headphones",
      "highlighted": "<em>bluet</em>ooth headphones",
      "score": 0.95
    },
    {
      "text": "bluetooth speakers",
      "highlighted": "<em>bluet</em>ooth speakers",
      "score": 0.87
    },
    {
      "text": "bluetooth earbuds",
      "highlighted": "<em>bluet</em>ooth earbuds",
      "score": 0.82
    },
    {
      "text": "bluetooth adapter",
      "highlighted": "<em>bluet</em>ooth adapter",
      "score": 0.75
    },
    {
      "text": "bluetooth transmitter",
      "highlighted": "<em>bluet</em>ooth transmitter",
      "score": 0.68
    }
  ],
  "metadata": {
    "query": "bluet",
    "execution_time_ms": 12
  }
}
```

#### Product Autocomplete Example

For `type=product`:

```http
GET /search/v1/suggestions/autocomplete?query=bluet&size=3&type=product
```

Response:

```json
{
  "data": [
    {
      "id": "prod-12345",
      "text": "Wireless Bluetooth Headphones",
      "highlighted": "Wireless <em>Bluet</em>ooth Headphones",
      "image_url": "https://example.com/images/products/headphones-1-thumb.jpg",
      "price": {
        "current": 49.99,
        "currency": "USD"
      },
      "url": "https://example.com/products/wireless-bluetooth-headphones",
      "score": 0.92
    },
    {
      "id": "prod-23456",
      "text": "Bluetooth 5.0 Wireless Earbuds",
      "highlighted": "<em>Bluet</em>ooth 5.0 Wireless Earbuds",
      "image_url": "https://example.com/images/products/earbuds-thumb.jpg",
      "price": {
        "current": 39.99,
        "currency": "USD"
      },
      "url": "https://example.com/products/bluetooth-wireless-earbuds",
      "score": 0.85
    },
    {
      "id": "prod-34567",
      "text": "Portable Bluetooth Speaker",
      "highlighted": "Portable <em>Bluet</em>ooth Speaker",
      "image_url": "https://example.com/images/products/speaker-thumb.jpg",
      "price": {
        "current": 29.99,
        "currency": "USD"
      },
      "url": "https://example.com/products/portable-bluetooth-speaker",
      "score": 0.78
    }
  ],
  "metadata": {
    "query": "bluet",
    "execution_time_ms": 25
  }
}
```

## Search Suggestions

### Endpoint: GET /suggestions/search

Provides suggested search terms based on the input query, including common corrections and related terms.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query text |
| `size` | integer | No | Number of suggestions to return (default: 5, max: 10) |
| `include_corrections` | boolean | No | Include spell corrections (default: true) |
| `include_related` | boolean | No | Include related terms (default: true) |
| `locale` | string | No | Locale for suggestions (default: en-US) |

#### Example Request

```http
GET /search/v1/suggestions/search?query=bluetooth+headpones&size=5
```

#### Response

```json
{
  "data": {
    "corrections": [
      {
        "text": "bluetooth headphones",
        "highlighted": "bluetooth head<em>p</em><em>h</em>ones",
        "score": 0.95
      }
    ],
    "related": [
      {
        "text": "wireless headphones",
        "score": 0.87
      },
      {
        "text": "noise cancelling headphones",
        "score": 0.82
      },
      {
        "text": "bluetooth earbuds",
        "score": 0.78
      },
      {
        "text": "over ear bluetooth headphones",
        "score": 0.72
      }
    ]
  },
  "metadata": {
    "query": "bluetooth headpones",
    "has_correction": true,
    "execution_time_ms": 28
  }
}
```

## Popular Searches

### Endpoint: GET /suggestions/popular

Returns popular search terms, optionally filtered by context.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `size` | integer | No | Number of terms to return (default: 10, max: 20) |
| `context` | string | No | Context for suggestions (e.g., a category ID) |
| `timeframe` | string | No | Time period: `day`, `week` (default), `month` |
| `locale` | string | No | Locale for suggestions (default: en-US) |

#### Example Request

```http
GET /search/v1/suggestions/popular?size=5&context=electronics&timeframe=week
```

#### Response

```json
{
  "data": [
    {
      "text": "iphone 13",
      "rank": 1,
      "search_count": 1250
    },
    {
      "text": "samsung galaxy",
      "rank": 2,
      "search_count": 1100
    },
    {
      "text": "airpods pro",
      "rank": 3,
      "search_count": 950
    },
    {
      "text": "bluetooth headphones",
      "rank": 4,
      "search_count": 875
    },
    {
      "text": "smart tv",
      "rank": 5,
      "search_count": 820
    }
  ],
  "metadata": {
    "context": "electronics",
    "timeframe": "week",
    "date_range": {
      "from": "2023-10-01",
      "to": "2023-10-07"
    }
  }
}
```

## Implementation Details

### Autocomplete Implementation

The autocomplete functionality uses Elasticsearch's completion suggester for high performance:

```typescript
@Injectable()
export class AutocompleteService {
  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly cacheManager: Cache,
    private readonly logger: Logger,
  ) {}

  async getSuggestions(query: string, options: AutocompleteOptions): Promise<AutocompleteResult> {
    try {
      // Check cache first
      const cacheKey = `autocomplete:${query}:${JSON.stringify(options)}`;
      const cachedResult = await this.cacheManager.get<AutocompleteResult>(cacheKey);
      
      if (cachedResult) {
        return cachedResult;
      }
      
      // Prepare suggester based on type
      const suggester = this.buildSuggester(query, options);
      
      // Execute suggest query
      const response = await this.elasticsearchService.search({
        index: this.getIndexForType(options.type),
        body: {
          suggest: suggester
        }
      });
      
      // Process results
      const result = this.processSuggesterResponse(response, query, options);
      
      // Cache for 5 minutes
      await this.cacheManager.set(cacheKey, result, 300);
      
      return result;
    } catch (error) {
      this.logger.error(`Error getting autocomplete suggestions: ${error.message}`, error.stack);
      throw new SuggestionException('Failed to get autocomplete suggestions', error);
    }
  }

  private buildSuggester(query: string, options: AutocompleteOptions): any {
    if (options.type === 'product') {
      return {
        products_suggester: {
          prefix: query,
          completion: {
            field: 'suggest',
            size: options.size || 10,
            fuzzy: {
              fuzziness: 'AUTO'
            },
            contexts: options.context ? {
              category: [options.context]
            } : undefined
          }
        }
      };
    } else if (options.type === 'category') {
      // Similar structure for category suggestions
    } else {
      // Default term suggestions
      return {
        term_suggester: {
          prefix: query,
          completion: {
            field: 'suggest',
            size: options.size || 10,
            fuzzy: {
              fuzziness: 'AUTO'
            }
          }
        }
      };
    }
  }

  private processSuggesterResponse(response: any, query: string, options: AutocompleteOptions): AutocompleteResult {
    // Implementation details...
  }

  private getIndexForType(type: string): string {
    switch (type) {
      case 'product':
        return 'products';
      case 'category':
        return 'categories';
      default:
        return 'search_terms';
    }
  }
}
```

### Search Suggestions Implementation

Search suggestions combines spell correction and search analytics:

```typescript
@Injectable()
export class SearchSuggestionService {
  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly searchAnalyticsService: SearchAnalyticsService,
    private readonly cacheManager: Cache,
    private readonly logger: Logger,
  ) {}

  async getSuggestions(query: string, options: SearchSuggestionOptions): Promise<SearchSuggestionResult> {
    try {
      const result: SearchSuggestionResult = {
        corrections: [],
        related: []
      };
      
      // Get spell corrections if requested
      if (options.includeCorrections !== false) {
        result.corrections = await this.getSpellCorrections(query);
      }
      
      // Get related terms if requested
      if (options.includeRelated !== false) {
        result.related = await this.getRelatedTerms(query);
      }
      
      return result;
    } catch (error) {
      this.logger.error(`Error getting search suggestions: ${error.message}`, error.stack);
      throw new SuggestionException('Failed to get search suggestions', error);
    }
  }

  private async getSpellCorrections(query: string): Promise<SuggestionTerm[]> {
    // Use Elasticsearch's phrase suggester for spell correction
    const response = await this.elasticsearchService.search({
      index: 'search_terms',
      body: {
        suggest: {
          text: query,
          phrase_suggester: {
            phrase: {
              field: 'text',
              size: 1,
              highlight: {
                pre_tag: '<em>',
                post_tag: '</em>'
              }
            }
          }
        }
      }
    });
    
    // Process spell correction results
    // Implementation details...
  }

  private async getRelatedTerms(query: string): Promise<SuggestionTerm[]> {
    // Use a combination of search analytics and More Like This query
    // Implementation details...
  }
}
```

### Popular Searches Implementation

Popular searches are derived from analytics data:

```typescript
@Injectable()
export class PopularSearchService {
  constructor(
    private readonly searchAnalyticsRepository: SearchAnalyticsRepository,
    private readonly cacheManager: Cache,
    private readonly logger: Logger,
  ) {}

  async getPopularSearches(options: PopularSearchOptions): Promise<PopularSearchResult[]> {
    try {
      // Generate cache key based on options
      const cacheKey = `popular_searches:${JSON.stringify(options)}`;
      
      // Check cache first
      const cachedResult = await this.cacheManager.get<PopularSearchResult[]>(cacheKey);
      if (cachedResult) {
        return cachedResult;
      }
      
      // Calculate date range based on timeframe
      const dateRange = this.calculateDateRange(options.timeframe);
      
      // Query search analytics for popular terms
      const popularTerms = await this.searchAnalyticsRepository.getPopularSearches({
        from: dateRange.from,
        to: dateRange.to,
        context: options.context,
        locale: options.locale,
        limit: options.size || 10
      });
      
      // Format results
      const result = popularTerms.map((term, index) => ({
        text: term.query,
        rank: index + 1,
        search_count: term.count
      }));
      
      // Cache for 1 hour
      await this.cacheManager.set(cacheKey, result, 3600);
      
      return result;
    } catch (error) {
      this.logger.error(`Error getting popular searches: ${error.message}`, error.stack);
      throw new SuggestionException('Failed to get popular searches', error);
    }
  }

  private calculateDateRange(timeframe: string = 'week'): { from: Date, to: Date } {
    const to = new Date();
    let from = new Date();
    
    switch (timeframe) {
      case 'day':
        from.setDate(from.getDate() - 1);
        break;
      case 'month':
        from.setMonth(from.getMonth() - 1);
        break;
      case 'week':
      default:
        from.setDate(from.getDate() - 7);
        break;
    }
    
    return { from, to };
  }
}
```

## Performance Considerations

1. **Completion Suggester**: Elasticsearch's completion suggester provides sub-10ms response times
2. **Aggressive Caching**: Suggestion responses are cached for 5 minutes
3. **Minimal Payload**: Responses only include essential fields for rendering suggestions
4. **Prefetching**: UI can prefetch popular searches on page load
5. **Debouncing**: Client should implement 200-300ms debouncing for autocomplete requests