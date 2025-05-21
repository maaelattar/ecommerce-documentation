# Product Service Integration

## 1. Overview

This document specifies the integration between the Order Service and Product Service. The Order Service relies on the Product Service for product information, pricing, and availability when creating and managing orders. This integration uses a combination of asynchronous event-driven patterns and synchronous REST API calls where immediate responses are required. This balanced approach ensures data consistency across services, reduces coupling, and enables resilient order processing.

## 2. Integration Points

### 2.1. API Endpoints (Synchronous)

| Endpoint                 | Method | Description                                          | Caller        | Provider        |
| ------------------------ | ------ | ---------------------------------------------------- | ------------- | --------------- |
| `/api/v1/products/{id}`  | GET    | Get product details by ID (for immediate needs only) | Order Service | Product Service |
| `/api/v1/products/batch` | POST   | Get multiple products by IDs (for immediate needs)   | Order Service | Product Service |

### 2.2. Events (Asynchronous)

| Event                             | Publisher       | Subscriber      | Purpose                                         |
| --------------------------------- | --------------- | --------------- | ----------------------------------------------- |
| `product.updated`                 | Product Service | Order Service   | Notify when product details are updated         |
| `product.price_changed`           | Product Service | Order Service   | Notify when product pricing changes             |
| `product.discontinued`            | Product Service | Order Service   | Notify when a product is discontinued           |
| `product.created`                 | Product Service | Order Service   | Notify when a new product is created            |
| `order.created`                   | Order Service   | Product Service | Notify when a new order is created              |
| `product.details_requested`       | Order Service   | Product Service | Request product details asynchronously          |
| `product.details_provided`        | Product Service | Order Service   | Respond with requested product details          |
| `product.batch_details_requested` | Order Service   | Product Service | Request multiple product details asynchronously |
| `product.batch_details_provided`  | Product Service | Order Service   | Respond with requested batch product details    |
| `product.availability_changed`    | Product Service | Order Service   | Notify when product availability status changes |

## 3. API Integration (Synchronous)

The following synchronous API calls are still used in scenarios where immediate response is critical for the user experience:

### 3.1. Get Product Details (Synchronous Mode)

**Endpoint:** `GET /api/v1/products/{id}`

The Order Service calls this endpoint only when immediate product information is required:

- During real-time user interactions (e.g., checkout process)
- When cache is invalid and data is critical

**Example Request:**

```typescript
const getProductDetails = async (productId: string): Promise<ProductDto> => {
  try {
    const response = await httpClient.get(`/api/v1/products/${productId}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      throw new ProductNotFoundException(
        `Product with ID ${productId} not found`
      );
    }
    throw new ProductServiceException(
      `Failed to fetch product details: ${error.message}`
    );
  }
};
```

### 3.2. Batch Product Retrieval (Synchronous Mode)

**Endpoint:** `POST /api/v1/products/batch`

Used only when multiple products must be retrieved with minimal latency:

- During checkout process
- When displaying order details to users in real-time

**Example Request:**

```typescript
const getProductsBatch = async (
  productIds: string[]
): Promise<Map<string, ProductDto>> => {
  try {
    const response = await httpClient.post("/api/v1/products/batch", {
      ids: productIds,
    });

    // Convert array to map for easier lookup
    return new Map(response.data.map((product) => [product.id, product]));
  } catch (error) {
    throw new ProductServiceException(
      `Failed to fetch products in batch: ${error.message}`
    );
  }
};
```

## 4. Event-Driven Integration (Asynchronous)

For most operations, the Order Service uses asynchronous event-driven patterns to reduce coupling and improve resilience:

### 4.1. Handling Product Updates

The Order Service listens for `product.updated` events to keep product information up-to-date:

```typescript
@EventPattern('product.updated')
async handleProductUpdated(
  @Payload() event: ProductUpdatedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, data } = event;
  const { productId, name, price, status } = data;

  this.logger.log(`Processing product.updated event ${eventId} for product ${productId}`);

  try {
    // Update product cache
    await this.productCacheService.updateProduct({
      id: productId,
      name,
      price,
      status
    });

    // If product is discontinued, flag affected orders
    if (status === 'DISCONTINUED') {
      await this.orderService.flagOrdersWithDiscontinuedProduct(productId);
    }

    // Acknowledge event processing
    context.getMessage().ack();
  } catch (error) {
    this.logger.error(
      `Error processing product.updated event: ${error.message}`,
      error.stack
    );
    // Negative acknowledge to trigger retry
    context.getMessage().nak();
  }
}
```

### 4.2. Requesting Product Details Asynchronously

For non-critical, background operations, the Order Service requests product details asynchronously:

```typescript
async requestProductDetails(productId: string, requestId: string): Promise<void> {
  try {
    await this.eventBus.publish({
      id: uuidv4(),
      type: 'product.details_requested',
      source: 'order-service',
      dataVersion: '1.0',
      timestamp: new Date().toISOString(),
      correlationId: requestId,
      data: {
        productId,
        requestId,
        callbackEvent: 'product.details_provided'
      }
    });

    this.logger.log(`Published product.details_requested for ${productId}`);
  } catch (error) {
    this.logger.error(`Failed to publish product details request: ${error.message}`);
    // Add to retry queue
    await this.eventRetryQueue.add('product.details_requested', {
      productId,
      requestId
    });
  }
}
```

### 4.3. Handling Product Details Response

```typescript
@EventPattern('product.details_provided')
async handleProductDetailsProvided(
  @Payload() event: ProductDetailsProvidedEvent,
  @Ctx() context: NatsContext
): Promise<void> {
  const { id: eventId, data } = event;
  const { productId, requestId, productDetails } = data;

  this.logger.log(`Processing product.details_provided event ${eventId} for product ${productId}`);

  try {
    // Update product cache
    await this.productCacheService.updateProduct(productDetails);

    // Notify any waiting processes
    await this.productRequestCompletionService.notifyCompletion(requestId, productDetails);

    // Acknowledge event
    context.getMessage().ack();
  } catch (error) {
    this.logger.error(
      `Error processing product details response: ${error.message}`,
      error.stack
    );
    // Negative acknowledge to trigger retry
    context.getMessage().nak();
  }
}
```

### 4.4. Batch Product Details Request

For bulk operations or background processing:

```typescript
async requestProductBatchDetails(
  productIds: string[],
  requestId: string
): Promise<void> {
  try {
    await this.eventBus.publish({
      id: uuidv4(),
      type: 'product.batch_details_requested',
      source: 'order-service',
      dataVersion: '1.0',
      timestamp: new Date().toISOString(),
      correlationId: requestId,
      data: {
        productIds,
        requestId,
        callbackEvent: 'product.batch_details_provided'
      }
    });

    this.logger.log(`Published product.batch_details_requested for ${productIds.length} products`);
  } catch (error) {
    this.logger.error(`Failed to publish batch product details request: ${error.message}`);
    // Add to retry queue
    await this.eventRetryQueue.add('product.batch_details_requested', {
      productIds,
      requestId
    });
  }
}
```

### 4.5. Publishing Order Created Events

When a new order is created, the Order Service publishes an `order.created` event with product information:

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
        items: order.items.map(item => ({
          productId: item.productId,
          variantId: item.variantId,
          quantity: item.quantity,
          unitPrice: item.unitPrice
        })),
        totalAmount: order.totalAmount,
        timestamp: order.createdAt.toISOString()
      }
    });
  } catch (error) {
    this.logger.error(`Failed to publish order.created event: ${error.message}`);
    // Queue for retry
    await this.eventRetryQueue.add('order.created', { orderId: order.id });
  }
}
```

## 5. Advanced Implementation Patterns

### 5.1. Request-Reply Pattern with Correlation ID

For operations that conceptually need a response but can be handled asynchronously:

```typescript
@Injectable()
export class ProductAsyncRequestService {
  private pendingRequests = new Map<
    string,
    {
      resolve: (data: any) => void;
      reject: (error: any) => void;
      timeout: NodeJS.Timeout;
    }
  >();

  constructor(
    private readonly eventBus: EventBus,
    private readonly logger: Logger
  ) {}

  async requestProductDetailsWithTimeout(
    productId: string,
    timeoutMs: number = 5000
  ): Promise<ProductDto> {
    const requestId = uuidv4();

    try {
      const result = await this.createPendingRequest(requestId, timeoutMs);

      // Publish the request event
      await this.eventBus.publish({
        id: uuidv4(),
        type: "product.details_requested",
        source: "order-service",
        dataVersion: "1.0",
        timestamp: new Date().toISOString(),
        correlationId: requestId,
        data: {
          productId,
          requestId,
          callbackEvent: "product.details_provided",
        },
      });

      // Wait for the response or timeout
      return await result;
    } catch (error) {
      if (error.message === "Request timed out") {
        this.logger.warn(`Product details request for ${productId} timed out`);

        // Fall back to synchronous request
        this.logger.log(`Falling back to synchronous request for ${productId}`);
        return this.productServiceClient.getProduct(productId);
      }
      throw error;
    }
  }

  private createPendingRequest(
    requestId: string,
    timeoutMs: number
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        const request = this.pendingRequests.get(requestId);
        if (request) {
          request.reject(new Error("Request timed out"));
          this.pendingRequests.delete(requestId);
        }
      }, timeoutMs);

      this.pendingRequests.set(requestId, { resolve, reject, timeout });
    });
  }

  completeRequest(requestId: string, data: any): void {
    const request = this.pendingRequests.get(requestId);
    if (request) {
      clearTimeout(request.timeout);
      request.resolve(data);
      this.pendingRequests.delete(requestId);
    }
  }

  failRequest(requestId: string, error: any): void {
    const request = this.pendingRequests.get(requestId);
    if (request) {
      clearTimeout(request.timeout);
      request.reject(error);
      this.pendingRequests.delete(requestId);
    }
  }
}
```

### 5.2. Background Data Refresh with Event Sourcing

To keep product data up to date without blocking user operations:

```typescript
@Injectable()
export class ProductDataRefreshService {
  constructor(
    private readonly eventBus: EventBus,
    private readonly productCacheService: ProductCacheService,
    private readonly logger: Logger
  ) {}

  @Cron("0 */2 * * *") // Every 2 hours
  async refreshActiveProductData(): Promise<void> {
    try {
      const activeProducts =
        await this.productCacheService.getActiveProductIds();

      // Split into batches to avoid large events
      const batches = this.chunkArray(activeProducts, 50);

      for (const batch of batches) {
        const requestId = uuidv4();

        await this.eventBus.publish({
          id: uuidv4(),
          type: "product.batch_details_requested",
          source: "order-service",
          dataVersion: "1.0",
          timestamp: new Date().toISOString(),
          correlationId: requestId,
          data: {
            productIds: batch,
            requestId,
            refreshMode: true,
          },
        });

        this.logger.log(`Scheduled refresh for ${batch.length} products`);

        // Small delay between batches to avoid overwhelming the product service
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    } catch (error) {
      this.logger.error(
        `Error scheduling product data refresh: ${error.message}`
      );
    }
  }

  private chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }
}
```

## 6. Data Consistency

### 6.1. Product Caching

To reduce latency and dependency on the Product Service, the Order Service implements a caching strategy:

```typescript
@Injectable()
export class ProductCacheService {
  constructor(
    @InjectRedis() private readonly redis: Redis,
    private readonly logger: Logger
  ) {}

  private readonly CACHE_TTL = 3600; // 1 hour in seconds
  private readonly CACHE_PREFIX = "product:";

  async getProduct(productId: string): Promise<ProductDto | null> {
    try {
      const cached = await this.redis.get(`${this.CACHE_PREFIX}${productId}`);
      if (cached) {
        return JSON.parse(cached);
      }
      return null;
    } catch (error) {
      this.logger.warn(`Error retrieving product from cache: ${error.message}`);
      return null;
    }
  }

  async updateProduct(product: ProductDto): Promise<void> {
    try {
      await this.redis.set(
        `${this.CACHE_PREFIX}${product.id}`,
        JSON.stringify(product),
        "EX",
        this.CACHE_TTL
      );
    } catch (error) {
      this.logger.error(`Error updating product in cache: ${error.message}`);
    }
  }

  async invalidateProduct(productId: string): Promise<void> {
    try {
      await this.redis.del(`${this.CACHE_PREFIX}${productId}`);
    } catch (error) {
      this.logger.error(
        `Error invalidating product in cache: ${error.message}`
      );
    }
  }

  async getActiveProductIds(): Promise<string[]> {
    try {
      const keys = await this.redis.keys(`${this.CACHE_PREFIX}*`);
      const activeIds: string[] = [];

      for (const key of keys) {
        const productData = await this.redis.get(key);
        if (productData) {
          const product = JSON.parse(productData);
          if (product.status === "ACTIVE") {
            activeIds.push(product.id);
          }
        }
      }

      return activeIds;
    } catch (error) {
      this.logger.error(
        `Error retrieving active product IDs: ${error.message}`
      );
      return [];
    }
  }
}
```

### 6.2. Handling Data Discrepancies

When discrepancies are detected between the cached product data and the Product Service:

1. Log the discrepancy for analysis
2. Update the cache with latest information
3. Use the latest information for processing
4. If critical (e.g., price difference > 10%), flag the order for review

```typescript
async validateProductPricing(
  orderId: string,
  items: OrderItemDto[]
): Promise<PriceDiscrepancyResult> {
  const discrepancies = [];
  let totalDifference = 0;

  for (const item of items) {
    const latestProduct = await this.productService.getProductDetails(item.productId);

    // Calculate price difference percentage
    const priceDifference = Math.abs(
      ((item.unitPrice - latestProduct.currentPrice) / latestProduct.currentPrice) * 100
    );

    if (priceDifference > 1.0) { // More than 1% difference
      discrepancies.push({
        productId: item.productId,
        orderPrice: item.unitPrice,
        currentPrice: latestProduct.currentPrice,
        difference: priceDifference
      });

      totalDifference += (latestProduct.currentPrice - item.unitPrice) * item.quantity;
    }
  }

  return {
    hasDiscrepancies: discrepancies.length > 0,
    discrepancies,
    totalDifference,
    requiresReview: Math.abs(totalDifference) > 10 || discrepancies.some(d => d.difference > 10)
  };
}
```

## 7. Error Handling

### 7.1. Circuit Breaker Pattern

To handle temporary Product Service outages, a circuit breaker pattern is implemented:

```typescript
@Injectable()
export class ProductServiceClient {
  private readonly circuitBreaker: CircuitBreaker;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
    private readonly logger: Logger
  ) {
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 3,
      resetTimeout: 30000, // 30 seconds
      fallback: (productId) => this.fallbackGetProduct(productId),
    });
  }

  async getProduct(productId: string): Promise<ProductDto> {
    return this.circuitBreaker.fire(() => this.makeHttpRequest(productId));
  }

  private async makeHttpRequest(productId: string): Promise<ProductDto> {
    try {
      const response = await this.httpService
        .get(
          `${this.configService.get(
            "PRODUCT_SERVICE_URL"
          )}/api/v1/products/${productId}`
        )
        .toPromise();
      return response.data;
    } catch (error) {
      this.logger.error(`Failed to get product ${productId}: ${error.message}`);
      throw error;
    }
  }

  private async fallbackGetProduct(productId: string): Promise<ProductDto> {
    // Try to get from cache first
    const cachedProduct = await this.productCacheService.getProduct(productId);
    if (cachedProduct) {
      return {
        ...cachedProduct,
        _source: "cache",
      };
    }

    throw new ServiceUnavailableException(
      "Product Service is currently unavailable and product not in cache"
    );
  }
}
```

### 7.2. Retry Strategies

API calls to the Product Service use exponential backoff retry:

```typescript
const getProductWithRetry = async (productId: string): Promise<ProductDto> => {
  return retry(
    async () => {
      return await productServiceClient.getProduct(productId);
    },
    {
      maxRetries: 3,
      retryInterval: 1000,
      exponentialBackoff: true,
      shouldRetry: (error) => {
        return (
          error.status === 503 || error.status === 429 || error.status >= 500
        );
      },
    }
  );
};
```

## 8. Testing Strategy

### 8.1. Integration Tests

```typescript
describe("Product Service Integration", () => {
  let orderService: OrderService;
  let productServiceMock: jest.Mocked<ProductServiceClient>;
  let eventBusMock: jest.Mocked<EventBus>;

  beforeEach(async () => {
    const moduleRef = await Test.createTestingModule({
      providers: [
        OrderService,
        {
          provide: ProductServiceClient,
          useFactory: () => ({
            getProduct: jest.fn(),
            getProductsBatch: jest.fn(),
            checkProductAvailability: jest.fn(),
          }),
        },
        {
          provide: EventBus,
          useFactory: () => ({
            publish: jest.fn().mockResolvedValue(undefined),
          }),
        },
      ],
    }).compile();

    orderService = moduleRef.get<OrderService>(OrderService);
    productServiceMock = moduleRef.get(ProductServiceClient);
    eventBusMock = moduleRef.get(EventBus);
  });

  describe("createOrder", () => {
    it("should fetch product details when creating an order", async () => {
      // Arrange
      const createOrderDto = {
        /* test data */
      };

      productServiceMock.getProductsBatch.mockResolvedValue(
        new Map([
          [
            "product-1",
            { id: "product-1", name: "Test Product", price: 19.99 },
          ],
        ])
      );

      // Act
      await orderService.createOrder(createOrderDto);

      // Assert
      expect(productServiceMock.getProductsBatch).toHaveBeenCalledWith(
        expect.arrayContaining(["product-1"])
      );
    });

    it("should publish order.created event after order creation", async () => {
      // Arrange
      const createOrderDto = {
        /* test data */
      };

      productServiceMock.getProductsBatch.mockResolvedValue(
        new Map([
          [
            "product-1",
            { id: "product-1", name: "Test Product", price: 19.99 },
          ],
        ])
      );

      // Act
      const createdOrder = await orderService.createOrder(createOrderDto);

      // Assert
      expect(eventBusMock.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "order.created",
          correlationId: createdOrder.id,
          data: expect.objectContaining({
            orderId: createdOrder.id,
          }),
        })
      );
    });

    it("should throw an error when product is not available", async () => {
      // Arrange
      const createOrderDto = {
        /* test data with product-2 */
      };

      productServiceMock.getProductsBatch.mockResolvedValue(
        new Map([
          [
            "product-2",
            { id: "product-2", name: "Test Product", price: 29.99 },
          ],
        ])
      );

      productServiceMock.checkProductAvailability.mockResolvedValue({
        productId: "product-2",
        available: false,
        quantityAvailable: 0,
      });

      // Act & Assert
      await expect(orderService.createOrder(createOrderDto)).rejects.toThrow(
        "Product product-2 is not available in the requested quantity"
      );
    });
  });

  describe("handleProductDetailsProvided", () => {
    it("should update product cache when receiving product details", async () => {
      // Arrange
      const event = {
        id: "event-1",
        data: {
          productId: "product-1",
          requestId: "request-1",
          productDetails: {
            id: "product-1",
            name: "Updated Product Name",
            price: 24.99,
            status: "ACTIVE",
          },
        },
      };

      const productCacheServiceMock = {
        updateProduct: jest.fn().mockResolvedValue(undefined),
      };

      const handler = new ProductEventHandlers(
        productCacheServiceMock as any,
        new Logger()
      );

      const contextMock = {
        getMessage: () => ({
          ack: jest.fn(),
          nak: jest.fn(),
        }),
      };

      // Act
      await handler.handleProductDetailsProvided(event, contextMock as any);

      // Assert
      expect(productCacheServiceMock.updateProduct).toHaveBeenCalledWith(
        event.data.productDetails
      );
    });
  });
});
```

### 8.2. Contract Tests

```typescript
// Pact consumer test for Product Service integration
describe("Product Service Pact", () => {
  let provider;

  beforeAll(async () => {
    provider = new PactV3({
      consumer: "OrderService",
      provider: "ProductService",
    });
  });

  describe("get product details", () => {
    it("should return product details", async () => {
      // Arrange
      const productId = "e8acc97f-c204-4c53-9c33-5d91a1061618";

      await provider.addInteraction({
        states: [{ description: "a product exists" }],
        uponReceiving: "a request for product details",
        withRequest: {
          method: "GET",
          path: `/api/v1/products/${productId}`,
        },
        willRespondWith: {
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: {
            id: productId,
            name: "Ergonomic Office Chair",
            basePrice: 249.99,
            status: "ACTIVE",
          },
        },
      });

      // Act
      const client = new ProductServiceClient(
        `${provider.mockService.baseUrl}`
      );
      const product = await client.getProduct(productId);

      // Assert
      expect(product.id).toBe(productId);
      expect(product.name).toBe("Ergonomic Office Chair");
    });
  });

  describe("product events", () => {
    it("should produce valid product.details_requested events", async () => {
      // Arrange
      const messageProvider = new MessageProviderPact({
        consumer: "OrderService",
        provider: "ProductService",
        pactBrokerUrl: process.env.PACT_BROKER_URL,
      });

      // Act & Assert
      await messageProvider.verifyMessageConsumer(
        "a product.details_requested event",
        {
          id: uuidv4(),
          type: "product.details_requested",
          source: "order-service",
          dataVersion: "1.0",
          timestamp: new Date().toISOString(),
          correlationId: uuidv4(),
          data: {
            productId: "e8acc97f-c204-4c53-9c33-5d91a1061618",
            requestId: uuidv4(),
            callbackEvent: "product.details_provided",
          },
        }
      );
    });
  });
});
```

## 9. Performance Considerations

1. **Batch Requests**: Use batch endpoints for multiple products to reduce network overhead
2. **Caching**: Cache frequently accessed product data with appropriate TTL
3. **Request Timeout**: Set appropriate timeouts for Product Service requests (500ms default)
4. **Connection Pooling**: Use HTTP connection pooling for efficient API calls
5. **Asynchronous Processing**: Process non-critical product updates asynchronously
6. **Event Chunking**: Split large event payloads into manageable chunks
7. **Scheduled Prefetching**: Proactively request product data during off-peak hours

## 10. Monitoring

1. **Service Health Checks**: Regular pings to the Product Service API to verify availability
2. **Request Metrics**: Track response times, error rates, and throughput of both synchronous and asynchronous operations
3. **Circuit Breaker Status**: Monitor open/closed status of the circuit breaker
4. **Cache Hit Ratio**: Track cache effectiveness for product data
5. **Discrepancy Alerts**: Alert on significant price or availability discrepancies
6. **Event Success Rate**: Monitor success rates of event publishing and processing
7. **Asynchronous Request Completion Time**: Track time from request to response for asynchronous operations

## 11. References

- [Product Service API Specification](../../product-service/04-api-endpoints/00-api-index.md)
- [Event-Driven Architecture Standards](../../../architecture/quality-standards/01-event-driven-architecture-standards.md)
- [Order Service Data Model](../02-data-model-setup/00-data-model-index.md)
- [API Gateway Configuration](../../infrastructure/api-gateway.md)
- [Caching Strategy](../../architecture/patterns/caching-strategy.md)
- [Asynchronous Request-Reply Pattern](../../../architecture/patterns/async-request-reply.md)
