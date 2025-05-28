# Tutorial 10: Performance Optimization

## 🎯 Objective
Implement caching, database optimization, and performance monitoring.

## Step 1: Redis Caching

```bash
pnpm add cache-manager cache-manager-redis-store redis
```

**src/modules/cache/cache.module.ts:**
```typescript
import { Module, CacheModule } from '@nestjs/common';
import * as redisStore from 'cache-manager-redis-store';

@Module({
  imports: [
    CacheModule.register({
      store: redisStore,
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      ttl: 300, // 5 minutes
    }),
  ],
  exports: [CacheModule],
})
export class AppCacheModule {}
```

## Step 2: Cached Product Service

**src/modules/products/services/product.service.ts:**
```typescript
import { Injectable, CacheInterceptor, UseInterceptors } from '@nestjs/common';

@Injectable()
export class ProductService {
  @UseInterceptors(CacheInterceptor)
  async findAll(page = 1, limit = 10): Promise<Product[]> {
    return await this.productRepository.find({
      relations: ['category', 'variants'],
      skip: (page - 1) * limit,
      take: limit,
    });
  }

  @UseInterceptors(CacheInterceptor)
  async findOne(id: string): Promise<Product> {
    // Implementation with caching
  }
}
```

## Step 3: Database Indexing

**migrations/add-product-indexes.ts:**
```typescript
import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddProductIndexes implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE INDEX idx_products_slug ON products(slug)`);
    await queryRunner.query(`CREATE INDEX idx_products_category ON products(category_id)`);
    await queryRunner.query(`CREATE INDEX idx_products_active ON products(is_active)`);
  }
}
```

## ✅ Next Steps
Continue with **[11-monitoring.md](./11-monitoring.md)** for CloudWatch integration.