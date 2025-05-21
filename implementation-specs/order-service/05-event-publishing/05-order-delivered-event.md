# `OrderDeliveredEvent` Specification

## 1. Overview

This document specifies the `OrderDeliveredEvent` published by the Order Service. This event is emitted when an order (or a shipment part of an order) is confirmed as delivered to the customer. It signifies a key milestone in the order lifecycle, triggering post-purchase activities like review requests, warranty activation, and final analytics updates.

This event conforms to the `StandardMessage<T>` envelope detailed in the [Order Service Events Index](./00-events-index.md).

## 2. Event Details

| Attribute             | Value                                                                                                   |
| --------------------- | ------------------------------------------------------------------------------------------------------- |
| `messageType`         | `OrderDeliveredEvent`                                                                                   |
| `source`              | `OrderService`                                                                                          |
| `messageVersion`      | `1.0` (Initial version)                                                                                 |
| Potential Consumers   | Notification Service, Product Service (for reviews), Customer Service Systems, Analytics Service, Returns Service. |
| Message Broker        | RabbitMQ (via Amazon MQ)                                                                                |
| Key `StandardMessage` Fields | `messageId`, `timestamp`, `correlationId` (optional), `partitionKey` (set to `orderId`)               |

## 3. Event Schema (`StandardMessage<OrderDeliveredEventPayload>`)

Events are structured using the `StandardMessage<T>` envelope. The `payload` for an `OrderDeliveredEvent` is `OrderDeliveredEventPayload`.

### 3.1. `StandardMessage<T>` Envelope Example

```json
{
  "messageId": "msg-delivery-event-11223",
  "messageType": "OrderDeliveredEvent",
  "messageVersion": "1.0",
  "timestamp": "2023-11-28T14:15:22.487Z",
  "source": "OrderService",
  "correlationId": "corr-delivery-op-44556", // Optional
  "partitionKey": "f47ac10b-58cc-4372-a567-0e02b2c3d479", // Value of orderId
  "payload": { // OrderDeliveredEventPayload starts here
    "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    // ... other fields from OrderDeliveredEventPayload ...
  }
}
```

### 3.2. `OrderDeliveredEventPayload` Schema

```json
{
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "orderNumber": "ORD-12345678",
  "shipmentId": "ship-abc-78901", // Optional: ID of the specific shipment if order was split-shipped
  "deliveredAt": "2023-11-28T14:15:22.487Z",
  "deliveryMethod": "COURIER", // e.g., "COURIER", "MAIL", "CUSTOMER_PICKUP", "LOCKER"
  "carrierName": "UPS", // If applicable
  "trackingNumber": "1Z999AA10123456784", // If applicable
  "recipientName": "Jane Doe", // Name of person who confirmed receipt or was designated recipient
  "deliveryAddressSnapshot": { // Optional: Snapshot of where it was delivered, if applicable
    "addressLine1": "456 Park Ave",
    "city": "New York",
    "postalCode": "10022",
    "country": "US"
  },
  "deliveryNotes": "Left with doorman as per instructions.",
  "proofOfDeliveryUrl": "https://carrier-proofs.com/pod/1Z999AA10123456784.jpg", // Optional URL to image/signature
  "deliveredItems": [
    {
      "itemId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "productName": "Wireless Headphones",
      "quantityDelivered": 2,
      "productReviewPromptEnabled": true
    }
    // ... other items in this delivery ...
  ],
  "returnEligibility": {
      "isEligible": true,
      "eligibleUntilDate": "2023-12-28",
      "returnPolicyUrl": "https://example.com/returns"
  },
  "feedbackSurveyUrl": "https://example.com/feedback/delivery/f47ac10b", // Optional
  "metadata": { // Optional
    "actualDeliveryvsEta": "EARLY", // e.g., "EARLY", "ON_TIME", "LATE"
    "packageConditionReported": "GOOD"
  }
}
```

### 3.3. `OrderDeliveredEventPayload` Field Definitions

| Field                         | Type     | Required | Description                                                                     |
| ----------------------------- | -------- | -------- | ------------------------------------------------------------------------------- |
| `orderId`                     | UUID     | Yes      | Identifier of the order. Used as `partitionKey`.                                |
| `userId`                      | UUID     | Yes      | Identifier of the customer.                                                     |
| `orderNumber`                 | String   | Yes      | Human-readable order number.                                                    |
| `shipmentId`                  | String   | No       | Identifier of the specific shipment if the order was fulfilled in parts.        |
| `deliveredAt`                 | ISO Date | Yes      | Timestamp when the delivery was confirmed (UTC).                                |
| `deliveryMethod`              | String   | Yes      | Method of delivery (e.g., "COURIER", "CUSTOMER_PICKUP").                        |
| `carrierName`                 | String   | No       | Name of the carrier, if applicable.                                             |
| `trackingNumber`              | String   | No       | Tracking number, if applicable.                                                 |
| `recipientName`               | String   | No       | Name of the person who received the delivery (if known and different from user).|
| `deliveryAddressSnapshot`     | Object   | No       | A snapshot of key address fields where delivery occurred.                       |
| `deliveryNotes`               | String   | No       | Any notes recorded at the time of delivery.                                     |
| `proofOfDeliveryUrl`          | String   | No       | URL to proof of delivery (e.g., signature image).                               |
| `deliveredItems`              | Array    | Yes      | Array of `DeliveredItem` objects detailing items in this delivery.              |
| `deliveredItems[].itemId`     | String   | Yes      | Original order item ID.                                                         |
| `deliveredItems[].productId`  | UUID     | Yes      | Product identifier.                                                             |
| `deliveredItems[].variantId`  | UUID     | No       | Product variant identifier.                                                     |
| `deliveredItems[].productName`| String   | Yes      | Name of the product.                                                            |
| `deliveredItems[].quantityDelivered`| Integer| Yes      | Quantity of this item in this specific delivery.                                |
| `deliveredItems[].productReviewPromptEnabled`| Boolean| No | Indicates if a review prompt is suggested for this item.                        |
| `returnEligibility`           | Object   | Yes      | Details about return eligibility.                                               |
| `returnEligibility.isEligible`| Boolean  | Yes      | Is the order/shipment eligible for return.                                      |
| `returnEligibility.eligibleUntilDate`| Date   | No   | Date (YYYY-MM-DD) until which returns are accepted.                             |
| `returnEligibility.returnPolicyUrl`| String | No   | Link to applicable return policy.                                               |
| `feedbackSurveyUrl`           | String   | No       | URL for the customer to provide feedback on the delivery experience.            |
| `metadata`                    | Object   | No       | Additional key-value pairs for context.                                         |

## 4. Publishing Logic

The `OrderDeliveredEvent` is published by the Order Service when:

1.  Delivery confirmation is received from an integrated logistics provider or carrier API.
2.  A customer confirms delivery through the platform's interface.
3.  An administrator manually updates the order status to "DELIVERED" with necessary confirmation details.

The event is published after the order status and any relevant delivery details are persisted in the Order Service database.

### 4.1. Implementation Example (using `@ecommerce-platform/rabbitmq-event-utils`)

```typescript
// Assumes necessary services, DTOs, and RabbitMQProducerService are available
// import { crypto } from 'crypto'; // For Node.js environment

@Injectable()
export class OrderDeliveryService {
  constructor(
    private readonly orderRepository: OrderRepository, // Your data access layer
    private readonly rabbitMQProducerService: RabbitMQProducerService,
    private readonly logger: LoggerService // from @ecommerce-platform/nestjs-core-utils
    // Potentially a ProductIntegrationService to get review prompt flags
  ) {}

  async confirmOrderDelivery(orderId: string, deliveryConfirmation: /* DeliveryConfirmationDto */ any): Promise<Order> {
    this.logger.log(`Processing delivery confirmation for order ${orderId}`, 'OrderDeliveryService');
    const order = await this.orderRepository.findById(orderId);
    if (!order) throw new NotFoundException(`Order ${orderId} not found.`);
    // ... logic to validate delivery confirmation and update order status to DELIVERED ...
    const updatedOrder = await this.orderRepository.updateStatus(orderId, 'DELIVERED', deliveryConfirmation.notes);

    const eventPayload: OrderDeliveredEventPayload = {
      orderId: updatedOrder.id,
      userId: updatedOrder.userId,
      orderNumber: updatedOrder.orderNumber,
      shipmentId: deliveryConfirmation.shipmentId, // If provided by confirmation source
      deliveredAt: deliveryConfirmation.deliveredAtTimestamp || new Date().toISOString(),
      deliveryMethod: deliveryConfirmation.method || updatedOrder.shippingMethod,
      carrierName: deliveryConfirmation.carrier || updatedOrder.carrier,
      trackingNumber: deliveryConfirmation.trackingNumber || updatedOrder.trackingNumber,
      recipientName: deliveryConfirmation.recipientName,
      deliveryAddressSnapshot: deliveryConfirmation.addressSnapshot, // Snapshot of address if different or confirmed
      deliveryNotes: deliveryConfirmation.notes,
      proofOfDeliveryUrl: deliveryConfirmation.podUrl,
      deliveredItems: updatedOrder.items.map(item => ({
        itemId: item.id,
        productId: item.productId,
        variantId: item.variantId,
        productName: item.productName,
        quantityDelivered: item.quantity, // Assuming full item delivery in this event
        productReviewPromptEnabled: true // Determine this based on product/customer settings
      })),
      returnEligibility: {
        isEligible: true, // Determine based on policy and item types
        eligibleUntilDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Example: 30 days
        returnPolicyUrl: 'https://example.com/policy/returns'
      },
      feedbackSurveyUrl: `https://example.com/feedback/order/${updatedOrder.id}`,
      metadata: deliveryConfirmation.metadata
    };

    const eventMessage: StandardMessage<OrderDeliveredEventPayload> = {
      messageId: `msg-${crypto.randomUUID()}`,
      messageType: 'OrderDeliveredEvent',
      messageVersion: '1.0',
      timestamp: new Date().toISOString(),
      source: 'OrderService',
      correlationId: deliveryConfirmation.correlationId,
      partitionKey: updatedOrder.id,
      payload: eventPayload,
    };

    try {
      await this.rabbitMQProducerService.publish(
        'order.events', // Exchange name
        eventMessage.messageType, // Routing key
        eventMessage
      );
      this.logger.log(`Published ${eventMessage.messageType} for order ${updatedOrder.id}`, 'OrderDeliveryService');
    } catch (error) {
      this.logger.error(
        `Failed to publish ${eventMessage.messageType} for order ${updatedOrder.id}: ${error.message}`,
        error.stack,
        'OrderDeliveryService'
      );
      // Implement robust error handling
      throw error;
    }
    return updatedOrder;
  }
}
```

## 5. Event Handling by Consumers

-   **Notification Service:** Send "Order Delivered" confirmation. Schedule follow-up emails/notifications for product reviews or satisfaction surveys.
-   **Product Service / Review Service:** Enable review submissions for delivered items. Associate delivery date with products for warranty calculations.
-   **Customer Service Systems:** Update order history; potentially trigger loyalty point updates.
-   **Analytics Service:** Finalize order lifecycle tracking, calculate actual delivery times, update fulfillment metrics.
-   **Returns Service:** Start the return eligibility window for the delivered items based on `returnEligibility.eligibleUntilDate`.

(Refer to "General Consumer Responsibilities" in [00-events-index.md](./00-events-index.md) for common practices.)

## 6. Versioning and Compatibility

Refer to the versioning strategy (`messageVersion`) outlined in [00-events-index.md](./00-events-index.md).

## 7. Testing Considerations

-   **Publisher:** Test various delivery scenarios (courier, pickup), including cases with and without proof of delivery. Verify correct calculation of `returnEligibility`. Test RabbitMQ publishing.
-   **Consumer:** Test specific actions triggered by delivery (e.g., Notification Service sending review requests, Returns Service activating return window). Test idempotency.

## 8. Security Considerations

-   Standard RabbitMQ security.
-   Careful handling of PII in `deliveryAddressSnapshot` and `recipientName`.
-   `proofOfDeliveryUrl` should point to a secure storage location if it contains sensitive imagery.

## 9. References

-   [Order Service Events Index](./00-events-index.md)
-   `@ecommerce-platform/rabbitmq-event-utils` (Shared Library Documentation)
-   Relevant ADRs (e.g., ADR-018 for Message Broker Strategy)
