# Indexing Services

## 1. Introduction

Indexing Services are responsible for managing the lifecycle of documents within Elasticsearch indices. This includes adding new documents, updating existing ones, and deleting documents that are no longer relevant. They act as an abstraction layer over the Elasticsearch client for all write operations related to specific entities (Products, Categories, Content).

These services are crucial for keeping the search indices synchronized with the primary data sources (e.g., product catalog database, CMS).

## 2. Responsibilities

- **Document Indexing**: Add new documents to the appropriate Elasticsearch index (e.g., a new product to the `products` index).
- **Document Updating**: Update existing documents in Elasticsearch when their source data changes.
  - Full document updates (re-indexing the entire document).
  - Partial document updates (updating specific fields using the Update API).
- **Document Deletion**: Remove documents from Elasticsearch indices.
- **Bulk Operations**: Support efficient bulk indexing, updating, and deletion of multiple documents in a single request.
- **Index Alias Management (Optional)**: May participate in or trigger alias switching during re-indexing processes, though this is often managed by a higher-level Admin or Orchestration service.
- **Error Handling**: Manage errors during indexing operations, log issues, and potentially implement retry mechanisms or dead-letter queue (DLQ) logic for failed operations.
- **Data Transformation (Light)**: May perform light transformation of data from source format to the Elasticsearch document schema if not already handled by an upstream data pipeline or event transformer.

## 3. Core Indexing Services

### 3.1. Product Indexing Service (`ProductIndexingService`)

Manages indexing operations for product documents.

#### Key Features:
- `indexProduct(product: ProductDocument)`: Indexes a single product.
- `bulkIndexProducts(products: ProductDocument[])`: Indexes multiple products in a batch.
- `updateProduct(productId: string, updateDoc: Partial<ProductDocument> | Script)`: Updates a product, supporting both partial document updates and scripted updates.
- `deleteProduct(productId: string)`: Deletes a product from the index.
- Handles Elasticsearch responses, including error reporting for bulk operations.
- Interacts with the `products` index (configurable).

#### Implementation Example (TypeScript/NestJS)

(Extended from the `00-overview.md` with more robust error handling and bulk response processing)

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchService } from '@nestjs/elasticsearch'; // Official Elasticsearch client
import { ProductDocument } from '../models/product-document.model'; // Assumes a defined ProductDocument type for ES
import { IndexingException } from '../exceptions/indexing.exception';
import { BulkIndexResult, BulkError } from '../models/bulk-index-result.model';
import { ConfigService } from '@nestjs/config';
import { WriteResponseBase } from '@elastic/elasticsearch/lib/api/types'; // Official ES types

@Injectable()
export class ProductIndexingService {
  private readonly logger = new Logger(ProductIndexingService.name);
  private readonly productIndex: string;

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly configService: ConfigService,
  ) {
    this.productIndex = this.configService.get<string>('elasticsearch.indices.products', 'products-v1');
  }

  async indexProduct(product: ProductDocument): Promise<WriteResponseBase> {
    this.logger.debug(`Indexing product ${product.id} into index ${this.productIndex}`);
    try {
      const response = await this.elasticsearchService.index({
        index: this.productIndex,
        id: product.id.toString(), // Ensure ID is a string
        document: product, // Use 'document' instead of 'body' for v8 client
        refresh: 'wait_for', // Or true/false depending on consistency needs
      });
      this.logger.log(`Successfully indexed product ${product.id}, result: ${response.body.result}`);
      return response.body;
    } catch (error) {
      this.logger.error(
        `Error indexing product ${product.id} into ${this.productIndex}: ${error.message}`,
        error.meta?.body || error.stack,
      );
      throw new IndexingException(`Failed to index product ${product.id}: ${error.message}`, error.meta?.body);
    }
  }

  async bulkIndexProducts(products: ProductDocument[]): Promise<BulkIndexResult> {
    if (!products || products.length === 0) {
      this.logger.warn('Bulk index called with no products.');
      return { successful: 0, failed: 0, errors: [], total: 0, took: 0 };
    }
    this.logger.log(`Bulk indexing ${products.length} products into index ${this.productIndex}`);

    const operations = products.flatMap(product => [
      { index: { _index: this.productIndex, _id: product.id.toString() } },
      product,
    ]);

    try {
      const response = await this.elasticsearchService.bulk({
        refresh: 'wait_for', // Or true/false, or remove for default
        body: operations,
      });
      
      const result = this.processBulkResponse(response.body, products.length);
      this.logger.log(
        `Bulk indexing completed for ${this.productIndex}: ${result.successful} successful, ${result.failed} failed. Took: ${result.took}ms`
      );
      if (result.failed > 0) {
        this.logger.warn(`Bulk indexing errors for ${this.productIndex}: ${JSON.stringify(result.errors)}`);
      }
      return result;
    } catch (error) {
      this.logger.error(
        `Error during bulk indexing products into ${this.productIndex}: ${error.message}`,
        error.meta?.body || error.stack,
      );
      throw new IndexingException('Failed to bulk index products.', error.meta?.body);
    }
  }

  async updateProduct(productId: string, updateDoc: Partial<ProductDocument>): Promise<WriteResponseBase> {
    this.logger.debug(`Updating product ${productId} in index ${this.productIndex}`);
    try {
      const response = await this.elasticsearchService.update({
        index: this.productIndex,
        id: productId,
        doc: updateDoc, // Use 'doc' for partial updates
        refresh: 'wait_for',
      });
      this.logger.log(`Successfully updated product ${productId}, result: ${response.body.result}`);
      return response.body;
    } catch (error) {
      this.logger.error(
        `Error updating product ${productId} in ${this.productIndex}: ${error.message}`,
         error.meta?.body || error.stack,
      );
      if (error.meta?.statusCode === 404) {
        throw new IndexingException(`Product ${productId} not found for update.`, error.meta?.body, 404);
      }
      throw new IndexingException(`Failed to update product ${productId}: ${error.message}`, error.meta?.body);
    }
  }
  
  async upsertProduct(product: ProductDocument): Promise<WriteResponseBase> {
    this.logger.debug(`Upserting product ${product.id} in index ${this.productIndex}`);
    try {
        const response = await this.elasticsearchService.update({
            index: this.productIndex,
            id: product.id.toString(),
            doc: product,
            doc_as_upsert: true, // Key for upsert behavior
            refresh: 'wait_for',
        });
        this.logger.log(`Successfully upserted product ${product.id}, result: ${response.body.result}`);
        return response.body;
    } catch (error) {
        this.logger.error(
            `Error upserting product ${product.id} in ${this.productIndex}: ${error.message}`,
            error.meta?.body || error.stack,
        );
        throw new IndexingException(`Failed to upsert product ${product.id}: ${error.message}`, error.meta?.body);
    }
  }

  async deleteProduct(productId: string): Promise<WriteResponseBase> {
    this.logger.debug(`Deleting product ${productId} from index ${this.productIndex}`);
    try {
      const response = await this.elasticsearchService.delete({
        index: this.productIndex,
        id: productId,
        refresh: 'wait_for',
      });
      this.logger.log(`Successfully deleted product ${productId}, result: ${response.body.result}`);
      return response.body;
    } catch (error) {
      this.logger.error(
        `Error deleting product ${productId} from ${this.productIndex}: ${error.message}`,
        error.meta?.body || error.stack,
      );
       if (error.meta?.statusCode === 404) {
        this.logger.warn(`Product ${productId} not found for deletion from ${this.productIndex}.`);
        // Depending on desired behavior, either throw or return a specific status
        throw new IndexingException(`Product ${productId} not found for deletion.`, error.meta?.body, 404);
      }
      throw new IndexingException(`Failed to delete product ${productId}: ${error.message}`, error.meta?.body);
    }
  }

  private processBulkResponse(responseBody: any, totalRequested: number): BulkIndexResult {
    let successfulCount = 0;
    const errors: BulkError[] = [];

    if (responseBody.errors === false) {
      successfulCount = responseBody.items.length;
    } else {
      responseBody.items.forEach((item: any) => {
        const operation = Object.keys(item)[0]; // index, create, update, delete
        if (item[operation]?.error) {
          errors.push({
            id: item[operation]._id,
            type: item[operation].error.type,
            reason: item[operation].error.reason,
            status: item[operation].status,
          });
        } else {
          successfulCount++;
        }
      });
    }

    return {
      successful: successfulCount,
      failed: errors.length,
      errors,
      total: totalRequested,
      took: responseBody.took,
    };
  }
}
```

### 3.2. Category Indexing Service (`CategoryIndexingService`)

Manages indexing operations for category documents.

#### Key Features:
- `indexCategory(category: CategoryDocument)`
- `bulkIndexCategories(categories: CategoryDocument[])`
- `updateCategory(categoryId: string, updateDoc: Partial<CategoryDocument>)`
- `deleteCategory(categoryId: string)`
- Interacts with the `categories` index.

#### Implementation Sketch:

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { CategoryDocument } from '../models/category-document.model'; 
import { IndexingException } from '../exceptions/indexing.exception';
import { BulkIndexResult } from '../models/bulk-index-result.model';
import { ConfigService } from '@nestjs/config';
import { WriteResponseBase } from '@elastic/elasticsearch/lib/api/types';

@Injectable()
export class CategoryIndexingService {
  private readonly logger = new Logger(CategoryIndexingService.name);
  private readonly categoryIndex: string;

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly configService: ConfigService,
  ) {
    this.categoryIndex = this.configService.get<string>('elasticsearch.indices.categories', 'categories-v1');
  }

  async indexCategory(category: CategoryDocument): Promise<WriteResponseBase> {
    this.logger.debug(`Indexing category ${category.id} into index ${this.categoryIndex}`);
    try {
      const response = await this.elasticsearchService.index({
        index: this.categoryIndex,
        id: category.id.toString(),
        document: category,
        refresh: 'wait_for',
      });
      return response.body;
    } catch (error) {
      this.logger.error(`Error indexing category ${category.id}: ${error.message}`, error.meta?.body);
      throw new IndexingException(`Failed to index category ${category.id}.`, error.meta?.body);
    }
  }

  // Similar bulkIndex, update, delete methods as ProductIndexingService, adapted for CategoryDocument
  async bulkIndexCategories(categories: CategoryDocument[]): Promise<BulkIndexResult> {
    // ... implementation similar to ProductIndexingService.bulkIndexProducts
    return { successful: 0, failed: 0, errors: [], total: 0, took: 0 }; // Placeholder
  }

  async updateCategory(categoryId: string, updateDoc: Partial<CategoryDocument>): Promise<WriteResponseBase> {
    // ... implementation similar to ProductIndexingService.updateProduct
    return {} as WriteResponseBase; // Placeholder
  }

  async deleteCategory(categoryId: string): Promise<WriteResponseBase> {
    // ... implementation similar to ProductIndexingService.deleteProduct
    return {} as WriteResponseBase; // Placeholder
  }
}
```

### 3.3. Content Indexing Service (`ContentIndexingService`)

Manages indexing operations for content documents (articles, FAQs, etc.).

#### Key Features:
- `indexContent(content: ContentDocument)`
- `bulkIndexContent(contents: ContentDocument[])`
- `updateContent(contentId: string, updateDoc: Partial<ContentDocument>)`
- `deleteContent(contentId: string)`
- Interacts with the `content` index.

#### Implementation Sketch:

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { ContentDocument } from '../models/content-document.model'; 
import { IndexingException } from '../exceptions/indexing.exception';
import { BulkIndexResult } from '../models/bulk-index-result.model';
import { ConfigService } from '@nestjs/config';
import { WriteResponseBase } from '@elastic/elasticsearch/lib/api/types';

@Injectable()
export class ContentIndexingService {
  private readonly logger = new Logger(ContentIndexingService.name);
  private readonly contentIndex: string;

  constructor(
    private readonly elasticsearchService: ElasticsearchService,
    private readonly configService: ConfigService,
  ) {
    this.contentIndex = this.configService.get<string>('elasticsearch.indices.content', 'content-v1');
  }

  async indexContent(content: ContentDocument): Promise<WriteResponseBase> {
    this.logger.debug(`Indexing content ${content.id} into index ${this.contentIndex}`);
    try {
      const response = await this.elasticsearchService.index({
        index: this.contentIndex,
        id: content.id.toString(),
        document: content,
        refresh: 'wait_for',
      });
      return response.body;
    } catch (error) {
      this.logger.error(`Error indexing content ${content.id}: ${error.message}`, error.meta?.body);
      throw new IndexingException(`Failed to index content ${content.id}.`, error.meta?.body);
    }
  }
  
  // Similar bulkIndex, update, delete methods as ProductIndexingService, adapted for ContentDocument
  async bulkIndexContent(contents: ContentDocument[]): Promise<BulkIndexResult> {
    // ... implementation similar to ProductIndexingService.bulkIndexProducts
    return { successful: 0, failed: 0, errors: [], total: 0, took: 0 }; // Placeholder
  }

  async updateContent(contentId: string, updateDoc: Partial<ContentDocument>): Promise<WriteResponseBase> {
    // ... implementation similar to ProductIndexingService.updateProduct
    return {} as WriteResponseBase; // Placeholder
  }

  async deleteContent(contentId: string): Promise<WriteResponseBase> {
    // ... implementation similar to ProductIndexingService.deleteProduct
    return {} as WriteResponseBase; // Placeholder
  }
}
```

## 4. Common Patterns & Best Practices

- **Idempotency**: Design indexing operations to be idempotent where possible (e.g., re-indexing a document should have the same result as indexing it the first time, modulo versioning).
- **Refresh Policy**: Carefully choose the `refresh` policy (`true`, `false`, `wait_for`) for indexing operations based on consistency requirements versus performance impact. `wait_for` is often a good balance.
- **Error Handling in Bulk**: For bulk operations, parse the response to identify and log individual item failures. Decide on a strategy for retrying failed items.
- **Optimistic Concurrency Control**: Utilize Elasticsearch's versioning (`if_seq_no`, `if_primary_term`) for conditional updates if needed to prevent race conditions.
- **Configuration**: Index names and other operational parameters should be configurable (e.g., via `ConfigService`).
- **Logging**: Detailed logging of indexing operations, successes, and failures is crucial for monitoring and troubleshooting.
- **Scalability**: For high-volume indexing, consider asynchronous processing and message queues (handled by Event Consumers typically).

## 5. Interactions

- **Event Consumers**: Often the primary callers of Indexing Services, triggering indexing operations in response to data change events from source systems (e.g., `ProductCreatedEvent`).
- **Admin Facade/Services**: May call Indexing Services for manual re-indexing, bulk uploads, or administrative data management tasks.
- **ElasticsearchService (Client Wrapper)**: Indexing Services use this client to interact with Elasticsearch for all write operations.
- **Data Transformers**: May be used upstream (e.g., in Event Consumers or before calling the indexing service) to convert source data into the correct `ProductDocument`, `CategoryDocument`, or `ContentDocument` format.

Indexing Services are fundamental to maintaining the accuracy and freshness of the search data, forming a critical link between the system of record and the search engine.
