# Event Publishing - Updated with Shared Libraries

## 🎯 Objective

Implement reliable event publishing using the enterprise-grade `@ecommerce/rabbitmq-event-utils` shared library with transactional outbox pattern.

## 🏗️ Architecture Changes

**❌ Before**: Inline event publishing with potential data consistency issues  
**✅ After**: Shared library with transactional outbox pattern for guaranteed delivery

---

## 🔧 Event Publishing Implementation

### Product Events Definition

```typescript
// src/events/product.events.ts
import { DomainEvent } from '@ecommerce/rabbitmq-event-utils';

export class ProductCreatedEvent extends DomainEvent {
  constructor(
    public readonly productId: string,
    public readonly name: string,
    public readonly price: number,
    public readonly categoryId: string,
    public readonly sellerId: string,
  ) {
    super('product.created', '1.0.0');
  }
}

export class ProductUpdatedEvent extends DomainEvent {
  constructor(
    public readonly productId: string,
    public readonly changes: Record<string, any>,
    public readonly previousVersion: number,
    public readonly newVersion: number,
  ) {
    super('product.updated', '1.0.0');
  }
}
```export class ProductDeletedEvent extends DomainEvent {
  constructor(
    public readonly productId: string,
    public readonly reason: string,
  ) {
    super('product.deleted', '1.0.0');
  }
}

export class InventoryUpdatedEvent extends DomainEvent {
  constructor(
    public readonly productId: string,
    public readonly previousQuantity: number,
    public readonly newQuantity: number,
    public readonly reason: 'sale' | 'restock' | 'adjustment',
  ) {
    super('inventory.updated', '1.0.0');
  }
}
```

### Updated Product Service with Event Publishing

```typescript
// src/product/product.service.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, DataSource } from 'typeorm';

// Import shared utilities
import { LoggerService } from '@ecommerce/nestjs-core-utils';
import { EventPublisher } from '@ecommerce/rabbitmq-event-utils';

import { Product } from './entities/product.entity';
import { CreateProductDto } from './dto/create-product.dto';
import { ProductCreatedEvent, ProductUpdatedEvent, ProductDeletedEvent } from '../events/product.events';

@Injectable()
export class ProductService {
  constructor(
    @InjectRepository(Product)
    private readonly productRepository: Repository<Product>,
    private readonly dataSource: DataSource,
    private readonly logger: LoggerService,
    private readonly eventPublisher: EventPublisher,
  ) {}

  async createProduct(createProductDto: CreateProductDto, sellerId: string): Promise<Product> {
    return await this.dataSource.transaction(async (manager) => {
      try {
        // Create product
        const product = manager.create(Product, {
          ...createProductDto,
          sellerId,
        });
        
        const savedProduct = await manager.save(product);

        // Publish event using shared library (transactional outbox)
        const event = new ProductCreatedEvent(
          savedProduct.id,
          savedProduct.name,
          savedProduct.price,
          savedProduct.categoryId,
          sellerId,
        );

        await this.eventPublisher.publishWithTransaction(event, manager);

        this.logger.log('Product created successfully', 'ProductService', {
          productId: savedProduct.id,
          sellerId,
        });

        return savedProduct;
      } catch (error) {
        this.logger.error('Failed to create product', error, 'ProductService', {
          sellerId,
          name: createProductDto.name,
        });
        throw error;
      }
    });
  }
```