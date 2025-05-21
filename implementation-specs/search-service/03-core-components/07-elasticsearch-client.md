# Elasticsearch Client Service

## 1. Introduction

The Elasticsearch Client Service acts as a dedicated wrapper around the official Elasticsearch client library (e.g., `@elastic/elasticsearch` for Node.js/TypeScript). It centralizes all direct interactions with the Elasticsearch cluster, providing a configured and potentially enhanced client instance to the rest of the Search Service components.

This service is not about re-implementing the client but rather about managing its configuration, lifecycle, and possibly adding common functionalities like standardized logging, error handling, or connection management.

## 2. Responsibilities

- **Client Instantiation and Configuration**: Initialize the Elasticsearch client with appropriate configurations (node URLs, authentication, timeouts, SSL settings, etc.), typically sourced from application configuration.
- **Providing Client Instance**: Make the configured Elasticsearch client instance available to other services (Search Services, Indexing Services) via dependency injection.
- **Connection Management**: Handle connection strategies, retries, and lifecycle events of the Elasticsearch client if not sufficiently managed by the official library itself.
- **Centralized Logging**: Implement standardized logging for all Elasticsearch requests and responses, including timing and status. This helps in monitoring performance and debugging issues.
- **Error Normalization**: Catch low-level Elasticsearch client errors and potentially normalize them into application-specific exceptions or more structured error objects.
- **Health Checks**: Provide methods to check the health and connectivity of the Elasticsearch cluster.
- **Utility Methods (Optional)**: May expose thin wrappers around common Elasticsearch operations if further abstraction or simplification is beneficial (though often, services use the raw client methods for flexibility).

## 3. Design

The Elasticsearch Client Service is typically a singleton service within the application, ensuring that a single, consistently configured client instance is used throughout.

### 3.1. Dependencies

- **Official Elasticsearch Client Library**: The primary dependency (e.g., `@elastic/elasticsearch`).
- **Configuration Service** (e.g., `@nestjs/config`): To load Elasticsearch connection parameters and other settings.
- **Logger**: For logging interactions and errors.

### 3.2. Key Aspects

- **Configuration Loading**: Securely load connection details (cloud ID, API keys, node addresses) from environment variables or a configuration management system.
- **Client Options**: Configure client options like `maxRetries`, `requestTimeout`, `sniffOnStart`, `sniffInterval`, etc.
- **Authentication**: Implement the chosen authentication mechanism (API Key, username/password, token-based).
- **Secure Connection**: Ensure SSL/TLS is properly configured for encrypted communication with the Elasticsearch cluster, especially for cloud-hosted solutions.

## 4. Implementation Example (TypeScript/NestJS)

This example demonstrates how to set up the Elasticsearch module using `@nestjs/elasticsearch` which handles much of the client instantiation and provision.

```typescript
// src/elasticsearch/elasticsearch.module.ts
import { Module, Global } from '@nestjs/common';
import { ElasticsearchModule as NestElasticsearchModule } from '@nestjs/elasticsearch';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { Logger } from '@nestjs/common';

@Global() // Make the ElasticsearchService available globally without importing this module everywhere
@Module({
  imports: [
    NestElasticsearchModule.registerAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => {
        const logger = new Logger('ElasticsearchModule');
        const node = configService.get<string>('ELASTICSEARCH_NODE');
        const cloudId = configService.get<string>('ELASTICSEARCH_CLOUD_ID');
        const username = configService.get<string>('ELASTICSEARCH_USERNAME');
        const password = configService.get<string>('ELASTICSEARCH_PASSWORD');
        const apiKey = configService.get<string>('ELASTICSEARCH_API_KEY');

        let esOptions: any;

        if (cloudId) {
          logger.log(`Connecting to Elasticsearch using Cloud ID: ${cloudId}`);
          esOptions = { cloud: { id: cloudId } };
        } else if (node) {
          logger.log(`Connecting to Elasticsearch using Node: ${node}`);
          esOptions = { node };
        } else {
          logger.error('Elasticsearch connection details not found. Set ELASTICSEARCH_NODE or ELASTICSEARCH_CLOUD_ID.');
          throw new Error('Elasticsearch connection configuration is missing.');
        }

        if (apiKey) {
          logger.log('Using API Key for Elasticsearch authentication.');
          esOptions.auth = { apiKey };
        } else if (username && password) {
          logger.log('Using Username/Password for Elasticsearch authentication.');
          esOptions.auth = { username, password };
        }
        
        // Common client options
        esOptions.maxRetries = configService.get<number>('ELASTICSEARCH_MAX_RETRIES', 3);
        esOptions.requestTimeout = configService.get<number>('ELASTICSEARCH_REQUEST_TIMEOUT', 30000); // 30 seconds
        // Add more options as needed: sniffOnStart, sniffInterval, ssl context, etc.

        logger.log(`Elasticsearch client configured with options: ${JSON.stringify({ ...esOptions, auth: 'REDACTED' })}`);
        return esOptions;
      },
      inject: [ConfigService],
    }),
  ],
  exports: [NestElasticsearchModule], // Export the official module which provides ElasticsearchService
})
export class ElasticsearchClientModule {}

/*
Usage in other services:

import { Injectable } from '@nestjs/common';
import { ElasticsearchService } from '@nestjs/elasticsearch';

@Injectable()
export class ProductSearchService {
  constructor(private readonly esService: ElasticsearchService) {}

  async search(query: any) {
    const result = await this.esService.search({
      index: 'products',
      body: query
    });
    return result.body;
  }
}
*/
```

### 4.1. Enhancing the Client (Optional Custom Wrapper)

If more specific centralized logic is needed beyond what `@nestjs/elasticsearch` provides (like custom logging interceptors for every call or very specific error mapping), you might create a thin wrapper service.

```typescript
// src/elasticsearch/elasticsearch-wrapper.service.ts (Optional)
import { Injectable, Logger } from '@nestjs/common';
import { ElasticsearchService as NestElasticsearchService } from '@nestjs/elasticsearch';
import { SearchRequest, GetRequest, IndexRequest, UpdateRequest, DeleteRequest, BulkRequest } from '@elastic/elasticsearch/lib/api/types';
import { SearchException } from '../exceptions/search.exception';
import { IndexingException } from '../exceptions/indexing.exception';

@Injectable()
export class ElasticsearchClientWrapperService {
  private readonly logger = new Logger(ElasticsearchClientWrapperService.name);

  constructor(private readonly esService: NestElasticsearchService) {}

  private async handleEsError(error: any, operation: string, params: any): Promise<never> {
    this.logger.error(
        `Elasticsearch ${operation} error for params ${JSON.stringify(params)}: ${error.message}`,
        error.meta?.body || error.stack
    );
    const statusCode = error.meta?.statusCode;
    const esErrorBody = error.meta?.body;

    if (operation.includes('search') || operation.includes('get')) {
        throw new SearchException(`ES ${operation} failed.`, esErrorBody, statusCode);
    }
    throw new IndexingException(`ES ${operation} failed.`, esErrorBody, statusCode);
  }

  async search<TDocument = unknown>(params: SearchRequest) {
    this.logger.debug(`Executing ES Search: index=${params.index}, query=${JSON.stringify(params.body?.query).substring(0, 100)}...`);
    try {
      const response = await this.esService.search<TDocument>(params);
      return response.body; // .body contains the actual search response for v8+
    } catch (e) {
      return this.handleEsError(e, 'search', { index: params.index });
    }
  }

  async get<TDocument = unknown>(params: GetRequest) {
    this.logger.debug(`Executing ES Get: index=${params.index}, id=${params.id}`);
    try {
        const response = await this.esService.get<TDocument>(params);
        return response.body;
    } catch (e) {
        return this.handleEsError(e, 'get', { index: params.index, id: params.id });
    }
  }
  
  async index<TDocument = unknown>(params: IndexRequest<TDocument>) {
    this.logger.debug(`Executing ES Index: index=${params.index}, id=${params.id}`);
    try {
        const response = await this.esService.index<TDocument>(params);
        return response.body;
    } catch (e) {
        return this.handleEsError(e, 'index', { index: params.index, id: params.id });
    }
  }
  
  async update<TDocument = unknown, TPartialDocument = unknown>(params: UpdateRequest<TDocument, TPartialDocument>) {
    this.logger.debug(`Executing ES Update: index=${params.index}, id=${params.id}`);
    try {
        const response = await this.esService.update<TDocument, TPartialDocument>(params);
        return response.body;
    } catch (e) {
        return this.handleEsError(e, 'update', { index: params.index, id: params.id });
    }
  }
  
  async delete(params: DeleteRequest) {
    this.logger.debug(`Executing ES Delete: index=${params.index}, id=${params.id}`);
    try {
        const response = await this.esService.delete(params);
        return response.body;
    } catch (e) {
        return this.handleEsError(e, 'delete', { index: params.index, id: params.id });
    }
  }
  
  async bulk<TDocument = unknown>(params: BulkRequest<TDocument>) {
    this.logger.debug(`Executing ES Bulk: index=${params.index || 'multiple'}, operations=${(params.body as any[])?.length / 2}`);
    try {
        const response = await this.esService.bulk<any, TDocument>(params);
        return response.body;
    } catch (e) {
        return this.handleEsError(e, 'bulk', { index: params.index });
    }
  }

  async ping(): Promise<boolean> {
    try {
      const response = await this.esService.ping();
      this.logger.log(`Elasticsearch ping successful: ${response.body}`);
      return response.body;
    } catch (error) {
      this.logger.error('Elasticsearch ping failed', error.meta?.body || error.stack);
      return false;
    }
  }

  async getClusterHealth(): Promise<any> {
    try {
      const response = await this.esService.cluster.health();
      this.logger.log(`Elasticsearch cluster health: ${response.body.status}`);
      return response.body;
    } catch (error) {
      this.logger.error('Failed to get Elasticsearch cluster health', error.meta?.body || error.stack);
      throw new SearchException('Failed to retrieve cluster health', error.meta?.body);
    }
  }
}

// If using the wrapper, ElasticsearchClientModule would provide ElasticsearchClientWrapperService
// and other services would inject ElasticsearchClientWrapperService instead of NestElasticsearchService directly.
```

## 5. Health Checks

A common responsibility for an Elasticsearch client wrapper or module is to expose a health check endpoint that the application's main health check can utilize.

```typescript
// In a health check controller or service
// constructor(private readonly esClientWrapper: ElasticsearchClientWrapperService) {}

// async checkElasticsearchHealth(): Promise<HealthIndicatorResult> {
//   const isHealthy = await this.esClientWrapper.ping();
//   if (isHealthy) {
//     return this.getStatus('elasticsearch', true);
//   }
//   const health = await this.esClientWrapper.getClusterHealth().catch(() => null);
//   throw new HealthCheckError(
//       'Elasticsearch health check failed',
//       this.getStatus('elasticsearch', false, { status: health?.status, message: 'Ping failed' }),
//   );
// }
```

## 6. Interactions

- **Search Services & Indexing Services**: These are the primary consumers. They inject the `ElasticsearchService` (from `@nestjs/elasticsearch`) or a custom wrapper service to perform operations like `search`, `index`, `update`, `delete`, `bulk`.
- **Configuration Service**: Provides the necessary connection and operational parameters.
- **Application Health Check System**: May query the client service for Elasticsearch cluster health.

## 7. Benefits

- **Centralized Configuration**: Manages Elasticsearch client configuration in one place.
- **Consistency**: Ensures all parts of the application use the same client instance and settings.
- **Abstraction (Optional)**: A wrapper can provide a slightly higher-level API or add common cross-cutting concerns like standardized logging or error mapping.
- **Testability**: Easier to mock the Elasticsearch client interactions when testing services that depend on it.

By using a dedicated module or service for Elasticsearch client management, the application ensures robust and consistent communication with the Elasticsearch cluster.
