# Tutorial 2: Database Models & Entities

## 🎯 Objective
Create TypeORM entities for products, categories, and pricing with proper relationships.

## Step 1: Database Configuration

**src/config/database.config.ts:**
```typescript
import { TypeOrmModuleOptions } from '@nestjs/typeorm';

export const databaseConfig: TypeOrmModuleOptions = {
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT) || 5432,
  username: process.env.DB_USERNAME || 'postgres',
  password: process.env.DB_PASSWORD || 'password',
  database: process.env.DB_NAME || 'productservice',
  entities: [__dirname + '/../**/*.entity{.ts,.js}'],
  synchronize: process.env.NODE_ENV === 'development',
};
```

## Step 2: Category Entity

**src/modules/categories/entities/category.entity.ts:**
```typescript
import { Entity, Column, PrimaryGeneratedColumn, Tree, TreeParent, TreeChildren } from 'typeorm';

@Entity('categories')
@Tree("nested-set")
export class Category {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  name: string;

  @Column({ unique: true })
  slug: string;

  @TreeParent()
  parent: Category;

  @TreeChildren()
  children: Category[];
}
```

> 💡 **Learning Note**: Notice we're using TypeORM's nested-set pattern for hierarchical categories. While this works, it can become complex for frequent category updates. MongoDB's native array support would handle this more naturally with a simple `parentPath` array. We'll explore this evolution in Tutorial 8b.

## ✅ Next Step
Continue with **[02b-product-entity.md](./02b-product-entity.md)** to create the Product entity.