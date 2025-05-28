# Tutorial 7: Search Integration with Amazon OpenSearch

## 🎯 Objective
Integrate Amazon OpenSearch for fast product search and filtering capabilities.

## Step 1: Install OpenSearch Client

```bash
pnpm add @opensearch-project/opensearch
```

## Step 2: Search Service

**src/modules/search/services/search.service.ts:**
```typescript
import { Injectable } from '@nestjs/common';
import { Client } from '@opensearch-project/opensearch';

@Injectable()
export class SearchService {
  private client: Client;

  constructor() {
    this.client = new Client({
      node: process.env.OPENSEARCH_ENDPOINT || 'http://localhost:9200',
    });
  }

  async indexProduct(product: any) {
    return await this.client.index({
      index: 'products',
      id: product.id,
      body: {
        name: product.name,
        description: product.description,
        price: product.basePrice,
        category: product.category.name,
        tags: product.tags,
      },
    });
  }

  async searchProducts(query: string, filters?: any) {
    return await this.client.search({
      index: 'products',
      body: {
        query: {
          multi_match: {
            query,
            fields: ['name^2', 'description', 'category'],
          },
        },
        sort: [{ price: { order: 'asc' } }],
      },
    });
  }
}
```

> 🚨 **Architecture Pain Point**: Notice we need TWO databases now - PostgreSQL for transactional data AND OpenSearch for search! This creates:
> - **Data synchronization challenges** - keeping both in sync
> - **Complex deployment** - two database systems to manage
> - **Eventual consistency** - search results might lag behind updates
> - **Development overhead** - writing to both systems for every change
> 
> MongoDB with full-text search indexes could eliminate this dual-database complexity. We'd have one system handling both transactional operations AND search. Consider this trade-off as you build production systems!

## ✅ Next Step
Continue with **[08-testing.md](./08-testing.md)** for testing strategies.