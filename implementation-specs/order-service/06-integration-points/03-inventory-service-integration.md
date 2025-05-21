# Order Service Integration with Inventory Service

## 1. Overview

This document outlines the integration between the Order Service and the Inventory Service. This integration is critical for ensuring product availability, managing inventory levels during order processing, and preventing overselling. The Order Service interacts with the Inventory Service both synchronously and asynchronously throughout the order lifecycle.

## 2. Integration Points

### 2.1. Synchronous Integrations (REST API)

| Operation           | Endpoint                               | Method | Purpose                                                           |
| ------------------- | -------------------------------------- | ------ | ----------------------------------------------------------------- |
| Check Availability  | `/api/v1/inventory/check-availability` | POST   | Verify if all items in a cart are available before order creation |
| Reserve Inventory   | `/api/v1/inventory/reserve`            | POST   | Place a temporary hold on inventory during checkout               |
| Release Reservation | `/api/v1/inventory/release`            | POST   | Release a reservation when an order is cancelled or fails payment |

### 2.2. Asynchronous Integrations (Events)

| Event                           | Publisher         | Subscriber        | Purpose                                                     |
| ------------------------------- | ----------------- | ----------------- | ----------------------------------------------------------- |
| `order.created`                 | Order Service     | Inventory Service | Signal to validate and confirm inventory reservations       |
| `order.cancelled`               | Order Service     | Inventory Service | Signal to release reserved inventory                        |
| `order.returned`                | Order Service     | Inventory Service | Signal to restock returned items                            |
| `inventory.confirm_requested`   | Order Service     | Inventory Service | Request to confirm inventory deduction after order creation |
| `inventory.confirmed`           | Inventory Service | Order Service     | Confirm that inventory has been successfully deducted       |
| `inventory.confirmation_failed` | Inventory Service | Order Service     | Signal that inventory confirmation failed                   |
| `inventory.out_of_stock`        | Inventory Service | Order Service     | Alert Order Service when a product becomes unavailable      |
| `inventory.low_stock`           | Inventory Service | Order Service     | Inform Order Service when inventory reaches low threshold   |

## 3. Data Models

### 3.1. Request/Response Models

#### Check Availability Request

```json
{
  "items": [
    {
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "quantity": 2
    },
    {
      "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
      "variantId": "4f6a9b7c-0e2d-4f37-9a3c-2e9a4e3b5c1d",
      "quantity": 1
    }
  ]
}
```

#### Check Availability Response

```json
{
  "success": true,
  "data": {
    "available": true,
    "items": [
      {
        "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
        "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "available": true,
        "requestedQuantity": 2,
        "availableQuantity": 15
      },
      {
        "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
        "variantId": "4f6a9b7c-0e2d-4f37-9a3c-2e9a4e3b5c1d",
        "available": true,
        "requestedQuantity": 1,
        "availableQuantity": 8
      }
    ]
  },
  "meta": {
    "timestamp": "2023-11-21T15:27:30.123Z"
  }
}
```

#### Reserve Inventory Request

```json
{
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "items": [
    {
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "quantity": 2
    },
    {
      "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
      "variantId": "4f6a9b7c-0e2d-4f37-9a3c-2e9a4e3b5c1d",
      "quantity": 1
    }
  ],
  "expiresIn": 1800, // Reservation time in seconds (30 minutes)
  "metadata": {
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }
}
```

#### Reserve Inventory Response

```json
{
  "success": true,
  "data": {
    "reservationId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "items": [
      {
        "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
        "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "quantity": 2,
        "reserved": true
      },
      {
        "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
        "variantId": "4f6a9b7c-0e2d-4f37-9a3c-2e9a4e3b5c1d",
        "quantity": 1,
        "reserved": true
      }
    ],
    "expiresAt": "2023-11-21T15:57:30.123Z"
  },
  "meta": {
    "timestamp": "2023-11-21T15:27:30.123Z"
  }
}
```

### 3.2. Event Payloads

#### Order Created Event

```json
{
  "eventType": "order.created",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "items": [
    {
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "quantity": 2
    },
    {
      "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
      "variantId": "4f6a9b7c-0e2d-4f37-9a3c-2e9a4e3b5c1d",
      "quantity": 1
    }
  ],
  "reservationId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "timestamp": "2023-11-21T15:27:30.123Z"
}
```

#### Order Cancelled Event

```json
{
  "eventType": "order.cancelled",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "items": [
    {
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "quantity": 2
    },
    {
      "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
      "variantId": "4f6a9b7c-0e2d-4f37-9a3c-2e9a4e3b5c1d",
      "quantity": 1
    }
  ],
  "reason": "CUSTOMER_CANCELLED",
  "timestamp": "2023-11-21T16:15:45.789Z"
}
```

## 4. Sequence Diagrams

### 4.1. Order Creation Flow

```
┌─────────┐          ┌─────────────┐          ┌────────────────┐
│  User   │          │Order Service│          │Inventory Service│
└────┬────┘          └──────┬──────┘          └────────┬───────┘
     │                       │                          │
     │ Create Order Request  │                          │
     │──────────────────────>│                          │
     │                       │                          │
     │                       │ Check Availability       │
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │ Availability Response    │
     │                       │<─────────────────────────│
     │                       │                          │
     │                       │ Reserve Inventory        │
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │ Reservation Confirmation │
     │                       │<─────────────────────────│
     │                       │                          │
     │                       │ Process Payment          │
     │                       │                          │
     │                       │ Create Order Record      │
     │                       │                          │
     │ Order Confirmation    │                          │
     │<──────────────────────│                          │
     │                       │                          │
     │                       │ Publish inventory.confirm_requested |
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │ Publish order.created    │
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │                          │ Confirm inventory
     │                       │                          │ deduction
     │                       │                          │
     │                       │ Publish inventory.confirmed |
     │                       │<─────────────────────────│
     │                       │                          │
     │                       │ Update order status      │
     │                       │ with confirmed inventory │
     │                       │                          │
┌────┴────┐          ┌──────┴──────┐          ┌────────┴───────┐
│  User   │          │Order Service│          │Inventory Service│
└─────────┘          └─────────────┘          └────────────────┘
```

### 4.2. Order Cancellation Flow

```
┌─────────┐          ┌─────────────┐          ┌────────────────┐
│  User   │          │Order Service│          │Inventory Service│
└────┬────┘          └──────┬──────┘          └────────┬───────┘
     │                       │                          │
     │ Cancel Order Request  │                          │
     │──────────────────────>│                          │
     │                       │                          │
     │                       │ Update Order Status      │
     │                       │ to CANCELLED             │
     │                       │                          │
     │                       │ Publish order.cancelled  │
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │                          │ Release inventory
     │                       │                          │ reservation
     │                       │                          │
     │ Cancellation Confirmed│                          │
     │<──────────────────────│                          │
     │                       │                          │
┌────┴────┐          ┌──────┴──────┐          ┌────────┴───────┐
│  User   │          │Order Service│          │Inventory Service│
└─────────┘          └─────────────┘          └────────────────┘
```

## 5. Service Client Implementation

The Order Service implements an Inventory Service client to handle the synchronous communication and uses events for asynchronous operations:

```typescript
@Injectable()
export class InventoryServiceClient {
  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
    private readonly logger: Logger,
    private readonly eventBus: EventBus
  ) {}

  private readonly baseUrl = this.configService.get<string>(
    "INVENTORY_SERVICE_URL"
  );
  private readonly timeout =
    this.configService.get<number>("INVENTORY_SERVICE_TIMEOUT") || 3000;

  /**
   * Check availability of items
   */
  async checkAvailability(
    items: OrderItemDto[]
  ): Promise<AvailabilityResponseDto> {
    this.logger.log(`Checking availability for ${items.length} items`);

    try {
      const response = await firstValueFrom(
        this.httpService
          .post<AvailabilityResponseDto>(
            `${this.baseUrl}/api/v1/inventory/check-availability`,
            { items }
          )
          .pipe(
            timeout(this.timeout),
            catchError((error) => {
              this.logger.error(
                `Error checking inventory availability: ${error.message}`,
                error.stack
              );
              throw new ServiceUnavailableException(
                "Inventory service is currently unavailable"
              );
            })
          )
      );

      return response.data;
    } catch (error) {
      // Handle different types of errors
      if (error instanceof TimeoutError) {
        throw new RequestTimeoutException(
          "Inventory availability check timed out"
        );
      }

      throw error;
    }
  }

  /**
   * Reserve inventory for an order
   */
  async reserveInventory(
    orderId: string,
    items: OrderItemDto[],
    userId: string
  ): Promise<ReservationResponseDto> {
    this.logger.log(`Reserving inventory for order ${orderId}`);

    try {
      const response = await firstValueFrom(
        this.httpService
          .post<ReservationResponseDto>(
            `${this.baseUrl}/api/v1/inventory/reserve`,
            {
              orderId,
              items,
              expiresIn: 1800, // 30 minutes
              metadata: { userId },
            }
          )
          .pipe(
            timeout(this.timeout),
            catchError((error) => {
              if (error.response) {
                // Handle specific inventory service errors
                if (error.response.status === 409) {
                  throw new ConflictException(
                    "Insufficient inventory available"
                  );
                }
              }

              this.logger.error(
                `Error reserving inventory: ${error.message}`,
                error.stack
              );
              throw new ServiceUnavailableException(
                "Inventory service is currently unavailable"
              );
            })
          )
      );

      return response.data;
    } catch (error) {
      // Re-throw specific exceptions
      if (
        error instanceof ConflictException ||
        error instanceof RequestTimeoutException ||
        error instanceof ServiceUnavailableException
      ) {
        throw error;
      }

      // Generic error
      throw new InternalServerErrorException("Failed to reserve inventory");
    }
  }

  /**
   * Release inventory reservation
   */
  async releaseReservation(orderId: string): Promise<void> {
    this.logger.log(`Releasing inventory reservation for order ${orderId}`);

    try {
      await firstValueFrom(
        this.httpService
          .post(`${this.baseUrl}/api/v1/inventory/release`, { orderId })
          .pipe(
            timeout(this.timeout),
            catchError((error) => {
              this.logger.error(
                `Error releasing inventory: ${error.message}`,
                error.stack
              );
              // We don't want to throw an error in this case as it could block the cancellation flow
              // Instead, we'll log it for retry and monitoring
              return of(null);
            })
          )
      );
    } catch (error) {
      // Log but don't throw
      this.logger.error(
        `Failed to release inventory for order ${orderId}: ${error.message}`
      );
    }
  }

  /**
   * Request inventory confirmation asynchronously
   */
  async requestInventoryConfirmation(
    orderId: string,
    reservationId: string
  ): Promise<void> {
    this.logger.log(`Requesting inventory confirmation for order ${orderId}`);

    try {
      // Publish event to request inventory confirmation
      await this.eventBus.publish({
        id: uuidv4(),
        type: "inventory.confirm_requested",
        source: "order-service",
        dataVersion: "1.0",
        timestamp: new Date().toISOString(),
        correlationId: orderId,
        data: {
          orderId,
          reservationId,
        },
      });
    } catch (error) {
      this.logger.error(
        `Error publishing inventory confirmation request: ${error.message}`,
        error.stack
      );
      // We still log the error but don't block the flow
      // A background process will retry failed event publishing
    }
  }
}
```

## 6. Event Handlers

The Order Service implements handlers for inventory-related events:

```typescript
@Injectable()
export class InventoryEventHandlers {
  constructor(
    private readonly orderService: OrderService,
    private readonly logger: Logger
  ) {}

  @EventPattern("inventory.confirmed")
  async handleInventoryConfirmed(
    @Payload() event: InventoryConfirmedEvent,
    @Ctx() context: NatsContext
  ): Promise<void> {
    const { id: eventId, data } = event;
    const { orderId, reservationId } = data;

    this.logger.log(
      `Processing inventory.confirmed event ${eventId} for order ${orderId}`
    );

    try {
      // Update order with confirmed inventory status
      await this.orderService.updateOrderInventoryStatus(
        orderId,
        "INVENTORY_CONFIRMED",
        {
          reservationId,
          confirmedAt: new Date().toISOString(),
        }
      );

      // Acknowledge event
      context.getMessage().ack();
    } catch (error) {
      this.logger.error(
        `Error processing inventory confirmed event: ${error.message}`,
        error.stack
      );
      // Negative acknowledge to trigger retry
      context.getMessage().nak();
    }
  }

  @EventPattern("inventory.confirmation_failed")
  async handleInventoryConfirmationFailed(
    @Payload() event: InventoryConfirmationFailedEvent,
    @Ctx() context: NatsContext
  ): Promise<void> {
    const { id: eventId, data } = event;
    const { orderId, reservationId, reason } = data;

    this.logger.log(
      `Processing inventory.confirmation_failed event ${eventId} for order ${orderId}`
    );

    try {
      // Update order with inventory failure status
      await this.orderService.updateOrderInventoryStatus(
        orderId,
        "INVENTORY_FAILED",
        {
          reservationId,
          failureReason: reason,
          failedAt: new Date().toISOString(),
        }
      );

      // Flag order for review
      await this.orderService.flagOrderForReview(
        orderId,
        "INVENTORY_CONFIRMATION_FAILED",
        `Inventory confirmation failed: ${reason}`
      );

      // Acknowledge event
      context.getMessage().ack();
    } catch (error) {
      this.logger.error(
        `Error processing inventory confirmation failed event: ${error.message}`,
        error.stack
      );
      // Negative acknowledge to trigger retry
      context.getMessage().nak();
    }
  }

  @EventPattern("inventory.out_of_stock")
  async handleInventoryOutOfStock(
    @Payload() event: InventoryOutOfStockEvent,
    @Ctx() context: NatsContext
  ): Promise<void> {
    const { id: eventId, data } = event;
    const { productId, variantId } = data;

    this.logger.log(
      `Processing inventory.out_of_stock event ${eventId} for product ${productId}`
    );

    try {
      // Update product availability status in cache
      await this.orderService.updateProductAvailability(
        productId,
        variantId,
        false
      );

      // Acknowledge event
      context.getMessage().ack();
    } catch (error) {
      this.logger.error(
        `Error processing out of stock event: ${error.message}`,
        error.stack
      );
      // Negative acknowledge to trigger retry
      context.getMessage().nak();
    }
  }
}
```

## 7. Resilience Patterns

### 7.1. Circuit Breaker

The Order Service implements a circuit breaker pattern for Inventory Service calls to prevent cascading failures:

```typescript
// Circuit breaker implementation using NestJS-specific tools
import { CircuitBreaker, CircuitBreakerOptions } from "nestjs-circuit-breaker";

@Injectable()
export class InventoryServiceWithCircuitBreaker {
  constructor(
    private readonly inventoryServiceClient: InventoryServiceClient,
    private readonly logger: Logger
  ) {}

  @CircuitBreaker({
    resetTimeout: 30000, // 30 seconds
    errorThresholdPercentage: 50,
    rollingCountTimeout: 10000,
    rollingCountBuckets: 10,
    name: "inventoryServiceChecker",
  })
  async checkAvailability(
    items: OrderItemDto[]
  ): Promise<AvailabilityResponseDto> {
    return this.inventoryServiceClient.checkAvailability(items);
  }

  @CircuitBreaker({
    resetTimeout: 30000, // 30 seconds
    errorThresholdPercentage: 50,
    rollingCountTimeout: 10000,
    rollingCountBuckets: 10,
    name: "inventoryServiceReserver",
  })
  async reserveInventory(
    orderId: string,
    items: OrderItemDto[],
    userId: string
  ): Promise<ReservationResponseDto> {
    return this.inventoryServiceClient.reserveInventory(orderId, items, userId);
  }

  // Similar circuit breaker implementations for other methods
}
```

### 7.2. Retry with Backoff

For critical operations, a retry strategy with exponential backoff is implemented:

```typescript
// Retry strategies are implemented in the client methods
// See the reserveInventory and confirmInventoryDeduction methods in InventoryServiceClient
```

### 7.3. Fallback Mechanisms

When integration with the Inventory Service fails, the Order Service implements the following fallbacks:

1. **Availability Check Failures**:

   - For high-priority customers: Allow order to proceed with a flag for manual review
   - For standard customers: Error message requesting to try again later

2. **Reservation Failures**:
   - Fault monitoring triggers for operations team
   - Retry mechanism with notification
   - If all retries fail, order is placed in a special "pending inventory" state for manual review

## 8. Error Handling

### 8.1. Error Codes and Messages

| Error Code               | HTTP Status | Description                                      | Action                           |
| ------------------------ | ----------- | ------------------------------------------------ | -------------------------------- |
| `INVENTORY_UNAVAILABLE`  | 503         | Inventory service is unavailable                 | Retry after delay                |
| `INSUFFICIENT_INVENTORY` | 409         | One or more products don't have enough inventory | Notify user to adjust quantities |
| `INVENTORY_TIMEOUT`      | 408         | Inventory operation took too long                | Retry with backoff               |
| `RESERVATION_FAILED`     | 422         | Failed to reserve inventory                      | Check inventory status and retry |
| `RELEASE_FAILED`         | 500         | Failed to release inventory                      | Trigger manual review            |

### 8.2. Error Handling Strategy

The Order Service implements a multi-layered error handling approach:

1. **Immediate Retry** - For transient errors (network issues, timeouts)
2. **Delayed Retry** - For service unavailability with exponential backoff
3. **Graceful Degradation** - Limited functionality when the Inventory Service is down
4. **Manual Resolution Queue** - Critical failures that can't be handled automatically

## 9. Monitoring and Alerting

### 9.1. Key Metrics

1. **Inventory Service Response Time** - Latency of inventory operations
2. **Availability Check Success Rate** - Percentage of successful availability checks
3. **Reservation Success Rate** - Percentage of successful inventory reservations
4. **Circuit Breaker Status** - Open/closed status of the Inventory Service circuit breaker
5. **Inventory-Related Order Failures** - Count of orders failing due to inventory issues

### 9.2. Alerts

1. **Circuit Breaker Open** - Alert when the Inventory Service circuit breaker trips
2. **High Reservation Failure Rate** - Alert when reservation success rate drops below 95%
3. **Reservation Queue Depth** - Alert when the pending reservation queue grows beyond threshold
4. **Multiple Failed Releases** - Alert when inventory release operations fail repeatedly
5. **Inventory Service Latency** - Alert when latency exceeds 1 second for availability checks

## 10. Testing Strategy

### 10.1. Unit Tests

```typescript
// Unit test for Inventory Service client
describe("InventoryServiceClient", () => {
  let client: InventoryServiceClient;
  let httpService: HttpService;
  let logger: Logger;

  beforeEach(() => {
    // Setup test mocks and DI
  });

  describe("checkAvailability", () => {
    it("should return availability status when service responds successfully", async () => {
      // Test implementation
    });

    it("should throw ServiceUnavailableException when service is down", async () => {
      // Test implementation
    });

    it("should throw RequestTimeoutException when service times out", async () => {
      // Test implementation
    });
  });

  // Additional test cases
});
```

### 10.2. Integration Tests

```typescript
// Integration test for Order Service with Inventory Service
describe("Order-Inventory Integration", () => {
  let app: INestApplication;
  let orderService: OrderService;
  let mockInventoryService: Server;

  beforeAll(async () => {
    // Setup mock Inventory Service
    mockInventoryService = setupMockInventoryService();

    // Setup test app with real Order Service
    const moduleFixture = await Test.createTestingModule({
      // Module configuration
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();

    orderService = app.get<OrderService>(OrderService);
  });

  afterAll(async () => {
    // Cleanup
    await app.close();
    mockInventoryService.close();
  });

  it("should successfully create an order with inventory reservation", async () => {
    // Test full order creation flow with inventory integration
  });

  it("should handle inventory service outage gracefully", async () => {
    // Test with inventory service down
  });

  // Additional test cases
});
```

### 10.3. Contract Testing

The Order Service implements contract testing using Pact.js to verify integration with the Inventory Service:

```typescript
// Pact consumer test for Order Service
describe("Order Service as Inventory Service Consumer", () => {
  const provider = new PactV3({
    consumer: "OrderService",
    provider: "InventoryService",
  });

  // Define interactions and expectations

  // Define test cases
});
```

## 11. References

- [Order Service API Specifications](../04-api-endpoints/00-api-index.md)
- [Inventory Service API Specifications](../../inventory-service/04-api-endpoints/01-inventory-api.md)
- [Order Entity Model](../02-data-model-setup/01-order-entity.md)
- [Order Item Entity Model](../02-data-model-setup/02-order-item-entity.md)
- [Circuit Breaker Pattern](../../../architecture/adr/ADR-009-resilience-patterns.md)
- [Event-Driven Architecture](../../../architecture/adr/ADR-007-event-driven-architecture.md)
