# Core Components Overview

## Introduction

This section outlines the core components of the Search Service. These components work together to deliver fast, relevant, and feature-rich search capabilities for the e-commerce platform. The architecture is designed to be modular, maintainable, and scalable.

## Component Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        Search Service API                          │
└───────────┬───────────────────────────────────────────┬───────────┘
            │                                           │
            ▼                                           ▼
┌───────────────────────┐                   ┌───────────────────────┐
│   Search Facade       │                   │   Admin Facade        │
└───────────┬───────────┘                   └───────────┬───────────┘
            │                                           │
            ▼                                           ▼
┌───────────────────────┐                   ┌───────────────────────┐
│  Query Builder        │                   │  Index Management     │
│  - Product Query      │                   │  - Create Index       │
│  - Category Query     │                   │  - Update Mapping     │
│  - Autocomplete Query │                   │  - Reindex            │
└───────────┬───────────┘                   └───────────┬───────────┘
            │                                           │
            ▼                                           ▼
┌───────────────────────┐                   ┌───────────────────────┐
│  Search Service       │                   │  Indexing Service     │
│  - Execute Query      │                   │  - Process Events     │
│  - Process Results    │                   │  - Bulk Index         │
│  - Apply Filters      │                   │  - Update Documents   │
└───────────┬───────────┘                   └───────────┬───────────┘
            │                                           │
            ▼                                           ▼
┌───────────────────────┐                   ┌───────────────────────┐
│  Result Processor     │                   │  Event Consumer       │
│  - Format Results     │                   │  - Consume Kafka      │
│  - Apply Scoring      │                   │  - Transform Events   │
│  - Generate Facets    │                   │  - Queue Documents    │
└───────────┬───────────┘                   └───────────┬───────────┘
            │                                           │
            ▼                                           ▼
┌───────────────────────────────────────────────────────────────────┐
│                     Elasticsearch Client                           │
└───────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Search Facade

The Search Facade provides a simplified interface for the API layer to interact with the search functionality:

```typescript
@Injectable()
export class SearchFacade {
  constructor(
    private readonly productSearchService: ProductSearchService,
    private readonly categorySearchService: CategorySearchService,
    private readonly autocompleteService: AutocompleteService,
    private readonly logger: Logger,
  ) {}

  async searchProducts(params: ProductSearchParams): Promise<SearchResult<Product>> {
    this.logger.debug(`Searching products with params: ${JSON.stringify(params)}`);
    return this.productSearchService.search(params);
  }

  async searchCategories(params: CategorySearchParams): Promise<SearchResult<Category>> {
    this.logger.debug(`Searching categories with params: ${JSON.stringify(params)}`);
    return this.categorySearchService.search(params);
  }

  async getAutocomplete(query: string, options: AutocompleteOptions): Promise<AutocompleteResult> {
    this.logger.debug(`Getting autocomplete for query: ${query}`);
    return this.autocompleteService.getSuggestions(query, options);
  }
}
```

### 2. Query Builder

The Query Builder constructs Elasticsearch query DSL objects based on search parameters:

```typescript
@Injectable()
export class ProductQueryBuilder {
  buildSearchQuery(params: ProductSearchParams): SearchQuery {
    const query = {
      bool: {
        must: [],
        filter: [],
        should: [],
        must_not: []
      }
    };

    // Add text search
    if (params.query) {
      query.bool.must.push({
        multi_match: {
          query: params.query,
          fields: [
            'name^3',
            'description',
            'short_description^2',
            'attributes.*.value_text',
            'brand.name^2',
            'categories.name',
            'search_data.search_keywords'
          ],
          type: 'best_fields',
          fuzziness: 'AUTO'
        }
      });
    }

    // Add filters
    this.addStatusFilter(query, params);
    this.addCategoryFilter(query, params);
    this.addPriceFilter(query, params);
    this.addAttributeFilters(query, params);
    this.addBrandFilter(query, params);
    this.addRatingFilter(query, params);
    this.addAvailabilityFilter(query, params);

    // Add sorting
    const sort = this.buildSortClauses(params);

    return {
      query,
      sort,
      from: params.from || 0,
      size: params.size || 20,
      aggs: this.buildAggregations(params)
    };
  }

  // Helper methods for filter building
  private addStatusFilter(query: any, params: ProductSearchParams): void {
    query.bool.filter.push({
      term: {
        status: 'active'
      }
    });
    
    query.bool.filter.push({
      term: {
        visibility: 'visible'
      }
    });
  }

  // Additional filter methods...

  private buildSortClauses(params: ProductSearchParams): any[] {
    const sort = [];
    
    switch (params.sort) {
      case 'price_asc':
        sort.push({ 'pricing.list_price': { order: 'asc' } });
        break;
      case 'price_desc':
        sort.push({ 'pricing.list_price': { order: 'desc' } });
        break;
      case 'name_asc':
        sort.push({ 'name.keyword': { order: 'asc' } });
        break;
      case 'name_desc':
        sort.push({ 'name.keyword': { order: 'desc' } });
        break;
      case 'newest':
        sort.push({ 'created_at': { order: 'desc' } });
        break;
      case 'rating':
        sort.push({ 'ratings.average': { order: 'desc' } });
        break;
      case 'relevance':
      default:
        // For relevance, rely on the _score
        sort.push({ '_score': { order: 'desc' } });
        // Add secondary sort by popularity
        sort.push({ 'search_data.popularity_score': { order: 'desc' } });
    }
    
    return sort;
  }

  private buildAggregations(params: ProductSearchParams): any {
    // Define aggregations for faceted navigation
    return {
      categories: {
        terms: {
          field: 'categories.name.keyword',
          size: 50
        }
      },
      brands: {
        terms: {
          field: 'brand.name.keyword',
          size: 50
        }
      },
      price_ranges: {
        range: {
          field: 'pricing.list_price',
          ranges: [
            { to: 25 },
            { from: 25, to: 50 },
            { from: 50, to: 100 },
            { from: 100, to: 200 },
            { from: 200 }
          ]
        }
      },
      attributes: {
        nested: {
          path: 'attributes.custom_attributes'
        },
        aggs: {
          filterable: {
            filter: {
              term: {
                'attributes.custom_attributes.filterable': true
              }
            },
            aggs: {
              attribute_codes: {
                terms: {
                  field: 'attributes.custom_attributes.code.keyword',
                  size: 20
                },
                aggs: {
                  attribute_values: {
                    terms: {
                      field: 'attributes.custom_attributes.value_text.keyword',
                      size: 50
                    }
                  }
                }
              }
            }
          }
        }
      }
    };
  }
}
```

### 3. Search Service

The Search Service executes queries against Elasticsearch and processes the raw results:

```typescript
@Injectable()
export class ProductSearchService {
  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly queryBuilder: ProductQueryBuilder,
    private readonly resultProcessor: ProductResultProcessor,
    private readonly cacheManager: Cache,
    private readonly logger: Logger,
  ) {}

  async search(params: ProductSearchParams): Promise<SearchResult<Product>> {
    try {
      // Check cache for identical search
      const cacheKey = this.generateCacheKey(params);
      const cachedResult = await this.cacheManager.get<SearchResult<Product>>(cacheKey);
      
      if (cachedResult) {
        this.logger.debug(`Cache hit for search: ${cacheKey}`);
        return cachedResult;
      }
      
      // Build query
      const searchQuery = this.queryBuilder.buildSearchQuery(params);
      
      // Execute search
      const searchResponse = await this.elasticsearchService.search({
        index: 'products',
        body: searchQuery,
      });
      
      // Process results
      const result = this.resultProcessor.processResponse(searchResponse, params);
      
      // Cache result
      await this.cacheManager.set(cacheKey, result, 300); // 5 minutes TTL
      
      return result;
    } catch (error) {
      this.logger.error(`Error during product search: ${error.message}`, error.stack);
      throw new SearchException('Failed to execute product search', error);
    }
  }

  private generateCacheKey(params: ProductSearchParams): string {
    return `product_search:${JSON.stringify(params)}`;
  }
}
```

### 4. Result Processor

The Result Processor transforms Elasticsearch responses into application-specific result objects:

```typescript
@Injectable()
export class ProductResultProcessor {
  processResponse(searchResponse: any, params: ProductSearchParams): SearchResult<Product> {
    const hits = searchResponse.hits.hits;
    const total = searchResponse.hits.total.value;
    
    // Map ES documents to Product objects
    const products = hits.map(hit => this.mapToProduct(hit));
    
    // Process aggregations into facets
    const facets = this.processFacets(searchResponse.aggregations, params);
    
    return {
      items: products,
      total,
      page: Math.floor(params.from / params.size) + 1,
      size: params.size,
      pages: Math.ceil(total / params.size),
      facets,
      query: params.query
    };
  }

  private mapToProduct(hit: any): Product {
    const source = hit._source;
    
    // Transform Elasticsearch document to Product
    return {
      id: source.id,
      sku: source.sku,
      name: source.name,
      description: source.description,
      shortDescription: source.short_description,
      // Map all other fields...
      score: hit._score,
      highlight: hit.highlight
    };
  }

  private processFacets(aggregations: any, params: ProductSearchParams): Facet[] {
    if (!aggregations) return [];
    
    const facets: Facet[] = [];
    
    // Process category facets
    if (aggregations.categories) {
      facets.push({
        code: 'category',
        label: 'Category',
        type: 'terms',
        values: aggregations.categories.buckets.map(bucket => ({
          value: bucket.key,
          count: bucket.doc_count,
          selected: params.category?.includes(bucket.key) || false
        }))
      });
    }
    
    // Process other facets...
    
    return facets;
  }
}
```

### 5. Indexing Service

The Indexing Service handles document indexing operations:

```typescript
@Injectable()
export class ProductIndexingService {
  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly logger: Logger,
  ) {}

  async indexProduct(product: ProductDocument): Promise<void> {
    try {
      await this.elasticsearchService.index({
        index: 'products',
        id: product.id,
        body: product,
      });
      
      this.logger.debug(`Indexed product ${product.id}`);
    } catch (error) {
      this.logger.error(`Error indexing product ${product.id}: ${error.message}`, error.stack);
      throw new IndexingException(`Failed to index product: ${error.message}`);
    }
  }

  async bulkIndexProducts(products: ProductDocument[]): Promise<BulkIndexResult> {
    try {
      const operations = products.flatMap(product => [
        { index: { _index: 'products', _id: product.id } },
        product
      ]);
      
      const response = await this.elasticsearchService.bulk({
        refresh: true,
        body: operations,
      });
      
      const result = this.processBulkResponse(response);
      
      this.logger.debug(`Bulk indexed ${result.successful} products, ${result.failed} failures`);
      
      return result;
    } catch (error) {
      this.logger.error(`Error during bulk indexing: ${error.message}`, error.stack);
      throw new IndexingException(`Failed to bulk index products: ${error.message}`);
    }
  }

  async updateProduct(productId: string, updateDoc: Partial<ProductDocument>): Promise<void> {
    try {
      await this.elasticsearchService.update({
        index: 'products',
        id: productId,
        body: {
          doc: updateDoc
        }
      });
      
      this.logger.debug(`Updated product ${productId}`);
    } catch (error) {
      this.logger.error(`Error updating product ${productId}: ${error.message}`, error.stack);
      throw new IndexingException(`Failed to update product: ${error.message}`);
    }
  }

  async deleteProduct(productId: string): Promise<void> {
    try {
      await this.elasticsearchService.delete({
        index: 'products',
        id: productId
      });
      
      this.logger.debug(`Deleted product ${productId}`);
    } catch (error) {
      this.logger.error(`Error deleting product ${productId}: ${error.message}`, error.stack);
      throw new IndexingException(`Failed to delete product: ${error.message}`);
    }
  }

  private processBulkResponse(response: any): BulkIndexResult {
    const items = response.items || [];
    const failed = items.filter(item => item.index?.error).length;
    
    return {
      successful: items.length - failed,
      failed,
      errors: items
        .filter(item => item.index?.error)
        .map(item => ({
          id: item.index._id,
          reason: item.index.error.reason
        }))
    };
  }
}
```

### 6. Event Consumer

The Event Consumer processes events from Kafka to keep the search index in sync:

```typescript
@Injectable()
export class ProductEventConsumer {
  constructor(
    private readonly productIndexingService: ProductIndexingService,
    private readonly productTransformer: ProductTransformer,
    private readonly logger: Logger,
  ) {}

  @OnEvent('product.created')
  async handleProductCreated(event: ProductCreatedEvent): Promise<void> {
    try {
      const productDocument = this.productTransformer.transformToDocument(event.product);
      await this.productIndexingService.indexProduct(productDocument);
    } catch (error) {
      this.logger.error(
        `Error processing product.created event for ${event.product.id}: ${error.message}`,
        error.stack
      );
      // Handle error (retry, DLQ, etc.)
    }
  }

  @OnEvent('product.updated')
  async handleProductUpdated(event: ProductUpdatedEvent): Promise<void> {
    try {
      const productDocument = this.productTransformer.transformToDocument(event.product);
      await this.productIndexingService.updateProduct(event.product.id, productDocument);
    } catch (error) {
      this.logger.error(
        `Error processing product.updated event for ${event.product.id}: ${error.message}`,
        error.stack
      );
      // Handle error (retry, DLQ, etc.)
    }
  }

  @OnEvent('product.deleted')
  async handleProductDeleted(event: ProductDeletedEvent): Promise<void> {
    try {
      await this.productIndexingService.deleteProduct(event.productId);
    } catch (error) {
      this.logger.error(
        `Error processing product.deleted event for ${event.productId}: ${error.message}`,
        error.stack
      );
      // Handle error (retry, DLQ, etc.)
    }
  }
}
```

## Component Documentation

Detailed documentation for each component is available in the corresponding files:

1. [Search Facade](./01-search-facade.md)
2. [Query Builders](./02-query-builders.md)
3. [Search Services](./03-search-services.md)
4. [Result Processors](./04-result-processors.md)
5. [Indexing Service](./05-indexing-service.md)
6. [Event Consumers](./06-event-consumers.md)
7. [Elasticsearch Client](./07-elasticsearch-client.md)
8. [Cache Management](./08-cache-management.md)

## Component Relationships

- **Search Facade** uses **Search Services** to execute searches
- **Search Services** use **Query Builders** to construct queries and **Result Processors** to format results
- **Query Builders** create Elasticsearch DSL queries based on search parameters
- **Result Processors** transform Elasticsearch responses into domain objects
- **Indexing Service** uses the **Elasticsearch Client** to index documents
- **Event Consumers** use the **Indexing Service** to keep the index in sync

## Error Handling Strategy

1. **Graceful Degradation**: If Elasticsearch is unavailable, fall back to basic functionality
2. **Retry Mechanisms**: Implement automatic retries for transient failures
3. **Circuit Breaker**: Prevent cascading failures when Elasticsearch is experiencing issues
4. **Detailed Logging**: Log all errors with context for troubleshooting
5. **Monitoring**: Set up alerts for repeated errors