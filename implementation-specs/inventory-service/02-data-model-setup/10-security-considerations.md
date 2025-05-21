# Security Considerations for Inventory Service Data Model

## Overview

This document outlines the security considerations, controls, and best practices for the Inventory Service data model. It covers data protection, access control, audit logging, and other security aspects critical for maintaining the integrity and confidentiality of inventory data.

## Data Classification

### Inventory Data Sensitivity

The Inventory Service manages data with the following sensitivity levels:

| Data Category | Classification | Examples | Protection Requirements |
|---------------|---------------|----------|------------------------|
| Inventory Quantities | Business Critical | Current stock levels, Available quantities | Integrity protection, Access controls |
| Warehouse Information | Business Sensitive | Warehouse locations, Addresses, Codes | Access controls, Encryption at rest |
| Supplier Information | Confidential | Supplier contracts, Pricing terms | Strict access controls, Encryption, Audit logging |
| Transaction Records | Business Critical | Stock movements, Adjustments | Immutability, Tamper evidence, Audit logging |
| Customer Reservations | Business Sensitive | Order reservations, Allocation data | Access controls, Encryption, Retention policies |

## Database Security Controls

### 1. Authentication and Authorization

```typescript
// src/config/database-security.config.ts
import { ConfigService } from '@nestjs/config';
import { TypeOrmModuleOptions } from '@nestjs/typeorm';

export const getSecureTypeOrmConfig = (configService: ConfigService): TypeOrmModuleOptions => ({
  type: 'postgres',
  host: configService.get('DB_HOST'),
  port: configService.get('DB_PORT'),
  username: configService.get('DB_USERNAME'),
  password: configService.get('DB_PASSWORD'),
  database: configService.get('DB_DATABASE'),
  // Security-specific configurations
  ssl: {
    rejectUnauthorized: true,
    ca: configService.get('DB_CA_CERT'), // CA certificate for verification
  },
  extra: {
    // Connection timeout to prevent hanging connections
    connectionTimeoutMillis: 5000,
    // Maximum connection lifetime to ensure rotation
    maxLifetimeMillis: 3600000, // 1 hour
  },
  // Prevent accidental schema sync in production
  synchronize: configService.get('NODE_ENV') === 'development' ? 
    configService.get('DB_ALLOW_SYNC') === 'true' : false,
  logging: ['error', 'warn'],
});
```

### 2. RDS Security Groups and Network Isolation

AWS RDS security configuration implemented through Infrastructure as Code:

```yaml
# CloudFormation template for DB security setup
Resources:
  InventoryDBSecurityGroup:
    Type: 'AWS::EC2::SecurityGroup'
    Properties:
      GroupDescription: Security group for Inventory Service database
      VpcId: !Ref VpcId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref InventoryServiceSecurityGroup
      Tags:
        - Key: Name
          Value: inventory-db-sg
        - Key: Service
          Value: inventory-service
```

### 3. Database Encryption

```typescript
// src/config/encryption.config.ts
export interface EncryptionConfig {
  atRest: boolean;
  inTransit: boolean;
  kmsKeyId?: string;
}

export const getDatabaseEncryptionConfig = (): EncryptionConfig => ({
  atRest: process.env.DB_ENCRYPTION_AT_REST === 'true',
  inTransit: process.env.DB_ENCRYPTION_IN_TRANSIT === 'true',
  kmsKeyId: process.env.DB_KMS_KEY_ID,
});
```

## Data Access Security

### 1. Repository Pattern Security

```typescript
// src/inventory/repositories/secure-repository.base.ts
import { Repository, EntityManager } from 'typeorm';
import { Logger } from '@nestjs/common';
import { User } from '../../users/entities/user.entity';

export abstract class SecureRepositoryBase<T> extends Repository<T> {
  protected readonly logger: Logger;
  
  constructor(entityType: new () => T, manager: EntityManager) {
    super(entityType, manager);
    this.logger = new Logger(this.constructor.name);
  }
  
  /**
   * Perform operations with user context for audit
   * @param user The user performing the operation
   * @param operation The database operation to perform
   */
  async executeWithAudit<R>(user: User, operation: (manager: EntityManager) => Promise<R>): Promise<R> {
    const queryRunner = this.manager.connection.createQueryRunner();
    await queryRunner.connect();
    await queryRunner.startTransaction();
    
    try {
      // Set session context with user information for audit
      await queryRunner.query(`
        SET LOCAL "application.user_id" = '${user.id}';
        SET LOCAL "application.user_role" = '${user.role}';
      `);
      
      const result = await operation(queryRunner.manager);
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
  
  /**
   * Check if user has permission for the operation
   * @param user The user to check
   * @param operation The operation being performed
   * @param entityId Optional entity ID if checking for specific entity
   */
  protected async checkPermission(user: User, operation: string, entityId?: string): Promise<boolean> {
    // Implementation depends on authorization system
    // This could check against RBAC, ABAC, or custom permission system
    
    // Example implementation
    const permissions = await this.getPermissionsForUser(user);
    const requiredPermission = entityId ? 
      `inventory:${operation}:${entityId}` : 
      `inventory:${operation}`;
    
    return permissions.includes(requiredPermission) || 
           permissions.includes(`inventory:${operation}:*`) ||
           user.role === 'ADMIN';
  }
  
  private async getPermissionsForUser(user: User): Promise<string[]> {
    // Implementation to fetch user permissions
    // This is a placeholder
    return ['inventory:read:*'];
  }
}
```

### 2. Row-Level Security

```sql
-- SQL for implementing row-level security in PostgreSQL
-- src/migrations/1709123456789-AddRowLevelSecurity.ts

-- Enable Row-Level Security on inventory_items table
ALTER TABLE inventory_items ENABLE ROW LEVEL SECURITY;

-- Create policy for warehouse-specific access
CREATE POLICY warehouse_isolation_policy ON inventory_items
    USING (warehouse_id IN (
        SELECT warehouse_id FROM user_warehouse_access
        WHERE user_id = current_setting('app.current_user_id', true)::uuid
    ));

-- Create policy for inventory managers (can see all warehouses)
CREATE POLICY inventory_manager_policy ON inventory_items
    USING (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_id = current_setting('app.current_user_id', true)::uuid
            AND role = 'INVENTORY_MANAGER'
        )
    );
```

### 3. Sensitive Data Protection

```typescript
// src/inventory/entities/warehouse.entity.ts
import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';
import { Exclude, Expose } from 'class-transformer';

@Entity('warehouses')
export class Warehouse {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  @Column()
  code: string;

  @Column()
  address: string;

  @Column()
  city: string;

  @Column()
  state: string;

  @Column()
  zipCode: string;

  @Column()
  country: string;

  // Sensitive information excluded from default serialization
  @Exclude()
  @Column({ nullable: true })
  securityCode: string;

  @Exclude()
  @Column({ type: 'jsonb', nullable: true })
  securityDetails: any;

  @Exclude()
  @Column({ nullable: true })
  accessInstructions: string;

  // Only expose for authorized users
  @Expose({ groups: ['admin', 'warehouse-manager'] })
  getSecurityDetails(): any {
    return this.securityDetails;
  }
}
```

## Audit and Compliance

### 1. Audit Logging

```typescript
// src/audit/services/audit-log.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AuditLog } from '../entities/audit-log.entity';
import { User } from '../../users/entities/user.entity';

export enum AuditAction {
  CREATE = 'CREATE',
  READ = 'READ',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
  RESERVE = 'RESERVE',
  RELEASE = 'RELEASE',
  ADJUST = 'ADJUST',
}

@Injectable()
export class AuditLogService {
  private readonly logger = new Logger(AuditLogService.name);

  constructor(
    @InjectRepository(AuditLog)
    private auditLogRepository: Repository<AuditLog>,
  ) {}

  async logAction(
    user: User,
    action: AuditAction,
    entityType: string,
    entityId: string,
    details: any,
  ): Promise<void> {
    try {
      const auditLog = new AuditLog();
      auditLog.userId = user.id;
      auditLog.username = user.username;
      auditLog.userIp = user.lastIpAddress;
      auditLog.action = action;
      auditLog.entityType = entityType;
      auditLog.entityId = entityId;
      auditLog.timestamp = new Date();
      auditLog.details = details;

      await this.auditLogRepository.save(auditLog);
    } catch (error) {
      // Log error but don't fail the operation due to audit log failure
      this.logger.error(`Failed to create audit log: ${error.message}`, error.stack);
      // Consider implementing a fallback mechanism for critical audit events
    }
  }

  async findAuditLogsForEntity(
    entityType: string,
    entityId: string,
    startDate?: Date,
    endDate?: Date,
  ): Promise<AuditLog[]> {
    const queryBuilder = this.auditLogRepository.createQueryBuilder('audit')
      .where('audit.entityType = :entityType', { entityType })
      .andWhere('audit.entityId = :entityId', { entityId })
      .orderBy('audit.timestamp', 'DESC');

    if (startDate) {
      queryBuilder.andWhere('audit.timestamp >= :startDate', { startDate });
    }

    if (endDate) {
      queryBuilder.andWhere('audit.timestamp <= :endDate', { endDate });
    }

    return queryBuilder.getMany();
  }
}
```

### 2. Database Audit Implementation

```sql
-- SQL for implementing audit triggers in PostgreSQL
-- src/migrations/1709123456790-AddAuditTriggers.ts

-- Create the audit log tables
CREATE TABLE IF NOT EXISTS inventory_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    changed_by TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    old_data JSONB,
    new_data JSONB
);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION inventory_audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    audit_row inventory_audit_log;
    user_id TEXT;
BEGIN
    -- Try to get user_id from session context, fall back to current_user
    BEGIN
        user_id := current_setting('application.user_id');
    EXCEPTION WHEN OTHERS THEN
        user_id := current_user;
    END;
    
    audit_row = ROW(
        gen_random_uuid(),
        TG_TABLE_NAME,
        TG_OP,
        user_id,
        CURRENT_TIMESTAMP,
        NULL,
        NULL
    );
    
    IF (TG_OP = 'UPDATE') THEN
        audit_row.old_data = to_jsonb(OLD);
        audit_row.new_data = to_jsonb(NEW);
        INSERT INTO inventory_audit_log VALUES (audit_row.*);
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        audit_row.old_data = to_jsonb(OLD);
        INSERT INTO inventory_audit_log VALUES (audit_row.*);
        RETURN OLD;
    ELSIF (TG_OP = 'INSERT') THEN
        audit_row.new_data = to_jsonb(NEW);
        INSERT INTO inventory_audit_log VALUES (audit_row.*);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to inventory tables
CREATE TRIGGER inventory_item_audit
AFTER INSERT OR UPDATE OR DELETE ON inventory_items
FOR EACH ROW EXECUTE FUNCTION inventory_audit_trigger_func();

CREATE TRIGGER warehouse_audit
AFTER INSERT OR UPDATE OR DELETE ON warehouses
FOR EACH ROW EXECUTE FUNCTION inventory_audit_trigger_func();

CREATE TRIGGER stock_transaction_audit
AFTER INSERT OR UPDATE OR DELETE ON stock_transactions
FOR EACH ROW EXECUTE FUNCTION inventory_audit_trigger_func();
```

### 3. Event Sourcing Audit Trail

The event sourcing system in DynamoDB provides an inherent audit trail:

```typescript
// src/event-sourcing/audit-trail.service.ts
import { Injectable } from '@nestjs/common';
import { DynamoDBEventRepository } from './dynamodb-event.repository';
import { User } from '../users/entities/user.entity';

@Injectable()
export class EventAuditTrailService {
  constructor(private eventRepository: DynamoDBEventRepository) {}
  
  async getAuditTrail(
    aggregateId: string,
    startDate?: Date,
    endDate?: Date,
  ): Promise<any[]> {
    // Fetch all events for the aggregate
    const events = await this.eventRepository.getEvents(aggregateId);
    
    // Filter by date range if specified
    let filteredEvents = events;
    if (startDate || endDate) {
      filteredEvents = events.filter(event => {
        const eventDate = new Date(event.timestamp);
        if (startDate && eventDate < startDate) return false;
        if (endDate && eventDate > endDate) return false;
        return true;
      });
    }
    
    // Transform events into audit format
    return filteredEvents.map(event => ({
      timestamp: event.timestamp,
      eventType: event.eventType,
      userId: event.metadata?.userId,
      username: event.metadata?.username,
      changes: event.data,
      metadata: event.metadata
    }));
  }
  
  async addUserContextToEvent(event: any, user: User): Promise<any> {
    if (!event.metadata) {
      event.metadata = {};
    }
    
    event.metadata.userId = user.id;
    event.metadata.username = user.username;
    event.metadata.userIp = user.lastIpAddress;
    event.metadata.userRole = user.role;
    
    return event;
  }
}
```

## Vulnerability Mitigation

### 1. SQL Injection Prevention

```typescript
// src/common/security/query-sanitizer.ts
import { BadRequestException } from '@nestjs/common';

export class QuerySanitizer {
  /**
   * Sanitize input to prevent SQL injection
   * @param input String input to sanitize
   */
  static sanitizeInput(input: string): string {
    if (!input) return input;
    
    // Remove SQL comment sequences
    let sanitized = input.replace(/\/\*.*?\*\/|--.*?$/gm, '');
    
    // Remove SQL keywords that could be used for injection
    const sqlKeywords = [
      'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 
      'ALTER', 'CREATE', 'TRUNCATE', 'UNION'
    ];
    
    const regex = new RegExp(`\\b(${sqlKeywords.join('|')})\\b`, 'gi');
    sanitized = sanitized.replace(regex, '');
    
    return sanitized;
  }
  
  /**
   * Validate that the sort column is allowed
   * @param column Column name to check
   * @param allowedColumns List of allowed column names
   */
  static validateSortColumn(column: string, allowedColumns: string[]): string {
    const sanitized = this.sanitizeInput(column);
    
    if (!allowedColumns.includes(sanitized)) {
      throw new BadRequestException(`Sort column not allowed: ${column}`);
    }
    
    return sanitized;
  }
  
  /**
   * Sanitize and validate a database identifier
   * @param identifier Database identifier to check
   */
  static sanitizeIdentifier(identifier: string): string {
    if (!identifier) return identifier;
    
    // Allow only alphanumeric, underscore and dot
    if (!/^[a-zA-Z0-9_.]+$/.test(identifier)) {
      throw new BadRequestException(`Invalid identifier: ${identifier}`);
    }
    
    return identifier;
  }
}
```

### 2. JSON Injection Protection

```typescript
// src/common/security/json-validator.ts
import { BadRequestException } from '@nestjs/common';
import * as Ajv from 'ajv';

export class JsonValidator {
  private static ajv = new Ajv({ allErrors: true });
  
  /**
   * Validate JSON against a schema to prevent injection
   * @param json JSON data to validate
   * @param schema JSON schema for validation
   */
  static validate(json: any, schema: object): boolean {
    const validate = this.ajv.compile(schema);
    const valid = validate(json);
    
    if (!valid) {
      const errors = validate.errors.map(e => 
        `${e.dataPath} ${e.message}`
      ).join(', ');
      
      throw new BadRequestException(`Invalid data: ${errors}`);
    }
    
    return true;
  }
  
  /**
   * Sanitize JSON to remove potential script injection
   * @param json JSON object to sanitize
   */
  static sanitizeJson(json: any): any {
    if (!json) return json;
    
    if (typeof json === 'string') {
      // Handle string case
      return this.sanitizeJsonString(json);
    }
    
    // Recursively sanitize object properties
    if (typeof json === 'object' && json !== null) {
      const sanitized = Array.isArray(json) ? [] : {};
      
      for (const key in json) {
        if (Object.prototype.hasOwnProperty.call(json, key)) {
          sanitized[key] = this.sanitizeJson(json[key]);
        }
      }
      
      return sanitized;
    }
    
    return json;
  }
  
  private static sanitizeJsonString(str: string): string {
    // Remove potential XSS vectors
    return str
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+=/gi, '');
  }
}
```

## AWS-Specific Security Features

### 1. DynamoDB Encryption

```typescript
// src/config/dynamodb-security.config.ts
import * as AWS from 'aws-sdk';
import { ConfigService } from '@nestjs/config';

export const getSecureDynamoDBConfig = (configService: ConfigService): AWS.DynamoDB.ClientConfiguration => {
  const config: AWS.DynamoDB.ClientConfiguration = {
    region: configService.get('AWS_REGION') || 'us-east-1',
    maxRetries: 3,
    httpOptions: {
      timeout: 5000
    }
  };
  
  // Use IAM authentication in production
  if (configService.get('NODE_ENV') === 'production') {
    // No need to set credentials explicitly, use IAM role
  } else {
    // For local development
    config.accessKeyId = configService.get('AWS_ACCESS_KEY_ID');
    config.secretAccessKey = configService.get('AWS_SECRET_ACCESS_KEY');
    config.endpoint = configService.get('DYNAMODB_ENDPOINT');
  }
  
  return config;
};

export const getDynamoDBEncryptionSettings = (configService: ConfigService): any => {
  return {
    enabled: configService.get('DYNAMODB_ENCRYPTION_ENABLED') === 'true',
    keyId: configService.get('DYNAMODB_KMS_KEY_ID')
  };
};
```

### 2. AWS Secrets Manager Integration

```typescript
// src/config/secrets-manager.ts
import * as AWS from 'aws-sdk';
import { Logger } from '@nestjs/common';

export class SecretsManager {
  private static instance: SecretsManager;
  private secretsManager: AWS.SecretsManager;
  private cache: Map<string, any> = new Map();
  private readonly logger = new Logger(SecretsManager.name);
  
  private constructor() {
    this.secretsManager = new AWS.SecretsManager({
      region: process.env.AWS_REGION || 'us-east-1'
    });
  }
  
  public static getInstance(): SecretsManager {
    if (!SecretsManager.instance) {
      SecretsManager.instance = new SecretsManager();
    }
    return SecretsManager.instance;
  }
  
  async getSecret(secretId: string, useCache: boolean = true): Promise<any> {
    if (useCache && this.cache.has(secretId)) {
      return this.cache.get(secretId);
    }
    
    try {
      const data = await this.secretsManager.getSecretValue({ SecretId: secretId }).promise();
      let secret;
      
      if (data.SecretString) {
        secret = JSON.parse(data.SecretString);
      } else {
        // Handle binary secret
        const buff = Buffer.from(data.SecretBinary.toString(), 'base64');
        secret = JSON.parse(buff.toString('ascii'));
      }
      
      if (useCache) {
        this.cache.set(secretId, secret);
      }
      
      return secret;
    } catch (error) {
      this.logger.error(`Failed to retrieve secret ${secretId}: ${error.message}`);
      throw error;
    }
  }
  
  clearCache(): void {
    this.cache.clear();
  }
}
```

## Security Best Practices

### 1. Data Validation

```typescript
// src/inventory/dto/validate-inventory-input.ts
import { Injectable } from '@nestjs/common';
import { plainToClass } from 'class-transformer';
import { validate, ValidationError } from 'class-validator';
import { CreateInventoryItemDto } from './create-inventory-item.dto';
import { UpdateInventoryItemDto } from './update-inventory-item.dto';

@Injectable()
export class InventoryValidator {
  async validateCreateDto(data: any): Promise<[CreateInventoryItemDto, ValidationError[]]> {
    const dto = plainToClass(CreateInventoryItemDto, data);
    const errors = await validate(dto);
    return [dto, errors];
  }
  
  async validateUpdateDto(data: any): Promise<[UpdateInventoryItemDto, ValidationError[]]> {
    const dto = plainToClass(UpdateInventoryItemDto, data);
    const errors = await validate(dto, { skipMissingProperties: true });
    return [dto, errors];
  }
  
  validateQuantity(quantity: number): boolean {
    return quantity >= 0 && Number.isInteger(quantity);
  }
  
  validateSku(sku: string): boolean {
    // SKU format validation: alphanumeric with optional hyphens
    return /^[A-Za-z0-9-]+$/.test(sku);
  }
  
  validateWarehouseCode(code: string): boolean {
    // Warehouse code format validation
    return /^[A-Z]{2}-[A-Z0-9]{3}$/.test(code);
  }
}
```

### 2. Least Privilege Database Users

```sql
-- SQL for setting up least privilege database users
-- src/migrations/1709123456791-SetupDbRoles.ts

-- Create application roles
CREATE ROLE inventory_app_read WITH LOGIN PASSWORD 'password_here';
CREATE ROLE inventory_app_write WITH LOGIN PASSWORD 'password_here';
CREATE ROLE inventory_app_admin WITH LOGIN PASSWORD 'password_here';

-- Grant appropriate permissions to roles
GRANT CONNECT ON DATABASE inventory_service TO inventory_app_read;
GRANT USAGE ON SCHEMA public TO inventory_app_read;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO inventory_app_read;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO inventory_app_read;

-- For the write role, inherit read permissions and add write
GRANT inventory_app_read TO inventory_app_write;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO inventory_app_write;

-- Admin role gets all permissions
GRANT inventory_app_write TO inventory_app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO inventory_app_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO inventory_app_admin;
```

## References

- [OWASP Database Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Database_Security_Cheat_Sheet.html)
- [AWS Security Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.Security.html)
- [PostgreSQL Security Documentation](https://www.postgresql.org/docs/current/security.html)
- [DynamoDB Encryption Client](https://docs.aws.amazon.com/dynamodb-encryption-client/latest/devguide/what-is-ddb-encrypt.html)
- [NestJS Security Best Practices](https://docs.nestjs.com/techniques/security)
- [Event Sourcing Security Patterns](https://www.eventstore.com/blog/security-in-event-sourcing)