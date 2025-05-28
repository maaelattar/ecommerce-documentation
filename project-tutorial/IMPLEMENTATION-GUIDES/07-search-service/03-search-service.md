# Search Service - Core Implementation with Shared Libraries

## 🎯 Objective
Implement advanced product search functionality using Elasticsearch with shared utilities for logging, authentication, and error handling.

## 🔍 SearchService Implementation

```typescript
// src/search/search.service.ts
import { Injectable } from '@nestjs/common';
import { ElasticsearchService } from '@nestjs/elasticsearch';

// Import shared utilities
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { SearchProductsDto } from './dto/search-products.dto';
import { SearchResultDto } from './dto/search-result.dto';

@Injectable()
export class SearchService {
  private readonly PRODUCT_INDEX = 'products';

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly logger: LoggerService,
  ) {}

  async searchProducts(searchDto: SearchProductsDto): Promise<SearchResultDto> {
    try {
      const query = this.buildSearchQuery(searchDto);
      
      this.logger.log('Executing product search', 'SearchService', {
        query: searchDto.q,
        filters: searchDto.filters,
        page: searchDto.page,
        limit: searchDto.limit,
      });

      const response = await this.elasticsearchService.search({
        index: this.PRODUCT_INDEX,
        body: query,
      });

      const results = this.transformSearchResults(response);

      this.logger.log('Search completed successfully', 'SearchService', {
        query: searchDto.q,
        totalHits: results.total,
        resultsCount: results.products.length,
        took: response.took,
      });

      return results;
    } catch (error) {
      this.logger.error('Search query failed', error, 'SearchService', {
        query: searchDto.q,
        filters: searchDto.filters,
      });
      throw error;
    }
  }

  async getSearchSuggestions(query: string, limit: number = 10): Promise<string[]> {
    try {
      const response = await this.elasticsearchService.search({
        index: this.PRODUCT_INDEX,
        body: {
          suggest: {
            product_suggestions: {
              prefix: query,
              completion: {
                field: 'name.suggest',
                size: limit,
              },
            },
          },
        },
      });

      const suggestions = response.body.suggest.product_suggestions[0].options.map(
        (option: any) => option.text
      );

      this.logger.log('Suggestions generated', 'SearchService', {
        query,
        suggestionsCount: suggestions.length,
      });

      return suggestions;
    } catch (error) {
      this.logger.error('Failed to get suggestions', error, 'SearchService', {
        query,
      });
      return [];
    }
  }

  async getFacets(searchDto: SearchProductsDto): Promise<any> {
    try {
      const baseQuery = this.buildSearchQuery(searchDto, false);
      
      const response = await this.elasticsearchService.search({
        index: this.PRODUCT_INDEX,
        body: {
          ...baseQuery,
          size: 0, // We only want aggregations
          aggs: {
            categories: {
              terms: {
                field: 'category.name',
                size: 20,
              },
            },
            brands: {
              terms: {
                field: 'brand',
                size: 20,
              },
            },
            price_ranges: {
              range: {
                field: 'price',
                ranges: [
                  { to: 50 },
                  { from: 50, to: 100 },
                  { from: 100, to: 200 },
                  { from: 200, to: 500 },
                  { from: 500 },
                ],
              },
            },
            availability: {
              terms: {
                field: 'availability.inStock',
              },
            },
          },
        },
      });

      return this.transformFacets(response.body.aggregations);
    } catch (error) {
      this.logger.error('Failed to get facets', error, 'SearchService');
      return {};
    }
  }

  private buildSearchQuery(searchDto: SearchProductsDto, includePagination: boolean = true) {
    const query: any = {
      query: {
        bool: {
          must: [],
          filter: [],
        },
      },
    };

    // Text search
    if (searchDto.q) {
      query.query.bool.must.push({
        multi_match: {
          query: searchDto.q,
          fields: [
            'name.search^3',
            'name^2',
            'description',
            'brand^1.5',
            'tags',
          ],
          type: 'best_fields',
          fuzziness: 'AUTO',
        },
      });
    } else {
      query.query.bool.must.push({
        match_all: {},
      });
    }

    // Filters
    if (searchDto.filters) {
      if (searchDto.filters.category) {
        query.query.bool.filter.push({
          term: { 'category.name': searchDto.filters.category },
        });
      }

      if (searchDto.filters.brand) {
        query.query.bool.filter.push({
          term: { brand: searchDto.filters.brand },
        });
      }

      if (searchDto.filters.minPrice || searchDto.filters.maxPrice) {
        const priceRange: any = {};
        if (searchDto.filters.minPrice) priceRange.gte = searchDto.filters.minPrice;
        if (searchDto.filters.maxPrice) priceRange.lte = searchDto.filters.maxPrice;
        
        query.query.bool.filter.push({
          range: { price: priceRange },
        });
      }

      if (searchDto.filters.inStock !== undefined) {
        query.query.bool.filter.push({
          term: { 'availability.inStock': searchDto.filters.inStock },
        });
      }
    }

    // Sorting
    query.sort = this.buildSortClause(searchDto.sortBy, searchDto.sortOrder);

    // Pagination
    if (includePagination) {
      query.from = ((searchDto.page || 1) - 1) * (searchDto.limit || 20);
      query.size = searchDto.limit || 20;
    }

    return query;
  }

  private buildSortClause(sortBy?: string, sortOrder?: 'asc' | 'desc') {
    const order = sortOrder || 'desc';
    
    switch (sortBy) {
      case 'price':
        return [{ price: { order } }];
      case 'rating':
        return [{ 'ratings.average': { order } }];
      case 'name':
        return [{ 'name.keyword': { order } }];
      case 'newest':
        return [{ createdAt: { order: 'desc' } }];
      default:
        return [{ _score: { order: 'desc' } }, { createdAt: { order: 'desc' } }];
    }
  }

  private transformSearchResults(response: any): SearchResultDto {
    const hits = response.body.hits;
    
    return {
      products: hits.hits.map((hit: any) => ({
        ...hit._source,
        score: hit._score,
      })),
      total: hits.total.value,
      page: Math.floor(hits.hits.length > 0 ? (hits.from || 0) / hits.hits.length : 0) + 1,
      totalPages: Math.ceil(hits.total.value / (hits.hits.length || 20)),
      took: response.body.took,
    };
  }

  private transformFacets(aggregations: any) {
    return {
      categories: aggregations.categories.buckets.map((bucket: any) => ({
        value: bucket.key,
        count: bucket.doc_count,
      })),
      brands: aggregations.brands.buckets.map((bucket: any) => ({
        value: bucket.key,
        count: bucket.doc_count,
      })),
      priceRanges: aggregations.price_ranges.buckets.map((bucket: any) => ({
        from: bucket.from || 0,
        to: bucket.to || null,
        count: bucket.doc_count,
      })),
      availability: aggregations.availability.buckets.map((bucket: any) => ({
        inStock: bucket.key,
        count: bucket.doc_count,
      })),
    };
  }
}
```