# Testing Strategy for Inventory Service Data Model

## Overview

This document outlines the comprehensive testing strategy for the Inventory Service data model, including unit testing, integration testing, performance testing, and data validation. The strategy ensures that the data model functions correctly and reliably across various scenarios.

## Testing Layers

### 1. Unit Testing

Unit tests focus on testing individual entities, repositories, and utility classes in isolation:

```typescript
// src/inventory/entities/inventory-item.entity.spec.ts
import { InventoryItem } from './inventory-item.entity';

describe('InventoryItem Entity', () => {
  it('should calculate available quantity correctly', () => {
    const item = new InventoryItem();
    item.quantity = 100;
    item.reservedQuantity = 30;
    
    expect(item.getAvailableQuantity()).toBe(70);
  });
  
  it('should validate minimum stock level', () => {
    const item = new InventoryItem();
    item.quantity = 100;
    item.minimumStockLevel = 20;
    
    expect(item.isBelowMinimumStock()).toBeFalsy();
    
    item.quantity = 15;
    expect(item.isBelowMinimumStock()).toBeTruthy();
  });
  
  it('should throw error when reserving more than available', () => {
    const item = new InventoryItem();
    item.quantity = 100;
    item.reservedQuantity = 30;
    
    expect(() => item.reserve(80)).toThrow('Insufficient inventory');
  });
});
```

### 2. Repository Testing

Repository tests verify the data access layer functions correctly:

```typescript
// src/inventory/repositories/inventory-item.repository.spec.ts
import { Test } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { InventoryItemRepository } from './inventory-item.repository';
import { InventoryItem } from '../entities/inventory-item.entity';

describe('InventoryItemRepository', () => {
  let repository: InventoryItemRepository;
  let mockEntityManager: any;
  
  beforeEach(async () => {
    mockEntityManager = {
      findOne: jest.fn(),
      find: jest.fn(),
      save: jest.fn(),
      createQueryBuilder: jest.fn().mockReturnValue({
        where: jest.fn().mockReturnThis(),
        andWhere: jest.fn().mockReturnThis(),
        getMany: jest.fn(),
        getOne: jest.fn()
      }),
      connection: {
        createQueryRunner: jest.fn().mockReturnValue({
          connect: jest.fn(),
          startTransaction: jest.fn(),
          commitTransaction: jest.fn(),
          rollbackTransaction: jest.fn(),
          release: jest.fn(),
          manager: {}
        })
      }
    };
    
    const module = await Test.createTestingModule({
      providers: [
        InventoryItemRepository,
        {
          provide: getRepositoryToken(InventoryItem),
          useValue: mockEntityManager
        }
      ],
    }).compile();
    
    repository = module.get<InventoryItemRepository>(InventoryItemRepository);
  });
  
  it('should find inventory item by SKU', async () => {
    const testSku = 'TEST-SKU-123';
    const inventoryItem = new InventoryItem();
    inventoryItem.sku = testSku;
    
    mockEntityManager.findOne.mockResolvedValue(inventoryItem);
    
    const result = await repository.findBySku(testSku);
    
    expect(mockEntityManager.findOne).toHaveBeenCalledWith({ where: { sku: testSku } });
    expect(result).toBe(inventoryItem);
  });
  
  it('should find available inventory items', async () => {
    const queryBuilder = mockEntityManager.createQueryBuilder();
    const testSkus = ['SKU1', 'SKU2'];
    const inventoryItems = [new InventoryItem(), new InventoryItem()];
    
    queryBuilder.getMany.mockResolvedValue(inventoryItems);
    
    const result = await repository.findAvailableItems(testSkus);
    
    expect(queryBuilder.andWhere).toHaveBeenCalledWith('item.sku IN (:...skus)', { skus: testSkus });
    expect(result).toBe(inventoryItems);
  });
  
  it('should execute in transaction', async () => {
    const queryRunner = mockEntityManager.connection.createQueryRunner();
    const mockFn = jest.fn().mockResolvedValue('result');
    
    const result = await repository.executeInTransaction(mockFn);
    
    expect(queryRunner.startTransaction).toHaveBeenCalled();
    expect(mockFn).toHaveBeenCalled();
    expect(queryRunner.commitTransaction).toHaveBeenCalled();
    expect(queryRunner.release).toHaveBeenCalled();
    expect(result).toBe('result');
  });
  
  it('should rollback transaction on error', async () => {
    const queryRunner = mockEntityManager.connection.createQueryRunner();
    const mockError = new Error('Test error');
    const mockFn = jest.fn().mockRejectedValue(mockError);
    
    await expect(repository.executeInTransaction(mockFn)).rejects.toThrow(mockError);
    
    expect(queryRunner.startTransaction).toHaveBeenCalled();
    expect(mockFn).toHaveBeenCalled();
    expect(queryRunner.rollbackTransaction).toHaveBeenCalled();
    expect(queryRunner.release).toHaveBeenCalled();
  });
});
```

### 3. Integration Testing

Integration tests verify that the data model components work together correctly:

```typescript
// src/inventory/inventory.integration.spec.ts
import { Test } from '@nestjs/testing';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { InventoryModule } from './inventory.module';
import { InventoryService } from './inventory.service';
import { InventoryItem } from './entities/inventory-item.entity';
import { StockTransaction } from './entities/stock-transaction.entity';
import { getTestTypeOrmConfig } from '../config/test-database.config';

describe('Inventory Integration Tests', () => {
  let inventoryService: InventoryService;
  
  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({ isGlobal: true }),
        TypeOrmModule.forRootAsync({
          imports: [ConfigModule],
          inject: [ConfigService],
          useFactory: getTestTypeOrmConfig
        }),
        InventoryModule
      ],
    }).compile();
    
    inventoryService = moduleRef.get<InventoryService>(InventoryService);
  });
  
  it('should create and retrieve inventory item', async () => {
    const testSku = `TEST-SKU-${Date.now()}`;
    
    // Create inventory item
    await inventoryService.createInventoryItem({
      sku: testSku,
      name: 'Test Product',
      quantity: 100,
      warehouseId: 'warehouse-1'
    });
    
    // Retrieve the item
    const item = await inventoryService.getInventoryBySku(testSku);
    
    expect(item).toBeDefined();
    expect(item.sku).toBe(testSku);
    expect(item.quantity).toBe(100);
    expect(item.reservedQuantity).toBe(0);
    expect(item.availableQuantity).toBe(100);
  });
  
  it('should handle inventory reservation and release', async () => {
    const testSku = `TEST-SKU-${Date.now()}`;
    
    // Create inventory item
    await inventoryService.createInventoryItem({
      sku: testSku,
      name: 'Test Product',
      quantity: 100,
      warehouseId: 'warehouse-1'
    });
    
    // Reserve inventory
    const reservationId = await inventoryService.reserveInventory({
      sku: testSku,
      quantity: 30,
      orderId: 'test-order-1'
    });
    
    expect(reservationId).toBeDefined();
    
    // Check updated inventory
    const itemAfterReserve = await inventoryService.getInventoryBySku(testSku);
    expect(itemAfterReserve.quantity).toBe(100);
    expect(itemAfterReserve.reservedQuantity).toBe(30);
    expect(itemAfterReserve.availableQuantity).toBe(70);
    
    // Release reservation
    await inventoryService.releaseReservation(reservationId);
    
    // Check updated inventory
    const itemAfterRelease = await inventoryService.getInventoryBySku(testSku);
    expect(itemAfterRelease.quantity).toBe(100);
    expect(itemAfterRelease.reservedQuantity).toBe(0);
    expect(itemAfterRelease.availableQuantity).toBe(100);
  });
  
  it('should create stock transaction when adjusting inventory', async () => {
    const testSku = `TEST-SKU-${Date.now()}`;
    
    // Create inventory item
    await inventoryService.createInventoryItem({
      sku: testSku,
      name: 'Test Product',
      quantity: 100,
      warehouseId: 'warehouse-1'
    });
    
    // Adjust inventory
    await inventoryService.adjustInventory({
      sku: testSku,
      quantity: -20,
      reason: 'DAMAGE',
      notes: 'Items damaged during handling'
    });
    
    // Check updated inventory
    const item = await inventoryService.getInventoryBySku(testSku);
    expect(item.quantity).toBe(80);
    
    // Check transaction was created
    const transactions = await inventoryService.getTransactionsForSku(testSku);
    expect(transactions.length).toBeGreaterThan(0);
    
    const transaction = transactions[0];
    expect(transaction.type).toBe('ADJUSTMENT');
    expect(transaction.quantity).toBe(-20);
    expect(transaction.reason).toBe('DAMAGE');
    expect(transaction.notes).toBe('Items damaged during handling');
  });
});
```

### 4. Event Sourcing Tests

Specialized tests for the event sourcing capabilities:

```typescript
// src/event-sourcing/event-store.spec.ts
import { Test } from '@nestjs/testing';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { EventStore } from './event-store';
import { DynamoDBEventRepository } from './dynamodb-event.repository';
import { InventoryItemCreatedEvent } from '../inventory/events/inventory-item-created.event';
import { InventoryItemUpdatedEvent } from '../inventory/events/inventory-item-updated.event';

describe('Event Store', () => {
  let eventStore: EventStore;
  let mockDynamoDBRepo: any;
  
  beforeEach(async () => {
    mockDynamoDBRepo = {
      saveEvent: jest.fn(),
      getEvents: jest.fn()
    };
    
    const module = await Test.createTestingModule({
      imports: [ConfigModule.forRoot()],
      providers: [
        EventStore,
        {
          provide: DynamoDBEventRepository,
          useValue: mockDynamoDBRepo
        }
      ],
    }).compile();
    
    eventStore = module.get<EventStore>(EventStore);
  });
  
  it('should store events', async () => {
    const inventoryItemId = 'item-1';
    const event = new InventoryItemCreatedEvent(inventoryItemId, {
      sku: 'TEST-SKU',
      name: 'Test Product',
      quantity: 100
    });
    
    await eventStore.saveEvent(event);
    
    expect(mockDynamoDBRepo.saveEvent).toHaveBeenCalledWith(event);
  });
  
  it('should retrieve events by aggregateId', async () => {
    const inventoryItemId = 'item-1';
    const events = [
      new InventoryItemCreatedEvent(inventoryItemId, {
        sku: 'TEST-SKU',
        name: 'Test Product',
        quantity: 100
      }),
      new InventoryItemUpdatedEvent(inventoryItemId, {
        quantity: 120
      })
    ];
    
    mockDynamoDBRepo.getEvents.mockResolvedValue(events);
    
    const result = await eventStore.getEventsByAggregateId(inventoryItemId);
    
    expect(mockDynamoDBRepo.getEvents).toHaveBeenCalledWith(inventoryItemId);
    expect(result).toBe(events);
    expect(result.length).toBe(2);
  });
  
  it('should reconstruct aggregate from events', async () => {
    const inventoryItemId = 'item-1';
    const events = [
      new InventoryItemCreatedEvent(inventoryItemId, {
        sku: 'TEST-SKU',
        name: 'Test Product',
        quantity: 100
      }),
      new InventoryItemUpdatedEvent(inventoryItemId, {
        quantity: 120
      }),
      new InventoryItemUpdatedEvent(inventoryItemId, {
        reservedQuantity: 20
      })
    ];
    
    mockDynamoDBRepo.getEvents.mockResolvedValue(events);
    
    const aggregate = await eventStore.reconstructAggregate(inventoryItemId);
    
    expect(mockDynamoDBRepo.getEvents).toHaveBeenCalledWith(inventoryItemId);
    expect(aggregate.id).toBe(inventoryItemId);
    expect(aggregate.sku).toBe('TEST-SKU');
    expect(aggregate.name).toBe('Test Product');
    expect(aggregate.quantity).toBe(120);
    expect(aggregate.reservedQuantity).toBe(20);
    expect(aggregate.version).toBe(3);
  });
});
```

## Performance Testing

### 1. Load Testing

Testing for high-volume scenarios:

```typescript
// src/tests/performance/inventory-load.test.ts
import { Test } from '@nestjs/testing';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { InventoryModule } from '../../inventory/inventory.module';
import { InventoryService } from '../../inventory/inventory.service';
import { getTypeOrmConfig } from '../../config/typeorm.config';

describe('Inventory Load Tests', () => {
  let inventoryService: InventoryService;
  
  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({ isGlobal: true }),
        TypeOrmModule.forRootAsync({
          imports: [ConfigModule],
          inject: [ConfigService],
          useFactory: getTypeOrmConfig
        }),
        InventoryModule
      ],
    }).compile();
    
    inventoryService = moduleRef.get<InventoryService>(InventoryService);
  });
  
  it('should handle bulk inventory creation', async () => {
    const items = new Array(1000).fill(0).map((_, i) => ({
      sku: `BULK-SKU-${i}`,
      name: `Bulk Product ${i}`,
      quantity: Math.floor(Math.random() * 1000),
      warehouseId: 'warehouse-1'
    }));
    
    const startTime = Date.now();
    
    await inventoryService.bulkCreateInventoryItems(items);
    
    const endTime = Date.now();
    console.log(`Bulk creation of 1000 items took ${endTime - startTime}ms`);
    
    // Verify a sample of created items
    const sampledItems = [0, 250, 500, 750, 999].map(i => items[i].sku);
    for (const sku of sampledItems) {
      const item = await inventoryService.getInventoryBySku(sku);
      expect(item).toBeDefined();
      expect(item.sku).toBe(sku);
    }
  });
  
  it('should handle concurrent inventory reservations', async () => {
    const testSku = `CONCURRENCY-TEST-${Date.now()}`;
    
    // Create inventory item with 100 units
    await inventoryService.createInventoryItem({
      sku: testSku,
      name: 'Concurrency Test Product',
      quantity: 100,
      warehouseId: 'warehouse-1'
    });
    
    // Create 10 concurrent reservation requests of 10 units each
    const concurrentReservations = new Array(10).fill(0).map((_, i) => 
      inventoryService.reserveInventory({
        sku: testSku,
        quantity: 10,
        orderId: `concurrent-order-${i}`
      })
    );
    
    const startTime = Date.now();
    const results = await Promise.all(concurrentReservations);
    const endTime = Date.now();
    
    console.log(`10 concurrent reservations took ${endTime - startTime}ms`);
    
    // All reservations should succeed and be assigned unique IDs
    expect(results.length).toBe(10);
    expect(new Set(results).size).toBe(10); // All IDs should be unique
    
    // Check final inventory state
    const item = await inventoryService.getInventoryBySku(testSku);
    expect(item.quantity).toBe(100);
    expect(item.reservedQuantity).toBe(100);
    expect(item.availableQuantity).toBe(0);
  });
});
```

### 2. Query Performance Testing

Testing query performance for common inventory operations:

```typescript
// src/tests/performance/query-performance.test.ts
import { Test } from '@nestjs/testing';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { InventoryModule } from '../../inventory/inventory.module';
import { InventoryService } from '../../inventory/inventory.service';
import { InventoryItemRepository } from '../../inventory/repositories/inventory-item.repository';
import { getTypeOrmConfig } from '../../config/typeorm.config';

describe('Query Performance Tests', () => {
  let inventoryService: InventoryService;
  let inventoryRepository: InventoryItemRepository;
  
  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({ isGlobal: true }),
        TypeOrmModule.forRootAsync({
          imports: [ConfigModule],
          inject: [ConfigService],
          useFactory: getTypeOrmConfig
        }),
        InventoryModule
      ],
    }).compile();
    
    inventoryService = moduleRef.get<InventoryService>(InventoryService);
    inventoryRepository = moduleRef.get<InventoryItemRepository>(InventoryItemRepository);
    
    // Pre-load test data if needed
  });
  
  it('should efficiently query inventory by warehouse', async () => {
    const warehouseId = 'warehouse-perf-test';
    
    const startTime = Date.now();
    const items = await inventoryRepository.findByWarehouse(warehouseId);
    const endTime = Date.now();
    
    console.log(`Query for items in warehouse took ${endTime - startTime}ms and returned ${items.length} items`);
    expect(endTime - startTime).toBeLessThan(500); // Should complete in under 500ms
  });
  
  it('should efficiently query items below minimum stock levels', async () => {
    const startTime = Date.now();
    const lowStockItems = await inventoryRepository.findItemsBelowMinimumStock();
    const endTime = Date.now();
    
    console.log(`Query for low stock items took ${endTime - startTime}ms and returned ${lowStockItems.length} items`);
    expect(endTime - startTime).toBeLessThan(500); // Should complete in under 500ms
  });
  
  it('should efficiently execute complex inventory reports', async () => {
    const startTime = Date.now();
    const report = await inventoryService.generateInventoryStatusReport();
    const endTime = Date.now();
    
    console.log(`Generating inventory report took ${endTime - startTime}ms`);
    expect(endTime - startTime).toBeLessThan(2000); // Should complete in under 2 seconds
  });
});
```

## Test Data Management

### 1. Test Data Generation

Specialized utilities for generating test data:

```typescript
// src/tests/utils/test-data-generator.ts
import { faker } from '@faker-js/faker';
import { InventoryItem } from '../../inventory/entities/inventory-item.entity';
import { Warehouse } from '../../inventory/entities/warehouse.entity';

export class TestDataGenerator {
  static createWarehouse(): Partial<Warehouse> {
    return {
      name: faker.commerce.department() + ' Warehouse',
      code: faker.string.alphanumeric(6).toUpperCase(),
      address: faker.location.streetAddress(),
      city: faker.location.city(),
      state: faker.location.state(),
      country: faker.location.country(),
      zipCode: faker.location.zipCode(),
      isActive: true
    };
  }
  
  static createInventoryItem(warehouseId: string): Partial<InventoryItem> {
    const name = faker.commerce.productName();
    return {
      sku: faker.string.alphanumeric(10).toUpperCase(),
      name,
      description: faker.commerce.productDescription(),
      warehouseId,
      quantity: faker.number.int({ min: 5, max: 500 }),
      reservedQuantity: 0,
      minimumStockLevel: faker.number.int({ min: 5, max: 20 }),
      tags: [faker.commerce.department(), faker.commerce.productMaterial()],
      metadata: {
        brand: faker.company.name(),
        category: faker.commerce.department(),
        weight: parseFloat(faker.number.float({ min: 0.1, max: 50, precision: 0.01 }).toFixed(2)),
        dimensions: {
          length: faker.number.int({ min: 1, max: 100 }),
          width: faker.number.int({ min: 1, max: 100 }),
          height: faker.number.int({ min: 1, max: 100 })
        }
      }
    };
  }
  
  static async seedTestData(
    warehouseCount: number,
    itemsPerWarehouse: number,
    warehouseRepository: any,
    inventoryRepository: any
  ): Promise<void> {
    // Create warehouses
    const warehouses = [];
    for (let i = 0; i < warehouseCount; i++) {
      const warehouse = warehouseRepository.create(this.createWarehouse());
      warehouses.push(await warehouseRepository.save(warehouse));
    }
    
    // Create inventory items
    for (const warehouse of warehouses) {
      const items = [];
      for (let i = 0; i < itemsPerWarehouse; i++) {
        const item = inventoryRepository.create(this.createInventoryItem(warehouse.id));
        items.push(item);
      }
      await inventoryRepository.save(items);
    }
    
    console.log(`Seeded ${warehouseCount} warehouses with ${itemsPerWarehouse} items each`);
  }
}
```

### 2. Database Reset

Utilities for resetting the test database:

```typescript
// src/tests/utils/db-reset.ts
import { DataSource } from 'typeorm';
import { Logger } from '@nestjs/common';

export class DatabaseReset {
  private readonly logger = new Logger(DatabaseReset.name);
  
  constructor(private readonly dataSource: DataSource) {}
  
  async resetDatabase(): Promise<void> {
    if (process.env.NODE_ENV !== 'test') {
      this.logger.error('Database reset only allowed in test environment');
      throw new Error('Cannot reset database outside test environment');
    }
    
    const queryRunner = this.dataSource.createQueryRunner();
    await queryRunner.connect();
    
    try {
      this.logger.log('Starting database reset');
      
      // Disable foreign key checks for the reset
      await queryRunner.query('SET FOREIGN_KEY_CHECKS = 0');
      
      // Get all tables
      const tables = await queryRunner.query(`
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '${this.dataSource.options.database}'
      `);
      
      // Truncate all tables
      for (const { table_name } of tables) {
        if (table_name !== 'migrations') {
          await queryRunner.query(`TRUNCATE TABLE \`${table_name}\``);
          this.logger.debug(`Truncated table: ${table_name}`);
        }
      }
      
      // Re-enable foreign key checks
      await queryRunner.query('SET FOREIGN_KEY_CHECKS = 1');
      
      this.logger.log('Database reset completed');
    } catch (error) {
      this.logger.error(`Database reset failed: ${error.message}`, error.stack);
      throw error;
    } finally {
      await queryRunner.release();
    }
  }
}
```

## Test Coverage

The test strategy aims for the following coverage:

1. **Entity Coverage**: 100% coverage of entity methods
2. **Repository Coverage**: 95%+ coverage of repository methods
3. **Service Layer Coverage**: 90%+ coverage of service methods
4. **Edge Cases**: Specific tests for all identified edge cases
5. **Performance**: All critical queries tested for performance

## Integration with CI/CD

### 1. Test Execution in CI Pipeline

```yaml
# .github/workflows/test.yml
name: Inventory Service Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: inventory_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      dynamodb-local:
        image: amazon/dynamodb-local:latest
        ports:
          - 8000:8000
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run linting
        run: npm run lint
        
      - name: Run unit tests
        run: npm run test
        
      - name: Run integration tests
        run: npm run test:integration
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_USERNAME: test
          DB_PASSWORD: test
          DB_DATABASE: inventory_test
          DYNAMODB_ENDPOINT: http://localhost:8000
        
      - name: Generate coverage report
        run: npm run test:cov
        
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

### 2. Test Reports

```typescript
// src/tests/setup.ts
import { reporter } from 'jest-junit';

// Configure test reporter
if (process.env.CI) {
  jest.setTimeout(30000); // Longer timeout in CI environment
  
  // Configure JUnit reporter for CI
  process.env.JEST_JUNIT_OUTPUT_DIR = 'reports/junit';
  process.env.JEST_JUNIT_OUTPUT_NAME = 'inventory-tests.xml';
  reporter(/* optional config */);
}
```

## References

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [TypeORM Testing](https://typeorm.io/#/testing)
- [NestJS Testing](https://docs.nestjs.com/fundamentals/testing)
- [AWS SDK for JavaScript Testing](https://docs.aws.amazon.com/sdk-for-javascript/v2/developer-guide/creating-and-calling-service-objects.html)
- [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html)
- [Jest JUnit Reporter](https://github.com/jest-community/jest-junit)