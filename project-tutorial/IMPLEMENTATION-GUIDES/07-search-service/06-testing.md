# Testing - Search Service with Shared Libraries

## 🎯 Objective
Implement comprehensive testing using shared testing utilities for search functionality, Elasticsearch integration, and event handling.

## 🧪 Unit Tests with Shared Testing Utilities

```typescript
// src/search/search.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { ElasticsearchService } from '@nestjs/elasticsearch';

// Import shared testing utilities
import { 
  createMockElasticsearch,
  createMockLogger,
} from '@ecommerce/testing-utils';

import { SearchService } from './search.service';

describe('SearchService', () => {
  let service: SearchService;
  let mockElasticsearchService: any;
  let mockLogger: any;

  beforeEach(async () => {
    // Use shared testing utilities for consistent mocks
    mockElasticsearchService = createMockElasticsearch();
    mockLogger = createMockLogger();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        SearchService,
        {
          provide: ElasticsearchService,
          useValue: mockElasticsearchService,
        },
        {
          provide: 'LoggerService',
          useValue: mockLogger,
        },
      ],
    }).compile();

    service = module.get<SearchService>(SearchService);
  });

  describe('searchProducts', () => {
    it('should search products successfully', async () => {
      const searchDto = {
        q: 'laptop',
        page: 1,
        limit: 20,
      };

      const mockSearchResponse = {
        body: {
          took: 5,
          hits: {
            total: { value: 10 },
            hits: [
              {
                _source: {
                  id: 'product-1',
                  name: 'Gaming Laptop',
                  price: 999.99,
                  category: { name: 'Electronics' },
                },
                _score: 1.5,
              },
            ],
          },
        },
      };

      mockElasticsearchService.search.mockResolvedValue(mockSearchResponse);

      const result = await service.searchProducts(searchDto);

      expect(result).toEqual({
        products: [
          {
            id: 'product-1',
            name: 'Gaming Laptop',
            price: 999.99,
            category: { name: 'Electronics' },
            score: 1.5,
          },
        ],
        total: 10,
        page: 1,
        totalPages: 1,
        took: 5,
      });

      expect(mockLogger.log).toHaveBeenCalledWith(
        'Executing product search',
        'SearchService',
        expect.objectContaining({
          query: 'laptop',
          page: 1,
          limit: 20,
        })
      );
    });

    it('should handle search errors', async () => {
      const searchDto = { q: 'test' };
      const error = new Error('Elasticsearch error');

      mockElasticsearchService.search.mockRejectedValue(error);

      await expect(service.searchProducts(searchDto)).rejects.toThrow(error);
      
      expect(mockLogger.error).toHaveBeenCalledWith(
        'Search query failed',
        error,
        'SearchService',
        expect.objectContaining({
          query: 'test',
        })
      );
    });
  });

  describe('getSearchSuggestions', () => {
    it('should return search suggestions', async () => {
      const mockSuggestResponse = {
        body: {
          suggest: {
            product_suggestions: [
              {
                options: [
                  { text: 'laptop gaming' },
                  { text: 'laptop business' },
                ],
              },
            ],
          },
        },
      };

      mockElasticsearchService.search.mockResolvedValue(mockSuggestResponse);

      const result = await service.getSearchSuggestions('laptop');

      expect(result).toEqual(['laptop gaming', 'laptop business']);
      expect(mockLogger.log).toHaveBeenCalledWith(
        'Suggestions generated',
        'SearchService',
        {
          query: 'laptop',
          suggestionsCount: 2,
        }
      );
    });
  });
});
```

## 🔄 Event Handler Tests

```typescript
// src/events/handlers/product-events.handler.spec.ts
import { Test, TestingModule } from '@nestjs/testing';

// Import shared testing utilities
import { createMockLogger } from '@ecommerce/testing-utils';

import { ProductEventsHandler } from './product-events.handler';
import { IndexManagementService } from '../../elasticsearch/index-management.service';

describe('ProductEventsHandler', () => {
  let handler: ProductEventsHandler;
  let mockIndexManagementService: any;
  let mockLogger: any;

  beforeEach(async () => {
    mockIndexManagementService = {
      indexProduct: jest.fn(),
      updateProductIndex: jest.fn(),
      removeProductFromIndex: jest.fn(),
    };

    mockLogger = createMockLogger();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ProductEventsHandler,
        {
          provide: IndexManagementService,
          useValue: mockIndexManagementService,
        },
        {
          provide: 'LoggerService',
          useValue: mockLogger,
        },
      ],
    }).compile();

    handler = module.get<ProductEventsHandler>(ProductEventsHandler);
  });

  describe('handleProductCreated', () => {
    it('should index new product successfully', async () => {
      const event = {
        id: 'event-123',
        productId: 'product-123',
        name: 'New Product',
        description: 'Product description',
        price: '99.99',
        categoryId: 'category-1',
        sellerId: 'seller-1',
        timestamp: new Date().toISOString(),
      };

      mockIndexManagementService.indexProduct.mockResolvedValue(undefined);

      await handler.handleProductCreated(event);

      expect(mockIndexManagementService.indexProduct).toHaveBeenCalledWith({
        id: event.productId,
        name: event.name,
        description: event.description,
        price: event.price,
        categoryId: event.categoryId,
        sellerId: event.sellerId,
        brand: event.brand,
        tags: event.tags,
        createdAt: event.timestamp,
        updatedAt: event.timestamp,
      });

      expect(mockLogger.log).toHaveBeenCalledWith(
        'Product indexed after creation',
        'ProductEventsHandler',
        {
          productId: event.productId,
          eventId: event.id,
        }
      );
    });

    it('should handle indexing errors', async () => {
      const event = {
        id: 'event-123',
        productId: 'product-123',
        name: 'New Product',
      };

      const error = new Error('Indexing failed');
      mockIndexManagementService.indexProduct.mockRejectedValue(error);

      await handler.handleProductCreated(event);

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to index created product',
        error,
        'ProductEventsHandler',
        {
          productId: event.productId,
          eventId: event.id,
        }
      );
    });
  });
});
```

## 🌐 Integration Tests

```typescript
// src/search/search.integration.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';

// Import shared testing utilities
import { 
  createTestApp,
  setupTestDatabase,
  cleanupTestDatabase,
} from '@ecommerce/testing-utils';

import { AppModule } from '../app.module';

describe('Search Integration Tests', () => {
  let app: INestApplication;

  beforeAll(async () => {
    await setupTestDatabase();
    
    const moduleRef: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = await createTestApp(moduleRef);
  });

  afterAll(async () => {
    await cleanupTestDatabase();
    await app.close();
  });

  describe('GET /search/products', () => {
    it('should return search results', async () => {
      const response = await request(app.getHttpServer())
        .get('/search/products')
        .query({ q: 'laptop', limit: 10 })
        .expect(200);

      expect(response.body).toHaveProperty('products');
      expect(response.body).toHaveProperty('total');
      expect(response.body).toHaveProperty('page');
      expect(response.body).toHaveProperty('totalPages');
      expect(Array.isArray(response.body.products)).toBe(true);
    });

    it('should handle search with filters', async () => {
      const response = await request(app.getHttpServer())
        .get('/search/products')
        .query({ 
          q: 'laptop',
          category: 'Electronics',
          minPrice: 100,
          maxPrice: 1000,
          inStock: true,
        })
        .expect(200);

      expect(response.body.products).toBeDefined();
    });
  });

  describe('GET /search/suggestions', () => {
    it('should return search suggestions', async () => {
      const response = await request(app.getHttpServer())
        .get('/search/suggestions')
        .query({ q: 'lap', limit: 5 })
        .expect(200);

      expect(response.body).toHaveProperty('suggestions');
      expect(Array.isArray(response.body.suggestions)).toBe(true);
    });
  });

  describe('GET /search/facets', () => {
    it('should return search facets', async () => {
      const response = await request(app.getHttpServer())
        .get('/search/facets')
        .query({ q: 'laptop' })
        .expect(200);

      expect(response.body).toHaveProperty('categories');
      expect(response.body).toHaveProperty('brands');
      expect(response.body).toHaveProperty('priceRanges');
      expect(response.body).toHaveProperty('availability');
    });
  });
});
```