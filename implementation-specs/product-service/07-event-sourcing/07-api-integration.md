# API Integration with Event Sourcing

## 1. Overview

This document outlines how the existing Product Service APIs will be integrated with the new event sourcing implementation. The goal is to maintain backward compatibility for API consumers while leveraging the benefits of event sourcing internally.

## 2. API Architecture

The enhanced Product Service architecture follows these principles:

1. **Command/Query Separation**: Clear distinction between operations that modify state (commands) and those that read state (queries)
2. **Event-Driven**: State changes are captured as events
3. **Backward Compatibility**: Existing APIs continue to function with the same contracts
4. **Gradual Migration**: Allows incremental transition to event sourcing without disrupting service

## 3. API Layer Transformation

### 3.1. Command APIs

Command APIs that modify state will be transformed to:

1. Validate input and permissions
2. Transform API requests into commands
3. Send commands to the command bus
4. Process results and return appropriate responses

### 3.2. Query APIs

Query APIs will be transformed to:

1. Validate query parameters and permissions
2. Fetch data from the appropriate projection (not the event store)
3. Transform projection data to API response format
4. Return results with appropriate caching headers

## 4. API Endpoint Implementations

### 4.1. CREATE Operations

#### POST /products

**Before (Direct Repository Access):**

```typescript
@Post()
async createProduct(
  @Body() createProductDto: CreateProductDto,
  @User() user: UserInfo
): Promise<ProductResponseDto> {
  const product = await this.productService.createProduct(createProductDto);
  return this.productMapper.toResponseDto(product);
}
```

**After (Command-Based):**

```typescript
@Post()
async createProduct(
  @Body() createProductDto: CreateProductDto,
  @User() user: UserInfo
): Promise<ProductResponseDto> {
  // Create command from DTO
  const command: CreateProductCommand = {
    commandId: uuid(),
    commandType: 'CreateProductCommand',
    timestamp: new Date().toISOString(),
    userId: user.id,
    correlationId: uuid(), // Or from request headers
    data: createProductDto
  };
  
  // Dispatch command
  const events = await this.commandBus.dispatch(command);
  
  // Get generated productId from the ProductCreated event
  const productId = events[0].entityId;
  
  // Fetch the product from the read model
  const product = await this.productQueryService.findProductById(productId);
  
  // Return API response
  return this.productMapper.toResponseDto(product);
}
```

### 4.2. UPDATE Operations

#### PUT /products/{id}

**Before (Direct Repository Access):**

```typescript
@Put(':id')
async updateProduct(
  @Param('id') id: string,
  @Body() updateProductDto: UpdateProductDto,
  @User() user: UserInfo
): Promise<ProductResponseDto> {
  const product = await this.productService.updateProduct(id, updateProductDto);
  return this.productMapper.toResponseDto(product);
}
```

**After (Command-Based):**

```typescript
@Put(':id')
async updateProduct(
  @Param('id') id: string,
  @Body() updateProductDto: UpdateProductDto,
  @User() user: UserInfo
): Promise<ProductResponseDto> {
  // Create command from DTO
  const command: UpdateProductCommand = {
    commandId: uuid(),
    commandType: 'UpdateProductCommand',
    timestamp: new Date().toISOString(),
    userId: user.id,
    correlationId: uuid(),
    productId: id,
    data: updateProductDto
  };
  
  // Dispatch command
  await this.commandBus.dispatch(command);
  
  // Fetch the updated product from the read model
  const product = await this.productQueryService.findProductById(id);
  
  if (!product) {
    throw new NotFoundException(`Product with ID ${id} not found`);
  }
  
  // Return API response
  return this.productMapper.toResponseDto(product);
}
```

### 4.3. DELETE Operations

#### DELETE /products/{id}

**Before (Direct Repository Access):**

```typescript
@Delete(':id')
async deleteProduct(
  @Param('id') id: string,
  @User() user: UserInfo
): Promise<void> {
  await this.productService.deleteProduct(id);
}
```

**After (Command-Based):**

```typescript
@Delete(':id')
async deleteProduct(
  @Param('id') id: string,
  @User() user: UserInfo
): Promise<void> {
  // Create command
  const command: DeleteProductCommand = {
    commandId: uuid(),
    commandType: 'DeleteProductCommand',
    timestamp: new Date().toISOString(),
    userId: user.id,
    correlationId: uuid(),
    productId: id
  };
  
  // Dispatch command
  await this.commandBus.dispatch(command);
  
  // Return 204 No Content (handled by NestJS)
}
```

### 4.4. READ Operations

#### GET /products

**Before (Direct Repository Access):**

```typescript
@Get()
async findProducts(
  @Query() filterDto: ProductFilterDto
): Promise<PaginatedResponse<ProductResponseDto>> {
  const [products, total] = await this.productService.findProducts(filterDto);
  
  return {
    items: products.map(product => this.productMapper.toResponseDto(product)),
    total,
    page: filterDto.page || 1,
    limit: filterDto.limit || 10
  };
}
```

**After (Projection-Based):**

```typescript
@Get()
async findProducts(
  @Query() filterDto: ProductFilterDto,
  @Query() sortDto: ProductSortDto,
  @Query() paginationDto: PaginationDto
): Promise<PaginatedResponse<ProductResponseDto>> {
  // Query the product catalog projection
  const result = await this.productQueryService.findProducts(
    filterDto,
    sortDto,
    paginationDto
  );
  
  // Transform to API response format
  return {
    items: result.items.map(item => this.productMapper.toResponseDto(item)),
    total: result.total,
    page: result.page,
    limit: result.limit
  };
}
```

#### GET /products/{id}

**Before (Direct Repository Access):**

```typescript
@Get(':id')
async findProductById(@Param('id') id: string): Promise<ProductResponseDto> {
  const product = await this.productService.findProductById(id);
  
  if (!product) {
    throw new NotFoundException(`Product with ID ${id} not found`);
  }
  
  return this.productMapper.toResponseDto(product);
}
```

**After (Projection-Based):**

```typescript
@Get(':id')
async findProductById(@Param('id') id: string): Promise<ProductResponseDto> {
  // Query the product detail projection
  const product = await this.productQueryService.findProductById(id);
  
  if (!product) {
    throw new NotFoundException(`Product with ID ${id} not found`);
  }
  
  return this.productMapper.toResponseDto(product);
}
```

## 5. Error Handling

The API layer will translate command and query errors to appropriate HTTP responses:

```typescript
@Catch()
export class CommandErrorFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    
    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = 'Internal server error';
    
    if (exception instanceof ValidationError) {
      status = HttpStatus.BAD_REQUEST;
      message = exception.message;
    } else if (exception instanceof ConcurrencyError) {
      status = HttpStatus.CONFLICT;
      message = 'The resource was modified by another request. Please reload and try again.';
    } else if (exception instanceof NotFoundError) {
      status = HttpStatus.NOT_FOUND;
      message = exception.message;
    } else if (exception instanceof UnauthorizedError) {
      status = HttpStatus.FORBIDDEN;
      message = 'You do not have permission to perform this action';
    }
    
    response.status(status).json({
      statusCode: status,
      message,
      timestamp: new Date().toISOString(),
    });
  }
}
```

## 6. Special Considerations

### 6.1. Handling Eventual Consistency

When a command is processed, the read projections may not be immediately updated. To handle this:

```typescript
@Post()
async createProduct(
  @Body() createProductDto: CreateProductDto,
  @User() user: UserInfo
): Promise<ProductResponseDto> {
  // Dispatch command and get events as before
  const events = await this.commandBus.dispatch(command);
  const productId = events[0].entityId;
  
  // Option 1: Reconstruct response directly from the event
  // This is faster but requires duplicating logic from projections
  const productResponseFromEvent = this.productMapper.createFromEvent(events[0]);
  
  // Option 2: Wait for projection with retry/timeout
  // This ensures consistency but adds latency
  const maxRetries = 3;
  for (let i = 0; i < maxRetries; i++) {
    const product = await this.productQueryService.findProductById(productId);
    if (product) {
      return this.productMapper.toResponseDto(product);
    }
    await new Promise(resolve => setTimeout(resolve, 100)); // Wait 100ms
  }
  
  // Fall back to option 1 if projection not updated in time
  return productResponseFromEvent;
}
```

### 6.2. Transaction Boundaries

Since commands may emit multiple events, we need to ensure transaction boundaries are correctly defined:

```typescript
class ProductCommandHandlers {
  // Using transaction manager to ensure all events are stored atomically
  @Transactional()
  async executeCreateVariantCommand(command: CreateProductVariantCommand): Promise<DomainEvent<any>[]> {
    const events: DomainEvent<any>[] = [];
    const productId = command.productId;
    
    // Generate ProductVariantAdded event
    const variantAddedEvent = this.createVariantAddedEvent(command);
    events.push(variantAddedEvent);
    
    // Store the event
    await this.eventStore.appendEvent(
      'Product',
      productId,
      variantAddedEvent.eventType,
      variantAddedEvent.data,
      command.userId,
      command.correlationId
    );
    
    // If default variant, generate ProductDefaultVariantChanged event
    if (command.data.isDefault) {
      const defaultChangedEvent = this.createDefaultVariantChangedEvent(command, variantAddedEvent);
      events.push(defaultChangedEvent);
      
      // Store the second event in the same transaction
      await this.eventStore.appendEvent(
        'Product',
        productId,
        defaultChangedEvent.eventType,
        defaultChangedEvent.data,
        command.userId,
        command.correlationId,
        1 // Expected version increment after first event
      );
    }
    
    return events;
  }
}
```

## 7. Performance Optimizations

1. **Request-Scoped Data Loading**: Load data only once per request and reuse
2. **Projection Caching**: Cache frequently accessed projection data
3. **Batch Command Processing**: Group related commands into batches where appropriate
4. **Eager Loading**: Configure projections to eagerly load related data
5. **Query Optimization**: Ensure projection schema supports efficient queries

## 8. References

- [RESTful API Design Best Practices](https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design)
- [NestJS Controller Documentation](https://docs.nestjs.com/controllers)
- [Event Sourcing Best Practices](https://docs.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)