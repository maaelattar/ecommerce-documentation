# Tutorial 2b: Product Entity

## 🎯 Objective
Create the main Product entity with variants and pricing models.

## Step 1: Product Entity

**src/modules/products/entities/product.entity.ts:**
```typescript
import { Entity, Column, PrimaryGeneratedColumn, ManyToOne, OneToMany, CreateDateColumn, UpdateDateColumn } from 'typeorm';
import { Category } from '../../categories/entities/category.entity';
import { ProductVariant } from './product-variant.entity';

@Entity('products')
export class Product {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  @Column({ unique: true })
  slug: string;

  @Column('text')
  description: string;

  @Column('decimal', { precision: 10, scale: 2 })
  basePrice: number;

  @Column('simple-array', { nullable: true })
  images?: string[];

  @Column({ default: true })
  isActive: boolean;

  @ManyToOne(() => Category)
  category: Category;

  @OneToMany(() => ProductVariant, variant => variant.product, { cascade: true })
  variants: ProductVariant[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
```

> 💡 **Learning Note**: Notice how we're separating products and variants into different entities with foreign key relationships. This is classic relational thinking! But consider: what if we need to add attributes like "color", "size", "material" to products? We'd need junction tables or JSONB columns. MongoDB would let us embed variants directly in the product document with flexible schemas. Keep this in mind as we build more features.

## ✅ Next Step
Continue with **[02c-product-variant.md](./02c-product-variant.md)** for product variants.