# Index Update Logic

## Overview

After an event has been consumed, validated, and transformed into a search document (e.g., `ProductDocument`, `CategoryDocument`), the next crucial step is to apply this change to the corresponding Elasticsearch index. This involves using the Elasticsearch client to perform Create, Read (for conditional updates), Update, or Delete (CRUD) operations.

## Elasticsearch Client

The Search Service will use an Elasticsearch client library compatible with NestJS. The official `@elastic/elasticsearch` client is a common choice.

**Integration (Conceptual `elasticsearch.module.ts`):**
```typescript
import { Module, Global } from '@nestjs/common';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { ConfigService } from '@nestjs/config';

// @Global() // Optionally make it global if used widely
@Module({
  imports: [],
  providers: [
    {
      provide: ElasticsearchService,
      useFactory: async (configService: ConfigService) => {
        return new ElasticsearchService({
          node: configService.get<string>('elasticsearch.node'), // e.g., 'http://localhost:9200'
          // Other options: cloud: { id: '...' }, auth, etc.
          // maxRetries: 5,
          // requestTimeout: 60000,
        });
      },
      inject: [ConfigService],
    },
  ],
  exports: [ElasticsearchService],
})
export class CustomElasticsearchModule {}
```
This module would then be imported into other modules that need to interact with Elasticsearch, like the `IndexingService`.

## Indexing Service

A dedicated `IndexingService` (as shown in previous examples) will encapsulate all interactions with Elasticsearch for updating indexes.

```typescript
// src/search/services/indexing.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { ProductDocument } from '../interfaces/product-document.interface';
// Import other document types (CategoryDocument, ContentDocument)

@Injectable()
export class IndexingService {
  private readonly logger = new Logger(IndexingService.name);
  private readonly processedEventIds = new Set<string>(); // Simple in-memory store for idempotency demo

  constructor(private readonly esService: ElasticsearchService) {}

  // --- Idempotency Example --- 
  // In a real system, this would use a persistent store (Redis, DB) or leverage Elasticsearch itself.
  async hasProcessed(eventId: string): Promise<boolean> {
    if (this.processedEventIds.has(eventId)) {
      this.logger.log(`Event ${eventId} already processed.`);
      return true;
    }
    return false;
  }

  async markAsProcessed(eventId: string): Promise<void> {
    // Add to persistent store in a real scenario
    this.processedEventIds.add(eventId);
    // Optional: Clean up old event IDs from the set/store periodically
  }

  // --- Product Indexing --- 
  async indexProduct(document: ProductDocument, eventId: string, indexName = 'products'): Promise<void> {
    if (await this.hasProcessed(eventId)) return;

    try {
      await this.esService.index({
        index: indexName,
        id: document.id, // Use product ID as Elasticsearch document ID
        document: document,
        // refresh: 'wait_for', // Or true/false - consider performance implications
      });
      this.logger.log(`Indexed product ${document.id} successfully (Event: ${eventId}).`);
      await this.markAsProcessed(eventId);
    } catch (error) {
      this.logger.error(`Error indexing product ${document.id} (Event: ${eventId}):`, error.meta?.body || error);
      throw error; // Re-throw to be handled by event processing error strategy (DLQ, retry)
    }
  }

  async updateProduct(productId: string, partialDocument: Partial<ProductDocument>, eventId: string, indexName = 'products'): Promise<void> {
    if (await this.hasProcessed(eventId)) return;

    try {
      // Using 'update' with a script or doc for partial updates
      await this.esService.update({
        index: indexName,
        id: productId,
        doc: partialDocument,
        // refresh: 'wait_for',
      });
      this.logger.log(`Updated product ${productId} successfully (Event: ${eventId}).`);
      await this.markAsProcessed(eventId);
    } catch (error) {
      // Handle potential 'document_missing_exception' if needed, though update can upsert with 'doc_as_upsert'
      this.logger.error(`Error updating product ${productId} (Event: ${eventId}):`, error.meta?.body || error);
      throw error;
    }
  }

  async deleteProduct(productId: string, eventId: string, indexName = 'products'): Promise<void> {
    if (await this.hasProcessed(eventId)) return;

    try {
      await this.esService.delete({
        index: indexName,
        id: productId,
        // refresh: 'wait_for',
      });
      this.logger.log(`Deleted product ${productId} successfully (Event: ${eventId}).`);
      await this.markAsProcessed(eventId);
    } catch (error) {
      if (error.meta?.statusCode === 404) {
        this.logger.warn(`Product ${productId} not found for deletion (Event: ${eventId}). Already deleted?`);
        await this.markAsProcessed(eventId); // Mark as processed if it's a 404 on delete
        return;
      }
      this.logger.error(`Error deleting product ${productId} (Event: ${eventId}):`, error.meta?.body || error);
      throw error;
    }
  }

  // --- Methods for Category Indexing (similar to product) ---
  // async indexCategory(document: CategoryDocument, eventId: string, indexName = 'categories') { ... }
  // async updateCategory(categoryId: string, partialDocument: Partial<CategoryDocument>, eventId: string, indexName = 'categories') { ... }
  // async deleteCategory(categoryId: string, eventId: string, indexName = 'categories') { ... }

  // --- Methods for Content Indexing (similar to product) ---
  // async indexContent(document: ContentDocument, eventId: string, indexName = 'content') { ... }
  // async updateContent(contentId: string, partialDocument: Partial<ContentDocument>, eventId: string, indexName = 'content') { ... }
  // async deleteContent(contentId: string, eventId: string, indexName = 'content') { ... }

  // --- Bulk Operations --- 
  // For scenarios where multiple documents need to be indexed/updated/deleted from a single event or a batch of events.
  async bulkIndexDocuments(documents: Array<{ index: string; id: string; document: any }>, eventId?: string): Promise<void> {
    // Note: Idempotency for bulk operations needs careful consideration. 
    // If eventId pertains to the whole batch, mark it. If individual items can fail/succeed,
    // idempotency might need to be at the individual document level if retried.

    if (!documents.length) return;

    const operations = documents.flatMap(doc => [{ index: { _index: doc.index, _id: doc.id } }, doc.document]);

    try {
      const bulkResponse = await this.esService.bulk({
        refresh: false, // 'wait_for' or true can impact performance significantly
        operations,
      });

      if (bulkResponse.errors) {
        const erroredDocuments = [];
        bulkResponse.items.forEach((action, i) => {
          const operation = Object.keys(action)[0];
          if (action[operation].error) {
            erroredDocuments.push({
              // Depending on your source documents, you might have more info to log
              id: documents[i].id,
              error: action[operation].error,
            });
          }
        });
        this.logger.error(`Bulk indexing completed with errors (Event: ${eventId || 'N/A'}):`, erroredDocuments);
        // Decide on error handling: throw an error to trigger DLQ for the whole batch, 
        // or attempt to DLQ/log only failed items (more complex).
        throw new Error('Bulk indexing had failures.'); 
      } else {
        this.logger.log(`Bulk operation successful (Event: ${eventId || 'N/A'}). ${documents.length} documents processed.`);
        if (eventId) await this.markAsProcessed(eventId); // If batch is tied to a single eventId
      }
    } catch (error) {
      this.logger.error(`Error during bulk operation (Event: ${eventId || 'N/A'}):`, error);
      throw error;
    }
  }
}
```

## CRUD Operations Logic

1.  **Create (`ProductCreated`, `ContentPublished`):**
    *   Use the `index` API of Elasticsearch.
    *   The document ID in Elasticsearch should be the natural ID of the entity (e.g., `product.id`). This makes updates and deletions straightforward and ensures uniqueness.

2.  **Update (`ProductUpdated`, `PriceChanged`, `StockChanged`):**
    *   **Full Update**: If the event contains the complete, updated entity, the `index` API can be used (same as create). Elasticsearch will overwrite the existing document with the same ID.
    *   **Partial Update**: If the event contains only changed fields, use the `update` API. This is more efficient as it avoids re-indexing unchanged data.
        *   `doc`: Send the partial document.
        *   `script`: For more complex updates (e.g., incrementing a counter, adding to an array if item doesn't exist).
        *   `doc_as_upsert`: Can be useful if an `update` event might arrive for a document not yet created (e.g., due to event ordering issues). It will create the document if it doesn't exist.

3.  **Delete (`ProductDeleted`, `ContentUnpublished` if it means removal):**
    *   Use the `delete` API with the document ID.
    *   Handle `404 Not Found` errors gracefully, as a delete event might arrive after the document has already been deleted (or was never created due to an earlier issue).

## Idempotency in Indexing

As highlighted in the `IndexingService` example:

*   **Mechanism**: Before performing an Elasticsearch operation, check if the `eventId` has been processed.
*   **Storage for Event IDs**: Use a persistent, fast key-value store (e.g., Redis, a dedicated DB table) or even a separate Elasticsearch index to track processed event IDs. The in-memory `Set` is for demonstration only and not suitable for production with multiple service instances.
*   **Mark as Processed**: Only mark an event ID as processed *after* the Elasticsearch operation is confirmed successful. If the ES operation fails, the event is not marked, allowing retries to attempt it again.
*   **Atomicity**: If possible, the check for processed ID and marking it as processed should be atomic with the main operation, or at least robust against failures between steps.

## Refresh Policy

*   `refresh` parameter in Elasticsearch operations (`false`, `true`, `wait_for`).
*   `false` (default): Changes are made available for search after the next scheduled refresh (default 1s). Best for indexing throughput.
*   `true`: Force a refresh immediately. Poor for performance, use sparingly.
*   `wait_for`: Waits for the changes to be visible to search before returning. Impacts latency but ensures read-your-writes consistency if needed immediately after an update.
*   For event-driven updates, `false` is usually appropriate, relying on eventual consistency. If immediate visibility is critical for a specific event type, `wait_for` might be considered with caution.

## Error Handling

*   The `IndexingService` should catch errors from the Elasticsearch client.
*   Specific ES errors (e.g., mapping conflicts, malformed queries) should be logged with detail.
*   Generic errors or transient issues (e.g., network problems) should allow for retries.
*   Persistent errors should lead to the event being sent to a Dead Letter Queue (DLQ).
*   These are further detailed in `08-error-handling-and-resilience.md`.

## Next Steps

*   `08-error-handling-and-resilience.md`: Deep dive into strategies for retries, DLQs, and ensuring robust event processing.
