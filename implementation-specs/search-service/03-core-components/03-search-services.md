# Search Services

## 1. Introduction

Search Services are the core workhorses that orchestrate the search process for specific entities (Products, Categories, Content) or functionalities (Autocomplete). They bridge the gap between the high-level Search Facade and the lower-level Query Builders and Elasticsearch Client.

Each Search Service is responsible for:
- Receiving search parameters from the facade.
- Utilizing the appropriate Query Builder to construct an Elasticsearch query.
- Executing the query via the Elasticsearch Client.
- Employing a Result Processor to transform the raw Elasticsearch response into a structured, application-friendly format.
- Managing caching for search results to improve performance.

## 2. Core Search Services

### 2.1. Product Search Service (`ProductSearchService`)

Handles all search operations related to product documents.

#### Key Features:
- Accepts `ProductSearchParams` (query string, filters, sorting, pagination).
- Uses `ProductQueryBuilder` to generate the Elasticsearch query.
- Interacts with the `ElasticsearchService` (or client wrapper) to execute the search against the products index.
- Employs `ProductResultProcessor` to map Elasticsearch hits to `Product` objects and format aggregations into facets.
- Implements caching logic to store and retrieve search results, reducing load on Elasticsearch and improving response times.
- Handles errors gracefully, logging issues and potentially throwing specific search exceptions.

#### Implementation Example (TypeScript/NestJS)

(Extended from the `00-overview.md` with more details and error handling)

```typescript
import { Injectable, Logger, Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';
import { ElasticsearchService } from '@nestjs/elasticsearch'; // Official Elasticsearch client
import { ProductQueryBuilder } from './query-builders/product-query.builder';
import { ProductResultProcessor } from './result-processors/product-result.processor';
import { ProductSearchParams, ProductSearchResult } from '../models/product-search.model';
import { SearchException } from '../exceptions/search.exception';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class ProductSearchService {
  private readonly logger = new Logger(ProductSearchService.name);
  private readonly productIndex: string;
  private readonly cacheTtl: number;

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly queryBuilder: ProductQueryBuilder,
    private readonly resultProcessor: ProductResultProcessor,
    @Inject(CACHE_MANAGER) private readonly cacheManager: Cache,
    private readonly configService: ConfigService,
  ) {
    this.productIndex = this.configService.get<string>('elasticsearch.indices.products', 'products-v1');
    this.cacheTtl = this.configService.get<number>('cache.ttl.productSearch', 300); // Default 5 mins
  }

  async search(params: ProductSearchParams): Promise<ProductSearchResult> {
    const cacheKey = this.generateCacheKey(params);
    try {
      const cachedResult = await this.cacheManager.get<ProductSearchResult>(cacheKey);
      if (cachedResult) {
        this.logger.debug(`Cache hit for product search: ${cacheKey}`);
        return cachedResult;
      }
      this.logger.debug(`Cache miss for product search: ${cacheKey}. Querying Elasticsearch.`);

      const searchQuery = this.queryBuilder.buildSearchQuery(params);
      this.logger.verbose(`Product search ES query: ${JSON.stringify(searchQuery)}`);

      const searchResponse = await this.elasticsearchService.search({
        index: this.productIndex,
        body: searchQuery,
      });

      const result = this.resultProcessor.processResponse(searchResponse.body, params); // .body contains the response
      
      if (result.items.length > 0 || !params.query) { // Cache results with items or no-query requests
        await this.cacheManager.set(cacheKey, result, this.cacheTtl * 1000); // TTL in ms
        this.logger.debug(`Product search result cached: ${cacheKey}`);
      }

      return result;
    } catch (error) {
      this.logger.error(
        `Error during product search (key: ${cacheKey}): ${error.message}`,
        error.response?.body || error.stack, // Log ES error if available
      );
      if (error.meta?.body?.type === 'index_not_found_exception') {
        throw new SearchException('Product index not found. Please ensure indexing is complete.', error);
      }
      throw new SearchException('Failed to execute product search. Please try again later.', error);
    }
  }

  private generateCacheKey(params: ProductSearchParams): string {
    // Consistent serialization for cache key
    const sortedParams = Object.keys(params)
      .sort()
      .reduce((obj, key) => { 
        obj[key] = params[key]; 
        return obj; 
      }, {});
    return `product_search:${this.productIndex}:${JSON.stringify(sortedParams)}`;
  }

  async getProductById(id: string): Promise<Product | null> {
    const cacheKey = `product_by_id:${this.productIndex}:${id}`;
    try {
      const cachedProduct = await this.cacheManager.get<Product>(cacheKey);
      if (cachedProduct) {
        this.logger.debug(`Cache hit for getProductById: ${id}`);
        return cachedProduct;
      }

      const response = await this.elasticsearchService.get({
        index: this.productIndex,
        id: id,
      });

      if (!response.body.found) return null;
      const product = this.resultProcessor.mapToProduct(response.body);
      await this.cacheManager.set(cacheKey, product, this.cacheTtl * 1000);
      return product;

    } catch (error) {
        if (error.meta?.statusCode === 404) {
            this.logger.warn(`Product with ID ${id} not found in index ${this.productIndex}`);
            return null;
        }
        this.logger.error(`Error fetching product by ID ${id}: ${error.message}`, error.stack);
        throw new SearchException(`Failed to fetch product ${id}.`, error);
    }
  }
}
```

### 2.2. Category Search Service (`CategorySearchService`)

Handles search operations for category documents.

#### Key Features:
- Accepts `CategorySearchParams` (query string, parent ID, sorting).
- Uses `CategoryQueryBuilder`.
- Executes queries against the categories index.
- Employs `CategoryResultProcessor`.
- Implements caching.

#### Implementation Sketch:

```typescript
import { Injectable, Logger, Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { CategoryQueryBuilder } from './query-builders/category-query.builder';
import { CategoryResultProcessor } from './result-processors/category-result.processor';
import { CategorySearchParams, CategorySearchResult, Category } from '../models/category-search.model';
import { SearchException } from '../exceptions/search.exception';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class CategorySearchService {
  private readonly logger = new Logger(CategorySearchService.name);
  private readonly categoryIndex: string;
  private readonly cacheTtl: number;

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly queryBuilder: CategoryQueryBuilder,
    private readonly resultProcessor: CategoryResultProcessor,
    @Inject(CACHE_MANAGER) private readonly cacheManager: Cache,
    private readonly configService: ConfigService,
  ) {
    this.categoryIndex = this.configService.get<string>('elasticsearch.indices.categories', 'categories-v1');
    this.cacheTtl = this.configService.get<number>('cache.ttl.categorySearch', 600); // Default 10 mins, categories change less often
  }

  async search(params: CategorySearchParams): Promise<CategorySearchResult> {
    const cacheKey = `category_search:${this.categoryIndex}:${JSON.stringify(params)}`;
    try {
      const cachedResult = await this.cacheManager.get<CategorySearchResult>(cacheKey);
      if (cachedResult) {
        this.logger.debug(`Cache hit for category search: ${cacheKey}`);
        return cachedResult;
      }

      const searchQuery = this.queryBuilder.buildSearchQuery(params);
      this.logger.verbose(`Category search ES query: ${JSON.stringify(searchQuery)}`);
      
      const searchResponse = await this.elasticsearchService.search({
        index: this.categoryIndex,
        body: searchQuery,
      });

      const result = this.resultProcessor.processResponse(searchResponse.body, params);
      await this.cacheManager.set(cacheKey, result, this.cacheTtl * 1000);
      return result;
    } catch (error) {
      this.logger.error(`Error during category search: ${error.message}`, error.stack);
      throw new SearchException('Failed to execute category search.', error);
    }
  }

  async getCategoryById(id: string): Promise<Category | null> {
    // Similar to getProductById, implement caching and fetching by ID
    return null; // Placeholder
  }

  async getCategoriesByParentId(parentId: string | null, params: Omit<CategorySearchParams, 'parentId' | 'query'>): Promise<CategorySearchResult> {
    // Specific method to fetch children of a category or root categories
    return this.search({ ...params, parentId: parentId === null ? undefined : parentId, fetchRoot: parentId === null });
  }
}
```

### 2.3. Content Search Service (`ContentSearchService`)

Handles search operations for content documents (articles, FAQs, etc.).

#### Key Features:
- Accepts `ContentSearchParams` (query string, content type, tags, sorting).
- Uses `ContentQueryBuilder`.
- Executes queries against the content index.
- Employs `ContentResultProcessor`.
- Implements caching.

#### Implementation Sketch:

```typescript
import { Injectable, Logger, Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { ContentQueryBuilder } from './query-builders/content-query.builder';
import { ContentResultProcessor } from './result-processors/content-result.processor';
import { ContentSearchParams, ContentSearchResult, ContentDoc } from '../models/content-search.model'; // Note: ContentDoc to avoid conflict
import { SearchException } from '../exceptions/search.exception';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class ContentSearchService {
  private readonly logger = new Logger(ContentSearchService.name);
  private readonly contentIndex: string;
  private readonly cacheTtl: number;

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly queryBuilder: ContentQueryBuilder,
    private readonly resultProcessor: ContentResultProcessor,
    @Inject(CACHE_MANAGER) private readonly cacheManager: Cache,
    private readonly configService: ConfigService,
  ) {
    this.contentIndex = this.configService.get<string>('elasticsearch.indices.content', 'content-v1');
    this.cacheTtl = this.configService.get<number>('cache.ttl.contentSearch', 300);
  }

  async search(params: ContentSearchParams): Promise<ContentSearchResult> {
    const cacheKey = `content_search:${this.contentIndex}:${JSON.stringify(params)}`;
    try {
      const cachedResult = await this.cacheManager.get<ContentSearchResult>(cacheKey);
      if (cachedResult) {
        this.logger.debug(`Cache hit for content search: ${cacheKey}`);
        return cachedResult;
      }

      const searchQuery = this.queryBuilder.buildSearchQuery(params);
      this.logger.verbose(`Content search ES query: ${JSON.stringify(searchQuery)}`);

      const searchResponse = await this.elasticsearchService.search({
        index: this.contentIndex,
        body: searchQuery,
      });

      const result = this.resultProcessor.processResponse(searchResponse.body, params);
      await this.cacheManager.set(cacheKey, result, this.cacheTtl * 1000);
      return result;
    } catch (error) {
      this.logger.error(`Error during content search: ${error.message}`, error.stack);
      throw new SearchException('Failed to execute content search.', error);
    }
  }
  
  async getContentById(id: string): Promise<ContentDoc | null> {
    // Similar to getProductById, implement caching and fetching by ID
    return null; // Placeholder
  }
}
```

### 2.4. Autocomplete Service (`AutocompleteService`)

Provides search term suggestions (type-ahead functionality).

#### Key Features:
- Accepts a query string and options (limit, types of suggestions).
- Uses `AutocompleteQueryBuilder` to construct suggester queries.
- Executes queries against relevant indices (products, categories, potentially a dedicated suggestions index).
- Employs `AutocompleteResultProcessor` to format suggestions.
- Implements caching, often with shorter TTLs due to the dynamic nature of suggestions.

#### Implementation Sketch:

```typescript
import { Injectable, Logger, Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { AutocompleteQueryBuilder } from './query-builders/autocomplete-query.builder';
import { AutocompleteResultProcessor } from './result-processors/autocomplete-result.processor';
import { AutocompleteOptions, AutocompleteResult } from '../models/autocomplete.model';
import { SearchException } from '../exceptions/search.exception';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class AutocompleteService {
  private readonly logger = new Logger(AutocompleteService.name);
  private readonly productIndex: string; // May query multiple indices or a dedicated one
  private readonly cacheTtl: number;

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly queryBuilder: AutocompleteQueryBuilder,
    private readonly resultProcessor: AutocompleteResultProcessor,
    @Inject(CACHE_MANAGER) private readonly cacheManager: Cache,
    private readonly configService: ConfigService,
  ) {
    this.productIndex = this.configService.get<string>('elasticsearch.indices.products', 'products-v1');
    this.cacheTtl = this.configService.get<number>('cache.ttl.autocomplete', 60); // Shorter TTL for suggestions
  }

  async getSuggestions(queryText: string, options?: AutocompleteOptions): Promise<AutocompleteResult> {
    const cacheKey = `autocomplete:${this.productIndex}:${queryText}:${JSON.stringify(options || {})}`;
    try {
      const cachedResult = await this.cacheManager.get<AutocompleteResult>(cacheKey);
      if (cachedResult) {
        this.logger.debug(`Cache hit for autocomplete: ${cacheKey}`);
        return cachedResult;
      }

      const suggestQuery = this.queryBuilder.buildSuggestQuery(queryText, options);
      this.logger.verbose(`Autocomplete ES query: ${JSON.stringify(suggestQuery)}`);
      
      // Autocomplete might query a specific index or multiple via an alias
      const searchResponse = await this.elasticsearchService.search({
        index: this.productIndex, // Or a dedicated suggestions index/alias
        body: suggestQuery,
      });

      const result = this.resultProcessor.processResponse(searchResponse.body, queryText, options);
      await this.cacheManager.set(cacheKey, result, this.cacheTtl * 1000);
      return result;
    } catch (error) {
      this.logger.error(`Error during autocomplete for "${queryText}": ${error.message}`, error.stack);
      throw new SearchException('Failed to retrieve autocomplete suggestions.', error);
    }
  }
}
```

## 4. Common Patterns & Best Practices

- **Dependency Injection**: Utilize DI to manage dependencies like query builders, result processors, ES client, and cache manager.
- **Clear Separation**: Each service should be focused on its specific domain (Product, Category, etc.).
- **Configuration-driven**: Index names, cache TTLs, and other operational parameters should be configurable.
- **Robust Caching**: Implement effective caching strategies with appropriate TTLs and cache key generation.
- **Comprehensive Logging**: Log key events, parameters, and errors for monitoring and debugging.
- **Custom Exceptions**: Throw specific exceptions (e.g., `SearchException`, `IndexingException`) to allow for tailored error handling upstream.
- **Asynchronous Operations**: All interactions with Elasticsearch and caching should be asynchronous (`async/await`).

## 5. Interactions

- **Search Facade**: The primary caller of these Search Services.
- **Query Builders**: Used by Search Services to create Elasticsearch queries.
- **Result Processors**: Used by Search Services to format Elasticsearch responses.
- **ElasticsearchService (Client Wrapper)**: Used to execute queries against Elasticsearch.
- **Cache Manager**: Used for storing and retrieving cached search results.
- **ConfigService**: Used to fetch operational configurations like index names and TTLs.

These Search Services form the core logic layer for handling search and autocomplete operations, ensuring a structured and maintainable approach to interacting with the Elasticsearch backend.
