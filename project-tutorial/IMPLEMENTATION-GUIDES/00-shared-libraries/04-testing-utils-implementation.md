# Testing Utils Implementation Guide 🧪

> **Goal**: Build comprehensive testing utilities for reliable, fast, and maintainable tests across all microservices

---

## 🎯 **What You'll Build**

A complete testing toolkit with:
- **Test database utilities** with isolation and cleanup
- **Mock factories and builders** for consistent test data
- **Integration test helpers** for API and service testing
- **Event testing utilities** for event-driven workflows
- **Performance testing tools** for load and stress testing

---

## 📦 **Package Setup**

### **1. Initialize Package**
```bash
cd packages/testing-utils
npm init -y
```

### **2. Package.json Configuration**
```json
{
  "name": "@ecommerce/testing-utils",
  "version": "1.0.0",
  "description": "Testing utilities for ecommerce microservices",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "test:watch": "jest --watch",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/testing": "^10.0.0",
    "@nestjs/typeorm": "^10.0.0",
    "typeorm": "^0.3.0",
    "faker": "^6.6.6",
    "factory.ts": "^0.5.0",
    "supertest": "^6.3.0",
    "testcontainers": "^10.0.0",
    "redis-mock": "^0.56.0"
  },
  "devDependencies": {
    "@types/faker": "^6.6.0",
    "@types/supertest": "^2.0.0",
    "jest": "^29.0.0",
    "typescript": "^5.0.0"
  }
}
```

---

## 🏗️ **Implementation Structure**

```
packages/testing-utils/
├── src/
│   ├── database/
│   │   ├── test-database.service.ts
│   │   ├── database-cleaner.ts
│   │   └── index.ts
│   ├── factories/
│   │   ├── user.factory.ts
│   │   ├── product.factory.ts
│   │   ├── order.factory.ts
│   │   └── index.ts
│   ├── mocks/
│   │   ├── repository.mock.ts
│   │   ├── service.mock.ts
│   │   ├── event.mock.ts
│   │   └── index.ts
│   ├── helpers/
│   │   ├── api-test.helper.ts
│   │   ├── integration-test.helper.ts
│   │   ├── event-test.helper.ts
│   │   └── index.ts
│   ├── performance/
│   │   ├── load-test.helper.ts
│   │   ├── metrics.collector.ts
│   │   └── index.ts
│   └── index.ts
└── tests/
```

---

## 🗄️ **1. Database Testing Utilities**

### **Test Database Service**
```typescript
// src/database/test-database.service.ts
import { Injectable, OnModuleDestroy } from '@nestjs/common';
import { DataSource, EntityTarget, Repository } from 'typeorm';
import { GenericContainer, StartedTestContainer } from 'testcontainers';

@Injectable()
export class TestDatabaseService implements OnModuleDestroy {
  private container: StartedTestContainer;
  private dataSource: DataSource;
  private static instance: TestDatabaseService;

  static getInstance(): TestDatabaseService {
    if (!TestDatabaseService.instance) {
      TestDatabaseService.instance = new TestDatabaseService();
    }
    return TestDatabaseService.instance;
  }

  async setupTestDatabase(): Promise<DataSource> {
    if (this.dataSource?.isInitialized) {
      return this.dataSource;
    }

    // Start PostgreSQL container
    this.container = await new GenericContainer('postgres:15')
      .withEnvironment({
        POSTGRES_DB: 'test_db',
        POSTGRES_USER: 'test_user',
        POSTGRES_PASSWORD: 'test_password'
      })
      .withExposedPorts(5432)
      .start();

    const host = this.container.getHost();
    const port = this.container.getMappedPort(5432);

    // Create DataSource
    this.dataSource = new DataSource({
      type: 'postgres',
      host,
      port,
      username: 'test_user',
      password: 'test_password',
      database: 'test_db',
      synchronize: true,
      dropSchema: true,
      entities: [], // Will be set by test modules
      logging: false
    });

    await this.dataSource.initialize();
    return this.dataSource;
  }

  async getRepository<T>(entity: EntityTarget<T>): Promise<Repository<T>> {
    if (!this.dataSource?.isInitialized) {
      await this.setupTestDatabase();
    }
    return this.dataSource.getRepository(entity);
  }

  async truncateAllTables(): Promise<void> {
    if (!this.dataSource?.isInitialized) return;

    const entities = this.dataSource.entityMetadatas;
    
    for (const entity of entities) {
      const repository = this.dataSource.getRepository(entity.name);
      await repository.query(`TRUNCATE "${entity.tableName}" RESTART IDENTITY CASCADE;`);
    }
  }

  async closeConnection(): Promise<void> {
    if (this.dataSource?.isInitialized) {
      await this.dataSource.destroy();
    }
    if (this.container) {
      await this.container.stop();
    }
  }

  async onModuleDestroy(): Promise<void> {
    await this.closeConnection();
  }
}
```

### **Database Cleaner**
```typescript
// src/database/database-cleaner.ts
import { DataSource } from 'typeorm';

export class DatabaseCleaner {
  constructor(private dataSource: DataSource) {}

  async cleanAll(): Promise<void> {
    const queryRunner = this.dataSource.createQueryRunner();
    
    try {
      await queryRunner.connect();
      await queryRunner.startTransaction();

      // Disable foreign key checks
      await queryRunner.query('SET session_replication_role = replica;');

      // Get all table names
      const tables = await queryRunner.query(`
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
      `);

      // Truncate all tables
      for (const table of tables) {
        await queryRunner.query(`TRUNCATE TABLE "${table.tablename}" RESTART IDENTITY CASCADE;`);
      }

      // Re-enable foreign key checks
      await queryRunner.query('SET session_replication_role = DEFAULT;');

      await queryRunner.commitTransaction();
    } catch (error) {
      await queryRunner.rollbackTransaction();
      throw error;
    } finally {
      await queryRunner.release();
    }
  }

  async cleanTable(tableName: string): Promise<void> {
    await this.dataSource.query(`TRUNCATE TABLE "${tableName}" RESTART IDENTITY CASCADE;`);
  }

  async cleanTables(tableNames: string[]): Promise<void> {
    const queryRunner = this.dataSource.createQueryRunner();
    
    try {
      await queryRunner.connect();
      await queryRunner.startTransaction();

      for (const tableName of tableNames) {
        await queryRunner.query(`TRUNCATE TABLE "${tableName}" RESTART IDENTITY CASCADE;`);
      }

      await queryRunner.commitTransaction();
    } catch (error) {
      await queryRunner.rollbackTransaction();
      throw error;
    } finally {
      await queryRunner.release();
    }
  }
}
```

---

## 🏭 **2. Factory Pattern Implementation**

### **Base Factory**
```typescript
// src/factories/base.factory.ts
import { Factory } from 'factory.ts';
import { faker } from '@faker-js/faker';

export abstract class BaseFactory<T> {
  protected abstract factory: Factory<T>;

  build(overrides?: Partial<T>): T {
    return this.factory.build(overrides);
  }

  buildMany(count: number, overrides?: Partial<T>): T[] {
    return Array.from({ length: count }, () => this.build(overrides));
  }

  async create(overrides?: Partial<T>): Promise<T> {
    const entity = this.build(overrides);
    return await this.save(entity);
  }

  async createMany(count: number, overrides?: Partial<T>): Promise<T[]> {
    const entities = this.buildMany(count, overrides);
    return await Promise.all(entities.map(entity => this.save(entity)));
  }

  protected abstract save(entity: T): Promise<T>;

  protected generateFakeData() {
    return {
      uuid: () => faker.string.uuid(),
      email: () => faker.internet.email(),
      firstName: () => faker.person.firstName(),
      lastName: () => faker.person.lastName(),
      company: () => faker.company.name(),
      phone: () => faker.phone.number(),
      address: () => ({
        street: faker.location.streetAddress(),
        city: faker.location.city(),
        state: faker.location.state(),
        zipCode: faker.location.zipCode(),
        country: faker.location.country()
      }),
      date: () => faker.date.recent(),
      pastDate: () => faker.date.past(),
      futureDate: () => faker.date.future(),
      number: (min = 1, max = 1000) => faker.number.int({ min, max }),
      decimal: (min = 1, max = 1000) => faker.number.float({ min, max }),
      boolean: () => faker.datatype.boolean(),
      word: () => faker.lorem.word(),
      sentence: () => faker.lorem.sentence(),
      paragraph: () => faker.lorem.paragraph(),
      url: () => faker.internet.url(),
      imageUrl: () => faker.image.url()
    };
  }
}
```

### **User Factory**
```typescript
// src/factories/user.factory.ts
import { Factory } from 'factory.ts';
import { Repository } from 'typeorm';
import { BaseFactory } from './base.factory';

export interface UserTestData {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  isActive: boolean;
  roles: string[];
  createdAt: Date;
  updatedAt: Date;
}

export class UserFactory extends BaseFactory<UserTestData> {
  constructor(private userRepository?: Repository<any>) {
    super();
  }

  protected factory = Factory.makeFactory<UserTestData>({
    id: () => this.generateFakeData().uuid(),
    email: () => this.generateFakeData().email(),
    firstName: () => this.generateFakeData().firstName(),
    lastName: () => this.generateFakeData().lastName(),
    isActive: true,
    roles: ['customer'],
    createdAt: () => this.generateFakeData().pastDate(),
    updatedAt: () => new Date()
  });

  // Specific user types
  admin(overrides?: Partial<UserTestData>): UserTestData {
    return this.build({
      roles: ['admin'],
      email: 'admin@example.com',
      ...overrides
    });
  }

  customer(overrides?: Partial<UserTestData>): UserTestData {
    return this.build({
      roles: ['customer'],
      ...overrides
    });
  }

  vendor(overrides?: Partial<UserTestData>): UserTestData {
    return this.build({
      roles: ['vendor'],
      ...overrides
    });
  }

  inactive(overrides?: Partial<UserTestData>): UserTestData {
    return this.build({
      isActive: false,
      ...overrides
    });
  }

  protected async save(entity: UserTestData): Promise<UserTestData> {
    if (!this.userRepository) {
      throw new Error('Repository not provided');
    }
    return await this.userRepository.save(entity);
  }
}
```

### **Product Factory**
```typescript
// src/factories/product.factory.ts
import { Factory } from 'factory.ts';
import { Repository } from 'typeorm';
import { BaseFactory } from './base.factory';

export interface ProductTestData {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  sku: string;
  stockQuantity: number;
  isActive: boolean;
  vendorId: string;
  createdAt: Date;
  updatedAt: Date;
}

export class ProductFactory extends BaseFactory<ProductTestData> {
  constructor(private productRepository?: Repository<any>) {
    super();
  }

  protected factory = Factory.makeFactory<ProductTestData>({
    id: () => this.generateFakeData().uuid(),
    name: () => this.generateFakeData().word(),
    description: () => this.generateFakeData().paragraph(),
    price: () => this.generateFakeData().decimal(10, 500),
    category: () => 'Electronics',
    sku: () => `SKU-${this.generateFakeData().number(10000, 99999)}`,
    stockQuantity: () => this.generateFakeData().number(0, 100),
    isActive: true,
    vendorId: () => this.generateFakeData().uuid(),
    createdAt: () => this.generateFakeData().pastDate(),
    updatedAt: () => new Date()
  });

  // Specific product types
  electronics(overrides?: Partial<ProductTestData>): ProductTestData {
    return this.build({
      category: 'Electronics',
      price: this.generateFakeData().decimal(50, 2000),
      ...overrides
    });
  }

  clothing(overrides?: Partial<ProductTestData>): ProductTestData {
    return this.build({
      category: 'Clothing',
      price: this.generateFakeData().decimal(20, 200),
      ...overrides
    });
  }

  outOfStock(overrides?: Partial<ProductTestData>): ProductTestData {
    return this.build({
      stockQuantity: 0,
      ...overrides
    });
  }

  expensive(overrides?: Partial<ProductTestData>): ProductTestData {
    return this.build({
      price: this.generateFakeData().decimal(1000, 5000),
      ...overrides
    });
  }

  protected async save(entity: ProductTestData): Promise<ProductTestData> {
    if (!this.productRepository) {
      throw new Error('Repository not provided');
    }
    return await this.productRepository.save(entity);
  }
}
```

---

## 🎭 **3. Mock Utilities**

### **Repository Mock**
```typescript
// src/mocks/repository.mock.ts
export class MockRepository<T = any> {
  private entities: Map<string, T> = new Map();
  private idCounter = 1;

  // Basic CRUD operations
  async save(entity: Partial<T>): Promise<T> {
    const id = (entity as any).id || this.idCounter++;
    const savedEntity = { ...entity, id } as T;
    this.entities.set(String(id), savedEntity);
    return savedEntity;
  }

  async findOne(options: any): Promise<T | null> {
    if (options.where?.id) {
      return this.entities.get(String(options.where.id)) || null;
    }
    
    // Simple property matching
    for (const entity of this.entities.values()) {
      let matches = true;
      for (const [key, value] of Object.entries(options.where || {})) {
        if ((entity as any)[key] !== value) {
          matches = false;
          break;
        }
      }
      if (matches) return entity;
    }
    
    return null;
  }

  async find(options?: any): Promise<T[]> {
    let results = Array.from(this.entities.values());
    
    // Apply where conditions
    if (options?.where) {
      results = results.filter(entity => {
        for (const [key, value] of Object.entries(options.where)) {
          if ((entity as any)[key] !== value) {
            return false;
          }
        }
        return true;
      });
    }
    
    // Apply take/limit
    if (options?.take) {
      results = results.slice(0, options.take);
    }
    
    return results;
  }

  async delete(id: string | number): Promise<void> {
    this.entities.delete(String(id));
  }

  async remove(entity: T): Promise<T> {
    const id = (entity as any).id;
    this.entities.delete(String(id));
    return entity;
  }

  async count(options?: any): Promise<number> {
    if (!options?.where) {
      return this.entities.size;
    }
    
    const filtered = await this.find(options);
    return filtered.length;
  }

  // Test utilities
  clear(): void {
    this.entities.clear();
    this.idCounter = 1;
  }

  getAll(): T[] {
    return Array.from(this.entities.values());
  }

  getById(id: string | number): T | undefined {
    return this.entities.get(String(id));
  }

  // Mock query builder
  createQueryBuilder = jest.fn().mockReturnValue({
    where: jest.fn().mockReturnThis(),
    andWhere: jest.fn().mockReturnThis(),
    orWhere: jest.fn().mockReturnThis(),
    orderBy: jest.fn().mockReturnThis(),
    take: jest.fn().mockReturnThis(),
    skip: jest.fn().mockReturnThis(),
    getMany: jest.fn().mockResolvedValue([]),
    getOne: jest.fn().mockResolvedValue(null),
    getCount: jest.fn().mockResolvedValue(0)
  });
}
```

### **Event Mock**
```typescript
// src/mocks/event.mock.ts
import { DomainEvent } from '@ecommerce/rabbitmq-event-utils';

export class MockEventPublisher {
  private publishedEvents: DomainEvent[] = [];

  async publishEvent(event: DomainEvent): Promise<void> {
    this.publishedEvents.push(event);
  }

  async publishBatch(events: DomainEvent[]): Promise<void> {
    this.publishedEvents.push(...events);
  }

  // Test utilities
  getPublishedEvents(): DomainEvent[] {
    return [...this.publishedEvents];
  }

  getEventsOfType<T extends DomainEvent>(eventType: string): T[] {
    return this.publishedEvents.filter(
      event => event.eventType === eventType
    ) as T[];
  }

  getLastEvent(): DomainEvent | undefined {
    return this.publishedEvents[this.publishedEvents.length - 1];
  }

  getLastEventOfType<T extends DomainEvent>(eventType: string): T | undefined {
    const events = this.getEventsOfType<T>(eventType);
    return events[events.length - 1];
  }

  hasEventOfType(eventType: string): boolean {
    return this.publishedEvents.some(event => event.eventType === eventType);
  }

  clear(): void {
    this.publishedEvents = [];
  }

  expectEventToBePublished(eventType: string): void {
    expect(this.hasEventOfType(eventType)).toBe(true);
  }

  expectEventsCount(count: number): void {
    expect(this.publishedEvents).toHaveLength(count);
  }
}

export class MockEventSubscriber {
  private handlers: Map<string, Function[]> = new Map();
  private receivedEvents: DomainEvent[] = [];

  subscribe(eventType: string, handler: Function): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  async simulateEvent(event: DomainEvent): Promise<void> {
    this.receivedEvents.push(event);
    const handlers = this.handlers.get(event.eventType) || [];
    
    for (const handler of handlers) {
      await handler(event);
    }
  }

  getReceivedEvents(): DomainEvent[] {
    return [...this.receivedEvents];
  }

  clear(): void {
    this.receivedEvents = [];
    this.handlers.clear();
  }
}
```

---

## 🛠️ **4. Test Helpers**

### **API Test Helper**
```typescript
// src/helpers/api-test.helper.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';

export class ApiTestHelper {
  private app: INestApplication;
  private authToken?: string;

  constructor(app: INestApplication) {
    this.app = app;
  }

  static async create(moduleMetadata: any): Promise<ApiTestHelper> {
    const moduleFixture: TestingModule = await Test.createTestingModule(moduleMetadata).compile();
    const app = moduleFixture.createNestApplication();
    await app.init();
    return new ApiTestHelper(app);
  }

  setAuthToken(token: string): void {
    this.authToken = token;
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    return headers;
  }

  async get(path: string, query?: Record<string, any>): Promise<request.Test> {
    let req = request(this.app.getHttpServer())
      .get(path)
      .set(this.getHeaders());

    if (query) {
      req = req.query(query);
    }

    return req;
  }

  async post(path: string, body?: any): Promise<request.Test> {
    return request(this.app.getHttpServer())
      .post(path)
      .set(this.getHeaders())
      .send(body);
  }

  async put(path: string, body?: any): Promise<request.Test> {
    return request(this.app.getHttpServer())
      .put(path)
      .set(this.getHeaders())
      .send(body);
  }

  async patch(path: string, body?: any): Promise<request.Test> {
    return request(this.app.getHttpServer())
      .patch(path)
      .set(this.getHeaders())
      .send(body);
  }

  async delete(path: string): Promise<request.Test> {
    return request(this.app.getHttpServer())
      .delete(path)
      .set(this.getHeaders());
  }

  // Authentication helpers
  async login(credentials: { email: string; password: string }): Promise<string> {
    const response = await this.post('/auth/login', credentials);
    expect(response.status).toBe(200);
    
    const token = response.body.data.accessToken;
    this.setAuthToken(token);
    return token;
  }

  // Common assertions
  expectSuccess(response: request.Response, expectedStatus = 200): void {
    expect(response.status).toBe(expectedStatus);
    expect(response.body.success).toBe(true);
  }

  expectError(response: request.Response, expectedStatus: number, errorCode?: string): void {
    expect(response.status).toBe(expectedStatus);
    expect(response.body.success).toBe(false);
    
    if (errorCode) {
      expect(response.body.errorCode).toBe(errorCode);
    }
  }

  expectValidationError(response: request.Response): void {
    this.expectError(response, 400, 'VALIDATION_ERROR');
    expect(response.body.metadata?.validationErrors).toBeDefined();
  }

  expectUnauthorized(response: request.Response): void {
    this.expectError(response, 401);
  }

  expectForbidden(response: request.Response): void {
    this.expectError(response, 403);
  }

  expectNotFound(response: request.Response): void {
    this.expectError(response, 404);
  }

  async close(): Promise<void> {
    await this.app.close();
  }
}
```

### **Integration Test Helper**
```typescript
// src/helpers/integration-test.helper.ts
import { TestDatabaseService } from '../database/test-database.service';
import { DatabaseCleaner } from '../database/database-cleaner';
import { MockEventPublisher } from '../mocks/event.mock';

export class IntegrationTestHelper {
  private databaseService: TestDatabaseService;
  private databaseCleaner: DatabaseCleaner;
  private eventPublisher: MockEventPublisher;

  constructor() {
    this.databaseService = TestDatabaseService.getInstance();
    this.eventPublisher = new MockEventPublisher();
  }

  async setupDatabase(): Promise<void> {
    const dataSource = await this.databaseService.setupTestDatabase();
    this.databaseCleaner = new DatabaseCleaner(dataSource);
  }

  async cleanDatabase(): Promise<void> {
    await this.databaseCleaner.cleanAll();
  }

  async teardownDatabase(): Promise<void> {
    await this.databaseService.closeConnection();
  }

  getEventPublisher(): MockEventPublisher {
    return this.eventPublisher;
  }

  async getRepository<T>(entity: any) {
    return await this.databaseService.getRepository<T>(entity);
  }

  // Lifecycle helpers
  async beforeEach(): Promise<void> {
    await this.cleanDatabase();
    this.eventPublisher.clear();
  }

  async afterAll(): Promise<void> {
    await this.teardownDatabase();
  }
}
```

---

## 📤 **5. Main Export File**

```typescript
// src/index.ts
// Database utilities
export * from './database';

// Factories
export * from './factories';

// Mocks
export * from './mocks';

// Helpers
export * from './helpers';

// Performance testing
export * from './performance';

// Test module
export { TestingModule } from './testing.module';
```

### **Testing Module**
```typescript
// src/testing.module.ts
import { Global, Module } from '@nestjs/common';
import { TestDatabaseService } from './database/test-database.service';
import { DatabaseCleaner } from './database/database-cleaner';
import { IntegrationTestHelper } from './helpers/integration-test.helper';

@Global()
@Module({
  providers: [
    TestDatabaseService,
    DatabaseCleaner,
    IntegrationTestHelper
  ],
  exports: [
    TestDatabaseService,
    DatabaseCleaner,
    IntegrationTestHelper
  ]
})
export class TestingModule {}
```

---

## 🧪 **Usage Examples**

### **Unit Test Example**
```typescript
// Example usage in service test
import { UserFactory, MockRepository } from '@ecommerce/testing-utils';

describe('UserService', () => {
  let userService: UserService;
  let userRepository: MockRepository<User>;
  let userFactory: UserFactory;

  beforeEach(() => {
    userRepository = new MockRepository<User>();
    userFactory = new UserFactory();
    userService = new UserService(userRepository as any);
  });

  it('should create user', async () => {
    const userData = userFactory.build();
    const result = await userService.create(userData);
    
    expect(result).toBeDefined();
    expect(userRepository.getAll()).toHaveLength(1);
  });
});
```

### **Integration Test Example**
```typescript
// Example usage in integration test
import { IntegrationTestHelper, UserFactory } from '@ecommerce/testing-utils';

describe('User API Integration', () => {
  let helper: IntegrationTestHelper;
  let userFactory: UserFactory;

  beforeAll(async () => {
    helper = new IntegrationTestHelper();
    await helper.setupDatabase();
  });

  beforeEach(async () => {
    await helper.beforeEach();
    const userRepo = await helper.getRepository(User);
    userFactory = new UserFactory(userRepo);
  });

  afterAll(async () => {
    await helper.afterAll();
  });

  it('should get user profile', async () => {
    const user = await userFactory.create();
    // Test implementation...
  });
});
```

---

## ✅ **Validation Steps**

1. **Build the package**: `npm run build`
2. **Run tests**: `npm run test`
3. **Test database utilities** with containers
4. **Verify mock functionality** with sample tests

---

## 🎉 **Completion**

Congratulations! You've built comprehensive shared libraries that provide:

- ✅ **Consistent logging and error handling** across all services
- ✅ **Secure authentication and authorization** utilities
- ✅ **Reliable event-driven messaging** with outbox pattern
- ✅ **Comprehensive testing tools** for all types of tests

These libraries will dramatically reduce development time and ensure consistency across your microservices platform! 🚀

---

## 🔗 **Next Step**

With shared libraries complete, you're ready to move to **Task 3: User Service Implementation** where you'll use these utilities to build your first microservice!