# `OrderShippedEvent` Specification

## 1. Overview

This document specifies the `OrderShippedEvent` published by the Order Service. This event is emitted when an order, or a part of an order, has been shipped and transitions to a corresponding status (e.g., `SHIPPED`, `PARTIALLY_SHIPPED`). It carries essential shipping details, including carrier and tracking information, enabling other services to update their records and notify customers.

This event conforms to the `StandardMessage<T>` envelope detailed in the [Order Service Events Index](./00-events-index.md).

## 2. Event Details

| Attribute             | Value                                                                                          |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| `messageType`         | `OrderShippedEvent`                                                                            |
| `source`              | `OrderService`                                                                                 |
| `messageVersion`      | `1.0` (Initial version)                                                                        |
| Potential Consumers   | Notification Service, Customer Service Systems, Analytics Service                                |
| Message Broker        | RabbitMQ (via Amazon MQ)                                                                       |
| Key `StandardMessage` Fields | `messageId`, `timestamp`, `correlationId` (optional), `partitionKey` (set to `orderId`)      |

## 3. Event Schema (`StandardMessage<OrderShippedEventPayload>`)

Events are structured using the `StandardMessage<T>` envelope. The `payload` for an `OrderShippedEvent` is defined as `OrderShippedEventPayload`.

### 3.1. `StandardMessage<T>` Envelope Example

```json
{
  "messageId": "msg-fedcba98-7654-3210-fedc-ba9876543210",
  "messageType": "OrderShippedEvent",
  "messageVersion": "1.0",
  "timestamp": "2023-11-23T14:35:12.487Z",
  "source": "OrderService",
  "correlationId": "corr-xyz-987", // Optional
  "partitionKey": "f47ac10b-58cc-4372-a567-0e02b2c3d479", // Value of orderId
  "payload": { // OrderShippedEventPayload starts here
    "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    // ... other fields from OrderShippedEventPayload as defined below ...
  }
}
```

### 3.2. `OrderShippedEventPayload` Schema

This defines the structure of the `payload` field within the `StandardMessage<T>` for an `OrderShippedEvent`.

```json
{
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "orderNumber": "ORD-12345678",
  "shipmentId": "ship-abc-78901", // Unique ID for this specific shipment, especially if order is split-shipped
  "shippedAt": "2023-11-23T14:35:12.487Z",
  "carrierName": "UPS", // Standardized carrier name
  "trackingNumber": "1Z999AA10123456784",
  "trackingUrl": "https://www.ups.com/track?tracknum=1Z999AA10123456784", // Optional, direct tracking link
  "estimatedDeliveryDate": "2023-11-26", // Date YYYY-MM-DD
  "shippingMethodUsed": "EXPRESS",
  "shipmentType": "PARTIAL", // e.g., "FULL", "PARTIAL"
  "itemsShipped": [
    {
      "itemId": "d290f1ee-6c54-4b01-90e6-d701748f0851", // Corresponds to original order item ID
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "productName": "Wireless Headphones",
      "quantityShipped": 1 // Quantity of this item in *this* shipment
    }
    // ... other items in this shipment
  ],
  "packageDetails": { // Optional, if multiple packages for this one shipmentId
      "packageCountInShipment": 1,
      "packageTrackingNumbers": ["1Z999AA10123456784"] // Can have multiple if carrier uses sub-package tracking
  },
  "destinationAddress": {
    "recipientName": "Jane Doe",
    "addressLine1": "456 Park Ave",
    "addressLine2": "Apt 7C",
    "city": "New York",
    "stateOrProvince": "NY",
    "postalCode": "10022",
    "country": "US",
    "phoneNumber": "+12125551234"
  },
  "returnAddress": { // Optional, if different from standard
    "addressLine1": "123 Return Warehouse Ln",
    "city": "Returnsville",
    "stateOrProvince": "CA",
    "postalCode": "90210",
    "country": "US"
  },
  "specialInstructions": "Leave with doorman if no answer.",
  "shippingLabelUrl": "https://shipping-api.example.com/labels/1Z999AA10123456784.pdf", // Optional
  "packageWeight": {"value": 1.2, "unit": "kg"}, // Optional
  "packageDimensions": {"length": 30, "width": 20, "height": 10, "unit": "cm"} // Optional
}
```

### 3.3. `OrderShippedEventPayload` Field Definitions

| Field                         | Type     | Required | Description                                                                   |
| ----------------------------- | -------- | -------- | ----------------------------------------------------------------------------- |
| `orderId`                     | UUID     | Yes      | Identifier of the order this shipment belongs to. Used as `partitionKey`.       |
| `userId`                      | UUID     | Yes      | Identifier of the customer.                                                   |
| `orderNumber`                 | String   | Yes      | Human-readable order number.                                                  |
| `shipmentId`                  | String   | Yes      | Unique identifier for this specific shipment.                                 |
| `shippedAt`                   | ISO Date | Yes      | Timestamp when the shipment was processed (UTC).                              |
| `carrierName`                 | String   | Yes      | Standardized name of the shipping carrier (e.g., "UPS", "FedEx", "DHL").      |
| `trackingNumber`              | String   | Yes      | Primary tracking number for the shipment.                                     |
| `trackingUrl`                 | String   | No       | Direct URL to the carrier’s tracking page for this shipment.                  |
| `estimatedDeliveryDate`       | Date     | No       | Estimated delivery date (YYYY-MM-DD).                                         |
| `shippingMethodUsed`          | String   | Yes      | The shipping method used for this shipment (e.g., "STANDARD", "EXPRESS").     |
| `shipmentType`                | String   | Yes      | Indicates if it's a "FULL" or "PARTIAL" shipment of the order.                |
| `itemsShipped`                | Array    | Yes      | Array of `ShippedItem` objects detailing items in this shipment.              |
| `itemsShipped[].itemId`       | String   | Yes      | Original order item ID.                                                       |
| `itemsShipped[].productId`    | UUID     | Yes      | Product identifier.                                                           |
| `itemsShipped[].variantId`    | UUID     | No       | Product variant identifier, if applicable.                                    |
| `itemsShipped[].productName`  | String   | Yes      | Name of the product.                                                          |
| `itemsShipped[].quantityShipped`| Integer  | Yes      | Quantity of this item included in this specific shipment.                     |
| `packageDetails`              | Object   | No       | Optional details about packages if a single shipmentId has multiple packages. |
| `destinationAddress`          | Object   | Yes      | Object containing the recipient's shipping address.                           |
| `destinationAddress.*`        | Various  | (Varies) | Standard address fields.                                                      |
| `returnAddress`               | Object   | No       | Optional return address details if specific to this shipment.                 |
| `specialInstructions`         | String   | No       | Any special delivery instructions for the carrier.                            |
| `shippingLabelUrl`            | String   | No       | URL to the generated shipping label, if available.                            |
| `packageWeight`               | Object   | No       | Object with `value` and `unit` (e.g., "kg", "lb").                          |
| `packageDimensions`           | Object   | No       | Object with `length`, `width`, `height`, and `unit` (e.g., "cm", "in").       |

## 4. Publishing Logic

The `OrderShippedEvent` is published by the Order Service (or a dedicated Fulfillment/Shipment sub-service if architecture dictates) when:

1.  A shipment is confirmed by the warehouse or a third-party logistics (3PL) provider.
2.  Carrier and tracking information are available.
3.  The order status is updated to reflect shipment (e.g., `SHIPPED`, `PARTIALLY_SHIPPED`).

### 4.1. Implementation Example (using `@ecommerce-platform/rabbitmq-event-utils`)

```typescript
// Assumes Order, Shipment, RabbitMQProducerService, etc. are defined/imported
// import { crypto } from 'crypto'; // For Node.js environment

@Injectable()
export class OrderShipmentService {
  constructor(
    private readonly rabbitMQProducerService: RabbitMQProducerService,
    private readonly logger: LoggerService // from @ecommerce-platform/nestjs-core-utils
  ) {}

  async processOrderShipment(order: Order, shipmentDetails: /* ShipmentDetailsDto */ any): Promise<void> {
    this.logger.log(`Processing shipment for order ${order.id}, shipment ID ${shipmentDetails.shipmentId}`, 'OrderShipmentService');
    
    // ... logic to update order status, associate shipment with order ...

    const eventPayload: OrderShippedEventPayload = {
      orderId: order.id,
      userId: order.userId,
      orderNumber: order.orderNumber,
      shipmentId: shipmentDetails.shipmentId,
      shippedAt: new Date().toISOString(), // Or from shipmentDetails if provided by external system
      carrierName: shipmentDetails.carrierName,
      trackingNumber: shipmentDetails.trackingNumber,
      trackingUrl: shipmentDetails.trackingUrl, // Or generate it
      estimatedDeliveryDate: shipmentDetails.estimatedDeliveryDate,
      shippingMethodUsed: shipmentDetails.shippingMethodUsed,
      shipmentType: shipmentDetails.shipmentType, // "FULL" or "PARTIAL"
      itemsShipped: shipmentDetails.items.map(item => ({
        itemId: item.originalOrderItemId,
        productId: item.productId,
        variantId: item.variantId,
        productName: item.productName,
        quantityShipped: item.quantity
      })),
      destinationAddress: shipmentDetails.destinationAddress, // Map address fields
      // ... map other optional fields like packageDetails, specialInstructions etc.
    };

    const eventMessage: StandardMessage<OrderShippedEventPayload> = {
      messageId: `msg-${crypto.randomUUID()}`,
      messageType: 'OrderShippedEvent',
      messageVersion: '1.0',
      timestamp: new Date().toISOString(),
      source: 'OrderService', // Or 'FulfillmentService' if distinct
      correlationId: shipmentDetails.correlationId, // If available
      partitionKey: order.id,
      payload: eventPayload,
    };

    try {
      await this.rabbitMQProducerService.publish(
        'order.events', // Target exchange
        eventMessage.messageType, // Routing key
        eventMessage
      );
      this.logger.log(`Published ${eventMessage.messageType} for order ${order.id}, shipment ${shipmentDetails.shipmentId}`, 'OrderShipmentService');
    } catch (error) {
      this.logger.error(
        `Failed to publish ${eventMessage.messageType} for order ${order.id}: ${error.message}`,
        error.stack,
        'OrderShipmentService'
      );
      // Implement robust error handling (retry, DLQ for publisher, outbox pattern)
      throw error;
    }
  }
}
```

## 5. Event Handling by Consumers

-   **Notification Service:** Send shipping confirmation email/SMS to the customer with tracking link and estimated delivery date. Trigger follow-up notifications (e.g., "out for delivery", "delivered").
-   **Customer Service Systems:** Update order history with shipment details, making it available to support agents.
-   **Analytics Service:** Track fulfillment times, carrier performance, delivery success rates.
-   **Order Service (itself, potentially):** If managing complex order states, it might consume its own shipped events to update overall order status if multiple shipments are involved.

(Refer to "General Consumer Responsibilities" in [00-events-index.md](./00-events-index.md) for common practices like idempotency, retries, DLQ handling.)

## 6. Versioning and Compatibility

Refer to the versioning strategy (`messageVersion`) outlined in [00-events-index.md](./00-events-index.md).

## 7. Testing Considerations

-   **Publisher:** Unit tests for payload construction, integration tests for `RabbitMQProducerService` interaction, contract tests.
-   **Consumer:** Unit tests for event processing logic, integration tests with mock RabbitMQ, contract tests.

## 8. Security Considerations

-   Secure RabbitMQ communication (TLS, authentication, authorization).
-   Minimize sensitive data in the payload if possible, though shipping addresses are inherently PII.

## 9. References

-   [Order Service Events Index](./00-events-index.md)
-   `@ecommerce-platform/rabbitmq-event-utils` (Shared Library Documentation)
-   Relevant ADRs (e.g., ADR-018 for Message Broker Strategy)
