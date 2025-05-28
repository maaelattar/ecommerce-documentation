# Project Setup - Product Service with Shared Libraries

## 🎯 Objective

Create a NestJS microservice for product catalog management using enterprise-grade shared libraries for consistency and code reuse.

## 🏗️ Architecture Changes

**❌ Before**: Inline authentication, logging, and event handling  
**✅ After**: Shared library dependencies for enterprise patterns

---

## 🔧 Create Project with Shared Libraries

### Initialize Project
```bash
mkdir -p services/product-service && cd services/product-service
npx @nestjs/cli new product-service --package-manager pnpm
cd product-service
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
pnpm add @nestjs/typeorm typeorm pg
pnpm add @nestjs/config @nestjs/swagger
pnpm add @nestjs/microservices amqplib
pnpm add class-validator class-transformer uuid

# Development dependencies  
pnpm add --save-dev @types/pg @types/uuid
pnpm add --save-dev @nestjs/testing jest supertest
```### Updated App Module with Shared Libraries

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

// Import shared libraries
import { CoreModule } from '@ecommerce/nestjs-core-utils';
import { AuthClientModule } from '@ecommerce/auth-client-utils';
import { EventModule } from '@ecommerce/rabbitmq-event-utils';

import { ProductModule } from './product/product.module';
import { InventoryModule } from './inventory/inventory.module';

@Module({
  imports: [
    // Environment configuration
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: `.env.${process.env.NODE_ENV || 'local'}`,
    }),
    
    // Shared enterprise modules
    CoreModule.forRoot({
      service: 'product-service',
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
      serviceName: 'product-service',
    }),

    // Database configuration
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

    // Domain modules
    ProductModule,
    InventoryModule,
  ],
})
export class AppModule {}
```### Environment Configuration

**.env.local:**
```env
NODE_ENV=development
PORT=3001

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/productservice
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=password
DB_NAME=productservice

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672

# Authentication (shared from user-service)
AUTH_JWKS_URI=http://localhost:3000/.well-known/jwks.json
AUTH_AUDIENCE=ecommerce-api
AUTH_ISSUER=ecommerce-user-service

# AWS LocalStack
AWS_ENDPOINT_URL=http://localhost:4566
AWS_REGION=us-east-1

# OpenSearch
OPENSEARCH_ENDPOINT=http://localhost:9200
```## 🚀 Bootstrap Application

### Updated main.ts with Shared Library Utilities

```typescript
// src/main.ts
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';

// Import shared utilities
import { LoggerService } from '@ecommerce/nestjs-core-utils';
import { GlobalExceptionFilter } from '@ecommerce/nestjs-core-utils';
import { CorrelationIdMiddleware } from '@ecommerce/nestjs-core-utils';

import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    bufferLogs: true,
  });

  // Use shared logger
  const logger = app.get(LoggerService);
  app.useLogger(logger);

  // Use shared global exception filter
  app.useGlobalFilters(new GlobalExceptionFilter(logger));

  // Use shared correlation ID middleware
  app.use(CorrelationIdMiddleware);

  // Validation pipes
  app.useGlobalPipes(new ValidationPipe({
    transform: true,
    whitelist: true,
    forbidNonWhitelisted: true,
  }));

  // Swagger documentation
  const config = new DocumentBuilder()
    .setTitle('Product Service API')
    .setDescription('Product catalog and inventory management')
    .setVersion('1.0')
    .addBearerAuth()
    .build();
    
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api/docs', app, document);

  const port = process.env.PORT || 3001;
  await app.listen(port);
  
  logger.log(`Product Service running on port ${port}`, 'Bootstrap');
}

bootstrap();
```## 📁 Project Structure with Shared Libraries

```
product-service/
├── src/
│   ├── product/
│   │   ├── dto/
│   │   ├── entities/
│   │   ├── product.controller.ts    # Uses @ecommerce/auth-client-utils
│   │   ├── product.service.ts       # Uses @ecommerce/nestjs-core-utils
│   │   └── product.module.ts
│   ├── inventory/
│   │   ├── dto/
│   │   ├── entities/
│   │   ├── inventory.controller.ts
│   │   ├── inventory.service.ts
│   │   └── inventory.module.ts
│   ├── events/
│   │   └── handlers/               # Uses @ecommerce/rabbitmq-event-utils
│   ├── app.module.ts
│   └── main.ts
├── test/                          # Uses @ecommerce/testing-utils
├── .env.local
├── .env.production
├── package.json
└── tsconfig.json
```

## 🔗 Key Integration Points

### 1. Authentication Integration
- Uses `@ecommerce/auth-client-utils` for JWT validation
- No more inline authentication code
- Consistent auth across all services

### 2. Logging Integration  
- Uses `@ecommerce/nestjs-core-utils` for structured logging
- Automatic correlation ID handling
- Consistent log format across services

### 3. Event Publishing Integration
- Uses `@ecommerce/rabbitmq-event-utils` for event publishing
- Transactional outbox pattern built-in
- Reliable event delivery guarantees

### 4. Testing Integration
- Uses `@ecommerce/testing-utils` for consistent test setup
- Mock factories for shared components
- Integration test utilities

---

## ✅ Next Steps

1. **Database Models** - Define product and inventory entities
2. **Core Services** - Implement business logic using shared utilities  
3. **Auth Integration** - Protect endpoints with shared auth guards
4. **API Implementation** - Build REST endpoints with shared validators
5. **Event Publishing** - Publish events using shared event utilities

## 🎯 Learning Outcomes

- **Enterprise Architecture**: Understanding shared library patterns
- **Code Reuse**: Eliminating duplicate authentication and logging code  
- **Consistency**: Using standardized patterns across all services
- **Maintainability**: Centralized utilities for easier updates