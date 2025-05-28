# Project Setup - Search Service with Shared Libraries

## 🎯 Objective
Create a NestJS microservice for product search and discovery using Elasticsearch and enterprise-grade shared libraries.

## 🏗️ Architecture Overview
**Search & Discovery**: Advanced product search with filtering, facets, and recommendations
**Elasticsearch Integration**: Full-text search with relevance scoring
**Event-Driven Indexing**: Real-time index updates from product events
**Shared Libraries**: Consistent patterns across all services

---

## 🔧 Create Project with Shared Libraries

### Initialize Project
```bash
mkdir -p services/search-service && cd services/search-service
npx @nestjs/cli new search-service --package-manager pnpm
cd search-service
```

### Install Shared Libraries FIRST
```bash
# Install our enterprise shared libraries
pnpm add @ecommerce/auth-client-utils
pnpm add @ecommerce/nestjs-core-utils
pnpm add @ecommerce/rabbitmq-event-utils
pnpm add @ecommerce/testing-utils
```

### Install Core Dependencies
```bash
# Core NestJS packages
pnpm add @nestjs/config @nestjs/microservices
pnpm add class-validator class-transformer

# Search and database
pnpm add @elastic/elasticsearch
pnpm add @nestjs/typeorm typeorm pg

# Development dependencies  
pnpm add --save-dev @types/pg
pnpm add --save-dev @nestjs/testing jest supertest
```

### App Module with Shared Libraries

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

// Import shared libraries
import { CoreModule } from '@ecommerce/nestjs-core-utils';
import { AuthClientModule } from '@ecommerce/auth-client-utils';
import { EventModule } from '@ecommerce/rabbitmq-event-utils';

import { SearchModule } from './search/search.module';
import { EventHandlerModule } from './events/event-handler.module';
import { ElasticsearchModule } from './elasticsearch/elasticsearch.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: `.env.${process.env.NODE_ENV || 'local'}`,
    }),
    
    // Shared enterprise modules
    CoreModule.forRoot({
      service: 'search-service',
      version: '1.0.0',
      logLevel: 'debug',
    }),
    AuthClientModule.forRoot({
      jwksUri: process.env.AUTH_JWKS_URI,
      audience: process.env.AUTH_AUDIENCE,
      issuer: process.env.AUTH_ISSUER,
    }),
    EventModule.forRoot({
      connectionString: process.env.RABBITMQ_URL,
      serviceName: 'search-service',
      subscriptions: [
        'product.created',
        'product.updated',
        'product.deleted',
        'inventory.updated',
      ],
    }),

    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST,
      port: parseInt(process.env.DB_PORT, 10),
      username: process.env.DB_USERNAME,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME,
      autoLoadEntities: true,
      synchronize: process.env.NODE_ENV === 'development',
    }),

    ElasticsearchModule,
    SearchModule,
    EventHandlerModule,
  ],
})
export class AppModule {}
```