# Notification Service - Event Consumption

## 1. Overview

The primary way the Notification Service is triggered to perform its duties is by consuming domain events published by other microservices on the e-commerce platform. This event-driven approach ensures loose coupling and allows the Notification Service to react to various business occurrences without requiring direct, synchronous calls from other services.

## 2. Event Consumption Mechanism

*   **Message Broker**: The Notification Service listens for events on **RabbitMQ** (via Amazon MQ).
*   **Shared Library**: It utilizes the `@ecommerce-platform/rabbitmq-event-utils` shared library for:
    *   Connecting to RabbitMQ.
    *   Defining consumer groups and queue bindings.
    *   Deserializing messages from the `StandardMessage<T>` envelope.
    *   Implementing message handlers (e.g., using decorators like `@RabbitListener` if provided by a NestJS-specific RabbitMQ utility built on top of the base library, or by direct use of the consumer classes).
*   **Queues**: Dedicated queues will be bound to relevant exchanges and routing keys that the Notification Service is interested in. For example:
    *   A queue `notification.order.events` bound to the `order.events` exchange with routing keys like `order.OrderCreated.#`, `order.OrderShipped.#`, `order.PaymentFailed.#`.
    *   A queue `notification.user.events` bound to the `user.events` exchange with routing keys like `user.UserRegistered.#`, `user.PasswordResetRequested.#`.
*   **Idempotency**: Event handlers within the Notification Service must be idempotent, typically by checking the `messageId` of the incoming `StandardMessage<T>` against a store of processed message IDs to prevent duplicate notification dispatches if an event is delivered more than once.
*   **Error Handling**: Robust error handling for consumed messages, including:
    *   Logging errors.
    *   Implementing retry logic for transient processing errors within the Notification Service.
    *   Utilizing Dead Letter Queues (DLQs) for messages that consistently fail processing.

## 3. Consumed Events and Triggered Notifications (Examples)

This section lists examples of events the Notification Service might consume and the types of notifications they would typically trigger. The exact list will evolve with the platform's features.

| Consumed Event (`messageType`) | Source Service   | Typical Notification Triggered                                  | Channels (Examples)         |
| ------------------------------ | ---------------- | --------------------------------------------------------------- | --------------------------- |
| `OrderCreated`                 | Order Service    | Order Confirmation                                              | Email, SMS (Optional)       |
| `OrderShipped`                 | Order Service    | Shipment Notification                                           | Email, SMS                  |
| `OrderDelivered`               | Order Service    | Delivery Confirmation                                           | Email, Push (Optional)      |
| `OrderCancelled`               | Order Service    | Order Cancellation Confirmation                                 | Email                       |
| `PaymentProcessed`             | Payment Service  | Payment Successful (often part of Order Confirmation)           | Email                       |
| `PaymentFailed`                | Payment Service  | Payment Failed Notification                                     | Email, SMS (Urgent)         |
| `RefundProcessed`              | Payment Service  | Refund Confirmation                                             | Email                       |
| `UserRegistered`               | User Service     | Welcome Email / Account Verification                            | Email                       |
| `PasswordResetRequested`       | User Service     | Password Reset Instructions / OTP                               | Email, SMS                  |
| `PasswordChanged`              | User Service     | Password Change Confirmation                                    | Email                       |
| `EmailVerificationRequired`  | User Service     | Email Verification Link                                         | Email                       |
| `TwoFactorAuthEnabled`         | User Service     | 2FA Setup Confirmation                                          | Email                       |
| `TwoFactorAuthCode`            | User Service     | 2FA Login Code (if not handled directly by User Service auth flow) | SMS, Authenticator App (Push) |
| `ProductBackInStock`         | Inventory Service| Back in Stock Alert (for subscribed users)                    | Email, Push                 |
| `LowStockWarning`              | Inventory Service| (Internal) Low Stock Alert for Admins/Merchants                 | Email, Webhook (Admin Tool) |
| `SupportTicketCreated`         | (Support Service)| Support Ticket Acknowledgement                                  | Email                       |
| `SupportTicketReply`           | (Support Service)| New Reply on Support Ticket                                     | Email                       |

## 4. Event Handler Implementation Strategy

For each consumed event type, a dedicated handler method will be implemented within a NestJS module (e.g., `NotificationTriggerModule` or more specific modules like `OrderEventHandlersModule`).

**Example Handler (Conceptual):**

```typescript
// In a module like OrderEventNotificationHandler.ts
import { Injectable, Logger } from '@nestjs/common';
import { StandardMessage } from '@ecommerce-platform/rabbitmq-event-utils';
// Assuming a decorator for RabbitMQ listeners is available or using the consumer service directly
// import { RabbitListener, Nack } from '@ecommerce-platform/nestjs-rabbitmq-utils'; // Hypothetical
import { NotificationProcessingService } from '../orchestration/notification-processing.service';
// import { OrderCreatedPayload } from '../../../../order-service/05-event-publishing/01-event-schema-definitions.md'; // Path to actual payload type

interface OrderCreatedPayload { // Simplified example payload
  orderId: string;
  userId: string;
  customerEmail: string;
  customerName: string;
  totalAmount: number;
  items: any[];
}

@Injectable()
export class OrderEventHandlers {
  private readonly logger = new Logger(OrderEventHandlers.name);

  constructor(
    private readonly notificationProcessor: NotificationProcessingService,
    // private readonly idempotencyService: IdempotencyService // For tracking processed message IDs
  ) {}

  // @RabbitListener('notification.order.events', { bindingKey: 'order.OrderCreated.#' })
  async handleOrderCreated(message: StandardMessage<OrderCreatedPayload>): Promise<void | /*Nack*/> {
    const { messageId, payload, timestamp, correlationId } = message;
    this.logger.log(`Received OrderCreatedEvent: ${messageId} for order ${payload.orderId}`);

    // 1. Idempotency Check
    // if (await this.idempotencyService.isProcessed(messageId)) {
    //   this.logger.warn(`Message ${messageId} already processed. Acknowledging.`);
    //   return; // ACK
    // }

    try {
      // 2. Map to internal notification request
      const notificationRequest = {
        type: 'ORDER_CONFIRMATION',
        recipient: {
          userId: payload.userId,
          email: payload.customerEmail,
          name: payload.customerName,
        },
        data: { ...payload }, // Pass relevant order data for templating
        triggeringEventId: messageId,
        correlationId: correlationId,
      };

      // 3. Delegate to NotificationProcessingService
      await this.notificationProcessor.processNotificationRequest(notificationRequest);
      
      // 4. Mark as processed for idempotency
      // await this.idempotencyService.markProcessed(messageId);
      
      // ACK (implicitly if no error/Nack thrown)
    } catch (error) {
      this.logger.error(`Error processing OrderCreatedEvent ${messageId}: ${error.message}`, error.stack);
      // Decide whether to Nack with requeue: true (transient) or false (DLQ)
      // return new Nack(error.isTransient); 
      throw error; // Let the framework handle Nack/requeue based on error type or default consumer config
    }
  }
}
```

## 5. Data Requirements from Events

For the Notification Service to effectively personalize and send notifications, consumed events must carry sufficient data in their payloads. This includes:

*   Relevant entity IDs (e.g., `orderId`, `userId`, `productId`).
*   Recipient contact information if readily available (e.g., `customerEmail` in `OrderCreatedEvent`). If not, the Notification Service might need to fetch it from the User Service (though this adds coupling and latency).
*   Key data points for message personalization (e.g., `orderNumber`, `productName`, `resetLink`).
*   Contextual information (e.g., `reasonForCancellation`).

If critical data is missing, the Notification Service's ability to function is impaired. Schema definitions for events published by other services should consider the Notification Service as a key consumer.

## 6. Filtering and Preference Checks

Before actually dispatching a notification triggered by an event:

1.  **User Preferences**: The `NotificationProcessingService` will check the recipient's communication preferences for the specific notification type and channel.
2.  **Global Unsubscribes/Blocks**: Check against any global unsubscribe lists or blocked recipients.
3.  **Consent**: Ensure necessary consent has been obtained, especially for marketing communications.

If preferences or lack of consent prevent dispatch, the notification process for that channel will be halted, and this should be logged.
