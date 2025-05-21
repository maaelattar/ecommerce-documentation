# TypeORM Configuration for Inventory Service

## Overview

This document details the TypeORM configuration for the Inventory Service, including database connection settings, entity configuration, and repository patterns. The configuration is specifically designed to work with PostgreSQL for the relational data aspects of the Inventory Service, in accordance with our architectural decisions.

## Configuration Structure

### Main Configuration

```typescript
// src/config/typeorm.config.ts
import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { ConfigService } from '@nestjs/config';

export const getTypeOrmConfig = (configService: ConfigService): TypeOrmModuleOptions => ({
  type: 'postgres',
  host: configService.get('DB_HOST'),
  port: configService.get('DB_PORT'),
  username: configService.get('DB_USERNAME'),
  password: configService.get('DB_PASSWORD'),
  database: configService.get('DB_DATABASE'),
  entities: [__dirname + '/../**/*.entity{.ts,.js}'],
  synchronize: false, // Never true in production
  logging: configService.get('NODE_ENV') === 'development',
  ssl: configService.get('DB_SSL') === 'true',
  extra: {
    max: 20, // Connection pool maximum
    idleTimeoutMillis: 30000, // Idle connection timeout
    connectionTimeoutMillis: 5000 // Connection timeout
  },
  migrations: [__dirname + '/../migrations/*{.ts,.js}'],
  migrationsRun: false, // Controlled migration execution
  migrationsTableName: 'migrations'
});
```

### Environment Configuration

```typescript
// src/config/env.config.ts
import { registerAs } from '@nestjs/config';

export default registerAs('database', () => ({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT, 10) || 5432,
  username: process.env.DB_USERNAME || 'postgres',
  password: process.env.DB_PASSWORD,
  database: process.env.DB_DATABASE || 'inventory_service',
  ssl: process.env.DB_SSL === 'true',
  maxConnections: parseInt(process.env.DB_MAX_CONNECTIONS, 10) || 20,
  idleTimeout: parseInt(process.env.DB_IDLE_TIMEOUT_MS, 10) || 30000,
  connectionTimeout: parseInt(process.env.DB_CONNECTION_TIMEOUT_MS, 10) || 5000
}));
```

## Entity Configuration

### Base Entity

```typescript
// src/common/entities/base.entity.ts
import { 
  PrimaryGeneratedColumn, 
  CreateDateColumn, 
  UpdateDateColumn,
  Column 
} from 'typeorm';

export abstract class BaseEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @Column({ name: 'created_by', nullable: true })
  createdBy?: string;

  @Column({ name: 'updated_by', nullable: true })
  updatedBy?: string;
}
```

### Versioned Entity

```typescript
// src/common/entities/versioned.entity.ts
import { Column } from 'typeorm';
import { BaseEntity } from './base.entity';

export abstract class VersionedEntity extends BaseEntity {
  @Column({ name: 'version', default: 1 })
  version: number;
}
```

## Repository Configuration

### Base Repository

```typescript
// src/common/repositories/base.repository.ts
import { Repository, EntityRepository, EntityManager } from 'typeorm';
import { Logger } from '@nestjs/common';

export class BaseRepository<T> extends Repository<T> {
  protected readonly logger: Logger;

  constructor(entityType: new () => T, manager: EntityManager) {
    super(entityType, manager);
    this.logger = new Logger(this.constructor.name);
  }

  /**
   * Execute a function within a transaction
   * @param fn Function to execute within the transaction
   */
  async executeInTransaction<R>(fn: (entityManager: EntityManager) => Promise<R>): Promise<R> {
    const queryRunner = this.manager.connection.createQueryRunner();
    await queryRunner.connect();
    await queryRunner.startTransaction();

    try {
      const result = await fn(queryRunner.manager);
      await queryRunner.commitTransaction();
      return result;
    } catch (error) {
      this.logger.error(`Transaction failed: ${error.message}`, error.stack);
      await queryRunner.rollbackTransaction();
      throw error;
    } finally {
      await queryRunner.release();
    }
  }
}
```

### Specialized Repository Example

```typescript
// src/inventory/repositories/inventory-item.repository.ts
import { EntityRepository, EntityManager } from 'typeorm';
import { Injectable } from '@nestjs/common';
import { InventoryItem } from '../entities/inventory-item.entity';
import { BaseRepository } from '../../common/repositories/base.repository';

@Injectable()
export class InventoryItemRepository extends BaseRepository<InventoryItem> {
  constructor(manager: EntityManager) {
    super(InventoryItem, manager);
  }

  /**
   * Find inventory item by SKU
   * @param sku The product SKU
   */
  async findBySku(sku: string): Promise<InventoryItem | null> {
    return this.findOne({ where: { sku } });
  }

  /**
   * Find available inventory items
   * @param skus Optional array of SKUs to filter by
   */
  async findAvailableItems(skus?: string[]): Promise<InventoryItem[]> {
    const query = this.createQueryBuilder('item')
      .where('item.availableQuantity > 0');
    
    if (skus && skus.length > 0) {
      query.andWhere('item.sku IN (:...skus)', { skus });
    }

    return query.getMany();
  }
}
```

## Database Connection Management

### Connection Provider

```typescript
// src/database/database.providers.ts
import { DataSource } from 'typeorm';
import { ConfigService } from '@nestjs/config';
import { getTypeOrmConfig } from '../config/typeorm.config';

export const DATABASE_CONNECTION = 'DATABASE_CONNECTION';

export const databaseProviders = [
  {
    provide: DATABASE_CONNECTION,
    useFactory: async (configService: ConfigService) => {
      const dataSource = new DataSource(getTypeOrmConfig(configService));
      return dataSource.initialize();
    },
    inject: [ConfigService],
  },
];
```

### Connection Module

```typescript
// src/database/database.module.ts
import { Module, Global } from '@nestjs/common';
import { databaseProviders } from './database.providers';
import { ConfigModule } from '@nestjs/config';

@Global()
@Module({
  imports: [ConfigModule],
  providers: [...databaseProviders],
  exports: [...databaseProviders],
})
export class DatabaseModule {}
```

## TypeORM Customizations

### Custom Naming Strategy

```typescript
// src/database/strategies/snake-naming.strategy.ts
import { DefaultNamingStrategy, NamingStrategyInterface } from 'typeorm';
import { snakeCase } from 'typeorm/util/StringUtils';

export class SnakeNamingStrategy extends DefaultNamingStrategy implements NamingStrategyInterface {
  tableName(targetName: string, userSpecifiedName: string): string {
    return userSpecifiedName ? userSpecifiedName : snakeCase(targetName);
  }

  columnName(propertyName: string, customName: string): string {
    return customName ? customName : snakeCase(propertyName);
  }

  relationName(propertyName: string): string {
    return snakeCase(propertyName);
  }

  joinColumnName(relationName: string, referencedColumnName: string): string {
    return snakeCase(`${relationName}_${referencedColumnName}`);
  }

  joinTableName(
    firstTableName: string,
    secondTableName: string,
    firstPropertyName: string,
  ): string {
    return snakeCase(`${firstTableName}_${secondTableName}`);
  }

  joinTableColumnName(tableName: string, propertyName: string): string {
    return snakeCase(`${tableName}_${propertyName}`);
  }
}
```

### Custom Subscribers

```typescript
// src/database/subscribers/timestamp.subscriber.ts
import { 
  EntitySubscriberInterface, 
  InsertEvent, 
  UpdateEvent, 
  EventSubscriber 
} from 'typeorm';
import { BaseEntity } from '../../common/entities/base.entity';

@EventSubscriber()
export class TimestampSubscriber implements EntitySubscriberInterface<BaseEntity> {
  listenTo() {
    return BaseEntity;
  }

  beforeInsert(event: InsertEvent<BaseEntity>) {
    event.entity.createdAt = new Date();
    event.entity.updatedAt = new Date();
  }

  beforeUpdate(event: UpdateEvent<BaseEntity>) {
    event.entity.updatedAt = new Date();
  }
}
```

## Error Handling

### Database Error Handler

```typescript
// src/common/errors/database.error.ts
import { QueryFailedError } from 'typeorm';
import { Logger } from '@nestjs/common';

export class DatabaseError extends Error {
  constructor(
    public readonly originalError: Error,
    public readonly context: string
  ) {
    super(`Database error in ${context}: ${originalError.message}`);
    this.name = 'DatabaseError';
    
    // Capture postgres error code if available
    if (originalError instanceof QueryFailedError) {
      const pgError = originalError as any;
      if (pgError.code) {
        (this as any).code = pgError.code;
      }
    }
  }

  static isUniqueViolation(error: any): boolean {
    return error.code === '23505';
  }

  static isForeignKeyViolation(error: any): boolean {
    return error.code === '23503';
  }

  static isCheckViolation(error: any): boolean {
    return error.code === '23514';
  }

  static handle(error: Error, context: string, logger: Logger): never {
    const dbError = new DatabaseError(error, context);
    logger.error(dbError.message, error.stack);
    throw dbError;
  }
}
```

## Testing Configuration

### Test Database Configuration

```typescript
// src/config/test-database.config.ts
import { TypeOrmModuleOptions } from '@nestjs/typeorm';

export const getTestTypeOrmConfig = (): TypeOrmModuleOptions => ({
  type: 'postgres',
  host: process.env.TEST_DB_HOST || 'localhost',
  port: parseInt(process.env.TEST_DB_PORT, 10) || 5432,
  username: process.env.TEST_DB_USERNAME || 'test',
  password: process.env.TEST_DB_PASSWORD || 'test',
  database: process.env.TEST_DB_DATABASE || 'inventory_test',
  entities: [__dirname + '/../**/*.entity{.ts,.js}'],
  synchronize: true, // Only for tests
  dropSchema: true, // Only for tests
  logging: false
});
```

## Performance Optimization

### Query Optimization

```typescript
// src/common/optimizations/query.optimization.ts
import { SelectQueryBuilder } from 'typeorm';

export function optimizeInventoryQueries(queryBuilder: SelectQueryBuilder<any>): void {
  // Disable sequential scans for large tables
  queryBuilder.setQueryRunner(queryBuilder.connection.createQueryRunner());
  
  // Add caching for read-heavy queries
  queryBuilder.cache(true);
  
  // Use pagination to limit result set size
  if (!queryBuilder.expressionMap.take) {
    queryBuilder.take(100); // Default limit if none specified
  }
}

export function addInventoryItemJoins(queryBuilder: SelectQueryBuilder<any>): void {
  queryBuilder
    .leftJoinAndSelect('item.warehouse', 'warehouse')
    .leftJoinAndSelect('item.reservations', 'reservations', 'reservations.status = :status', {
      status: 'ACTIVE'
    });
}
```

## DynamoDB Configuration for Event Sourcing

In addition to TypeORM for PostgreSQL, the Inventory Service also utilizes DynamoDB for event sourcing:

```typescript
// src/config/dynamodb.config.ts
import { ConfigService } from '@nestjs/config';
import * as AWS from 'aws-sdk';

export const getDynamoDBConfig = (configService: ConfigService): AWS.DynamoDB.ClientConfiguration => ({
  region: configService.get('AWS_REGION') || 'us-east-1',
  accessKeyId: configService.get('AWS_ACCESS_KEY_ID'),
  secretAccessKey: configService.get('AWS_SECRET_ACCESS_KEY'),
  endpoint: configService.get('DYNAMODB_ENDPOINT'), // For local development
  maxRetries: 3,
  httpOptions: {
    timeout: 5000, // 5 seconds
    connectTimeout: 1000 // 1 second
  }
});

export const getDynamoDBClient = (configService: ConfigService): AWS.DynamoDB => {
  return new AWS.DynamoDB(getDynamoDBConfig(configService));
};

export const getDynamoDBDocumentClient = (configService: ConfigService): AWS.DynamoDB.DocumentClient => {
  const dynamoDB = getDynamoDBClient(configService);
  return new AWS.DynamoDB.DocumentClient({ service: dynamoDB });
};
```

## Integration with NestJS

### TypeORM Module Integration

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { getTypeOrmConfig } from './config/typeorm.config';
import { InventoryModule } from './inventory/inventory.module';
import { EventSourcingModule } from './event-sourcing/event-sourcing.module';
import databaseConfig from './config/env.config';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [databaseConfig]
    }),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: getTypeOrmConfig
    }),
    InventoryModule,
    EventSourcingModule
  ]
})
export class AppModule {}
```

## AWS-Specific Configurations

### RDS Configuration

```typescript
// src/config/aws-rds.config.ts
import { ConfigService } from '@nestjs/config';
import * as AWS from 'aws-sdk';

export const getRDSConfig = (configService: ConfigService): AWS.RDS.ClientConfiguration => ({
  region: configService.get('AWS_REGION') || 'us-east-1',
  accessKeyId: configService.get('AWS_ACCESS_KEY_ID'),
  secretAccessKey: configService.get('AWS_SECRET_ACCESS_KEY')
});

export const getRDSClient = (configService: ConfigService): AWS.RDS => {
  return new AWS.RDS(getRDSConfig(configService));
};
```

## References

- [TypeORM Documentation](https://typeorm.io/)
- [NestJS TypeORM Integration](https://docs.nestjs.com/techniques/database)
- [AWS SDK for JavaScript](https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/DynamoDB.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [Amazon RDS for PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)