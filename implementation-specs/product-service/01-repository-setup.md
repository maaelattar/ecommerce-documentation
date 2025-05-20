# Product Service Implementation: Phase 1 - Repository Setup & Project Scaffolding

## 1. Overview

This document provides detailed implementation specifications for setting up the Product Service repository and scaffolding the initial NestJS project structure. This is the first phase of the Product Service implementation plan.

## 2. Prerequisites

- Access to Git hosting platform (e.g., GitHub, GitLab)
- Node.js LTS version installed (preferably v18 or newer)
- npm or Yarn package manager
- Docker and Docker Compose installed (for local development)
- NestJS CLI installed (`npm i -g @nestjs/cli`)

## 3. Repository Creation and Structure

### 3.1 Repository Creation

1. **Create a new repository** on the Git hosting platform:
   - Name: `product-service`
   - Description: "E-commerce Product Service - Manages product information, inventory, and pricing"
   - Visibility: Private
   - Initialize with: Nothing (empty repository)

2. **Clone the repository** locally within the workspace directory:
   ```bash
   mkdir -p /Users/mh/Documents/Wave/demo/ecommerce-repos-gemi/product-service
   cd /Users/mh/Documents/Wave/demo/ecommerce-repos-gemi/product-service
   git init
   git remote add origin [REPOSITORY_URL]
   ```

### 3.2 NestJS Project Generation

Use the NestJS CLI to scaffold a new NestJS application:

```bash
cd /Users/mh/Documents/Wave/demo/ecommerce-repos-gemi/product-service
nest new . --strict --package-manager npm
```

Options:
- `--strict`: Enables TypeScript strict mode (recommended)
- `--package-manager npm`: Uses npm as the package manager (can be changed to `yarn` if preferred)

### 3.3 Additional NPM Packages

Add the following essential packages:

```bash
npm install --save \
  @nestjs/config \
  @nestjs/swagger \
  class-validator \
  class-transformer \
  @nestjs/typeorm \
  typeorm \
  pg \
  amqplib \
  @nestjs/microservices \
  joi

npm install --save-dev \
  @types/amqplib \
  eslint-plugin-prettier \
  @typescript-eslint/eslint-plugin \
  @typescript-eslint/parser
```

## 4. Core Configuration Files

### 4.1 `.gitignore` Setup

Update the `.gitignore` file to include all necessary exclusions:

```
# compiled output
/dist
/node_modules

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*

# OS
.DS_Store

# Tests
/coverage
/.nyc_output

# IDEs and editors
/.idea
.project
.classpath
.c9/
*.launch
.settings/
*.sublime-workspace
.vscode/*

# Environment variables
.env
.env.*
!.env.example

# Docker volumes
/docker/data

# Database volume
/pg_data

# Temp files
tmp/
```

### 4.2 `README.md` Content

Create a comprehensive README with the following sections:

```markdown
# Product Service

## Description

The Product Service is a core microservice for the e-commerce platform, responsible for managing:
- Product information (details, categories, attributes)
- Inventory tracking
- Pricing and promotions
- Product reviews
- Search integration

## Technology Stack

- **Framework**: NestJS
- **Language**: TypeScript
- **Database**: PostgreSQL (via Amazon RDS in production)
- **ORM**: TypeORM
- **Messaging**: RabbitMQ (via Amazon MQ in production)
- **Search**: Elasticsearch/OpenSearch
- **Documentation**: Swagger/OpenAPI
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## Installation

```bash
$ npm install
```

## Running the app

```bash
# development
$ npm run start

# watch mode
$ npm run start:dev

# production mode
$ npm run start:prod
```

## Test

```bash
# unit tests
$ npm run test

# e2e tests
$ npm run test:e2e

# test coverage
$ npm run test:cov
```

## Local Development with Docker

This service can be run locally using Docker Compose:

```bash
# Start all services
$ docker-compose up

# Start in detached mode
$ docker-compose up -d

# Stop all services
$ docker-compose down
```

## API Documentation

When running in development mode, Swagger API documentation is available at:
- http://localhost:3000/api/docs

## Database Schema

[To be added - Entity relationship diagram for the product data model]

## Event Publishing

This service publishes the following events to the message broker:
- ProductCreated
- ProductUpdated
- ProductDeleted
- InventoryUpdated
- PriceChanged
- ReviewAdded

## Environment Variables

See `.env.example` for required environment variables.
```

### 4.3 Environment Configuration

Create a `.env.example` file to document required environment variables:

```
# Application
NODE_ENV=development
PORT=3000
API_PREFIX=api

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_DATABASE=product_service

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

# AWS (for production)
AWS_REGION=us-east-1
# AWS_RDS_* entries would be used in production
# AWS_MQ_* entries would be used in production

# OpenSearch
OPENSEARCH_NODE=http://localhost:9200
```

Create an actual `.env` file with development values:

```
NODE_ENV=development
PORT=3000
API_PREFIX=api
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_DATABASE=product_service
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
OPENSEARCH_NODE=http://localhost:9200
```

## 5. Docker Setup

### 5.1 Dockerfile

Create a `Dockerfile` in the root directory:

```Dockerfile
FROM node:18-alpine As development

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

FROM node:18-alpine As production

ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install --only=production

COPY . .

COPY --from=development /usr/src/app/dist ./dist

CMD ["node", "dist/main"]
```

### 5.2 docker-compose.yml

Create a `docker-compose.yml` file for local development:

```yaml
version: '3.8'

services:
  product-service:
    build:
      context: .
      target: development
    volumes:
      - .:/usr/src/app
      - /usr/src/app/node_modules
    ports:
      - '3000:3000'
    command: npm run start:dev
    env_file:
      - .env
    depends_on:
      - postgres
      - rabbitmq
      - elasticsearch

  postgres:
    image: postgres:14
    ports:
      - '5432:5432'
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: product_service
    volumes:
      - postgres_data:/var/lib/postgresql/data

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - '5672:5672'
      - '15672:15672'
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - '9200:9200'
      - '9300:9300'
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

volumes:
  postgres_data:
  elasticsearch_data:
```

## 6. Initial NestJS Configuration

### 6.1 Configure Application Module

Update `src/app.module.ts`:

```typescript
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import * as Joi from 'joi';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      validationSchema: Joi.object({
        NODE_ENV: Joi.string().valid('development', 'production', 'test').default('development'),
        PORT: Joi.number().default(3000),
        API_PREFIX: Joi.string().default('api'),
        DB_HOST: Joi.string().required(),
        DB_PORT: Joi.number().default(5432),
        DB_USERNAME: Joi.string().required(),
        DB_PASSWORD: Joi.string().required(),
        DB_DATABASE: Joi.string().required(),
        RABBITMQ_HOST: Joi.string().required(),
        RABBITMQ_PORT: Joi.number().default(5672),
        RABBITMQ_USERNAME: Joi.string().required(),
        RABBITMQ_PASSWORD: Joi.string().required(),
        RABBITMQ_VHOST: Joi.string().default('/'),
        OPENSEARCH_NODE: Joi.string().default('http://localhost:9200'),
      }),
    }),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => ({
        type: 'postgres',
        host: configService.get('DB_HOST'),
        port: configService.get<number>('DB_PORT'),
        username: configService.get('DB_USERNAME'),
        password: configService.get('DB_PASSWORD'),
        database: configService.get('DB_DATABASE'),
        autoLoadEntities: true, // Will be set to false in production
        synchronize: configService.get('NODE_ENV') !== 'production', // Never use synchronize in production
      }),
    }),
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
```

### 6.2 Swagger Integration

Update `src/main.ts`:

```typescript
import { NestFactory } from '@nestjs/core';
import { ConfigService } from '@nestjs/config';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const configService = app.get(ConfigService);
  
  const apiPrefix = configService.get('API_PREFIX') || 'api';
  app.setGlobalPrefix(apiPrefix);
  
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }),
  );

  // Swagger setup
  if (configService.get('NODE_ENV') !== 'production') {
    const config = new DocumentBuilder()
      .setTitle('Product Service API')
      .setDescription('E-commerce Product Service API documentation')
      .setVersion('1.0')
      .addTag('products')
      .addBearerAuth()
      .build();
    
    const document = SwaggerModule.createDocument(app, config);
    SwaggerModule.setup(`${apiPrefix}/docs`, app, document);
  }

  // Enable CORS
  app.enableCors();

  const port = configService.get('PORT') || 3000;
  await app.listen(port);
  console.log(`Application is running on: http://localhost:${port}/${apiPrefix}`);
}
bootstrap();
```

## 7. Initial Project Structure

Create placeholder directories with `.gitkeep` files:

```
src/
├── common/                # Common utilities, interceptors, filters, etc.
│   ├── constants/
│   ├── decorators/
│   ├── dto/               # Shared DTOs
│   ├── filters/           # Exception filters
│   ├── guards/            # Auth guards
│   ├── interceptors/      # Request/response interceptors
│   ├── interfaces/        # TypeScript interfaces
│   └── pipes/             # Validation pipes
│
├── config/                # Configuration modules
│   ├── database.config.ts
│   ├── swagger.config.ts
│   └── rabbitmq.config.ts
│
├── modules/               # Feature modules (to be implemented)
│   ├── products/          # Product module (core functionality)
│   ├── categories/        # Category module
│   ├── inventory/         # Inventory module
│   ├── pricing/           # Pricing module
│   ├── reviews/           # Reviews module
│   └── search/            # Search integration module
│
├── app.controller.ts      # Root controller
├── app.module.ts          # Root module
├── app.service.ts         # Root service
└── main.ts                # Application entry point
```

## 8. Initial Git Commit

After setting up the project structure, make the initial commit:

```bash
git add .
git commit -m "feat: initial project setup for Product Service"
git push -u origin main
```

## 9. Branch Protection Setup

On the Git hosting platform, set up branch protection rules for the `main` branch:

1. Require pull request reviews before merging
2. Require status checks to pass before merging
3. Include administrators in these restrictions

## 10. Next Steps

After completing the repository setup and project scaffolding, the next phase will focus on:

1. Database design and entity model creation
2. TypeORM integration
3. Migration scripts

These steps are detailed in the next specification document: [02-data-model-setup.md](./02-data-model-setup.md).

## 11. References

- [NestJS Documentation](https://docs.nestjs.com/)
- [TypeORM Documentation](https://typeorm.io/)
- [Docker Documentation](https://docs.docker.com/)
- [AWS RDS for PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
