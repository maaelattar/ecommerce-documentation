# `OrderCancelledEvent` Specification

## 1. Overview

This document specifies the `OrderCancelledEvent` published by the Order Service. This event is emitted when an order is successfully cancelled, either by a customer, an administrator, or an automated system process (e.g., due to payment failure or stock issues). It is crucial for coordinating actions such as refund processing, inventory release, and customer notifications.

This event conforms to the `StandardMessage<T>` envelope detailed in the [Order Service Events Index](./00-events-index.md).

## 2. Event Details

| Attribute             | Value                                                                                                |
| --------------------- | ---------------------------------------------------------------------------------------------------- |
| `messageType`         | `OrderCancelledEvent`                                                                                |
| `source`              | `OrderService`                                                                                       |
| `messageVersion`      | `1.0` (Initial version)                                                                              |
| Potential Consumers   | Payment Service, Inventory Service, Notification Service, Analytics Service, Customer Support Systems. |
| Message Broker        | RabbitMQ (via Amazon MQ)                                                                             |
| Key `StandardMessage` Fields | `messageId`, `timestamp`, `correlationId` (optional), `partitionKey` (set to `orderId`)            |

## 3. Event Schema (`StandardMessage<OrderCancelledEventPayload>`)

Events are structured using the `StandardMessage<T>` envelope. The `payload` for an `OrderCancelledEvent` is `OrderCancelledEventPayload`.

### 3.1. `StandardMessage<T>` Envelope Example

```json
{
  "messageId": "msg-cancel-event-67890",
  "messageType": "OrderCancelledEvent",
  "messageVersion": "1.0",
  "timestamp": "2023-11-25T09:15:27.123Z",
  "source": "OrderService",
  "correlationId": "corr-cancel-op-12345", // Optional
  "partitionKey": "f47ac10b-58cc-4372-a567-0e02b2c3d479", // Value of orderId
  "payload": { // OrderCancelledEventPayload starts here
    "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    // ... other fields from OrderCancelledEventPayload ...
  }
}
```

### 3.2. `OrderCancelledEventPayload` Schema

```json
{
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "orderNumber": "ORD-12345678",
  "cancelledAt": "2023-11-25T09:15:27.123Z", // Timestamp of cancellation
  "cancellationReasonCode": "CUSTOMER_REQUEST", // Standardized reason code
  "cancellationNotes": "Customer found a better deal elsewhere.", // Optional free-text notes
  "cancelledBy": {
    "actorType": "CUSTOMER", // "CUSTOMER", "ADMIN", "SYSTEM"
    "actorId": "3fa85f64-5717-4562-b3fc-2c963f66afa6" // userId, adminId, or system process name
  },
  "previousStatus": "PROCESSING", // The status of the order before it was cancelled
  "originalOrderTotal": 149.99,
  "currency": "USD",
  "itemsCancelled": [
    {
      "itemId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "variantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "productName": "Wireless Headphones",
      "quantityCancelled": 2,
      "unitPriceAtOrder": 59.99
    }
    // ... other items ...
  ],
  "refundDetails": {
    "isRefundApplicable": true,
    "refundStatus": "PENDING", // "PENDING", "PROCESSING", "COMPLETED", "FAILED"
    "refundAmount": 149.99,
    "refundCurrency": "USD",
    "refundMethodHint": "CREDIT_CARD_ENDING_4242", // Hint of original payment method
    "paymentTransactionId": "pi_3OBtP1CZ6qsJgndP0NZUQ1ZW" // Original payment transaction ID, if available
  },
  "inventoryRestockRequested": true, // Indicates if items should be restocked
  "metadata": { // Optional
    "originalOrderDate": "2023-11-24T10:30:15.456Z"
  }
}
```

### 3.3. `OrderCancelledEventPayload` Field Definitions

| Field                         | Type     | Required | Description                                                                      |
| ----------------------------- | -------- | -------- | -------------------------------------------------------------------------------- |
| `orderId`                     | UUID     | Yes      | Unique identifier of the cancelled order. Used as `partitionKey`.                |
| `userId`                      | UUID     | Yes      | Identifier of the customer.                                                      |
| `orderNumber`                 | String   | Yes      | Human-readable order number.                                                     |
| `cancelledAt`                 | ISO Date | Yes      | Timestamp when the cancellation was recorded (UTC).                                |
| `cancellationReasonCode`      | String   | Yes      | Standardized code for the reason (e.g., "CUSTOMER_REQUEST", "FRAUD_SUSPECTED"). |
| `cancellationNotes`           | String   | No       | Optional free-text notes providing more context.                                 |
| `cancelledBy`                 | Object   | Yes      | Details of the actor who initiated the cancellation.                             |
| `cancelledBy.actorType`       | String   | Yes      | Type of actor: "CUSTOMER", "ADMIN", "SYSTEM".                                  |
| `cancelledBy.actorId`         | String   | No       | Identifier for the actor (e.g., User ID, Admin ID, System Process Name).         |
| `previousStatus`              | String   | Yes      | The order status immediately before cancellation.                                  |
| `originalOrderTotal`          | Decimal  | Yes      | The total amount of the order when it was placed.                                |
| `currency`                    | String   | Yes      | Currency code (ISO 4217) for the order total.                                    |
| `itemsCancelled`              | Array    | Yes      | Array of `CancelledItem` objects detailing items affected.                       |
| `itemsCancelled[].itemId`     | String   | Yes      | Original order item ID.                                                          |
| `itemsCancelled[].productId`  | UUID     | Yes      | Product identifier.                                                              |
| `itemsCancelled[].variantId`  | UUID     | No       | Product variant identifier, if applicable.                                       |
| `itemsCancelled[].productName`| String   | Yes      | Name of the product.                                                             |
| `itemsCancelled[].quantityCancelled` | Integer | Yes    | Quantity of this item that was cancelled.                                        |
| `itemsCancelled[].unitPriceAtOrder` | Decimal | Yes    | Unit price of the item at the time of order.                                     |
| `refundDetails`               | Object   | Yes      | Object containing information about any applicable refund.                         |
| `refundDetails.isRefundApplicable` | Boolean | Yes    | True if a refund is expected for this cancellation.                                |
| `refundDetails.refundStatus`  | String   | Yes      | Current status of the refund (e.g., "PENDING", "COMPLETED").                   |
| `refundDetails.refundAmount`  | Decimal  | No       | The amount to be refunded (if `isRefundApplicable` is true).                     |
| `refundDetails.refundCurrency`| String   | No       | Currency for the refund amount.                                                  |
| `refundDetails.refundMethodHint` | String | No       | Hint of the original payment method used.                                        |
| `refundDetails.paymentTransactionId` | String | No     | Original payment transaction ID, useful for linking refunds.                     |
| `inventoryRestockRequested`   | Boolean  | Yes      | Flag indicating if the cancelled items should be considered for restocking.      |
| `metadata`                    | Object   | No       | Optional additional key-value pairs for context.                                 |

## 4. Publishing Logic

The `OrderCancelledEvent` is published by the Order Service when an order is moved to a terminal "CANCELLED" status due to:

1.  Customer request (e.g., via UI or API).
2.  Administrator action.
3.  Automated system processes (e.g., payment timeout, fraud detection, inability to fulfill).

The event is published *after* the order status is updated in the Order Service's database and any immediate internal processes (like attempting to halt fulfillment) are initiated.

### 4.1. Implementation Example (using `@ecommerce-platform/rabbitmq-event-utils`)

```typescript
// Assumes necessary services and DTOs are defined/imported
// import { crypto } from 'crypto'; // For Node.js environment

@Injectable()
export class OrderCancellationService {
  constructor(
    private readonly orderRepository: OrderRepository, // Your data access layer
    private readonly rabbitMQProducerService: RabbitMQProducerService,
    private readonly logger: LoggerService // from @ecommerce-platform/nestjs-core-utils
    // Potentially a PaymentIntegrationService to get payment details for refunds
  ) {}

  async cancelOrder(
    orderId: string, 
    cancellationRequest: /* CancellationRequestDto */ any
  ): Promise<Order> {
    this.logger.log(`Processing cancellation for order ${orderId}`, 'OrderCancellationService');
    const order = await this.orderRepository.findById(orderId); // Fetch order details
    if (!order) throw new NotFoundException(`Order ${orderId} not found.`);
    if (order.status === 'CANCELLED') throw new BadRequestException(`Order ${orderId} is already cancelled.`);

    const previousStatus = order.status;
    // ... logic to validate if cancellation is allowed ...
    // ... logic to determine refund applicability and amount ...
    // ... logic to update order status to CANCELLED in DB ...
    const updatedOrder = await this.orderRepository.updateStatus(orderId, 'CANCELLED', cancellationRequest.reason);

    const eventPayload: OrderCancelledEventPayload = {
      orderId: updatedOrder.id,
      userId: updatedOrder.userId,
      orderNumber: updatedOrder.orderNumber,
      cancelledAt: new Date().toISOString(),
      cancellationReasonCode: cancellationRequest.reasonCode,
      cancellationNotes: cancellationRequest.notes,
      cancelledBy: {
        actorType: cancellationRequest.actorType, // e.g., "CUSTOMER"
        actorId: cancellationRequest.actorId // e.g., customer's userId
      },
      previousStatus: previousStatus,
      originalOrderTotal: updatedOrder.totalAmount, // Or original if different
      currency: updatedOrder.currency,
      itemsCancelled: updatedOrder.items.map(item => ({
        itemId: item.id,
        productId: item.productId,
        variantId: item.variantId,
        productName: item.productName,
        quantityCancelled: item.quantity, // Assuming full item cancellation here
        unitPriceAtOrder: item.unitPrice
      })),
      refundDetails: {
        isRefundApplicable: /* ... based on logic ... */ true,
        refundStatus: 'PENDING',
        refundAmount: /* ... calculated refund amount ... */ updatedOrder.totalAmount,
        refundCurrency: updatedOrder.currency,
        refundMethodHint: /* ... from payment details ... */ 'CREDIT_CARD_ENDING_4242',
        paymentTransactionId: /* ... original payment txn id ... */ 'pi_123'
      },
      inventoryRestockRequested: cancellationRequest.reasonCode !== 'ITEM_DAMAGED', // Example logic
      metadata: { originalOrderDate: updatedOrder.createdAt.toISOString() }
    };

    const eventMessage: StandardMessage<OrderCancelledEventPayload> = {
      messageId: `msg-${crypto.randomUUID()}`,
      messageType: 'OrderCancelledEvent',
      messageVersion: '1.0',
      timestamp: new Date().toISOString(),
      source: 'OrderService',
      correlationId: cancellationRequest.correlationId,
      partitionKey: updatedOrder.id,
      payload: eventPayload,
    };

    try {
      await this.rabbitMQProducerService.publish(
        'order.events', // Exchange name
        eventMessage.messageType, // Routing key
        eventMessage
      );
      this.logger.log(`Published ${eventMessage.messageType} for order ${updatedOrder.id}`, 'OrderCancellationService');
    } catch (error) {
      this.logger.error(
        `Failed to publish ${eventMessage.messageType} for order ${updatedOrder.id}: ${error.message}`,
        error.stack,
        'OrderCancellationService'
      );
      // Implement robust error handling
      throw error;
    }
    return updatedOrder;
  }
}
```

## 5. Event Handling by Consumers

-   **Payment Service:** If `refundDetails.isRefundApplicable` is true and `refundDetails.refundStatus` is "PENDING", initiate refund processing. Update internal records upon refund completion or failure.
-   **Inventory Service:** If `inventoryRestockRequested` is true, release previously allocated stock for the `itemsCancelled` back into available inventory.
-   **Notification Service:** Send an order cancellation confirmation to the customer, including details about any refund being processed.
-   **Analytics Service:** Record the cancellation event, update metrics on cancellation rates, reasons, and impact on revenue.

(Refer to "General Consumer Responsibilities" in [00-events-index.md](./00-events-index.md) for common practices.)

## 6. Versioning and Compatibility

Refer to the versioning strategy (`messageVersion`) outlined in [00-events-index.md](./00-events-index.md).

## 7. Testing Considerations

-   **Publisher:** Test various cancellation scenarios (customer, admin, system), different `cancellationReasonCode`s, and ensure `refundDetails` and `inventoryRestockRequested` are set correctly. Verify RabbitMQ publishing.
-   **Consumer:** Test specific actions based on `OrderCancelledEvent` (e.g., Payment Service processing refund, Inventory Service restocking). Test idempotency.

## 8. Security Considerations

-   Standard RabbitMQ security. Access to cancellation functions in Order Service should be strictly controlled.
-   Refund processing triggered by this event must be secure and auditable within the Payment Service.

## 9. References

-   [Order Service Events Index](./00-events-index.md)
-   `@ecommerce-platform/rabbitmq-event-utils` (Shared Library Documentation)
-   Relevant ADRs (e.g., ADR-018 for Message Broker Strategy)
