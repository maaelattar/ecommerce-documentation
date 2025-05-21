# Order Service Integration with Notification Service

## 1. Overview

This document outlines the integration between the Order Service and the Notification Service. This integration enables the Order Service to trigger various types of customer notifications throughout the order lifecycle, including order confirmations, shipping updates, cancellation notices, and more. The integration follows an event-driven, asynchronous pattern to ensure loose coupling and high resilience.

## 2. Integration Points

### 2.1. Synchronous Integrations

None. The Order Service communicates with the Notification Service exclusively through asynchronous event-based integration to ensure maximum resilience and decoupling.

### 2.2. Asynchronous Integrations (Events)

| Event                         | Publisher            | Subscriber           | Purpose                                       |
| ----------------------------- | -------------------- | -------------------- | --------------------------------------------- |
| `order.created`               | Order Service        | Notification Service | Trigger order confirmation notification       |
| `order.updated`               | Order Service        | Notification Service | Alert customer about changes to their order   |
| `order.cancelled`             | Order Service        | Notification Service | Notify customer about order cancellation      |
| `order.shipped`               | Order Service        | Notification Service | Notify customer that order has shipped        |
| `order.delivered`             | Order Service        | Notification Service | Notify customer that order has been delivered |
| `order.delivery_delayed`      | Order Service        | Notification Service | Alert customer about delivery delay           |
| `order.return_approved`       | Order Service        | Notification Service | Confirm return request approval               |
| `order.refund_initiated`      | Order Service        | Notification Service | Notify customer about refund initiation       |
| `order.refund_completed`      | Order Service        | Notification Service | Confirm refund completion                     |
| `notification.send_requested` | Order Service        | Notification Service | Request to send a specific notification       |
| `notification.sent`           | Notification Service | Order Service        | Confirm a notification was sent successfully  |
| `notification.failed`         | Notification Service | Order Service        | Report failure in notification delivery       |

## 3. Data Models

### 3.1. Event Payloads

#### Notification Send Requested Event

```json
{
  "eventType": "notification.send_requested",
  "notificationId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "type": "ORDER_CONFIRMATION",
  "channels": ["EMAIL", "SMS"],
  "priority": "HIGH",
  "recipient": {
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "customer@example.com",
    "phone": "+15551234567",
    "preferredLanguage": "en",
    "preferredChannel": "EMAIL"
  },
  "templateData": {
    "orderNumber": "ORD-12345678",
    "customerName": "Jane Doe",
    "orderDate": "2023-11-21T15:27:30.123Z",
    "orderItems": [
      {
        "name": "Ergonomic Desk Chair",
        "quantity": 1,
        "price": 299.99
      },
      {
        "name": "Adjustable Standing Desk",
        "quantity": 1,
        "price": 649.99
      }
    ],
    "shippingAddress": {
      "line1": "123 Main Street",
      "city": "Boston",
      "state": "MA",
      "postal": "02108",
      "country": "US"
    },
    "subtotal": 949.98,
    "tax": 79.5,
    "shipping": 0,
    "total": 1029.48
  },
  "idempotencyKey": "ord_f47ac10b-58cc-4372-a567-0e02b2c3d479_confirmation",
  "timestamp": "2023-11-21T15:27:35.123Z"
}
```

#### Notification Sent Event

```json
{
  "eventType": "notification.sent",
  "notificationId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "type": "ORDER_CONFIRMATION",
  "channels": ["EMAIL"],
  "recipient": {
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "customer@example.com"
  },
  "sentAt": "2023-11-21T15:27:38.456Z",
  "deliveryStatus": "DELIVERED",
  "messageId": "msg_5f9c1b2a-3d7e-4b0f-8d7c-6a5d8b9e1f3a",
  "timestamp": "2023-11-21T15:27:40.789Z"
}
```

#### Notification Failed Event

```json
{
  "eventType": "notification.failed",
  "notificationId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "type": "ORDER_CONFIRMATION",
  "channels": ["SMS"],
  "recipient": {
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "phone": "+15551234567"
  },
  "failedAt": "2023-11-21T15:27:39.123Z",
  "errorCode": "INVALID_PHONE_NUMBER",
  "errorMessage": "Phone number is not valid or unreachable",
  "retryCount": 2,
  "willRetry": false,
  "timestamp": "2023-11-21T15:27:40.789Z"
}
```

## 4. Sequence Diagrams

### 4.1. Order Confirmation Notification Flow

```
┌─────────┐          ┌─────────────┐          ┌────────────────────┐
│  User   │          │Order Service │          │Notification Service│
└────┬────┘          └──────┬──────┘          └─────────┬──────────┘
     │                       │                           │
     │ Place Order           │                           │
     │──────────────────────>│                           │
     │                       │                           │
     │                       │ Process Order             │
     │                       │                           │
     │ Order Confirmation    │                           │
     │<──────────────────────│                           │
     │                       │                           │
     │                       │ Publish order.created     │
     │                       │──────────────────────────>│
     │                       │                           │
     │                       │                           │ Process event
     │                       │                           │ and prepare
     │                       │                           │ notification
     │                       │                           │
     │                       │                           │ Send notification
     │                       │                           │ to customer
     │                       │                           │
     │                       │ Publish notification.sent │
     │                       │<──────────────────────────│
     │                       │                           │
     │                       │ Update notification       │
     │                       │ status in order record    │
     │                       │                           │
     │ Email Notification    │                           │
     │<────────────────────────────────────────────────────
     │                       │                           │
┌────┴────┐          ┌──────┴──────┐          ┌─────────┴──────────┐
│  User   │          │Order Service │          │Notification Service│
└─────────┘          └─────────────┘          └────────────────────┘
```

### 4.2. Custom Notification Request Flow

```
┌─────────┐          ┌─────────────┐          ┌────────────────────┐
│  Admin   │          │Order Service │          │Notification Service│
└────┬────┘          └──────┬──────┘          └─────────┬──────────┘
     │                       │                           │
     │ Request to send       │                           │
     │ custom notification   │                           │
     │──────────────────────>│                           │
     │                       │                           │
     │                       │ Publish notification.send_requested │
     │                       │──────────────────────────>│
     │                       │                           │
     │                       │                           │ Process request
     │                       │                           │ and send
     │                       │                           │ notification
     │                       │                           │
     │                       │ Publish notification.sent │
     │                       │<──────────────────────────│
     │                       │                           │
     │ Notification Sent     │                           │
     │ Confirmation          │                           │
     │<──────────────────────│                           │
     │                       │                           │
┌────┴────┐          ┌──────┴──────┐          ┌─────────┴──────────┐
│  Admin   │          │Order Service │          │Notification Service│
└─────────┘          └─────────────┘          └────────────────────┘
```

## 5. Service Client Implementation

The Order Service implements a Notification Publisher component to handle event publishing:

```typescript
@Injectable()
export class NotificationPublisher {
  constructor(
    private readonly eventBus: EventBus,
    private readonly logger: Logger,
    private readonly configService: ConfigService
  ) {}

  /**
   * Request to send an order confirmation notification
   */
  async requestOrderConfirmationNotification(
    order: Order,
    customer: CustomerDto
  ): Promise<void> {
    this.logger.log(`Requesting order confirmation for order ${order.id}`);

    try {
      // Build notification data
      const notificationData = this.buildOrderConfirmationData(order, customer);

      // Publish event to request notification
      await this.eventBus.publish({
        id: uuidv4(),
        type: "notification.send_requested",
        source: "order-service",
        dataVersion: "1.0",
        timestamp: new Date().toISOString(),
        correlationId: order.id,
        data: notificationData,
      });

      this.logger.log(
        `Order confirmation notification request published for order ${order.id}`
      );
    } catch (error) {
      this.logger.error(
        `Error requesting order confirmation notification: ${error.message}`,
        error.stack
      );
      // Add to retry queue for background processing
      await this.addToRetryQueue("ORDER_CONFIRMATION", order.id, {
        order,
        customer,
      });
    }
  }

  /**
   * Request to send an order cancellation notification
   */
  async requestOrderCancellationNotification(
    order: Order,
    cancellationReason: string
  ): Promise<void> {
    this.logger.log(
      `Requesting cancellation notification for order ${order.id}`
    );

    try {
      // Build notification data
      const notificationData = this.buildOrderCancellationData(
        order,
        cancellationReason
      );

      // Publish event to request notification
      await this.eventBus.publish({
        id: uuidv4(),
        type: "notification.send_requested",
        source: "order-service",
        dataVersion: "1.0",
        timestamp: new Date().toISOString(),
        correlationId: order.id,
        data: notificationData,
      });

      this.logger.log(
        `Order cancellation notification request published for order ${order.id}`
      );
    } catch (error) {
      this.logger.error(
        `Error requesting order cancellation notification: ${error.message}`,
        error.stack
      );
      // Add to retry queue for background processing
      await this.addToRetryQueue("ORDER_CANCELLATION", order.id, {
        order,
        cancellationReason,
      });
    }
  }

  /**
   * Request to send an order shipped notification
   */
  async requestOrderShippedNotification(
    order: Order,
    shippingDetails: ShippingDetailsDto
  ): Promise<void> {
    this.logger.log(`Requesting shipped notification for order ${order.id}`);

    try {
      // Build notification data
      const notificationData = this.buildOrderShippedData(
        order,
        shippingDetails
      );

      // Publish event to request notification
      await this.eventBus.publish({
        id: uuidv4(),
        type: "notification.send_requested",
        source: "order-service",
        dataVersion: "1.0",
        timestamp: new Date().toISOString(),
        correlationId: order.id,
        data: notificationData,
      });

      this.logger.log(
        `Order shipped notification request published for order ${order.id}`
      );
    } catch (error) {
      this.logger.error(
        `Error requesting order shipped notification: ${error.message}`,
        error.stack
      );
      // Add to retry queue for background processing
      await this.addToRetryQueue("ORDER_SHIPPED", order.id, {
        order,
        shippingDetails,
      });
    }
  }

  /**
   * Helper method to build order confirmation notification data
   */
  private buildOrderConfirmationData(
    order: Order,
    customer: CustomerDto
  ): Record<string, any> {
    return {
      notificationId: uuidv4(),
      orderId: order.id,
      type: "ORDER_CONFIRMATION",
      channels: ["EMAIL", "SMS"],
      priority: "HIGH",
      recipient: {
        userId: customer.id,
        email: customer.email,
        phone: customer.phone,
        preferredLanguage: customer.preferredLanguage || "en",
        preferredChannel: customer.preferredChannel || "EMAIL",
      },
      templateData: {
        orderNumber: order.orderNumber,
        customerName: customer.name,
        orderDate: order.createdAt,
        orderItems: order.items.map((item) => ({
          name: item.productName,
          quantity: item.quantity,
          price: item.unitPrice,
        })),
        shippingAddress: {
          line1: order.shippingAddress.addressLine1,
          line2: order.shippingAddress.addressLine2,
          city: order.shippingAddress.city,
          state: order.shippingAddress.state,
          postal: order.shippingAddress.postalCode,
          country: order.shippingAddress.country,
        },
        subtotal: order.subtotal,
        tax: order.tax,
        shipping: order.shippingCost,
        total: order.total,
      },
      idempotencyKey: `ord_${order.id}_confirmation`,
    };
  }

  /**
   * Helper method to build order cancellation notification data
   */
  private buildOrderCancellationData(
    order: Order,
    cancellationReason: string
  ): Record<string, any> {
    // Similar implementation to buildOrderConfirmationData
    // with cancellation-specific fields
    return {
      notificationId: uuidv4(),
      orderId: order.id,
      type: "ORDER_CANCELLATION",
      // Additional fields...
    };
  }

  /**
   * Helper method to build order shipped notification data
   */
  private buildOrderShippedData(
    order: Order,
    shippingDetails: ShippingDetailsDto
  ): Record<string, any> {
    // Similar implementation to buildOrderConfirmationData
    // with shipping-specific fields
    return {
      notificationId: uuidv4(),
      orderId: order.id,
      type: "ORDER_SHIPPED",
      // Additional fields...
    };
  }

  /**
   * Add failed notification request to retry queue
   */
  private async addToRetryQueue(
    type: string,
    orderId: string,
    payload: any
  ): Promise<void> {
    // Implementation of retry queue logic
    // This would store the failed notification request
    // for background processing
  }
}
```

## 6. Event Handlers

The Order Service implements handlers for notification-related events:

```typescript
@Injectable()
export class NotificationEventHandlers {
  constructor(
    private readonly orderService: OrderService,
    private readonly logger: Logger
  ) {}

  @EventPattern("notification.sent")
  async handleNotificationSent(
    @Payload() event: NotificationSentEvent,
    @Ctx() context: NatsContext
  ): Promise<void> {
    const { id: eventId, data } = event;
    const { notificationId, orderId, type } = data;

    this.logger.log(
      `Processing notification.sent event ${eventId} for order ${orderId}`
    );

    try {
      // Update order notification status
      await this.orderService.updateNotificationStatus(orderId, type, "SENT", {
        notificationId,
        sentAt: data.sentAt,
        messageId: data.messageId,
      });

      // Acknowledge event
      context.getMessage().ack();
    } catch (error) {
      this.logger.error(
        `Error processing notification sent event: ${error.message}`,
        error.stack
      );
      // Negative acknowledge to trigger retry
      context.getMessage().nak();
    }
  }

  @EventPattern("notification.failed")
  async handleNotificationFailed(
    @Payload() event: NotificationFailedEvent,
    @Ctx() context: NatsContext
  ): Promise<void> {
    const { id: eventId, data } = event;
    const { notificationId, orderId, type, errorCode, errorMessage } = data;

    this.logger.log(
      `Processing notification.failed event ${eventId} for order ${orderId}`
    );

    try {
      // Update order notification status
      await this.orderService.updateNotificationStatus(
        orderId,
        type,
        "FAILED",
        {
          notificationId,
          failedAt: data.failedAt,
          errorCode,
          errorMessage,
          retryCount: data.retryCount,
          willRetry: data.willRetry,
        }
      );

      // If critical notification and no more retries planned,
      // flag order for manual intervention
      if (
        ["ORDER_CONFIRMATION", "ORDER_SHIPPED"].includes(type) &&
        !data.willRetry
      ) {
        await this.orderService.flagOrderForReview(
          orderId,
          "NOTIFICATION_FAILURE",
          `Failed to send ${type} notification: ${errorMessage}`
        );
      }

      // Acknowledge event
      context.getMessage().ack();
    } catch (error) {
      this.logger.error(
        `Error processing notification failed event: ${error.message}`,
        error.stack
      );
      // Negative acknowledge to trigger retry
      context.getMessage().nak();
    }
  }
}
```

## 7. Resilience Patterns

### 7.1. Retry Strategy

The Order Service implements a robust retry strategy for notification event publishing:

```typescript
// Example implementation of retry logic for event publishing
private async publishWithRetry(
  eventType: string,
  data: any,
  correlationId: string
): Promise<void> {
  const retryConfig = {
    retries: 3,
    minTimeout: 1000, // 1 second
    maxTimeout: 10000, // 10 seconds
    factor: 2, // exponential backoff factor
  };

  const operation = retry.operation(retryConfig);

  return new Promise((resolve, reject) => {
    operation.attempt(async (attemptNumber) => {
      try {
        this.logger.log(
          `Publishing ${eventType} event attempt ${attemptNumber}`
        );

        await this.eventBus.publish({
          id: uuidv4(),
          type: eventType,
          source: "order-service",
          dataVersion: "1.0",
          timestamp: new Date().toISOString(),
          correlationId,
          data,
        });

        resolve();
      } catch (error) {
        if (operation.retry(error)) {
          // Will retry
          this.logger.warn(
            `Retrying ${eventType} event publication after error: ${error.message}`
          );
          return;
        }

        // Max retries reached
        reject(operation.mainError() || error);
      }
    });
  });
}
```

### 7.2. Event Store and Outbox Pattern

For critical notifications, the Order Service implements an outbox pattern to ensure event delivery:

```typescript
// Pseudocode for outbox pattern implementation
@Transactional()
async createOrderWithNotification(orderData: CreateOrderDto): Promise<Order> {
  // Create order in database
  const order = await this.orderRepository.save(orderData);

  // Store outbox message
  await this.outboxRepository.save({
    aggregateType: 'Order',
    aggregateId: order.id,
    eventType: 'notification.send_requested',
    payload: {
      notificationId: uuidv4(),
      orderId: order.id,
      type: "ORDER_CONFIRMATION",
      // Additional notification data
    },
    createdAt: new Date()
  });

  return order;
}
```

A background process regularly polls the outbox table and publishes events that haven't been processed yet:

```typescript
@Injectable()
export class OutboxProcessor {
  @Cron("*/10 * * * * *") // Every 10 seconds
  async processOutbox() {
    // Get unpublished events
    const events = await this.outboxRepository.findUnpublished(50);

    for (const event of events) {
      try {
        // Publish event
        await this.eventBus.publish({
          id: event.id,
          type: event.eventType,
          source: "order-service",
          dataVersion: "1.0",
          timestamp: new Date().toISOString(),
          correlationId: event.aggregateId,
          data: event.payload,
        });

        // Mark as published
        await this.outboxRepository.markAsPublished(event.id);
      } catch (error) {
        // Update retry count
        await this.outboxRepository.incrementRetryCount(event.id);
      }
    }
  }
}
```

## 8. Error Handling

### 8.1. Error Scenarios and Mitigation

| Error Scenario                     | Mitigation Strategy                                    |
| ---------------------------------- | ------------------------------------------------------ |
| Event publishing failure           | Retry with exponential backoff + outbox pattern        |
| Notification service unavailable   | Event persistence with eventual consistency            |
| Critical notification failure      | Flag for manual review + alternative notification path |
| Customer contact information error | Fall back to available channel + flag for review       |
| Template rendering error           | Use default template + log detailed error              |

### 8.2. Dead Letter Queue

For notification events that repeatedly fail, a dead letter queue mechanism is implemented:

```typescript
// After max retries or specific errors
@Injectable()
export class DeadLetterQueueHandler {
  @EventPattern("notification.retry.maxattempts")
  async handleMaxRetries(@Payload() event: any) {
    // Log failure
    this.logger.error(
      `Max retries reached for notification: ${JSON.stringify(event)}`
    );

    // Store in DLQ table
    await this.deadLetterRepository.save({
      originalEvent: event,
      failureReason: "MAX_RETRIES_EXCEEDED",
      processedAt: null,
    });

    // Alert operations team for critical notifications
    if (this.isCriticalNotification(event.data.type)) {
      await this.alertService.sendOperationsAlert("NOTIFICATION_FAILURE", {
        orderId: event.data.orderId,
        notificationType: event.data.type,
        retryCount: event.data.retryCount || 0,
      });
    }
  }
}
```

## 9. Monitoring and Alerting

### 9.1. Key Metrics

1. **Notification Send Rate** - Count of notification requests per time period
2. **Notification Success Rate** - Percentage of successfully sent notifications
3. **Notification Failure Rate** - Percentage and count of failed notifications by type
4. **Event Publishing Success Rate** - Percentage of successful event publications
5. **Outbox Queue Size** - Number of pending notification events
6. **Dead Letter Queue Size** - Number of failed notification events

### 9.2. Alerts

1. **High Notification Failure Rate** - Alert when failure rate exceeds 5%
2. **Critical Notification Failure** - Immediate alert on ORDER_CONFIRMATION or ORDER_SHIPPED failures
3. **Dead Letter Queue Growth** - Alert when DLQ size increases beyond threshold
4. **Outbox Queue Buildup** - Alert when outbox processing falls behind
5. **Event Publishing Errors** - Alert on repeated event publishing failures

## 10. Testing Strategy

### 10.1. Unit Tests

```typescript
// Unit test for NotificationPublisher
describe("NotificationPublisher", () => {
  let publisher: NotificationPublisher;
  let eventBus: EventBus;
  let logger: Logger;

  beforeEach(() => {
    // Setup test mocks and DI
  });

  describe("requestOrderConfirmationNotification", () => {
    it("should publish a notification.send_requested event", async () => {
      // Test implementation
    });

    it("should handle publish errors by adding to retry queue", async () => {
      // Test implementation
    });
  });

  // Additional test cases
});
```

### 10.2. Integration Tests

```typescript
// Integration test for notification event handling
describe("Notification Integration", () => {
  let app: INestApplication;
  let orderService: OrderService;
  let notificationPublisher: NotificationPublisher;

  beforeAll(async () => {
    // Setup test app
    const moduleFixture = await Test.createTestingModule({
      // Module configuration
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();

    orderService = app.get<OrderService>(OrderService);
    notificationPublisher = app.get<NotificationPublisher>(
      NotificationPublisher
    );
  });

  afterAll(async () => {
    // Cleanup
    await app.close();
  });

  it("should handle notification.sent events properly", async () => {
    // Test implementation
  });

  it("should handle notification.failed events properly", async () => {
    // Test implementation
  });

  // Additional test cases
});
```

## 11. References

- [Order Service API Specifications](../04-api-endpoints/00-api-index.md)
- [Notification Service API Specifications](../../notification-service/04-api-endpoints/01-notification-api.md)
- [Order Entity Model](../02-data-model-setup/01-order-entity.md)
- [Event-Driven Architecture Standards](../../../architecture/quality-standards/01-event-driven-architecture-standards.md)
- [Outbox Pattern](../../../architecture/adr/ADR-012-outbox-pattern.md)
- [Retry Strategies](../../../architecture/adr/ADR-009-resilience-patterns.md)
