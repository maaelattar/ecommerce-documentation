# 03: RabbitMQ Consumer Utilities

## 1. Purpose

This document outlines utilities and patterns for consuming messages from RabbitMQ (Amazon MQ for RabbitMQ) in a standardized way within NestJS microservices. While NestJS offers a RabbitMQ transport via `@nestjs/microservices`, this section of the `rabbitmq-event-utils` library aims to provide additional conventions, helpers, or enhancements for common consumer tasks.

Key objectives:
*   Promote consistent deserialization and handling of the `StandardMessage` envelope.
*   Simplify error handling, including Dead Letter Exchange (DLX) patterns and retry mechanisms.
*   Facilitate context propagation (e.g., `correlationId`) for logging and tracing.
*   Provide clear guidance on using NestJS's RabbitMQ transport with these utilities.

## 2. Leveraging `@nestjs/microservices` with RabbitMQ Transport

NestJS's built-in RabbitMQ transport (`@nestjs/microservices` with `Transport.RMQ`) is the primary recommended way to consume messages. It handles:
*   Connection and channel management.
*   Message acknowledgement (`ack`, `nack`, `reject`).
*   Mapping message patterns (routing keys) to handler methods using `@MessagePattern()` or `@EventPattern()` decorators.

Our utilities will aim to complement this, not replace it entirely.

## 3. Proposed Utilities and Patterns

### 3.1. Standard Message Deserialization and Typing

*   **Problem:** When using `@Payload()` in a NestJS RMQ handler, the payload is typically the raw message body. Developers need to manually parse the JSON and cast it to the `StandardMessage<T>` type.
*   **Solution:** A custom parameter decorator or a pipe to automatically deserialize the AMQP message body (which contains the JSON `StandardMessage` envelope) into a typed `StandardMessage<PayloadType>` object and potentially extract just the business `payload`.

    ```typescript
    // standard-message.decorator.ts (Conceptual)
    import { createParamDecorator, ExecutionContext, ParsePipe } from '@nestjs/common';
    import { RmqContext } from '@nestjs/microservices';
    // import { StandardMessage } from './01-standard-message-envelope'; // Assumes this type is available

    // Interface for the StandardMessage for example purposes
    export interface StandardMessage<T> {
      messageId: string;
      messageType: string;
      envelopeVersion: string;
      timestamp: string;
      sourceService: string;
      correlationId?: string;
      payload: T;
      partitionKey?: string;
    }

    // Option 1: Decorator to get the full StandardMessage
    export const EventEnvelope = createParamDecorator(
      (data: unknown, ctx: ExecutionContext): StandardMessage<any> | null => {
        const context = ctx.switchToRpc().getContext<RmqContext>();
        const message = context.getMessage(); // amqp.Message
        if (message?.content) {
          try {
            const parsedContent = JSON.parse(message.content.toString());
            // Here you could add validation against a Zod/Joi schema for StandardMessage if desired
            return parsedContent as StandardMessage<any>;
          } catch (e) {
            // Log error: Failed to parse message content
            return null; // Or throw an error to NACK the message
          }
        }
        return null;
      },
    );

    // Option 2: Decorator to directly get the business payload (T)
    // This would typically also use a Pipe for validation if desired
    export const EventPayload = createParamDecorator(
      (data: unknown, ctx: ExecutionContext): any | null => {
        const context = ctx.switchToRpc().getContext<RmqContext>();
        const message = context.getMessage(); // amqp.Message
        if (message?.content) {
          try {
            const parsedContent = JSON.parse(message.content.toString()) as StandardMessage<any>;
            return parsedContent.payload;
          } catch (e) {
            // Log error
            return null;
          }
        }
        return null;
      },
    );
    ```
*   **Usage:**
    ```typescript
    import { Controller } from '@nestjs/common';
    import { EventPattern, Ctx, RmqContext } from '@nestjs/microservices';
    // import { EventEnvelope, EventPayload, StandardMessage } from '@my-org/rabbitmq-event-utils';

    interface UserCreatedPayload { userId: string; email: string; }

    @Controller()
    export class UserEventsController {
      @EventPattern('user.created') // Listens to messages with routing key 'user.created'
      async handleUserCreated(
        @EventPayload() payload: UserCreatedPayload, // Automatically gets & types the business payload
        @EventEnvelope() envelope: StandardMessage<UserCreatedPayload>, // Gets the full envelope
        @Ctx() context: RmqContext, // Standard RmqContext for ack/nack
      ) {
        console.log(`Received UserCreatedEvent (ID: ${envelope.messageId}):`, payload);
        // ... business logic ...
        const channel = context.getChannelRef();
        const originalMsg = context.getMessage();
        channel.ack(originalMsg);
      }
    }
    ```

### 3.2. Correlation ID Propagation for Logging

*   **Problem:** Extracting `correlationId` from the message envelope or AMQP properties and making it available for structured logging within the handler.
*   **Solution:** An interceptor or enhancements to the custom decorators (`@EventEnvelope`, `@EventPayload`) to automatically add the `correlationId` to a request-scoped context (e.g., using `AsyncLocalStorage` or by attaching to the request object if applicable in the microservice context), which the `LoggingModule` can then pick up.

### 3.3. Standardized DLX/Retry Configuration

*   **Problem:** Implementing consistent retry and Dead Letter Exchange (DLX) logic for message processing failures.
*   **Solution:**
    *   Provide clear documentation and examples on configuring queues with DLX arguments when services declare their queues.
    *   Offer a NestJS interceptor that can automatically handle retries (with backoff) for a certain number of attempts before NACKing the message (and requeueing it to a DLQ if the queue is configured with one).
    *   The interceptor could inspect AMQP message headers for retry counts (e.g., `x-death` header from RabbitMQ DLX).
    ```typescript
    // Conceptual RetryInterceptor
    @Injectable()
    export class RabbitMQRetryInterceptor implements NestInterceptor {
      constructor(private readonly defaultRetries: number = 3) {}
      async intercept(context: ExecutionContext, next: CallHandler): Promise<Observable<any>> {
        // ... logic to get retry count from message headers (x-death)
        // ... if retries exhausted, NACK and DONT requeue (message goes to DLX)
        // ... otherwise, call next.handle().pipe(catchError(... NACK and requeue for retry or throw to trigger NACK))
        return next.handle(); // Simplified
      }
    }
    ```

### 3.4. Idempotent Consumer Helper (Optional)

*   **Problem:** Ensuring messages are processed exactly once, even if redelivered.
*   **Solution:** While true exactly-once processing is complex, the library could provide decorators or utilities to help implement idempotency checks based on `messageId` against a persistent store (e.g., Redis, database table for processed message IDs). This is often best handled within the business logic itself but helpers could reduce boilerplate.

## 4. Configuration of Queues and Exchanges

*   This library itself will likely **not** be responsible for declaring queues, exchanges, and bindings. This is typically done by:
    *   The consuming service itself on startup (idempotently).
    *   Infrastructure-as-Code (IaC) scripts (e.g., Terraform, CloudFormation) managing Amazon MQ.
*   However, the library **will** provide clear guidance, conventions, and potentially helper functions or configuration examples for services to declare these resources in a standardized way (e.g., naming conventions, DLX setup, durable queues).

    **Example Queue Declaration Arguments (for service setup):**
    ```javascript
    // When a service defines its queue (e.g., using amqplib directly or via NestJS RMQ options)
    {
      durable: true,
      arguments: {
        'x-dead-letter-exchange': 'my_service_dlx', // Name of the DLX
        'x-dead-letter-routing-key': 'original_routing_key_dlq' // Routing key for messages going to DLX
        // 'x-message-ttl': 60000, // Optional: message TTL on the queue
        // 'x-max-length': 10000, // Optional: max number of messages in queue
      }
    }
    ```

## 5. Usage Example (with NestJS RMQ Transport)

Services would configure the RabbitMQ transport in their `main.ts` or a module:

```typescript
// main.ts or a module
const app = await NestFactory.createMicroservice<MicroserviceOptions>(AppModule, {
  transport: Transport.RMQ,
  options: {
    urls: [process.env.RABBITMQ_URL], // From config
    queue: 'my_service_queue',
    queueOptions: {
      durable: true,
      // ... other queue options like DLX arguments
    },
    noAck: false, // Explicitly require message acknowledgment
    prefetchCount: 10, // Example: number of messages to fetch at once
  },
});
await app.listen();
```

And then use decorators like `@EventPattern`, `@EventPayload`, `@EventEnvelope` in their controllers/services.

## 6. Error Handling Flow

1.  Handler method throws an error (or promise rejects).
2.  (Optional) `RabbitMQRetryInterceptor` catches the error.
    *   If retries not exhausted, NACKs the message with `requeue: true` (or specific retry queue logic).
    *   If retries exhausted, NACKs the message with `requeue: false`. Message goes to DLX if configured.
3.  If no interceptor, NestJS RMQ transport NACKs the message (requeue behavior depends on its default or error). It's generally better to explicitly control this.
4.  Messages in DLX can be inspected/reprocessed manually or by a dedicated DLQ consumer.

This approach provides a balance between leveraging NestJS's built-in capabilities and providing valuable, standardized utilities to enhance the developer experience and robustness of RabbitMQ consumers.