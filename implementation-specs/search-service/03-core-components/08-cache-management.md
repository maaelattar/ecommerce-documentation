# Cache Management

## 1. Introduction

Cache Management within the Search Service is crucial for optimizing performance, reducing latency, and minimizing the load on the Elasticsearch cluster. By caching frequently accessed search results and autocomplete suggestions, the service can respond much faster to repeat requests.

This component outlines the strategies and implementation details for caching within the Search Service, typically leveraging an in-memory cache (like a local cache within a NestJS module) or a distributed cache (like Redis or Memcached) for multi-instance deployments.

## 2. Responsibilities

- **Cache Storage**: Store search results, autocomplete suggestions, and potentially other data (e.g., heavily accessed individual documents like popular products or categories) in a cache.
- **Cache Retrieval**: Retrieve data from the cache if available, bypassing a potentially expensive Elasticsearch query.
- **Cache Key Generation**: Implement a consistent and effective strategy for generating unique cache keys based on request parameters.
- **Cache Invalidation/Eviction**: Define strategies for cache invalidation or eviction:
    - **Time-To-Live (TTL)**: Automatically evict cache entries after a specified duration.
    - **Event-Driven Invalidation**: Invalidate specific cache entries when underlying data changes (e.g., a product update event invalidates related product search caches).
    - **Manual Invalidation**: Provide mechanisms for administrators to manually clear caches if needed.
- **Cache Configuration**: Allow configuration of cache behavior (e.g., TTLs for different data types, cache size limits, choice of cache store).
- **Conditional Caching**: Decide when to cache results (e.g., only cache successful responses, or cache responses with items, avoid caching for highly dynamic or personalized queries if the hit rate is low).

## 3. Cacheable Components & Data

- **Search Results**: Responses from `ProductSearchService`, `CategorySearchService`, `ContentSearchService`.
- **Autocomplete Suggestions**: Responses from `AutocompleteService`.
- **Individual Entities**: Frequently accessed single documents (e.g., `ProductService.getProductById`) can also be cached.
- **Aggregations/Facets**: If facets are relatively stable, they can be cached, though they are typically part of the search result cache.

## 4. Implementation Strategy (NestJS using `@nestjs/cache-manager`)

NestJS provides a flexible `CacheModule` (`@nestjs/cache-manager`) that supports various cache stores (in-memory, Redis via `cache-manager-redis-store`, etc.) and can be easily integrated into services.

### 4.1. Cache Module Setup

```typescript
// src/cache/cache.config.module.ts
import { Module, Global } from '@nestjs/common';
import { CacheModule as NestCacheModule, CacheStore } from '@nestjs/cache-manager';
import { ConfigModule, ConfigService } from '@nestjs/config';
import * as redisStore from 'cache-manager-redis-store'; // For Redis

@Global() // Make CacheModule available globally
@Module({
  imports: [
    NestCacheModule.registerAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => {
        const cacheStoreType = configService.get<string>('CACHE_STORE_TYPE', 'memory');
        const defaultTtl = configService.get<number>('CACHE_DEFAULT_TTL_SECONDS', 300); // Default 5 minutes

        if (cacheStoreType === 'redis') {
          return {
            store: (redisStore as unknown) as CacheStore, // Type assertion might be needed
            host: configService.get<string>('REDIS_HOST', 'localhost'),
            port: configService.get<number>('REDIS_PORT', 6379),
            password: configService.get<string>('REDIS_PASSWORD'),
            db: configService.get<number>('REDIS_DB', 0),
            ttl: defaultTtl, // Default TTL for Redis entries
            // ... other Redis options
          };
        }
        
        // Default to in-memory store
        return {
          store: 'memory',
          max: configService.get<number>('CACHE_MEMORY_MAX_ITEMS', 1000), // Max items in memory cache
          ttl: defaultTtl,
        };
      },
      inject: [ConfigService],
    }),
  ],
  exports: [NestCacheModule], // Export to make Cache objects injectable
})
export class CacheConfigModule {}
```

### 4.2. Usage in Services

Services inject the `Cache` object (from `cache-manager`) to interact with the cache.

```typescript
// Example in ProductSearchService.ts
import { Injectable, Logger, Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager'; // Correct import for CACHE_MANAGER token
import { Cache } from 'cache-manager'; // Type for injected cache instance
import { ProductSearchParams, ProductSearchResult } from '../models/product-search.model';
import { ConfigService } from '@nestjs/config';
// ... other imports (ElasticsearchService, ProductQueryBuilder, ProductResultProcessor)

@Injectable()
export class ProductSearchService {
  private readonly logger = new Logger(ProductSearchService.name);
  private readonly cacheTtlProductSearch: number;

  constructor(
    // ... other dependencies
    @Inject(CACHE_MANAGER) private readonly cacheManager: Cache,
    private readonly configService: ConfigService,
  ) {
    this.cacheTtlProductSearch = this.configService.get<number>('cache.ttl.productSearch', 300); // seconds
  }

  async search(params: ProductSearchParams): Promise<ProductSearchResult> {
    const cacheKey = this.generateCacheKey('product_search', params);
    try {
      const cachedResult = await this.cacheManager.get<ProductSearchResult>(cacheKey);
      if (cachedResult) {
        this.logger.debug(`Cache HIT for product search: ${cacheKey}`);
        return cachedResult;
      }
      this.logger.debug(`Cache MISS for product search: ${cacheKey}`);

      // ... (logic to build query, call Elasticsearch, process results) ...
      // const result = this.resultProcessor.processResponse(...);
      const result: ProductSearchResult = {} as ProductSearchResult; // Placeholder for actual result

      if (result.items.length > 0 || !params.query) { // Example: Cache if results or no specific query
        await this.cacheManager.set(cacheKey, result, this.cacheTtlProductSearch * 1000); // TTL in ms for cache-manager v4+
        this.logger.debug(`Product search result CACHED: ${cacheKey} for ${this.cacheTtlProductSearch}s`);
      }
      return result;
    } catch (error) {
      // ... error handling ...
      throw error;
    }
  }

  private generateCacheKey(prefix: string, params: any): string {
    // Ensure consistent key generation: sort keys, stringify, then hash or use directly.
    const sortedParams = Object.keys(params)
      .sort()
      .reduce((obj, key) => { 
        obj[key] = params[key]; 
        return obj; 
      }, {});
    return `${prefix}:${this.configService.get('elasticsearch.indices.products')}:${JSON.stringify(sortedParams)}`;
  }

  // Method for cache invalidation (example)
  async invalidateProductCache(productId: string) {
    // This is complex. Naive approach: clear all product search cache (too broad).
    // Better: Use tags if cache store supports it (e.g., Redis with custom logic), or delete specific keys if knowable.
    // For simplicity, often rely on TTL or event-driven invalidation of specific item caches.
    this.logger.warn(`Product cache invalidation requested for ${productId} - strategy needs refinement.`);
    // Example: If caching individual products by ID
    const itemCacheKey = this.generateCacheKey('product_by_id', { id: productId });
    await this.cacheManager.del(itemCacheKey);
    this.logger.log(`Deleted cache for individual product: ${itemCacheKey}`);
    
    // Invalidating search results containing this product is harder without tags.
    // Consider shorter TTLs for searches if event-driven invalidation is too complex.
  }
}
```

## 5. Cache Key Generation Strategies

- **Consistency is Key**: The same set of parameters must always produce the same cache key.
- **Serialization**: Sort object keys before JSON stringification to ensure consistency (e.g., `{a:1, b:2}` and `{b:2, a:1}` should produce the same key).
- **Include All Relevant Parameters**: The key should incorporate all parameters that affect the search result (query string, filters, sort order, pagination, index name/alias).
- **Prefixing**: Use prefixes to namespace keys (e.g., `prod_search:`, `cat_suggest:`) to avoid collisions and allow for targeted invalidation if possible.
- **Hashing (Optional)**: For very long keys, consider hashing (e.g., MD5, SHA1) the stringified parameters, but be mindful of potential (though rare) collisions.

## 6. Cache Invalidation Strategies

- **Time-To-Live (TTL)**: Simplest approach. Each cache entry expires after a set duration. Suitable for data that can tolerate some staleness.
    - _Pros_: Easy to implement.
    - _Cons_: Data can be stale until TTL expires. Finding optimal TTL can be tricky.

- **Event-Driven Invalidation**: When data changes (e.g., a `product.updated` event), attempt to invalidate relevant cache entries.
    - _Pros_: Fresher data.
    - _Cons_: Can be complex to implement correctly. Identifying all affected cache keys for a given data change is challenging without tagging or pattern-based deletion. For instance, updating a product means many different search result caches *could* contain it.
    - _Common Approach_: Invalidate caches for specific items (e.g., `product_by_id:123`). For list/search results, often rely on shorter TTLs or accept some staleness.

- **LRU (Least Recently Used)**: If using an in-memory store with a max item limit, LRU is a common eviction policy.

- **Admin API for Cache Clearing**: Provide an administrative endpoint to manually clear all caches or specific cache namespaces, useful during deployments or troubleshooting.

## 7. Cache Store Considerations

- **In-Memory Cache** (e.g., `cache-manager` default, NodeCache):
    - _Pros_: Very fast, no network latency, simple setup.
    - _Cons_: Cache is local to each application instance (not shared in a distributed setup). Cache lost on application restart. Limited by instance memory.
    - _Use Cases_: Single-instance deployments, development, caching very frequently accessed non-shared data.

- **Distributed Cache** (e.g., Redis, Memcached):
    - _Pros_: Shared across all application instances. Persistent (Redis can persist to disk). Scalable. Supports advanced features (e.g., pub/sub for invalidation with Redis).
    - _Cons_: Adds a network hop (higher latency than in-memory). Requires separate infrastructure.
    - _Use Cases_: Multi-instance production deployments, when cache consistency across instances is needed.

## 8. Monitoring Cache Performance

- **Hit Rate**: Percentage of requests served from the cache.
- **Miss Rate**: Percentage of requests that bypass the cache and hit Elasticsearch.
- **Cache Size/Memory Usage**: Monitor memory consumption, especially for in-memory caches.
- **Evictions/Invalidations**: Track how often items are evicted or invalidated.
- **Latency**: Measure average response times for cached vs. non-cached requests.

## 9. Best Practices

- **Configure TTLs Appropriately**: Balance data freshness with performance gains. Autocomplete might have shorter TTLs (e.g., 1-5 minutes) than general search results (e.g., 5-15 minutes) or category listings (e.g., 30-60 minutes).
- **Cache Selectively**: Don't cache everything. Highly dynamic or personalized results with low re-access probability might not benefit from caching.
- **Error Handling**: If the cache store fails, gracefully fall back to querying Elasticsearch directly. Don't let cache failures bring down the search functionality.
- **Cache Key Granularity**: Be mindful of key granularity. Too fine-grained might lead to low hit rates; too coarse might lead to excessive invalidations or staleness.
- **Test Caching Behavior**: Thoroughly test cache hits, misses, and invalidation logic.

Effective cache management is a cornerstone of a high-performance Search Service, significantly enhancing user experience by providing faster responses and reducing the operational load on backend systems.
