# Testing Strategy for Event Sourcing

## 1. Overview

Testing an event-sourced system requires special approaches that differ from traditional systems. This document outlines the testing strategy for the Product Service event sourcing implementation, addressing the unique challenges and requirements of this architectural pattern.

## 2. Testing Layers

### 2.1. Unit Testing

#### Command Handlers

- **Test Focus**: Business logic, validation, and event generation
- **Approach**:
  - Mock event store and repositories
  - Verify events are correctly generated for valid commands
  - Verify validation errors are thrown for invalid commands
  - Test optimistic concurrency control

Example:

```typescript
describe('CreateProductCommandHandler', () => {
  let handler: CreateProductCommandHandler;
  let eventStoreMock: MockType<EventStore>;
  let productRepositoryMock: MockType<ProductRepository>;
  let categoryServiceMock: MockType<CategoryService>;

  beforeEach(() => {
    eventStoreMock = {
      appendEvent: jest.fn().mockResolvedValue(1),
      getEvents: jest.fn().mockResolvedValue([]),
    };
    productRepositoryMock = {
      findByNameAndBrand: jest.fn().mockResolvedValue(null),
    };
    categoryServiceMock = {
      validateCategories: jest.fn().mockResolvedValue({ isValid: true, invalidIds: [] }),
    };

    handler = new CreateProductCommandHandler(
      eventStoreMock,
      productRepositoryMock,
      categoryServiceMock
    );
  });

  it('should generate ProductCreated event for valid command', async () => {
    // Arrange
    const command = createValidProductCommand();

    // Act
    const events = await handler.execute(command);

    // Assert
    expect(events).toHaveLength(1);
    expect(events[0].eventType).toBe('ProductCreated');
    expect(events[0].data.name).toBe(command.data.name);
    expect(eventStoreMock.appendEvent).toHaveBeenCalledTimes(1);
  });

  it('should throw validation error for duplicate product name', async () => {
    // Arrange
    productRepositoryMock.findByNameAndBrand.mockResolvedValue({ id: 'existing-id' });
    const command = createValidProductCommand();

    // Act & Assert
    await expect(handler.execute(command)).rejects.toThrow(ValidationError);
    expect(eventStoreMock.appendEvent).not.toHaveBeenCalled();
  });
});
```

#### Event Handlers

- **Test Focus**: Projection updates based on events
- **Approach**:
  - Mock projection repositories
  - Verify repositories are updated correctly for each event

Example:

```typescript
describe('ProductCatalogProjection', () => {
  let projection: ProductCatalogProjection;
  let repositoryMock: MockType<ProductCatalogRepository>;

  beforeEach(() => {
    repositoryMock = {
      create: jest.fn().mockResolvedValue(undefined),
      update: jest.fn().mockResolvedValue(undefined),
      findById: jest.fn(),
    };

    projection = new ProductCatalogProjection(repositoryMock);
  });

  it('should create product catalog item on ProductCreated event', async () => {
    // Arrange
    const event = createProductCreatedEvent();

    // Act
    await projection.handleProductCreated(event);

    // Assert
    expect(repositoryMock.create).toHaveBeenCalledTimes(1);
    const createdItem = repositoryMock.create.mock.calls[0][0];
    expect(createdItem.id).toBe(event.entityId);
    expect(createdItem.name).toBe(event.data.name);
  });

  it('should update product catalog item on ProductPriceUpdated event', async () => {
    // Arrange
    const productId = 'test-product-id';
    const mockProduct = createMockProductCatalogItem(productId);
    repositoryMock.findById.mockResolvedValue(mockProduct);
    
    const event = createProductPriceUpdatedEvent(productId);

    // Act
    await projection.handleProductPriceUpdated(event);

    // Assert
    expect(repositoryMock.update).toHaveBeenCalledTimes(1);
    const updatedItem = repositoryMock.update.mock.calls[0][0];
    expect(updatedItem.price).toEqual(event.data.newPrice);
  });
});
```

#### Domain Models

- **Test Focus**: Event application and state reconstruction
- **Approach**:
  - Test applying each event type to a product entity
  - Verify the entity's state is correctly updated

Example:

```typescript
describe('Product Entity', () => {
  it('should apply ProductCreated event correctly', () => {
    // Arrange
    const product = new Product();
    const event = createProductCreatedEvent();

    // Act
    product.apply(event);

    // Assert
    expect(product.id).toBe(event.entityId);
    expect(product.name).toBe(event.data.name);
    expect(product.status).toBe(event.data.status);
    expect(product.version).toBe(1);
  });

  it('should apply multiple events in sequence', () => {
    // Arrange
    const product = new Product();
    const events = [
      createProductCreatedEvent(),
      createProductBasicInfoUpdatedEvent(),
      createProductStatusChangedEvent()
    ];

    // Act
    events.forEach(event => product.apply(event));

    // Assert
    expect(product.id).toBe(events[0].entityId);
    expect(product.name).toBe(events[1].data.name);
    expect(product.status).toBe(events[2].data.newStatus);
    expect(product.version).toBe(3);
  });
});
```

### 2.2. Integration Testing

#### Event Store

- **Test Focus**: Event persistence and retrieval
- **Approach**:
  - Use a local DynamoDB instance for testing
  - Test event store API methods
  - Verify optimistic concurrency control works

Example:

```typescript
describe('DynamoDBEventStore Integration', () => {
  let eventStore: DynamoDBEventStore;
  let dynamoDbLocal: any;

  beforeAll(async () => {
    dynamoDbLocal = await startLocalDynamoDB();
    const client = new DynamoDBClient({
      endpoint: 'http://localhost:8000',
      region: 'local',
      credentials: { accessKeyId: 'test', secretAccessKey: 'test' }
    });
    eventStore = new DynamoDBEventStore(client, 'TestEvents', 'TestSnapshots');
    await createTestTables(client);
  });

  afterAll(async () => {
    await stopLocalDynamoDB(dynamoDbLocal);
  });

  it('should append and retrieve events', async () => {
    // Arrange
    const entityId = uuid();
    const eventData = { name: 'Test Product', status: 'DRAFT' };

    // Act - Append event
    const seq = await eventStore.appendEvent(
      'Product',
      entityId,
      'ProductCreated',
      eventData,
      'test-user',
      'correlation-id'
    );

    // Act - Retrieve events
    const events = await eventStore.getEvents(entityId);

    // Assert
    expect(seq).toBe(1);
    expect(events).toHaveLength(1);
    expect(events[0].entityId).toBe(entityId);
    expect(events[0].eventType).toBe('ProductCreated');
    expect(JSON.parse(events[0].eventData)).toEqual(eventData);
  });

  it('should enforce optimistic concurrency control', async () => {
    // Arrange
    const entityId = uuid();
    
    // Act - Append first event
    await eventStore.appendEvent(
      'Product',
      entityId,
      'ProductCreated',
      { name: 'Test Product' },
      'test-user',
      'correlation-id'
    );

    // Act & Assert - Try to append with wrong expected version
    await expect(
      eventStore.appendEvent(
        'Product',
        entityId,
        'ProductUpdated',
        { name: 'Updated Name' },
        'test-user',
        'correlation-id',
        2 // Wrong version
      )
    ).rejects.toThrow(ConcurrencyError);
  });
});
```

#### Command/Event Flow

- **Test Focus**: End-to-end command handling and event processing
- **Approach**:
  - Test command handler -> event store -> event handler flow
  - Verify projections are updated correctly after command execution

Example:

```typescript
describe('Product Command/Event Flow', () => {
  let commandBus: CommandBus;
  let eventStore: EventStore;
  let projection: ProductCatalogProjection;
  let projectionRepo: ProductCatalogRepository;

  beforeEach(async () => {
    // Setup dependencies with test implementations
    eventStore = new InMemoryEventStore();
    projectionRepo = new InMemoryProductCatalogRepository();
    projection = new ProductCatalogProjection(projectionRepo);
    
    // Register command handlers
    commandBus = new CommandBus();
    commandBus.registerHandler(
      new CreateProductCommandHandler(
        eventStore,
        new InMemoryProductRepository(),
        new MockCategoryService()
      )
    );
    
    // Setup event handlers
    const eventBus = new EventBus();
    eventBus.subscribe('ProductCreated', (event) => projection.handleProductCreated(event));
    
    // Connect event store to event bus
    const synchronizer = new EventStoreSynchronizer(eventStore, eventBus);
    await synchronizer.start();
  });

  it('should update projection after command execution', async () => {
    // Arrange
    const command = createValidProductCommand();
    
    // Act
    const events = await commandBus.dispatch(command);
    const productId = events[0].entityId;
    
    // Wait for projections to update
    await new Promise(resolve => setTimeout(resolve, 50));
    
    // Assert
    const product = await projectionRepo.findById(productId);
    expect(product).toBeDefined();
    expect(product!.name).toBe(command.data.name);
  });
});
```

### 2.3. System Testing

- **Test Focus**: API endpoints, command handling, and projection querying
- **Approach**:
  - Use supertest or similar for HTTP API testing
  - Test complete flows from API request to response

Example:

```typescript
describe('Product API with Event Sourcing', () => {
  let app: INestApplication;
  let eventStore: EventStore;

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(EventStore)
      .useValue(new InMemoryEventStore())
      .compile();

    app = moduleRef.createNestApplication();
    await app.init();
    
    eventStore = moduleRef.get<EventStore>(EventStore);
  });

  afterAll(async () => {
    await app.close();
  });

  it('should create a product and return its details', async () => {
    // Arrange
    const createProductDto = {
      name: 'Test Product',
      description: 'Test Description',
      brand: 'Test Brand',
      sku: 'TEST-SKU-123',
      status: 'DRAFT',
    };

    // Act - Create product
    const createResponse = await request(app.getHttpServer())
      .post('/products')
      .send(createProductDto)
      .expect(201);

    const productId = createResponse.body.id;

    // Act - Get product details
    const getResponse = await request(app.getHttpServer())
      .get(`/products/${productId}`)
      .expect(200);

    // Assert
    expect(getResponse.body.name).toBe(createProductDto.name);
    expect(getResponse.body.description).toBe(createProductDto.description);
    
    // Verify events in event store
    const events = await eventStore.getEvents(productId);
    expect(events).toHaveLength(1);
    expect(events[0].eventType).toBe('ProductCreated');
  });

  it('should update a product and record the event', async () => {
    // Arrange - Create a product first
    const createResponse = await request(app.getHttpServer())
      .post('/products')
      .send({ name: 'Product To Update', brand: 'Test Brand', sku: 'UPDATE-SKU' })
      .expect(201);

    const productId = createResponse.body.id;
    
    // Act - Update the product
    const updateDto = { name: 'Updated Product Name' };
    await request(app.getHttpServer())
      .put(`/products/${productId}`)
      .send(updateDto)
      .expect(200);

    // Assert - Check via API
    const getResponse = await request(app.getHttpServer())
      .get(`/products/${productId}`)
      .expect(200);
    
    expect(getResponse.body.name).toBe(updateDto.name);
    
    // Verify events in event store
    const events = await eventStore.getEvents(productId);
    expect(events).toHaveLength(2);
    expect(events[0].eventType).toBe('ProductCreated');
    expect(events[1].eventType).toBe('ProductBasicInfoUpdated');
  });
});
```

## 3. Event Sourcing Specific Testing Strategies

### 3.1. Event Replay Testing

- **Purpose**: Verify that replaying events recreates the correct state
- **Approach**: 
  - Generate a sequence of events
  - Rebuild state by applying events
  - Compare with expected state

Example:

```typescript
describe('Event Replay', () => {
  it('should rebuild product state correctly from events', async () => {
    // Arrange
    const productId = uuid();
    const events = [
      createEvent('ProductCreated', productId, { name: 'Original Name', status: 'DRAFT' }),
      createEvent('ProductBasicInfoUpdated', productId, { name: 'Updated Name' }),
      createEvent('ProductStatusChanged', productId, { oldStatus: 'DRAFT', newStatus: 'ACTIVE' }),
      createEvent('ProductPriceUpdated', productId, { 
        newPrice: { amount: 99.99, currency: 'USD' } 
      }),
    ];
    
    // Act
    const product = new Product();
    events.forEach(event => product.apply(event));
    
    // Assert
    expect(product.id).toBe(productId);
    expect(product.name).toBe('Updated Name');
    expect(product.status).toBe('ACTIVE');
    expect(product.price.amount).toBe(99.99);
    expect(product.price.currency).toBe('USD');
    expect(product.version).toBe(4);
  });
});
```

### 3.2. Snapshot Testing

- **Purpose**: Verify that snapshots are created and restored correctly
- **Approach**:
  - Create multiple events
  - Generate a snapshot
  - Verify state can be rebuilt from snapshot + newer events

Example:

```typescript
describe('Product Snapshots', () => {
  let eventStore: EventStore;
  let snapshotStore: SnapshotStore;
  
  beforeEach(() => {
    eventStore = new InMemoryEventStore();
    snapshotStore = new InMemorySnapshotStore();
  });
  
  it('should create and use snapshots correctly', async () => {
    // Arrange
    const productId = uuid();
    
    // Add events to event store
    await addTestEvents(eventStore, productId, 20);
    
    // Act - Create snapshot after 10 events
    const product = new Product();
    const events = await eventStore.getEvents(productId);
    
    // Apply first 10 events
    events.slice(0, 10).forEach(event => product.apply(event));
    
    // Create snapshot
    await snapshotStore.saveSnapshot(productId, 10, product);
    
    // Load snapshot and apply remaining events
    const snapshot = await snapshotStore.getLatestSnapshot(productId);
    const restoredProduct = snapshot.data;
    
    events.slice(10).forEach(event => restoredProduct.apply(event));
    
    // Assert
    expect(restoredProduct.version).toBe(20);
    
    // Rebuild from scratch as comparison
    const fullProduct = new Product();
    events.forEach(event => fullProduct.apply(event));
    
    // Compare states
    expect(restoredProduct).toEqual(fullProduct);
  });
});
```

### 3.3. Temporal Testing

- **Purpose**: Verify that state can be reconstructed for any point in time
- **Approach**:
  - Create a sequence of timestamped events
  - Retrieve events up to a specific time
  - Verify state is correct for that time

Example:

```typescript
describe('Temporal Queries', () => {
  let eventStore: EventStore;
  
  beforeEach(async () => {
    eventStore = new InMemoryEventStore();
    
    // Create a sequence of events with increasing timestamps
    const productId = uuid();
    let time = new Date('2023-01-01T00:00:00Z');
    
    await eventStore.appendEvent(
      'Product', productId, 'ProductCreated',
      { name: 'Original Name', status: 'DRAFT' },
      'test-user', 'correlation-id', undefined, time.toISOString()
    );
    
    time = new Date(time.getTime() + 86400000); // +1 day
    await eventStore.appendEvent(
      'Product', productId, 'ProductBasicInfoUpdated',
      { name: 'Updated Name' },
      'test-user', 'correlation-id', 1, time.toISOString()
    );
    
    time = new Date(time.getTime() + 86400000); // +1 day
    await eventStore.appendEvent(
      'Product', productId, 'ProductStatusChanged',
      { oldStatus: 'DRAFT', newStatus: 'ACTIVE' },
      'test-user', 'correlation-id', 2, time.toISOString()
    );
  });
  
  it('should reconstruct state at a specific point in time', async () => {
    // Arrange
    const targetTime = new Date('2023-01-02T12:00:00Z');
    
    // Act - Find all events before target time
    const events = await eventStore.getEventsByTime(undefined, targetTime.toISOString());
    
    // Rebuild state
    const product = new Product();
    events.forEach(event => product.apply(event));
    
    // Assert
    expect(product.name).toBe('Updated Name');
    expect(product.status).toBe('DRAFT'); // Status change event was after target time
  });
});
```

### 3.4. Idempotency Testing

- **Purpose**: Verify handling the same event multiple times is safe
- **Approach**:
  - Process the same event multiple times
  - Verify the final state is correct

Example:

```typescript
describe('Projection Idempotency', () => {
  let projection: ProductCatalogProjection;
  let repository: InMemoryProductCatalogRepository;
  
  beforeEach(() => {
    repository = new InMemoryProductCatalogRepository();
    projection = new ProductCatalogProjection(repository);
  });
  
  it('should handle the same event multiple times idempotently', async () => {
    // Arrange
    const event = createProductCreatedEvent();
    
    // Act - Process the same event multiple times
    await projection.handleProductCreated(event);
    await projection.handleProductCreated(event);
    await projection.handleProductCreated(event);
    
    // Assert
    const products = await repository.findAll();
    expect(products).toHaveLength(1);
    expect(products[0].id).toBe(event.entityId);
  });
});
```

## 4. Test Data Management

### 4.1. Event Generation Helpers

Create helper functions to generate standard events for testing:

```typescript
function createProductCreatedEvent(
  entityId = uuid(),
  overrides = {}
): DomainEvent<ProductCreatedData> {
  return {
    eventId: uuid(),
    entityId,
    eventType: 'ProductCreated',
    eventTime: new Date().toISOString(),
    version: '1.0',
    userId: 'test-user',
    correlationId: 'test-correlation',
    data: {
      name: 'Test Product',
      description: 'Test Description',
      brand: 'Test Brand',
      status: 'DRAFT',
      sku: 'TEST-SKU',
      tags: [],
      attributes: {},
      metadata: {},
      categoryIds: [],
      createdBy: 'test-user',
      ...overrides
    }
  };
}
```

### 4.2. Command Generation Helpers

Create helper functions to generate standard commands for testing:

```typescript
function createValidProductCommand(
  overrides = {}
): CreateProductCommand {
  return {
    commandId: uuid(),
    commandType: 'CreateProductCommand',
    timestamp: new Date().toISOString(),
    userId: 'test-user',
    correlationId: 'test-correlation',
    data: {
      name: 'Test Product',
      description: 'Test Description',
      brand: 'Test Brand',
      sku: 'TEST-SKU',
      tags: [],
      attributes: {},
      ...overrides
    }
  };
}
```

## 5. Test Infrastructure

### 5.1. In-Memory Implementations

Create in-memory implementations of key interfaces for testing:

```typescript
class InMemoryEventStore implements EventStore {
  private events: Map<string, DomainEvent<any>[]> = new Map();
  
  async appendEvent<T>(
    aggregateType: string,
    entityId: string,
    eventType: string,
    eventData: T,
    userId: string,
    correlationId: string,
    expectedVersion?: number
  ): Promise<number> {
    const entityEvents = this.events.get(entityId) || [];
    
    // Check version if expected version provided
    if (expectedVersion !== undefined && entityEvents.length !== expectedVersion) {
      throw new ConcurrencyError(
        `Expected version ${expectedVersion}, got ${entityEvents.length}`
      );
    }
    
    const newEvent = {
      eventId: uuid(),
      entityId,
      aggregateType,
      eventType,
      eventTime: new Date().toISOString(),
      eventData: JSON.stringify(eventData),
      version: '1.0',
      userId,
      correlationId,
      sequenceNumber: entityEvents.length + 1
    };
    
    entityEvents.push(newEvent);
    this.events.set(entityId, entityEvents);
    
    return entityEvents.length;
  }
  
  async getEvents(
    entityId: string,
    fromSequence?: number,
    toSequence?: number
  ): Promise<DomainEvent<any>[]> {
    const entityEvents = this.events.get(entityId) || [];
    
    let filteredEvents = entityEvents;
    
    if (fromSequence !== undefined) {
      filteredEvents = filteredEvents.filter(e => e.sequenceNumber >= fromSequence);
    }
    
    if (toSequence !== undefined) {
      filteredEvents = filteredEvents.filter(e => e.sequenceNumber <= toSequence);
    }
    
    return filteredEvents;
  }
  
  // Other methods...
}
```

## 6. References

- [Testing Event Sourcing Applications](https://docs.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)
- [NestJS Testing](https://docs.nestjs.com/fundamentals/testing)
- [Jest Documentation](https://jestjs.io/docs/getting-started)