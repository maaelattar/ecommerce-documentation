# TypeORM Configuration Specification

## Overview

This document details the TypeORM configuration for the Product Service, including database connection settings, entity configuration, and migration strategy.

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
    synchronize: false,
    logging: configService.get('NODE_ENV') === 'development',
    ssl: configService.get('DB_SSL') === 'true',
    extra: {
        max: 20, // Maximum number of connections in the pool
        connectionTimeoutMillis: 5000, // Connection timeout
        idleTimeoutMillis: 30000, // Idle connection timeout
    },
    migrations: [__dirname + '/../migrations/*{.ts,.js}'],
    migrationsRun: true,
    migrationsTableName: 'migrations',
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
    database: process.env.DB_DATABASE || 'ecommerce',
    ssl: process.env.DB_SSL === 'true',
}));
```

## Entity Configuration

### Base Entity

```typescript
// src/common/entities/base.entity.ts
import { PrimaryGeneratedColumn, CreateDateColumn, UpdateDateColumn } from 'typeorm';

export abstract class BaseEntity {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;
}
```

### Entity Decorators

```typescript
// src/common/decorators/entity.decorators.ts
import { Entity, Column } from 'typeorm';

export function AuditedEntity() {
    return function (target: any) {
        Entity()(target);
        Column('uuid', { name: 'created_by' })(target.prototype, 'createdBy');
        Column('uuid', { name: 'updated_by' })(target.prototype, 'updatedBy');
    };
}

export function SoftDeleteEntity() {
    return function (target: any) {
        Entity()(target);
        Column('timestamp', { name: 'deleted_at', nullable: true })(target.prototype, 'deletedAt');
    };
}
```

## Migration Configuration

### Migration Script

```typescript
// src/migrations/1709123456789-InitialSchema.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class InitialSchema1709123456789 implements MigrationInterface {
    name = 'InitialSchema1709123456789';

    public async up(queryRunner: QueryRunner): Promise<void> {
        // Create extensions
        await queryRunner.query(`CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`);
        await queryRunner.query(`CREATE EXTENSION IF NOT EXISTS "pgcrypto"`);

        // Create product_variants table
        await queryRunner.query(`
            CREATE TABLE product_variants (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                product_id UUID NOT NULL,
                sku VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                attributes JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID,
                updated_by UUID
            )
        `);

        // Create product_prices table
        await queryRunner.query(`
            CREATE TABLE product_prices (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                product_variant_id UUID NOT NULL REFERENCES product_variants(id),
                base_price DECIMAL(10,2) NOT NULL,
                sale_price DECIMAL(10,2) NOT NULL,
                msrp DECIMAL(10,2) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                price_type VARCHAR(20) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        `);

        // Create inventory table
        await queryRunner.query(`
            CREATE TABLE inventory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                product_variant_id UUID NOT NULL REFERENCES product_variants(id),
                quantity INTEGER NOT NULL DEFAULT 0,
                reserved_quantity INTEGER NOT NULL DEFAULT 0,
                available_quantity INTEGER NOT NULL DEFAULT 0,
                status VARCHAR(20) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB,
                CONSTRAINT positive_quantity CHECK (quantity >= 0),
                CONSTRAINT positive_reserved CHECK (reserved_quantity >= 0),
                CONSTRAINT valid_available CHECK (available_quantity >= 0)
            )
        `);

        // Create indexes
        await queryRunner.query(`
            CREATE INDEX idx_product_variants_product ON product_variants(product_id);
            CREATE INDEX idx_product_variants_sku ON product_variants(sku);
            CREATE INDEX idx_product_prices_variant ON product_prices(product_variant_id);
            CREATE INDEX idx_inventory_variant ON inventory(product_variant_id);
            CREATE INDEX idx_inventory_status ON inventory(status);
        `);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        // Drop indexes
        await queryRunner.query(`DROP INDEX IF EXISTS idx_inventory_status`);
        await queryRunner.query(`DROP INDEX IF EXISTS idx_inventory_variant`);
        await queryRunner.query(`DROP INDEX IF EXISTS idx_product_prices_variant`);
        await queryRunner.query(`DROP INDEX IF EXISTS idx_product_variants_sku`);
        await queryRunner.query(`DROP INDEX IF EXISTS idx_product_variants_product`);

        // Drop tables
        await queryRunner.query(`DROP TABLE IF EXISTS inventory`);
        await queryRunner.query(`DROP TABLE IF EXISTS product_prices`);
        await queryRunner.query(`DROP TABLE IF EXISTS product_variants`);

        // Drop extensions
        await queryRunner.query(`DROP EXTENSION IF EXISTS "pgcrypto"`);
        await queryRunner.query(`DROP EXTENSION IF EXISTS "uuid-ossp"`);
    }
}
```

## Connection Management

### Connection Pool

```typescript
// src/database/connection-pool.ts
import { DataSource } from 'typeorm';
import { getTypeOrmConfig } from '../config/typeorm.config';
import { ConfigService } from '@nestjs/config';

export class DatabaseConnectionPool {
    private static instance: DatabaseConnectionPool;
    private dataSource: DataSource;

    private constructor() {}

    static getInstance(): DatabaseConnectionPool {
        if (!DatabaseConnectionPool.instance) {
            DatabaseConnectionPool.instance = new DatabaseConnectionPool();
        }
        return DatabaseConnectionPool.instance;
    }

    async initialize(configService: ConfigService): Promise<void> {
        if (!this.dataSource) {
            this.dataSource = new DataSource(getTypeOrmConfig(configService));
            await this.dataSource.initialize();
        }
    }

    getDataSource(): DataSource {
        if (!this.dataSource) {
            throw new Error('Database connection not initialized');
        }
        return this.dataSource;
    }

    async close(): Promise<void> {
        if (this.dataSource) {
            await this.dataSource.destroy();
            this.dataSource = null;
        }
    }
}
```

## Error Handling

### Database Error Handler

```typescript
// src/common/errors/database.error.ts
import { QueryFailedError } from 'typeorm';

export class DatabaseError extends Error {
    constructor(
        public readonly originalError: QueryFailedError,
        public readonly context: string
    ) {
        super(`Database error in ${context}: ${originalError.message}`);
        this.name = 'DatabaseError';
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
}
```

## Testing Configuration

### Test Database Configuration

```typescript
// src/config/test-database.config.ts
import { TypeOrmModuleOptions } from '@nestjs/typeorm';

export const getTestTypeOrmConfig = (): TypeOrmModuleOptions => ({
    type: 'postgres',
    host: 'localhost',
    port: 5432,
    username: 'test',
    password: 'test',
    database: 'ecommerce_test',
    entities: [__dirname + '/../**/*.entity{.ts,.js}'],
    synchronize: true,
    dropSchema: true,
    logging: false,
});
```

## Performance Optimization

### Query Optimization

```typescript
// src/common/optimizations/query.optimization.ts
import { SelectQueryBuilder } from 'typeorm';

export function optimizeProductQuery(queryBuilder: SelectQueryBuilder<any>): void {
    queryBuilder
        .leftJoinAndSelect('product.prices', 'prices')
        .leftJoinAndSelect('product.inventory', 'inventory')
        .cache(true)
        .setQueryRunner(null); // Use connection pool
}

export function optimizeInventoryQuery(queryBuilder: SelectQueryBuilder<any>): void {
    queryBuilder
        .leftJoinAndSelect('inventory.productVariant', 'variant')
        .cache(true)
        .setQueryRunner(null);
}
```

## Security Considerations

### Database Security

1. **Connection Security**
   - Use SSL for database connections
   - Implement connection pooling
   - Set appropriate timeouts
   - Use environment variables for credentials

2. **Query Security**
   - Use parameterized queries
   - Implement input validation
   - Use appropriate access controls
   - Implement audit logging

3. **Data Protection**
   - Encrypt sensitive data
   - Implement row-level security
   - Use appropriate indexes
   - Implement backup strategy

## Monitoring and Logging

### Database Monitoring

```typescript
// src/monitoring/database.monitoring.ts
import { DataSource } from 'typeorm';
import { Logger } from '@nestjs/common';

export class DatabaseMonitoring {
    private readonly logger = new Logger(DatabaseMonitoring.name);

    constructor(private readonly dataSource: DataSource) {
        this.initializeMonitoring();
    }

    private initializeMonitoring(): void {
        this.dataSource.driver.afterConnect().then(() => {
            this.logger.log('Database connection established');
        });

        this.dataSource.driver.beforeDisconnect().then(() => {
            this.logger.log('Database connection closing');
        });
    }

    async getConnectionStats(): Promise<any> {
        const stats = await this.dataSource.query(`
            SELECT * FROM pg_stat_activity 
            WHERE datname = current_database()
        `);
        return stats;
    }
}
```

## References

- [TypeORM Documentation](https://typeorm.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [NestJS Documentation](https://docs.nestjs.com/)
- [Node.js Documentation](https://nodejs.org/docs/) 