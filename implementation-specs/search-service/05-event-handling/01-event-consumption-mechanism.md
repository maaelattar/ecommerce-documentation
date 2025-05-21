# Event Consumption Mechanism

## Overview

The Search Service relies on an event-driven architecture to stay synchronized with data changes occurring in other microservices. It consumes events published to a message broker (e.g., Apache Kafka) by services like Product, Category, and Content services. This document outlines the mechanism used for event consumption.

## Message Broker

*   **Primary Choice**: Apache Kafka (Assumed based on common microservice patterns, confirm with overall architecture).
*   **Alternative**: RabbitMQ, AWS SQS/SNS, Google Cloud Pub/Sub, etc., if specified by the platform's technology stack.

### Kafka Configuration

*   **Topics**: Dedicated topics will be used for different types of events or domains (e.g., `product.events`, `category.events`, `content.events`). Alternatively, a single topic with different event types distinguished by a header or a field in the payload could be used, but separate topics offer better segregation and independent scaling of consumers.
*   **Consumer Groups**: The Search Service will use a specific consumer group ID (e.g., `search-service-consumer-group`) to ensure that each event is processed by one instance of the Search Service if it's scaled horizontally. This allows for load balancing and fault tolerance.
*   **Partitions**: Topics should be partitioned appropriately to allow for parallel consumption and ordering guarantees within a partition (e.g., events for the same product ID go to the same partition).
*   **Serialization/Deserialization**: Events are expected to be in a standard format like JSON. Schema management (e.g., Avro with a Schema Registry) is recommended for robust evolution of event structures.

## Event Consumer Implementation (NestJS)

The Search Service, being a NestJS application, will leverage NestJS's microservice capabilities or a dedicated Kafka client library like `kafkajs` for event consumption.

### Using NestJS Microservice Transporter (e.g., Kafka)

NestJS provides built-in support for various microservice transporters, including Kafka. This is often the preferred way for integrating event consumption within a NestJS application.

**Example (`main.ts` or a dedicated module):**

```typescript
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { MicroserviceOptions, Transport } from '@nestjs/microservices';
import { ConfigService } from '@nestjs/config';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const configService = app.get(ConfigService);

  // Start the microservice listener for Kafka events
  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.KAFKA,
    options: {
      client: {
        brokers: configService.get<string[]>('kafka.brokers'),
        // clientId: 'search-service', // Optional: helps in Kafka logs
        // ssl: true, // If applicable
        // sasl: { // If applicable
        //   mechanism: 'plain',
        //   username: configService.get<string>('kafka.sasl.username'),
        //   password: configService.get<string>('kafka.sasl.password'),
        // },
      },
      consumer: {
        groupId: configService.get<string>('kafka.consumerGroupId', 'search-service-consumer-group'),
        // allowAutoTopicCreation: false, // Recommended for production
      },
      // subscribe: {
      //   topics: ['product.events', 'category.events', 'content.events'], // Or use @MessagePattern for specific topics/events
      //   fromBeginning: false, // Or true, depending on recovery needs
      // },
    },
  });

  await app.startAllMicroservices();
  await app.listen(configService.get<number>('http.port', 3000));
  console.log(`Search Service HTTP server running on port ${configService.get<number>('http.port', 3000)}`);
  console.log(`Search Service Kafka consumer connected`);
}
bootstrap();
```

**Event Handler (in a service or controller):**

Event handlers use decorators like `@MessagePattern('topic.name')` or `@EventPattern('event_name')` to subscribe to specific topics or event types.

```typescript
import { Controller } from '@nestjs/common';
import { MessagePattern, Payload, Ctx, KafkaContext, EventPattern } from '@nestjs/microservices';
import { IndexingService } from '../indexing/indexing.service'; // Your service that updates Elasticsearch

@Controller()
export class EventHandlingController {
  constructor(private readonly indexingService: IndexingService) {}

  // Example: Listening to a specific topic for all messages
  @MessagePattern('product.events') // Subscribes to the 'product.events' Kafka topic
  async handleProductEvents(@Payload() message: any, @Ctx() context: KafkaContext) {
    const { key, value, topic, partition, offset, headers } = context.getMessage();
    const eventType = headers?.['eventType']?.toString(); // Assuming eventType is in headers

    console.log(`Received event on topic ${topic} [${partition}#${offset}]: ${eventType}`);
    // Delegate to a specific handler based on eventType or message content
    // await this.indexingService.processProductEvent(eventType, value);

    // Manual offset commit can be configured if auto-commit is disabled
    // const heartbeat = context.getHeartbeat();
    // await heartbeat(); // if processing takes time
    // Do not manually commit if auto-commit is enabled in Kafka consumer config.
  }

  // Example: Using @EventPattern for more semantic event handling (if event names are part of the message or headers)
  // This pattern is often used when events from different topics might share the same handler logic
  // or if you are using NestJS event bus internally which is then bridged to Kafka.
  // For direct Kafka topic subscription, @MessagePattern is more common.

  @EventPattern('product.created') // This pattern might be matched against a field in the event payload or headers
  async handleProductCreated(@Payload() productData: any) {
    console.log('Processing product.created event:', productData);
    // await this.indexingService.createProductDocument(productData);
  }

  @EventPattern('product.updated')
  async handleProductUpdated(@Payload() productData: any) {
    console.log('Processing product.updated event:', productData);
    // await this.indexingService.updateProductDocument(productData.id, productData);
  }

  @EventPattern('product.deleted')
  async handleProductDeleted(@Payload() data: { id: string }) {
    console.log('Processing product.deleted event:', data);
    // await this.indexingService.deleteProductDocument(data.id);
  }

  // Similar handlers for category events, content events, etc.
  @MessagePattern('category.events')
  async handleCategoryEvents(@Payload() message: any, @Ctx() context: KafkaContext) {
    // ... process category events
  }

  @MessagePattern('content.events')
  async handleContentEvents(@Payload() message: any, @Ctx() context: KafkaContext) {
    // ... process content events
  }
}
```

### Using `kafkajs` Directly

For more fine-grained control over Kafka consumer behavior, `kafkajs` can be used directly. This would involve setting up the Kafka consumer, subscribing to topics, and managing the message processing loop manually within a NestJS service (e.g., an `onModuleInit` lifecycle hook).

**Pros**: Maximum flexibility, direct access to all `kafkajs` features.
**Cons**: More boilerplate code, less integrated with NestJS DI for handlers (though still manageable).

## Key Considerations

*   **Configuration Management**: Kafka broker addresses, consumer group IDs, topic names, and security settings (SASL/SSL) will be managed via the `@nestjs/config` module, sourced from environment variables or configuration files.
*   **Connection Management**: The NestJS Kafka transporter or `kafkajs` client will handle connection retries and reconnections to the Kafka brokers.
*   **Backpressure**: If event processing is slow, the rate of consumption might need to be managed. Kafka inherently handles some of this by batching, but if processing is CPU/IO bound, ensure service instances can keep up or scale them out.
*   **Offset Management**: Kafka uses offsets to track consumed messages. By default, NestJS Kafka transporter (and `kafkajs`) can auto-commit offsets. For critical operations where at-least-once processing is vital and processing might fail, manual offset commit after successful processing might be considered, though this adds complexity. This is crucial for `08-error-handling-and-resilience.md`.
*   **Dead Letter Queues (DLQs)**: For events that repeatedly fail processing, a DLQ strategy is essential. This involves sending problematic messages to a separate topic for later inspection and reprocessing. This will be detailed in `08-error-handling-and-resilience.md`.

## Next Steps

With the consumption mechanism in place, the subsequent documents will detail:
*   Specific events subscribed to (`02-*`, `03-*`, `04-*`).
*   How these events are processed and transformed (`06-*`).
*   Logic for updating search indexes (`07-*`).
*   Error handling and resilience strategies (`08-*`).
