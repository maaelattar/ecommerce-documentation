# Migration Strategy for Inventory Service

## Overview

This document outlines the migration strategy for the Inventory Service database, focusing on version control, deployment procedures, and rollback plans. It complements the [Database Schema Migration](./08-database-schema-migration.md) document which provides AWS-specific migration implementation details.

## Migration Philosophy

The Inventory Service follows these principles for database migrations:

1. **Versioned and Repeatable**: All schema changes are versioned and can be applied repeatedly
2. **Forward-Only by Default**: Migrations primarily support moving forward, with rollback as a contingency
3. **Zero Downtime Goal**: Migrations are designed to minimize or eliminate service interruption
4. **Dual Database Awareness**: Coordinated migrations for both PostgreSQL and DynamoDB components

## Migration Types

### 1. Schema Migrations

Schema migrations handle structural changes to the database:

```typescript
// Example schema migration
export class AddWarehouseLocation1709123456789 implements MigrationInterface {
    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`
            ALTER TABLE warehouses
            ADD COLUMN location GEOMETRY(POINT, 4326)
        `);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`
            ALTER TABLE warehouses
            DROP COLUMN location
        `);
    }
}
```

### 2. Data Migrations

Data migrations handle data transformations and seeding:

```typescript
// Example data migration
export class SeedWarehouseData1709123456789 implements MigrationInterface {
    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`
            INSERT INTO warehouses (id, name, code, location)
            VALUES 
                (gen_random_uuid(), 'Main Warehouse', 'WH-MAIN', ST_SetSRID(ST_MakePoint(-122.335167, 47.608013), 4326)),
                (gen_random_uuid(), 'East Coast Hub', 'WH-EAST', ST_SetSRID(ST_MakePoint(-74.005974, 40.712776), 4326))
        `);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`
            DELETE FROM warehouses
            WHERE code IN ('WH-MAIN', 'WH-EAST')
        `);
    }
}
```

### 3. DynamoDB Migrations

For the event store in DynamoDB:

```typescript
// src/migrations/dynamodb/create-events-table.ts
import * as AWS from 'aws-sdk';

export async function createEventsTable(dynamoDb: AWS.DynamoDB): Promise<void> {
  try {
    await dynamoDb.describeTable({ TableName: 'inventory_events' }).promise();
    console.log('Table inventory_events already exists');
  } catch (error) {
    if (error.code === 'ResourceNotFoundException') {
      await dynamoDb.createTable({
        TableName: 'inventory_events',
        KeySchema: [
          { AttributeName: 'inventoryItemId', KeyType: 'HASH' },
          { AttributeName: 'sequenceNumber', KeyType: 'RANGE' }
        ],
        AttributeDefinitions: [
          { AttributeName: 'inventoryItemId', AttributeType: 'S' },
          { AttributeName: 'sequenceNumber', AttributeType: 'N' },
          { AttributeName: 'eventType', AttributeType: 'S' }
        ],
        GlobalSecondaryIndexes: [
          {
            IndexName: 'EventTypeIndex',
            KeySchema: [
              { AttributeName: 'eventType', KeyType: 'HASH' }
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
        ProvisionedThroughput: {
          ReadCapacityUnits: 5,
          WriteCapacityUnits: 5
        }
      }).promise();
      console.log('Table inventory_events created successfully');
    } else {
      throw error;
    }
  }
}
```

## Migration Workflow

### 1. Development Workflow

```bash
# Generate migration
npm run typeorm migration:generate -- -n AddWarehouseLocation

# Run migration
npm run typeorm migration:run

# Run DynamoDB migrations
npm run dynamodb:migrate

# Revert migration (PostgreSQL only)
npm run typeorm migration:revert
```

### 2. Production Workflow

```bash
# Deploy migrations with specific config
npm run typeorm migration:run -- -d src/config/typeorm.config.ts

# Verify migrations
npm run typeorm migration:show -- -d src/config/typeorm.config.ts

# Deploy DynamoDB migrations
NODE_ENV=production npm run dynamodb:migrate
```

## Version Control

### 1. Migration Naming Convention

```
<timestamp>-<description>.ts
```

Example: `1709123456789-AddWarehouseLocation.ts`

### 2. Migration File Structure

```typescript
import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddWarehouseLocation1709123456789 implements MigrationInterface {
    name = 'AddWarehouseLocation1709123456789';

    public async up(queryRunner: QueryRunner): Promise<void> {
        // Migration logic
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        // Rollback logic
    }
}
```

## Deployment Strategy

### 1. Pre-deployment Checks

```typescript
// src/migration/checks/pre-deployment.check.ts
export class PreDeploymentCheck {
    async validateMigration(migration: MigrationInterface): Promise<void> {
        // Check for destructive operations
        if (this.hasDestructiveOperations(migration)) {
            throw new Error('Migration contains destructive operations');
        }

        // Check for data loss risk
        if (this.hasDataLossRisk(migration)) {
            throw new Error('Migration may cause data loss');
        }

        // Check for performance impact
        if (this.hasPerformanceImpact(migration)) {
            console.warn('Migration may impact performance');
        }
    }

    private hasDestructiveOperations(migration: MigrationInterface): boolean {
        // Implementation details
        return false;
    }

    private hasDataLossRisk(migration: MigrationInterface): boolean {
        // Implementation details
        return false;
    }

    private hasPerformanceImpact(migration: MigrationInterface): boolean {
        // Implementation details
        return false;
    }
}
```

### 2. Deployment Process

1. **Backup**: Create database snapshot before migration
2. **Pre-checks**: Run migration validation
3. **Execution**: Apply migrations in proper order
4. **Verification**: Verify migration success
5. **Notification**: Update stakeholders on completion

## Rollback Strategy

### 1. Standard Rollback

For simple migrations, use the built-in revert functionality:

```bash
# Revert the last migration
npm run typeorm migration:revert
```

### 2. Point-in-Time Recovery

For complex failures, use AWS RDS point-in-time recovery:

```typescript
// src/scripts/restore-database.ts
import * as AWS from 'aws-sdk';

async function restoreToPointInTime(
  dbInstanceId: string,
  targetTime: Date
): Promise<void> {
  const rds = new AWS.RDS({ region: process.env.AWS_REGION });
  
  const params = {
    SourceDBInstanceIdentifier: dbInstanceId,
    TargetDBInstanceIdentifier: `${dbInstanceId}-restored`,
    RestoreTime: targetTime,
    UseLatestRestorableTime: false
  };
  
  await rds.restoreDBInstanceToPointInTime(params).promise();
  console.log(`Restored ${dbInstanceId} to ${targetTime.toISOString()}`);
}
```

### 3. Emergency Rollback

For critical failures:

```typescript
// src/scripts/emergency-rollback.ts
export class EmergencyRollback {
    async executeEmergencyRollback(): Promise<void> {
        // 1. Stop application
        await this.stopApplication();

        // 2. Restore from latest snapshot
        await this.restoreFromSnapshot();

        // 3. Verify restoration
        await this.verifyRestoration();

        // 4. Restart application
        await this.restartApplication();
    }

    // Implementation details...
}
```

## Testing Strategy

### 1. Migration Testing

Every migration must be tested in isolation:

```typescript
// src/migration/tests/migration.test.ts
describe('Migration Tests', () => {
    it('should apply migration successfully', async () => {
        // Test migration application
    });

    it('should rollback migration successfully', async () => {
        // Test migration rollback
    });

    it('should handle errors gracefully', async () => {
        // Test error handling
    });
});
```

### 2. Integration Testing

Migrations must be tested against a realistic dataset:

```typescript
// src/migration/tests/integration.test.ts
describe('Migration Integration Tests', () => {
    it('should maintain data integrity', async () => {
        // Test data integrity after migration
    });

    it('should handle concurrent operations', async () => {
        // Test migration with concurrent operations
    });

    it('should maintain backward compatibility', async () => {
        // Test application compatibility after migration
    });
});
```

## Event Store Migration Considerations

Since the Inventory Service uses event sourcing, special considerations apply:

### 1. Event Schema Evolution

```typescript
// src/event-sourcing/schema-registry.ts
export class EventSchemaRegistry {
    private schemas: Map<string, Map<number, object>> = new Map();

    registerSchema(eventType: string, version: number, schema: object): void {
        if (!this.schemas.has(eventType)) {
            this.schemas.set(eventType, new Map());
        }
        this.schemas.get(eventType).set(version, schema);
    }

    getSchema(eventType: string, version: number): object {
        if (!this.schemas.has(eventType) || !this.schemas.get(eventType).has(version)) {
            throw new Error(`Schema not found for ${eventType} version ${version}`);
        }
        return this.schemas.get(eventType).get(version);
    }

    getLatestVersion(eventType: string): number {
        if (!this.schemas.has(eventType)) {
            throw new Error(`No schemas registered for ${eventType}`);
        }
        
        const versions = Array.from(this.schemas.get(eventType).keys());
        return Math.max(...versions);
    }
}
```

### 2. Event Upcasting

When event schemas evolve, provide upcasting functions:

```typescript
// src/event-sourcing/upcasting.ts
export interface EventUpcastingFunction {
    (oldEvent: any): any;
}

export class EventUpcaster {
    private upcasters: Map<string, Map<number, EventUpcastingFunction[]>> = new Map();

    registerUpcaster(
        eventType: string, 
        fromVersion: number, 
        toVersion: number, 
        upcaster: EventUpcastingFunction
    ): void {
        if (!this.upcasters.has(eventType)) {
            this.upcasters.set(eventType, new Map());
        }
        
        if (!this.upcasters.get(eventType).has(fromVersion)) {
            this.upcasters.get(eventType).set(fromVersion, []);
        }
        
        this.upcasters.get(eventType).get(fromVersion).push(upcaster);
    }

    upcast(event: any): any {
        const eventType = event.eventType;
        const eventVersion = event.eventVersion || 1;
        
        if (!this.upcasters.has(eventType)) {
            return event;
        }
        
        let upcasted = { ...event };
        
        for (const [fromVersion, upcasters] of this.upcasters.get(eventType).entries()) {
            if (fromVersion === eventVersion) {
                for (const upcaster of upcasters) {
                    upcasted = upcaster(upcasted);
                }
            }
        }
        
        return upcasted;
    }
}
```

## Monitoring and Logging

### 1. Migration Monitoring

```typescript
// src/migration/monitoring/migration.monitoring.ts
export class MigrationMonitoring {
    async monitorMigration(migration: MigrationInterface): Promise<void> {
        // 1. Log migration start
        this.logMigrationStart(migration);

        // 2. Monitor migration progress
        await this.monitorProgress(migration);

        // 3. Log migration completion
        this.logMigrationCompletion(migration);

        // 4. Update monitoring dashboards
        await this.updateDashboards(migration);
    }

    // Implementation details...
}
```

### 2. Performance Monitoring

```typescript
// src/migration/monitoring/performance.monitoring.ts
export class MigrationPerformanceMonitoring {
    async monitorPerformance(migration: MigrationInterface): Promise<void> {
        // 1. Measure execution time
        const startTime = Date.now();
        
        // 2. Apply migration
        await migration.up(/* queryRunner */);
        
        // 3. Calculate duration
        const duration = Date.now() - startTime;
        
        // 4. Log performance metrics
        this.logPerformanceMetrics(migration, duration);
        
        // 5. Alert if slow
        if (duration > 30000) { // 30 seconds
            await this.alertSlowMigration(migration, duration);
        }
    }

    // Implementation details...
}
```

## Best Practices

1. **Migration Design**
   - Keep migrations small and focused
   - Implement both up and down migrations
   - Test thoroughly before deployment
   - Document migration purpose

2. **Deployment**
   - Always backup before deployment
   - Deploy during low-traffic periods
   - Monitor closely during and after migration
   - Have rollback plan ready

3. **Performance**
   - Use batching for large data migrations
   - Create indexes concurrently
   - Monitor lock contention
   - Consider using table partitioning for large tables

4. **Documentation**
   - Document each migration's purpose
   - Keep track of all applied migrations
   - Document any special handling required
   - Document known limitations or issues

## Special Considerations for Inventory Service

1. **Stock Quantity Integrity**
   - Ensure migrations maintain stock quantity integrity
   - Validate available = total - reserved after migrations

2. **Warehouse Location Data**
   - Handle geographic data type migrations carefully

3. **Event Chronology**
   - Maintain strict ordering of inventory events during migrations

4. **Reservation Consistency**
   - Ensure reservations remain valid after schema changes

## References

- [TypeORM Migration Documentation](https://typeorm.io/#/migrations)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/index.html)
- [DynamoDB Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [Event Sourcing Pattern](https://microservices.io/patterns/data/event-sourcing.html)
- [Blue-Green Deployment Strategy](https://martinfowler.com/bliki/BlueGreenDeployment.html)