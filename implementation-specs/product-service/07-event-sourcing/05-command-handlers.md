# Command Handlers

## 1. Overview

Command handlers are responsible for validating commands and converting them into events. They form the write side of the CQRS pattern and enforce business rules before state changes are recorded as events.

## 2. Command Pattern

Commands represent user intentions and are named in the imperative form. They follow this structure:

```typescript
interface Command {
  commandId: string;     // UUID for the command
  commandType: string;   // Type of command (class name)
  timestamp: string;     // ISO 8601 timestamp
  userId: string;        // User who initiated the command
  correlationId: string; // For tracing related operations
}

// Example of a specific command
interface CreateProductCommand extends Command {
  data: {
    name: string;
    description: string;
    brand: string;
    // ... other product properties
  };
}
```

## 3. Command Handler Interface

All command handlers implement a common interface:

```typescript
interface CommandHandler<T extends Command> {
  // Command type this handler can process
  commandType: string;
  
  // Execute the command and return generated events
  execute(command: T): Promise<DomainEvent<any>[]>;
  
  // Validate the command
  validate(command: T): Promise<ValidationResult>;
}
```

## 4. Product Command Handlers

### 4.1. CreateProductCommandHandler

**Command:** `CreateProductCommand`  
**Generated Events:** `ProductCreated`

```typescript
class CreateProductCommandHandler implements CommandHandler<CreateProductCommand> {
  commandType = 'CreateProductCommand';
  
  constructor(
    private readonly eventStore: EventStore,
    private readonly productRepository: ProductRepository,
    private readonly categoryService: CategoryService
  ) {}
  
  async validate(command: CreateProductCommand): Promise<ValidationResult> {
    const { name, brand, categoryIds } = command.data;
    
    // Check for duplicate product name within brand
    const existingProduct = await this.productRepository.findByNameAndBrand(name, brand);
    if (existingProduct) {
      return {
        isValid: false,
        errors: ['A product with this name already exists for this brand']
      };
    }
    
    // Validate categories exist
    if (categoryIds && categoryIds.length > 0) {
      const validCategories = await this.categoryService.validateCategories(categoryIds);
      if (!validCategories.isValid) {
        return {
          isValid: false,
          errors: [`Invalid categories: ${validCategories.invalidIds.join(', ')}`]
        };
      }
    }
    
    return { isValid: true };
  }
  
  async execute(command: CreateProductCommand): Promise<DomainEvent<any>[]> {
    // Validate command
    const validationResult = await this.validate(command);
    if (!validationResult.isValid) {
      throw new ValidationError(validationResult.errors.join(', '));
    }
    
    // Generate productId
    const productId = uuid();
    
    // Create ProductCreated event
    const event: DomainEvent<ProductCreatedData> = {
      eventId: uuid(),
      entityId: productId,
      eventType: 'ProductCreated',
      eventTime: new Date().toISOString(),
      version: '1.0',
      userId: command.userId,
      correlationId: command.correlationId,
      data: {
        name: command.data.name,
        description: command.data.description,
        brand: command.data.brand,
        status: 'DRAFT', // Initial status
        sku: command.data.sku,
        tags: command.data.tags || [],
        attributes: command.data.attributes || {},
        metadata: command.data.metadata || {},
        categoryIds: command.data.categoryIds || [],
        createdBy: command.userId
      }
    };
    
    // Store event
    await this.eventStore.appendEvent(
      'Product',
      productId,
      event.eventType,
      event.data,
      command.userId,
      command.correlationId
    );
    
    return [event];
  }
}
```

### 4.2. UpdateProductCommandHandler

**Command:** `UpdateProductCommand`  
**Generated Events:** `ProductBasicInfoUpdated`, `ProductCategoriesUpdated`

```typescript
class UpdateProductCommandHandler implements CommandHandler<UpdateProductCommand> {
  commandType = 'UpdateProductCommand';
  
  constructor(
    private readonly eventStore: EventStore,
    private readonly productService: ProductService,
    private readonly categoryService: CategoryService
  ) {}
  
  async validate(command: UpdateProductCommand): Promise<ValidationResult> {
    const { productId, data } = command;
    
    // Check product exists
    const product = await this.productService.getProductById(productId);
    if (!product) {
      return {
        isValid: false,
        errors: [`Product with ID ${productId} not found`]
      };
    }
    
    // Validate categories if provided
    if (data.categoryIds) {
      const validCategories = await this.categoryService.validateCategories(data.categoryIds);
      if (!validCategories.isValid) {
        return {
          isValid: false,
          errors: [`Invalid categories: ${validCategories.invalidIds.join(', ')}`]
        };
      }
    }
    
    return { isValid: true };
  }
  
  async execute(command: UpdateProductCommand): Promise<DomainEvent<any>[]> {
    // Validate command
    const validationResult = await this.validate(command);
    if (!validationResult.isValid) {
      throw new ValidationError(validationResult.errors.join(', '));
    }
    
    const events: DomainEvent<any>[] = [];
    const { productId, data } = command;
    
    // Get current product state
    const product = await this.productService.getProductById(productId);
    
    // Generate ProductBasicInfoUpdated event if basic info changes
    if (
      data.name !== undefined || 
      data.description !== undefined || 
      data.brand !== undefined ||
      data.sku !== undefined ||
      data.tags !== undefined ||
      data.attributes !== undefined ||
      data.metadata !== undefined
    ) {
      const basicInfoEvent: DomainEvent<ProductBasicInfoUpdatedData> = {
        eventId: uuid(),
        entityId: productId,
        eventType: 'ProductBasicInfoUpdated',
        eventTime: new Date().toISOString(),
        version: '1.0',
        userId: command.userId,
        correlationId: command.correlationId,
        data: {
          name: data.name,
          description: data.description,
          brand: data.brand,
          sku: data.sku,
          tags: data.tags,
          attributes: data.attributes,
          metadata: data.metadata,
          updatedBy: command.userId
        }
      };
      
      // Remove undefined fields
      Object.keys(basicInfoEvent.data).forEach(key => {
        if (basicInfoEvent.data[key] === undefined) {
          delete basicInfoEvent.data[key];
        }
      });
      
      // Only add event if there are actual changes
      if (Object.keys(basicInfoEvent.data).length > 1) { // More than just updatedBy
        events.push(basicInfoEvent);
        
        await this.eventStore.appendEvent(
          'Product',
          productId,
          basicInfoEvent.eventType,
          basicInfoEvent.data,
          command.userId,
          command.correlationId,
          product.version
        );
      }
    }
    
    // Generate ProductCategoriesUpdated event if categories change
    if (data.categoryIds !== undefined) {
      const currentCategoryIds = product.categoryIds || [];
      const newCategoryIds = data.categoryIds || [];
      
      // Calculate added and removed categories
      const addedCategoryIds = newCategoryIds.filter(id => !currentCategoryIds.includes(id));
      const removedCategoryIds = currentCategoryIds.filter(id => !newCategoryIds.includes(id));
      
      // Only create event if categories actually changed
      if (addedCategoryIds.length > 0 || removedCategoryIds.length > 0) {
        const categoriesEvent: DomainEvent<ProductCategoriesUpdatedData> = {
          eventId: uuid(),
          entityId: productId,
          eventType: 'ProductCategoriesUpdated',
          eventTime: new Date().toISOString(),
          version: '1.0',
          userId: command.userId,
          correlationId: command.correlationId,
          data: {
            addedCategoryIds,
            removedCategoryIds,
            updatedBy: command.userId
          }
        };
        
        events.push(categoriesEvent);
        
        await this.eventStore.appendEvent(
          'Product',
          productId,
          categoriesEvent.eventType,
          categoriesEvent.data,
          command.userId,
          command.correlationId,
          product.version + (events.length - 1) // Increment version for each event
        );
      }
    }
    
    return events;
  }
}
```

## 5. Command Bus Implementation

The command bus is responsible for routing commands to their respective handlers:

```typescript
class CommandBus {
  private handlers: Map<string, CommandHandler<any>> = new Map();
  
  registerHandler(handler: CommandHandler<any>): void {
    this.handlers.set(handler.commandType, handler);
  }
  
  async dispatch<T extends Command>(command: T): Promise<DomainEvent<any>[]> {
    const handler = this.handlers.get(command.commandType);
    
    if (!handler) {
      throw new Error(`No handler registered for command type ${command.commandType}`);
    }
    
    return handler.execute(command);
  }
}
```

## 6. Integration with API Controllers

API controllers receive HTTP requests and translate them into commands:

```typescript
@Controller('products')
export class ProductController {
  constructor(private readonly commandBus: CommandBus) {}
  
  @Post()
  async createProduct(@Body() dto: CreateProductDto, @User() user: UserInfo): Promise<any> {
    const command: CreateProductCommand = {
      commandId: uuid(),
      commandType: 'CreateProductCommand',
      timestamp: new Date().toISOString(),
      userId: user.id,
      correlationId: uuid(), // Or from request headers if available
      data: dto
    };
    
    try {
      const events = await this.commandBus.dispatch(command);
      
      // Return the ID of the created product
      return {
        id: events[0].entityId, // ProductCreated event contains the new ID
        status: 'created'
      };
    } catch (error) {
      // Handle errors appropriately
      if (error instanceof ValidationError) {
        throw new BadRequestException(error.message);
      }
      throw error;
    }
  }
  
  // Other controller methods...
}
```

## 7. Best Practices

1. **Keep commands simple**: Commands should represent a single intention
2. **Validate early**: Perform all validations before generating events
3. **Idempotency**: Design commands to be idempotent where possible
4. **Handle concurrency**: Use optimistic concurrency control via expected versions
5. **Transaction boundaries**: Ensure atomicity when multiple events must be stored together
6. **Logging**: Log all commands for audit and debugging purposes

## 8. References

- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Command Pattern](https://en.wikipedia.org/wiki/Command_pattern)
- [NestJS Documentation](https://docs.nestjs.com/)