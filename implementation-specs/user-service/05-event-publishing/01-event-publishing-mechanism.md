# 01 - Event Publishing Mechanism

This document describes the primary mechanism and technologies used by the User Service for publishing domain events, aligning with the platform's event-driven architecture strategy (see ADR-018 and TDAC/03-message-broker-selection.md).

## 1. Message Broker

*   **Primary Technology**: RabbitMQ, specifically leveraging **Amazon MQ for RabbitMQ**.
*   **Rationale**:
    *   Provides reliable message delivery with acknowledgements and persistent messages.
    *   Offers flexible routing capabilities using exchanges and bindings.
    *   Mature and well-supported in the Node.js/NestJS ecosystem.
    *   Amazon MQ for RabbitMQ offers a managed service, reducing operational overhead.
    *   Aligns with the platform's decision (ADR-018) for a robust general-purpose message broker.
*   **Secondary/Specialized Option**: For scenarios requiring extremely high throughput or event stream processing capabilities beyond typical RabbitMQ use cases, Apache Kafka (via Amazon MSK) is the designated secondary option. The User Service will primarily use RabbitMQ.
*   **Shared Library**: The `@ecommerce-platform/rabbitmq-event-utils` shared library will be used to standardize RabbitMQ interactions.

## 2. Integration with Message Broker

*   **NestJS Modules**: The User Service will integrate with RabbitMQ using the `RabbitMQProducerModule` from the `@ecommerce-platform/rabbitmq-event-utils` library. This module provides a `RabbitMQProducerService` for publishing messages.
*   **Configuration**:
    *   RabbitMQ connection URI (e.g., `AMQP_URI="amqps://user:password@host:port"`).
    *   Default exchange name and type for user events (e.g., `USER_EVENTS_EXCHANGE="user.events"` of type `topic`).
    *   These configurations will be managed via the `ConfigService` (`@nestjs/config`) and `@ecommerce-platform/nestjs-core-utils`.

    ```typescript
    // Example: In a module definition (e.g., UserModule or a dedicated UserEventsIntegrationModule)
    import { Module } from '@nestjs/common';
    import { ConfigModule, ConfigService } from '@nestjs/config';
    import { RabbitMQProducerModule, RabbitMQProducerService } from '@ecommerce-platform/rabbitmq-event-utils';
    import { UserEventPublisher } from './user-event-publisher.service'; // Assumed service

    @Module({
      imports: [
        RabbitMQProducerModule.forRootAsync({
          imports: [ConfigModule], // Make ConfigService available
          useFactory: async (configService: ConfigService) => ({
            uri: configService.getOrThrow<string>('AMQP_URI'),
            defaultExchange: {
              name: configService.getOrThrow<string>('USER_EVENTS_EXCHANGE'),
              type: 'topic', // Example, could be direct or fanout based on needs
              options: { durable: true },
            },
            // Other common options like default serialization, connection retries, etc.
            // can be configured here or rely on library defaults.
            // Refer to @ecommerce-platform/rabbitmq-event-utils documentation.
          }),
          inject: [ConfigService],
        }),
      ],
      providers: [UserEventPublisher, RabbitMQProducerService], // RabbitMQProducerService might be re-exported or directly used
      exports: [UserEventPublisher, RabbitMQProducerModule], // Or just UserEventPublisher if it encapsulates producer
    })
    export class UserEventsIntegrationModule {}
    ```

## 3. Event Serialization Format

*   **Format**: JSON (JavaScript Object Notation).
*   **Rationale**: JSON is human-readable, widely supported, and integrates easily with NestJS.
*   **Structure**: Events will adhere to the `StandardMessage<T>` envelope defined in the `@ecommerce-platform/rabbitmq-event-utils` library. This ensures consistency across all published events.

    ```json
    // Example structure (referencing StandardMessage<T> from rabbitmq-event-utils)
    {
      "messageId": "uuid-v4-generated-for-this-instance",
      "messageType": "UserRegistered.v1", // Event type + version
      "envelopeVersion": "1.0", // Version of the StandardMessage schema itself
      "timestamp": "2023-10-28T12:00:00.123Z", // ISO 8601 format
      "sourceService": "UserService",
      "correlationId": "uuid-for-tracking-request-across-services", // Optional
      "payload": {
        // Event-specific data for UserRegistered.v1
        "userId": "user-uuid-abc",
        "email": "user@example.com",
        "registeredAt": "2023-10-28T12:00:00.123Z"
        // ... other relevant fields
      },
      "partitionKey": "user-uuid-abc" // Optional, can assist consumers or specialized routing
    }
    ```
    *   The `rabbitmq-event-utils` library will also handle setting appropriate AMQP message properties (e.g., `content_type`, `delivery_mode`, `app_id`, `correlation_id`, `message_id` from the envelope).

## 4. Event Publishing Logic

*   A dedicated `UserEventPublisher` service (or methods within originating services like `AuthService`, `UserService`) will be responsible for:
    1.  Constructing the event payload (`payload` field of `StandardMessage<T>`) according to the defined schema for that event type.
    2.  Instantiating the `StandardMessage<T>` object, populating all required envelope fields.
    3.  Utilizing the `RabbitMQProducerService.publish()` method from `@ecommerce-platform/rabbitmq-event-utils`.
        *   This method will take the exchange name, routing key, and the `StandardMessage<T>` object.
        *   Example: `await producerService.publish('user.events', 'user.registered.v1', standardMessage);`
        *   The routing key (e.g., `user.registered.v1`, `user.profile.updated.v1`) is crucial for enabling topic-based subscriptions by consumers.
        *   The `RabbitMQProducerService` handles serialization to JSON and setting AMQP properties.
*   **Message Keys for Ordering**: While RabbitMQ doesn't use "message keys" for partitioning in the same way Kafka does, if strict ordering for events related to a specific entity (e.g., a particular user) is required by a consumer, strategies like using a consistent routing key for that entity or employing a sharded queue approach with a consistent hashing mechanism (potentially using the `partitionKey` field) would need to be considered at the consumer/broker topology level. For general event publishing, topic-based routing keys are standard.

## 5. Asynchronous Nature

*   Event publishing via RabbitMQ is an asynchronous operation. The User Service will typically publish an event and not wait for downstream consumers to process it before completing the primary user-facing operation.
*   Publisher confirms can be used by the `RabbitMQProducerService` to ensure the message has been durably accepted by the RabbitMQ broker, enhancing reliability.
*   This ensures loose coupling and resilience; if a consuming service is down, the User Service can continue operating (assuming messages are persisted in RabbitMQ).

This mechanism, leveraging RabbitMQ and the `rabbitmq-event-utils` library, provides a robust, standardized, and scalable way for the User Service to broadcast domain events.
