# `OrderCreatedEvent` Specification

## 1. Overview

This document specifies the `OrderCreatedEvent` published by the Order Service. This event is emitted when a new order has been successfully created and persisted. It signals other interested services that a new order is available for subsequent processing (e.g., inventory allocation, notification, payment finalization).

This event conforms to the `StandardMessage<T>` envelope detailed in the [Order Service Events Index](./00-events-index.md).

## 2. Event Details

| Attribute             | Value                                                                                          |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| `messageType`         | `OrderCreatedEvent`                                                                            |
| `source`              | `OrderService`                                                                                 |
| `messageVersion`      | `1.0` (Initial version)                                                                        |
| Potential Consumers   | Inventory Service, Notification Service, Payment Service, Analytics Service, Search Service (for order history) |
| Message Broker        | RabbitMQ (via Amazon MQ)                                                                       |
| Key `StandardMessage` Fields | `messageId`, `timestamp`, `correlationId` (optional), `partitionKey` (set to `orderId`)      |

## 3. Event Schema (`StandardMessage<OrderCreatedEventPayload>`)

Events are structured using the `StandardMessage<T>` envelope. The `payload` for an `OrderCreatedEvent` is defined as `OrderCreatedEventPayload`.

### 3.1. `StandardMessage<T>` Envelope Example

```json
{
  "messageId": "msg-f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "messageType": "OrderCreatedEvent",
  "messageVersion": "1.0",
  "timestamp": "2023-11-21T12:34:56.789Z",
  "source": "OrderService",
  "correlationId": "corr-abc-123", // Optional: If the creation was part of a larger traceable operation
  "partitionKey": "f47ac10b-58cc-4372-a567-0e02b2c3d479", // Value of orderId
  "payload": { // OrderCreatedEventPayload starts here
    "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    // ... other fields from OrderCreatedEventPayload as defined below ...
  }
}
```

### 3.2. `OrderCreatedEventPayload` Schema

This defines the structure of the `payload` field within the `StandardMessage<T>` for an `OrderCreatedEvent`.

```json
{
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "orderDate": "2023-11-21T12:34:56.789Z",
  "status": "PENDING_PAYMENT", // Initial status of the order
  "statusHistory": [ // Optional: initial status entry
    {
      "status": "PENDING_PAYMENT",
      "timestamp": "2023-11-21T12:34:56.789Z",
      "notes": "Order created."
    }
  ],
  "totalAmount": 149.99,
  "subtotal": 139.99,
  "taxAmount": 10.0,
  "shippingCost": 15.99,
  "discountAmount": 15.99,
  "currency": "USD",
  "promoCodeApplied": "SUMMER10",
  "items": [
    {
      "itemId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7", // Optional
      "productName": "Wireless Headphones",
      "quantity": 2,
      "unitPrice": 59.99,
      "totalPrice": 119.98,
      "attributes": [{"name": "Color", "value": "Black"}] // Optional
    }
    // ... more items ...
  ],
  "shippingDetails": {
    "recipientName": "Jane Doe",
    "addressLine1": "456 Park Ave",
    "addressLine2": "Apt 7C",
    "city": "New York",
    "stateOrProvince": "NY",
    "postalCode": "10022",
    "country": "US",
    "phoneNumber": "+15551234567", // Optional
    "shippingMethodChosen": "EXPRESS",
    "estimatedDeliveryDate": "2023-11-24T12:00:00Z" // Optional
  },
  "billingDetails": {
    "paymentMethodHint": "CREDIT_CARD_ENDING_1234", // Avoid sending full payment details
    "billingAddressLine1": "456 Park Ave",
    "billingAddressLine2": "Apt 7C",
    "billingCity": "New York",
    "stateOrProvince": "NY",
    "postalCode": "10022",
    "country": "US"
  },
  "customerNotes": "Please deliver after 5 PM.", // Optional
  "inventoryReservationId": "res-d290f1ee-6c54-4b01", // Optional, if pre-reserved
  "appliedCoupons": ["SUMMER10"], // Optional
  "metadata": { // Optional: For non-domain specific context
    "channel": "WEB", // e.g., WEB, MOBILE_APP, POS
    "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "ipAddress": "192.168.1.1",
    "isGuestCheckout": false
  }
}
```

### 3.3. `OrderCreatedEventPayload` Field Definitions

| Field                    | Type     | Required | Description                                                                 |
| ------------------------ | -------- | -------- | --------------------------------------------------------------------------- |
| `orderId`                | UUID     | Yes      | Unique identifier of the created order. Used as `partitionKey`.             |
| `userId`                 | UUID     | Yes      | Identifier of the user who placed the order.                                |
| `orderDate`              | ISO Date | Yes      | Timestamp when the order was created (UTC).                                 |
| `status`                 | String   | Yes      | Current status of the order (e.g., `PENDING_PAYMENT`, `AWAITING_FULFILLMENT`). |
| `statusHistory`          | Array    | No       | Optional: Array of status transition objects.                               |
| `totalAmount`            | Decimal  | Yes      | Total order amount including tax and shipping.                              |
| `subtotal`               | Decimal  | Yes      | Order amount before tax, shipping, and discounts.                           |
| `taxAmount`              | Decimal  | Yes      | Tax amount for the order.                                                   |
| `shippingCost`           | Decimal  | Yes      | Shipping cost for the order.                                                |
| `discountAmount`         | Decimal  | No       | Total discount applied to the order.                                        |
| `currency`               | String   | Yes      | Three-letter currency code (ISO 4217), e.g., "USD".                         |
| `promoCodeApplied`       | String   | No       | Primary promotion code used for the order.                                  |
| `items`                  | Array    | Yes      | Array of `OrderItem` objects.                                               |
| `items[].itemId`         | UUID     | Yes      | Unique identifier of the order item.                                        |
| `items[].productId`      | UUID     | Yes      | Identifier of the product.                                                  |
| `items[].variantId`      | UUID     | No       | Identifier of the product variant, if applicable.                           |
| `items[].productName`    | String   | Yes      | Name of the product at the time of order.                                   |
| `items[].quantity`       | Integer  | Yes      | Quantity of the product ordered.                                            |
| `items[].unitPrice`      | Decimal  | Yes      | Price per unit of the product at the time of order.                         |
| `items[].totalPrice`     | Decimal  | Yes      | Total price for this item line (quantity * unitPrice - item discounts).     |
| `items[].attributes`     | Array    | No       | Optional: Array of product attributes selected (e.g., color, size).         |
| `shippingDetails`        | Object   | Yes      | Object containing shipping information.                                     |
| `shippingDetails.*`      | Various  | (Varies) | Standard shipping address fields, contact info, method.                       |
| `billingDetails`         | Object   | Yes      | Object containing billing information.                                      |
| `billingDetails.*`       | Various  | (Varies) | Standard billing address fields, payment method hint.                         |
| `customerNotes`          | String   | No       | Any notes provided by the customer with the order.                          |
| `inventoryReservationId` | String   | No       | Identifier if inventory was pre-reserved via a reservation system.          |
| `appliedCoupons`         | Array    | No       | List of all coupon/promo codes applied.                                     |
| `metadata`               | Object   | No       | Additional non-domain specific context (e.g., channel, user agent).         |

## 4. Publishing Logic

The `OrderCreatedEvent` is published by the Order Service after:

1.  The order request is validated successfully.
2.  Initial payment authorization or verification is successful (if applicable at this stage).
3.  Any initial inventory reservation attempts are made (results might be part of the payload or handled by subsequent events/sagas).
4.  The order entity is successfully persisted to the Order Service's database.

### 4.1. Implementation Example (using `@ecommerce-platform/rabbitmq-event-utils`)

```typescript
// Assumes OrderService, RabbitMQProducerService, Order, OrderCreatedEventPayload types are defined/imported
// import { crypto } from 'crypto'; // For Node.js environment if not globally available

@Injectable()
export class OrderCreationService { // Example service responsible for order creation flow
  constructor(
    private readonly orderRepository: OrderRepository, // Your order data access layer
    private readonly rabbitMQProducerService: RabbitMQProducerService,
    private readonly logger: LoggerService // from @ecommerce-platform/nestjs-core-utils
  ) {}

  async createOrder(createOrderDto: /* your DTO */ any): Promise<Order> {
    this.logger.log('Starting order creation process...', 'OrderCreationService');
    // ... complex business logic for order creation ...
    // ... validation, payment pre-auth, initial inventory checks ...
    const orderEntity = new Order(/* ... from DTO and logic ... */);
    
    // Persist the order
    const savedOrder = await this.orderRepository.save(orderEntity);
    this.logger.log(`Order ${savedOrder.id} persisted.`, 'OrderCreationService');

    // Prepare and publish the OrderCreatedEvent
    const eventPayload: OrderCreatedEventPayload = {
      orderId: savedOrder.id,
      userId: savedOrder.userId,
      orderDate: savedOrder.orderDate.toISOString(),
      status: savedOrder.status,
      // ... map all other relevant fields from savedOrder to eventPayload ...
      totalAmount: savedOrder.totalAmount,
      currency: savedOrder.currency,
      items: savedOrder.items.map(item => ({ /* ... map item fields ... */ })),
      shippingDetails: { /* ... map shipping fields ... */ },
      billingDetails: { /* ... map billing fields ... */ },
      metadata: { channel: 'WEB' /* ... other metadata ... */ }
    };

    const eventMessage: StandardMessage<OrderCreatedEventPayload> = {
      messageId: `msg-${crypto.randomUUID()}`,
      messageType: 'OrderCreatedEvent',
      messageVersion: '1.0',
      timestamp: new Date().toISOString(),
      source: 'OrderService',
      correlationId: createOrderDto.correlationId, // Pass from incoming request if available
      partitionKey: savedOrder.id,
      payload: eventPayload,
    };

    try {
      await this.rabbitMQProducerService.publish(
        'order.events', // Exchange name (defined in RabbitMQ config)
        eventMessage.messageType, // Routing key (often the messageType itself)
        eventMessage
      );
      this.logger.log(`Published ${eventMessage.messageType} for order ${savedOrder.id}`, 'OrderCreationService');
    } catch (error) {
      this.logger.error(
        `Failed to publish ${eventMessage.messageType} for order ${savedOrder.id}: ${error.message}`,
        error.stack,
        'OrderCreationService'
      );
      // Implement more robust error handling: retry, dead-lettering for publisher, or compensating transaction
      throw error; // Re-throw or handle as per application's error strategy
    }
    return savedOrder;
  }
}
```

## 5. Event Handling by Consumers

### 5.1. General Consumer Responsibilities

Services consuming this event (and others from Order Service) via RabbitMQ should:

1.  **Acknowledge Messages:** Properly acknowledge messages upon successful processing to remove them from the queue.
2.  **Idempotency:** Ensure processing is idempotent (e.g., using the `messageId` or `payload.orderId` to detect and ignore duplicates).
3.  **Retry Mechanisms:** Implement retry logic (e.g., with exponential backoff and jitter) for transient failures before rejecting or dead-lettering a message.
4.  **Dead-Letter Queues (DLQs):** Configure and monitor DLQs for messages that consistently fail processing.
5.  **Schema Validation:** Validate the `payload` against the expected schema and `messageVersion`.

### 5.2. Potential Consumer Actions

-   **Inventory Service:** Finalize inventory reservation for order items, update stock levels.
-   **Notification Service:** Send order confirmation email/SMS to the customer, internal notifications.
-   **Payment Service:** (If payment is not fully completed at creation) Initiate payment capture, or link existing pre-authorization to the order.
-   **Analytics Service:** Record order details for sales reporting, customer behavior analysis.
-   **Fulfillment Service:** Create a new fulfillment request if the order is ready for fulfillment.

## 6. Error Handling

### 6.1. Publisher (Order Service) Error Handling

If the Order Service fails to publish the event to RabbitMQ:

1.  **Logging:** Detailed error logging, including message details and exception.
2.  **Retry:** Implement retries with backoff for transient broker unavailability (often handled by the `rabbitmq-event-utils` library if configured).
3.  **Circuit Breaker:** Consider a circuit breaker pattern if broker failures are persistent.
4.  **Outbox Pattern (Advanced):** For critical events, implement the transactional outbox pattern to ensure events are published reliably even if the service crashes after persisting the order but before publishing. This involves saving the event to a local DB table as part of the main transaction, and a separate process reads from this table and publishes to RabbitMQ.
5.  **Alerting:** Alerts for consistent publishing failures.

### 6.2. Consumer Error Handling

Refer to "General Consumer Responsibilities" above. DLQ analysis is crucial for understanding and fixing persistent processing issues.

## 7. Versioning and Compatibility (`messageVersion`)

-   The `messageVersion` field in `StandardMessage<T>` (e.g., "1.0", "1.1", "2.0") indicates the version of the `payload` schema.
-   **Minor versions (e.g., 1.0 -> 1.1):** Backward-compatible changes (e.g., adding new optional fields to the payload). Consumers should be tolerant of unknown fields.
-   **Major versions (e.g., 1.1 -> 2.0):** Breaking changes (e.g., removing fields, changing field types, adding mandatory fields). Consumers may need to update their logic to handle new major versions, potentially by subscribing to version-specific queues or routing keys if necessary.

## 8. Testing Considerations

-   **Publisher (Order Service):**
    -   Unit tests for `OrderCreatedEventPayload` construction.
    -   Integration tests verifying that the `RabbitMQProducerService` is called correctly with the right parameters (exchange, routing key, message).
    -   Contract testing for the event schema (e.g., using Pact).
-   **Consumer Services:**
    -   Unit tests for event deserialization and business logic for `OrderCreatedEvent`.
    -   Integration tests with a mock RabbitMQ (or a real instance) to verify message consumption, idempotency, and error handling (e.g., dead-lettering).
    -   Contract testing against the event schema.

## 9. Security Considerations

-   **Data Sensitivity:** The `OrderCreatedEventPayload` contains PII and order details. Access to queues must be restricted.
-   **Transport Security:** RabbitMQ communication should be secured using TLS/SSL.
-   **Authentication & Authorization:** Use RabbitMQ user authentication and configure permissions (vhost access, read/write permissions on exchanges/queues) appropriately for the Order Service (publisher) and consumer services.
-   **Payload Encryption (Optional):** For extremely sensitive fields within the payload, consider application-level encryption if broker-level and transport-level security are deemed insufficient for specific compliance requirements.

## 10. References

-   [Order Service Events Index](./00-events-index.md)
-   `@ecommerce-platform/rabbitmq-event-utils` (Shared Library Documentation - *link to be added*)
-   `@ecommerce-platform/nestjs-core-utils` (For LoggerService - *link to be added*)
-   [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
-   [Amazon MQ for RabbitMQ Developer Guide](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/rabbitmq-broker-architecture.html)
-   [ADR-018-message-broker-strategy.md](../../../architecture/adr/ADR-018-message-broker-strategy.md)

