# Configuration Management

## 1. Introduction

Configuration Management for the Search Service involves how the service retrieves and utilizes its operational parameters. These parameters can range from Elasticsearch connection details and index names to feature flags, cache TTLs, and default query settings.

A robust configuration management strategy is essential for flexibility, maintainability, and adaptability across different environments (development, staging, production).

While not a single "component" in the same way as a Query Builder, it's a cross-cutting concern that affects all other components.

## 2. Responsibilities of the Configuration System

- **Provide Configuration Values**: Make configuration parameters accessible to all components that need them.
- **Environment-Specific Configurations**: Support different configuration values for different deployment environments.
- **Secure Handling of Secrets**: Ensure sensitive information (API keys, passwords) is managed securely (e.g., via environment variables, secret management systems like HashiCorp Vault, AWS Secrets Manager).
- **Type Safety**: Provide typed access to configuration values where possible to prevent runtime errors.
- **Centralization**: Offer a centralized way to access configurations rather than scattering them throughout the codebase.
- **Dynamic Updates (Optional)**: For some configurations, support dynamic updates without requiring an application restart (e.g., using a configuration server like Spring Cloud Config or Consul), though this adds complexity.

## 3. Key Configuration Parameters

Examples of parameters the Search Service might need:

- **Elasticsearch Connection**:
    - `ELASTICSEARCH_NODE` (e.g., `http://localhost:9200`) or `ELASTICSEARCH_CLOUD_ID`
    - `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD` or `ELASTICSEARCH_API_KEY`
    - `ELASTICSEARCH_REQUEST_TIMEOUT`, `ELASTICSEARCH_MAX_RETRIES`
    - SSL/TLS settings
- **Index Names & Aliases**:
    - `elasticsearch.indices.products` (e.g., `products-v1`)
    - `elasticsearch.indices.categories` (e.g., `categories-v1`)
    - `elasticsearch.indices.content` (e.g., `content-v1`)
    - `elasticsearch.aliases.productsRead` (e.g., `products_read_alias`)
    - `elasticsearch.aliases.productsWrite` (e.g., `products_write_alias`)
- **Cache Settings**:
    - `CACHE_STORE_TYPE` (e.g., `memory`, `redis`)
    - `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` (if using Redis)
    - `CACHE_DEFAULT_TTL_SECONDS`
    - `cache.ttl.productSearch`, `cache.ttl.autocomplete`, etc. (specific TTLs)
- **Query Defaults**:
    - `search.defaultPageSize`
    - `search.maxPageSize`
    - `autocomplete.defaultLimit`
- **Feature Flags**:
    - `featureFlags.enablePhoneticSearch`
    - `featureFlags.useAdvancedSynonyms`
- **Logging Levels**:
    - `LOG_LEVEL` (e.g., `debug`, `info`, `warn`, `error`)
- **Message Broker (for Event Consumers)**:
    - `KAFKA_BROKERS`
    - `KAFKA_CLIENT_ID`, `KAFKA_GROUP_ID`
    - Topic names (e.g., `topic.product.created`)
- **Retry Policies**:
    - `eventConsumer.retryAttempts`
    - `eventConsumer.retryDelayMs`

## 4. Implementation Strategy (NestJS using `@nestjs/config`)

NestJS's `ConfigModule` is a powerful tool for managing application configuration. It supports loading from `.env` files, custom configuration files (e.g., YAML, JSON), and environment variables, with validation and typed access.

### 4.1. ConfigModule Setup

```typescript
// src/config/config.module.ts
import { Module, Global } from '@nestjs/common';
import { ConfigModule as NestConfigModule } from '@nestjs/config';
import * as Joi from 'joi'; // For validation

// Optional: Define a typed configuration object/interface
export interface AppConfig {
  PORT: number;
  LOG_LEVEL: string;
  ELASTICSEARCH_NODE?: string;
  ELASTICSEARCH_CLOUD_ID?: string;
  ELASTICSEARCH_USERNAME?: string;
  ELASTICSEARCH_PASSWORD?: string;
  ELASTICSEARCH_API_KEY?: string;
  // ... other config properties
}

@Global() // Make ConfigService available globally
@Module({
  imports: [
    NestConfigModule.forRoot({
      isGlobal: true, // Makes ConfigService available application-wide without importing ConfigModule in each module
      envFilePath: process.env.NODE_ENV === 'test' ? '.env.test' : '.env', // Load .env or .env.test
      // load: [configuration], // For loading custom config files (e.g., YAML)
      validationSchema: Joi.object({ // Define validation rules for environment variables
        NODE_ENV: Joi.string().valid('development', 'production', 'test', 'provision').default('development'),
        PORT: Joi.number().default(3000),
        LOG_LEVEL: Joi.string().valid('debug', 'info', 'warn', 'error').default('info'),
        
        // Elasticsearch - either Node or Cloud ID must be present
        ELASTICSEARCH_NODE: Joi.string().uri().optional(),
        ELASTICSEARCH_CLOUD_ID: Joi.string().optional(),
        ELASTICSEARCH_USERNAME: Joi.string().optional(),
        ELASTICSEARCH_PASSWORD: Joi.string().optional(), // Note: secrets should ideally be handled by a secret manager
        ELASTICSEARCH_API_KEY: Joi.string().optional(),
        
        ELASTICSEARCH_REQUEST_TIMEOUT: Joi.number().default(30000),
        ELASTICSEARCH_MAX_RETRIES: Joi.number().default(3),

        // Example for index names (can also be in a separate config file loaded via `load`)
        ES_INDEX_PRODUCTS: Joi.string().default('products-v1'),
        ES_ALIAS_PRODUCTS_READ: Joi.string().default('products_read'),

        CACHE_STORE_TYPE: Joi.string().valid('memory', 'redis').default('memory'),
        REDIS_HOST: Joi.string().default('localhost'),
        REDIS_PORT: Joi.number().default(6379),
        CACHE_DEFAULT_TTL_SECONDS: Joi.number().default(300),
        // Add more validation rules as needed
      }).xor('ELASTICSEARCH_NODE', 'ELASTICSEARCH_CLOUD_ID'), // Ensures either node or cloud_id is provided
      validationOptions: {
        allowUnknown: true, // Allow other env variables not defined in schema
        abortEarly: false, // Report all errors at once
      },
    }),
  ],
  providers: [ConfigService], // ConfigService is already provided by NestConfigModule.forRoot
  exports: [ConfigService],   // Export ConfigService to be injectable
})
export class AppConfigModule {}
```

### 4.2. Using ConfigService in Other Services

```typescript
// Example in ElasticsearchClientModule or a service
import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class ProductIndexingService {
  private readonly productIndexReadAlias: string;

  constructor(private readonly configService: ConfigService /*<AppConfig> if using typed config */) {
    // Get typed configuration value with a default fallback
    this.productIndexReadAlias = this.configService.get<string>('ES_ALIAS_PRODUCTS_READ', 'products_read');
    
    const esNode = this.configService.get('ELASTICSEARCH_NODE');
    // this.logger.debug(`Product index read alias: ${this.productIndexReadAlias}, ES Node: ${esNode}`);
  }
  
  // ... rest of the service
}
```

### 4.3. Custom Configuration Files (e.g., `config/search.config.ts`)

For more complex or structured configurations, you can use custom configuration files.

```typescript
// src/config/search.config.ts
import { registerAs } from '@nestjs/config';

export default registerAs('search', () => ({
  defaultPageSize: parseInt(process.env.SEARCH_DEFAULT_PAGE_SIZE, 10) || 20,
  maxPageSize: parseInt(process.env.SEARCH_MAX_PAGE_SIZE, 10) || 100,
  cacheTTLs: {
    productSearch: parseInt(process.env.CACHE_TTL_PRODUCT_SEARCH_SECONDS, 10) || 300,
    categorySearch: parseInt(process.env.CACHE_TTL_CATEGORY_SEARCH_SECONDS, 10) || 600,
    autocomplete: parseInt(process.env.CACHE_TTL_AUTOCOMPLETE_SECONDS, 10) || 60,
  },
  indices: {
    products: process.env.ES_INDEX_PRODUCTS || 'products-v1',
    categories: process.env.ES_INDEX_CATEGORIES || 'categories-v1',
    content: process.env.ES_INDEX_CONTENT || 'content-v1',
  },
  aliases: {
    productsRead: process.env.ES_ALIAS_PRODUCTS_READ || 'products_read',
    productsWrite: process.env.ES_ALIAS_PRODUCTS_WRITE || 'products_write',
    // ... other aliases
  },
  featureFlags: {
    enablePhoneticSearch: process.env.FEATURE_PHONETIC_SEARCH === 'true',
  }
}));

// Then load it in ConfigModule:
// NestConfigModule.forRoot({ load: [searchConfig] })

// Access it in services:
// constructor(private readonly configService: ConfigService) {
//   const pageSize = this.configService.get<number>('search.defaultPageSize');
// }
```

## 5. Environment Variables and `.env` Files

- **`.env` file**: Store default development values. This file should generally NOT be committed to version control if it contains sensitive information, or a `.env.example` should be provided.
- **Environment Variables**: Override `.env` file values. This is the standard way to configure applications in staging/production environments (e.g., in Docker containers, Kubernetes deployments, PaaS platforms).
- **Secrets Management**: For production secrets (API keys, passwords), use a dedicated secrets management tool. The application can then load these secrets into environment variables at runtime or use SDKs provided by the secret manager.

## 6. Best Practices

- **Centralize Access**: Use the `ConfigService` as the single source of truth for configuration values.
- **Validate Configurations**: Use validation schemas (like Joi) to ensure that necessary configurations are present and have valid formats, failing fast on startup if misconfigured.
- **Type Safety**: Use typed configuration access (`configService.get<number>('PORT')`) and potentially define interfaces for your configuration structure.
- **Environment Parity**: Strive to keep configuration mechanisms similar across environments, varying only the values, not the way they are loaded.
- **Do Not Hardcode**: Avoid hardcoding configuration values directly in the code.
- **Separate Config from Code**: Keep configuration files and `.env` files separate from the application logic.
- **Security for Secrets**: Never commit sensitive data to version control. Use environment variables for secrets or integrate with a secrets management system.

## 7. Interactions

- **All Components**: Virtually all services and modules within the Search Service will interact with the `ConfigService` to fetch their required configurations.
- **Application Bootstrap**: The `ConfigModule` is typically one of the first modules to be loaded when the application starts to ensure configurations are available early.

Proper configuration management is fundamental to building a flexible, secure, and easily deployable Search Service that can adapt to different operational environments and requirements.
