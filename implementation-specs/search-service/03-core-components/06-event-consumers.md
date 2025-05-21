# Event Consumers

## 1. Introduction

Event Consumers are responsible for listening to domain events originating from other microservices or parts of the system (e.g., Product Service, Order Service, CMS) and reacting to them by updating the search indices. They form the backbone of the real-time or near real-time synchronization between the source-of-truth systems and the Search Service.

Typically, these consumers subscribe to messages from a message broker like Apache Kafka, RabbitMQ, or AWS SQS/SNS.

## 2. Responsibilities

- **Event Subscription**: Subscribe to relevant topics or queues on a message broker.
- **Event Deserialization**: Deserialize incoming event messages into structured event objects (e.g., `ProductCreatedEvent`, `CategoryUpdatedEvent`).
- **Data Transformation**: Transform the data from the event payload into the format required by the Elasticsearch document schema (e.g., transforming a `ProductDTO` from Product Service into a `ProductDocument` for Elasticsearch). This is often delegated to a dedicated Transformer component.
- **Invoking Indexing Services**: Call the appropriate Indexing Service methods (e.g., `ProductIndexingService.indexProduct()`, `CategoryIndexingService.updateCategory()`) to persist changes to Elasticsearch.
- **Error Handling**: Implement robust error handling for event processing, including:
    - Retries for transient errors.
    - Dead-Letter Queue (DLQ) for events that consistently fail processing.
    - Logging of errors and problematic events.
- **Idempotency**: Ensure that processing the same event multiple times (due to retries or message broker guarantees) does not cause adverse effects (e.g., by using optimistic locking or checking document versions).
- **Filtering Irrelevant Events**: Discard events that are not relevant to the search index or do not require an update.

## 3. Core Event Consumers

Each major entity managed by the Search Service will typically have its own set of event consumers.

### 3.1. Product Event Consumer (`ProductEventConsumer`)

Listens to events related to products (e.g., from a Product Information Management system or Product Service).

#### Key Events Handled:
- `product.created`: A new product is created.
- `product.updated`: An existing product's details are updated.
- `product.deleted`: A product is removed.
- `product.price.updated`: A product's price changes (might be part of `product.updated` or a separate event).
- `product.inventory.updated`: A product's stock status or quantity changes.

#### Implementation Example (TypeScript/NestJS with Kafka)

(Extended from `00-overview.md` with more robust error handling and transformation)

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { OnEvent } from '@nestjs/event-emitter'; // Using NestJS EventEmitter for internal events as example, or @MessagePattern for Kafka via @nestjs/microservices
import { ProductIndexingService } from './indexing/product-indexing.service';
import { ProductTransformer } from '../transformers/product.transformer'; // Dedicated transformer
import { 
    ProductCreatedEvent, 
    ProductUpdatedEvent, 
    ProductDeletedEvent, 
    ProductInventoryUpdatedEvent 
} from '../events/product.events'; // Define these event DTOs
import { SearchServiceMessageProducer } from '../producers/search-service-message.producer'; // For DLQ or retry topics

@Injectable()
export class ProductEventConsumer {
  private readonly logger = new Logger(ProductEventConsumer.name);

  constructor(
    private readonly productIndexingService: ProductIndexingService,
    private readonly productTransformer: ProductTransformer,
    private readonly dlqProducer: SearchServiceMessageProducer, // Example: for sending to DLQ
  ) {}

  // Example for Kafka using @nestjs/microservices (requires Kafka setup)
  // @MessagePattern('topic.product.created') // Or use specific client
  // async handleProductCreatedKafka(payload: KafkaMessage<ProductCreatedEventPayload>) {
  //    const event = payload.value; 
  //    // ... process ...
  // }

  @OnEvent('product.created') // Using NestJS internal event emitter for simplicity here
  async handleProductCreated(eventPayload: ProductCreatedEvent): Promise<void> {
    this.logger.log(`Received product.created event for ID: ${eventPayload.product.id}`);
    try {
      const productDocument = this.productTransformer.transformToDocument(eventPayload.product);
      await this.productIndexingService.indexProduct(productDocument);
      this.logger.log(`Successfully indexed new product ${eventPayload.product.id}`);
    } catch (error) {
      this.logger.error(
        `Error processing product.created event for ${eventPayload.product.id}: ${error.message}`,
        error.stack,
      );
      // Send to DLQ or implement retry logic
      await this.dlqProducer.sendToDlq('product.created', eventPayload, error);
    }
  }

  @OnEvent('product.updated')
  async handleProductUpdated(eventPayload: ProductUpdatedEvent): Promise<void> {
    this.logger.log(`Received product.updated event for ID: ${eventPayload.product.id}`);
    try {
      // For updates, it's often better to fetch the latest full state if the event is partial
      // or ensure the event contains all necessary fields for the ProductDocument.
      const productDocument = this.productTransformer.transformToDocument(eventPayload.product);
      // Using upsert to handle cases where the document might not exist yet (e.g., if create event was missed)
      await this.productIndexingService.upsertProduct(productDocument);
      this.logger.log(`Successfully updated/upserted product ${eventPayload.product.id}`);
    } catch (error) {
      this.logger.error(
        `Error processing product.updated event for ${eventPayload.product.id}: ${error.message}`,
        error.stack,
      );
      await this.dlqProducer.sendToDlq('product.updated', eventPayload, error);
    }
  }

  @OnEvent('product.deleted')
  async handleProductDeleted(eventPayload: ProductDeletedEvent): Promise<void> {
    this.logger.log(`Received product.deleted event for ID: ${eventPayload.productId}`);
    try {
      await this.productIndexingService.deleteProduct(eventPayload.productId);
      this.logger.log(`Successfully deleted product ${eventPayload.productId}`);
    } catch (error) {
      this.logger.error(
        `Error processing product.deleted event for ${eventPayload.productId}: ${error.message}`,
        error.stack,
      );
      // Deletion failures might be critical or ignorable if already deleted
      // Consider specific error handling based on error type (e.g., 404)
      if (error.status !== 404) { // Example: only DLQ if not a 'not found' error
        await this.dlqProducer.sendToDlq('product.deleted', eventPayload, error);
      }
    }
  }
  
  @OnEvent('product.inventory.updated')
  async handleProductInventoryUpdated(eventPayload: ProductInventoryUpdatedEvent): Promise<void> {
    this.logger.log(`Received product.inventory.updated event for ID: ${eventPayload.productId}`);
    try {
      // This is a partial update, so we only send the fields that changed.
      const partialUpdateDoc = this.productTransformer.transformInventoryUpdateToPartialDocument(eventPayload);
      if (Object.keys(partialUpdateDoc).length > 0) {
          await this.productIndexingService.updateProduct(eventPayload.productId, partialUpdateDoc);
          this.logger.log(`Successfully updated inventory for product ${eventPayload.productId}`);
      } else {
          this.logger.warn(`No relevant inventory fields to update for product ${eventPayload.productId} from event.`);
      }
    } catch (error) {
      this.logger.error(
        `Error processing product.inventory.updated for ${eventPayload.productId}: ${error.message}`,
        error.stack,
      );
      await this.dlqProducer.sendToDlq('product.inventory.updated', eventPayload, error);
    }
  }
}
```

### 3.2. Category Event Consumer (`CategoryEventConsumer`)

Listens to events related to categories (e.g., from a PIM or an Admin panel for category management).

#### Key Events Handled:
- `category.created`
- `category.updated` (name, description, hierarchy changes, etc.)
- `category.deleted`
- `category.moved` (if parent changes, affecting path and level)

#### Implementation Sketch:

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { OnEvent } from '@nestjs/event-emitter';
import { CategoryIndexingService } from './indexing/category-indexing.service';
import { CategoryTransformer } from '../transformers/category.transformer';
import { CategoryCreatedEvent, CategoryUpdatedEvent, CategoryDeletedEvent } from '../events/category.events';
import { SearchServiceMessageProducer } from '../producers/search-service-message.producer';

@Injectable()
export class CategoryEventConsumer {
  private readonly logger = new Logger(CategoryEventConsumer.name);

  constructor(
    private readonly categoryIndexingService: CategoryIndexingService,
    private readonly categoryTransformer: CategoryTransformer,
    private readonly dlqProducer: SearchServiceMessageProducer,
  ) {}

  @OnEvent('category.created')
  async handleCategoryCreated(eventPayload: CategoryCreatedEvent): Promise<void> {
    this.logger.log(`Received category.created event for ID: ${eventPayload.category.id}`);
    try {
      const categoryDocument = this.categoryTransformer.transformToDocument(eventPayload.category);
      await this.categoryIndexingService.indexCategory(categoryDocument);
      this.logger.log(`Successfully indexed new category ${eventPayload.category.id}`);
    } catch (error) {
      this.logger.error(`Error processing category.created for ${eventPayload.category.id}: ${error.message}`, error.stack);
      await this.dlqProducer.sendToDlq('category.created', eventPayload, error);
    }
  }

  @OnEvent('category.updated')
  async handleCategoryUpdated(eventPayload: CategoryUpdatedEvent): Promise<void> {
    this.logger.log(`Received category.updated event for ID: ${eventPayload.category.id}`);
    try {
      const categoryDocument = this.categoryTransformer.transformToDocument(eventPayload.category);
      // Upsert might be safer if create event was missed
      await this.categoryIndexingService.updateCategory(eventPayload.category.id, categoryDocument); 
      this.logger.log(`Successfully updated category ${eventPayload.category.id}`);
      
      // If hierarchy changed, might need to update children paths too (more complex logic)
      if (eventPayload.hierarchyChanged) {
          // this.logger.log(`Category hierarchy changed for ${eventPayload.category.id}, potential child updates needed.`);
          // Potentially trigger a separate process to update descendant paths if not handled by transformer
      }
    } catch (error) {
      this.logger.error(`Error processing category.updated for ${eventPayload.category.id}: ${error.message}`, error.stack);
      await this.dlqProducer.sendToDlq('category.updated', eventPayload, error);
    }
  }

  @OnEvent('category.deleted')
  async handleCategoryDeleted(eventPayload: CategoryDeletedEvent): Promise<void> {
    this.logger.log(`Received category.deleted event for ID: ${eventPayload.categoryId}`);
    try {
      await this.categoryIndexingService.deleteCategory(eventPayload.categoryId);
      this.logger.log(`Successfully deleted category ${eventPayload.categoryId}`);
      // Consider implications for products in this category (they might need re-indexing or denormalized data updated)
    } catch (error) {
      this.logger.error(`Error processing category.deleted for ${eventPayload.categoryId}: ${error.message}`, error.stack);
      if (error.status !== 404) {
         await this.dlqProducer.sendToDlq('category.deleted', eventPayload, error);
      }
    }
  }
}
```

### 3.3. Content Event Consumer (`ContentEventConsumer`)

Listens to events related to content (e.g., from a CMS or blog platform).

#### Key Events Handled:
- `content.published` (could be create or update)
- `content.updated`
- `content.unpublished` (status change)
- `content.deleted`

#### Implementation Sketch:

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { OnEvent } from '@nestjs/event-emitter';
import { ContentIndexingService } from './indexing/content-indexing.service';
import { ContentTransformer } from '../transformers/content.transformer';
import { ContentPublishedEvent, ContentUpdatedEvent, ContentDeletedEvent } from '../events/content.events';
import { SearchServiceMessageProducer } from '../producers/search-service-message.producer';

@Injectable()
export class ContentEventConsumer {
  private readonly logger = new Logger(ContentEventConsumer.name);

  constructor(
    private readonly contentIndexingService: ContentIndexingService,
    private readonly contentTransformer: ContentTransformer,
    private readonly dlqProducer: SearchServiceMessageProducer,
  ) {}

  @OnEvent('content.published') // Combines create and update to published status
  async handleContentPublished(eventPayload: ContentPublishedEvent): Promise<void> {
    this.logger.log(`Received content.published event for ID: ${eventPayload.content.id}`);
    try {
      const contentDocument = this.contentTransformer.transformToDocument(eventPayload.content);
      // Assuming upsert logic for published content
      await this.contentIndexingService.updateContent(eventPayload.content.id, contentDocument); // Or a dedicated upsert
      this.logger.log(`Successfully indexed/updated published content ${eventPayload.content.id}`);
    } catch (error) {
      this.logger.error(`Error processing content.published for ${eventPayload.content.id}: ${error.message}`, error.stack);
      await this.dlqProducer.sendToDlq('content.published', eventPayload, error);
    }
  }
  
  @OnEvent('content.updated') // For updates that don't change published status directly but affect indexed data
  async handleContentUpdated(eventPayload: ContentUpdatedEvent): Promise<void> {
    this.logger.log(`Received content.updated event for ID: ${eventPayload.content.id}`);
    try {
      const contentDocument = this.contentTransformer.transformToDocument(eventPayload.content);
      await this.contentIndexingService.updateContent(eventPayload.content.id, contentDocument);
      this.logger.log(`Successfully updated content ${eventPayload.content.id}`);
    } catch (error) {
      this.logger.error(`Error processing content.updated for ${eventPayload.content.id}: ${error.message}`, error.stack);
      await this.dlqProducer.sendToDlq('content.updated', eventPayload, error);
    }
  }

  @OnEvent('content.unpublished') // Example of status change leading to deletion or status update in index
  async handleContentUnpublished(eventPayload: { contentId: string }): Promise<void> {
    this.logger.log(`Received content.unpublished event for ID: ${eventPayload.contentId}`);
    try {
      // Option 1: Delete from index
      // await this.contentIndexingService.deleteContent(eventPayload.contentId);
      // Option 2: Update status in index to 'unpublished' if it needs to be searchable by admins
      await this.contentIndexingService.updateContent(eventPayload.contentId, { status: 'unpublished' } as any);
      this.logger.log(`Successfully marked content ${eventPayload.contentId} as unpublished.`);
    } catch (error) {
      this.logger.error(`Error processing content.unpublished for ${eventPayload.contentId}: ${error.message}`, error.stack);
      await this.dlqProducer.sendToDlq('content.unpublished', eventPayload, error);
    }
  }

  @OnEvent('content.deleted')
  async handleContentDeleted(eventPayload: ContentDeletedEvent): Promise<void> {
    this.logger.log(`Received content.deleted event for ID: ${eventPayload.contentId}`);
    try {
      await this.contentIndexingService.deleteContent(eventPayload.contentId);
      this.logger.log(`Successfully deleted content ${eventPayload.contentId}`);
    } catch (error) {
      this.logger.error(`Error processing content.deleted for ${eventPayload.contentId}: ${error.message}`, error.stack);
      if (error.status !== 404) {
        await this.dlqProducer.sendToDlq('content.deleted', eventPayload, error);
      }
    }
  }
}
```

## 4. Data Transformers (`*.transformer.ts`)

While not Event Consumers themselves, Transformers are crucial collaborators.
- **Responsibility**: Convert DTOs from external events or source systems into the specific `ProductDocument`, `CategoryDocument`, or `ContentDocument` structure required by Elasticsearch.
- **Example** (`ProductTransformer`):
  ```typescript
  import { Injectable } from '@nestjs/common';
  import { ProductSourceDto } from '../dtos/product-source.dto'; // DTO from Product Service event
  import { ProductDocument } from '../models/product-document.model';
  import { ProductInventoryUpdatedEvent } from '../events/product.events';

  @Injectable()
  export class ProductTransformer {
    transformToDocument(sourceDto: ProductSourceDto): ProductDocument {
      // Comprehensive mapping from sourceDto to ProductDocument fields
      // This includes handling nested structures, data type conversions, etc.
      return {
        id: sourceDto.id,
        sku: sourceDto.sku,
        name: sourceDto.name,
        description: sourceDto.fullDescription,
        short_description: sourceDto.shortSummary,
        slug: sourceDto.urlSlug,
        status: sourceDto.isActive ? 'active' : 'inactive',
        visibility: sourceDto.isPublic ? 'visible' : 'hidden',
        created_at: sourceDto.creationDate,
        updated_at: sourceDto.lastModifiedDate,
        published_at: sourceDto.publishDate,
        type: sourceDto.productType,
        categories: sourceDto.categories?.map(c => ({ id: c.id, name: c.name, path: c.pathString, level: c.hierarchyLevel, position: c.sortOrder })) || [],
        brand: sourceDto.brand ? { id: sourceDto.brand.id, name: sourceDto.brand.name, logo_url: sourceDto.brand.logo } : undefined,
        pricing: {
          currency: sourceDto.price.currency,
          list_price: sourceDto.price.list,
          sale_price: sourceDto.price.sale,
          // ... other pricing fields from schema
        },
        inventory: {
          in_stock: sourceDto.stock.available > 0,
          quantity: sourceDto.stock.available,
          availability: sourceDto.stock.status,
          // ... other inventory fields from schema
        },
        attributes: {
            // Map fixed attributes like color, size if they exist directly
            // Then map custom/dynamic attributes
            custom_attributes: sourceDto.customAttributes?.map(attr => ({
                code: attr.code,
                label: attr.displayName,
                value: attr.value, // This needs careful handling for 'any' type
                value_text: String(attr.value), // Ensure a searchable text representation
                filterable: attr.isFilterable,
                searchable: attr.isSearchable
            })) || []
        },
        // ... map all other fields as per ProductDocumentSchema (media, seo, ratings, etc.)
        media: { thumbnail: sourceDto.mainImage, images: sourceDto.galleryImages?.map(i=>({url: i.url, alt: i.altText})) || [] },
        seo: { title: sourceDto.metaTitle, description: sourceDto.metaDescription },
        ratings: { average: sourceDto.avgRating, count: sourceDto.ratingCount },
        tags: sourceDto.tags || [],
        search_data: {
            search_keywords: sourceDto.additionalKeywords || [],
            popularity_score: sourceDto.popularity, // Assuming a popularity field
            // ... other search_data fields
        },
        metadata: { tenant_id: sourceDto.tenantId, version: sourceDto.version }
      } as ProductDocument; // Cast as ProductDocument to ensure all fields are considered
    }

    transformInventoryUpdateToPartialDocument(event: ProductInventoryUpdatedEvent): Partial<ProductDocument> {
        const partialDoc: Partial<ProductDocument> = {};
        const inventoryUpdate: Partial<ProductDocument['inventory']> = {};

        if (event.quantity !== undefined) {
            inventoryUpdate.quantity = event.quantity;
            inventoryUpdate.in_stock = event.quantity > 0;
        }
        if (event.availabilityStatus) {
            inventoryUpdate.availability = event.availabilityStatus;
            if (event.availabilityStatus === 'out_of_stock') {
                 inventoryUpdate.in_stock = false;
            }
        }
        if (Object.keys(inventoryUpdate).length > 0) {
            partialDoc.inventory = inventoryUpdate;
        }
        partialDoc.updated_at = new Date().toISOString();
        return partialDoc;
    }
  }
  ```

## 5. Common Patterns & Best Practices

- **Message Broker Choice**: Select a message broker that fits the system's scalability and reliability needs.
- **Event Schema Definition**: Clearly define event schemas (e.g., using Avro, Protobuf, or JSON Schema) and maintain a schema registry if possible.
- **Dedicated Transformers**: Separate data transformation logic into dedicated Transformer classes for better testability and maintainability.
- **DLQ Strategy**: Implement a robust Dead-Letter Queue strategy to handle events that cannot be processed after several retries. Monitor the DLQ for recurring issues.
- **Monitoring and Alerting**: Monitor event consumption rates, error rates, and queue lengths. Set up alerts for critical failures or high DLQ volumes.
- **Batching (if supported)**: Some message brokers and Elasticsearch clients support batching of messages/operations, which can improve throughput.
- **Concurrency Control**: Configure consumer concurrency appropriately to balance throughput with resource utilization and potential ordering constraints.
- **Stateless Consumers**: Aim for stateless consumers where possible. If state is needed, manage it carefully (e.g., in a distributed cache or database).

## 6. Interactions

- **Message Broker**: Event Consumers subscribe to topics/queues on the message broker.
- **Indexing Services**: After transforming an event, consumers call methods on the appropriate Indexing Service to update Elasticsearch.
- **Data Transformers**: Consumers utilize Transformer components to map event data to Elasticsearch document schemas.
- **DLQ Producer (Optional)**: For sending poison pill messages or unprocessable events to a Dead-Letter Queue.
- **Source Systems**: (Indirectly) Events originate from various source systems like PIM, CMS, Order Management, etc.

Event Consumers are essential for maintaining data consistency and freshness in the Search Service by reacting to changes across the e-commerce platform in an event-driven manner.
