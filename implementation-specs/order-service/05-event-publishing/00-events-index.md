# Order Service Event Publishing

## Introduction

This document outlines the event-driven architecture aspects of the Order Service. As a key component in the e-commerce platform, the Order Service publishes various events during the order lifecycle. These events enable loosely-coupled integration with other services and provide a reliable communication mechanism for asynchronous workflows.

The event publishing strategy follows the guidelines established in [ADR-007-event-driven-architecture](../../../architecture/adr/ADR-007-event-driven-architecture.md).

## Event Architecture

### Publishing Mechanism

The Order Service utilizes **RabbitMQ (via Amazon MQ for RabbitMQ)** for robust and reliable event publishing. This aligns with the platform's standardized approach (see ADR-018: Message Broker Strategy and TDAC/03: Message Broker Selection) and leverages the `@ecommerce-platform/rabbitmq-event-utils` shared library.

Key features of this mechanism include:

1.  **Exchanges**: Events are published to specific RabbitMQ exchanges (e.g., a direct exchange like `order.events`).
2.  **Routing Keys**: Messages are routed from the exchange to bound queues based on routing keys (often corresponding to the `messageType` or a specific entity ID in the `partitionKey`).
3.  **Queues**: Consumer services subscribe to dedicated queues to receive relevant events.
4.  **Producer Confirms**: Ensures messages are successfully received by the RabbitMQ broker.
5.  **Dead-Letter Exchanges/Queues (DLX/DLQ)**: For handling messages that cannot be processed successfully after retries.
6.  **Shared Library**: The `RabbitMQProducerService` from `@ecommerce-platform/rabbitmq-event-utils` simplifies publishing, incorporating best practices like standardized message envelopes (`StandardMessage<T>`).

### Event Flow Diagram (RabbitMQ)

```mermaid
graph TD
    A[Order Service] -- Publishes Event (StandardMessage<T>) --> B{Exchange (e.g., order.events)};
    B -- Routing Key (e.g., OrderCreated) --> C[Queue: ServiceX_OrderEvents];
    B -- Routing Key (e.g., OrderUpdated) --> D[Queue: ServiceY_OrderEvents];
    C --> E[Consumer Service X];
    D --> F[Consumer Service Y];
    B -.-> G((DLX for order.events));
    G --> H[DLQ_order.events];
```

This diagram illustrates the Order Service publishing an event to a RabbitMQ exchange. The exchange then routes the event to appropriate consumer queues based on routing keys. A Dead Letter Exchange (DLX) and Queue (DLQ) are configured for unprocessable messages.

## Event Types Published by Order Service

The Order Service publishes the following domain events. These events adhere to the `StandardMessage<T>` envelope, where the `messageType` corresponds to the event names listed below. The `partitionKey` will typically be the `orderId` for order-specific events.

| Event Name (messageType)                  | Description                                                                 | Trigger                                                                 |
| ----------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `OrderCreatedEvent`                       | A new order has been successfully created.                                  | Successful order creation process completion.                           |
| `OrderUpdatedEvent`                       | Significant details of an existing order have been updated.                 | Successful update of order data (e.g., shipping address before processing). |
| `OrderStatusChangedEvent`                 | The overall status of an order has changed.                                 | Change in order lifecycle state (e.g., `PROCESSING` to `SHIPPED`).        |
| `OrderCancelledEvent`                     | An order has been successfully cancelled.                                   | Successful order cancellation process.                                  |
| `OrderPaymentCompletedEvent`              | Payment for an order has been successfully completed and confirmed.         | Confirmation of successful payment from Payment Service.                  |
| `OrderPaymentFailedEvent`                 | Payment for an order has failed.                                            | Notification of payment failure from Payment Service.                     |
| `OrderRefundRequestedEvent`               | A refund has been requested for an order or part of an order.             | User or system initiates a refund request against an order.             |
| `OrderRefundProcessedEvent`               | A refund for an order has been successfully processed.                      | Confirmation of successful refund processing (e.g., from Payment Service). |
| `OrderShippedEvent`                       | An order or part of an order has been shipped.                              | Shipment information updated by fulfillment process.                      |
| `OrderDeliveredEvent`                     | An order or part of an order has been delivered to the customer.            | Delivery confirmation received.                                         |
| `OrderPaymentProcessingInitiatedEvent`    | The Order Service has initiated payment processing for an order.            | Order transitions to a state requiring payment processing.              |
| `OrderConfirmationNotificationRequestedEvent` | A request to send an order confirmation notification to the user.         | Typically after successful order creation or payment.                   |
| `OrderPlacedForAnalyticsEvent`            | An order has been placed and its core data is available for analytics.    | Successful order placement, for consumption by analytics systems.         |

*Note: Events like `inventory.items_reserved` or `payment.processing_initiated` (if seen as direct communication from other services) are typically *consumed* by the Order Service or represent commands/responses in a saga, rather than primary domain events *published* by the Order Service to a general audience. The list above focuses on events the Order Service itself owns and broadcasts about its state changes.*


## Event Format

All events published by the Order Service adhere to the `StandardMessage<T>` envelope defined in the `@ecommerce-platform/rabbitmq-event-utils` shared library. This ensures consistency across all services.

**Example: `OrderCreatedEvent`**

```json
{
  "messageId": "msg-f47ac10b-58cc-4372-a567-0e02b2c3d479", // Unique ID for this event message
  "messageType": "OrderCreatedEvent",                  // Type of the event
  "messageVersion": "1.0",                             // Version of the event schema
  "timestamp": "2023-11-21T12:34:56.789Z",             // Time the event occurred (ISO 8601)
  "source": "OrderService",                           // Service that published the event
  "correlationId": "corr-12345678-1234-1234-1234-123456789012", // Optional: For tracing related operations
  "partitionKey": "order-abc-123",                       // The orderId, used for routing/partitioning
  "payload": {                                         // Event-specific data (T)
    "orderId": "order-abc-123",
    "userId": "user-xyz-789",
    "orderDate": "2023-11-21T12:34:56.789Z",
    "status": "PENDING_PAYMENT", // Or a more specific initial status based on workflow
    "totalAmount": 149.99,
    "currency": "USD",
    "itemCount": 2,
    "customerDetails": {
      "name": "John Doe",
      "email": "john.doe@example.com"
    },
    "shippingAddress": {
      "street": "123 Main St",
      "city": "Anytown",
      "postalCode": "12345",
      "country": "US"
    },
    "items": [
      {
        "productId": "prod-456",
        "quantity": 1,
        "unitPrice": 99.99
      },
      {
        "productId": "prod-789",
        "quantity": 1,
        "unitPrice": 50.00
      }
    ]
    // ... other relevant order details ...
  }
}
```

## Detailed Event Specifications

Detailed schemas and descriptions for each event type published by the Order Service are provided in separate documents. These documents align with the `StandardMessage<T>` format and the event names listed previously.

- [01-order-created-event.md](./01-order-created-event.md): Details for `OrderCreatedEvent`.
- [02-order-shipped-event.md](./02-order-shipped-event.md): Details for `OrderShippedEvent`.
- [03-order-status-changed-event.md](./03-order-status-changed-event.md): Details for `OrderStatusChangedEvent` (and potentially other general status changes).
- [04-order-cancelled-event.md](./04-order-cancelled-event.md): Details for `OrderCancelledEvent`.
- [05-order-delivered-event.md](./05-order-delivered-event.md): Details for `OrderDeliveredEvent`.
- [06-order-payment-completed-event.md](./06-order-payment-completed-event.md): Details for `OrderPaymentCompletedEvent` (and potentially `OrderPaymentFailedEvent`).

*Note: Further consolidation or creation of new files for events like `OrderUpdatedEvent`, `OrderRefundRequestedEvent`, `OrderRefundProcessedEvent`, `OrderPaymentProcessingInitiatedEvent`, `OrderConfirmationNotificationRequestedEvent`, and `OrderPlacedForAnalyticsEvent` may be necessary based on the content of the existing files and desired granularity.*


## Event Schema Versioning

Event schemas are versioned using the `messageVersion` field within the `StandardMessage<T>` envelope. The following practices are encouraged:

1.  **Semantic Versioning (Optional but Recommended):** Use versions like `1.0`, `1.1`, `2.0`.
2.  **Additive Changes for Minor Versions:** New optional fields can be added in minor versions (e.g., `1.0` to `1.1`). Consumers should be tolerant of unknown fields.
3.  **Breaking Changes for Major Versions:** Modifications to existing fields (type change, removal) or addition of new mandatory fields require a major version increment (e.g., `1.1` to `2.0`).
4.  **Schema Registry (Future Consideration):** While not initially mandated for all events, a central schema registry (like Avro Schema Registry or AWS Glue Schema Registry with appropriate RabbitMQ integration) can be considered for more complex scenarios or as the system scales to enforce compatibility and provide discoverability.

## Consumer Considerations

Services consuming events from the Order Service via RabbitMQ should implement:

1.  **Idempotent Processing:** Design consumers to handle potential duplicate message deliveries gracefully (e.g., by tracking processed `messageId`s or using optimistic locking).
2.  **Retry Logic & DLQs:** Implement retry mechanisms (e.g., exponential backoff) for transient failures. Unrecoverable messages should be sent to a Dead-Letter Queue (DLQ) for investigation.
3.  **Schema Validation:** Validate incoming event payloads against the expected schema version, especially if strict validation is required.
4.  **Selective Consumption:** Consumers should bind their queues to the exchange with appropriate routing keys to only receive events they are interested in.

## Example Event Publishing Code (using `@ecommerce-platform/rabbitmq-event-utils`)

```typescript
// Order Service - Example of Publishing an OrderCreatedEvent

import { Injectable } from '@nestjs/common';
import { RabbitMQProducerService, StandardMessage } from '@ecommerce-platform/rabbitmq-event-utils';
// Assuming Order and OrderCreatedEventPayload types are defined elsewhere
import { Order, OrderCreatedEventPayload } from './order.types'; 

@Injectable()
export class OrderEventPublisher {
  constructor(private readonly rabbitMQProducerService: RabbitMQProducerService) {}

  async publishOrderCreated(order: Order): Promise<void> {
    const payload: OrderCreatedEventPayload = {
      orderId: order.id,
      userId: order.userId,
      orderDate: order.orderDate.toISOString(),
      status: order.status,
      totalAmount: order.totalAmount,
      currency: order.currency,
      itemCount: order.items.length,
      customerDetails: order.customerDetails, // Assuming these are part of the Order type
      shippingAddress: order.shippingAddress,
      items: order.items.map(item => ({
        productId: item.productId,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
      })),
      // ... any other relevant fields for the event payload
    };

    const eventMessage: StandardMessage<OrderCreatedEventPayload> = {
      messageId: `msg-${crypto.randomUUID()}`, // Generate a unique message ID
      messageType: 'OrderCreatedEvent',
      messageVersion: '1.0',
      timestamp: new Date().toISOString(),
      source: 'OrderService',
      // correlationId: obtained from incoming request or context if available
      partitionKey: order.id, // Use orderId for routing/partitioning if needed
      payload: payload,
    };

    try {
      // Assuming 'order.events' is the exchange and messageType is used as routing key
      await this.rabbitMQProducerService.publish(
        'order.events', // Target exchange
        eventMessage.messageType, // Routing key (can be more complex)
        eventMessage
      );
      console.log(`Published ${eventMessage.messageType} for order ${order.id}`);
    } catch (error) {
      console.error(
        `Failed to publish ${eventMessage.messageType} for order ${order.id}:`,
        error
      );
      // Implement more robust error handling/logging as needed
      throw error;
    }
  }

  // ... other event publishing methods for OrderUpdatedEvent, OrderCancelledEvent, etc.
}
```

## Event Monitoring

Monitoring for event publishing and consumption in a RabbitMQ environment (including Amazon MQ for RabbitMQ) typically involves:

1.  **RabbitMQ Management Plugin/API:** Monitoring exchanges, queues (depths, message rates), connections, and channels.
2.  **Amazon CloudWatch Metrics (for Amazon MQ):** Provides metrics for broker health, queue sizes, message rates, connections, etc.
3.  **Application-Level Logging:** Logging successful publications and consumptions, including `messageId` and `correlationId` for tracing.
4.  **Distributed Tracing:** Implementing distributed tracing (e.g., OpenTelemetry, AWS X-Ray) across services to follow the lifecycle of an operation that spans multiple event publications and consumptions.
5.  **Alerting:** Setting up alerts (e.g., via CloudWatch Alarms or other monitoring tools) for critical issues like high DLQ depth, sustained publishing failures, or unresponsive consumers.

## References

- [ADR-007-event-driven-architecture](../../../architecture/adr/ADR-007-event-driven-architecture.md)
- [ADR-018-message-broker-strategy.md](../../../architecture/adr/ADR-018-message-broker-strategy.md)
- [TDAC/03-message-broker-selection.md](../../../architecture/technology-decisions-aws-centeric/03-message-broker-selection.md)
- `@ecommerce-platform/rabbitmq-event-utils` (Shared Library Documentation - *link to be added*)
- [Order Service Data Model](../02-data-model-setup/00-data-model-index.md) (Adjust path if needed)
- [Order Service Components](../03-core-service-components/00-service-components-index.md) (Adjust path if needed)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [Amazon MQ for RabbitMQ Developer Guide](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/rabbitmq-broker-architecture.html)

