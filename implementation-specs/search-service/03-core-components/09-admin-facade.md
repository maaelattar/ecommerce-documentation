# Admin Facade

## 1. Introduction

The Admin Facade provides a dedicated interface for administrative operations related to the Search Service. While the primary `SearchFacade` handles public search and autocomplete queries, the `AdminFacade` exposes functionalities required for managing the search indices, monitoring, and performing maintenance tasks.

This facade is typically consumed by an internal admin panel or CLI tools, not by end-user facing applications.

## 2. Responsibilities

- **Index Management**: Expose operations to manage Elasticsearch indices:
    - Create indices (e.g., for new versions or new data types).
    - Delete indices (e.g., old, unused versions).
    - Update index mappings and settings.
    - Re-index data from a source to a target index (full or partial re-indexing).
    - Manage index aliases (create, update, delete, point to different versions).
- **Data Management (Manual)**:
    - Trigger manual indexing or re-indexing of specific documents or document sets.
    - Manually delete specific documents from an index.
    - Interface for bulk data uploads to an index.
- **Cache Management**: Provide endpoints to clear caches (all, specific namespaces, or by key patterns).
- **Monitoring & Diagnostics**: Expose methods to retrieve:
    - Index statistics (document counts, storage size, shard health).
    - Cluster health and status.
    - Search query logs or performance metrics (potentially through an analytics component).
- **Synonym Management (if applicable)**: Interface to manage synonym dictionaries if they are stored and updated via an API rather than just file-based.
- **Configuration Management (Viewing)**: Allow viewing of current search service configurations (e.g., active index aliases, analysis settings).
- **Security**: Ensure that all administrative operations are properly authenticated and authorized.

## 3. Design

The Admin Facade, like the Search Facade, is an injectable service that orchestrates calls to more specialized underlying services (e.g., `IndexManagementService`, `CacheManagementService`, `MonitoringService`).

### 3.1. Dependencies

- `IndexManagementService`: Handles low-level index operations (create, delete, mappings, aliases, re-indexing logic).
- `ProductIndexingService`, `CategoryIndexingService`, `ContentIndexingService`: For manual document manipulation tasks.
- `CacheManagementService` (or directly `CacheManager`): For cache clearing operations.
- `ElasticsearchClientService` (or `ElasticsearchService`): For direct cluster/index status queries.
- `Logger`: For logging administrative actions.
- `ConfigService`: To access configuration related to admin operations.

### 3.2. Key Methods (Illustrative)

- `createIndex(indexName: string, settings: IndexSettings, mappings: IndexMappings): Promise<void>`
- `deleteIndex(indexName: string): Promise<void>`
- `updateIndexAlias(aliasName: string, targetIndex: string, oldIndex?: string): Promise<void>`
- `triggerReindex(sourceIndex: string, targetIndex: string, script?: ReindexScript): Promise<ReindexTaskInfo>`
- `getIndexStats(indexName?: string): Promise<IndexStats | AllIndexStats>`
- `getClusterHealth(): Promise<ClusterHealth>`
- `clearCache(namespace?: string, keyPattern?: string): Promise<void>`
- `indexSingleDocument(indexName: string, documentId: string, document: any): Promise<void>`
- `deleteSingleDocument(indexName: string, documentId: string): Promise<void>`
- `getSynonymSets(dictionaryName: string): Promise<SynonymSet[]>` (if applicable)
- `addSynonymSet(dictionaryName: string, synonyms: string[]): Promise<void>` (if applicable)

## 4. Implementation Example (TypeScript/NestJS)

```typescript
import { Injectable, Logger, Inject, ForbiddenException, NotFoundException } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';
import { ElasticsearchService } from '@nestjs/elasticsearch';
import { ConfigService } from '@nestjs/config';
import { IndexManagementService } from './index-management.service'; // Assume this service exists
import { 
    ProductIndexingService, 
    CategoryIndexingService, 
    ContentIndexingService 
} from './indexing'; // Barrel file for indexing services
import { 
    ClusterHealthResponse, 
    IndicesStatsResponse, 
    ReindexResponse 
} from '@elastic/elasticsearch/lib/api/types';

// Define DTOs for request/response if necessary
export interface ReindexParams {
    sourceIndex: string;
    destIndex: string;
    script?: { source: string; lang: string; };
    waitForCompletion?: boolean;
}

@Injectable()
export class AdminFacade {
  private readonly logger = new Logger(AdminFacade.name);

  constructor(
    private readonly indexManagementService: IndexManagementService,
    private readonly productIndexingService: ProductIndexingService,
    // Inject other indexing services as needed
    private readonly elasticsearchService: ElasticsearchService,
    @Inject(CACHE_MANAGER) private readonly cacheManager: Cache,
    private readonly configService: ConfigService,
  ) {}

  // --- Index Lifecycle Operations ---
  async createIndex(indexName: string, settings?: any, mappings?: any): Promise<void> {
    this.logger.log(`Admin request: Create index ${indexName}`);
    // Add authorization checks here: e.g., if (user.role !== 'admin') throw new ForbiddenException();
    try {
      await this.indexManagementService.createIndex(indexName, settings, mappings);
      this.logger.log(`Index ${indexName} created successfully.`);
    } catch (error) {
      this.logger.error(`Failed to create index ${indexName}: ${error.message}`, error.stack);
      throw error; // Re-throw to be handled by global exception filter or controller
    }
  }

  async deleteIndex(indexName: string): Promise<void> {
    this.logger.log(`Admin request: Delete index ${indexName}`);
    // Authorization
    if (this.isProtectedIndex(indexName)) {
        throw new ForbiddenException(`Index ${indexName} is protected and cannot be deleted via this API.`);
    }
    try {
      await this.indexManagementService.deleteIndex(indexName);
      this.logger.log(`Index ${indexName} deleted successfully.`);
    } catch (error) {
      this.logger.error(`Failed to delete index ${indexName}: ${error.message}`, error.stack);
      throw error;
    }
  }
  
  private isProtectedIndex(indexName: string): boolean {
    // Logic to prevent deletion of critical indices (e.g. based on active aliases or config)
    const productAlias = this.configService.get('elasticsearch.aliases.products');
    return indexName === productAlias;
  }

  async updateAlias(aliasName: string, newIndexName: string, oldIndexName?: string): Promise<void> {
    this.logger.log(`Admin request: Update alias ${aliasName} to point to ${newIndexName}`);
    // Authorization
    try {
      await this.indexManagementService.updateAlias(aliasName, newIndexName, oldIndexName);
      this.logger.log(`Alias ${aliasName} updated successfully.`);
    } catch (error) {
      this.logger.error(`Failed to update alias ${aliasName}: ${error.message}`, error.stack);
      throw error;
    }
  }

  async triggerReindex(params: ReindexParams): Promise<ReindexResponse> {
    this.logger.log(
        `Admin request: Trigger reindex from ${params.sourceIndex} to ${params.destIndex}, wait: ${params.waitForCompletion}`
    );
    // Authorization
    try {
      const response = await this.indexManagementService.startReindexTask(
        params.sourceIndex,
        params.destIndex,
        params.script,
        params.waitForCompletion
      );
      this.logger.log(`Reindex task started/completed: ${JSON.stringify(response)}`);
      return response;
    } catch (error) {
      this.logger.error(`Failed to trigger reindex: ${error.message}`, error.stack);
      throw error;
    }
  }

  // --- Manual Data Operations ---
  async manualIndexProduct(productData: any): Promise<any> {
    this.logger.log(`Admin request: Manually index product ID ${productData.id}`);
    // Authorization + Validation
    // Assuming productData is a complete ProductDocument
    try {
        return await this.productIndexingService.indexProduct(productData);
    } catch(error) {
        this.logger.error(`Manual product indexing failed for ID ${productData.id}`, error.stack);
        throw error;
    }
  }

  async manualDeleteProduct(productId: string): Promise<any> {
    this.logger.log(`Admin request: Manually delete product ID ${productId}`);
    // Authorization
    try {
        return await this.productIndexingService.deleteProduct(productId);
    } catch(error) {
        if (error instanceof IndexingException && error.status === 404) {
            throw new NotFoundException(`Product ${productId} not found for deletion.`);
        }
        this.logger.error(`Manual product deletion failed for ID ${productId}`, error.stack);
        throw error;
    }
  }

  // --- Monitoring & Stats ---
  async getClusterHealth(): Promise<ClusterHealthResponse> {
    this.logger.debug('Admin request: Get cluster health');
    try {
      const health = await this.elasticsearchService.cluster.health();
      return health.body;
    } catch (error) {
      this.logger.error(`Failed to get cluster health: ${error.message}`, error.stack);
      throw error;
    }
  }

  async getIndexStats(indexName?: string): Promise<IndicesStatsResponse> {
    this.logger.debug(`Admin request: Get stats for index ${indexName || '_all'}`);
    try {
      const stats = await this.elasticsearchService.indices.stats({ index: indexName || '_all' });
      return stats.body;
    } catch (error) {
      this.logger.error(`Failed to get index stats: ${error.message}`, error.stack);
      throw error;
    }
  }

  // --- Cache Management ---
  async clearAllCaches(): Promise<void> {
    this.logger.log('Admin request: Clear all caches');
    // Authorization
    try {
      await this.cacheManager.reset(); // Clears all entries from the current store
      this.logger.log('All caches cleared successfully.');
    } catch (error) {
      this.logger.error(`Failed to clear all caches: ${error.message}`, error.stack);
      throw error;
    }
  }

  async clearCacheByKeyPattern(pattern: string): Promise<void> {
    this.logger.log(`Admin request: Clear cache by pattern: ${pattern}`);
    // Authorization
    // Note: Standard cache-manager might not support pattern deletion directly.
    // For Redis, you might use `scan` and `del`. This requires custom logic.
    // For in-memory, you'd iterate keys. This is a simplified example.
    if (this.cacheManager.store.name === 'memory') {
        const keys = await this.cacheManager.store.keys();
        const keysToDelete = keys.filter(key => key.match(new RegExp(pattern)));
        for (const key of keysToDelete) {
            await this.cacheManager.del(key);
        }
        this.logger.log(`Cleared ${keysToDelete.length} cache entries matching pattern ${pattern}`);
    } else {
        this.logger.warn(`Pattern-based cache clearing not fully supported for store: ${this.cacheManager.store.name}. Attempting generic approach or recommend manual for Redis.`);
        // For Redis, you would typically use ioredis or node-redis client directly to SCAN and DEL
        // This is a placeholder for more complex logic needed for distributed caches
        throw new Error('Pattern-based cache clearing for Redis requires custom implementation.');
    }
  }
}

// Assume IndexManagementService provides higher-level abstractions for index operations
@Injectable()
class IndexManagementService {
    constructor(private readonly esService: ElasticsearchService, private readonly config: ConfigService) {}
    async createIndex(indexName: string, settings?: any, mappings?: any) { /* ... */ }
    async deleteIndex(indexName: string) { /* ... */ }
    async updateAlias(aliasName: string, newIndexName: string, oldIndexName?: string) { /* ... */ }
    async startReindexTask(source: string, dest: string, script?: any, waitForCompletion?: boolean): Promise<ReindexResponse> { 
        const response = await this.esService.reindex({ source: { index: source }, dest: { index: dest }, script, wait_for_completion: waitForCompletion });
        return response.body;
     }
}
```

## 5. Security Considerations

- **Authentication & Authorization**: All Admin Facade endpoints MUST be protected with robust authentication and role-based authorization mechanisms. Only privileged users (administrators, SREs) should have access.
- **Input Validation**: Thoroughly validate all input parameters to prevent injection attacks or unintended operations (e.g., validating index names, script content for re-indexing).
- **Destructive Operations**: Operations like deleting indices or clearing caches should have extra safeguards, confirmations, or be restricted to highly privileged roles.
- **Audit Logging**: All administrative actions taken through this facade MUST be audit logged, recording who performed what action and when.

## 6. Interactions

- **Admin UI/CLI**: These are the primary clients of the Admin Facade.
- **Specialized Services**: The Admin Facade delegates tasks to services like `IndexManagementService`, specific `IndexingServices` (Product, Category, Content), and `CacheManager`.
- **Elasticsearch Client Service**: Used for direct interaction with Elasticsearch for status and stats when not abstracted by another service.
- **Authentication/Authorization Service**: To protect its endpoints.

## 7. Benefits

- **Centralized Admin Operations**: Provides a single, consistent interface for all search-related administrative tasks.
- **Abstraction**: Hides the low-level details of Elasticsearch API calls or cache management specifics from the admin client.
- **Security Enforcement**: Acts as a gatekeeper where security policies for administrative actions can be enforced.
- **Improved Manageability**: Simplifies the management and maintenance of the Search Service.

The Admin Facade is a critical component for the operational health and maintainability of the Search Service, enabling administrators to manage indices, monitor performance, and handle data effectively.
