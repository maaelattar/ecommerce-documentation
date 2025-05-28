# Elasticsearch Setup - Search Service

## 🎯 Objective
Configure Elasticsearch integration with proper indexing, mappings, and search capabilities for product discovery.

## 🔍 Elasticsearch Module

```typescript
// src/elasticsearch/elasticsearch.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { ElasticsearchModule as ESModule } from '@nestjs/elasticsearch';

@Module({
  imports: [
    ESModule.registerAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        node: configService.get('ELASTICSEARCH_NODE'),
        auth: {
          username: configService.get('ELASTICSEARCH_USERNAME'),
          password: configService.get('ELASTICSEARCH_PASSWORD'),
        },
        requestTimeout: 60000,
        pingTimeout: 60000,
        sniffOnStart: false,
      }),
      inject: [ConfigService],
    }),
  ],
  exports: [ESModule],
})
export class ElasticsearchModule {}
```

## 📊 Product Index Mapping

```typescript
// src/elasticsearch/mappings/product.mapping.ts
export const productIndexMapping = {
  mappings: {
    properties: {
      id: { type: 'keyword' },
      name: {
        type: 'text',
        analyzer: 'standard',
        fields: {
          keyword: { type: 'keyword' },
          search: {
            type: 'text',
            analyzer: 'product_search_analyzer',
          },
        },
      },
      description: {
        type: 'text',
        analyzer: 'standard',
      },
      price: { type: 'double' },
      category: {
        type: 'nested',
        properties: {
          id: { type: 'keyword' },
          name: { type: 'keyword' },
          path: { type: 'keyword' },
        },
      },
      brand: { type: 'keyword' },
      tags: { type: 'keyword' },
      attributes: {
        type: 'nested',
        properties: {
          name: { type: 'keyword' },
          value: { type: 'keyword' },
        },
      },
      availability: {
        type: 'object',
        properties: {
          inStock: { type: 'boolean' },
          quantity: { type: 'integer' },
        },
      },
      ratings: {
        type: 'object',
        properties: {
          average: { type: 'double' },
          count: { type: 'integer' },
        },
      },
      seller: {
        type: 'object',
        properties: {
          id: { type: 'keyword' },
          name: { type: 'keyword' },
        },
      },
      createdAt: { type: 'date' },
      updatedAt: { type: 'date' },
    },
  },
  settings: {
    analysis: {
      analyzer: {
        product_search_analyzer: {
          type: 'custom',
          tokenizer: 'standard',
          filter: ['lowercase', 'stop', 'snowball'],
        },
      },
    },
    number_of_shards: 1,
    number_of_replicas: 0,
  },
};
```

## 🚀 Index Management Service

```typescript
// src/elasticsearch/index-management.service.ts
import { Injectable, OnModuleInit } from '@nestjs/common';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { LoggerService } from '@ecommerce/nestjs-core-utils';
import { productIndexMapping } from './mappings/product.mapping';

@Injectable()
export class IndexManagementService implements OnModuleInit {
  private readonly PRODUCT_INDEX = 'products';

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly logger: LoggerService,
  ) {}

  async onModuleInit() {
    await this.createProductIndex();
  }

  async createProductIndex() {
    try {
      const indexExists = await this.elasticsearchService.indices.exists({
        index: this.PRODUCT_INDEX,
      });

      if (!indexExists) {
        await this.elasticsearchService.indices.create({
          index: this.PRODUCT_INDEX,
          body: productIndexMapping,
        });

        this.logger.log('Product index created successfully', 'IndexManagementService');
      } else {
        this.logger.log('Product index already exists', 'IndexManagementService');
      }
    } catch (error) {
      this.logger.error('Failed to create product index', error, 'IndexManagementService');
      throw error;
    }
  }

  async indexProduct(product: any) {
    try {
      await this.elasticsearchService.index({
        index: this.PRODUCT_INDEX,
        id: product.id,
        body: this.transformProductForIndex(product),
      });

      this.logger.log('Product indexed successfully', 'IndexManagementService', {
        productId: product.id,
      });
    } catch (error) {
      this.logger.error('Failed to index product', error, 'IndexManagementService', {
        productId: product.id,
      });
      throw error;
    }
  }

  private transformProductForIndex(product: any) {
    return {
      id: product.id,
      name: product.name,
      description: product.description,
      price: parseFloat(product.price),
      category: {
        id: product.categoryId,
        name: product.category?.name,
        path: product.category?.path,
      },
      brand: product.brand,
      tags: product.tags || [],
      attributes: product.attributes || [],
      availability: {
        inStock: product.inventory?.quantity > 0,
        quantity: product.inventory?.quantity || 0,
      },
      ratings: {
        average: product.averageRating || 0,
        count: product.reviewCount || 0,
      },
      seller: {
        id: product.sellerId,
        name: product.seller?.name,
      },
      createdAt: product.createdAt,
      updatedAt: product.updatedAt,
    };
  }
}
```