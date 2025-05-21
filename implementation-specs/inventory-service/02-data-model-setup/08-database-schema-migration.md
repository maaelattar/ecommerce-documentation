# Database Schema Migration for Inventory Service

## Overview

This document outlines the database schema migration strategy specifically for the Inventory Service, which uses a dual-database approach with PostgreSQL for operational data and DynamoDB for event sourcing. This migration strategy ensures reliable schema evolution while maintaining system availability and data integrity.

## Dual-Database Migration Considerations

### PostgreSQL Migrations (Operational Data)

PostgreSQL migrations will follow standard relational database practices with AWS-specific optimizations:

```typescript
// src/config/typeorm-migration.config.ts
import { ConfigService } from '@nestjs/config';
import { TypeOrmModuleOptions } from '@nestjs/typeorm';

export const getMigrationConfig = (configService: ConfigService): TypeOrmModuleOptions => ({
  type: 'postgres',
  host: configService.get('DB_HOST'),
  port: configService.get('DB_PORT'),
  username: configService.get('DB_USERNAME'),
  password: configService.get('DB_PASSWORD'),
  database: configService.get('DB_DATABASE'),
  entities: [__dirname + '/../**/*.entity{.ts,.js}'],
  migrations: [__dirname + '/../migrations/postgres/**/*{.ts,.js}'],
  migrationsTableName: 'migrations',
  migrationsRun: false,
  logging: true,
  maxQueryExecutionTime: 10000,
});
```

### DynamoDB Migrations (Event Store)

For DynamoDB, which is schemaless but requires careful handling of table structure and indexes:

```typescript
// src/migrations/dynamodb/migration-registry.ts
import * as AWS from 'aws-sdk';
import { Logger } from '@nestjs/common';

export interface DynamoDBMigration {
  id: string;
  description: string;
  up: (dynamoDb: AWS.DynamoDB) => Promise<void>;
  down: (dynamoDb: AWS.DynamoDB) => Promise<void>;
}

export class DynamoDBMigrationRegistry {
  private readonly logger = new Logger(DynamoDBMigrationRegistry.name);
  private readonly dynamoDb: AWS.DynamoDB;
  private readonly documentClient: AWS.DynamoDB.DocumentClient;
  private readonly migrationsTableName: string;
  
  constructor(
    region: string = process.env.AWS_REGION || 'us-east-1',
    migrationsTableName: string = 'inventory_dynamodb_migrations'
  ) {
    this.dynamoDb = new AWS.DynamoDB({ region });
    this.documentClient = new AWS.DynamoDB.DocumentClient({ service: this.dynamoDb });
    this.migrationsTableName = migrationsTableName;
  }
  
  async initialize(): Promise<void> {
    try {
      await this.dynamoDb.describeTable({ TableName: this.migrationsTableName }).promise();
      this.logger.log(`DynamoDB migrations table ${this.migrationsTableName} exists`);
    } catch (error) {
      if (error.code === 'ResourceNotFoundException') {
        this.logger.log(`Creating DynamoDB migrations table ${this.migrationsTableName}`);
        await this.dynamoDb.createTable({
          TableName: this.migrationsTableName,
          KeySchema: [
            { AttributeName: 'id', KeyType: 'HASH' }
          ],
          AttributeDefinitions: [
            { AttributeName: 'id', AttributeType: 'S' }
          ],
          BillingMode: 'PAY_PER_REQUEST'
        }).promise();
        
        await this.dynamoDb.waitFor('tableExists', {
          TableName: this.migrationsTableName
        }).promise();
        
        this.logger.log(`DynamoDB migrations table created successfully`);
      } else {
        throw error;
      }
    }
  }
  
  async getAppliedMigrations(): Promise<string[]> {
    const result = await this.documentClient.scan({
      TableName: this.migrationsTableName,
      ProjectionExpression: 'id'
    }).promise();
    
    return (result.Items || []).map(item => item.id);
  }
  
  async applyMigration(migration: DynamoDBMigration): Promise<void> {
    this.logger.log(`Applying DynamoDB migration: ${migration.id} - ${migration.description}`);
    
    await migration.up(this.dynamoDb);
    
    await this.documentClient.put({
      TableName: this.migrationsTableName,
      Item: {
        id: migration.id,
        description: migration.description,
        appliedAt: new Date().toISOString()
      }
    }).promise();
    
    this.logger.log(`Migration ${migration.id} applied successfully`);
  }
  
  async revertMigration(migration: DynamoDBMigration): Promise<void> {
    this.logger.log(`Reverting DynamoDB migration: ${migration.id} - ${migration.description}`);
    
    await migration.down(this.dynamoDb);
    
    await this.documentClient.delete({
      TableName: this.migrationsTableName,
      Key: { id: migration.id }
    }).promise();
    
    this.logger.log(`Migration ${migration.id} reverted successfully`);
  }
}
```

### Example DynamoDB Migration

```typescript
// src/migrations/dynamodb/1709123456789-CreateInventoryEventsTable.ts
import { DynamoDBMigration } from './migration-registry';
import * as AWS from 'aws-sdk';

export const CreateInventoryEventsTable: DynamoDBMigration = {
  id: '1709123456789-CreateInventoryEventsTable',
  description: 'Create the inventory_events table for event sourcing',
  
  async up(dynamoDb: AWS.DynamoDB): Promise<void> {
    await dynamoDb.createTable({
      TableName: 'inventory_events',
      KeySchema: [
        { AttributeName: 'inventoryItemId', KeyType: 'HASH' },
        { AttributeName: 'sequenceNumber', KeyType: 'RANGE' }
      ],
      AttributeDefinitions: [
        { AttributeName: 'inventoryItemId', AttributeType: 'S' },
        { AttributeName: 'sequenceNumber', AttributeType: 'N' },
        { AttributeName: 'eventType', AttributeType: 'S' },
        { AttributeName: 'timestamp', AttributeType: 'S' }
      ],
      GlobalSecondaryIndexes: [
        {
          IndexName: 'EventTypeIndex',
          KeySchema: [
            { AttributeName: 'eventType', KeyType: 'HASH' },
            { AttributeName: 'timestamp', KeyType: 'RANGE' }
          ],
          Projection: {
            ProjectionType: 'ALL'
          },
          BillingMode: 'PAY_PER_REQUEST'
        }
      ],
      BillingMode: 'PAY_PER_REQUEST',
      StreamSpecification: {
        StreamEnabled: true,
        StreamViewType: 'NEW_AND_OLD_IMAGES'
      }
    }).promise();
  },
  
  async down(dynamoDb: AWS.DynamoDB): Promise<void> {
    await dynamoDb.deleteTable({
      TableName: 'inventory_events'
    }).promise();
  }
};
```

## Coordinated Migration Approach

For the Inventory Service with dual databases, we need a coordinated migration approach:

```typescript
// src/scripts/run-migrations.ts
import { TypeOrmMigrationRunner } from './typeorm-migration-runner';
import { DynamoDBMigrationRegistry, allDynamoDBMigrations } from '../migrations/dynamodb';
import { ConfigService } from '@nestjs/config';
import { Logger } from '@nestjs/common';

class MigrationCoordinator {
  private readonly logger = new Logger(MigrationCoordinator.name);
  private readonly typeOrmRunner: TypeOrmMigrationRunner;
  private readonly dynamoDbRegistry: DynamoDBMigrationRegistry;
  
  constructor(configService: ConfigService) {
    this.typeOrmRunner = new TypeOrmMigrationRunner(configService);
    this.dynamoDbRegistry = new DynamoDBMigrationRegistry();
  }
  
  async initialize(): Promise<void> {
    await this.dynamoDbRegistry.initialize();
  }
  
  async runMigrations(): Promise<void> {
    this.logger.log('Starting coordinated database migrations');
    
    // Create a database snapshot before migration
    await this.createRdsSnapshot();
    
    try {
      // 1. Run PostgreSQL migrations first
      this.logger.log('Running PostgreSQL migrations');
      await this.typeOrmRunner.runMigrations();
      
      // 2. Run DynamoDB migrations
      this.logger.log('Running DynamoDB migrations');
      const appliedMigrations = await this.dynamoDbRegistry.getAppliedMigrations();
      
      for (const migration of allDynamoDBMigrations) {
        if (!appliedMigrations.includes(migration.id)) {
          await this.dynamoDbRegistry.applyMigration(migration);
        }
      }
      
      this.logger.log('All migrations completed successfully');
      
    } catch (error) {
      this.logger.error(`Migration failed: ${error.message}`, error.stack);
      
      // Notify about failure
      await this.sendFailureNotification(error);
      
      throw error;
    }
  }
  
  private async createRdsSnapshot(): Promise<string> {
    const AWS = require('aws-sdk');
    const rds = new AWS.RDS({ region: process.env.AWS_REGION });
    
    const dbInstanceId = process.env.DB_INSTANCE_ID;
    const snapshotId = `pre-migration-${dbInstanceId}-${Date.now()}`;
    
    try {
      this.logger.log(`Creating RDS snapshot: ${snapshotId}`);
      await rds.createDBSnapshot({
        DBInstanceIdentifier: dbInstanceId,
        DBSnapshotIdentifier: snapshotId
      }).promise();
      
      this.logger.log(`Waiting for snapshot to complete...`);
      await rds.waitFor('dbSnapshotAvailable', {
        DBSnapshotIdentifier: snapshotId
      }).promise();
      
      this.logger.log(`Snapshot ${snapshotId} created successfully`);
      return snapshotId;
      
    } catch (error) {
      this.logger.error(`Failed to create snapshot: ${error.message}`);
      throw error;
    }
  }
  
  private async sendFailureNotification(error: Error): Promise<void> {
    const AWS = require('aws-sdk');
    const sns = new AWS.SNS({ region: process.env.AWS_REGION });
    
    try {
      await sns.publish({
        TopicArn: process.env.NOTIFICATION_TOPIC_ARN,
        Subject: 'Inventory Service Migration Failed',
        Message: `
          Migration failed at ${new Date().toISOString()}
          Error: ${error.message}
          
          Please check the logs and take appropriate action.
        `
      }).promise();
    } catch (snsError) {
      this.logger.error(`Failed to send notification: ${snsError.message}`);
    }
  }
}

// Execute migrations
async function main() {
  const configService = new ConfigService();
  const coordinator = new MigrationCoordinator(configService);
  
  await coordinator.initialize();
  await coordinator.runMigrations();
}

main().catch(error => {
  console.error('Migration script failed:', error);
  process.exit(1);
});
```

## CI/CD Integration for Dual Database Migrations

### CodeBuild Buildspec

```yaml
# buildspec-inventory-migration.yml
version: 0.2

phases:
  install:
    runtime-versions:
      nodejs: 18
    commands:
      - npm install -g typescript ts-node
      - npm ci
      
  pre_build:
    commands:
      - echo "Retrieving database credentials from Secrets Manager"
      - export POSTGRES_CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id ${POSTGRES_SECRET_ARN} --query SecretString --output text)
      - export DB_HOST=$(echo $POSTGRES_CREDENTIALS | jq -r '.host')
      - export DB_PORT=$(echo $POSTGRES_CREDENTIALS | jq -r '.port')
      - export DB_USERNAME=$(echo $POSTGRES_CREDENTIALS | jq -r '.username')
      - export DB_PASSWORD=$(echo $POSTGRES_CREDENTIALS | jq -r '.password')
      - export DB_DATABASE=$(echo $POSTGRES_CREDENTIALS | jq -r '.dbname')
      - export DB_SSL=true
      - export DB_INSTANCE_ID=$(echo $POSTGRES_CREDENTIALS | jq -r '.dbInstanceIdentifier')
      
  build:
    commands:
      - echo "Running database migrations"
      - npm run migrations
      
  post_build:
    commands:
      - if [ $CODEBUILD_BUILD_SUCCEEDING -eq 1 ]; then
          echo "Migrations completed successfully";
          aws cloudwatch put-metric-data --namespace "InventoryService/Migrations" --metric-name "SuccessfulMigration" --value 1;
        else
          echo "Migrations failed";
          aws cloudwatch put-metric-data --namespace "InventoryService/Migrations" --metric-name "FailedMigration" --value 1;
          exit 1;
        fi

artifacts:
  files:
    - migration-report.json
  discard-paths: yes
```

## Event Sourcing Migration Strategies

The Inventory Service uses event sourcing, which requires special migration considerations:

### Event Schema Evolution

```typescript
// src/event-sourcing/event-schema-registry.ts
import { Logger } from '@nestjs/common';
import * as AWS from 'aws-sdk';

interface EventSchemaVersion {
  version: number;
  eventType: string;
  schemaDefinition: object;
  migrationFunction?: (oldEvent: any) => any;
}

export class EventSchemaRegistry {
  private readonly logger = new Logger(EventSchemaRegistry.name);
  private readonly schemas: Map<string, EventSchemaVersion[]> = new Map();
  private readonly dynamoDB: AWS.DynamoDB.DocumentClient;
  
  constructor(region: string = process.env.AWS_REGION || 'us-east-1') {
    this.dynamoDB = new AWS.DynamoDB.DocumentClient({ region });
  }
  
  registerSchema(eventType: string, version: number, schemaDefinition: object, migrationFunction?: (oldEvent: any) => any): void {
    if (!this.schemas.has(eventType)) {
      this.schemas.set(eventType, []);
    }
    
    const versions = this.schemas.get(eventType);
    versions.push({ version, eventType, schemaDefinition, migrationFunction });
    versions.sort((a, b) => a.version - b.version);
    
    this.logger.log(`Registered schema version ${version} for event type ${eventType}`);
  }
  
  getLatestSchema(eventType: string): EventSchemaVersion {
    const versions = this.schemas.get(eventType) || [];
    if (versions.length === 0) {
      throw new Error(`No schema found for event type ${eventType}`);
    }
    
    return versions[versions.length - 1];
  }
  
  getSchemaVersion(eventType: string, version: number): EventSchemaVersion {
    const versions = this.schemas.get(eventType) || [];
    const schema = versions.find(s => s.version === version);
    
    if (!schema) {
      throw new Error(`Schema version ${version} not found for event type ${eventType}`);
    }
    
    return schema;
  }
  
  async migrateEvent(event: any): Promise<any> {
    const eventType = event.eventType;
    const eventVersion = event.eventVersion || 1;
    const latestVersion = this.getLatestSchema(eventType).version;
    
    if (eventVersion === latestVersion) {
      return event;
    }
    
    let migratedEvent = { ...event };
    
    for (let version = eventVersion; version < latestVersion; version++) {
      const nextVersion = version + 1;
      const schema = this.getSchemaVersion(eventType, nextVersion);
      
      if (schema.migrationFunction) {
        migratedEvent = schema.migrationFunction(migratedEvent);
        migratedEvent.eventVersion = nextVersion;
      }
    }
    
    return migratedEvent;
  }
  
  async migrateEventStream(inventoryItemId: string): Promise<void> {
    this.logger.log(`Migrating event stream for inventory item ${inventoryItemId}`);
    
    let lastEvaluatedKey;
    
    do {
      const params: AWS.DynamoDB.DocumentClient.QueryInput = {
        TableName: 'inventory_events',
        KeyConditionExpression: 'inventoryItemId = :id',
        ExpressionAttributeValues: {
          ':id': inventoryItemId
        },
        ExclusiveStartKey: lastEvaluatedKey
      };
      
      const result = await this.dynamoDB.query(params).promise();
      lastEvaluatedKey = result.LastEvaluatedKey;
      
      for (const event of result.Items) {
        const migratedEvent = await this.migrateEvent(event);
        
        if (migratedEvent !== event) {
          await this.dynamoDB.put({
            TableName: 'inventory_events',
            Item: migratedEvent
          }).promise();
          
          this.logger.log(`Migrated event ${event.sequenceNumber} for item ${inventoryItemId} from version ${event.eventVersion} to ${migratedEvent.eventVersion}`);
        }
      }
      
    } while (lastEvaluatedKey);
    
    this.logger.log(`Completed migration for inventory item ${inventoryItemId}`);
  }
}

// Example usage
const eventSchemaRegistry = new EventSchemaRegistry();

// Register schema versions
eventSchemaRegistry.registerSchema('InventoryItemCreated', 1, {
  // V1 schema
});

eventSchemaRegistry.registerSchema('InventoryItemCreated', 2, {
  // V2 schema with additional fields
}, (oldEvent) => {
  // Migration function to upgrade from V1 to V2
  return {
    ...oldEvent,
    warehouseId: oldEvent.warehouseId || 'default',
    createdBy: oldEvent.createdBy || 'system'
  };
});
```

## Database Schema Synchronization

For the Inventory Service with dual databases, keeping schemas in sync is important:

```typescript
// src/scripts/verify-schema-consistency.ts
import { DataSource } from 'typeorm';
import * as AWS from 'aws-sdk';
import { Logger } from '@nestjs/common';
import { getTypeOrmConfig } from '../config/typeorm.config';
import { ConfigService } from '@nestjs/config';

class SchemaConsistencyVerifier {
  private readonly logger = new Logger(SchemaConsistencyVerifier.name);
  private readonly dynamoDB: AWS.DynamoDB;
  private readonly dataSource: DataSource;
  
  constructor(configService: ConfigService) {
    this.dynamoDB = new AWS.DynamoDB({ region: process.env.AWS_REGION || 'us-east-1' });
    this.dataSource = new DataSource(getTypeOrmConfig(configService));
  }
  
  async verifyConsistency(): Promise<void> {
    await this.dataSource.initialize();
    
    try {
      // 1. Verify PostgreSQL schema
      this.logger.log('Verifying PostgreSQL schema');
      const pgSchemaValid = await this.verifyPostgresSchema();
      
      // 2. Verify DynamoDB tables
      this.logger.log('Verifying DynamoDB tables');
      const dynamoTablesValid = await this.verifyDynamoDBTables();
      
      // 3. Verify event schema registry
      this.logger.log('Verifying event schema registry');
      const eventSchemaValid = await this.verifyEventSchemaRegistry();
      
      if (pgSchemaValid && dynamoTablesValid && eventSchemaValid) {
        this.logger.log('Schema consistency verification passed');
      } else {
        throw new Error('Schema consistency verification failed');
      }
      
    } finally {
      await this.dataSource.destroy();
    }
  }
  
  private async verifyPostgresSchema(): Promise<boolean> {
    try {
      // Check if all expected tables exist
      const tables = await this.dataSource.query(`
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
      `);
      
      const requiredTables = [
        'inventory_items',
        'warehouses',
        'inventory_reservations',
        'stock_transactions',
        'inventory_snapshots'
      ];
      
      const missingTables = requiredTables.filter(
        table => !tables.some(t => t.table_name === table)
      );
      
      if (missingTables.length > 0) {
        this.logger.error(`Missing tables: ${missingTables.join(', ')}`);
        return false;
      }
      
      // Additional checks as needed
      
      return true;
    } catch (error) {
      this.logger.error(`PostgreSQL schema verification failed: ${error.message}`);
      return false;
    }
  }
  
  private async verifyDynamoDBTables(): Promise<boolean> {
    try {
      const requiredTables = ['inventory_events'];
      
      for (const tableName of requiredTables) {
        try {
          await this.dynamoDB.describeTable({ TableName: tableName }).promise();
        } catch (error) {
          if (error.code === 'ResourceNotFoundException') {
            this.logger.error(`DynamoDB table ${tableName} does not exist`);
            return false;
          }
          throw error;
        }
      }
      
      return true;
    } catch (error) {
      this.logger.error(`DynamoDB table verification failed: ${error.message}`);
      return false;
    }
  }
  
  private async verifyEventSchemaRegistry(): Promise<boolean> {
    // Implementation to verify event schema registry
    // This would check that all required event types and versions are registered
    return true;
  }
}

// Execute verification
async function main() {
  const configService = new ConfigService();
  const verifier = new SchemaConsistencyVerifier(configService);
  
  try {
    await verifier.verifyConsistency();
    console.log('Schema consistency verification completed successfully');
    process.exit(0);
  } catch (error) {
    console.error('Schema consistency verification failed:', error);
    process.exit(1);
  }
}

main().catch(console.error);
```

## AWS-Specific Monitoring for Migrations

```typescript
// src/monitoring/migration-monitoring.ts
import * as AWS from 'aws-sdk';
import { Logger } from '@nestjs/common';

export class MigrationMonitoring {
  private readonly logger = new Logger(MigrationMonitoring.name);
  private readonly cloudwatch: AWS.CloudWatch;
  private readonly sns: AWS.SNS;
  
  constructor(
    region: string = process.env.AWS_REGION || 'us-east-1',
    private readonly notificationTopicArn: string = process.env.NOTIFICATION_TOPIC_ARN
  ) {
    this.cloudwatch = new AWS.CloudWatch({ region });
    this.sns = new AWS.SNS({ region });
  }
  
  async recordMigrationStart(migrationId: string, environment: string): Promise<void> {
    await this.publishMetric('MigrationStarted', 1, migrationId, environment);
    await this.publishNotification(
      'Database Migration Started',
      `Migration ${migrationId} started in ${environment} at ${new Date().toISOString()}`
    );
  }
  
  async recordMigrationCompletion(
    migrationId: string,
    environment: string,
    success: boolean,
    durationMs: number
  ): Promise<void> {
    await this.publishMetric(
      success ? 'MigrationSucceeded' : 'MigrationFailed',
      1,
      migrationId,
      environment
    );
    
    await this.publishMetric(
      'MigrationDuration',
      durationMs,
      migrationId,
      environment
    );
    
    const subject = success
      ? 'Database Migration Completed Successfully'
      : 'Database Migration Failed';
    
    const message = success
      ? `Migration ${migrationId} completed successfully in ${environment} at ${new Date().toISOString()}. Duration: ${durationMs}ms`
      : `Migration ${migrationId} failed in ${environment} at ${new Date().toISOString()}. Duration: ${durationMs}ms`;
    
    await this.publishNotification(subject, message);
  }
  
  private async publishMetric(
    metricName: string,
    value: number,
    migrationId: string,
    environment: string
  ): Promise<void> {
    try {
      await this.cloudwatch.putMetricData({
        Namespace: 'InventoryService/Migrations',
        MetricData: [
          {
            MetricName: metricName,
            Value: value,
            Unit: metricName === 'MigrationDuration' ? 'Milliseconds' : 'Count',
            Dimensions: [
              {
                Name: 'MigrationId',
                Value: migrationId
              },
              {
                Name: 'Environment',
                Value: environment
              }
            ],
            Timestamp: new Date()
          }
        ]
      }).promise();
    } catch (error) {
      this.logger.error(`Failed to publish metric ${metricName}: ${error.message}`);
    }
  }
  
  private async publishNotification(subject: string, message: string): Promise<void> {
    if (!this.notificationTopicArn) {
      this.logger.warn('No SNS topic ARN provided, skipping notification');
      return;
    }
    
    try {
      await this.sns.publish({
        TopicArn: this.notificationTopicArn,
        Subject: subject,
        Message: message
      }).promise();
    } catch (error) {
      this.logger.error(`Failed to publish notification: ${error.message}`);
    }
  }
}
```

## Best Practices for Inventory Service Migrations

### PostgreSQL Best Practices

1. **Incremental Changes**: Make small, incremental schema changes
2. **Avoid Locking**: Minimize operations that lock tables (e.g., ALTER TABLE)
3. **Transaction Control**: Use transactions for related changes
4. **Indexing Strategy**: Create indexes concurrently

```sql
-- Example of adding an index without locking
CREATE INDEX CONCURRENTLY idx_inventory_items_sku ON inventory_items(sku);
```

### DynamoDB Best Practices

1. **Table Design**: Plan for future access patterns
2. **GSI Updates**: Add Global Secondary Indexes incrementally
3. **Capacity Planning**: Monitor capacity during migrations
4. **Item Size Growth**: Account for growing item sizes in capacity planning

```typescript
// Example of updating capacity during high-load migration
async function updateDynamoDBCapacity(tableName: string, readCapacity: number, writeCapacity: number): Promise<void> {
  const dynamoDB = new AWS.DynamoDB();
  
  await dynamoDB.updateTable({
    TableName: tableName,
    ProvisionedThroughput: {
      ReadCapacityUnits: readCapacity,
      WriteCapacityUnits: writeCapacity
    }
  }).promise();
}
```

### Event Sourcing Best Practices

1. **Backward Compatibility**: Maintain backwards compatibility in events
2. **Version Events**: Include version numbers in event schemas
3. **Event Upcasting**: Implement functions to convert old event versions to new ones
4. **Test Replays**: Test event replay after schema changes

## System-Specific Migration Scenarios

### Inventory Item Model Changes

```typescript
// src/migrations/postgres/1709123456789-AddInventoryItemAttributes.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddInventoryItemAttributes1709123456789 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // 1. Add new column with default
    await queryRunner.query(`
      ALTER TABLE inventory_items
      ADD COLUMN attributes JSONB NOT NULL DEFAULT '{}'
    `);
    
    // 2. Update existing records if needed
    await queryRunner.query(`
      UPDATE inventory_items
      SET attributes = jsonb_build_object(
        'brand', 'Unknown',
        'condition', 'New'
      )
    `);
    
    // 3. Add index for querying
    await queryRunner.query(`
      CREATE INDEX CONCURRENTLY idx_inventory_item_attributes
      ON inventory_items USING gin (attributes)
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX IF EXISTS idx_inventory_item_attributes`);
    await queryRunner.query(`ALTER TABLE inventory_items DROP COLUMN attributes`);
  }
}
```

### Warehouse Relocation

```typescript
// src/migrations/postgres/1709123456789-AddWarehouseGeolocation.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddWarehouseGeolocation1709123456789 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Add PostGIS extension if not already added
    await queryRunner.query(`CREATE EXTENSION IF NOT EXISTS postgis`);
    
    // Add geolocation column
    await queryRunner.query(`
      ALTER TABLE warehouses
      ADD COLUMN location GEOGRAPHY(POINT)
    `);
    
    // Add index for geo queries
    await queryRunner.query(`
      CREATE INDEX idx_warehouse_location
      ON warehouses USING GIST (location)
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX IF EXISTS idx_warehouse_location`);
    await queryRunner.query(`ALTER TABLE warehouses DROP COLUMN location`);
    // Note: We don't drop the PostGIS extension as it might be used elsewhere
  }
}
```

## Backup and Recovery Plan

### Coordinated Backup Strategy

```typescript
// src/scripts/coordinated-backup.ts
import * as AWS from 'aws-sdk';
import { Logger } from '@nestjs/common';

export class CoordinatedBackupService {
  private readonly logger = new Logger(CoordinatedBackupService.name);
  private readonly rds: AWS.RDS;
  private readonly dynamoDB: AWS.DynamoDB;
  
  constructor(region: string = process.env.AWS_REGION || 'us-east-1') {
    this.rds = new AWS.RDS({ region });
    this.dynamoDB = new AWS.DynamoDB({ region });
  }
  
  async createCoordinatedBackup(
    rdsInstanceId: string,
    dynamoDBTables: string[]
  ): Promise<{ rdsSnapshotId: string; dynamoDBBackupArns: string[] }> {
    // Generate a unique backup ID
    const backupId = `inventory-backup-${Date.now()}`;
    this.logger.log(`Creating coordinated backup with ID: ${backupId}`);
    
    // Start RDS snapshot
    const rdsSnapshotId = `${backupId}-rds`;
    await this.rds.createDBSnapshot({
      DBInstanceIdentifier: rdsInstanceId,
      DBSnapshotIdentifier: rdsSnapshotId
    }).promise();
    
    // Create DynamoDB backups
    const dynamoDBBackupArns = [];
    for (const tableName of dynamoDBTables) {
      const result = await this.dynamoDB.createBackup({
        TableName: tableName,
        BackupName: `${backupId}-${tableName}`
      }).promise();
      
      dynamoDBBackupArns.push(result.BackupDetails.BackupArn);
    }
    
    // Wait for RDS snapshot to complete
    this.logger.log(`Waiting for RDS snapshot ${rdsSnapshotId} to complete...`);
    await this.rds.waitFor('dbSnapshotAvailable', {
      DBSnapshotIdentifier: rdsSnapshotId
    }).promise();
    
    this.logger.log(`Coordinated backup ${backupId} completed successfully`);
    
    return {
      rdsSnapshotId,
      dynamoDBBackupArns
    };
  }
  
  async restoreFromCoordinatedBackup(
    rdsSnapshotId: string,
    targetRdsInstanceId: string,
    dynamoDBBackupArns: string[],
    dynamoDBTargetTables: Record<string, string>
  ): Promise<void> {
    this.logger.log(`Restoring from coordinated backup. RDS snapshot: ${rdsSnapshotId}`);
    
    // Restore RDS instance
    await this.rds.restoreDBInstanceFromDBSnapshot({
      DBInstanceIdentifier: targetRdsInstanceId,
      DBSnapshotIdentifier: rdsSnapshotId,
      PubliclyAccessible: false
    }).promise();
    
    this.logger.log(`Waiting for RDS instance ${targetRdsInstanceId} to become available...`);
    await this.rds.waitFor('dbInstanceAvailable', {
      DBInstanceIdentifier: targetRdsInstanceId
    }).promise();
    
    // Restore DynamoDB tables
    for (const backupArn of dynamoDBBackupArns) {
      // Get the source table name from the backup
      const describeResult = await this.dynamoDB.describeBackup({
        BackupArn: backupArn
      }).promise();
      
      const sourceTableName = describeResult.BackupDescription.SourceTableDetails.TableName;
      const targetTableName = dynamoDBTargetTables[sourceTableName] || sourceTableName;
      
      this.logger.log(`Restoring DynamoDB table ${sourceTableName} to ${targetTableName}...`);
      
      await this.dynamoDB.restoreTableFromBackup({
        TargetTableName: targetTableName,
        BackupArn: backupArn
      }).promise();
      
      // Wait for table to become active
      let tableStatus = '';
      do {
        const tableDescription = await this.dynamoDB.describeTable({
          TableName: targetTableName
        }).promise();
        
        tableStatus = tableDescription.Table.TableStatus;
        if (tableStatus !== 'ACTIVE') {
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      } while (tableStatus !== 'ACTIVE');
    }
    
    this.logger.log('Coordinated restore completed successfully');
  }
}
```

## References

- [AWS Database Migration Service Documentation](https://docs.aws.amazon.com/dms/latest/userguide/Welcome.html)
- [TypeORM Migrations Documentation](https://typeorm.io/#/migrations)
- [DynamoDB Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [PostgreSQL Zero Downtime Migrations](https://medium.com/braintree-product-technology/postgresql-at-scale-database-schema-changes-without-downtime-20d3749ed680)
- [ADR-004: PostgreSQL for Relational Data](../../../architecture/adr/ADR-004-postgresql-for-relational-data.md)
- [Event Sourcing Pattern](https://microservices.io/patterns/data/event-sourcing.html)