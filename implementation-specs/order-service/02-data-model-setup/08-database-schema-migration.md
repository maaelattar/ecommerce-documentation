# Database Schema Migration for Order Service

## Overview

This document details the database schema migration strategy for the Order Service, utilizing Amazon RDS for PostgreSQL as the primary database with DynamoDB for specific complementary use cases. The migration approach focuses on maintaining system reliability, minimizing disruption, and ensuring data integrity throughout the schema evolution process.

## Database Technology Context

The Order Service utilizes:
1. **Amazon RDS for PostgreSQL**: Primary database for order data, with complex relationships and ACID requirements
2. **Amazon DynamoDB**: Used for order status history, session-scoped data, and high-throughput metrics

This dual-database approach requires coordinated migration strategies.

## PostgreSQL Migration Framework

### TypeORM Migration Configuration

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
  migrations: [__dirname + '/../migrations/**/*{.ts,.js}'],
  migrationsTableName: 'migrations',
  migrationsRun: false, // Control migrations with dedicated command
  logging: true,
  ssl: configService.get('DB_SSL') === 'true',
  maxQueryExecutionTime: 10000, // Give extra time for migrations
});
```

### Migration Runner Service

```typescript
// src/services/migration.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { DataSource } from 'typeorm';
import * as AWS from 'aws-sdk';

@Injectable()
export class MigrationService {
  private readonly logger = new Logger(MigrationService.name);
  private readonly cloudwatch: AWS.CloudWatch;
  private readonly sns: AWS.SNS;
  private readonly rds: AWS.RDS;
  
  constructor(
    private readonly dataSource: DataSource,
    private readonly region: string = process.env.AWS_REGION || 'us-east-1',
    private readonly topicArn: string = process.env.MIGRATION_NOTIFICATION_TOPIC_ARN,
    private readonly dbInstanceId: string = process.env.DB_INSTANCE_ID
  ) {
    this.cloudwatch = new AWS.CloudWatch({ region });
    this.sns = new AWS.SNS({ region });
    this.rds = new AWS.RDS({ region });
  }
  
  async runMigrations(): Promise<void> {
    const startTime = Date.now();
    let success = false;
    let snapshotId: string = null;
    
    try {
      // Create pre-migration snapshot
      snapshotId = await this.createSnapshot();
      
      // Run migrations
      this.logger.log('Running database migrations...');
      const migrations = await this.dataSource.runMigrations();
      
      if (migrations.length > 0) {
        this.logger.log(`Applied ${migrations.length} migrations successfully`);
        
        // Record metrics
        await this.recordMigrationMetrics(migrations.length, true, Date.now() - startTime);
        
        // Send notification
        await this.sendNotification(
          'Order Service Database Migration Successful',
          `Applied ${migrations.length} migrations successfully.\nMigration IDs: ${migrations.map(m => m.name).join(', ')}`
        );
      } else {
        this.logger.log('No migrations were pending');
      }
      
      success = true;
    } catch (error) {
      this.logger.error(`Migration failed: ${error.message}`, error.stack);
      
      // Record failure metrics
      await this.recordMigrationMetrics(0, false, Date.now() - startTime);
      
      // Send failure notification with snapshot info
      await this.sendNotification(
        'Order Service Database Migration Failed',
        `Migration failed: ${error.message}\nPre-migration snapshot ID: ${snapshotId}\nPlease restore from snapshot if necessary.`
      );
      
      throw error;
    }
  }
  
  private async createSnapshot(): Promise<string> {
    if (!this.dbInstanceId) {
      this.logger.warn('No DB instance ID provided, skipping snapshot creation');
      return null;
    }
    
    try {
      const snapshotId = `pre-migration-${this.dbInstanceId}-${Date.now()}`;
      this.logger.log(`Creating snapshot ${snapshotId}...`);
      
      await this.rds.createDBSnapshot({
        DBInstanceIdentifier: this.dbInstanceId,
        DBSnapshotIdentifier: snapshotId
      }).promise();
      
      this.logger.log(`Snapshot creation initiated for ${snapshotId}`);
      return snapshotId;
    } catch (error) {
      this.logger.error(`Failed to create snapshot: ${error.message}`);
      // Continue with migration even if snapshot fails
      return null;
    }
  }
  
  private async recordMigrationMetrics(
    count: number,
    success: boolean,
    durationMs: number
  ): Promise<void> {
    try {
      await this.cloudwatch.putMetricData({
        Namespace: 'OrderService/Migrations',
        MetricData: [
          {
            MetricName: 'MigrationCount',
            Value: count,
            Unit: 'Count'
          },
          {
            MetricName: success ? 'MigrationSuccess' : 'MigrationFailure',
            Value: 1,
            Unit: 'Count'
          },
          {
            MetricName: 'MigrationDuration',
            Value: durationMs,
            Unit: 'Milliseconds'
          }
        ]
      }).promise();
    } catch (error) {
      this.logger.error(`Failed to publish metrics: ${error.message}`);
    }
  }
  
  private async sendNotification(subject: string, message: string): Promise<void> {
    if (!this.topicArn) {
      this.logger.warn('No SNS topic ARN provided, skipping notification');
      return;
    }
    
    try {
      await this.sns.publish({
        TopicArn: this.topicArn,
        Subject: subject,
        Message: message
      }).promise();
    } catch (error) {
      this.logger.error(`Failed to send notification: ${error.message}`);
    }
  }
}
```

## Migration Types and Patterns

### 1. Schema Migrations

For structural database changes:

```typescript
// src/migrations/1709123456789-AddOrderTags.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddOrderTags1709123456789 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Add new column for order tags
    await queryRunner.query(`
      ALTER TABLE orders
      ADD COLUMN tags TEXT[] NOT NULL DEFAULT '{}'
    `);
    
    // Create index for tag-based queries
    await queryRunner.query(`
      CREATE INDEX idx_orders_tags ON orders USING gin (tags)
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX IF EXISTS idx_orders_tags`);
    await queryRunner.query(`ALTER TABLE orders DROP COLUMN tags`);
  }
}
```

### 2. Data Migrations

For transforming existing data:

```typescript
// src/migrations/1709123456789-NormalizePhoneNumbers.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class NormalizePhoneNumbers1709123456789 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Create temporary function for phone normalization
    await queryRunner.query(`
      CREATE OR REPLACE FUNCTION normalize_phone(phone TEXT) RETURNS TEXT AS $$
      BEGIN
        RETURN regexp_replace(regexp_replace(phone, '[^0-9]', '', 'g'), '^1?([0-9]{10})$', '\1');
      END;
      $$ LANGUAGE plpgsql;
    `);
    
    // Update shipping_details phone numbers
    await queryRunner.query(`
      UPDATE shipping_details
      SET phone = normalize_phone(phone)
      WHERE phone IS NOT NULL AND phone != ''
    `);
    
    // Update billing_details phone numbers
    await queryRunner.query(`
      UPDATE billing_details
      SET phone = normalize_phone(phone)
      WHERE phone IS NOT NULL AND phone != ''
    `);
    
    // Drop temporary function
    await queryRunner.query(`DROP FUNCTION normalize_phone`);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    // No down migration for data normalization - would require original data
    this.logger.log('Down migration not implemented for phone normalization');
  }
}
```

### 3. Multi-Phase Migrations

For complex schema changes that need to be rolled out gradually:

```typescript
// Phase 1: Add new column
// src/migrations/1709123456789-AddOrderTypePhase1.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddOrderTypePhase11709123456789 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      ALTER TABLE orders
      ADD COLUMN order_type VARCHAR(50) NULL
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE orders DROP COLUMN order_type`);
  }
}

// Phase 2: Populate data (run after application deployed with dual-write)
// src/migrations/1709123456790-AddOrderTypePhase2.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddOrderTypePhase21709123456790 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Set default values for existing records
    await queryRunner.query(`
      UPDATE orders
      SET order_type = 'STANDARD'
      WHERE order_type IS NULL
    `);
    
    // Make column non-nullable
    await queryRunner.query(`
      ALTER TABLE orders
      ALTER COLUMN order_type SET NOT NULL
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    // Make column nullable again
    await queryRunner.query(`
      ALTER TABLE orders
      ALTER COLUMN order_type DROP NOT NULL
    `);
  }
}
```

## DynamoDB Schema Migration

For the DynamoDB tables used in the Order Service:

```typescript
// src/scripts/dynamodb-migration.ts
import * as AWS from 'aws-sdk';
import { Logger } from '@nestjs/common';

interface DynamoDBMigration {
  id: string;
  timestamp: number;
  description: string;
  apply: () => Promise<void>;
}

class DynamoDBMigrationRunner {
  private readonly logger = new Logger(DynamoDBMigrationRunner.name);
  private readonly dynamoDB: AWS.DynamoDB;
  private readonly documentClient: AWS.DynamoDB.DocumentClient;
  
  constructor(region: string = process.env.AWS_REGION || 'us-east-1') {
    this.dynamoDB = new AWS.DynamoDB({ region });
    this.documentClient = new AWS.DynamoDB.DocumentClient({ service: this.dynamoDB });
  }
  
  async runMigrations(migrations: DynamoDBMigration[]): Promise<void> {
    // Sort migrations by timestamp
    const sortedMigrations = [...migrations].sort((a, b) => a.timestamp - b.timestamp);
    
    for (const migration of sortedMigrations) {
      this.logger.log(`Applying DynamoDB migration: ${migration.id} - ${migration.description}`);
      
      try {
        await migration.apply();
        this.logger.log(`Successfully applied migration: ${migration.id}`);
      } catch (error) {
        this.logger.error(`Failed to apply migration ${migration.id}: ${error.message}`, error.stack);
        throw error;
      }
    }
  }
}

// Example migrations
const migrations: DynamoDBMigration[] = [
  {
    id: 'create-order-status-history-table',
    timestamp: 1709123456789,
    description: 'Create order status history table',
    apply: async () => {
      const dynamoDB = new AWS.DynamoDB({ region: process.env.AWS_REGION });
      
      try {
        await dynamoDB.describeTable({ TableName: 'order_status_history' }).promise();
        console.log('Table order_status_history already exists, skipping creation');
      } catch (error) {
        if (error.code === 'ResourceNotFoundException') {
          console.log('Creating order_status_history table...');
          
          await dynamoDB.createTable({
            TableName: 'order_status_history',
            KeySchema: [
              { AttributeName: 'orderId', KeyType: 'HASH' },
              { AttributeName: 'timestamp', KeyType: 'RANGE' }
            ],
            AttributeDefinitions: [
              { AttributeName: 'orderId', AttributeType: 'S' },
              { AttributeName: 'timestamp', AttributeType: 'N' },
              { AttributeName: 'status', AttributeType: 'S' }
            ],
            GlobalSecondaryIndexes: [
              {
                IndexName: 'StatusIndex',
                KeySchema: [
                  { AttributeName: 'status', KeyType: 'HASH' },
                  { AttributeName: 'timestamp', KeyType: 'RANGE' }
                ],
                Projection: {
                  ProjectionType: 'ALL'
                },
                ProvisionedThroughput: {
                  ReadCapacityUnits: 5,
                  WriteCapacityUnits: 5
                }
              }
            ],
            BillingMode: 'PROVISIONED',
            ProvisionedThroughput: {
              ReadCapacityUnits: 5,
              WriteCapacityUnits: 5
            },
            StreamSpecification: {
              StreamEnabled: true,
              StreamViewType: 'NEW_AND_OLD_IMAGES'
            }
          }).promise();
          
          console.log('Table order_status_history created successfully');
        } else {
          throw error;
        }
      }
    }
  },
  {
    id: 'add-order-metrics-table',
    timestamp: 1709123456790,
    description: 'Create order metrics table',
    apply: async () => {
      const dynamoDB = new AWS.DynamoDB({ region: process.env.AWS_REGION });
      
      try {
        await dynamoDB.describeTable({ TableName: 'order_metrics' }).promise();
        console.log('Table order_metrics already exists, skipping creation');
      } catch (error) {
        if (error.code === 'ResourceNotFoundException') {
          console.log('Creating order_metrics table...');
          
          await dynamoDB.createTable({
            TableName: 'order_metrics',
            KeySchema: [
              { AttributeName: 'metricKey', KeyType: 'HASH' },
              { AttributeName: 'timestamp', KeyType: 'RANGE' }
            ],
            AttributeDefinitions: [
              { AttributeName: 'metricKey', AttributeType: 'S' },
              { AttributeName: 'timestamp', AttributeType: 'N' }
            ],
            BillingMode: 'PAY_PER_REQUEST'
          }).promise();
          
          console.log('Table order_metrics created successfully');
        } else {
          throw error;
        }
      }
    }
  }
];

// Run migrations
async function main() {
  const runner = new DynamoDBMigrationRunner();
  await runner.runMigrations(migrations);
}

main().catch(console.error);
```

## CI/CD Integration for Order Service Migrations

### Migration Pipeline Configuration

```yaml
# migration-pipeline.yml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  OrderServiceMigrationPipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      ArtifactStore:
        Type: S3
        Location: !Ref ArtifactBucket
      RoleArn: !GetAtt PipelineServiceRole.Arn
      Stages:
        - Name: Source
          Actions:
            - Name: Source
              ActionTypeId:
                Category: Source
                Owner: AWS
                Provider: CodeStarSourceConnection
                Version: '1'
              Configuration:
                ConnectionArn: !Ref GitHubConnection
                FullRepositoryId: "organization/order-service"
                BranchName: "main"
              OutputArtifacts:
                - Name: SourceCode
          
        - Name: BuildAndValidate
          Actions:
            - Name: BuildAndValidate
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Ref OrderServiceBuildProject
              InputArtifacts:
                - Name: SourceCode
              OutputArtifacts:
                - Name: BuildOutput
          
        - Name: MigrateStaging
          Actions:
            - Name: RunMigrationStaging
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Ref StagingMigrationProject
              InputArtifacts:
                - Name: BuildOutput
          
        - Name: ApproveProduction
          Actions:
            - Name: ApprovalStep
              ActionTypeId:
                Category: Approval
                Owner: AWS
                Provider: Manual
                Version: '1'
              Configuration:
                CustomData: "Approve database migration to production"
          
        - Name: MigrateProduction
          Actions:
            - Name: RunMigrationProduction
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Ref ProductionMigrationProject
              InputArtifacts:
                - Name: BuildOutput
```

### CodeBuild Migration Project

```yaml
# buildspec-migration.yml
version: 0.2

env:
  parameter-store:
    DB_SECRET_ARN: "/order-service/${ENVIRONMENT}/db-secret-arn"
    DB_INSTANCE_ID: "/order-service/${ENVIRONMENT}/db-instance-id"
    SNS_TOPIC_ARN: "/order-service/${ENVIRONMENT}/migration-notification-topic"

phases:
  install:
    runtime-versions:
      nodejs: 18
    commands:
      - npm ci
  
  pre_build:
    commands:
      - echo "Retrieving database credentials from Secrets Manager"
      - DB_CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id $DB_SECRET_ARN --query SecretString --output text)
      - export DB_HOST=$(echo $DB_CREDENTIALS | jq -r '.host')
      - export DB_PORT=$(echo $DB_CREDENTIALS | jq -r '.port')
      - export DB_USERNAME=$(echo $DB_CREDENTIALS | jq -r '.username')
      - export DB_PASSWORD=$(echo $DB_CREDENTIALS | jq -r '.password')
      - export DB_DATABASE=$(echo $DB_CREDENTIALS | jq -r '.dbname')
      - export DB_SSL=true
  
  build:
    commands:
      - echo "Creating pre-migration snapshot"
      - SNAPSHOT_ID="pre-migration-${DB_INSTANCE_ID}-$(date +%Y%m%d%H%M%S)"
      - aws rds create-db-snapshot --db-instance-identifier $DB_INSTANCE_ID --db-snapshot-identifier $SNAPSHOT_ID
      - echo "Pre-migration snapshot $SNAPSHOT_ID creation initiated"
      
      - echo "Running database migrations"
      - npm run migration:run
      
      - echo "Running DynamoDB migrations"
      - npm run dynamodb:migrate
  
  post_build:
    commands:
      - if [ $CODEBUILD_BUILD_SUCCEEDING -eq 1 ]; then
          echo "Migrations completed successfully";
          aws sns publish --topic-arn $SNS_TOPIC_ARN --subject "Order Service Migration Successful" --message "Database migration for ${ENVIRONMENT} environment completed successfully at $(date)";
        else
          echo "Migrations failed";
          aws sns publish --topic-arn $SNS_TOPIC_ARN --subject "ALERT: Order Service Migration Failed" --message "Database migration for ${ENVIRONMENT} environment failed at $(date). Pre-migration snapshot: $SNAPSHOT_ID";
          exit 1;
        fi

artifacts:
  files:
    - migration-report.json
  discard-paths: yes
```

## Zero-Downtime Migration Strategies

### 1. Expand-Contract Pattern

For complex schema changes, use the expand-contract pattern:

```typescript
// Phase 1: Expand (Add new structure without breaking existing)
// src/migrations/1709123456789-OrderShippingExpandPhase.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class OrderShippingExpandPhase1709123456789 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Add new json column for shipping options
    await queryRunner.query(`
      ALTER TABLE shipping_details 
      ADD COLUMN shipping_options JSONB NOT NULL DEFAULT '{}'
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      ALTER TABLE shipping_details 
      DROP COLUMN shipping_options
    `);
  }
}

// Phase 2: Migrate data (dual-write period in application code)
// src/migrations/1709123456790-OrderShippingMigratePhase.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class OrderShippingMigratePhase1709123456790 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Migrate existing data to new format
    await queryRunner.query(`
      UPDATE shipping_details
      SET shipping_options = jsonb_build_object(
        'method', shipping_method,
        'speed', shipping_speed,
        'cost', shipping_cost::TEXT,
        'carrier', COALESCE(carrier, 'STANDARD')
      )
      WHERE shipping_options = '{}'
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    // No need for down migration as we don't remove original columns yet
  }
}

// Phase 3: Contract (Remove old structure when no longer needed)
// src/migrations/1709123456791-OrderShippingContractPhase.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class OrderShippingContractPhase1709123456791 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Remove the old columns now that the migration is complete
    await queryRunner.query(`
      ALTER TABLE shipping_details
      DROP COLUMN shipping_method,
      DROP COLUMN shipping_speed,
      DROP COLUMN shipping_cost,
      DROP COLUMN carrier
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    // Recreate the old columns
    await queryRunner.query(`
      ALTER TABLE shipping_details
      ADD COLUMN shipping_method VARCHAR(50),
      ADD COLUMN shipping_speed VARCHAR(50),
      ADD COLUMN shipping_cost DECIMAL(10,2),
      ADD COLUMN carrier VARCHAR(50)
    `);
    
    // Recreate data from the JSON column
    await queryRunner.query(`
      UPDATE shipping_details
      SET
        shipping_method = shipping_options->>'method',
        shipping_speed = shipping_options->>'speed',
        shipping_cost = (shipping_options->>'cost')::DECIMAL(10,2),
        carrier = shipping_options->>'carrier'
    `);
  }
}
```

### 2. Database View Patterns

For maintaining backward compatibility during migrations:

```typescript
// src/migrations/1709123456789-OrderAddressViewMigration.ts
import { MigrationInterface, QueryRunner } from 'typeorm';

export class OrderAddressViewMigration1709123456789 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // 1. Create new structure
    await queryRunner.query(`
      CREATE TABLE addresses (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        address_line1 VARCHAR(255) NOT NULL,
        address_line2 VARCHAR(255),
        city VARCHAR(100) NOT NULL,
        state VARCHAR(50) NOT NULL,
        postal_code VARCHAR(20) NOT NULL,
        country VARCHAR(50) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // 2. Migrate billing_details addresses to new table
    await queryRunner.query(`
      INSERT INTO addresses (
        address_line1,
        address_line2,
        city,
        state,
        postal_code,
        country
      )
      SELECT
        street_address,
        COALESCE(apartment, ''),
        city,
        state,
        zip_code,
        country
      FROM billing_details
    `);
    
    // 3. Add foreign key to billing_details
    await queryRunner.query(`
      ALTER TABLE billing_details
      ADD COLUMN address_id UUID,
      ADD CONSTRAINT fk_billing_address
        FOREIGN KEY (address_id)
        REFERENCES addresses(id)
        ON DELETE SET NULL
    `);
    
    // 4. Update foreign keys with the new address IDs
    await queryRunner.query(`
      WITH address_mapping AS (
        SELECT
          b.id as billing_id,
          a.id as address_id
        FROM
          billing_details b
          JOIN addresses a ON
            a.address_line1 = b.street_address AND
            a.city = b.city AND
            a.state = b.state AND
            a.postal_code = b.zip_code AND
            a.country = b.country
      )
      UPDATE billing_details
      SET address_id = address_mapping.address_id
      FROM address_mapping
      WHERE billing_details.id = address_mapping.billing_id
    `);
    
    // 5. Create view for backward compatibility
    await queryRunner.query(`
      CREATE OR REPLACE VIEW billing_address_view AS
      SELECT
        b.id,
        b.order_id,
        b.first_name,
        b.last_name,
        b.email,
        b.phone,
        a.address_line1 as street_address,
        a.address_line2 as apartment,
        a.city,
        a.state,
        a.postal_code as zip_code,
        a.country
      FROM
        billing_details b
        JOIN addresses a ON b.address_id = a.id
    `);
  }
  
  public async down(queryRunner: QueryRunner): Promise<void> {
    // 1. Drop the view
    await queryRunner.query(`DROP VIEW IF EXISTS billing_address_view`);
    
    // 2. Migrate data back to original columns
    await queryRunner.query(`
      UPDATE billing_details b
      SET
        street_address = a.address_line1,
        apartment = a.address_line2,
        city = a.city,
        state = a.state,
        zip_code = a.postal_code,
        country = a.country
      FROM addresses a
      WHERE b.address_id = a.id
    `);
    
    // 3. Drop the foreign key constraint and column
    await queryRunner.query(`
      ALTER TABLE billing_details
      DROP CONSTRAINT fk_billing_address,
      DROP COLUMN address_id
    `);
    
    // 4. Drop the addresses table
    await queryRunner.query(`DROP TABLE addresses`);
  }
}
```

## Database Restoration Strategy

For cases where migrations need to be rolled back:

```typescript
// src/scripts/restore-database.ts
import * as AWS from 'aws-sdk';
import { Logger } from '@nestjs/common';

class DatabaseRestoration {
  private readonly logger = new Logger(DatabaseRestoration.name);
  private readonly rds: AWS.RDS;
  
  constructor(
    private readonly region: string = process.env.AWS_REGION || 'us-east-1',
    private readonly dbInstanceId: string = process.env.DB_INSTANCE_ID
  ) {
    this.rds = new AWS.RDS({ region });
  }
  
  async findLatestPreMigrationSnapshot(): Promise<string | null> {
    try {
      const result = await this.rds.describeDBSnapshots({
        DBInstanceIdentifier: this.dbInstanceId,
        SnapshotType: 'manual',
        IncludeShared: false,
        IncludePublic: false
      }).promise();
      
      // Find snapshots with pre-migration prefix
      const preMigrationSnapshots = result.DBSnapshots
        .filter(snapshot => snapshot.DBSnapshotIdentifier.startsWith(`pre-migration-${this.dbInstanceId}`))
        .sort((a, b) => b.SnapshotCreateTime.getTime() - a.SnapshotCreateTime.getTime());
      
      if (preMigrationSnapshots.length === 0) {
        this.logger.warn('No pre-migration snapshots found');
        return null;
      }
      
      return preMigrationSnapshots[0].DBSnapshotIdentifier;
    } catch (error) {
      this.logger.error(`Failed to find pre-migration snapshots: ${error.message}`);
      return null;
    }
  }
  
  async restoreFromSnapshot(snapshotId: string): Promise<void> {
    if (!snapshotId) {
      throw new Error('No snapshot ID provided');
    }
    
    try {
      this.logger.log(`Checking if instance ${this.dbInstanceId} exists...`);
      
      try {
        await this.rds.describeDBInstances({
          DBInstanceIdentifier: this.dbInstanceId
        }).promise();
        
        // Instance exists, need to delete it first
        this.logger.log(`Deleting instance ${this.dbInstanceId}...`);
        await this.rds.deleteDBInstance({
          DBInstanceIdentifier: this.dbInstanceId,
          SkipFinalSnapshot: true,
          DeleteAutomatedBackups: false
        }).promise();
        
        this.logger.log(`Waiting for instance ${this.dbInstanceId} to be deleted...`);
        await this.rds.waitFor('dbInstanceDeleted', {
          DBInstanceIdentifier: this.dbInstanceId
        }).promise();
      } catch (error) {
        if (error.code !== 'DBInstanceNotFound') {
          throw error;
        }
      }
      
      // Now restore from snapshot
      this.logger.log(`Restoring instance ${this.dbInstanceId} from snapshot ${snapshotId}...`);
      
      // Get snapshot details to preserve settings
      const snapshotDetails = await this.rds.describeDBSnapshots({
        DBSnapshotIdentifier: snapshotId
      }).promise();
      
      const snapshot = snapshotDetails.DBSnapshots[0];
      
      await this.rds.restoreDBInstanceFromDBSnapshot({
        DBInstanceIdentifier: this.dbInstanceId,
        DBSnapshotIdentifier: snapshotId,
        DBSubnetGroupName: snapshot.DBSubnetGroup,
        MultiAZ: snapshot.MultiAZ,
        PubliclyAccessible: false,
        AutoMinorVersionUpgrade: true,
        CopyTagsToSnapshot: true
      }).promise();
      
      this.logger.log(`Waiting for instance ${this.dbInstanceId} to be available...`);
      await this.rds.waitFor('dbInstanceAvailable', {
        DBInstanceIdentifier: this.dbInstanceId
      }).promise();
      
      this.logger.log(`Instance ${this.dbInstanceId} restored successfully from snapshot ${snapshotId}`);
    } catch (error) {
      this.logger.error(`Failed to restore from snapshot: ${error.message}`);
      throw error;
    }
  }
  
  async performEmergencyRestore(): Promise<void> {
    this.logger.log('Starting emergency database restoration...');
    
    // 1. Find latest pre-migration snapshot
    const snapshotId = await this.findLatestPreMigrationSnapshot();
    
    if (!snapshotId) {
      throw new Error('No pre-migration snapshots found for emergency restore');
    }
    
    // 2. Restore database from snapshot
    await this.restoreFromSnapshot(snapshotId);
    
    // 3. Send notification about restoration
    const sns = new AWS.SNS({ region: this.region });
    await sns.publish({
      TopicArn: process.env.NOTIFICATION_TOPIC_ARN,
      Subject: 'Order Service Database Emergency Restoration Completed',
      Message: `
        Database ${this.dbInstanceId} has been restored from snapshot ${snapshotId}.
        Restoration completed at ${new Date().toISOString()}.
        Please verify the application is functioning correctly.
      `
    }).promise();
    
    this.logger.log('Emergency restoration completed successfully');
  }
}

// Command-line interface for restoration
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  const restorer = new DatabaseRestoration();
  
  if (command === 'find-snapshot') {
    const snapshotId = await restorer.findLatestPreMigrationSnapshot();
    console.log(`Latest pre-migration snapshot: ${snapshotId || 'None found'}`);
  } else if (command === 'restore') {
    const snapshotId = args[1] || await restorer.findLatestPreMigrationSnapshot();
    
    if (!snapshotId) {
      console.error('No snapshot ID provided or found');
      process.exit(1);
    }
    
    await restorer.restoreFromSnapshot(snapshotId);
  } else if (command === 'emergency') {
    await restorer.performEmergencyRestore();
  } else {
    console.log(`
      Usage:
        node restore-database.js find-snapshot
        node restore-database.js restore [snapshot-id]
        node restore-database.js emergency
    `);
  }
}

main().catch(error => {
  console.error('Restoration failed:', error);
  process.exit(1);
});
```

## Best Practices for Order Service Migrations

### 1. Schema Design Principles

- **Minimize Foreign Key Constraints**: Foreign keys add overhead during migrations.
- **Consider UUID Primary Keys**: Makes merging of databases easier if needed.
- **Use Connection Pooling**: Set explicit connection limits to avoid exhaustion during migrations.
- **Schema Documentation**: Keep schema documentation up-to-date with each migration.
  
### 2. Migration Safety Patterns

- **Reversible Migrations**: Always provide 'down' migrations.
- **Incremental Changes**: Smaller, focused migrations are safer.
- **Validate Data**: Include validation steps in migrations.
- **Checkpoints**: For large migrations, implement checkpoints to resume.

### 3. Performance Considerations

- **Off-Peak Migration Windows**: Schedule migrations during low traffic.
- **Batched Operations**: For large tables, process in batches to reduce locking.
- **Index Management**: Create indexes after data loading.
- **Monitor Lock Contention**: Watch for locks during migrations.

### 4. AWS-Specific Recommendations

- **Use RDS Read Replicas**: Offload reporting queries during migrations.
- **Leverage Point-in-Time Recovery**: Configure automated backups.
- **Monitor Performance Insights**: Watch for performance issues during/after migrations.
- **Use RDS Event Subscriptions**: Get notified of important database events.

## References

- [TypeORM Migration Documentation](https://typeorm.io/#/migrations)
- [AWS RDS Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [Zero-Downtime PostgreSQL Migrations](https://medium.com/braintree-product-technology/postgresql-at-scale-database-schema-changes-without-downtime-20d3749ed680)
- [CI/CD for Database Changes](https://aws.amazon.com/blogs/devops/implement-ci-cd-for-database-changes-using-aws-codepipeline-and-aws-lambda/)
- [AWS Database Migration Service](https://aws.amazon.com/dms/)
- [ADR-004: PostgreSQL for Relational Data](../../../architecture/adr/ADR-004-postgresql-for-relational-data.md)