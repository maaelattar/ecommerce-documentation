# 02. Data Models & Financial Entities

## Overview

This section focuses on designing secure, compliant data models for financial transactions. We'll implement entities that support PCI compliance through tokenization, maintain ACID properties for financial integrity, and provide comprehensive audit trails.

## 🎯 Learning Objectives

- Design payment and transaction entities with financial integrity
- Implement tokenization patterns for PCI compliance
- Create audit trails for regulatory compliance
- Set up database constraints for data consistency
- Build refund and chargeback models

---

## Step 1: Database Configuration

### 1.1 TypeORM Configuration

```typescript
// src/database/database.config.ts
import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { ConfigService } from '@nestjs/config';

export const createTypeOrmConfig = (
  configService: ConfigService,
): TypeOrmModuleOptions => ({
  type: 'postgres',
  host: configService.get('database.host'),
  port: configService.get('database.port'),
  username: configService.get('database.username'),
  password: configService.get('database.password'),
  database: configService.get('database.database'),
  ssl: configService.get('database.ssl'),
  entities: [__dirname + '/../**/*.entity{.ts,.js}'],
  migrations: [__dirname + '/migrations/*{.ts,.js}'],
  synchronize: configService.get('database.synchronize'),
  logging: configService.get('database.logging'),
  extra: {
    max: configService.get('database.maxConnections'),
    connectionTimeoutMillis: configService.get('database.acquireTimeout'),
    idleTimeoutMillis: configService.get('database.timeout'),
  },
});
```