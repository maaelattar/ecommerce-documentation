# Query Builders

## 1. Introduction

Query Builders are responsible for translating application-specific search parameters and criteria into valid Elasticsearch Query DSL (Domain Specific Language) objects. Each major searchable entity (Product, Category, Content) and the autocomplete functionality will have its own dedicated Query Builder to handle its specific fields, relevance logic, and aggregation requirements.

This component is crucial for abstracting the complexities of Elasticsearch's query language from the rest of the application, allowing services to request searches using simpler, domain-oriented parameters.

## 2. Responsibilities

- **Query Construction**: Dynamically build complex Elasticsearch queries (boolean queries, multi-match, term, range, nested, etc.) based on input parameters.
- **Filter Application**: Incorporate various filters (e.g., category, brand, price range, attributes, status).
- **Sorting Logic**: Implement sorting based on relevance, price, name, date, or custom criteria.
- **Aggregation Definition**: Define aggregations required for faceted navigation and result analytics.
- **Pagination**: Set `from` and `size` parameters for query pagination.
- **Relevance Tuning**: Apply boosts to specific fields or query clauses to influence search result ranking.
- **Handling Special Queries**: Construct queries for specific use cases like autocomplete suggestions or "more like this" functionality.

## 3. Core Query Builders

### 3.1. Product Query Builder (`ProductQueryBuilder`)

Builds queries for searching product documents.

#### Key Features:
- Handles text search across fields like `name`, `description`, `sku`, `brand.name`, `categories.name`, `attributes.custom_attributes.value_text`, `search_data.search_keywords`.
- Applies filters for status, visibility, category, brand, price range, ratings, availability, and custom attributes.
- Implements sorting by relevance (`_score`), price, name, newest, rating, and popularity.
- Defines aggregations for categories, brands, price ranges, and filterable attributes to support faceted navigation.
- Supports fuzziness for text queries to handle typos.

#### Implementation Example (TypeScript/NestJS)

(Extended from the `00-overview.md` with more details and helper methods)

```typescript
import { Injectable } from '@nestjs/common';
import { ProductSearchParams } from '../models/product-search.model'; // Define this model
import { SearchQuery } from '../models/search-query.model'; // Define this model

@Injectable()
export class ProductQueryBuilder {
  buildSearchQuery(params: ProductSearchParams): SearchQuery {
    const esQuery: any = {
      bool: {
        must: [],
        filter: [],
        should: [],
        must_not: [],
      },
    };

    // 1. Text Search (Main Query)
    if (params.query && params.query.trim() !== '') {
      esQuery.bool.must.push({
        multi_match: {
          query: params.query,
          fields: [
            'name^3', // Boost name field
            'short_description^2',
            'description',
            'sku.text^1.5',
            'brand.name^2',
            'categories.name^1.5',
            'tags^1.5',
            'attributes.custom_attributes.value_text',
            'search_data.search_keywords^1.2',
          ],
          type: 'best_fields', // Most relevant field wins
          fuzziness: 'AUTO',    // Allow for typos
          minimum_should_match: '75%',
        },
      });
    }

    // 2. Standard Filters (always apply)
    this.addStatusAndVisibilityFilters(esQuery, params.includeAdminFilters);

    // 3. User-Defined Filters
    if (params.filters) {
      this.addCategoryFilter(esQuery, params.filters.categoryIds);
      this.addBrandFilter(esQuery, params.filters.brandIds);
      this.addPriceFilter(esQuery, params.filters.priceMin, params.filters.priceMax);
      this.addRatingFilter(esQuery, params.filters.minRating);
      this.addInStockFilter(esQuery, params.filters.inStock);
      this.addAttributeFilters(esQuery, params.filters.attributes);
    }

    // 4. Sorting
    const sortClauses = this.buildSortClauses(params.sort, params.query);

    // 5. Aggregations for Facets
    const aggregations = this.buildAggregations(params.includeAggregations !== false);

    return {
      query: esQuery,
      sort: sortClauses,
      from: params.page && params.pageSize ? (params.page - 1) * params.pageSize : 0,
      size: params.pageSize || 20,
      aggs: aggregations,
      ...(params.query && params.query.trim() !== '' && { suggest: this.buildSuggestQuery(params.query) }),
      highlight: this.buildHighlightConfiguration(),
    };
  }

  private addStatusAndVisibilityFilters(esQuery: any, includeAdminFilters?: boolean): void {
    if (!includeAdminFilters) {
        esQuery.bool.filter.push({ term: { status: 'active' } });
        esQuery.bool.filter.push({ term: { visibility: 'visible' } });
    } else {
        // Potentially allow searching for inactive/hidden if admin
    }
  }

  private addCategoryFilter(esQuery: any, categoryIds?: string[]): void {
    if (categoryIds && categoryIds.length > 0) {
      esQuery.bool.filter.push({
        nested: {
          path: 'categories',
          query: {
            terms: { 'categories.id': categoryIds },
          },
        },
      });
    }
  }

  private addBrandFilter(esQuery: any, brandIds?: string[]): void {
    if (brandIds && brandIds.length > 0) {
      esQuery.bool.filter.push({ terms: { 'brand.id': brandIds } });
    }
  }

  private addPriceFilter(esQuery: any, minPrice?: number, maxPrice?: number): void {
    const priceQuery: any = {};
    if (minPrice !== undefined) priceQuery.gte = minPrice;
    if (maxPrice !== undefined) priceQuery.lte = maxPrice;
    if (Object.keys(priceQuery).length > 0) {
      esQuery.bool.filter.push({ range: { 'pricing.list_price': priceQuery } });
    }
  }

  private addRatingFilter(esQuery: any, minRating?: number): void {
    if (minRating !== undefined && minRating > 0) {
      esQuery.bool.filter.push({ range: { 'ratings.average': { gte: minRating } } });
    }
  }

  private addInStockFilter(esQuery: any, inStock?: boolean): void {
    if (inStock !== undefined) {
      esQuery.bool.filter.push({ term: { 'inventory.in_stock': inStock } });
    }
  }

  private addAttributeFilters(esQuery: any, attributes?: Array<{ code: string; values: string[] }>): void {
    if (attributes && attributes.length > 0) {
      const attributeQueries = attributes.map(attr => ({
        nested: {
          path: 'attributes.custom_attributes',
          query: {
            bool: {
              must: [
                { term: { 'attributes.custom_attributes.code': attr.code } },
                { terms: { 'attributes.custom_attributes.value.keyword': attr.values } }, // Assuming value is keyword for filtering
              ],
            },
          },
        },
      }));
      esQuery.bool.filter.push(...attributeQueries);
    }
  }

  private buildSortClauses(sortOption?: string, query?: string): any[] {
    const sort = [];
    const hasSearchQuery = query && query.trim() !== '';

    switch (sortOption) {
      case 'price_asc': sort.push({ 'pricing.list_price': { order: 'asc', unmapped_type: 'double' } }); break;
      case 'price_desc': sort.push({ 'pricing.list_price': { order: 'desc', unmapped_type: 'double' } }); break;
      case 'name_asc': sort.push({ 'name.keyword': { order: 'asc', unmapped_type: 'keyword' } }); break;
      case 'name_desc': sort.push({ 'name.keyword': { order: 'desc', unmapped_type: 'keyword' } }); break;
      case 'newest': sort.push({ published_at: { order: 'desc', unmapped_type: 'date' } }); break;
      case 'rating': sort.push({ 'ratings.average': { order: 'desc', unmapped_type: 'double' } }); break;
      case 'popularity': sort.push({ 'search_data.popularity_score': { order: 'desc', unmapped_type: 'double' } }); break;
      case 'relevance':
      default:
        if (hasSearchQuery) {
            sort.push({ _score: { order: 'desc' } });
        }
        // Secondary sort for tie-breaking, even without a query
        sort.push({ 'search_data.popularity_score': { order: 'desc', unmapped_type: 'double' } });
        sort.push({ 'search_data.sale_count': { order: 'desc', unmapped_type: 'integer' } });
        break;
    }
    return sort;
  }

  private buildAggregations(includeAggs: boolean): any {
    if (!includeAggs) return undefined;

    return {
      categories: {
        nested: { path: 'categories' },
        aggs: {
          ids: {
            terms: { field: 'categories.id', size: 50 },
            aggs: {
              names: { terms: { field: 'categories.name.keyword' } }
            }
          }
        }
      },
      brands: {
        terms: { field: 'brand.name.keyword', size: 50 },
      },
      price_ranges: {
        range: {
          field: 'pricing.list_price',
          ranges: [
            { key: '*-25', to: 25 },
            { key: '25-50', from: 25, to: 50 },
            { key: '50-100', from: 50, to: 100 },
            { key: '100-200', from: 100, to: 200 },
            { key: '200-*', from: 200 },
          ],
        },
      },
      attributes: {
        nested: { path: 'attributes.custom_attributes' },
        aggs: {
          filterable_attributes: {
            filter: { term: { 'attributes.custom_attributes.filterable': true } },
            aggs: {
              codes: {
                terms: { field: 'attributes.custom_attributes.code', size: 20 },
                aggs: {
                  labels: { terms: { field: 'attributes.custom_attributes.label.keyword' } },
                  values: { terms: { field: 'attributes.custom_attributes.value.keyword', size: 30 } },
                },
              },
            },
          },
        },
      },
      ratings: {
        range: {
            field: "ratings.average",
            ranges: [
                { key: '4-5', from: 4, to: 5 },
                { key: '3-4', from: 3, to: 4 },
                { key: '2-3', from: 2, to: 3 },
                { key: '1-2', from: 1, to: 2 }
            ]
        }
      }
    };
  }

  private buildSuggestQuery(queryText: string): any {
    return {
      text: queryText,
      term_suggester: {
        term: {
          field: 'name.ngram', // Use ngram field for term suggestions
          suggest_mode: 'popular',
          min_word_length: 3,
        },
      },
      phrase_suggester: {
        phrase: {
          field: 'name.completion', // Use completion field for phrase suggestions
          gram_size: 3,
          direct_generator: [
            {
              field: 'name.completion',
              suggest_mode: 'always',
            },
          ],
          highlight: {
            pre_tag: '<em>',
            post_tag: '</em>',
          },
        },
      },
    };
  }

  private buildHighlightConfiguration(): any {
    return {
      fields: {
        "name": { number_of_fragments: 0 }, // Show full name highlighted
        "description": { fragment_size: 150, number_of_fragments: 3 },
        "short_description": { number_of_fragments: 0 },
        "attributes.custom_attributes.value_text": { fragment_size: 100, number_of_fragments: 1 }
      },
      pre_tags: ["<strong>"],
      post_tags: ["</strong>"],
    };
  }
}
```

### 3.2. Category Query Builder (`CategoryQueryBuilder`)

Builds queries for searching category documents.

#### Key Features:
- Handles text search on category `name` and `description`.
- Filters by `parent_id` to fetch subcategories or root categories.
- Filters by `status` and `visibility`.
- Sorts by `name` or `position` (manual sort order).
- Can include aggregations for product counts within categories if needed.

#### Implementation Sketch:

```typescript
import { Injectable } from '@nestjs/common';
import { CategorySearchParams } from '../models/category-search.model';
import { SearchQuery } from '../models/search-query.model';

@Injectable()
export class CategoryQueryBuilder {
  buildSearchQuery(params: CategorySearchParams): SearchQuery {
    const esQuery: any = { bool: { must: [], filter: [] } };

    if (params.query && params.query.trim() !== '') {
      esQuery.bool.must.push({
        multi_match: {
          query: params.query,
          fields: ['name^2', 'description', 'slug'],
          fuzziness: 'AUTO',
        },
      });
    }

    // Standard filters
    esQuery.bool.filter.push({ term: { status: 'active' } });
    esQuery.bool.filter.push({ term: { visibility: 'visible' } });

    if (params.parentId) {
      esQuery.bool.filter.push({ term: { parent_id: params.parentId } });
    } else if (params.fetchRoot) {
      esQuery.bool.filter.push({ bool: { must_not: { exists: { field: "parent_id" } } } });
    }

    if (params.categoryIds && params.categoryIds.length > 0) {
        esQuery.bool.filter.push({ terms: { id: params.categoryIds } });
    }

    const sortClauses: any[] = [];
    if (params.sort === 'name_asc') sortClauses.push({ 'name.keyword': 'asc' });
    else if (params.sort === 'name_desc') sortClauses.push({ 'name.keyword': 'desc' });
    else sortClauses.push({ position: 'asc' }); // Default sort by position

    return {
      query: esQuery,
      sort: sortClauses,
      from: params.page && params.pageSize ? (params.page - 1) * params.pageSize : 0,
      size: params.pageSize || 50, // Usually fewer categories to fetch
      // Aggregations if needed (e.g., product count per category)
    };
  }
}
```

### 3.3. Content Query Builder (`ContentQueryBuilder`)

Builds queries for searching content documents (articles, blog posts, FAQs).

#### Key Features:
- Handles text search on `title`, `body`, `summary`, `tags`, `author.name`, `categories.name`.
- Filters by `content_type`, `tags`, `author_id`, `category_id`, `status`, `visibility`.
- Sorts by relevance, publication date, view count, or custom criteria.
- Defines aggregations for content types, tags, and categories.

#### Implementation Sketch:

```typescript
import { Injectable } from '@nestjs/common';
import { ContentSearchParams } from '../models/content-search.model';
import { SearchQuery } from '../models/search-query.model';

@Injectable()
export class ContentQueryBuilder {
  buildSearchQuery(params: ContentSearchParams): SearchQuery {
    const esQuery: any = { bool: { must: [], filter: [] } };

    if (params.query && params.query.trim() !== '') {
      esQuery.bool.must.push({
        multi_match: {
          query: params.query,
          fields: ['title^2', 'summary^1.5', 'body', 'tags', 'author.name', 'categories.name', 'sections.title', 'sections.content'],
          fuzziness: 'AUTO',
        },
      });
    }

    esQuery.bool.filter.push({ term: { status: 'published' } });
    esQuery.bool.filter.push({ term: { visibility: 'public' } });

    if (params.filters) {
        if (params.filters.contentType) {
            esQuery.bool.filter.push({ term: { content_type: params.filters.contentType } });
        }
        if (params.filters.tags && params.filters.tags.length > 0) {
            esQuery.bool.filter.push({ terms: { tags: params.filters.tags } });
        }
        if (params.filters.categoryIds && params.filters.categoryIds.length > 0) {
             esQuery.bool.filter.push({
                nested: {
                  path: 'categories',
                  query: {
                    terms: { 'categories.id': params.filters.categoryIds },
                  },
                },
            });
        }
        if (params.filters.authorIds && params.filters.authorIds.length > 0) {
            esQuery.bool.filter.push({ terms: { 'author.id': params.filters.authorIds } });
        }
    }
    
    const sortClauses: any[] = [];
    switch (params.sort) {
        case 'newest': sortClauses.push({ published_at: 'desc' }); break;
        case 'views': sortClauses.push({ 'engagement.view_count': 'desc' }); break;
        case 'relevance':
        default:
            if (params.query && params.query.trim() !== '') sortClauses.push({ _score: 'desc' });
            sortClauses.push({ 'engagement.view_count': 'desc' }); // Secondary sort
            break;
    }

    const aggregations = {
        content_types: { terms: { field: 'content_type' } },
        tags: { terms: { field: 'tags', size: 50 } },
        categories: {
            nested: { path: 'categories' },
            aggs: { names: { terms: { field: 'categories.name.keyword', size: 30 } } }
        }
    };

    return {
      query: esQuery,
      sort: sortClauses,
      from: params.page && params.pageSize ? (params.page - 1) * params.pageSize : 0,
      size: params.pageSize || 15,
      aggs: aggregations,
      highlight: {
        fields: {
            "title": { number_of_fragments: 0 },
            "summary": { fragment_size: 150, number_of_fragments: 1 },
            "body": { fragment_size: 150, number_of_fragments: 3 }
        },
        pre_tags: ["<strong>"],
        post_tags: ["</strong>"],
      }
    };
  }
}
```

### 3.4. Autocomplete Query Builder (`AutocompleteQueryBuilder`)

Builds queries specifically for autocomplete and type-ahead suggestions.

#### Key Features:
- Uses `completion` suggester or `search_as_you_type` field types for efficient prefix matching.
- Queries multiple fields like product name, category name, brand name, and popular search terms.
- Can be configured to prioritize certain types of suggestions (e.g., products over categories).
- May include context filtering (e.g., suggest categories relevant to the current department).

#### Implementation Sketch:

```typescript
import { Injectable } from '@nestjs/common';
import { AutocompleteOptions } from '../models/autocomplete.model';

@Injectable()
export class AutocompleteQueryBuilder {
  buildSuggestQuery(queryText: string, options?: AutocompleteOptions): any {
    const suggest: any = {};
    const limit = options?.limit || 5;
    const types = options?.types || ['product', 'category', 'brand', 'term'];

    if (types.includes('product')) {
      suggest.product_suggestions = {
        prefix: queryText,
        completion: {
          field: 'name.completion', // Assuming 'name.completion' is a completion field
          size: limit,
          skip_duplicates: true,
          fuzzy: {
            fuzziness: 'AUTO'
          }
        },
      };
    }

    if (types.includes('category')) {
      suggest.category_suggestions = {
        prefix: queryText,
        completion: {
          field: 'categories.name.completion', // Path to category name completion field in products index, or a separate category index
          size: limit,
          skip_duplicates: true,
        },
      };
    }
    
    if (types.includes('brand')) {
      suggest.brand_suggestions = {
        prefix: queryText,
        completion: {
          field: 'brand.name.completion', // Path to brand name completion field in products index
          size: limit,
          skip_duplicates: true,
        },
      };
    }
    
    // Example for popular search terms (might come from a dedicated index or field)
    if (types.includes('term')) {
        suggest.term_suggestions = {
            prefix: queryText,
            completion: {
                field: 'search_terms.completion', // Field in a dedicated search_terms index or product index
                size: limit,
                skip_duplicates: true,
                contexts: options?.context ? { category_context: options.context.category } : undefined
            }
        }
    }

    return { suggest };
  }
}
```

## 4. Common Patterns & Best Practices

- **Modularity**: Keep each query builder focused on its specific entity or purpose.
- **Parameter Objects**: Use well-defined parameter objects (`ProductSearchParams`, `CategorySearchParams`, etc.) as inputs to builders for clarity and type safety.
- **Helper Methods**: Break down complex query construction logic into private helper methods within each builder.
- **Configuration**: Externalize configurations like field boosts, fuzziness settings, or default page sizes where appropriate.
- **Testing**: Thoroughly test query builders by inspecting the generated Elasticsearch DSL and verifying results against a test index.
- **Extensibility**: Design builders to be easily extensible as new search requirements emerge.
- **Avoid Business Logic**: Query builders should focus solely on query construction and not contain other business logic (which belongs in services).

## 5. Interactions

- **Search Services**: (`ProductSearchService`, `CategorySearchService`, etc.) are the primary consumers of Query Builders. They instantiate or inject the appropriate builder, pass search parameters, and receive the Elasticsearch query object.
- **Elasticsearch Client**: The generated query object is then passed to the Elasticsearch client for execution.

By centralizing Elasticsearch query construction logic, Query Builders play a vital role in creating a maintainable, testable, and efficient search backend.
