# Event Handlers - Search Service with Shared Libraries

## 🎯 Objective
Implement real-time search index updates by handling product events using shared event utilities.

## 🔄 Product Event Handlers

```typescript
// src/events/handlers/product-events.handler.ts
import { Injectable } from '@nestjs/common';
import { EventHandler } from '@ecommerce/rabbitmq-event-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { IndexManagementService } from '../../elasticsearch/index-management.service';

@Injectable()
export class ProductEventsHandler {
  constructor(
    private readonly indexManagementService: IndexManagementService,
    private readonly logger: LoggerService,
  ) {}

  @EventHandler('product.created')
  async handleProductCreated(event: any) {
    try {
      await this.indexManagementService.indexProduct({
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

      this.logger.log('Product indexed after creation', 'ProductEventsHandler', {
        productId: event.productId,
        eventId: event.id,
      });
    } catch (error) {
      this.logger.error('Failed to index created product', error, 'ProductEventsHandler', {
        productId: event.productId,
        eventId: event.id,
      });
    }
  }

  @EventHandler('product.updated')
  async handleProductUpdated(event: any) {
    try {
      // Fetch the updated product data and re-index
      await this.indexManagementService.updateProductIndex(
        event.productId,
        event.changes
      );

      this.logger.log('Product index updated', 'ProductEventsHandler', {
        productId: event.productId,
        changes: Object.keys(event.changes),
        eventId: event.id,
      });
    } catch (error) {
      this.logger.error('Failed to update product index', error, 'ProductEventsHandler', {
        productId: event.productId,
        eventId: event.id,
      });
    }
  }

  @EventHandler('product.deleted')
  async handleProductDeleted(event: any) {
    try {
      await this.indexManagementService.removeProductFromIndex(event.productId);

      this.logger.log('Product removed from index', 'ProductEventsHandler', {
        productId: event.productId,
        eventId: event.id,
      });
    } catch (error) {
      this.logger.error('Failed to remove product from index', error, 'ProductEventsHandler', {
        productId: event.productId,
        eventId: event.id,
      });
    }
  }
}
```

## 📦 Inventory Event Handlers

```typescript
// src/events/handlers/inventory-events.handler.ts
import { Injectable } from '@nestjs/common';
import { EventHandler } from '@ecommerce/rabbitmq-event-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { IndexManagementService } from '../../elasticsearch/index-management.service';

@Injectable()
export class InventoryEventsHandler {
  constructor(
    private readonly indexManagementService: IndexManagementService,
    private readonly logger: LoggerService,
  ) {}

  @EventHandler('inventory.updated')
  async handleInventoryUpdated(event: any) {
    try {
      await this.indexManagementService.updateProductAvailability(
        event.productId,
        {
          inStock: event.newQuantity > 0,
          quantity: event.newQuantity,
        }
      );

      this.logger.log('Product availability updated in search index', 'InventoryEventsHandler', {
        productId: event.productId,
        previousQuantity: event.previousQuantity,
        newQuantity: event.newQuantity,
        eventId: event.id,
      });
    } catch (error) {
      this.logger.error('Failed to update product availability in search', error, 'InventoryEventsHandler', {
        productId: event.productId,
        eventId: event.id,
      });
    }
  }
}
```

## 🎯 Event Handler Module

```typescript
// src/events/event-handler.module.ts
import { Module } from '@nestjs/common';
import { EventModule } from '@ecommerce/rabbitmq-event-utils';

import { ProductEventsHandler } from './handlers/product-events.handler';
import { InventoryEventsHandler } from './handlers/inventory-events.handler';
import { ElasticsearchModule } from '../elasticsearch/elasticsearch.module';
import { IndexManagementService } from '../elasticsearch/index-management.service';

@Module({
  imports: [
    EventModule,
    ElasticsearchModule,
  ],
  providers: [
    IndexManagementService,
    ProductEventsHandler,
    InventoryEventsHandler,
  ],
})
export class EventHandlerModule {}
```

## 🔄 Index Management Extensions

```typescript
// Additional methods for IndexManagementService
export class IndexManagementService {
  // ... existing methods ...

  async updateProductIndex(productId: string, changes: Record<string, any>) {
    try {
      await this.elasticsearchService.update({
        index: this.PRODUCT_INDEX,
        id: productId,
        body: {
          doc: this.transformChangesForIndex(changes),
        },
      });

      this.logger.log('Product index updated', 'IndexManagementService', {
        productId,
        fields: Object.keys(changes),
      });
    } catch (error) {
      this.logger.error('Failed to update product index', error, 'IndexManagementService', {
        productId,
      });
      throw error;
    }
  }

  async updateProductAvailability(productId: string, availability: { inStock: boolean; quantity: number }) {
    try {
      await this.elasticsearchService.update({
        index: this.PRODUCT_INDEX,
        id: productId,
        body: {
          doc: {
            availability,
            updatedAt: new Date(),
          },
        },
      });

      this.logger.log('Product availability updated', 'IndexManagementService', {
        productId,
        availability,
      });
    } catch (error) {
      this.logger.error('Failed to update product availability', error, 'IndexManagementService', {
        productId,
      });
      throw error;
    }
  }

  async removeProductFromIndex(productId: string) {
    try {
      await this.elasticsearchService.delete({
        index: this.PRODUCT_INDEX,
        id: productId,
      });

      this.logger.log('Product removed from index', 'IndexManagementService', {
        productId,
      });
    } catch (error) {
      this.logger.error('Failed to remove product from index', error, 'IndexManagementService', {
        productId,
      });
      throw error;
    }
  }

  private transformChangesForIndex(changes: Record<string, any>) {
    const indexChanges: any = {};
    
    // Map changes to index fields
    if (changes.name) indexChanges.name = changes.name;
    if (changes.description) indexChanges.description = changes.description;
    if (changes.price) indexChanges.price = parseFloat(changes.price);
    if (changes.brand) indexChanges.brand = changes.brand;
    if (changes.tags) indexChanges.tags = changes.tags;
    
    indexChanges.updatedAt = new Date();
    
    return indexChanges;
  }
}
```