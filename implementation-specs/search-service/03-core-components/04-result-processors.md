# Result Processors

## 1. Introduction

Result Processors are responsible for transforming the raw JSON responses received from Elasticsearch into structured, application-specific data transfer objects (DTOs) or domain models. They play a critical role in decoupling the application's data representation from the Elasticsearch response format.

Each major searchable entity (Product, Category, Content) and the autocomplete functionality will typically have its own Result Processor to handle the specific structure of its search results and aggregations.

## 2. Responsibilities

- **Data Mapping**: Map fields from Elasticsearch documents (`_source`) to corresponding fields in application DTOs/models.
- **Hit Extraction**: Extract individual search hits (`hits.hits`) from the Elasticsearch response.
- **Pagination Data**: Calculate and include pagination details (total items, current page, total pages, page size).
- **Facet Processing**: Transform Elasticsearch aggregations (`aggregations`) into a user-friendly facet structure for faceted navigation.
- **Highlighting**: Extract and format highlighted snippets if requested in the query.
- **Score Handling**: Include relevance scores (`_score`) if applicable.
- **Suggestion Formatting**: For autocomplete, format suggester responses into a clean list of suggestions.
- **Error Handling (Minor)**: May perform minor checks on the response structure but generally relies on the Search Service for major error handling.

## 3. Core Result Processors

### 3.1. Product Result Processor (`ProductResultProcessor`)

Processes Elasticsearch responses for product searches.

#### Key Features:
- Maps Elasticsearch product documents to `Product` DTOs.
- Extracts product `id`, `name`, `price`, `images`, `attributes`, etc.
- Processes aggregations for categories, brands, price ranges, and custom attributes into `Facet` objects.
- Includes `_score` and `highlight` data in the resulting `Product` DTOs if available.
- Constructs a `ProductSearchResult` object containing the list of products, total count, pagination info, and facets.

#### Implementation Example (TypeScript/NestJS)

(Extended from the `00-overview.md` with more details)

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchSearchResponse } from '@elastic/elasticsearch/lib/api/types'; // Official ES types
import { Product, ProductSearchResult, ProductSearchParams } from '../models/product-search.model';
import { Facet, FacetValue } from '../models/facet.model';

@Injectable()
export class ProductResultProcessor {
  private readonly logger = new Logger(ProductResultProcessor.name);

  processResponse(
    searchResponse: ElasticsearchSearchResponse<any>, // Use official ES response type
    params: ProductSearchParams,
  ): ProductSearchResult {
    const hits = searchResponse.hits.hits;
    const total = typeof searchResponse.hits.total === 'number' ? searchResponse.hits.total : searchResponse.hits.total?.value || 0;
    const pageSize = params.pageSize || 20;
    const currentPage = params.page || 1;

    const products: Product[] = hits.map(hit => this.mapToProduct(hit as any)); // Cast hit to any or define a proper type
    const facets: Facet[] = this.processFacets(searchResponse.aggregations, params);
    
    this.logger.debug(`Processed ${products.length} products out of ${total} total. Current page: ${currentPage}`);

    return {
      items: products,
      total,
      page: currentPage,
      size: pageSize,
      pages: Math.ceil(total / pageSize),
      facets,
      query: params.query,
      suggestions: this.processSuggestions(searchResponse.suggest),
    };
  }

  mapToProduct(hit: { _id: string; _source: any; _score?: number; highlight?: any }): Product {
    const source = hit._source;
    // Basic transformation, ensure all fields from ProductDocumentSchema are considered
    return {
      id: hit._id, // or source.id if you prefer that source
      sku: source.sku,
      name: source.name,
      description: source.description,
      shortDescription: source.short_description,
      slug: source.slug,
      status: source.status,
      visibility: source.visibility,
      type: source.type,
      categories: source.categories?.map(cat => ({ 
        id: cat.id, 
        name: cat.name, 
        path: cat.path,
        level: cat.level,
        position: cat.position
      })) || [],
      brand: source.brand ? { id: source.brand.id, name: source.brand.name, logoUrl: source.brand.logo_url } : undefined,
      pricing: source.pricing ? {
        currency: source.pricing.currency,
        listPrice: source.pricing.list_price,
        salePrice: source.pricing.sale_price,
        // ... other pricing fields
      } : undefined,
      inventory: source.inventory ? {
        inStock: source.inventory.in_stock,
        quantity: source.inventory.quantity,
        // ... other inventory fields
      } : undefined,
      attributes: {
          color: source.attributes?.color,
          size: source.attributes?.size,
          material: source.attributes?.material,
          customAttributes: source.attributes?.custom_attributes?.map(ca => ({
              code: ca.code,
              label: ca.label,
              value: ca.value, // This might need further transformation depending on 'any' type
              valueText: ca.value_text,
              filterable: ca.filterable,
              searchable: ca.searchable
          })) || []
      },
      variants: source.variants?.map(v => ({
        id: v.id,
        sku: v.sku,
        // ... other variant fields
      })) || [],
      media: source.media ? { 
        thumbnail: source.media.thumbnail,
        images: source.media.images?.map(img => ({ url: img.url, alt: img.alt, type: img.type })) || [],
        // ... other media fields
      } : undefined,
      seo: source.seo ? { title: source.seo.title, description: source.seo.description, keywords: source.seo.keywords } : undefined,
      ratings: source.ratings ? { average: source.ratings.average, count: source.ratings.count } : undefined,
      shipping: source.shipping, // map if necessary
      tags: source.tags || [],
      searchData: source.search_data, // map if necessary
      metadata: source.metadata, // map if necessary
      score: hit._score,
      highlight: hit.highlight, // Pass highlight snippets directly
      // Ensure all relevant fields from ProductDocumentSchema are mapped
    };
  }

  private processFacets(aggregations: any, params: ProductSearchParams): Facet[] {
    if (!aggregations) return [];
    const facets: Facet[] = [];

    // Category Facets (from nested aggregation)
    if (aggregations.categories?.ids?.buckets) {
      facets.push({
        code: 'category',
        label: 'Category',
        type: 'terms',
        values: aggregations.categories.ids.buckets.map((bucket: any) => ({
          value: bucket.key, // This is category ID
          label: bucket.names?.buckets[0]?.key || bucket.key, // Category Name
          count: bucket.doc_count,
          selected: params.filters?.categoryIds?.includes(bucket.key) || false,
        })),
      });
    }

    // Brand Facets
    if (aggregations.brands?.buckets) {
      facets.push({
        code: 'brand',
        label: 'Brand',
        type: 'terms',
        values: aggregations.brands.buckets.map((bucket: any) => ({
          value: bucket.key,
          label: bucket.key, // Assuming brand name is the key
          count: bucket.doc_count,
          selected: params.filters?.brandIds?.includes(bucket.key) || false,
        })),
      });
    }

    // Price Range Facets
    if (aggregations.price_ranges?.buckets) {
      facets.push({
        code: 'price',
        label: 'Price Range',
        type: 'range',
        values: aggregations.price_ranges.buckets.map((bucket: any) => ({
          value: bucket.key,
          label: bucket.key, // e.g., "50-100" or "*-25"
          count: bucket.doc_count,
          selected: (params.filters?.priceMin !== undefined && bucket.from === params.filters.priceMin) || 
                      (params.filters?.priceMax !== undefined && bucket.to === params.filters.priceMax) ||
                      (params.filters?.priceMin === undefined && params.filters?.priceMax === undefined && bucket.key === '*'), // crude selection logic, needs refinement
          from: bucket.from,
          to: bucket.to,
        })),
      });
    }

    // Attribute Facets (from nested aggregation)
    if (aggregations.attributes?.filterable_attributes?.codes?.buckets) {
      aggregations.attributes.filterable_attributes.codes.buckets.forEach((attrBucket: any) => {
        facets.push({
          code: attrBucket.key, // Attribute code, e.g., 'color', 'size'
          label: attrBucket.labels?.buckets[0]?.key || attrBucket.key, // Attribute label
          type: 'terms', // Or could be 'swatch' etc. based on attribute config
          values: attrBucket.values.buckets.map((valueBucket: any) => ({
            value: valueBucket.key,
            label: valueBucket.key, // Attribute value label
            count: valueBucket.doc_count,
            selected: params.filters?.attributes?.find(a => a.code === attrBucket.key)?.values.includes(valueBucket.key) || false,
          })),
        });
      });
    }
    
    // Rating Facets
    if (aggregations.ratings?.buckets) {
      facets.push({
        code: 'rating',
        label: 'Rating',
        type: 'range',
        values: aggregations.ratings.buckets.map((bucket: any) => ({
          value: bucket.key, // e.g., "4-5"
          label: `${bucket.from || ''}${bucket.from ? '-' : ''}${bucket.to || '+'} stars`, 
          count: bucket.doc_count,
          selected: params.filters?.minRating === bucket.from
        }))
      });
    }

    return facets;
  }
  
  private processSuggestions(suggest: any): any {
    if (!suggest) return undefined;
    // Process term and phrase suggestions if available
    // Example: combine and rank them
    const suggestions = [];
    if (suggest.term_suggester) {
        suggest.term_suggester.forEach(sg => {
            sg.options.forEach(opt => suggestions.push({ text: opt.text, score: opt.score, type: 'term' }));
        });
    }
    if (suggest.phrase_suggester) {
        suggest.phrase_suggester.forEach(sg => {
            sg.options.forEach(opt => suggestions.push({ text: opt.text, highlighted: opt.highlighted, score: opt.score, type: 'phrase' }));
        });
    }
    return suggestions.sort((a, b) => (b.score || 0) - (a.score || 0));
  }
}
```

### 3.2. Category Result Processor (`CategoryResultProcessor`)

Processes Elasticsearch responses for category searches.

#### Key Features:
- Maps Elasticsearch category documents to `Category` DTOs.
- Extracts category `id`, `name`, `slug`, `path`, `product_counts`.
- Can process aggregations if queries include them (e.g., count of subcategories).
- Constructs a `CategorySearchResult` object.

#### Implementation Sketch:

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchSearchResponse } from '@elastic/elasticsearch/lib/api/types';
import { Category, CategorySearchResult, CategorySearchParams } from '../models/category-search.model';
import { Facet } from '../models/facet.model'; // If categories have facets

@Injectable()
export class CategoryResultProcessor {
  private readonly logger = new Logger(CategoryResultProcessor.name);

  processResponse(
    searchResponse: ElasticsearchSearchResponse<any>,
    params: CategorySearchParams,
  ): CategorySearchResult {
    const hits = searchResponse.hits.hits;
    const total = typeof searchResponse.hits.total === 'number' ? searchResponse.hits.total : searchResponse.hits.total?.value || 0;
    const pageSize = params.pageSize || 50;
    const currentPage = params.page || 1;

    const categories: Category[] = hits.map(hit => this.mapToCategory(hit as any));
    // Categories might not have facets, or they might be simpler
    // const facets: Facet[] = this.processFacets(searchResponse.aggregations, params);

    return {
      items: categories,
      total,
      page: currentPage,
      size: pageSize,
      pages: Math.ceil(total / pageSize),
      // facets,
      query: params.query
    };
  }

  mapToCategory(hit: { _id: string; _source: any; _score?: number }): Category {
    const source = hit._source;
    return {
      id: hit._id,
      name: source.name,
      slug: source.slug,
      description: source.description,
      status: source.status,
      visibility: source.visibility,
      path: source.path,
      pathIds: source.path_ids,
      level: source.level,
      position: source.position,
      parentId: source.parent_id,
      attributes: source.attributes, // Map if needed
      media: source.media, // Map if needed
      seo: source.seo, // Map if needed
      productCounts: source.product_counts,
      childrenCount: source.children?.length || 0, // Example if children are partially stored
      // children: source.children?.map(child => ({ id: child.id, name: child.name, slug: child.slug, position: child.position })) || [],
      score: hit._score,
    };
  }
  
  // private processFacets(aggregations: any, params: CategorySearchParams): Facet[] { /* ... */ return []; }
}
```

### 3.3. Content Result Processor (`ContentResultProcessor`)

Processes Elasticsearch responses for content searches.

#### Key Features:
- Maps Elasticsearch content documents to `ContentDoc` DTOs.
- Extracts `title`, `summary`, `body` (potentially snippets), `author`, `tags`, `publication_date`.
- Processes aggregations for content types, tags, and categories into facets.
- Constructs a `ContentSearchResult` object.

#### Implementation Sketch:

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchSearchResponse } from '@elastic/elasticsearch/lib/api/types';
import { ContentDoc, ContentSearchResult, ContentSearchParams } from '../models/content-search.model';
import { Facet } from '../models/facet.model';

@Injectable()
export class ContentResultProcessor {
  private readonly logger = new Logger(ContentResultProcessor.name);

  processResponse(
    searchResponse: ElasticsearchSearchResponse<any>,
    params: ContentSearchParams,
  ): ContentSearchResult {
    const hits = searchResponse.hits.hits;
    const total = typeof searchResponse.hits.total === 'number' ? searchResponse.hits.total : searchResponse.hits.total?.value || 0;
    const pageSize = params.pageSize || 15;
    const currentPage = params.page || 1;

    const contentItems: ContentDoc[] = hits.map(hit => this.mapToContent(hit as any));
    const facets: Facet[] = this.processFacets(searchResponse.aggregations, params);

    return {
      items: contentItems,
      total,
      page: currentPage,
      size: pageSize,
      pages: Math.ceil(total / pageSize),
      facets,
      query: params.query,
    };
  }

  mapToContent(hit: { _id: string; _source: any; _score?: number; highlight?: any }): ContentDoc {
    const source = hit._source;
    return {
      id: hit._id,
      title: source.title,
      slug: source.slug,
      contentType: source.content_type,
      body: source.body, // Potentially snippet from highlight if full body is large
      summary: source.summary,
      status: source.status,
      visibility: source.visibility,
      publishedAt: source.published_at,
      author: source.author, // Map if needed
      categories: source.categories?.map(c => ({ id: c.id, name: c.name, slug: c.slug })) || [],
      tags: source.tags || [],
      media: source.media, // Map if needed
      attributes: source.attributes, // Map if needed
      seo: source.seo, // Map if needed
      engagement: source.engagement,
      score: hit._score,
      highlight: hit.highlight,
    };
  }

  private processFacets(aggregations: any, params: ContentSearchParams): Facet[] {
    if (!aggregations) return [];
    const facets: Facet[] = [];

    if (aggregations.content_types?.buckets) {
      facets.push({
        code: 'contentType',
        label: 'Content Type',
        type: 'terms',
        values: aggregations.content_types.buckets.map((bucket: any) => ({
          value: bucket.key,
          label: bucket.key, 
          count: bucket.doc_count,
          selected: params.filters?.contentType === bucket.key,
        })),
      });
    }
    
    if (aggregations.tags?.buckets) {
      facets.push({
        code: 'tags',
        label: 'Tags',
        type: 'terms',
        values: aggregations.tags.buckets.map((bucket: any) => ({
          value: bucket.key,
          label: bucket.key, 
          count: bucket.doc_count,
          selected: params.filters?.tags?.includes(bucket.key) || false,
        })),
      });
    }
    
    // Example for categories if they are faceted for content
    if (aggregations.categories?.names?.buckets) {
        facets.push({
            code: 'contentCategory',
            label: 'Category',
            type: 'terms',
            values: aggregations.categories.names.buckets.map((bucket: any) => ({
                value: bucket.key, // This would be category name, ID might be needed if filtering by ID
                label: bucket.key,
                count: bucket.doc_count,
                selected: params.filters?.categoryIds?.includes(bucket.key) || false, // Adjust if filtering by ID
            }))
        });
    }

    return facets;
  }
}
```

### 3.4. Autocomplete Result Processor (`AutocompleteResultProcessor`)

Processes Elasticsearch suggester responses for autocomplete.

#### Key Features:
- Extracts suggestions from different suggesters (term, phrase, completion).
- Formats suggestions into a unified `AutocompleteSuggestion` DTO, including text, type (product, category, brand, term), and potentially a payload for navigation.
- Can merge and rank suggestions from multiple sources.
- Constructs an `AutocompleteResult` object.

#### Implementation Sketch:

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchSuggestResponse } from '@elastic/elasticsearch/lib/api/types'; // Type for suggester response
import { AutocompleteOptions, AutocompleteResult, AutocompleteSuggestion } from '../models/autocomplete.model';

@Injectable()
export class AutocompleteResultProcessor {
  private readonly logger = new Logger(AutocompleteResultProcessor.name);

  processResponse(
    suggestResponse: ElasticsearchSuggestResponse,
    queryText: string,
    options?: AutocompleteOptions,
  ): AutocompleteResult {
    const suggestions: AutocompleteSuggestion[] = [];
    this.logger.debug(`Processing autocomplete suggestions for query: "${queryText}", ES response: ${JSON.stringify(suggestResponse)}`);

    if (suggestResponse?.product_suggestions) {
      suggestResponse.product_suggestions.forEach(suggestionGroup => {
        suggestionGroup.options.forEach(option => {
          suggestions.push({
            text: option.text,
            highlightedText: option.highlighted || option.text,
            type: 'product',
            score: option._score,
            payload: { id: option._id, source: option._source }, // Example payload
          });
        });
      });
    }

    if (suggestResponse?.category_suggestions) {
      suggestResponse.category_suggestions.forEach(suggestionGroup => {
        suggestionGroup.options.forEach(option => {
          suggestions.push({
            text: option.text,
            highlightedText: option.highlighted || option.text,
            type: 'category',
            score: option._score,
            payload: { id: option._id, source: option._source }, 
          });
        });
      });
    }
    
    if (suggestResponse?.brand_suggestions) {
      suggestResponse.brand_suggestions.forEach(suggestionGroup => {
        suggestionGroup.options.forEach(option => {
          suggestions.push({
            text: option.text,
            highlightedText: option.highlighted || option.text,
            type: 'brand',
            score: option._score,
            payload: { id: option._id, name: option.text, source: option._source }, 
          });
        });
      });
    }
    
    if (suggestResponse?.term_suggestions) {
      suggestResponse.term_suggestions.forEach(suggestionGroup => {
        suggestionGroup.options.forEach(option => {
          suggestions.push({
            text: option.text,
            highlightedText: option.highlighted || option.text,
            type: 'term', // Popular search term
            score: option._score,
            payload: { term: option.text }, 
          });
        });
      });
    }

    // Sort suggestions by score if available, or keep ES order
    const sortedSuggestions = suggestions.sort((a, b) => (b.score || 0) - (a.score || 0));
    const limit = options?.limit || 10;

    return {
      query: queryText,
      suggestions: sortedSuggestions.slice(0, limit),
    };
  }
}
```

## 4. Common Patterns & Best Practices

- **DTOs/Models**: Define clear DTOs (Data Transfer Objects) or domain models for search results (e.g., `ProductSearchResult`, `Facet`, `AutocompleteSuggestion`) to ensure consistency.
- **Type Safety**: Utilize TypeScript interfaces or classes for Elasticsearch responses and application DTOs to improve type safety.
- **Null/Undefined Handling**: Gracefully handle missing fields or aggregations in Elasticsearch responses.
- **Configurable Formatting**: For facets or complex fields, formatting logic might be configurable (e.g., date formats, price display).
- **Performance**: Result processing should be efficient as it's part of every search request. Avoid complex computations or I/O operations.
- **Testability**: Result processors should be easily testable with mock Elasticsearch responses.

## 5. Interactions

- **Search Services**: (`ProductSearchService`, etc.) are the primary consumers of Result Processors. They pass the raw Elasticsearch response and original search parameters to the appropriate processor.
- **Application DTOs/Models**: Result Processors produce instances of these objects, which are then returned by the Search Services to the Search Facade and ultimately to the API layer.

Result Processors are essential for translating Elasticsearch's output into a format that is meaningful and easy to consume by the rest of the e-commerce application, promoting cleaner code and better separation of concerns.
