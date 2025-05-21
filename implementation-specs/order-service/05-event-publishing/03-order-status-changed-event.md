# `OrderStatusChangedEvent` Specification

## 1. Overview

This document specifies the `OrderStatusChangedEvent` published by the Order Service. This general-purpose event is emitted whenever an order's status transitions from one state to another, particularly for statuses not covered by more specific lifecycle events (e.g., `OrderShippedEvent`, `OrderPaymentCompletedEvent`).

It provides a notification that an order has changed its state, allowing other services to react accordingly. For critical lifecycle milestones with distinct data payloads, refer to their specific event documentation.

This event conforms to the `StandardMessage<T>` envelope detailed in the [Order Service Events Index](./00-events-index.md).

## 2. Event Details

| Attribute             | Value                                                                                          |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| `messageType`         | `OrderStatusChangedEvent`                                                                      |
| `source`              | `OrderService`                                                                                 |
| `messageVersion`      | `1.0` (Initial version)                                                                        |
| Potential Consumers   | Notification Service, Analytics Service, Customer Support Systems, other internal services tracking order progress. |
| Message Broker        | RabbitMQ (via Amazon MQ)                                                                       |
| Key `StandardMessage` Fields | `messageId`, `timestamp`, `correlationId` (optional), `partitionKey` (set to `orderId`)      |

## 3. Event Schema (`StandardMessage<OrderStatusChangedEventPayload>`)

Events are structured using the `StandardMessage<T>` envelope. The `payload` for an `OrderStatusChangedEvent` is `OrderStatusChangedEventPayload`.

### 3.1. `StandardMessage<T>` Envelope Example

```json
{
  "messageId": "msg-event-id-12345",
  "messageType": "OrderStatusChangedEvent",
  "messageVersion": "1.0",
  "timestamp": "2023-11-22T14:35:12.487Z",
  "source": "OrderService",
  "correlationId": "corr-op-67890", // Optional
  "partitionKey": "f47ac10b-58cc-4372-a567-0e02b2c3d479", // Value of orderId
  "payload": { // OrderStatusChangedEventPayload starts here
    "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    // ... other fields from OrderStatusChangedEventPayload ...
  }
}
```

### 3.2. `OrderStatusChangedEventPayload` Schema

```json
{
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6", // Optional, but good for context
  "previousStatus": "PAYMENT_PROCESSING", // Machine-readable status key
  "newStatus": "AWAITING_FULFILLMENT",   // Machine-readable status key
  "statusChangeTimestamp": "2023-11-22T14:35:12.487Z", // Timestamp of the actual status change
  "reason": "Payment successfully processed, order now awaiting fulfillment.", // Optional: Human-readable reason or system note
  "initiatedBy": "PaymentServiceCallback", // System, User ID, Service Name, or specific trigger
  "changeContext": { // Optional: Key-value pairs providing context specific to this status change
    "paymentTransactionId": "txn_123abc456efg",
    "fulfillmentHoldReason": null
  },
  "currentOrderSummary": { // Optional: A minimal summary of the order for context
    "totalAmount": 149.99,
    "currency": "USD",
    "itemCount": 2
  }
}
```

### 3.3. `OrderStatusChangedEventPayload` Field Definitions

| Field                   | Type     | Required | Description                                                                    |
| ----------------------- | -------- | -------- | ------------------------------------------------------------------------------ |
| `orderId`               | UUID     | Yes      | Unique identifier of the order. Used as `partitionKey`.                          |
| `userId`                | UUID     | No       | Identifier of the user who placed the order (contextual).                      |
| `previousStatus`        | String   | Yes      | The status of the order *before* this change (e.g., "PAYMENT_PROCESSING").     |
| `newStatus`             | String   | Yes      | The status of the order *after* this change (e.g., "AWAITING_FULFILLMENT").      |
| `statusChangeTimestamp` | ISO Date | Yes      | Timestamp when the status change was recorded (UTC).                             |
| `reason`                | String   | No       | Optional human-readable reason or system note for the status change.           |
| `initiatedBy`           | String   | No       | Identifier for the actor or process that triggered the change.                 |
| `changeContext`         | Object   | No       | Optional key-value pairs providing specific context for this transition.         |
| `currentOrderSummary`   | Object   | No       | Optional minimal summary of the order for quick reference by consumers.        |

**Note on `changeContext`:**
While this field is a generic object, specific status transitions might consistently include certain keys. For example:
- A change to `PAYMENT_FAILED` might include `{"paymentFailureCode": "card_declined", "paymentGatewayMessage": "Insufficient funds"}`.
- A change to `AWAITING_PICKUP` might include `{"pickupLocationId": "store-007", "pickupReadyBy": "2023-11-24T17:00:00Z"}`.
Consumers needing to react to specific details within `changeContext` should coordinate with the Order Service on expected keys for relevant transitions.

For major, well-defined lifecycle events like `OrderShippedEvent` or `OrderPaymentCompletedEvent`, those dedicated events carry richer, strongly-typed payloads and should be preferred by consumers needing that specific detail.

## 4. Publishing Logic

The `OrderStatusChangedEvent` is typically published when:

1.  An order's status is updated through an API call or internal process.
2.  The change does not correspond to a more specific, dedicated event (or is published in addition to it for general tracking).
3.  The status update is successfully persisted.

### 4.1. Implementation Example (using `@ecommerce-platform/rabbitmq-event-utils`)

```typescript
// Assumes RabbitMQProducerService, Order, StandardMessage etc. are available
// import { crypto } from 'crypto'; // For Node.js environment

@Injectable()
export class OrderStatusUpdaterService {
  constructor(
    private readonly orderRepository: OrderRepository, // Your data access layer
    private readonly rabbitMQProducerService: RabbitMQProducerService,
    private readonly logger: LoggerService // from @ecommerce-platform/nestjs-core-utils
  ) {}

  async updateOrderStatus(
    orderId: string, 
    newStatus: string, 
    previousStatus: string,
    details: { reason?: string; initiatedBy?: string; changeContext?: Record<string, any> }
  ): Promise<Order> {
    this.logger.log(`Updating status for order ${orderId} from ${previousStatus} to ${newStatus}`, 'OrderStatusUpdaterService');
    // ... logic to validate transition and persist order status update ...
    const updatedOrder = await this.orderRepository.updateStatus(orderId, newStatus, previousStatus, details.reason);

    const eventPayload: OrderStatusChangedEventPayload = {
      orderId: updatedOrder.id,
      userId: updatedOrder.userId,
      previousStatus: previousStatus,
      newStatus: newStatus,
      statusChangeTimestamp: new Date().toISOString(),
      reason: details.reason,
      initiatedBy: details.initiatedBy,
      changeContext: details.changeContext,
      currentOrderSummary: {
        totalAmount: updatedOrder.totalAmount,
        currency: updatedOrder.currency,
        itemCount: updatedOrder.items.length,
      }
    };

    const eventMessage: StandardMessage<OrderStatusChangedEventPayload> = {
      messageId: `msg-${crypto.randomUUID()}`,
      messageType: 'OrderStatusChangedEvent',
      messageVersion: '1.0',
      timestamp: new Date().toISOString(),
      source: 'OrderService',
      // correlationId: obtain if part of a larger operation
      partitionKey: updatedOrder.id,
      payload: eventPayload,
    };

    try {
      await this.rabbitMQProducerService.publish(
        'order.events', // Exchange name
        eventMessage.messageType, // Routing key
        eventMessage
      );
      this.logger.log(`Published ${eventMessage.messageType} for order ${updatedOrder.id}`, 'OrderStatusUpdaterService');
    } catch (error) {
      this.logger.error(
        `Failed to publish ${eventMessage.messageType} for order ${updatedOrder.id}: ${error.message}`,
        error.stack,
        'OrderStatusUpdaterService'
      );
      // Implement robust error handling (retry, DLQ for publisher, outbox pattern)
      throw error;
    }
    return updatedOrder;
  }
}
```

## 5. Event Handling by Consumers

Consumers of `OrderStatusChangedEvent` should:

-   Filter events based on `newStatus` and/or `previousStatus` to react only to relevant transitions.
-   Use the `changeContext` for additional details if needed, but be prepared for its variability.
-   Prefer consuming more specific events (e.g., `OrderShippedEvent`) if available and detailed payload information is critical.

(Refer to "General Consumer Responsibilities" in [00-events-index.md](./00-events-index.md) for common practices like idempotency, retries, DLQ handling.)

## 6. Versioning and Compatibility

Refer to the versioning strategy (`messageVersion`) outlined in [00-events-index.md](./00-events-index.md). The `changeContext` field, being an object, allows for additive changes without breaking consumers not specifically looking for those new keys.

## 7. Testing Considerations

-   **Publisher:** Test payload construction for various status transitions, ensuring `changeContext` is populated correctly where applicable. Test RabbitMQ publishing.
-   **Consumer:** Test logic for filtering relevant status changes. Test handling of different `changeContext` scenarios. Test idempotency.

## 8. Security Considerations

-   Standard RabbitMQ security (TLS, authN/authZ).
-   Ensure that sensitive details are not unnecessarily placed in `changeContext` if they are not meant for wide consumption.

## 9. References

-   [Order Service Events Index](./00-events-index.md)
-   `@ecommerce-platform/rabbitmq-event-utils` (Shared Library Documentation)
-   Relevant ADRs (e.g., ADR-018 for Message Broker Strategy)
-   Specific event documents for major lifecycle changes (e.g., `02-order-shipped-event.md`).
