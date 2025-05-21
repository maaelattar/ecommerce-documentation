# Order Controller

## 1. Overview

The `OrderController` is the entry point for HTTP requests to the Order Service. It handles all RESTful API endpoints related to orders, including creation, retrieval, updates, cancellations, and status changes. This controller implements the API contract defined in the OpenAPI specification and follows RESTful best practices for resource management.

## 2. Responsibilities

- Handling HTTP requests and responses for order operations
- Validating request parameters and structure
- Implementing authentication and authorization checks
- Transforming between HTTP request/response DTOs and service layer objects
- Implementing proper HTTP status codes and error responses
- Managing request throttling and rate limiting
- Providing versioned API endpoints
- Implementing proper logging for API requests

## 3. Class Definition

```typescript
@Controller("orders")
@ApiTags("orders")
export class OrderController {
  constructor(
    private readonly orderService: OrderService,
    private readonly orderMapper: OrderMapper,
    private readonly logger: Logger
  ) {}

  // Controller methods defined below
}
```

## 4. Core Endpoints

### 4.1. Create Order

```typescript
@Post()
@ApiOperation({ summary: 'Create a new order' })
@ApiResponse({ status: 201, description: 'Order created successfully', type: OrderResponseDto })
@ApiResponse({ status: 400, description: 'Invalid order data' })
@ApiResponse({ status: 409, description: 'Insufficient inventory' })
@UseGuards(JwtAuthGuard)
async createOrder(
  @Body() createOrderDto: CreateOrderDto,
  @User() user: UserDto
): Promise<OrderResponseDto> {
  this.logger.log(`Create order request received for user ${user.id}`);

  try {
    // Call service to create order
    const order = await this.orderService.createOrder(createOrderDto, user.id);

    // Map to response DTO
    return this.orderMapper.toResponseDto(order);
  } catch (error) {
    this.logger.error(`Error creating order: ${error.message}`, error.stack);

    if (error instanceof BadRequestException) {
      throw error;
    }

    if (error instanceof ConflictException) {
      throw error;
    }

    throw new InternalServerErrorException('Failed to create order');
  }
}
```

### 4.2. Get Order by ID

```typescript
@Get(':id')
@ApiOperation({ summary: 'Get order by ID' })
@ApiParam({ name: 'id', description: 'Order ID' })
@ApiResponse({ status: 200, description: 'Order found', type: OrderResponseDto })
@ApiResponse({ status: 404, description: 'Order not found' })
@UseGuards(JwtAuthGuard)
async getOrderById(
  @Param('id') orderId: string,
  @User() user: UserDto,
  @Query() queryParams: OrderDetailsQueryParamsDto
): Promise<OrderResponseDto> {
  this.logger.log(`Get order request received for order ${orderId}`);

  try {
    // Check access permissions based on user role
    const hasAccess = await this.checkOrderAccess(orderId, user);

    if (!hasAccess) {
      throw new ForbiddenException('You do not have permission to access this order');
    }

    // Get order with requested details
    const order = await this.orderService.findOrderById(orderId);

    // Map to response DTO with customized field inclusion
    return this.orderMapper.toResponseDto(order, {
      includeItems: queryParams.includeItems !== 'false',
      includeShippingDetails: queryParams.includeShippingDetails !== 'false',
      includeBillingDetails: queryParams.includeBillingDetails !== 'false',
      includeStatusHistory: queryParams.includeStatusHistory === 'true'
    });
  } catch (error) {
    this.logger.error(`Error retrieving order ${orderId}: ${error.message}`, error.stack);

    if (error instanceof OrderNotFoundException) {
      throw new NotFoundException(error.message);
    }

    if (error instanceof ForbiddenException) {
      throw error;
    }

    throw new InternalServerErrorException(`Failed to retrieve order: ${error.message}`);
  }
}
```

### 4.3. Get Orders

```typescript
@Get()
@ApiOperation({ summary: 'Get orders with pagination and filtering' })
@ApiResponse({ status: 200, description: 'Orders found', type: [OrderResponseDto] })
@UseGuards(JwtAuthGuard)
async getOrders(
  @Query() queryParams: OrderQueryParamsDto,
  @User() user: UserDto
): Promise<PaginatedResponseDto<OrderResponseDto>> {
  this.logger.log(`Get orders request received with params: ${JSON.stringify(queryParams)}`);

  try {
    // For non-admin users, force filter by their own user ID
    if (user.role !== 'admin' && user.role !== 'customer-service') {
      queryParams.userId = user.id;
    }

    // Get orders from service
    const [orders, totalCount] = await this.orderService.findOrders(queryParams);

    // Map to response DTOs
    const orderDtos = await Promise.all(
      orders.map(order => this.orderMapper.toResponseDto(order, {
        includeItems: true,
        includeShippingDetails: true,
        includeBillingDetails: user.role === 'admin' || user.role === 'customer-service',
        includeStatusHistory: false
      }))
    );

    // Return paginated response
    return {
      items: orderDtos,
      meta: {
        totalItems: totalCount,
        itemCount: orderDtos.length,
        itemsPerPage: queryParams.limit || 10,
        totalPages: Math.ceil(totalCount / (queryParams.limit || 10)),
        currentPage: queryParams.page || 1
      }
    };
  } catch (error) {
    this.logger.error(`Error retrieving orders: ${error.message}`, error.stack);
    throw new InternalServerErrorException(`Failed to retrieve orders: ${error.message}`);
  }
}
```

### 4.4. Update Order Status

```typescript
@Patch(':id/status')
@ApiOperation({ summary: 'Update order status' })
@ApiParam({ name: 'id', description: 'Order ID' })
@ApiResponse({ status: 200, description: 'Order status updated', type: OrderResponseDto })
@ApiResponse({ status: 400, description: 'Invalid status transition' })
@ApiResponse({ status: 404, description: 'Order not found' })
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin', 'customer-service', 'shipping')
async updateOrderStatus(
  @Param('id') orderId: string,
  @Body() statusUpdateDto: UpdateOrderStatusDto,
  @User() user: UserDto
): Promise<OrderResponseDto> {
  this.logger.log(`Update status request for order ${orderId} to ${statusUpdateDto.status}`);

  try {
    // Update order status
    const updatedOrder = await this.orderService.updateOrderStatus(
      orderId,
      statusUpdateDto,
      user.id
    );

    // Map to response DTO
    return this.orderMapper.toResponseDto(updatedOrder);
  } catch (error) {
    this.logger.error(`Error updating order status: ${error.message}`, error.stack);

    if (error instanceof OrderNotFoundException) {
      throw new NotFoundException(error.message);
    }

    if (error instanceof OrderStatusTransitionException) {
      throw new BadRequestException(error.message);
    }

    throw new InternalServerErrorException(`Failed to update order status: ${error.message}`);
  }
}
```

### 4.5. Cancel Order

```typescript
@Post(':id/cancel')
@ApiOperation({ summary: 'Cancel an order' })
@ApiParam({ name: 'id', description: 'Order ID' })
@ApiResponse({ status: 200, description: 'Order cancelled', type: OrderResponseDto })
@ApiResponse({ status: 400, description: 'Order cannot be cancelled' })
@ApiResponse({ status: 404, description: 'Order not found' })
@UseGuards(JwtAuthGuard)
async cancelOrder(
  @Param('id') orderId: string,
  @Body() cancelOrderDto: CancelOrderDto,
  @User() user: UserDto
): Promise<OrderResponseDto> {
  this.logger.log(`Cancel order request received for order ${orderId}`);

  try {
    // Check access permissions for cancellation
    const hasAccess = await this.checkOrderCancellationAccess(orderId, user);

    if (!hasAccess) {
      throw new ForbiddenException('You do not have permission to cancel this order');
    }

    // Cancel the order
    const cancelledOrder = await this.orderService.cancelOrder(
      orderId,
      cancelOrderDto.reason,
      cancelOrderDto.note,
      user.id
    );

    // Map to response DTO
    return this.orderMapper.toResponseDto(cancelledOrder);
  } catch (error) {
    this.logger.error(`Error cancelling order: ${error.message}`, error.stack);

    if (error instanceof OrderNotFoundException) {
      throw new NotFoundException(error.message);
    }

    if (error instanceof OrderStatusTransitionException) {
      throw new BadRequestException(error.message);
    }

    if (error instanceof ForbiddenException) {
      throw error;
    }

    throw new InternalServerErrorException(`Failed to cancel order: ${error.message}`);
  }
}
```

### 4.6. Bulk Operations

```typescript
@Post('bulk/status-update')
@ApiOperation({ summary: 'Bulk update order statuses' })
@ApiResponse({ status: 200, description: 'Bulk update processed', type: [BulkOrderStatusUpdateResultDto] })
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin', 'shipping')
async bulkStatusUpdate(
  @Body() bulkUpdateDto: BulkOrderStatusUpdateDto,
  @User() user: UserDto
): Promise<BulkOrderStatusUpdateResultDto[]> {
  this.logger.log(`Bulk status update request for ${bulkUpdateDto.orderIds.length} orders`);

  // Generate unique batch ID for tracking
  const batchId = uuidv4();

  try {
    // Process bulk update
    const results = await this.orderService.bulkStatusUpdate(
      bulkUpdateDto,
      user.id,
      batchId
    );

    return results;
  } catch (error) {
    this.logger.error(`Error processing bulk status update: ${error.message}`, error.stack);
    throw new InternalServerErrorException(`Failed to process bulk update: ${error.message}`);
  }
}
```

## 5. Helper Methods

### 5.1. Check Order Access

```typescript
/**
 * Checks if a user has permission to access an order
 */
private async checkOrderAccess(
  orderId: string,
  user: UserDto
): Promise<boolean> {
  // Admin and customer service can access all orders
  if (user.role === 'admin' || user.role === 'customer-service') {
    return true;
  }

  // For customers, check if the order belongs to them
  const order = await this.orderService.findOrderById(orderId);
  return order.userId === user.id;
}
```

### 5.2. Check Order Cancellation Access

```typescript
/**
 * Checks if a user has permission to cancel an order
 */
private async checkOrderCancellationAccess(
  orderId: string,
  user: UserDto
): Promise<boolean> {
  // Admin and customer service can cancel any order
  if (user.role === 'admin' || user.role === 'customer-service') {
    return true;
  }

  // Get the order to check ownership and status
  const order = await this.orderService.findOrderById(orderId);

  // For customers, check if the order belongs to them
  if (order.userId !== user.id) {
    return false;
  }

  // Check if order is in a cancellable state for customers
  const customerCancellableStates = ['PENDING_PAYMENT', 'PAYMENT_COMPLETED', 'PROCESSING'];
  return customerCancellableStates.includes(order.status.name);
}
```

## 6. Error Handling

The `OrderController` implements a consistent error handling approach:

1. Service exceptions are caught and mapped to appropriate HTTP exceptions
2. Each endpoint has specific error response documentation
3. Errors are logged with appropriate context
4. Error responses follow a standardized format:

```typescript
{
  statusCode: number,
  message: string,
  error: string,
  timestamp: string,
  path: string,
  details?: any
}
```

### Global Exception Filter Example:

```typescript
@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const message =
      exception instanceof HttpException
        ? exception.message
        : "Internal server error";

    const errorResponse = {
      statusCode: status,
      message,
      error: exception.name,
      timestamp: new Date().toISOString(),
      path: request.url,
      details: exception.response?.details,
    };

    Logger.error(
      `${request.method} ${request.url} ${status} - ${message}`,
      exception.stack,
      "HttpExceptionFilter"
    );

    response.status(status).json(errorResponse);
  }
}
```

## 7. Validation

The `OrderController` uses class-validator for request validation:

```typescript
// Example CreateOrderDto with validation
export class CreateOrderDto {
  @ApiProperty({ description: "Order items", type: [CreateOrderItemDto] })
  @ValidateNested({ each: true })
  @Type(() => CreateOrderItemDto)
  @ArrayMinSize(1, { message: "Order must have at least one item" })
  readonly items: CreateOrderItemDto[];

  @ApiProperty({ description: "Shipping details", type: ShippingDetailsDto })
  @ValidateNested()
  @Type(() => ShippingDetailsDto)
  @IsNotEmpty({ message: "Shipping details are required" })
  readonly shippingDetails: ShippingDetailsDto;

  @ApiProperty({ description: "Billing details", type: BillingDetailsDto })
  @ValidateNested()
  @Type(() => BillingDetailsDto)
  @IsNotEmpty({ message: "Billing details are required" })
  readonly billingDetails: BillingDetailsDto;

  @ApiProperty({ description: "Tax amount", required: false })
  @IsNumber({ allowNaN: false }, { message: "Tax must be a number" })
  @IsOptional()
  readonly tax?: number;

  @ApiProperty({ description: "Shipping cost", required: false })
  @IsNumber({ allowNaN: false }, { message: "Shipping cost must be a number" })
  @IsOptional()
  readonly shippingCost?: number;

  @ApiProperty({ description: "Discount amount", required: false })
  @IsNumber(
    { allowNaN: false },
    { message: "Discount amount must be a number" }
  )
  @Min(0, { message: "Discount amount cannot be negative" })
  @IsOptional()
  readonly discountAmount?: number;

  @ApiProperty({
    description: "Currency code",
    required: false,
    default: "USD",
  })
  @IsString({ message: "Currency must be a string" })
  @IsOptional()
  readonly currency?: string;

  @ApiProperty({ description: "Promo code", required: false })
  @IsString({ message: "Promo code must be a string" })
  @IsOptional()
  readonly promoCode?: string;

  @ApiProperty({ description: "Order notes", required: false })
  @IsString({ message: "Notes must be a string" })
  @IsOptional()
  readonly notes?: string;

  @ApiProperty({ description: "Additional metadata", required: false })
  @IsObject({ message: "Metadata must be an object" })
  @IsOptional()
  readonly metadata?: Record<string, any>;
}
```

## 8. API Documentation

The `OrderController` uses Swagger/OpenAPI for comprehensive API documentation:

```typescript
// Example OpenAPI setup
@ApiTags("orders")
@ApiBearerAuth()
@ApiExtraModels(
  OrderResponseDto,
  OrderItemDto,
  ShippingDetailsDto,
  BillingDetailsDto,
  StatusHistoryDto
)
export class OrderController {
  // Controller methods
}
```

## 9. Security Considerations

- JWT Authentication for all endpoints
- Role-based access control for sensitive operations
- Validation of request data to prevent injection attacks
- Rate limiting to prevent abuse
- Field-level access control in response DTOs based on user role
- Audit logging for all order status changes
- Sanitization of user inputs

## 10. References

- [Order Service](./02-order-service.md)
- [Order Mapper](./04-order-mapper.md)
- [Order API Contract](../04-api-endpoints/00-api-index.md)
- [Auth Service Integration](../06-integration-points/06-auth-service-integration.md)
- [Error Handling Strategy](../07-error-handling-strategies.md)
