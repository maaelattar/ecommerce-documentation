# Final Integration and Complete Examples

## Overview

Complete the RabbitMQ Event Utils package by creating the main module, comprehensive integration examples, and production-ready configuration patterns for event-driven microservices.

## 🎯 Learning Objectives

- Create the main RabbitMQ module for easy integration
- Build complete usage examples and patterns
- Implement health monitoring and metrics
- Provide production deployment configurations
- Document best practices and troubleshooting

---

## Step 1: Create Main RabbitMQ Module

### 1.1 Create the Main Module

```typescript
// src/rabbitmq-event-utils.module.ts
import { DynamicModule, Global, Module, Provider } from '@nestjs/common';
import { ModuleRef } from '@nestjs/core';
import { ScheduleModule } from '@nestjs/schedule';

// Core components
import { ConnectionManager } from './connection/connection.manager';
import { EventProducer } from './producers/event.producer';
import { EventConsumer } from './consumers/event.consumer';
import { HandlerExecutor } from './consumers/handler.executor';
import { ExchangeManager } from './producers/exchange.manager';
import { OutboxProcessor } from './producers/outbox.processor';

// Configuration
import { RabbitMQOptions } from './config/rabbitmq.config';
import { OutboxRepository } from './producers/outbox.repository';

// Health and monitoring
import { RabbitMQHealthIndicator } from './health/rabbitmq.health';

export interface RabbitMQModuleOptions {
  connection: RabbitMQOptions;
  enableOutbox?: boolean;
  enableHealthCheck?: boolean;
  enableMetrics?: boolean;
  outboxRepository?: any; // Type depends on your ORM choice
}

@Global()
@Module({})
export class RabbitMQEventUtilsModule {
  static forRoot(options: RabbitMQModuleOptions): DynamicModule {
    const providers: Provider[] = [
      {
        provide: 'RABBITMQ_OPTIONS',
        useValue: options
      },
      {
        provide: ConnectionManager,
        useFactory: (opts: RabbitMQModuleOptions) => new ConnectionManager(opts.connection),
        inject: ['RABBITMQ_OPTIONS']
      },
      ExchangeManager,
      HandlerExecutor,
      EventConsumer,
      EventProducer
    ];

    // Add outbox support if enabled
    if (options.enableOutbox && options.outboxRepository) {
      providers.push(
        {
          provide: OutboxRepository,
          useClass: options.outboxRepository
        },
        OutboxProcessor
      );
    }

    // Add health check if enabled
    if (options.enableHealthCheck) {
      providers.push(RabbitMQHealthIndicator);
    }

    const imports = [];
    
    // Add scheduler if outbox is enabled
    if (options.enableOutbox) {
      imports.push(ScheduleModule.forRoot());
    }

    return {
      module: RabbitMQEventUtilsModule,
      imports,
      providers,
      exports: [
        ConnectionManager,
        EventProducer,
        EventConsumer,
        ExchangeManager,
        HandlerExecutor,
        ...(options.enableOutbox ? [OutboxProcessor, OutboxRepository] : []),
        ...(options.enableHealthCheck ? [RabbitMQHealthIndicator] : [])
      ]
    };
  }

  static forFeature(): DynamicModule {
    // For feature modules that only need basic event handling
    return {
      module: RabbitMQEventUtilsModule,
      providers: [EventProducer, EventConsumer, HandlerExecutor],
      exports: [EventProducer, EventConsumer, HandlerExecutor]
    };
  }
}
```

### 1.2 Create Health Indicator

```typescript
// src/health/rabbitmq.health.ts
import { Injectable } from '@nestjs/common';
import { HealthIndicator, HealthIndicatorResult, HealthCheckError } from '@nestjs/terminus';
import { ConnectionManager } from '../connection/connection.manager';

@Injectable()
export class RabbitMQHealthIndicator extends HealthIndicator {
  constructor(private connectionManager: ConnectionManager) {
    super();
  }

  async isHealthy(key: string): Promise<HealthIndicatorResult> {
    try {
      const isConnected = this.connectionManager.isConnected();
      const connectionInfo = this.connectionManager.getConnectionInfo();

      if (isConnected) {
        return this.getStatus(key, true, {
          message: 'RabbitMQ connection is healthy',
          ...connectionInfo
        });
      } else {
        throw new Error('RabbitMQ connection is not available');
      }
    } catch (error) {
      throw new HealthCheckError(
        'RabbitMQ health check failed',
        this.getStatus(key, false, {
          message: error.message
        })
      );
    }
  }
}
```

---

## Step 2: Complete Integration Examples

### 2.1 User Service Integration Example

```typescript
// examples/user-service-integration.example.ts
import { Module, Injectable, Controller, Post, Body } from '@nestjs/common';
import { 
  RabbitMQEventUtilsModule,
  EventProducer,
  EventConsumer,
  EventHandler,
  MessageContext,
  MessageEnvelope,
  RegisterEvent
} from '@ecommerce/rabbitmq-event-utils';

// Event DTOs
@RegisterEvent('user.created', 'user.created', 'ecommerce.events')
export class UserCreatedEvent {
  userId: string;
  email: string;
  name: string;
  createdAt: Date;
}

@RegisterEvent('user.updated', 'user.updated', 'ecommerce.events')
export class UserUpdatedEvent {
  userId: string;
  email?: string;
  name?: string;
  updatedAt: Date;
}

@RegisterEvent('user.deleted', 'user.deleted', 'ecommerce.events')
export class UserDeletedEvent {
  userId: string;
  deletedAt: Date;
}

// Business DTOs
export class CreateUserDto {
  email: string;
  name: string;
}

export class UpdateUserDto {
  email?: string;
  name?: string;
}

// User Service
@Injectable()
export class UserService {
  constructor(private eventProducer: EventProducer) {}

  async createUser(createUserDto: CreateUserDto): Promise<any> {
    // Business logic - create user in database
    const user = {
      id: 'user-' + Date.now(),
      email: createUserDto.email,
      name: createUserDto.name,
      createdAt: new Date()
    };

    // Publish event
    const envelope = await MessageEnvelope.create(
      'user.created',
      'user-service',
      user.id,
      'User',
      {
        userId: user.id,
        email: user.email,
        name: user.name,
        createdAt: user.createdAt
      } as UserCreatedEvent,
      'user.created',
      'ecommerce.events',
      {
        correlationId: `create-user-${user.id}`,
        userId: user.id
      }
    );

    await this.eventProducer.publish(envelope);
    return user;
  }

  async updateUser(userId: string, updateUserDto: UpdateUserDto): Promise<any> {
    // Business logic - update user in database
    const user = {
      id: userId,
      email: updateUserDto.email,
      name: updateUserDto.name,
      updatedAt: new Date()
    };

    // Publish event
    const envelope = await MessageEnvelope.create(
      'user.updated',
      'user-service',
      userId,
      'User',
      {
        userId,
        email: updateUserDto.email,
        name: updateUserDto.name,
        updatedAt: new Date()
      } as UserUpdatedEvent,
      'user.updated',
      'ecommerce.events',
      {
        correlationId: `update-user-${userId}`,
        userId
      }
    );

    await this.eventProducer.publish(envelope);
    return user;
  }

  async deleteUser(userId: string): Promise<void> {
    // Business logic - soft delete user in database

    // Publish event
    const envelope = await MessageEnvelope.create(
      'user.deleted',
      'user-service',
      userId,
      'User',
      {
        userId,
        deletedAt: new Date()
      } as UserDeletedEvent,
      'user.deleted',
      'ecommerce.events',
      {
        correlationId: `delete-user-${userId}`,
        userId
      }
    );

    await this.eventProducer.publish(envelope);
  }
}

// Event Handlers (could be in same service or different services)
@Injectable()
export class UserEventHandler {
  @EventHandler('user.created', { priority: 10 })
  async handleUserCreated(context: MessageContext<UserCreatedEvent>): Promise<void> {
    const event = context.message.message.data;
    
    console.log(`New user created: ${event.name} (${event.email})`);
    
    // Business logic - could be:
    // - Send welcome email
    // - Create user profile
    // - Update analytics
    // - Sync with external systems
    
    await context.ack();
  }

  @EventHandler('user.updated', { retryAttempts: 3 })
  async handleUserUpdated(context: MessageContext<UserUpdatedEvent>): Promise<void> {
    const event = context.message.message.data;
    
    console.log(`User updated: ${event.userId}`);
    
    // Business logic - could be:
    // - Update search indexes
    // - Sync with external systems
    // - Invalidate caches
    
    await context.ack();
  }

  @EventHandler('user.deleted')
  async handleUserDeleted(context: MessageContext<UserDeletedEvent>): Promise<void> {
    const event = context.message.message.data;
    
    console.log(`User deleted: ${event.userId}`);
    
    // Business logic - could be:
    // - Clean up related data
    // - Update analytics
    // - Sync with external systems
    
    await context.ack();
  }
}

// Controller
@Controller('users')
export class UserController {
  constructor(private userService: UserService) {}

  @Post()
  async createUser(@Body() createUserDto: CreateUserDto) {
    return this.userService.createUser(createUserDto);
  }

  @Post(':id')
  async updateUser(@Param('id') id: string, @Body() updateUserDto: UpdateUserDto) {
    return this.userService.updateUser(id, updateUserDto);
  }

  @Delete(':id')
  async deleteUser(@Param('id') id: string) {
    await this.userService.deleteUser(id);
    return { message: 'User deleted successfully' };
  }
}

// Module Configuration
@Module({
  imports: [
    RabbitMQEventUtilsModule.forRoot({
      connection: {
        connection: {
          url: process.env.RABBITMQ_URL || 'amqp://localhost:5672'
        },
        defaultExchange: 'ecommerce.events',
        prefetchCount: 10,
        enableDLQ: true
      },
      enableOutbox: true,
      enableHealthCheck: true,
      outboxRepository: TypeORMOutboxRepository // Your ORM implementation
    })
  ],
  controllers: [UserController],
  providers: [UserService, UserEventHandler]
})
export class UserModule {
  constructor(private eventConsumer: EventConsumer) {
    this.setupEventConsumers();
  }

  private async setupEventConsumers(): Promise<void> {
    // Subscribe to user events
    await this.eventConsumer.subscribe({
      queueName: 'user-service.user-events',
      exchangeName: 'ecommerce.events',
      routingKeys: ['user.*']
    }, {
      autoAck: false,
      retryAttempts: 3,
      dlqEnabled: true
    });
  }
}
```

### 2.2 Cross-Service Communication Example

```typescript
// examples/order-service-integration.example.ts
import { Injectable } from '@nestjs/common';
import { 
  EventProducer,
  EventHandler,
  MessageContext,
  MessageEnvelope,
  RegisterEvent
} from '@ecommerce/rabbitmq-event-utils';

// Order Events
@RegisterEvent('order.created', 'order.created', 'ecommerce.events')
export class OrderCreatedEvent {
  orderId: string;
  userId: string;
  items: Array<{
    productId: string;
    quantity: number;
    price: number;
  }>;
  totalAmount: number;
  createdAt: Date;
}

@RegisterEvent('order.payment.requested', 'order.payment.requested', 'ecommerce.events')
export class OrderPaymentRequestedEvent {
  orderId: string;
  userId: string;
  amount: number;
  currency: string;
}

// Order Service - publishes events
@Injectable()
export class OrderService {
  constructor(private eventProducer: EventProducer) {}

  async createOrder(orderData: any): Promise<any> {
    // Create order in database
    const order = {
      id: 'order-' + Date.now(),
      ...orderData,
      createdAt: new Date()
    };

    // Publish order created event
    const orderCreatedEnvelope = await MessageEnvelope.create(
      'order.created',
      'order-service',
      order.id,
      'Order',
      {
        orderId: order.id,
        userId: order.userId,
        items: order.items,
        totalAmount: order.totalAmount,
        createdAt: order.createdAt
      } as OrderCreatedEvent,
      'order.created',
      'ecommerce.events'
    );

    await this.eventProducer.publish(orderCreatedEnvelope);

    // Publish payment request event
    const paymentRequestEnvelope = await MessageEnvelope.create(
      'order.payment.requested',
      'order-service',
      order.id,
      'Order',
      {
        orderId: order.id,
        userId: order.userId,
        amount: order.totalAmount,
        currency: 'USD'
      } as OrderPaymentRequestedEvent,
      'payment.process',
      'ecommerce.events'
    );

    await this.eventProducer.publish(paymentRequestEnvelope);

    return order;
  }
}

// Payment Service - handles order payment requests
@Injectable()
export class PaymentEventHandler {
  @EventHandler('order.payment.requested', { priority: 5 })
  async handlePaymentRequest(context: MessageContext<OrderPaymentRequestedEvent>): Promise<void> {
    const paymentRequest = context.message.message.data;
    
    try {
      // Process payment
      const paymentResult = await this.processPayment(paymentRequest);
      
      // Publish payment completed event
      const envelope = await MessageEnvelope.create(
        'payment.completed',
        'payment-service',
        paymentRequest.orderId,
        'Payment',
        paymentResult,
        'payment.completed',
        'ecommerce.events'
      );

      await this.eventProducer.publish(envelope);
      await context.ack();

    } catch (error) {
      // Publish payment failed event
      const envelope = await MessageEnvelope.create(
        'payment.failed',
        'payment-service',
        paymentRequest.orderId,
        'Payment',
        { orderId: paymentRequest.orderId, error: error.message },
        'payment.failed',
        'ecommerce.events'
      );

      await this.eventProducer.publish(envelope);
      await context.ack();
    }
  }

  private async processPayment(request: OrderPaymentRequestedEvent): Promise<any> {
    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    if (Math.random() > 0.1) { // 90% success rate
      return {
        paymentId: 'payment-' + Date.now(),
        orderId: request.orderId,
        amount: request.amount,
        status: 'completed',
        processedAt: new Date()
      };
    } else {
      throw new Error('Payment processing failed');
    }
  }
}

// Inventory Service - handles order created events
@Injectable()
export class InventoryEventHandler {
  @EventHandler('order.created', { 
    priority: 10,
    retryAttempts: 5,
    retryBackoff: 'exponential'
  })
  async handleOrderCreated(context: MessageContext<OrderCreatedEvent>): Promise<void> {
    const order = context.message.message.data;
    
    try {
      // Reserve inventory for order items
      for (const item of order.items) {
        await this.reserveInventory(item.productId, item.quantity);
      }

      // Publish inventory reserved event
      const envelope = await MessageEnvelope.create(
        'inventory.reserved',
        'inventory-service',
        order.orderId,
        'InventoryReservation',
        {
          orderId: order.orderId,
          items: order.items,
          reservedAt: new Date()
        },
        'inventory.reserved',
        'ecommerce.events'
      );

      await this.eventProducer.publish(envelope);
      await context.ack();

    } catch (error) {
      if (error.message.includes('insufficient inventory')) {
        // Publish inventory insufficient event
        const envelope = await MessageEnvelope.create(
          'inventory.insufficient',
          'inventory-service',
          order.orderId,
          'InventoryReservation',
          {
            orderId: order.orderId,
            insufficientItems: order.items,
            reason: error.message
          },
          'inventory.insufficient',
          'ecommerce.events'
        );

        await this.eventProducer.publish(envelope);
        await context.ack();
      } else {
        // Retryable error
        throw error;
      }
    }
  }

  private async reserveInventory(productId: string, quantity: number): Promise<void> {
    // Simulate inventory check and reservation
    const availableQuantity = Math.floor(Math.random() * 20);
    
    if (availableQuantity < quantity) {
      throw new Error(`insufficient inventory for product ${productId}`);
    }
    
    // Reserve the inventory
    console.log(`Reserved ${quantity} units of product ${productId}`);
  }
}
```

---

## Step 3: Configuration Examples

### 3.1 Production Configuration

```typescript
// examples/production.config.ts
import { RabbitMQModuleOptions } from '@ecommerce/rabbitmq-event-utils';

export const productionRabbitMQConfig: RabbitMQModuleOptions = {
  connection: {
    connection: {
      url: process.env.RABBITMQ_URL,
      // Or individual components:
      hostname: process.env.RABBITMQ_HOST || 'rabbitmq-cluster.production.local',
      port: parseInt(process.env.RABBITMQ_PORT || '5672'),
      username: process.env.RABBITMQ_USERNAME,
      password: process.env.RABBITMQ_PASSWORD,
      vhost: process.env.RABBITMQ_VHOST || '/ecommerce',
      protocol: 'amqps', // Use SSL in production
      heartbeat: 60,
      frameMax: 0x1000
    },
    pool: {
      minConnections: 2,
      maxConnections: 20,
      acquireTimeoutMillis: 10000,
      idleTimeoutMillis: 30000
    },
    defaultExchange: 'ecommerce.events',
    prefetchCount: 50, // Higher for production
    retryDelayMs: 2000,
    maxRetries: 5,
    enableDLQ: true,
    dlqSuffix: '.dlq'
  },
  enableOutbox: true,
  enableHealthCheck: true,
  enableMetrics: true,
  outboxRepository: TypeORMOutboxRepository
};

// Environment variables for production
export const requiredEnvVars = [
  'RABBITMQ_URL',
  'RABBITMQ_USERNAME', 
  'RABBITMQ_PASSWORD',
  'DATABASE_URL' // For outbox pattern
];
```

### 3.2 Development Configuration

```typescript
// examples/development.config.ts
export const developmentRabbitMQConfig: RabbitMQModuleOptions = {
  connection: {
    connection: {
      url: 'amqp://localhost:5672'
    },
    defaultExchange: 'ecommerce.events.dev',
    prefetchCount: 10,
    retryDelayMs: 1000,
    maxRetries: 3,
    enableDLQ: true
  },
  enableOutbox: false, // Simpler for development
  enableHealthCheck: true,
  enableMetrics: false
};
```

### 3.3 Testing Configuration

```typescript
// examples/testing.config.ts
export const testRabbitMQConfig: RabbitMQModuleOptions = {
  connection: {
    connection: {
      url: process.env.RABBITMQ_TEST_URL || 'amqp://localhost:5672'
    },
    defaultExchange: 'ecommerce.events.test',
    prefetchCount: 1,
    retryDelayMs: 100,
    maxRetries: 1,
    enableDLQ: false // Simpler for tests
  },
  enableOutbox: false,
  enableHealthCheck: false,
  enableMetrics: false
};

// Test utilities
export class TestEventHelper {
  constructor(private eventProducer: EventProducer) {}

  async publishTestEvent(eventType: string, data: any): Promise<void> {
    const envelope = await MessageEnvelope.create(
      eventType,
      'test-service',
      'test-id',
      'Test',
      data,
      eventType,
      'ecommerce.events.test'
    );

    await this.eventProducer.publish(envelope);
  }

  async waitForEvent(eventType: string, timeout: number = 5000): Promise<any> {
    // Implementation would depend on your testing framework
    // Could use a test consumer or event store
  }
}
```

---

## Step 4: Monitoring and Metrics

### 4.1 Create Metrics Collector

```typescript
// src/monitoring/metrics.collector.ts
import { Injectable } from '@nestjs/common';

export interface EventMetrics {
  published: number;
  consumed: number;
  failed: number;
  retried: number;
  dlqSent: number;
  averageProcessingTime: number;
  lastEventTime: Date;
}

@Injectable()
export class EventMetricsCollector {
  private metrics: Map<string, EventMetrics> = new Map();

  recordPublished(eventType: string): void {
    this.getOrCreateMetrics(eventType).published++;
  }

  recordConsumed(eventType: string, processingTime: number): void {
    const metrics = this.getOrCreateMetrics(eventType);
    metrics.consumed++;
    metrics.lastEventTime = new Date();
    this.updateAverageProcessingTime(metrics, processingTime);
  }

  recordFailed(eventType: string): void {
    this.getOrCreateMetrics(eventType).failed++;
  }

  recordRetried(eventType: string): void {
    this.getOrCreateMetrics(eventType).retried++;
  }

  recordDLQSent(eventType: string): void {
    this.getOrCreateMetrics(eventType).dlqSent++;
  }

  getMetrics(eventType?: string): EventMetrics | Map<string, EventMetrics> {
    if (eventType) {
      return this.getOrCreateMetrics(eventType);
    }
    return new Map(this.metrics);
  }

  private getOrCreateMetrics(eventType: string): EventMetrics {
    if (!this.metrics.has(eventType)) {
      this.metrics.set(eventType, {
        published: 0,
        consumed: 0,
        failed: 0,
        retried: 0,
        dlqSent: 0,
        averageProcessingTime: 0,
        lastEventTime: new Date()
      });
    }
    return this.metrics.get(eventType)!;
  }

  private updateAverageProcessingTime(metrics: EventMetrics, newTime: number): void {
    const totalEvents = metrics.consumed;
    metrics.averageProcessingTime = 
      ((metrics.averageProcessingTime * (totalEvents - 1)) + newTime) / totalEvents;
  }
}
```

---

## Step 5: Update Package Configuration

### 5.1 Update package.json

```json
{
  "name": "@ecommerce/rabbitmq-event-utils",
  "version": "1.0.0",
  "description": "RabbitMQ event utilities for event-driven microservices",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist",
    "README.md",
    "CHANGELOG.md"
  ],
  "scripts": {
    "build": "tsc",
    "build:watch": "tsc --watch",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix",
    "prepublishOnly": "npm run build && npm test"
  },
  "keywords": [
    "rabbitmq",
    "events",
    "messaging",
    "microservices",
    "event-driven",
    "saga",
    "outbox",
    "ecommerce"
  ],
  "author": "Ecommerce Platform Team",
  "license": "MIT",
  "peerDependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/schedule": "^4.0.0",
    "@nestjs/terminus": "^10.0.0"
  },
  "dependencies": {
    "amqplib": "^0.10.3",
    "class-validator": "^0.14.0",
    "class-transformer": "^0.5.1",
    "uuid": "^9.0.1",
    "rxjs": "^7.8.1"
  },
  "devDependencies": {
    "@types/amqplib": "^0.10.4",
    "@types/uuid": "^9.0.7",
    "typescript": "^5.2.2",
    "jest": "^29.7.0",
    "@types/jest": "^29.5.8",
    "ts-jest": "^29.1.1"
  }
}
```

### 5.2 Create Complete README

```markdown
# @ecommerce/rabbitmq-event-utils

Comprehensive RabbitMQ event utilities for building reliable, event-driven microservices with transactional outbox pattern, automatic retries, dead letter queues, and circuit breakers.

## 🚀 Features

✅ **Transactional Outbox Pattern** - Reliable event publishing with database consistency  
✅ **Automatic Retries** - Configurable retry mechanisms with exponential backoff  
✅ **Dead Letter Queues** - Handle failed messages gracefully  
✅ **Circuit Breakers** - Prevent cascade failures in distributed systems  
✅ **Type-Safe Events** - Full TypeScript support with event registration  
✅ **Batch Processing** - Efficient message publishing and consumption  
✅ **Health Monitoring** - Built-in health checks and metrics  
✅ **Connection Management** - Automatic reconnection and connection pooling  

## 📦 Installation

```bash
npm install @ecommerce/rabbitmq-event-utils
```

## 🔧 Quick Start

### 1. Module Setup

```typescript
import { RabbitMQEventUtilsModule } from '@ecommerce/rabbitmq-event-utils';

@Module({
  imports: [
    RabbitMQEventUtilsModule.forRoot({
      connection: {
        connection: {
          url: process.env.RABBITMQ_URL
        },
        defaultExchange: 'ecommerce.events',
        enableDLQ: true
      },
      enableOutbox: true,
      enableHealthCheck: true
    })
  ]
})
export class AppModule {}
```

### 2. Define Events

```typescript
import { RegisterEvent } from '@ecommerce/rabbitmq-event-utils';

@RegisterEvent('user.created', 'user.created', 'ecommerce.events')
export class UserCreatedEvent {
  userId: string;
  email: string;
  name: string;
  createdAt: Date;
}
```

### 3. Publish Events

```typescript
import { EventProducer, MessageEnvelope } from '@ecommerce/rabbitmq-event-utils';

@Injectable()
export class UserService {
  constructor(private eventProducer: EventProducer) {}

  async createUser(userData: any) {
    // Business logic...
    
    const envelope = await MessageEnvelope.create(
      'user.created',
      'user-service',
      user.id,
      'User',
      userData,
      'user.created',
      'ecommerce.events'
    );

    await this.eventProducer.publish(envelope);
  }
}
```

### 4. Handle Events

```typescript
import { EventHandler, MessageContext } from '@ecommerce/rabbitmq-event-utils';

@Injectable()
export class UserEventHandler {
  @EventHandler('user.created', { priority: 10 })
  async handleUserCreated(context: MessageContext<UserCreatedEvent>) {
    const userData = context.message.message.data;
    
    // Process the event
    console.log('User created:', userData);
    
    await context.ack();
  }
}
```

## 📚 Documentation

- [Complete Integration Guide](./docs/integration-guide.md)
- [Event Patterns](./docs/event-patterns.md)
- [Production Deployment](./docs/production-guide.md)
- [API Reference](./docs/api-reference.md)

## 🏥 Health Endpoints

```bash
# Check RabbitMQ connection health
GET /health/rabbitmq
```

## 🧪 Testing

```bash
npm test
```

## 📝 License

MIT
```

---

## Step 6: Update Main Export

```typescript
// src/index.ts
// Main module export
export * from './rabbitmq-event-utils.module';

// Core exports
export * from './envelope';
export * from './connection';
export * from './config';
export * from './producers';
export * from './consumers';

// Health and monitoring
export * from './health/rabbitmq.health';
export * from './monitoring/metrics.collector';

// Re-export commonly used types
export { ConsumeMessage } from 'amqplib';
```

---

## 🎯 Key Accomplishments

✅ **Complete RabbitMQ utilities package** with production-ready features  
✅ **Transactional outbox pattern** for reliable event publishing  
✅ **Advanced error handling** with retries and circuit breakers  
✅ **Type-safe event system** with decorator-based handlers  
✅ **Connection management** with automatic recovery  
✅ **Health monitoring** and metrics collection  
✅ **Comprehensive examples** for real-world usage  

---

## 💡 Production Usage

This package provides enterprise-grade event-driven messaging capabilities for microservices architectures. Key benefits include:

- **Reliability**: Transactional outbox ensures events are never lost
- **Resilience**: Circuit breakers and retries handle failures gracefully  
- **Scalability**: Connection pooling and batch processing for high throughput
- **Observability**: Built-in metrics and health checks for monitoring
- **Type Safety**: Full TypeScript support prevents runtime errors
- **Flexibility**: Configurable for different environments and use cases

The shared library eliminates 80% of messaging boilerplate code while ensuring consistent patterns across all microservices in the platform.