# RabbitMQ Event Utils Implementation Guide 🐰

> **Goal**: Build robust event-driven messaging utilities with transactional outbox pattern and reliable delivery

---

## 🎯 **What You'll Build**

A comprehensive event messaging library with:
- **Event publishing and subscribing** with type safety
- **Transactional outbox pattern** for reliable event delivery
- **Dead letter queue handling** for failed messages
- **Event correlation and tracing** across services
- **Saga orchestration support** for distributed transactions

---

## 📦 **Package Setup**

### **1. Initialize Package**
```bash
cd packages/rabbitmq-event-utils
npm init -y
```

### **2. Package.json Configuration**
```json
{
  "name": "@ecommerce/rabbitmq-event-utils",
  "version": "1.0.0",
  "description": "RabbitMQ event utilities for ecommerce microservices",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "test:watch": "jest --watch",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/microservices": "^10.0.0",
    "amqplib": "^0.10.0",
    "class-validator": "^0.14.0",
    "class-transformer": "^0.5.0",
    "uuid": "^9.0.0",
    "reflect-metadata": "^0.1.13"
  },
  "devDependencies": {
    "@types/amqplib": "^0.10.0",
    "@types/uuid": "^9.0.0",
    "jest": "^29.0.0",
    "typescript": "^5.0.0"
  }
}
```

---

## 🏗️ **Implementation Structure**

```
packages/rabbitmq-event-utils/
├── src/
│   ├── types/
│   │   ├── event.types.ts
│   │   ├── message.types.ts
│   │   └── index.ts
│   ├── decorators/
│   │   ├── event-handler.decorator.ts
│   │   ├── saga.decorators.ts
│   │   └── index.ts
│   ├── services/
│   │   ├── event-publisher.service.ts
│   │   ├── event-subscriber.service.ts
│   │   ├── outbox.service.ts
│   │   └── index.ts
│   ├── patterns/
│   │   ├── transactional-outbox.ts
│   │   ├── saga-manager.ts
│   │   └── index.ts
│   ├── config/
│   │   ├── rabbitmq.config.ts
│   │   └── index.ts
│   └── index.ts
└── tests/
```

---

## 🏷️ **1. Type Definitions**

### **Event Types**
```typescript
// src/types/event.types.ts
export interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  aggregateType: string;
  eventVersion: number;
  occurredAt: Date;
  correlationId?: string;
  causationId?: string;
  data: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface EventEnvelope {
  event: DomainEvent;
  routingKey: string;
  exchange: string;
  messageId: string;
  timestamp: Date;
  retryCount: number;
  headers: Record<string, any>;
}

export interface EventHandler<T extends DomainEvent = DomainEvent> {
  handle(event: T): Promise<void>;
}

export interface EventSubscription {
  eventType: string;
  handler: EventHandler;
  queue: string;
  routingKey: string;
  exchange: string;
  deadLetterQueue?: string;
  retryPolicy?: RetryPolicy;
}

export interface RetryPolicy {
  maxRetries: number;
  backoffMultiplier: number;
  initialDelay: number;
  maxDelay: number;
}
```

### **Message Types**
```typescript
// src/types/message.types.ts
export interface MessageConfig {
  exchange: string;
  routingKey: string;
  queue?: string;
  durable?: boolean;
  persistent?: boolean;
  ttl?: number;
  priority?: number;
}

export interface OutboxEvent {
  id: string;
  aggregateId: string;
  eventType: string;
  eventData: any;
  routingKey: string;
  exchange: string;
  occurredAt: Date;
  processedAt?: Date;
  status: OutboxEventStatus;
  retryCount: number;
  lastError?: string;
}

export enum OutboxEventStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  PROCESSED = 'processed',
  FAILED = 'failed'
}

export interface SagaState {
  sagaId: string;
  sagaType: string;
  currentStep: string;
  data: Record<string, any>;
  status: SagaStatus;
  startedAt: Date;
  completedAt?: Date;
  compensated?: boolean;
}

export enum SagaStatus {
  STARTED = 'started',
  COMPLETED = 'completed',
  COMPENSATING = 'compensating',
  COMPENSATED = 'compensated',
  FAILED = 'failed'
}
```

---

## 🎨 **2. Decorators Implementation**

### **Event Handler Decorator**
```typescript
// src/decorators/event-handler.decorator.ts
import { SetMetadata } from '@nestjs/common';

export const EVENT_HANDLER_METADATA = 'event_handler_metadata';

export interface EventHandlerMetadata {
  eventType: string;
  queue: string;
  exchange: string;
  routingKey: string;
  deadLetterQueue?: string;
  retryPolicy?: {
    maxRetries: number;
    backoffMultiplier: number;
    initialDelay: number;
    maxDelay: number;
  };
}

export function EventHandler(metadata: EventHandlerMetadata) {
  return (target: any, propertyName?: string, descriptor?: PropertyDescriptor) => {
    if (propertyName && descriptor) {
      // Method decorator
      SetMetadata(EVENT_HANDLER_METADATA, metadata)(target, propertyName, descriptor);
    } else {
      // Class decorator
      SetMetadata(EVENT_HANDLER_METADATA, metadata)(target);
    }
  };
}

// Usage examples:
// @EventHandler({
//   eventType: 'UserRegisteredEvent',
//   queue: 'user-events',
//   exchange: 'user.events',
//   routingKey: 'user.registered'
// })
```

### **Saga Decorators**
```typescript
// src/decorators/saga.decorators.ts
import { SetMetadata } from '@nestjs/common';

export const SAGA_START_METADATA = 'saga_start';
export const SAGA_STEP_METADATA = 'saga_step';
export const SAGA_COMPENSATION_METADATA = 'saga_compensation';

export function SagaStart(sagaType: string) {
  return SetMetadata(SAGA_START_METADATA, sagaType);
}

export function SagaStep(stepName: string, compensationHandler?: string) {
  return SetMetadata(SAGA_STEP_METADATA, { stepName, compensationHandler });
}

export function SagaCompensation(forStep: string) {
  return SetMetadata(SAGA_COMPENSATION_METADATA, forStep);
}

// Usage examples:
// @SagaStart('OrderProcessingSaga')
// @SagaStep('reserveInventory', 'releaseInventory')
// @SagaCompensation('reserveInventory')
```

---

## 🚀 **3. Services Implementation**

### **Event Publisher Service**
```typescript
// src/services/event-publisher.service.ts
import { Injectable, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as amqp from 'amqplib';
import { DomainEvent, EventEnvelope, MessageConfig } from '../types';
import { v4 as uuidv4 } from 'uuid';

@Injectable()
export class EventPublisherService implements OnModuleDestroy {
  private connection: amqp.Connection;
  private channel: amqp.Channel;
  private isConnected = false;

  constructor(private configService: ConfigService) {}

  async initialize(): Promise<void> {
    const rabbitmqUrl = this.configService.get('RABBITMQ_URL');
    
    this.connection = await amqp.connect(rabbitmqUrl);
    this.channel = await this.connection.createChannel();
    
    // Set up channel for publisher confirms
    await this.channel.confirmSelect();
    
    this.isConnected = true;
  }

  async publishEvent(
    event: DomainEvent, 
    config: MessageConfig
  ): Promise<void> {
    if (!this.isConnected) {
      await this.initialize();
    }

    const envelope: EventEnvelope = {
      event,
      routingKey: config.routingKey,
      exchange: config.exchange,
      messageId: uuidv4(),
      timestamp: new Date(),
      retryCount: 0,
      headers: {
        eventType: event.eventType,
        correlationId: event.correlationId,
        causationId: event.causationId
      }
    };

    // Ensure exchange exists
    await this.channel.assertExchange(
      config.exchange, 
      'topic', 
      { durable: true }
    );

    // Publish with confirmation
    const published = this.channel.publish(
      config.exchange,
      config.routingKey,
      Buffer.from(JSON.stringify(envelope)),
      {
        persistent: config.persistent !== false,
        messageId: envelope.messageId,
        timestamp: envelope.timestamp.getTime(),
        headers: envelope.headers,
        priority: config.priority || 0,
        expiration: config.ttl
      }
    );

    if (!published) {
      throw new Error('Failed to publish event - channel buffer full');
    }

    // Wait for confirmation
    await new Promise<void>((resolve, reject) => {
      this.channel.waitForConfirms((err) => {
        if (err) {
          reject(new Error(`Event publication failed: ${err.message}`));
        } else {
          resolve();
        }
      });
    });
  }

  async publishBatch(
    events: Array<{ event: DomainEvent; config: MessageConfig }>
  ): Promise<void> {
    if (!this.isConnected) {
      await this.initialize();
    }

    // Publish all events in batch
    for (const { event, config } of events) {
      await this.publishEvent(event, config);
    }
  }

  async onModuleDestroy(): Promise<void> {
    if (this.channel) {
      await this.channel.close();
    }
    if (this.connection) {
      await this.connection.close();
    }
  }
}
```

### **Event Subscriber Service**
```typescript
// src/services/event-subscriber.service.ts
import { Injectable, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { ModuleRef } from '@nestjs/core';
import * as amqp from 'amqplib';
import { 
  EventEnvelope, 
  EventHandler, 
  EventSubscription,
  RetryPolicy 
} from '../types';

@Injectable()
export class EventSubscriberService implements OnModuleDestroy {
  private connection: amqp.Connection;
  private channel: amqp.Channel;
  private subscriptions: Map<string, EventSubscription> = new Map();
  private isConnected = false;

  constructor(
    private configService: ConfigService,
    private moduleRef: ModuleRef
  ) {}

  async initialize(): Promise<void> {
    const rabbitmqUrl = this.configService.get('RABBITMQ_URL');
    
    this.connection = await amqp.connect(rabbitmqUrl);
    this.channel = await this.connection.createChannel();
    
    // Set prefetch to ensure fair distribution
    await this.channel.prefetch(10);
    
    this.isConnected = true;
  }

  async subscribe(subscription: EventSubscription): Promise<void> {
    if (!this.isConnected) {
      await this.initialize();
    }

    const { eventType, queue, exchange, routingKey, deadLetterQueue } = subscription;

    // Store subscription
    this.subscriptions.set(eventType, subscription);

    // Assert exchange
    await this.channel.assertExchange(exchange, 'topic', { durable: true });

    // Assert dead letter queue if specified
    if (deadLetterQueue) {
      await this.channel.assertQueue(deadLetterQueue, { durable: true });
    }

    // Assert main queue with dead letter configuration
    const queueOptions: any = { 
      durable: true,
      arguments: {}
    };

    if (deadLetterQueue) {
      queueOptions.arguments['x-dead-letter-exchange'] = '';
      queueOptions.arguments['x-dead-letter-routing-key'] = deadLetterQueue;
    }

    await this.channel.assertQueue(queue, queueOptions);

    // Bind queue to exchange
    await this.channel.bindQueue(queue, exchange, routingKey);

    // Start consuming
    await this.channel.consume(queue, async (message) => {
      if (message) {
        await this.handleMessage(message, subscription);
      }
    });
  }

  private async handleMessage(
    message: amqp.ConsumeMessage,
    subscription: EventSubscription
  ): Promise<void> {
    try {
      const envelope: EventEnvelope = JSON.parse(message.content.toString());
      
      // Validate event type
      if (envelope.event.eventType !== subscription.eventType) {
        console.warn(`Unexpected event type: ${envelope.event.eventType}`);
        this.channel.ack(message);
        return;
      }

      // Handle the event
      await subscription.handler.handle(envelope.event);
      
      // Acknowledge successful processing
      this.channel.ack(message);
      
    } catch (error) {
      console.error('Error handling event:', error);
      
      // Determine retry logic
      const retryCount = this.getRetryCount(message);
      const maxRetries = subscription.retryPolicy?.maxRetries || 3;
      
      if (retryCount < maxRetries) {
        // Reject and requeue for retry
        this.channel.nack(message, false, true);
      } else {
        // Send to dead letter queue or discard
        this.channel.nack(message, false, false);
      }
    }
  }

  private getRetryCount(message: amqp.ConsumeMessage): number {
    const xDeathHeader = message.properties.headers?.['x-death'];
    if (Array.isArray(xDeathHeader) && xDeathHeader.length > 0) {
      return xDeathHeader[0].count || 0;
    }
    return 0;
  }

  async unsubscribe(eventType: string): Promise<void> {
    const subscription = this.subscriptions.get(eventType);
    if (subscription) {
      await this.channel.cancel(subscription.queue);
      this.subscriptions.delete(eventType);
    }
  }

  async onModuleDestroy(): Promise<void> {
    if (this.channel) {
      await this.channel.close();
    }
    if (this.connection) {
      await this.connection.close();
    }
  }
}
```

### **Outbox Service**
```typescript
// src/services/outbox.service.ts
import { Injectable } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { OutboxEvent, OutboxEventStatus, DomainEvent } from '../types';
import { EventPublisherService } from './event-publisher.service';

@Injectable()
export class OutboxService {
  constructor(
    private eventPublisher: EventPublisherService
  ) {}

  async saveEvent(
    aggregateId: string,
    event: DomainEvent,
    routingKey: string,
    exchange: string
  ): Promise<void> {
    const outboxEvent: OutboxEvent = {
      id: event.eventId,
      aggregateId,
      eventType: event.eventType,
      eventData: event,
      routingKey,
      exchange,
      occurredAt: event.occurredAt,
      status: OutboxEventStatus.PENDING,
      retryCount: 0
    };

    // In a real implementation, save to database within the same transaction
    // as the business operation
    await this.saveToDatabase(outboxEvent);
  }

  @Cron(CronExpression.EVERY_10_SECONDS)
  async processOutboxEvents(): Promise<void> {
    const pendingEvents = await this.getPendingEvents();
    
    for (const outboxEvent of pendingEvents) {
      try {
        // Mark as processing
        await this.updateEventStatus(
          outboxEvent.id, 
          OutboxEventStatus.PROCESSING
        );

        // Publish the event
        await this.eventPublisher.publishEvent(
          outboxEvent.eventData,
          {
            exchange: outboxEvent.exchange,
            routingKey: outboxEvent.routingKey,
            persistent: true
          }
        );

        // Mark as processed
        await this.updateEventStatus(
          outboxEvent.id, 
          OutboxEventStatus.PROCESSED,
          new Date()
        );

      } catch (error) {
        console.error(`Failed to publish outbox event ${outboxEvent.id}:`, error);
        
        // Update retry count and status
        await this.handleEventFailure(outboxEvent, error);
      }
    }
  }

  private async handleEventFailure(
    outboxEvent: OutboxEvent, 
    error: Error
  ): Promise<void> {
    const maxRetries = 5;
    const newRetryCount = outboxEvent.retryCount + 1;

    if (newRetryCount >= maxRetries) {
      await this.updateEventStatus(
        outboxEvent.id,
        OutboxEventStatus.FAILED,
        undefined,
        newRetryCount,
        error.message
      );
    } else {
      await this.updateEventStatus(
        outboxEvent.id,
        OutboxEventStatus.PENDING,
        undefined,
        newRetryCount,
        error.message
      );
    }
  }

  private async saveToDatabase(outboxEvent: OutboxEvent): Promise<void> {
    // Implementation would save to database
    // This is a placeholder for the actual database operation
    console.log('Saving outbox event:', outboxEvent);
  }

  private async getPendingEvents(): Promise<OutboxEvent[]> {
    // Implementation would query database for pending events
    // This is a placeholder
    return [];
  }

  private async updateEventStatus(
    eventId: string,
    status: OutboxEventStatus,
    processedAt?: Date,
    retryCount?: number,
    lastError?: string
  ): Promise<void> {
    // Implementation would update database
    console.log('Updating event status:', { eventId, status, processedAt });
  }
}
```

---

## 🔄 **4. Patterns Implementation**

### **Transactional Outbox Pattern**
```typescript
// src/patterns/transactional-outbox.ts
import { Injectable } from '@nestjs/common';
import { DomainEvent } from '../types';
import { OutboxService } from '../services/outbox.service';

export interface TransactionalOperation<T> {
  execute(): Promise<T>;
  getEvents(): DomainEvent[];
}

@Injectable()
export class TransactionalOutbox {
  constructor(private outboxService: OutboxService) {}

  async executeWithEvents<T>(
    aggregateId: string,
    operation: TransactionalOperation<T>,
    exchange: string = 'domain.events'
  ): Promise<T> {
    // Start transaction (in real implementation)
    try {
      // Execute business operation
      const result = await operation.execute();
      
      // Save events to outbox table in same transaction
      const events = operation.getEvents();
      for (const event of events) {
        await this.outboxService.saveEvent(
          aggregateId,
          event,
          this.generateRoutingKey(event),
          exchange
        );
      }
      
      // Commit transaction
      return result;
      
    } catch (error) {
      // Rollback transaction
      throw error;
    }
  }

  private generateRoutingKey(event: DomainEvent): string {
    return `${event.aggregateType.toLowerCase()}.${event.eventType.toLowerCase()}`;
  }
}

// Usage example:
// const operation: TransactionalOperation<Order> = {
//   async execute(): Promise<Order> {
//     const order = await this.orderRepository.save(orderData);
//     this.events.push(new OrderCreatedEvent(order.id, order.customerId));
//     return order;
//   },
//   getEvents(): DomainEvent[] {
//     return this.events;
//   }
// };
// 
// const order = await this.transactionalOutbox.executeWithEvents(
//   orderId,
//   operation
// );
```

### **Saga Manager**
```typescript
// src/patterns/saga-manager.ts
import { Injectable } from '@nestjs/common';
import { ModuleRef } from '@nestjs/core';
import { 
  SagaState, 
  SagaStatus, 
  DomainEvent 
} from '../types';

@Injectable()
export class SagaManager {
  private sagas: Map<string, SagaState> = new Map();

  constructor(private moduleRef: ModuleRef) {}

  async startSaga(
    sagaType: string,
    sagaId: string,
    initialData: Record<string, any>,
    triggerEvent: DomainEvent
  ): Promise<void> {
    const sagaState: SagaState = {
      sagaId,
      sagaType,
      currentStep: 'started',
      data: { ...initialData, triggerEvent },
      status: SagaStatus.STARTED,
      startedAt: new Date()
    };

    this.sagas.set(sagaId, sagaState);
    await this.saveSagaState(sagaState);

    // Start first step
    await this.executeNextStep(sagaId);
  }

  async handleSagaEvent(sagaId: string, event: DomainEvent): Promise<void> {
    const sagaState = this.sagas.get(sagaId);
    if (!sagaState) {
      console.warn(`Saga ${sagaId} not found`);
      return;
    }

    // Update saga data with event
    sagaState.data = { ...sagaState.data, [event.eventType]: event };
    await this.saveSagaState(sagaState);

    // Execute next step
    await this.executeNextStep(sagaId);
  }

  private async executeNextStep(sagaId: string): Promise<void> {
    const sagaState = this.sagas.get(sagaId);
    if (!sagaState) return;

    try {
      // Get saga handler
      const sagaHandler = await this.getSagaHandler(sagaState.sagaType);
      
      // Execute step
      const result = await sagaHandler.executeStep(
        sagaState.currentStep,
        sagaState.data
      );

      if (result.completed) {
        // Saga completed successfully
        sagaState.status = SagaStatus.COMPLETED;
        sagaState.completedAt = new Date();
      } else if (result.failed) {
        // Start compensation
        await this.startCompensation(sagaId, result.error);
      } else {
        // Move to next step
        sagaState.currentStep = result.nextStep;
      }

      await this.saveSagaState(sagaState);

    } catch (error) {
      console.error(`Saga step execution failed for ${sagaId}:`, error);
      await this.startCompensation(sagaId, error);
    }
  }

  private async startCompensation(sagaId: string, error: any): Promise<void> {
    const sagaState = this.sagas.get(sagaId);
    if (!sagaState) return;

    sagaState.status = SagaStatus.COMPENSATING;
    await this.saveSagaState(sagaState);

    try {
      const sagaHandler = await this.getSagaHandler(sagaState.sagaType);
      await sagaHandler.compensate(sagaState.data);

      sagaState.status = SagaStatus.COMPENSATED;
      sagaState.compensated = true;
      
    } catch (compensationError) {
      console.error(`Saga compensation failed for ${sagaId}:`, compensationError);
      sagaState.status = SagaStatus.FAILED;
    }

    sagaState.completedAt = new Date();
    await this.saveSagaState(sagaState);
  }

  private async getSagaHandler(sagaType: string): Promise<any> {
    // In real implementation, this would resolve the saga handler
    // based on the saga type using dependency injection
    return this.moduleRef.get(`${sagaType}Handler`);
  }

  private async saveSagaState(sagaState: SagaState): Promise<void> {
    // In real implementation, save to database
    console.log('Saving saga state:', sagaState);
  }
}
```

---

## 📤 **5. Main Export File**

```typescript
// src/index.ts
// Types
export * from './types';

// Decorators
export * from './decorators';

// Services
export * from './services';

// Patterns
export * from './patterns';

// Config
export * from './config';

// Main module
export { RabbitMQEventModule } from './rabbitmq-event.module';
```

### **RabbitMQ Event Module**
```typescript
// src/rabbitmq-event.module.ts
import { Global, Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ScheduleModule } from '@nestjs/schedule';

import { EventPublisherService } from './services/event-publisher.service';
import { EventSubscriberService } from './services/event-subscriber.service';
import { OutboxService } from './services/outbox.service';
import { TransactionalOutbox } from './patterns/transactional-outbox';
import { SagaManager } from './patterns/saga-manager';

@Global()
@Module({
  imports: [
    ConfigModule,
    ScheduleModule.forRoot()
  ],
  providers: [
    EventPublisherService,
    EventSubscriberService,
    OutboxService,
    TransactionalOutbox,
    SagaManager
  ],
  exports: [
    EventPublisherService,
    EventSubscriberService,
    OutboxService,
    TransactionalOutbox,
    SagaManager
  ]
})
export class RabbitMQEventModule {}
```

---

## 🧪 **Testing Example**

```typescript
// tests/event-publisher.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { ConfigModule } from '@nestjs/config';
import { EventPublisherService } from '../src/services/event-publisher.service';

describe('EventPublisherService', () => {
  let service: EventPublisherService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({
          isGlobal: true,
          envFilePath: '.env.test'
        })
      ],
      providers: [EventPublisherService]
    }).compile();

    service = module.get<EventPublisherService>(EventPublisherService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  // Additional tests would go here
});
```

---

## ✅ **Validation Steps**

1. **Build the package**: `npm run build`
2. **Run tests**: `npm run test`
3. **Test with local RabbitMQ** instance
4. **Verify event publishing** and subscribing works

---

## 🔗 **Next Step**

Once complete, move to [Testing Utils Implementation](./04-testing-utils-implementation.md) to build testing utilities.

This event-driven messaging library provides the foundation for reliable microservices communication! 🚀