# 02: RabbitMQ Producer Module (`RabbitMQProducerModule`)

## 1. Purpose

The `RabbitMQProducerModule` within the `rabbitmq-event-utils` shared library provides a standardized and easy-to-use mechanism for NestJS microservices to publish messages to RabbitMQ (specifically Amazon MQ for RabbitMQ). It abstracts the underlying AMQP client library complexities, handles connection management, and ensures messages are published using the standard message envelope.

Key objectives:
*   Simplify the process of publishing messages to RabbitMQ.
*   Ensure consistent use of the standard message envelope and AMQP properties.
*   Manage AMQP connections and channels robustly.
*   Provide support for publisher confirms to ensure message delivery to the broker.
*   Integrate with shared configuration for RabbitMQ connection details.

## 2. Features

*   **Dynamic Module:** A NestJS dynamic module (`forRootAsync` or `forRoot`) to allow configuration of connection parameters (e.g., AMQP URI, default exchange) when imported.
*   **`RabbitMQProducerService`:** A service that encapsulates the logic for connecting to RabbitMQ and publishing messages.
    *   Manages AMQP connection and channels.
    *   Handles automatic reconnection with backoff strategies in case of connection failures.
    *   Provides a simple `publish<T>(exchange: string, routingKey: string, payload: T, messageType: string, options?: PublishOptions)` method.
*   **Standard Envelope Wrapping:** Automatically wraps the provided `payload` within the `StandardMessage<T>` envelope defined in `01-standard-message-envelope.md` before publishing.
    *   Generates `messageId`, sets `timestamp`, `envelopeVersion`, `sourceService` (from module configuration).
    *   Populates relevant AMQP properties (`message_id`, `correlation_id`, `content_type`, `type`, `app_id`, `delivery_mode`).
*   **Publisher Confirms:** Supports RabbitMQ publisher confirms to ensure messages have been accepted by the broker. The `publish` method can optionally return a Promise that resolves upon confirmation.
*   **Error Handling:** Provides clear error handling for publishing failures (e.g., connection issues, nack from broker).
*   **Configuration:** Leverages the `SharedConfigModule` (from `nestjs-core-utils`) or environment variables for AMQP connection URIs and other settings.

```typescript
// Interface for optional publish options
interface PublishOptions {
  correlationId?: string;
  partitionKey?: string; // For the envelope
  amqpProperties?: amqplib.Options.Publish; // To override or add specific AMQP properties
  waitForConfirmation?: boolean; // Default true
  confirmationTimeout?: number; // ms, default e.g. 5000ms
}
```

## 3. Implementation Considerations (using `amqplib`)

*   **Connection Management:**
    *   The `RabbitMQProducerService` will establish a persistent connection to RabbitMQ upon initialization.
    *   It will create one or more channels for publishing. Channels can be reused.
    *   Implement robust reconnection logic (e.g., exponential backoff) if the connection drops.
    *   Handle AMQP connection and channel events (`error`, `close`).
*   **`RabbitMQProducerService.publish<T>()` method:**
    1.  Accepts `exchange`, `routingKey`, `payload` (the business data), `messageType`.
    2.  Accepts optional `PublishOptions` for `correlationId`, `partitionKey`, custom AMQP properties, and publisher confirm behavior.
    3.  Constructs the `StandardMessage<T>` envelope:
        *   `messageId`: Generate UUID.
        *   `messageType`: Provided as argument.
        *   `envelopeVersion`: From a constant (e.g., "1.0").
        *   `timestamp`: Current ISO 8601 timestamp.
        *   `sourceService`: Configured at module level.
        *   `correlationId`: From `PublishOptions` or propagated.
        *   `payload`: The provided business data.
        *   `partitionKey`: From `PublishOptions`.
    4.  Serialize the `StandardMessage<T>` to a JSON string (Buffer).
    5.  Prepare AMQP properties:
        *   `contentType: "application/json"`
        *   `contentEncoding: "UTF-8"`
        *   `deliveryMode: 2` (persistent)
        *   `messageId: envelope.messageId`
        *   `correlationId: envelope.correlationId`
        *   `type: envelope.messageType`
        *   `appId: envelope.sourceService`
        *   `timestamp: Math.floor(new Date(envelope.timestamp).getTime() / 1000)` (seconds since epoch for AMQP)
        *   Merge with any custom `amqpProperties` from `PublishOptions`.
    6.  Publish the message using `channel.publish(exchange, routingKey, Buffer.from(jsonBody), amqpProperties)`.
    7.  If publisher confirms are enabled (default), use `channel.waitForConfirms()` or handle the callback mechanism of `channel.publish` to await broker acknowledgement.
*   **Module Setup (`RabbitMQProducerModule.forRootAsync`):**
    ```typescript
    // rabbitmq-producer.module.ts (simplified)
    import { DynamicModule, Module, Global } from '@nestjs/common';
    import { ConfigService } from '@nestjs/config';
    import { RabbitMQProducerService } from './rabbitmq-producer.service';
    // import { SharedConfigModule } from '@my-org/nestjs-core-utils'; // Assumed to be global or imported

    export interface RabbitMQProducerModuleOptions {
      amqpUrlEnvKey?: string; // Env key for AMQP URL, e.g., 'RABBITMQ_URL'
      defaultSourceService: string;
      connectionName?: string; // For multiple connections if ever needed
      // ... other options like default exchange, connection retries etc.
    }

    @Global() // Optional: to make ProducerService available globally
    @Module({})
    export class RabbitMQProducerModule {
      static forRootAsync(options: RabbitMQProducerModuleOptions): DynamicModule {
        return {
          module: RabbitMQProducerModule,
          // imports: [SharedConfigModule], // Ensure ConfigService is available
          providers: [
            {
              provide: RabbitMQProducerService,
              useFactory: async (configService: ConfigService) => {
                const amqpUrl = configService.get<string>(
                  options.amqpUrlEnvKey || 'RABBITMQ_PRIMARY_URL'
                );
                if (!amqpUrl) {
                  throw new Error('RabbitMQ AMQP URL not configured');
                }
                const service = new RabbitMQProducerService(
                  amqpUrl,
                  options.defaultSourceService
                );
                await service.connect(); // Establish connection on init
                return service;
              },
              inject: [ConfigService],
            },
          ],
          exports: [RabbitMQProducerService],
        };
      }
    }
    ```

## 4. Usage

1.  **Import and Configure:** Import `RabbitMQProducerModule.forRootAsync(...)` into the root `AppModule` of a service.
    ```typescript
    // app.module.ts
    import { Module } from '@nestjs/common';
    import { RabbitMQProducerModule } from '@my-org/rabbitmq-event-utils';
    import { ConfigModule } from '@nestjs/config'; // Assuming basic ConfigModule for env vars

    @Module({
      imports: [
        ConfigModule.forRoot({ isGlobal: true }), // Ensure env vars are loaded
        RabbitMQProducerModule.forRootAsync({
          defaultSourceService: 'MyAwesomeService',
          amqpUrlEnvKey: 'AMQP_CONNECTION_STRING',
        }),
        // ... other modules
      ],
    })
    export class AppModule {}
    ```
2.  **Inject `RabbitMQProducerService`:**
    ```typescript
    // my-event-emitter.service.ts
    import { Injectable } from '@nestjs/common';
    import { RabbitMQProducerService } from '@my-org/rabbitmq-event-utils';

    interface OrderCreatedPayload {
      orderId: string;
      customerId: string;
      amount: number;
    }

    @Injectable()
    export class MyEventEmitterService {
      constructor(private readonly producerService: RabbitMQProducerService) {}

      async publishOrderCreatedEvent(payload: OrderCreatedPayload, correlationId?: string) {
        try {
          await this.producerService.publish<OrderCreatedPayload>(
            'orders_exchange',       // Exchange name
            'order.created',         // Routing key
            payload,                 // Business payload
            'OrderCreatedEvent.v1',  // Message Type
            { correlationId, waitForConfirmation: true }
          );
          console.log('OrderCreatedEvent published successfully');
        } catch (error) {
          console.error('Failed to publish OrderCreatedEvent', error);
          // Handle error appropriately (e.g., retry, log to critical monitoring)
        }
      }
    }
    ```

## 5. Error Handling & Reliability

*   The service will implement retries for connection establishment.
*   Publisher confirms provide assurance that messages are accepted by the broker.
*   Applications using this service are still responsible for handling errors returned by the `publish` method (e.g., if the broker NACKs a message or if confirmation times out) and implementing their own retry or alternative logic (like an outbox pattern for critical events if the broker is temporarily unavailable for an extended period).

This producer module will significantly simplify robust and consistent message publishing to RabbitMQ across the platform.