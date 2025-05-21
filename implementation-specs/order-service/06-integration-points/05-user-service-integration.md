# User Service Integration

## 1. Overview

This document specifies the integration between the Order Service and User Service. The Order Service interacts with the User Service to validate users, retrieve customer information, and update order history data. This integration uses a combination of asynchronous event-driven patterns and synchronous REST API calls where immediate responses are required. This balanced approach ensures proper authorization, personalization, and customer data consistency across the platform while maintaining service resilience and loose coupling.

## 2. Integration Points

### 2.1. API Endpoints (Synchronous)

| Endpoint                             | Method | Description                                                  | Caller        | Provider      |
| ------------------------------------ | ------ | ------------------------------------------------------------ | ------------- | ------------- |
| `/api/v1/users/{id}`                 | GET    | Get user details by ID (for immediate needs only)            | Order Service | User Service  |
| `/api/v1/users/{id}/addresses`       | GET    | Get user shipping/billing addresses (for immediate needs)    | Order Service | User Service  |
| `/api/v1/users/{id}/payment-methods` | GET    | Get user payment methods (for checkout process)              | Order Service | User Service  |
| `/api/v1/users/{id}/orders`          | GET    | Get user order history                                       | User Service  | Order Service |
| `/api/v1/users/{id}/orders/summary`  | GET    | Get user order summary stats                                 | User Service  | Order Service |

### 2.2. Events (Asynchronous)

| Event                      | Publisher      | Subscriber      | Purpose                                           |
| -------------------------- | -------------- | --------------- | ------------------------------------------------- |
| `user.updated`             | User Service   | Order Service   | Notify when user details are updated              |
| `user.address_added`       | User Service   | Order Service   | Notify when a user adds a new address             |
| `user.address_updated`     | User Service   | Order Service   | Notify when a user updates an address             |
| `order.created`            | Order Service  | User Service    | Notify when a new order is created                |
| `order.status_changed`     | Order Service  | User Service    | Notify when an order status changes               |
| `user.details_requested`   | Order Service  | User Service    | Request user details asynchronously               |
| `user.details_provided`    | User Service   | Order Service   | Respond with requested user details               |
| `user.addresses_requested` | Order Service  | User Service    | Request user addresses asynchronously             |
| `user.addresses_provided`  | User Service   | Order Service   | Respond with requested user addresses             |
| `user.account_status_changed` | User Service | Order Service  | Notify when a user's account status changes       |

## 3. Synchronous API Integration

### 3.1. User Authentication and Authorization

The Order Service uses JWT tokens provided by the User Service for authentication and authorization. This remains synchronous as it's a critical security requirement:

```typescript
@Injectable()
export class AuthGuard implements CanActivate {
  constructor(
    private readonly userService: UserServiceClient,
    private readonly logger: Logger
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const token = this.extractTokenFromHeader(request);

    if (!token) {
      throw new UnauthorizedException("Missing authentication token");
    }

    try {
      // Validate token with User Service
      const userData = await this.userService.validateToken(token);

      // Attach user to request
      request.user = userData;
      return true;
    } catch (error) {
      this.logger.error(`Authentication failed: ${error.message}`);
      throw new UnauthorizedException("Invalid authentication token");
    }
  }

  private extractTokenFromHeader(request: Request): string | undefined {
    const [type, token] = request.headers.authorization?.split(" ") ?? [];
    return type === "Bearer" ? token : undefined;
  }
}
```

### 3.2. Get User Details (Synchronous Mode)

The Order Service fetches user details synchronously only when immediate data is required for user-facing operations:

```typescript
@Injectable()
export class UserServiceClient {
  constructor(
    private readonly httpService: HttpService,
    @Inject("USER_SERVICE_URL") private readonly userServiceUrl: string,
    private readonly cacheManager: Cache,
    private readonly logger: Logger,
    private readonly circuitBreaker: CircuitBreaker
  ) {}

  async getUserDetails(userId: string, token: string): Promise<UserDto> {
    const cacheKey = `user:${userId}`;

    // Try to get from cache first
    const cachedUser = await this.cacheManager.get<UserDto>(cacheKey);
    if (cachedUser) {
      return cachedUser;
    }

    // Use circuit breaker for resilience
    return this.circuitBreaker.fire(async () => {
      try {
        const response = await this.httpService
          .get(`${this.userServiceUrl}/api/v1/users/${userId}`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            timeout: 2000 // Short timeout for user-facing operations
          })
          .toPromise();

        const userData = response.data;

        // Cache user data for 5 minutes
        await this.cacheManager.set(cacheKey, userData, { ttl: 300 });

        return userData;
      } catch (error) {
        this.logger.error(`Failed to get user ${userId}: ${error.message}`);

        if (error.response?.status === 404) {
          throw new NotFoundException(`User ${userId} not found`);
        }

        throw new ServiceUnavailableException(
          "User Service is currently unavailable"
        );
      }
    });
  }
}
```

**Example Response:**

```json
{
  "id": "9f8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
  "email": "customer@example.com",
  "firstName": "Jane",
  "lastName": "Smith",
  "phone": "+1234567890",
  "preferredCurrency": "USD",
  "preferredLanguage": "en-US",
  "accountStatus": "ACTIVE",
  "createdAt": "2023-03-15T10:20:30Z",
  "lastLoginAt": "2023-05-19T14:30:15Z"
}
```

### 3.3. Get User Addresses (Synchronous Mode)

The Order Service retrieves user addresses synchronously only during checkout or when displaying user-facing content:

```typescript
async getUserAddresses(userId: string, token: string): Promise<AddressDto[]> {
  const cacheKey = `user:${userId}:addresses`;

  // Try to get from cache first
  const cachedAddresses = await this.cacheManager.get<AddressDto[]>(cacheKey);
  if (cachedAddresses) {
    return cachedAddresses;
  }

  // Use circuit breaker pattern for resilience
  return this.circuitBreaker.fire(async () => {
    try {
      const response = await this.httpService.get(
        `${this.userServiceUrl}/api/v1/users/${userId}/addresses`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          },
          timeout: 2000 // Short timeout for user-facing operations
        }
      ).toPromise();

      const addresses = response.data;

      // Cache addresses for 5 minutes
      await this.cacheManager.set(cacheKey, addresses, { ttl: 300 });

      return addresses;
    } catch (error) {
      this.logger.error(`Failed to get addresses for user ${userId}: ${error.message}`);

      if (error.response?.status === 404) {
        return []; // No addresses found
      }

      // For service unavailability, fall back to empty list but log the issue
      if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT' || 
          error.response?.status >= 500) {
        this.logger.warn(`User Service unavailable, using empty address list for ${userId}`);
        return [];
      }

      throw new ServiceUnavailableException('User Service is currently unavailable');
    }
  });
}
```

**Example Response:**

```json
[
  {
    "id": "addr-001",
    "type": "SHIPPING",
    "isDefault": true,
    "recipientName": "Jane Smith",
    "addressLine1": "123 Main St",
    "addressLine2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "postalCode": "10001",
    "country": "US",
    "phone": "+1234567890"
  },
  {
    "id": "addr-002",
    "type": "BILLING",
    "isDefault": true,
    "recipientName": "Jane Smith",
    "addressLine1": "123 Main St",
    "addressLine2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "postalCode": "10001",
    "country": "US",
    "phone": "+1234567890"
  }
]
```

### 3.4. Provide Order History API

The Order Service still exposes user order history through APIs for immediate needs:

```typescript
@Controller("api/v1/users/:userId/orders")
@UseGuards(ServiceAuthGuard)
export class UserOrdersController {
  constructor(
    private readonly orderService: OrderService,
    private readonly orderMapper: OrderMapper,
    private readonly logger: Logger
  ) {}

  @Get()
  async getUserOrders(
    @Param("userId") userId: string,
    @Query() queryParams: OrderQueryParamsDto
  ): Promise<PaginatedResponseDto<OrderSummaryDto>> {
    this.logger.log(`Fetching orders for user ${userId}`);

    // Force filter by user ID
    queryParams.userId = userId;

    const [orders, total] = await this.orderService.findOrders(queryParams);

    return {
      items: orders.map((order) => this.orderMapper.toSummaryDto(order)),
      meta: {
        total,
        page: queryParams.page || 1,
        limit: queryParams.limit || 10,
        pages: Math.ceil(total / (queryParams.limit || 10)),
      },
    };
  }

  @Get("summary")
  async getUserOrderSummary(
    @Param("userId") userId: string
  ): Promise<UserOrderSummaryDto> {
    this.logger.log(`Fetching order summary for user ${userId}`);

    return this.orderService.getUserOrderSummary(userId);
  }
}
```

**Example Order Summary Response:**

```json
{
  "totalOrders": 12,
  "totalSpent": 1249.85,
  "averageOrderValue": 104.15,
  "firstOrderDate": "2023-01-15T10:30:00Z",
  "lastOrderDate": "2023-05-10T15:45:20Z",
  "ordersByStatus": {
    "DELIVERED": 9,
    "SHIPPED": 2,
    "PROCESSING": 1
  },
  "returnRate": 0.08
}
```

## 4. Event-Driven Integration (Asynchronous)

### 4.1. Handling User Updates

The Order Service listens for user update events to keep user data consistent:

```typescript
@EventPattern('user.updated')
async handleUserUpdated(
  @Payload() event: UserUpdatedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, data } = event;
  const { userId, fields } = data;

  this.logger.log(`Processing user.updated event ${eventId} for user ${userId}`);

  try {
    // Only process relevant user fields for Order Service
    const relevantFields = ['email', 'phone', 'preferredCurrency', 'accountStatus'];
    const hasRelevantChanges = relevantFields.some(field => fields.includes(field));

    if (hasRelevantChanges) {
      // Invalidate user cache
      await this.cacheManager.del(`user:${userId}`);

      // If account status changed to INACTIVE, flag open orders
      if (fields.includes('accountStatus') && data.accountStatus === 'INACTIVE') {
        await this.orderService.flagOrdersForInactiveUser(userId);
      }
    }

    // Acknowledge event
    context.getMessage().ack();
  } catch (error) {
    this.logger.error(`Error processing user.updated event: ${error.message}`);
    context.getMessage().nak();
  }
}
```

### 4.2. Handling Address Updates

The Order Service handles address update events for order processing:

```typescript
@EventPattern('user.address_updated')
async handleAddressUpdated(
  @Payload() event: AddressUpdatedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, data } = event;
  const { userId, addressId, address } = data;

  this.logger.log(`Processing user.address_updated event ${eventId} for address ${addressId}`);

  try {
    // Invalidate addresses cache
    await this.cacheManager.del(`user:${userId}:addresses`);

    // Update pending orders that use this address
    if (address.type === 'SHIPPING') {
      await this.orderService.updatePendingOrdersWithAddress(userId, addressId, address);
    }

    // Acknowledge event
    context.getMessage().ack();
  } catch (error) {
    this.logger.error(`Error processing user.address_updated event: ${error.message}`);
    context.getMessage().nak();
  }
}
```

### 4.3. Requesting User Details Asynchronously

For non-critical background operations, the Order Service requests user details asynchronously:

```typescript
async requestUserDetails(userId: string, requestId: string): Promise<void> {
  try {
    await this.eventBus.publish({
      id: uuidv4(),
      type: 'user.details_requested',
      source: 'order-service',
      dataVersion: '1.0',
      timestamp: new Date().toISOString(),
      correlationId: requestId,
      data: {
        userId,
        requestId,
        callbackEvent: 'user.details_provided'
      }
    });
    
    this.logger.log(`Published user.details_requested for ${userId}`);
  } catch (error) {
    this.logger.error(`Failed to publish user details request: ${error.message}`);
    // Add to retry queue
    await this.eventRetryQueue.add('user.details_requested', { 
      userId, 
      requestId 
    });
  }
}
```

### 4.4. Handling User Details Response

```typescript
@EventPattern('user.details_provided')
async handleUserDetailsProvided(
  @Payload() event: UserDetailsProvidedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, data } = event;
  const { userId, requestId, userDetails } = data;

  this.logger.log(`Processing user.details_provided event ${eventId} for user ${userId}`);

  try {
    // Update user cache
    await this.userDataCacheService.cacheUserData(userId, userDetails);
    
    // Notify any pending processes waiting for this data
    await this.userRequestCompletionService.notifyCompletion(requestId, userDetails);
    
    // Acknowledge event
    context.getMessage().ack();
  } catch (error) {
    this.logger.error(
      `Error processing user details response: ${error.message}`,
      error.stack
    );
    // Negative acknowledge to trigger retry
    context.getMessage().nak();
  }
}
```

### 4.5. Publishing Order Events

The Order Service publishes events when orders are created or changed:

```typescript
async publishOrderCreated(order: Order): Promise<void> {
  try {
    await this.eventBus.publish({
      id: uuidv4(),
      type: 'order.created',
      source: 'order-service',
      dataVersion: '1.0',
      timestamp: new Date().toISOString(),
      correlationId: order.id,
      data: {
        orderId: order.id,
        userId: order.userId,
        orderNumber: order.orderNumber,
        totalAmount: order.totalAmount,
        currency: order.currency,
        status: order.status.name,
        itemCount: order.items.length,
        createdAt: order.createdAt.toISOString()
      }
    });
  } catch (error) {
    this.logger.error(`Failed to publish order.created event: ${error.message}`);
    await this.eventRetryQueue.add('order.created', { orderId: order.id });
  }
}
```

## 5. Data Consistency

### 5.1. User Data Caching

The Order Service caches user data with appropriate TTL to reduce load on the User Service:

```typescript
@Injectable()
export class UserDataCacheService {
  constructor(
    @Inject(CACHE_MANAGER) private readonly cache: Cache,
    private readonly logger: Logger
  ) {}

  // Cache TTL in seconds
  private readonly USER_CACHE_TTL = 300; // 5 minutes
  private readonly ADDRESS_CACHE_TTL = 300; // 5 minutes

  async cacheUserData(userId: string, userData: UserDto): Promise<void> {
    try {
      await this.cache.set(`user:${userId}`, userData, this.USER_CACHE_TTL);
    } catch (error) {
      this.logger.warn(`Failed to cache user data: ${error.message}`);
    }
  }

  async getUserData(userId: string): Promise<UserDto | null> {
    try {
      return await this.cache.get<UserDto>(`user:${userId}`);
    } catch (error) {
      this.logger.warn(`Failed to get cached user data: ${error.message}`);
      return null;
    }
  }

  async invalidateUserData(userId: string): Promise<void> {
    try {
      await this.cache.del(`user:${userId}`);
      await this.cache.del(`user:${userId}:addresses`);
    } catch (error) {
      this.logger.warn(`Failed to invalidate user cache: ${error.message}`);
    }
  }
}
```

### 5.2. User Data Consistency Checks

Periodic checks ensure user data consistency between services:

```typescript
@Injectable()
export class UserDataConsistencyService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly userServiceClient: UserServiceClient,
    private readonly logger: Logger
  ) {}

  @Cron("0 2 * * *") // Run daily at 2am
  async checkUserDataConsistency(): Promise<void> {
    this.logger.log("Starting user data consistency check");

    const batchSize = 100;
    let page = 1;
    let processedCount = 0;
    let inconsistencies = 0;

    try {
      // Get recent orders in batches
      while (true) {
        const orders = await this.orderRepository.findRecent(page, batchSize);

        if (orders.length === 0) {
          break;
        }

        // Check each order's user data
        for (const order of orders) {
          try {
            const userData = await this.userServiceClient.getUserDetails(
              order.userId,
              "system-token" // Service-to-service token
            );

            // Check for inconsistencies
            if (this.isUserDataInconsistent(order, userData)) {
              this.logger.warn(
                `User data inconsistency found for order ${order.id}, user ${order.userId}`
              );

              // Log inconsistency for later resolution
              await this.logInconsistency(order, userData);
              inconsistencies++;
            }
          } catch (error) {
            this.logger.error(
              `Error checking user data for order ${order.id}: ${error.message}`
            );
          }

          processedCount++;
        }

        page++;
      }

      this.logger.log(
        `User data consistency check completed. Processed: ${processedCount}, ` +
          `Inconsistencies found: ${inconsistencies}`
      );
    } catch (error) {
      this.logger.error(
        `Error in user data consistency check: ${error.message}`
      );
    }
  }

  private isUserDataInconsistent(order: Order, userData: UserDto): boolean {
    // Check relevant fields for inconsistency
    return (
      order.email !== userData.email ||
      order.shippingDetails.recipientName !==
        `${userData.firstName} ${userData.lastName}` ||
      order.currency !== userData.preferredCurrency
    );
  }
}
```

## 6. Error Handling and Resilience Patterns

### 6.1. Service Unavailability

The Order Service handles User Service unavailability with resilience patterns:

```typescript
async createOrder(createOrderDto: CreateOrderDto, token: string): Promise<Order> {
  try {
    // First check cache or try asynchronous request with timeout
    let userData;
    try {
      // Attempt to get user data with short timeout
      userData = await this.userServiceClient.getUserDetails(
        createOrderDto.userId,
        token
      );
    } catch (error) {
      // If immediate retrieval fails, proceed with limited data and queue background fetch
      if (createOrderDto.userEmail && createOrderDto.shippingDetails?.recipientName) {
        this.logger.warn(
          `Creating order with limited user data, will update asynchronously`
        );
        
        // Create placeholder user data
        userData = {
          id: createOrderDto.userId,
          email: createOrderDto.userEmail,
          firstName: createOrderDto.shippingDetails.recipientName.split(' ')[0],
          lastName: createOrderDto.shippingDetails.recipientName.split(' ').slice(1).join(' '),
          preferredCurrency: createOrderDto.currency || 'USD'
        };
        
        // Request user details asynchronously
        await this.requestUserDetails(createOrderDto.userId, uuidv4());
      } else {
        // If we don't have enough data to proceed, rethrow the error
        throw error;
      }
    }

    // Create order with best available user data
    const newOrder = await this.orderRepository.createOrder({
      ...createOrderDto,
      userData: this.mapUserToOrderData(userData)
    });
    
    // If we used limited data, flag order for verification
    if (!userData.verified) {
      await this.orderService.flagOrderForReview(
        newOrder.id,
        'USER_DATA_VERIFICATION',
        'Order created with limited user data'
      );
      
      // Queue job to update user data when available
      await this.userDataUpdateQueue.add(
        'update-order-user-data',
        { orderId: newOrder.id, userId: createOrderDto.userId }
      );
    }

    return newOrder;
  } catch (error) {
    this.logger.error(`Failed to create order: ${error.message}`);
    throw error;
  }
}
```

### 6.2. Data Validation with Async Fallback

The Order Service uses a hybrid approach for address validation:

```typescript
async validateOrderAddress(
  userId: string,
  addressDto: AddressDto,
  token: string
): Promise<ValidationResult> {
  try {
    // First check cache
    const cachedAddresses = await this.userDataCacheService.getAddresses(userId);
    
    if (cachedAddresses) {
      return this.validateWithCachedAddresses(addressDto, cachedAddresses);
    }
    
    // Try to get from User Service with timeout
    try {
      const userAddresses = await this.userServiceClient.getUserAddresses(userId, token);
      
      // Cache for future use
      await this.userDataCacheService.cacheAddresses(userId, userAddresses);
      
      return this.processAddressValidation(addressDto, userAddresses);
    } catch (error) {
      // If User Service is unavailable but we need immediate validation
      if (error instanceof ServiceUnavailableException || 
          error.code === 'ECONNABORTED' || 
          error.code === 'ETIMEDOUT') {
        
        // Fall back to basic validation
        this.logger.warn(`Falling back to basic validation for address due to User Service unavailability`);
        const validationResult = this.addressValidator.validate(addressDto);
        
        // Request addresses asynchronously for later verification
        await this.requestUserAddresses(userId, uuidv4());
        
        // If address passes basic validation, flag for verification later
        if (validationResult.valid) {
          return {
            valid: true,
            verifiedAddress: addressDto,
            needsVerification: true
          };
        }
        
        return validationResult;
      }
      
      throw error;
    }
  } catch (error) {
    this.logger.error(`Address validation error: ${error.message}`);
    throw error;
  }
}

private processAddressValidation(addressDto: AddressDto, userAddresses: AddressDto[]): ValidationResult {
  // If this is a saved address (has ID), verify it exists and belongs to user
  if (addressDto.id) {
    const matchingAddress = userAddresses.find(addr => addr.id === addressDto.id);
    
    if (!matchingAddress) {
      return {
        valid: false,
        message: `Address with ID ${addressDto.id} not found for user`
      };
    }
    
    // Use the verified address from User Service
    return {
      valid: true,
      verifiedAddress: matchingAddress
    };
  }
  
  // For new addresses, perform basic validation
  return this.addressValidator.validate(addressDto);
}
```

## 7. Security Considerations

### 7.1. Service-to-Service Authentication

The Order Service uses service-level authentication for User Service API calls:

```typescript
@Injectable()
export class ServiceAuthenticationService {
  constructor(
    @Inject("AUTH_SERVICE_URL") private readonly authServiceUrl: string,
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
    private readonly logger: Logger
  ) {}

  private serviceToken: string;
  private tokenExpiry: Date;

  async getServiceToken(): Promise<string> {
    // Check if we have a valid token
    if (this.serviceToken && this.tokenExpiry > new Date()) {
      return this.serviceToken;
    }

    try {
      // Get new service token
      const response = await this.httpService
        .post(`${this.authServiceUrl}/api/v1/auth/service-token`, {
          serviceId: this.configService.get("SERVICE_ID"),
          serviceSecret: this.configService.get("SERVICE_SECRET"),
        })
        .toPromise();

      this.serviceToken = response.data.token;

      // Set expiry time (token TTL minus 5 minutes for safety margin)
      const ttlSeconds = response.data.expiresIn;
      this.tokenExpiry = new Date(Date.now() + (ttlSeconds - 300) * 1000);

      return this.serviceToken;
    } catch (error) {
      this.logger.error(`Failed to get service token: ${error.message}`);
      throw new ServiceUnavailableException(
        "Authentication service is currently unavailable"
      );
    }
  }
}
```

### 7.2. Data Minimization

The Order Service applies data minimization principles when storing user data:

```typescript
private mapUserToOrderData(userData: UserDto): OrderUserDataDto {
  // Store only necessary user information in the order
  return {
    userId: userData.id,
    email: userData.email,
    phone: userData.phone,
    preferredCurrency: userData.preferredCurrency,
    // Exclude sensitive user information
  };
}
```

## 8. Testing Strategy

### 8.1. Integration Tests

```typescript
describe("User Service Integration", () => {
  let orderService: OrderService;
  let userServiceMock: jest.Mocked<UserServiceClient>;

  beforeEach(async () => {
    const moduleRef = await Test.createTestingModule({
      providers: [
        OrderService,
        {
          provide: UserServiceClient,
          useFactory: () => ({
            getUserDetails: jest.fn(),
            getUserAddresses: jest.fn(),
            validateToken: jest.fn(),
          }),
        },
      ],
    }).compile();

    orderService = moduleRef.get<OrderService>(OrderService);
    userServiceMock = moduleRef.get(UserServiceClient);
  });

  describe("createOrder", () => {
    it("should fetch user details when creating an order", async () => {
      // Arrange
      const userId = "user-123";
      const token = "valid-token";
      const createOrderDto = { userId };

      userServiceMock.getUserDetails.mockResolvedValue({
        id: userId,
        email: "test@example.com",
        firstName: "Test",
        lastName: "User",
        preferredCurrency: "USD",
      });

      // Act
      await orderService.createOrder(createOrderDto, token);

      // Assert
      expect(userServiceMock.getUserDetails).toHaveBeenCalledWith(
        userId,
        token
      );
    });

    it("should handle User Service unavailability", async () => {
      // Arrange
      const userId = "user-123";
      const token = "valid-token";
      const createOrderDto = {
        userId,
        userEmail: "fallback@example.com",
        shippingDetails: {
          recipientName: "Fallback User",
        },
      };

      userServiceMock.getUserDetails.mockRejectedValue(
        new ServiceUnavailableException("User Service unavailable")
      );

      // Act
      const result = await orderService.createOrder(createOrderDto, token);

      // Assert
      expect(result).toBeDefined();
      expect(result.flagged).toBe(true);
      expect(result.flagReason).toContain("user-data-verification");
    });
  });
});
```

### 8.2. Mock Server Tests

```typescript
describe("User Service Mock Integration", () => {
  let app: INestApplication;
  let mockUserService: MockService;

  beforeAll(async () => {
    // Start mock User Service
    mockUserService = new MockService(4001, {
      "/api/v1/users/:id": {
        GET: (req, res) => {
          const userId = req.params.id;
          if (userId === "test-user") {
            res.json({
              id: "test-user",
              email: "test@example.com",
              firstName: "Test",
              lastName: "User",
            });
          } else {
            res.status(404).json({ message: "User not found" });
          }
        },
      },
      "/api/v1/users/:id/addresses": {
        GET: (req, res) => {
          res.json([
            {
              id: "addr-1",
              type: "SHIPPING",
              recipientName: "Test User",
              addressLine1: "123 Test St",
            },
          ]);
        },
      },
    });

    // Configure app to use mock service
    const moduleFixture = await Test.createTestingModule({
      imports: [
        AppModule.forRoot({
          userServiceUrl: "http://localhost:4001",
        }),
      ],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  afterAll(async () => {
    await app.close();
    await mockUserService.stop();
  });

  it("should create an order with mock user data", async () => {
    // Arrange & Act
    const response = await request(app.getHttpServer())
      .post("/api/v1/orders")
      .set("Authorization", "Bearer valid-token")
      .send({
        userId: "test-user",
        items: [{ productId: "product-1", quantity: 1 }],
      });

    // Assert
    expect(response.status).toBe(201);
    expect(response.body.userId).toBe("test-user");
  });
});
```

## 9. Monitoring and Observability

1. **Request Metrics**: Track response times, error rates, and throughput for both synchronous API calls and asynchronous event processing
2. **User Service Dependency Health**: Monitor availability and response time of User Service APIs with circuit breaker status
3. **Cache Performance**: Track hit ratio and invalidation frequency for user data caching
4. **Event Processing**: Monitor event processing rates, latencies, and failures for all user-related events
5. **Failed Authentication**: Monitor authentication failures and token validation issues
6. **User Data Inconsistencies**: Track frequency and types of data inconsistencies
7. **Asynchronous Request Completions**: Monitor successful completion rate and latency of asynchronous user data requests
8. **Fallback Activations**: Track when fallback mechanisms are activated due to service unavailability

## 10. References

- [User Service API Specification](../../user-service/04-api-endpoints/00-api-index.md)
- [Authentication Architecture](../../architecture/authentication-authorization.md)
- [Order Service Data Model](../02-data-model-setup/00-data-model-index.md)
- [Service-to-Service Authentication](../../architecture/patterns/service-authentication.md)
- [Data Privacy Guidelines](../../security/data-privacy-implementation.md)
- [Event-Driven Architecture Standards](../../../architecture/quality-standards/01-event-driven-architecture-standards.md)
- [Microservice Architecture Standards](../../../architecture/quality-standards/03-microservice-architecture-standards.md)
- [Data Integrity and Consistency Standards](../../../architecture/quality-standards/04-data-integrity-and-consistency-standards.md)
- [Security Standards](../../../architecture/quality-standards/05-security-standards.md)
