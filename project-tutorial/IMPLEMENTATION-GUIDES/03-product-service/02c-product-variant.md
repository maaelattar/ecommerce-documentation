# Tutorial 2c: Product Variant Entity

## 🎯 Objective
Create ProductVariant entity for handling different product options (size, color, etc.).

## Step 1: Product Variant Entity

**src/modules/products/entities/product-variant.entity.ts:**
```typescript
import { Entity, Column, PrimaryGeneratedColumn, ManyToOne } from 'typeorm';
import { Product } from './product.entity';

@Entity('product_variants')
export class ProductVariant {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  sku: string;

  @Column('decimal', { precision: 10, scale: 2 })
  price: number;

  @Column('json', { nullable: true })
  attributes?: Record<string, any>; // e.g., {color: 'red', size: 'M'}

  @Column({ default: 0 })
  stockQuantity: number;

  @Column({ nullable: true })
  imageUrl?: string;

  @Column({ default: true })
  isActive: boolean;

  @ManyToOne(() => Product, product => product.variants)
  product: Product;
}
```

> 🚨 **Pain Point Alert**: Notice the `attributes` field as JSON? This is PostgreSQL forcing us to use JSONB for flexible data - essentially document storage in a relational database! This is a red flag that our data model wants to be document-based. What happens when we need to query by specific attributes (all red products, size M items)? JSONB queries become complex and slow. MongoDB would handle this naturally with flexible schemas and efficient queries.

## Step 2: Update App Module

**src/app.module.ts:**
```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule } from '@nestjs/config';
import { databaseConfig } from './config/database.config';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRoot(databaseConfig),
  ],
})
export class AppModule {}
```

## ✅ Next Step
Continue with **[03-core-services.md](./03-core-services.md)** for business logic.