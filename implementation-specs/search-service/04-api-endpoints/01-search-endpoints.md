# Search Endpoints

## Overview

The search endpoints are the core of the Search Service API, providing the ability to search for products, categories, and content. These endpoints support rich querying capabilities including full-text search, faceted navigation, and sorting.

## Product Search

### Endpoint: GET /products

Search for products based on a query string and optional filters.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | No | Search query text |
| `page` | integer | No | Page number (default: 1) |
| `size` | integer | No | Page size (default: 20, max: 100) |
| `sort` | string | No | Sort field and direction (see below) |
| `filter` | object | No | Filtering criteria (see below) |
| `locale` | string | No | Locale for results (default: en-US) |

**Sort Options:**
- `relevance` (default): Sort by search relevance
- `price:asc`: Sort by price (lowest first)
- `price:desc`: Sort by price (highest first)
- `name:asc`: Sort by name (A-Z)
- `name:desc`: Sort by name (Z-A)
- `created:desc`: Sort by creation date (newest first)
- `rating:desc`: Sort by customer rating (highest first)
- `popularity:desc`: Sort by popularity (most popular first)

**Filter Parameters:**
- `filter[category]`: Filter by category ID(s)
- `filter[brand]`: Filter by brand ID(s)
- `filter[price_min]`: Minimum price
- `filter[price_max]`: Maximum price
- `filter[in_stock]`: Filter by stock availability (`true` or `false`)
- `filter[rating_min]`: Minimum rating (1-5)
- `filter[attributes][{code}]`: Filter by attribute values

#### Example Request

```http
GET /search/v1/products?query=bluetooth+headphones&page=1&size=20&sort=price:asc&filter[category]=electronics&filter[price_max]=100&filter[in_stock]=true&filter[attributes][color]=black
```

#### Response

```json
{
  "data": [
    {
      "id": "prod-12345",
      "name": "Wireless Bluetooth Headphones",
      "description": "High-quality wireless headphones with noise cancellation...",
      "sku": "BT-HDPHN-BLK",
      "price": {
        "current": 49.99,
        "original": 79.99,
        "currency": "USD"
      },
      "images": [
        {
          "url": "https://example.com/images/products/headphones-1.jpg",
          "alt": "Wireless Bluetooth Headphones - Front View"
        }
      ],
      "brand": {
        "id": "brand-456",
        "name": "AudioTech"
      },
      "rating": {
        "average": 4.5,
        "count": 128
      },
      "availability": {
        "in_stock": true,
        "quantity": 42
      },
      "url": "https://example.com/products/wireless-bluetooth-headphones"
    },
    // More products...
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 87,
    "pages": 5
  },
  "facets": [
    {
      "code": "category",
      "label": "Category",
      "type": "terms",
      "values": [
        {
          "value": "electronics",
          "label": "Electronics",
          "count": 87,
          "selected": true
        },
        {
          "value": "audio",
          "label": "Audio Equipment",
          "count": 45,
          "selected": false
        }
      ]
    },
    {
      "code": "brand",
      "label": "Brand",
      "type": "terms",
      "values": [
        {
          "value": "audiotech",
          "label": "AudioTech",
          "count": 12,
          "selected": false
        },
        {
          "value": "soundwave",
          "label": "SoundWave",
          "count": 10,
          "selected": false
        }
      ]
    },
    {
      "code": "price",
      "label": "Price",
      "type": "range",
      "values": [
        {
          "from": 0,
          "to": 50,
          "count": 32,
          "selected": false
        },
        {
          "from": 50,
          "to": 100,
          "count": 55,
          "selected": false
        }
      ]
    },
    {
      "code": "attributes.color",
      "label": "Color",
      "type": "terms",
      "values": [
        {
          "value": "black",
          "label": "Black",
          "count": 45,
          "selected": true
        },
        {
          "value": "white",
          "label": "White",
          "count": 23,
          "selected": false
        }
      ]
    }
  ],
  "metadata": {
    "query": "bluetooth headphones",
    "corrected_query": null,
    "execution_time_ms": 87
  }
}
```

### Endpoint: GET /products/{id}

Retrieve a single product by ID with search highlights if a query is provided.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Product ID |
| `query` | string | No | Search query to highlight matches |

#### Example Request

```http
GET /search/v1/products/prod-12345?query=bluetooth
```

#### Response

```json
{
  "data": {
    "id": "prod-12345",
    "name": "Wireless Bluetooth Headphones",
    "description": "High-quality wireless headphones with noise cancellation...",
    // Full product details
    "highlights": {
      "name": ["Wireless <em>Bluetooth</em> Headphones"],
      "description": ["High-quality wireless <em>Bluetooth</em> headphones with noise cancellation..."]
    }
  }
}
```

## Category Search

### Endpoint: GET /categories

Search for product categories.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | No | Search query text |
| `page` | integer | No | Page number (default: 1) |
| `size` | integer | No | Page size (default: 20, max: 100) |
| `parent` | string | No | Filter by parent category ID |
| `level` | integer | No | Filter by category level |

#### Example Request

```http
GET /search/v1/categories?query=electronics&parent=root&level=1
```

#### Response

```json
{
  "data": [
    {
      "id": "cat-123",
      "name": "Electronics",
      "slug": "electronics",
      "level": 1,
      "parent_id": "root",
      "path": "/electronics",
      "product_count": 1250,
      "children_count": 15,
      "image_url": "https://example.com/images/categories/electronics.jpg"
    },
    // More categories...
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 5,
    "pages": 1
  }
}
```

## Content Search

### Endpoint: GET /content

Search for marketing and informational content.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query text |
| `page` | integer | No | Page number (default: 1) |
| `size` | integer | No | Page size (default: 20, max: 100) |
| `type` | string | No | Content type (article, blog, faq, guide) |
| `tags` | string | No | Comma-separated list of content tags |

#### Example Request

```http
GET /search/v1/content?query=headphone+guide&type=article&tags=audio,beginners
```

#### Response

```json
{
  "data": [
    {
      "id": "article-789",
      "title": "Complete Guide to Choosing Headphones",
      "summary": "Learn how to select the perfect headphones for your needs...",
      "content_type": "article",
      "url": "https://example.com/blog/headphone-guide",
      "published_date": "2023-05-15T10:30:00Z",
      "author": "Audio Expert",
      "tags": ["audio", "beginners", "buying-guide"],
      "thumbnail_url": "https://example.com/images/content/headphone-guide.jpg"
    },
    // More content...
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 3,
    "pages": 1
  }
}
```

## Universal Search

### Endpoint: GET /universal

Search across all content types (products, categories, and content).

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query text |
| `types` | string | No | Comma-separated list of types to include (default: all) |
| `limit` | object | No | Maximum results per type (e.g., `limit[products]=5`) |

#### Example Request

```http
GET /search/v1/universal?query=headphones&types=products,content&limit[products]=3&limit[content]=2
```

#### Response

```json
{
  "data": {
    "products": [
      {
        "id": "prod-12345",
        "name": "Wireless Bluetooth Headphones",
        "price": {
          "current": 49.99,
          "currency": "USD"
        },
        "image_url": "https://example.com/images/products/headphones-1-thumb.jpg",
        "url": "https://example.com/products/wireless-bluetooth-headphones"
      },
      // More products (up to limit)...
    ],
    "categories": [
      {
        "id": "cat-456",
        "name": "Headphones",
        "product_count": 87,
        "url": "https://example.com/categories/headphones"
      }
    ],
    "content": [
      {
        "id": "article-789",
        "title": "Complete Guide to Choosing Headphones",
        "content_type": "article",
        "url": "https://example.com/blog/headphone-guide"
      },
      // More content (up to limit)...
    ]
  },
  "metadata": {
    "query": "headphones",
    "results_count": {
      "products": 42,
      "categories": 3,
      "content": 7
    }
  }
}
```

## Implementation Details

### Controller Implementation

```typescript
@Controller('products')
export class ProductSearchController {
  constructor(
    private readonly searchFacade: SearchFacade,
    private readonly logger: Logger,
  ) {}

  @Get()
  async searchProducts(
    @Query() queryParams: ProductSearchQueryParams
  ): Promise<SearchResponse<Product>> {
    this.logger.debug(`Searching products with params: ${JSON.stringify(queryParams)}`);
    
    // Transform API query params to internal search params
    const searchParams = this.transformQueryParams(queryParams);
    
    // Execute search
    const result = await this.searchFacade.searchProducts(searchParams);
    
    // Transform internal result to API response format
    return this.transformSearchResult(result);
  }

  @Get(':id')
  async getProduct(
    @Param('id') id: string,
    @Query('query') query?: string
  ): Promise<SingleProductResponse> {
    this.logger.debug(`Retrieving product ${id} with query: ${query}`);
    
    const product = await this.searchFacade.getProductById(id, query);
    
    if (!product) {
      throw new NotFoundException(`Product with ID ${id} not found`);
    }
    
    return {
      data: product
    };
  }

  private transformQueryParams(queryParams: ProductSearchQueryParams): ProductSearchParams {
    // Implementation details...
  }

  private transformSearchResult(result: SearchResult<Product>): SearchResponse<Product> {
    // Implementation details...
  }
}
```

### Service Implementation

```typescript
@Injectable()
export class SearchFacade {
  constructor(
    private readonly productSearchService: ProductSearchService,
    private readonly categorySearchService: CategorySearchService,
    private readonly contentSearchService: ContentSearchService,
    private readonly universalSearchService: UniversalSearchService,
    private readonly logger: Logger,
  ) {}

  async searchProducts(params: ProductSearchParams): Promise<SearchResult<Product>> {
    try {
      return await this.productSearchService.search(params);
    } catch (error) {
      this.logger.error(`Error searching products: ${error.message}`, error.stack);
      throw new SearchException('Failed to search products', error);
    }
  }

  async getProductById(id: string, query?: string): Promise<Product | null> {
    try {
      return await this.productSearchService.getById(id, query);
    } catch (error) {
      this.logger.error(`Error getting product ${id}: ${error.message}`, error.stack);
      throw new SearchException(`Failed to get product ${id}`, error);
    }
  }

  // Additional methods for other search endpoints...
}
```

## Error Responses

### Not Found (404)

```json
{
  "errors": [
    {
      "code": "NOT_FOUND",
      "message": "Product with ID 'prod-12345' not found"
    }
  ]
}
```

### Invalid Parameters (400)

```json
{
  "errors": [
    {
      "code": "INVALID_PARAM",
      "message": "Invalid price range",
      "field": "filter.price_max",
      "details": "Price maximum must be greater than minimum"
    }
  ]
}
```

### Rate Limit Exceeded (429)

```json
{
  "errors": [
    {
      "code": "RATE_LIMITED",
      "message": "Rate limit exceeded",
      "details": "Limit of 20 requests per minute. Try again in 30 seconds."
    }
  ]
}
```

## Performance Considerations

1. **Caching**: Responses are cached for 5 minutes by default
2. **Result Limiting**: Default page size is 20 items to optimize response time
3. **Field Selection**: Use `fields` parameter to request only needed fields
4. **Query Timeout**: Queries have a 3-second timeout to prevent long-running searches