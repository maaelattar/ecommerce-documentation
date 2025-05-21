# Search Facade

## 1. Introduction

The Search Facade serves as a simplified, high-level entry point for all search-related operations originating from the API layer or other client services. It abstracts the complexities of interacting with various underlying search and autocomplete services, providing a clean and unified interface for different types of search queries (products, categories, content) and autocomplete suggestions.

## 2. Responsibilities

- **Unified Interface**: Provides a single point of contact for initiating searches for products, categories, and content, as well as fetching autocomplete suggestions.
- **Delegation**: Delegates requests to the appropriate specialized search service (e.g., `ProductSearchService`, `CategorySearchService`, `ContentSearchService`, `AutocompleteService`).
- **Parameter Validation (Basic)**: Can perform initial basic validation or transformation of search parameters before passing them to specialized services.
- **Logging**: Centralized logging for all incoming search and autocomplete requests.
- **Error Handling Abstraction**: May catch errors from underlying services and transform them into standardized API responses or exceptions.

## 3. Design

The Search Facade is typically implemented as an injectable service that depends on the more specialized search services. It does not contain complex business logic itself but rather orchestrates calls to other components.

### 3.1. Dependencies

- `ProductSearchService`: For handling product-specific search queries.
- `CategorySearchService`: For handling category-specific search queries.
- `ContentSearchService`: For handling content-specific search queries (e.g., articles, blog posts).
- `AutocompleteService`: For providing search term suggestions.
- `Logger`: For logging requests and errors.

### 3.2. Key Methods

- `searchProducts(params: ProductSearchParams): Promise<SearchResult<Product>>`: Searches for products.
- `searchCategories(params: CategorySearchParams): Promise<SearchResult<Category>>`: Searches for categories.
- `searchContent(params: ContentSearchParams): Promise<SearchResult<Content>>`: Searches for content.
- `getAutocomplete(query: string, options: AutocompleteOptions): Promise<AutocompleteResult>`: Retrieves autocomplete suggestions.

## 4. Implementation Example (TypeScript/NestJS)

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ProductSearchService, ProductSearchParams, Product } from './product-search.service'; // Assuming ProductSearchService handles Product type
import { CategorySearchService, CategorySearchParams, Category } from './category-search.service'; // Assuming CategorySearchService handles Category type
import { ContentSearchService, ContentSearchParams, Content } from './content-search.service'; // Assuming ContentSearchService handles Content type
import { AutocompleteService, AutocompleteOptions, AutocompleteResult } from './autocomplete.service';
import { SearchResult } from '../models/search-result.model';

@Injectable()
export class SearchFacade {
  private readonly logger = new Logger(SearchFacade.name);

  constructor(
    private readonly productSearchService: ProductSearchService,
    private readonly categorySearchService: CategorySearchService,
    private readonly contentSearchService: ContentSearchService,
    private readonly autocompleteService: AutocompleteService,
  ) {}

  async searchProducts(params: ProductSearchParams): Promise<SearchResult<Product>> {
    this.logger.log(`Initiating product search with params: ${JSON.stringify(params)}`);
    try {
      const results = await this.productSearchService.search(params);
      this.logger.log(`Product search successful for query: ${params.query}, found ${results.total} items.`);
      return results;
    } catch (error) {
      this.logger.error(`Product search failed for params: ${JSON.stringify(params)}`, error.stack);
      // Re-throw or handle as per application's error strategy
      throw error;
    }
  }

  async searchCategories(params: CategorySearchParams): Promise<SearchResult<Category>> {
    this.logger.log(`Initiating category search with params: ${JSON.stringify(params)}`);
    try {
      const results = await this.categorySearchService.search(params);
      this.logger.log(`Category search successful for query: ${params.query}, found ${results.total} items.`);
      return results;
    } catch (error) {
      this.logger.error(`Category search failed for params: ${JSON.stringify(params)}`, error.stack);
      throw error;
    }
  }

  async searchContent(params: ContentSearchParams): Promise<SearchResult<Content>> {
    this.logger.log(`Initiating content search with params: ${JSON.stringify(params)}`);
    try {
      const results = await this.contentSearchService.search(params);
      this.logger.log(`Content search successful for query: ${params.query}, found ${results.total} items.`);
      return results;
    } catch (error) {
      this.logger.error(`Content search failed for params: ${JSON.stringify(params)}`, error.stack);
      throw error;
    }
  }

  async getAutocomplete(query: string, options?: AutocompleteOptions): Promise<AutocompleteResult> {
    this.logger.log(`Fetching autocomplete suggestions for query: "${query}" with options: ${JSON.stringify(options)}`);
    try {
      const suggestions = await this.autocompleteService.getSuggestions(query, options);
      this.logger.log(`Autocomplete successful for query: "${query}", found ${suggestions.suggestions?.length || 0} suggestions.`);
      return suggestions;
    } catch (error) {
      this.logger.error(`Autocomplete failed for query: "${query}"`, error.stack);
      throw error;
    }
  }
}

// Placeholder definitions for dependent services and models
// These would be defined in their respective files

// interface ProductSearchParams { query: string; filters?: any; sort?: string; page?: number; pageSize?: number; }
// interface CategorySearchParams { query: string; parentId?: string; page?: number; pageSize?: number; }
// interface ContentSearchParams { query: string; type?: string; tags?: string[]; page?: number; pageSize?: number; }
// interface AutocompleteOptions { limit?: number; types?: Array<'product' | 'category' | 'content' | 'brand'>; }
// interface AutocompleteResult { query: string; suggestions: Array<{ text: string; type: string; payload?: any; score?: number; }>; }
// interface SearchResult<T> { items: T[]; total: number; page: number; size: number; pages: number; facets?: any[]; query?: string; }
// interface Product { id: string; name: string; /* ... other product fields ... */ }
// interface Category { id: string; name: string; /* ... other category fields ... */ }
// interface Content { id: string; title: string; /* ... other content fields ... */ }

// class ProductSearchService { async search(params: ProductSearchParams): Promise<SearchResult<Product>> { /* ... */ return {} as SearchResult<Product>; } }
// class CategorySearchService { async search(params: CategorySearchParams): Promise<SearchResult<Category>> { /* ... */ return {} as SearchResult<Category>; } }
// class ContentSearchService { async search(params: ContentSearchParams): Promise<SearchResult<Content>> { /* ... */ return {} as SearchResult<Content>; } }
// class AutocompleteService { async getSuggestions(query: string, options?: AutocompleteOptions): Promise<AutocompleteResult> { /* ... */ return {} as AutocompleteResult; } }

```

## 5. Interactions

- **API Layer**: The primary consumer of the Search Facade. The API controllers/resolvers will inject the `SearchFacade` and call its methods.
- **Specialized Search Services**: The `SearchFacade` delegates calls to these services (e.g., `ProductSearchService`, `AutocompleteService`).

## 6. Benefits

- **Decoupling**: Decouples the API layer from the underlying complexity of different search implementations.
- **Maintainability**: Simplifies changes to search logic as modifications can often be contained within specialized services without affecting the facade's interface.
- **Testability**: Easier to mock specialized services when testing components that use the Search Facade.
- **Clarity**: Provides a clear and concise API for all search-related operations.

## 7. Considerations

- **Over-Abstraction**: Care should be taken not to make the facade too generic, which might lead to a loss of type safety or require complex parameter objects.
- **Performance**: While generally a thin layer, any processing within the facade should be minimal to avoid adding latency.

This facade provides a clean entry point to the search subsystem, delegating responsibilities to more focused services for handling products, categories, content, and autocomplete features.
