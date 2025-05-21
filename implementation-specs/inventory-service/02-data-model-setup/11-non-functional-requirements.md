# Non-Functional Requirements for Inventory Service Data Model

## Overview

This document outlines the non-functional requirements for the Inventory Service data model, addressing performance, scalability, availability, resilience, and other quality attributes that are essential for a robust inventory management system.

## Performance Requirements

### 1. Query Performance

| Operation | Requirement | Measurement |
|-----------|-------------|------------|
| Get Inventory Item by SKU | < 50ms (p95) | Response time under normal load |
| List Inventory Items (paginated) | < 100ms (p95) | Response time for 100 items per page |
| Check Inventory Availability | < 30ms (p95) | Response time for single item check |
| Bulk Inventory Check | < 200ms (p95) | Response time for up to 50 items |
| Reserve Inventory | < 150ms (p95) | Transaction completion time |
| Stock Transaction Creation | < 100ms (p95) | Insert operation time |
| Inventory Search with Filters | < 250ms (p95) | Complex query response time |

```typescript
// src/common/interceptors/performance-monitoring.interceptor.ts
import { Injectable, NestInterceptor, ExecutionContext, CallHandler, Logger } from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import * as AWS from 'aws-sdk';

@Injectable()
export class PerformanceMonitoringInterceptor implements NestInterceptor {
  private readonly logger = new Logger(PerformanceMonitoringInterceptor.name);
  private readonly cloudwatch: AWS.CloudWatch;
  
  constructor() {
    this.cloudwatch = new AWS.CloudWatch({
      region: process.env.AWS_REGION || 'us-east-1'
    });
  }
  
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const startTime = Date.now();
    const req = context.switchToHttp().getRequest();
    const method = req.method;
    const url = req.url;
    
    return next
      .handle()
      .pipe(
        tap(() => {
          const duration = Date.now() - startTime;
          this.logger.debug(`${method} ${url} took ${duration}ms`);
          
          // Only record metrics in production to avoid costs
          if (process.env.NODE_ENV === 'production') {
            this.recordMetric(method, url, duration);
          }
          
          // Alert on slow queries
          if (duration > this.getThresholdForEndpoint(url)) {
            this.logger.warn(`Slow query detected: ${method} ${url} took ${duration}ms`);
          }
        }),
      );
  }
  
  private async recordMetric(method: string, url: string, duration: number): Promise<void> {
    try {
      const endpoint = this.normalizeUrl(url);
      
      await this.cloudwatch.putMetricData({
        Namespace: 'InventoryService/API',
        MetricData: [
          {
            MetricName: 'ResponseTime',
            Dimensions: [
              {
                Name: 'Endpoint',
                Value: endpoint
              },
              {
                Name: 'Method',
                Value: method
              }
            ],
            Value: duration,
            Unit: 'Milliseconds'
          }
        ]
      }).promise();
    } catch (error) {
      this.logger.error(`Failed to record metric: ${error.message}`);
    }
  }
  
  private normalizeUrl(url: string): string {
    // Convert URLs with IDs to a normalized form
    // e.g., /inventory/123 -> /inventory/:id
    return url.replace(/\/[0-9a-fA-F-]{36}/g, '/:id');
  }
  
  private getThresholdForEndpoint(url: string): number {
    // Define thresholds for different endpoints
    if (url.includes('/inventory/availability')) {
      return 50; // 50ms threshold for availability checks
    } else if (url.includes('/inventory/reserve')) {
      return 200; // 200ms threshold for reserve operations
    } else if (url.includes('/inventory/bulk')) {
      return 300; // 300ms threshold for bulk operations
    }
    
    return 150; // Default threshold
  }
}
```

### 2. Database Connection Pooling

```typescript
// src/config/database-performance.config.ts
import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { ConfigService } from '@nestjs/config';

export const getDatabasePerformanceConfig = (configService: ConfigService): Partial<TypeOrmModuleOptions> => ({
  // Connection pool configuration
  extra: {
    // Minimum connections in pool
    min: configService.get<number>('DB_POOL_MIN') || 5,
    // Maximum connections in pool
    max: configService.get<number>('DB_POOL_MAX') || 20,
    // Idle timeout (ms)
    idleTimeoutMillis: configService.get<number>('DB_IDLE_TIMEOUT') || 30000,
    // Maximum client lifetime (ms) - to handle memory leaks
    maxLifetimeMillis: configService.get<number>('DB_CLIENT_TIMEOUT') || 3600000, // 1 hour
    // Time to wait for connection (ms)
    connectionTimeoutMillis: configService.get<number>('DB_CONNECTION_TIMEOUT') || 5000,
    // Check connection validity before use
    checkExpirationOnUse: true
  },
  // Query execution timeout (ms)
  maxQueryExecutionTime: configService.get<number>('DB_QUERY_TIMEOUT') || 5000
});
```

### 3. Query Optimization

```typescript
// src/inventory/repositories/optimized-query.repository.ts
import { EntityRepository, Repository, SelectQueryBuilder } from 'typeorm';
import { InventoryItem } from '../entities/inventory-item.entity';

@EntityRepository(InventoryItem)
export class OptimizedInventoryRepository extends Repository<InventoryItem> {
  /**
   * Optimized query for finding available inventory
   * @param skus Array of SKUs to check
   * @param warehouseId Optional warehouse filter
   */
  async findAvailableInventory(skus: string[], warehouseId?: string): Promise<InventoryItem[]> {
    const queryBuilder = this.createQueryBuilder('item')
      .select([
        'item.id',
        'item.sku',
        'item.name',
        'item.quantity',
        'item.reservedQuantity',
        'item.warehouseId'
      ])
      .where('item.isActive = :isActive', { isActive: true })
      .andWhere('item.quantity > item.reservedQuantity')
      .andWhere('item.sku IN (:...skus)', { skus });
    
    if (warehouseId) {
      queryBuilder.andWhere('item.warehouseId = :warehouseId', { warehouseId });
    }
    
    // Add index hints for PostgreSQL
    queryBuilder.expressionMap.mainAlias.metadata.indices.forEach(index => {
      if (index.columns.some(column => column.propertyName === 'sku')) {
        queryBuilder.useIndex(`idx_inventory_item_sku`);
      }
    });
    
    // Use read-only transaction for better concurrency
    queryBuilder.setLock('pessimistic_read');
    
    // Cache common queries
    if (skus.length <= 10) {
      queryBuilder.cache(true);
    }
    
    return queryBuilder.getMany();
  }
  
  /**
   * Optimized query for inventory dashboard
   * Returns aggregated data for quick dashboard display
   */
  async getInventorySummary(): Promise<any> {
    // Use custom raw query for performance
    return this.manager.query(`
      WITH inventory_summary AS (
        SELECT
          w.name as warehouse_name,
          COUNT(i.id) as total_items,
          SUM(i.quantity) as total_quantity,
          SUM(i.reserved_quantity) as total_reserved,
          SUM(i.quantity - i.reserved_quantity) as total_available,
          COUNT(CASE WHEN i.quantity <= i.minimum_stock_level THEN 1 END) as low_stock_count
        FROM
          inventory_items i
          JOIN warehouses w ON i.warehouse_id = w.id
        WHERE
          i.is_active = true
        GROUP BY
          w.name
      )
      SELECT
        warehouse_name,
        total_items,
        total_quantity,
        total_reserved,
        total_available,
        low_stock_count,
        CASE 
          WHEN total_quantity > 0 THEN 
            ROUND((total_available::float / total_quantity) * 100, 2)
          ELSE 0 
        END as availability_percentage
      FROM
        inventory_summary
      ORDER BY
        total_items DESC;
    `);
  }
}
```

## Scalability Requirements

### 1. Data Volume Scalability

| Metric | Requirement |
|--------|-------------|
| Maximum SKUs | 10 million |
| Transactions per SKU | Up to 5,000 |
| Warehouses | Up to 1,000 |
| Daily Inventory Updates | Up to 500,000 |
| Data Growth | 20% annual growth |

### 2. Horizontal Scaling

```typescript
// src/config/scaling.config.ts
export interface ScalingConfig {
  enableSharding: boolean;
  enableReadReplicas: boolean;
  readReplicaHosts?: string[];
  shardingStrategy?: 'none' | 'warehouse' | 'product-category';
}

export const getScalingConfig = (): ScalingConfig => ({
  enableSharding: process.env.ENABLE_SHARDING === 'true',
  enableReadReplicas: process.env.ENABLE_READ_REPLICAS === 'true',
  readReplicaHosts: process.env.READ_REPLICA_HOSTS ? 
    process.env.READ_REPLICA_HOSTS.split(',') : [],
  shardingStrategy: (process.env.SHARDING_STRATEGY || 'none') as any
});
```

### 3. Database Partitioning

```sql
-- SQL for implementing table partitioning
-- src/migrations/1709123456789-AddTablePartitioning.ts

-- Convert stock_transactions table to use partitioning
CREATE TABLE stock_transactions_new (
    id UUID PRIMARY KEY,
    inventory_item_id UUID NOT NULL,
    warehouse_id UUID NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    reference_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
) PARTITION BY RANGE (transaction_date);

-- Create partitions for last 12 months plus future month
DO $$
DECLARE
   start_date DATE := date_trunc('month', now()) - interval '11 months';
   end_date DATE;
   partition_name TEXT;
BEGIN
   FOR i IN 0..12 LOOP
      end_date := start_date + interval '1 month';
      partition_name := 'stock_transactions_' || to_char(start_date, 'YYYY_MM');
      
      EXECUTE format(
         'CREATE TABLE %I PARTITION OF stock_transactions_new
          FOR VALUES FROM (%L) TO (%L)',
          partition_name,
          start_date,
          end_date
      );
      
      start_date := end_date;
   END LOOP;
END $$;

-- Create appropriate indexes on partitions
CREATE INDEX idx_stock_tx_item_id ON stock_transactions_new(inventory_item_id);
CREATE INDEX idx_stock_tx_warehouse_id ON stock_transactions_new(warehouse_id);
CREATE INDEX idx_stock_tx_type ON stock_transactions_new(transaction_type);
CREATE INDEX idx_stock_tx_date ON stock_transactions_new(transaction_date);

-- Copy data from old table to new
INSERT INTO stock_transactions_new 
SELECT * FROM stock_transactions;

-- Rename tables to complete migration
ALTER TABLE stock_transactions RENAME TO stock_transactions_old;
ALTER TABLE stock_transactions_new RENAME TO stock_transactions;
```

### 4. DynamoDB Auto-scaling

```typescript
// src/config/dynamodb-scaling.config.ts
import * as AWS from 'aws-sdk';

export interface DynamoDBScalingConfig {
  tableNames: string[];
  minCapacity: number;
  maxCapacity: number;
  targetUtilization: number;
  scaleOutCooldown: number;
  scaleInCooldown: number;
}

export async function configureDynamoDBAutoScaling(config: DynamoDBScalingConfig): Promise<void> {
  const applicationAutoScaling = new AWS.ApplicationAutoScaling({
    region: process.env.AWS_REGION || 'us-east-1'
  });
  
  for (const tableName of config.tableNames) {
    // Register scalable target for read capacity
    await applicationAutoScaling.registerScalableTarget({
      ServiceNamespace: 'dynamodb',
      ResourceId: `table/${tableName}`,
      ScalableDimension: 'dynamodb:table:ReadCapacityUnits',
      MinCapacity: config.minCapacity,
      MaxCapacity: config.maxCapacity
    }).promise();
    
    // Register scalable target for write capacity
    await applicationAutoScaling.registerScalableTarget({
      ServiceNamespace: 'dynamodb',
      ResourceId: `table/${tableName}`,
      ScalableDimension: 'dynamodb:table:WriteCapacityUnits',
      MinCapacity: config.minCapacity,
      MaxCapacity: config.maxCapacity
    }).promise();
    
    // Configure scaling policy for read capacity
    await applicationAutoScaling.putScalingPolicy({
      ServiceNamespace: 'dynamodb',
      ResourceId: `table/${tableName}`,
      ScalableDimension: 'dynamodb:table:ReadCapacityUnits',
      PolicyName: `${tableName}-read-scaling-policy`,
      PolicyType: 'TargetTrackingScaling',
      TargetTrackingScalingPolicyConfiguration: {
        PredefinedMetricSpecification: {
          PredefinedMetricType: 'DynamoDBReadCapacityUtilization'
        },
        ScaleOutCooldown: config.scaleOutCooldown,
        ScaleInCooldown: config.scaleInCooldown,
        TargetValue: config.targetUtilization
      }
    }).promise();
    
    // Configure scaling policy for write capacity
    await applicationAutoScaling.putScalingPolicy({
      ServiceNamespace: 'dynamodb',
      ResourceId: `table/${tableName}`,
      ScalableDimension: 'dynamodb:table:WriteCapacityUnits',
      PolicyName: `${tableName}-write-scaling-policy`,
      PolicyType: 'TargetTrackingScaling',
      TargetTrackingScalingPolicyConfiguration: {
        PredefinedMetricSpecification: {
          PredefinedMetricType: 'DynamoDBWriteCapacityUtilization'
        },
        ScaleOutCooldown: config.scaleOutCooldown,
        ScaleInCooldown: config.scaleInCooldown,
        TargetValue: config.targetUtilization
      }
    }).promise();
  }
}
```

## Availability and Reliability Requirements

### 1. High Availability

| Requirement | Target |
|-------------|--------|
| Service Uptime | 99.99% (52 minutes of downtime per year) |
| Database Availability | 99.995% (26 minutes of downtime per year) |
| Read Availability | 99.999% (5 minutes of downtime per year) |
| Recovery Time Objective (RTO) | < 5 minutes |
| Recovery Point Objective (RPO) | < 1 minute |

### 2. Resilience Implementation

```typescript
// src/common/resilience/circuit-breaker.ts
import { Injectable, Logger } from '@nestjs/common';

enum CircuitState {
  CLOSED,  // Normal operation
  OPEN,    // Failing, reject requests
  HALF_OPEN // Testing if system has recovered
}

interface CircuitBreakerOptions {
  failureThreshold: number;
  resetTimeout: number;
  halfOpenSuccessThreshold: number;
}

@Injectable()
export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount: number = 0;
  private successCount: number = 0;
  private lastFailureTime: number = 0;
  private readonly logger = new Logger(CircuitBreaker.name);
  
  constructor(
    private readonly options: CircuitBreakerOptions = {
      failureThreshold: 5,
      resetTimeout: 30000, // 30 seconds
      halfOpenSuccessThreshold: 3
    }
  ) {}
  
  async execute<T>(command: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailureTime >= this.options.resetTimeout) {
        this.transitionToHalfOpen();
      } else {
        this.logger.warn('Circuit breaker is OPEN, rejecting request');
        throw new Error('Service unavailable');
      }
    }
    
    try {
      const result = await command();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  private onSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.options.halfOpenSuccessThreshold) {
        this.reset();
      }
    }
  }
  
  private onFailure(): void {
    this.lastFailureTime = Date.now();
    
    if (this.state === CircuitState.HALF_OPEN) {
      this.transitionToOpen();
    } else if (this.state === CircuitState.CLOSED) {
      this.failureCount++;
      if (this.failureCount >= this.options.failureThreshold) {
        this.transitionToOpen();
      }
    }
  }
  
  private transitionToOpen(): void {
    this.state = CircuitState.OPEN;
    this.logger.warn('Circuit breaker transitioned to OPEN');
  }
  
  private transitionToHalfOpen(): void {
    this.state = CircuitState.HALF_OPEN;
    this.successCount = 0;
    this.logger.log('Circuit breaker transitioned to HALF_OPEN');
  }
  
  private reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.logger.log('Circuit breaker reset to CLOSED');
  }
  
  getState(): CircuitState {
    return this.state;
  }
}
```

### 3. Multi-AZ Database Configuration

```yaml
# CloudFormation template for multi-AZ database
Resources:
  InventoryServiceDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      Engine: postgres
      EngineVersion: "15.2"
      DBInstanceClass: db.r6g.large
      AllocatedStorage: 100
      StorageType: gp3
      MultiAZ: true
      AvailabilityZone: !Ref PrimaryAZ
      DBName: inventory_service
      MasterUsername: !Ref DBMasterUsername
      MasterUserPassword: !Ref DBMasterPassword
      BackupRetentionPeriod: 7
      PreferredBackupWindow: "03:00-04:00"
      PreferredMaintenanceWindow: "sun:04:30-sun:05:30"
      EnablePerformanceInsights: true
      PerformanceInsightsRetentionPeriod: 7
      MonitoringInterval: 60
      MonitoringRoleArn: !GetAtt MonitoringRole.Arn
      EnableCloudwatchLogsExports:
        - postgresql
        - upgrade
      DBSubnetGroupName: !Ref DBSubnetGroup
      VPCSecurityGroups:
        - !Ref DBSecurityGroup
      Tags:
        - Key: Service
          Value: InventoryService
```

## Caching Strategy

### 1. Multi-level Caching

```typescript
// src/common/caching/multi-level-cache.service.ts
import { Injectable, Logger, Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';
import * as AWS from 'aws-sdk';

interface CacheOptions {
  ttl?: number;
  useLocalCache?: boolean;
  useRedisCache?: boolean;
  tags?: string[];
}

@Injectable()
export class MultiLevelCacheService {
  private readonly logger = new Logger(MultiLevelCacheService.name);
  private readonly elasticache: AWS.ElastiCache;
  private readonly localCacheTTL: number = 60; // 60 seconds
  private readonly redisCacheTTL: number = 3600; // 1 hour
  
  constructor(
    @Inject(CACHE_MANAGER) private localCache: Cache,
    private redisCache: any // Redis client
  ) {
    this.elasticache = new AWS.ElastiCache({
      region: process.env.AWS_REGION || 'us-east-1'
    });
  }
  
  async get<T>(key: string, options?: CacheOptions): Promise<T | null> {
    // Try local memory cache first (fastest)
    if (options?.useLocalCache !== false) {
      const localValue = await this.localCache.get<T>(key);
      if (localValue !== undefined) {
        this.logger.debug(`Cache hit (local): ${key}`);
        return localValue;
      }
    }
    
    // Try Redis cache next
    if (options?.useRedisCache !== false && this.redisCache) {
      try {
        const redisValue = await this.redisCache.get(key);
        if (redisValue) {
          this.logger.debug(`Cache hit (Redis): ${key}`);
          const parsed = JSON.parse(redisValue);
          
          // Store in local cache for future requests
          if (options?.useLocalCache !== false) {
            await this.localCache.set(key, parsed, this.localCacheTTL);
          }
          
          return parsed;
        }
      } catch (error) {
        this.logger.warn(`Redis cache error: ${error.message}`);
      }
    }
    
    this.logger.debug(`Cache miss: ${key}`);
    return null;
  }
  
  async set<T>(key: string, value: T, options?: CacheOptions): Promise<void> {
    const localTTL = options?.ttl || this.localCacheTTL;
    const redisTTL = options?.ttl || this.redisCacheTTL;
    
    // Store in local memory cache
    if (options?.useLocalCache !== false) {
      await this.localCache.set(key, value, localTTL);
    }
    
    // Store in Redis cache
    if (options?.useRedisCache !== false && this.redisCache) {
      try {
        await this.redisCache.set(
          key,
          JSON.stringify(value),
          'EX',
          redisTTL
        );
        
        // Add tags if specified
        if (options?.tags?.length) {
          for (const tag of options.tags) {
            await this.redisCache.sadd(`tag:${tag}`, key);
          }
        }
      } catch (error) {
        this.logger.warn(`Redis cache error: ${error.message}`);
      }
    }
  }
  
  async invalidate(key: string): Promise<void> {
    // Remove from local cache
    await this.localCache.del(key);
    
    // Remove from Redis cache
    if (this.redisCache) {
      try {
        await this.redisCache.del(key);
      } catch (error) {
        this.logger.warn(`Redis cache error: ${error.message}`);
      }
    }
  }
  
  async invalidateByTag(tag: string): Promise<void> {
    if (!this.redisCache) {
      return;
    }
    
    try {
      // Get all keys with this tag
      const keys = await this.redisCache.smembers(`tag:${tag}`);
      
      if (keys.length > 0) {
        // Remove all keys from local cache
        for (const key of keys) {
          await this.localCache.del(key);
        }
        
        // Remove all keys from Redis cache
        await this.redisCache.del(...keys);
        
        // Remove the tag set itself
        await this.redisCache.del(`tag:${tag}`);
        
        this.logger.debug(`Invalidated ${keys.length} cache entries by tag: ${tag}`);
      }
    } catch (error) {
      this.logger.warn(`Failed to invalidate by tag: ${error.message}`);
    }
  }
}
```

### 2. Inventory-Specific Caching

```typescript
// src/inventory/services/inventory-cache.service.ts
import { Injectable } from '@nestjs/common';
import { MultiLevelCacheService } from '../../common/caching/multi-level-cache.service';
import { InventoryItem } from '../entities/inventory-item.entity';

@Injectable()
export class InventoryCacheService {
  private readonly INVENTORY_ITEM_KEY_PREFIX = 'inventory:item:';
  private readonly INVENTORY_LIST_KEY_PREFIX = 'inventory:list:';
  private readonly AVAILABILITY_KEY_PREFIX = 'inventory:availability:';
  
  constructor(private cacheService: MultiLevelCacheService) {}
  
  async getInventoryItem(sku: string): Promise<InventoryItem | null> {
    const key = `${this.INVENTORY_ITEM_KEY_PREFIX}${sku}`;
    return this.cacheService.get<InventoryItem>(key);
  }
  
  async setInventoryItem(item: InventoryItem): Promise<void> {
    const key = `${this.INVENTORY_ITEM_KEY_PREFIX}${item.sku}`;
    await this.cacheService.set(key, item, {
      ttl: 300, // 5 minutes
      tags: ['inventory', `warehouse:${item.warehouseId}`]
    });
  }
  
  async getInventoryList(warehouseId: string, page: number, limit: number): Promise<InventoryItem[] | null> {
    const key = `${this.INVENTORY_LIST_KEY_PREFIX}${warehouseId}:${page}:${limit}`;
    return this.cacheService.get<InventoryItem[]>(key);
  }
  
  async setInventoryList(warehouseId: string, page: number, limit: number, items: InventoryItem[]): Promise<void> {
    const key = `${this.INVENTORY_LIST_KEY_PREFIX}${warehouseId}:${page}:${limit}`;
    await this.cacheService.set(key, items, {
      ttl: 60, // 1 minute
      tags: ['inventory', `warehouse:${warehouseId}`]
    });
  }
  
  async getAvailability(skus: string[]): Promise<Record<string, number> | null> {
    const sortedSkus = [...skus].sort().join(',');
    const key = `${this.AVAILABILITY_KEY_PREFIX}${sortedSkus}`;
    return this.cacheService.get<Record<string, number>>(key);
  }
  
  async setAvailability(skus: string[], availability: Record<string, number>): Promise<void> {
    const sortedSkus = [...skus].sort().join(',');
    const key = `${this.AVAILABILITY_KEY_PREFIX}${sortedSkus}`;
    await this.cacheService.set(key, availability, {
      ttl: 30, // 30 seconds - short TTL as availability changes frequently
      tags: ['inventory', 'availability']
    });
  }
  
  async invalidateItemCache(sku: string): Promise<void> {
    const key = `${this.INVENTORY_ITEM_KEY_PREFIX}${sku}`;
    await this.cacheService.invalidate(key);
  }
  
  async invalidateWarehouseCache(warehouseId: string): Promise<void> {
    await this.cacheService.invalidateByTag(`warehouse:${warehouseId}`);
  }
  
  async invalidateAllAvailability(): Promise<void> {
    await this.cacheService.invalidateByTag('availability');
  }
}
```

## Monitoring and Observability

### 1. Metrics Collection

```typescript
// src/monitoring/metrics.service.ts
import { Injectable, Logger } from '@nestjs/common';
import * as AWS from 'aws-sdk';

export enum MetricUnit {
  COUNT = 'Count',
  MILLISECONDS = 'Milliseconds',
  BYTES = 'Bytes',
  PERCENT = 'Percent'
}

@Injectable()
export class MetricsService {
  private readonly logger = new Logger(MetricsService.name);
  private readonly cloudwatch: AWS.CloudWatch;
  private readonly namespace = 'InventoryService';
  
  constructor() {
    this.cloudwatch = new AWS.CloudWatch({
      region: process.env.AWS_REGION || 'us-east-1'
    });
  }
  
  async recordMetric(
    name: string,
    value: number,
    unit: MetricUnit,
    dimensions?: Record<string, string>
  ): Promise<void> {
    if (process.env.NODE_ENV !== 'production') {
      return; // Only record metrics in production
    }
    
    try {
      const metricData: AWS.CloudWatch.MetricData = [
        {
          MetricName: name,
          Value: value,
          Unit: unit,
          Timestamp: new Date(),
          Dimensions: dimensions ? 
            Object.entries(dimensions).map(([name, value]) => ({ Name: name, Value: value })) : 
            undefined
        }
      ];
      
      await this.cloudwatch.putMetricData({
        Namespace: this.namespace,
        MetricData: metricData
      }).promise();
      
    } catch (error) {
      this.logger.warn(`Failed to record metric ${name}: ${error.message}`);
    }
  }
  
  // Convenience methods for common metrics
  
  async recordInventoryCheck(sku: string, availableQuantity: number, durationMs: number): Promise<void> {
    await this.recordMetric('InventoryCheckDuration', durationMs, MetricUnit.MILLISECONDS, {
      SKU: sku
    });
    
    await this.recordMetric('AvailableQuantity', availableQuantity, MetricUnit.COUNT, {
      SKU: sku
    });
  }
  
  async recordReservationAttempt(sku: string, requestedQuantity: number, successful: boolean): Promise<void> {
    await this.recordMetric('ReservationAttempt', 1, MetricUnit.COUNT, {
      SKU: sku,
      Success: successful ? 'true' : 'false'
    });
    
    await this.recordMetric('RequestedQuantity', requestedQuantity, MetricUnit.COUNT, {
      SKU: sku
    });
  }
  
  async recordLowStockEvent(sku: string, currentQuantity: number, thresholdQuantity: number): Promise<void> {
    await this.recordMetric('LowStockEvent', 1, MetricUnit.COUNT, {
      SKU: sku
    });
    
    const percentOfThreshold = (currentQuantity / thresholdQuantity) * 100;
    await this.recordMetric('StockLevelPercent', percentOfThreshold, MetricUnit.PERCENT, {
      SKU: sku
    });
  }
}
```

### 2. Health Checks

```typescript
// src/health/health.controller.ts
import { Controller, Get } from '@nestjs/common';
import { HealthCheck, HealthCheckService, TypeOrmHealthIndicator, MemoryHealthIndicator } from '@nestjs/terminus';
import { RedisHealthIndicator } from './redis.health';
import { DynamoDBHealthIndicator } from './dynamodb.health';

@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private typeOrm: TypeOrmHealthIndicator,
    private redis: RedisHealthIndicator,
    private dynamoDB: DynamoDBHealthIndicator,
    private memory: MemoryHealthIndicator,
  ) {}

  @Get()
  @HealthCheck()
  check() {
    return this.health.check([
      // Database connection
      async () => this.typeOrm.pingCheck('database', { timeout: 3000 }),
      
      // Redis connection
      async () => this.redis.pingCheck('redis', { timeout: 3000 }),
      
      // DynamoDB connection
      async () => this.dynamoDB.checkConnection('dynamodb'),
      
      // Memory usage
      async () => this.memory.checkHeap('memory_heap', 250 * 1024 * 1024), // 250MB
      
      // Process load
      async () => this.memory.checkRSS('memory_rss', 512 * 1024 * 1024), // 512MB
    ]);
  }
  
  @Get('database')
  @HealthCheck()
  checkDatabase() {
    return this.health.check([
      async () => this.typeOrm.pingCheck('database', { timeout: 3000 }),
    ]);
  }
  
  @Get('cache')
  @HealthCheck()
  checkCache() {
    return this.health.check([
      async () => this.redis.pingCheck('redis', { timeout: 3000 }),
    ]);
  }
  
  @Get('dynamodb')
  @HealthCheck()
  checkDynamoDB() {
    return this.health.check([
      async () => this.dynamoDB.checkConnection('dynamodb'),
    ]);
  }
}
```

## References

- [AWS RDS Performance Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [NestJS Performance Tuning](https://docs.nestjs.com/techniques/performance)
- [AWS ElastiCache Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)
- [Circuit Breaker Pattern](https://microservices.io/patterns/reliability/circuit-breaker.html)
- [AWS CloudWatch Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/working_with_metrics.html)
- [TypeORM Performance Tips](https://typeorm.io/#/repository-api)