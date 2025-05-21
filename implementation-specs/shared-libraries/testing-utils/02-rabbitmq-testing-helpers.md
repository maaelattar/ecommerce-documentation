# 02: RabbitMQ Testing Helpers

## 1. Introduction

This document outlines testing utilities designed to help test microservice components that interact with RabbitMQ. These helpers, part of the `testing-utils` library, focus on mocking RabbitMQ producers and creating message payloads for testing consumers, aligning with the patterns established in the `rabbitmq-event-utils` shared library.

## 2. MockRabbitMQProducer

Many services will use a `RabbitMQProducerService` (from `rabbitmq-event-utils`) to publish messages. `MockRabbitMQProducer` provides a test double for this service.

### 2.1. Purpose

*   Allow testing of services that publish messages without an actual RabbitMQ connection.
*   Enable assertions that messages were "sent" with the correct payload, to the correct exchange and routing key.
*   Capture published messages for inspection.

### 2.2. Implementation Sketch

```typescript
// In @ecommerce-platform/testing-utils/src/mocks/mock-rabbitmq-producer.service.ts

// Assuming RabbitMQProducerService from @ecommerce-platform/rabbitmq-event-utils
// has a method like: publish<T>(exchange: string, routingKey: string, message: StandardMessage<T>): Promise<void>;
// And StandardMessage is the envelope defined in rabbitmq-event-utils.

export interface CapturedMessage {
  exchange: string;
  routingKey: string;
  message: any; // StandardMessage<any>
  options?: any; // Any publish options if your service uses them
}

export class MockRabbitMQProducerService {
  private publishedMessages: CapturedMessage[] = [];

  async publish<T>(
    exchange: string, 
    routingKey: string, 
    message: /* StandardMessage<T> */ any, 
    options?: any
  ): Promise<void> {
    this.publishedMessages.push({ exchange, routingKey, message, options });
    // In a real mock, you might also want to spy on this method using Jest/Sinon
    return Promise.resolve();
  }

  // Helper to get all captured messages for assertions
  getMessages(): CapturedMessage[] {
    return this.publishedMessages;
  }

  // Helper to get the last published message
  getLastMessage(): CapturedMessage | undefined {
    return this.publishedMessages[this.publishedMessages.length - 1];
  }
  
  // Helper to find messages sent to a specific exchange/routingKey
  getMessagesByRoute(exchange: string, routingKey?: string): CapturedMessage[] {
    return this.publishedMessages.filter(msg => 
      msg.exchange === exchange && (routingKey ? msg.routingKey === routingKey : true)
    );
  }

  // Helper to clear captured messages between tests
  clearMessages(): void {
    this.publishedMessages = [];
  }

  // Mock other methods if your actual RabbitMQProducerService has them (e.g., connect, close)
  async connect(): Promise<void> { return Promise.resolve(); }
  async close(): Promise<void> { return Promise.resolve(); }
}
```

### 2.3. Usage

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { YourPublishingService } from './your-publishing.service';
import { RabbitMQProducerService } from '@ecommerce-platform/rabbitmq-event-utils';
import { MockRabbitMQProducerService, CapturedMessage } from '@ecommerce-platform/testing-utils';

describe('YourPublishingService', () => {
  let service: YourPublishingService;
  let mockProducer: MockRabbitMQProducerService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        YourPublishingService,
        {
          provide: RabbitMQProducerService,
          useClass: MockRabbitMQProducerService,
        },
      ],
    }).compile();

    service = module.get<YourPublishingService>(YourPublishingService);
    // It's often better to get the instance directly for type safety and access to mock-specific methods
    mockProducer = module.get<MockRabbitMQProducerService>(RabbitMQProducerService as any); 
    mockProducer.clearMessages(); // Ensure clean state for each test
  });

  it('should publish a user created event', async () => {
    await service.handleUserCreation({ userId: '123', email: 'test@example.com' });

    const messages = mockProducer.getMessages();
    expect(messages).toHaveLength(1);
    
    const publishedEvent = messages[0];
    expect(publishedEvent.exchange).toBe('user-events-exchange');
    expect(publishedEvent.routingKey).toBe('user.created');
    expect(publishedEvent.message.payload.userId).toBe('123');
    // Further assertions on the StandardMessage envelope (messageId, timestamp, etc.)
  });
});
```

## 3. RabbitMQMessageFactory

When testing consumer logic (e.g., a NestJS microservice controller method decorated with `@EventPattern`), you need to construct message objects that mimic what RabbitMQ (via `@nestjs/microservices`) would deliver.

### 3.1. Purpose

*   Provide helper functions to easily create valid message objects, including the standard message envelope, for testing consumer handlers.
*   Ensure consistency in the structure of test messages.

### 3.2. Implementation Sketch

```typescript
// In @ecommerce-platform/testing-utils/src/factories/rabbitmq-message.factory.ts

// Assuming StandardMessage and its metadata fields are defined in @ecommerce-platform/rabbitmq-event-utils
// E.g., interface StandardMessage<T> { messageId: string; messageType: string; ... payload: T; }

export class RabbitMQMessageFactory {
  static create<T>(
    payload: T,
    messageType: string,
    overrideProps: Partial</*StandardMessage<T> & additional context props if any*/any> = {},
  ): /* StandardMessage<T> */ any {
    const defaults = {
      messageId: `test-msg-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`,
      timestamp: new Date().toISOString(),
      sourceService: 'test-source-service',
      messageVersion: '1.0',
      // ... other default envelope properties
    };

    return {
      ...defaults,
      messageType,
      payload,
      ...overrideProps,
    };
  }

  // If using NestJS microservices with RabbitMQ, the @Payload() decorator might get just the payload,
  // while @Ctx() gets RmqContext. The factory could also help create mock RmqContext if needed.
}
```

### 3.3. Usage (Testing a NestJS Microservice Event Handler)

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { YourConsumerController } from './your-consumer.controller';
import { RabbitMQMessageFactory } from '@ecommerce-platform/testing-utils';
// import { RmqContext } from '@nestjs/microservices'; // For context testing

describe('YourConsumerController', () => {
  let controller: YourConsumerController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [YourConsumerController],
      // ... mock other dependencies of YourConsumerController
    }).compile();
    controller = module.get<YourConsumerController>(YourConsumerController);
  });

  it('should process an order.created event correctly', async () => {
    const orderPayload = { orderId: 'order-abc', items: [], total: 100 };
    const message = RabbitMQMessageFactory.create(orderPayload, 'order.created');

    // const mockContext = { /* mock RmqContext methods if needed */ getMessage: () => message, getChannelRef: () => ({} as any) };
    
    // Assuming your handler is like: @EventPattern('order.created') async handleOrderCreated(@Payload() data: any, @Ctx() context: RmqContext) {}
    // Call the handler directly for unit testing:
    await controller.handleOrderCreated(message.payload /* , mockContext as RmqContext */);

    // ... assertions: verify dependencies were called, state changed, etc.
  });
});
```

## 4. Simulating Consumer Event Handling

For more integrated tests of consumers, especially if they involve acknowledging messages or interacting with the `RmqContext`, you might use `@nestjs/testing` more deeply. The `RabbitMQMessageFactory` helps create the input. For the context, you might need a more elaborate mock if your handlers use `channel.ack(originalMsg)`.

Refer to NestJS documentation on testing microservices for more advanced scenarios.

These helpers aim to simplify testing of RabbitMQ interactions significantly.
