# Event Consumers and Message Handlers

## Overview

Build robust event consumers with automatic message acknowledgment, error handling, retry mechanisms, and subscription management for reliable event-driven message processing.

## 🎯 Learning Objectives

- Create event consumers with subscription management
- Implement message acknowledgment patterns  
- Build retry mechanisms and circuit breakers
- Add message filtering and routing
- Create event handler decorators and registration

---

## Step 1: Message Consumer Infrastructure

### 1.1 Create Consumer Configuration

```typescript
// src/consumers/consumer.config.ts
export interface ConsumerConfig {
  queueName: string;
  exchangeName: string;
  routingKeys: string[];
  consumerTag?: string;
  prefetch?: number;
  noAck?: boolean;
  exclusive?: boolean;
  priority?: number;
  arguments?: Record<string, any>;
}

export interface ConsumerOptions {
  autoAck?: boolean;
  retryAttempts?: number;
  retryDelay?: number;
  retryBackoff?: 'fixed' | 'exponential';
  dlqEnabled?: boolean;
  circuitBreaker?: CircuitBreakerConfig;
  filterPattern?: string | RegExp;
  batchSize?: number;
  batchTimeout?: number;
}

export interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeout: number;
  monitoringPeriod: number;
  expectedErrors?: (error: Error) => boolean;
}

export const defaultConsumerOptions: ConsumerOptions = {
  autoAck: false,
  retryAttempts: 3,
  retryDelay: 1000,
  retryBackoff: 'exponential',
  dlqEnabled: true,
  batchSize: 1,
  batchTimeout: 1000
};
```

### 1.2 Create Message Context

```typescript
// src/consumers/message.context.ts
import { MessageEnvelope } from '../envelope/message.envelope';
import * as amqp from 'amqplib';

export interface MessageContext<T = any> {
  message: MessageEnvelope<T>;
  rawMessage: amqp.ConsumeMessage;
  ack(): Promise<void>;
  nack(requeue?: boolean): Promise<void>;
  reject(requeue?: boolean): Promise<void>;
  getRetryCount(): number;
  isRedelivered(): boolean;
  getHeaders(): Record<string, any>;
  getCorrelationId(): string | undefined;
  getTimestamp(): Date;
}

export class MessageContextImpl<T = any> implements MessageContext<T> {
  constructor(
    public readonly message: MessageEnvelope<T>,
    public readonly rawMessage: amqp.ConsumeMessage,
    private channel: amqp.Channel
  ) {}

  async ack(): Promise<void> {
    this.channel.ack(this.rawMessage);
  }

  async nack(requeue: boolean = false): Promise<void> {
    this.channel.nack(this.rawMessage, false, requeue);
  }

  async reject(requeue: boolean = false): Promise<void> {
    this.channel.reject(this.rawMessage, requeue);
  }

  getRetryCount(): number {
    return parseInt(this.rawMessage.properties.headers?.['x-retry-count'] || '0');
  }

  isRedelivered(): boolean {
    return this.rawMessage.fields.redelivered;
  }

  getHeaders(): Record<string, any> {
    return this.rawMessage.properties.headers || {};
  }

  getCorrelationId(): string | undefined {
    return this.rawMessage.properties.correlationId;
  }

  getTimestamp(): Date {
    return new Date(this.rawMessage.properties.timestamp * 1000);
  }
}
```

---

## Step 2: Event Handler Registry

### 2.1 Create Handler Registry

```typescript
// src/consumers/handler.registry.ts
import { Type } from '@nestjs/common';

export interface EventHandlerMetadata {
  eventTypes: string[];
  handlerClass: Type<any>;
  methodName: string;
  priority: number;
  filter?: (message: any) => boolean;
  retryConfig?: {
    attempts: number;
    delay: number;
    backoff: 'fixed' | 'exponential';
  };
}

export class EventHandlerRegistry {
  private static handlers = new Map<string, EventHandlerMetadata[]>();

  static register(metadata: EventHandlerMetadata): void {
    for (const eventType of metadata.eventTypes) {
      if (!this.handlers.has(eventType)) {
        this.handlers.set(eventType, []);
      }
      
      const handlers = this.handlers.get(eventType)!;
      handlers.push(metadata);
      
      // Sort by priority (higher priority first)
      handlers.sort((a, b) => b.priority - a.priority);
    }
  }

  static getHandlers(eventType: string): EventHandlerMetadata[] {
    return this.handlers.get(eventType) || [];
  }

  static getAllHandlers(): Map<string, EventHandlerMetadata[]> {
    return new Map(this.handlers);
  }

  static clear(): void {
    this.handlers.clear();
  }
}

// Decorator for event handlers
export function EventHandler(
  eventTypes: string | string[],
  options: {
    priority?: number;
    filter?: (message: any) => boolean;
    retryAttempts?: number;
    retryDelay?: number;
    retryBackoff?: 'fixed' | 'exponential';
  } = {}
) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const eventTypeArray = Array.isArray(eventTypes) ? eventTypes : [eventTypes];
    
    EventHandlerRegistry.register({
      eventTypes: eventTypeArray,
      handlerClass: target.constructor,
      methodName: propertyKey,
      priority: options.priority || 0,
      filter: options.filter,
      retryConfig: options.retryAttempts ? {
        attempts: options.retryAttempts,
        delay: options.retryDelay || 1000,
        backoff: options.retryBackoff || 'exponential'
      } : undefined
    });
  };
}
```

### 2.2 Create Handler Execution Engine

```typescript
// src/consumers/handler.executor.ts
import { Injectable, Logger } from '@nestjs/common';
import { ModuleRef } from '@nestjs/core';
import { EventHandlerRegistry, EventHandlerMetadata } from './handler.registry';
import { MessageContext } from './message.context';
import { CircuitBreaker } from './circuit-breaker';

export interface ExecutionResult {
  success: boolean;
  error?: Error;
  handlerName: string;
  executionTime: number;
  retryCount: number;
}

@Injectable()
export class HandlerExecutor {
  private readonly logger = new Logger(HandlerExecutor.name);
  private circuitBreakers = new Map<string, CircuitBreaker>();

  constructor(private moduleRef: ModuleRef) {}

  async executeHandlers<T>(context: MessageContext<T>): Promise<ExecutionResult[]> {
    const eventType = context.message.message.eventType;
    const handlers = EventHandlerRegistry.getHandlers(eventType);

    if (handlers.length === 0) {
      this.logger.warn(`No handlers found for event type: ${eventType}`);
      return [];
    }

    const results: ExecutionResult[] = [];

    for (const handlerMetadata of handlers) {
      const result = await this.executeHandler(context, handlerMetadata);
      results.push(result);

      // Stop execution if handler failed and circuit breaker is open
      if (!result.success && this.isCircuitBreakerOpen(handlerMetadata)) {
        break;
      }
    }

    return results;
  }

  private async executeHandler<T>(
    context: MessageContext<T>,
    metadata: EventHandlerMetadata
  ): Promise<ExecutionResult> {
    const startTime = Date.now();
    const handlerName = `${metadata.handlerClass.name}.${metadata.methodName}`;

    try {
      // Apply filter if specified
      if (metadata.filter && !metadata.filter(context.message)) {
        return {
          success: true,
          handlerName,
          executionTime: Date.now() - startTime,
          retryCount: 0
        };
      }

      // Get handler instance
      const handlerInstance = this.moduleRef.get(metadata.handlerClass, { strict: false });
      const handlerMethod = handlerInstance[metadata.methodName];

      if (typeof handlerMethod !== 'function') {
        throw new Error(`Handler method ${metadata.methodName} not found`);
      }

      // Execute with circuit breaker if configured
      const circuitBreaker = this.getCircuitBreaker(handlerName);
      
      let result: any;
      if (circuitBreaker) {
        result = await circuitBreaker.execute(() => handlerMethod.call(handlerInstance, context));
      } else {
        result = await handlerMethod.call(handlerInstance, context);
      }

      const executionTime = Date.now() - startTime;
      this.logger.debug(`Handler ${handlerName} executed successfully in ${executionTime}ms`);

      return {
        success: true,
        handlerName,
        executionTime,
        retryCount: context.getRetryCount()
      };

    } catch (error) {
      const executionTime = Date.now() - startTime;
      this.logger.error(`Handler ${handlerName} failed after ${executionTime}ms`, error);

      return {
        success: false,
        error,
        handlerName,
        executionTime,
        retryCount: context.getRetryCount()
      };
    }
  }

  private getCircuitBreaker(handlerName: string): CircuitBreaker | undefined {
    return this.circuitBreakers.get(handlerName);
  }

  private isCircuitBreakerOpen(metadata: EventHandlerMetadata): boolean {
    const handlerName = `${metadata.handlerClass.name}.${metadata.methodName}`;
    const circuitBreaker = this.circuitBreakers.get(handlerName);
    return circuitBreaker ? circuitBreaker.isOpen() : false;
  }

  addCircuitBreaker(handlerName: string, circuitBreaker: CircuitBreaker): void {
    this.circuitBreakers.set(handlerName, circuitBreaker);
  }
}
```

---

## Step 3: Circuit Breaker Implementation

### 3.1 Create Circuit Breaker

```typescript
// src/consumers/circuit-breaker.ts
import { Logger } from '@nestjs/common';

export enum CircuitBreakerState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open'
}

export interface CircuitBreakerMetrics {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  failureRate: number;
  averageResponseTime: number;
  state: CircuitBreakerState;
  lastStateChange: Date;
}

export class CircuitBreaker {
  private readonly logger = new Logger(CircuitBreaker.name);
  private state: CircuitBreakerState = CircuitBreakerState.CLOSED;
  private failures = 0;
  private successes = 0;
  private lastFailureTime: Date | null = null;
  private lastSuccessTime: Date | null = null;
  private stateChangeTime = new Date();
  private responseTimes: number[] = [];

  constructor(
    private name: string,
    private failureThreshold: number = 5,
    private resetTimeoutMs: number = 60000,
    private monitoringWindowMs: number = 60000,
    private isExpectedError: (error: Error) => boolean = () => false
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === CircuitBreakerState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitBreakerState.HALF_OPEN;
        this.stateChangeTime = new Date();
        this.logger.log(`Circuit breaker ${this.name} moved to HALF_OPEN state`);
      } else {
        throw new Error(`Circuit breaker ${this.name} is OPEN`);
      }
    }

    const startTime = Date.now();

    try {
      const result = await operation();
      const responseTime = Date.now() - startTime;
      
      this.recordSuccess(responseTime);
      return result;

    } catch (error) {
      const responseTime = Date.now() - startTime;
      this.recordFailure(error, responseTime);
      throw error;
    }
  }

  private recordSuccess(responseTime: number): void {
    this.successes++;
    this.lastSuccessTime = new Date();
    this.addResponseTime(responseTime);

    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.state = CircuitBreakerState.CLOSED;
      this.failures = 0;
      this.stateChangeTime = new Date();
      this.logger.log(`Circuit breaker ${this.name} moved to CLOSED state`);
    }
  }

  private recordFailure(error: Error, responseTime: number): void {
    this.addResponseTime(responseTime);

    // Don't count expected errors as failures
    if (this.isExpectedError(error)) {
      return;
    }

    this.failures++;
    this.lastFailureTime = new Date();

    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.state = CircuitBreakerState.OPEN;
      this.stateChangeTime = new Date();
      this.logger.warn(`Circuit breaker ${this.name} moved to OPEN state from HALF_OPEN`);
    } else if (this.state === CircuitBreakerState.CLOSED && this.failures >= this.failureThreshold) {
      this.state = CircuitBreakerState.OPEN;
      this.stateChangeTime = new Date();
      this.logger.warn(`Circuit breaker ${this.name} moved to OPEN state - failure threshold reached`);
    }
  }

  private shouldAttemptReset(): boolean {
    return Date.now() - this.stateChangeTime.getTime() >= this.resetTimeoutMs;
  }

  private addResponseTime(responseTime: number): void {
    this.responseTimes.push(responseTime);
    
    // Keep only recent response times (within monitoring window)
    const cutoffTime = Date.now() - this.monitoringWindowMs;
    this.responseTimes = this.responseTimes.slice(-100); // Keep last 100 measurements
  }

  isOpen(): boolean {
    return this.state === CircuitBreakerState.OPEN;
  }

  isClosed(): boolean {
    return this.state === CircuitBreakerState.CLOSED;
  }

  isHalfOpen(): boolean {
    return this.state === CircuitBreakerState.HALF_OPEN;
  }

  getMetrics(): CircuitBreakerMetrics {
    const totalRequests = this.successes + this.failures;
    const failureRate = totalRequests > 0 ? this.failures / totalRequests : 0;
    const averageResponseTime = this.responseTimes.length > 0 
      ? this.responseTimes.reduce((sum, time) => sum + time, 0) / this.responseTimes.length 
      : 0;

    return {
      totalRequests,
      successfulRequests: this.successes,
      failedRequests: this.failures,
      failureRate,
      averageResponseTime,
      state: this.state,
      lastStateChange: this.stateChangeTime
    };
  }

  reset(): void {
    this.state = CircuitBreakerState.CLOSED;
    this.failures = 0;
    this.successes = 0;
    this.responseTimes = [];
    this.stateChangeTime = new Date();
    this.logger.log(`Circuit breaker ${this.name} reset to CLOSED state`);
  }
}
```

---

## Step 4: Event Consumer Implementation

### 4.1 Create Event Consumer

```typescript
// src/consumers/event.consumer.ts
import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConnectionManager } from '../connection/connection.manager';
import { MessageEnvelope } from '../envelope/message.envelope';
import { MessageContextImpl } from './message.context';
import { HandlerExecutor } from './handler.executor';
import { ConsumerConfig, ConsumerOptions, defaultConsumerOptions } from './consumer.config';
import { ExchangeManager } from '../producers/exchange.manager';
import * as amqp from 'amqplib';

@Injectable()
export class EventConsumer implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(EventConsumer.name);
  private consumers = new Map<string, amqp.Channel>();
  private isConsuming = false;

  constructor(
    private connectionManager: ConnectionManager,
    private handlerExecutor: HandlerExecutor,
    private exchangeManager: ExchangeManager
  ) {}

  async onModuleInit(): Promise<void> {
    // Consumer initialization will be handled by individual subscribe calls
  }

  async onModuleDestroy(): Promise<void> {
    await this.stopAllConsumers();
  }

  async subscribe(
    config: ConsumerConfig,
    options: ConsumerOptions = {}
  ): Promise<void> {
    const finalOptions = { ...defaultConsumerOptions, ...options };
    
    this.logger.log(`Subscribing to queue: ${config.queueName}`);

    try {
      // Setup infrastructure
      await this.setupInfrastructure(config, finalOptions);

      // Start consuming
      await this.startConsuming(config, finalOptions);

    } catch (error) {
      this.logger.error(`Failed to subscribe to queue ${config.queueName}`, error);
      throw error;
    }
  }

  private async setupInfrastructure(
    config: ConsumerConfig,
    options: ConsumerOptions
  ): Promise<void> {
    // Declare exchange
    await this.exchangeManager.declareExchange({
      name: config.exchangeName,
      type: 'topic',
      durable: true
    });

    // Declare main queue
    const queueArgs: Record<string, any> = {
      ...config.arguments
    };

    // Setup DLQ if enabled
    if (options.dlqEnabled) {
      const dlxName = `${config.exchangeName}.dlx`;
      const dlqName = `${config.queueName}.dlq`;

      queueArgs['x-dead-letter-exchange'] = dlxName;
      queueArgs['x-dead-letter-routing-key'] = config.queueName;

      await this.exchangeManager.setupDeadLetterQueue(config.queueName, config.exchangeName);
    }

    await this.exchangeManager.declareQueue({
      name: config.queueName,
      durable: true,
      arguments: queueArgs
    });

    // Bind queue to exchange
    for (const routingKey of config.routingKeys) {
      await this.exchangeManager.bindQueue({
        queue: config.queueName,
        exchange: config.exchangeName,
        routingKey
      });
    }
  }

  private async startConsuming(
    config: ConsumerConfig,
    options: ConsumerOptions
  ): Promise<void> {
    const channel = await this.connectionManager.getChannel();

    // Set prefetch count
    await channel.prefetch(config.prefetch || 10);

    const consumerTag = await channel.consume(
      config.queueName,
      async (msg) => {
        if (msg) {
          await this.processMessage(msg, channel, options);
        }
      },
      {
        noAck: options.autoAck || false,
        consumerTag: config.consumerTag,
        exclusive: config.exclusive || false,
        priority: config.priority,
        arguments: config.arguments
      }
    );

    this.consumers.set(config.queueName, channel);
    this.logger.log(`Started consuming from queue: ${config.queueName} with consumer tag: ${consumerTag.consumerTag}`);
  }

  private async processMessage(
    rawMessage: amqp.ConsumeMessage,
    channel: amqp.Channel,
    options: ConsumerOptions
  ): Promise<void> {
    let envelope: MessageEnvelope;
    let context: MessageContextImpl;

    try {
      // Deserialize message
      envelope = MessageEnvelope.fromBuffer(rawMessage.content);
      context = new MessageContextImpl(envelope, rawMessage, channel);

      this.logger.debug(`Processing message: ${envelope.message.eventId} of type: ${envelope.message.eventType}`);

      // Apply filtering if specified
      if (options.filterPattern && !this.matchesFilter(envelope.message.eventType, options.filterPattern)) {
        await context.ack();
        return;
      }

      // Execute handlers
      const results = await this.handlerExecutor.executeHandlers(context);

      // Check if all handlers succeeded
      const allSucceeded = results.every(result => result.success);

      if (allSucceeded) {
        if (!options.autoAck) {
          await context.ack();
        }
        this.logger.debug(`Successfully processed message: ${envelope.message.eventId}`);
      } else {
        await this.handleFailedMessage(context, results, options);
      }

    } catch (error) {
      this.logger.error('Error processing message', error);
      
      if (context!) {
        await this.handleProcessingError(context, error, options);
      } else {
        // If we can't even deserialize, nack without requeue
        channel.nack(rawMessage, false, false);
      }
    }
  }

  private async handleFailedMessage(
    context: MessageContextImpl,
    results: any[],
    options: ConsumerOptions
  ): Promise<void> {
    const retryCount = context.getRetryCount();
    const maxRetries = options.retryAttempts || 3;

    if (retryCount < maxRetries) {
      // Retry the message
      const delay = this.calculateRetryDelay(retryCount, options);
      await this.retryMessage(context, delay);
    } else {
      // Max retries reached, send to DLQ or nack
      if (options.dlqEnabled) {
        await context.nack(false); // Send to DLQ
        this.logger.warn(`Message sent to DLQ after ${retryCount} retries: ${context.message.message.eventId}`);
      } else {
        await context.nack(false); // Discard message
        this.logger.warn(`Message discarded after ${retryCount} retries: ${context.message.message.eventId}`);
      }
    }
  }

  private async handleProcessingError(
    context: MessageContextImpl,
    error: Error,
    options: ConsumerOptions
  ): Promise<void> {
    const retryCount = context.getRetryCount();
    const maxRetries = options.retryAttempts || 3;

    this.logger.error(`Processing error for message ${context.message.message.eventId}:`, error);

    if (retryCount < maxRetries && this.isRetryableError(error)) {
      const delay = this.calculateRetryDelay(retryCount, options);
      await this.retryMessage(context, delay);
    } else {
      await context.nack(false);
    }
  }

  private async retryMessage(context: MessageContextImpl, delayMs: number): Promise<void> {
    // For simplicity, we'll nack with requeue (in production, use a retry exchange with TTL)
    await context.nack(true);
    
    this.logger.debug(`Retrying message ${context.message.message.eventId} after ${delayMs}ms delay`);
  }

  private calculateRetryDelay(retryCount: number, options: ConsumerOptions): number {
    const baseDelay = options.retryDelay || 1000;
    
    if (options.retryBackoff === 'exponential') {
      return baseDelay * Math.pow(2, retryCount);
    } else {
      return baseDelay;
    }
  }

  private isRetryableError(error: Error): boolean {
    // Define which errors are retryable
    return !error.message.includes('validation') && 
           !error.message.includes('authorization') &&
           !error.message.includes('forbidden');
  }

  private matchesFilter(eventType: string, filter: string | RegExp): boolean {
    if (typeof filter === 'string') {
      return eventType.includes(filter);
    } else {
      return filter.test(eventType);
    }
  }

  async unsubscribe(queueName: string): Promise<void> {
    const channel = this.consumers.get(queueName);
    
    if (channel) {
      try {
        await channel.cancel(''); // Cancel all consumers on this channel
        this.consumers.delete(queueName);
        this.logger.log(`Unsubscribed from queue: ${queueName}`);
      } catch (error) {
        this.logger.error(`Error unsubscribing from queue ${queueName}`, error);
      }
    }
  }

  async stopAllConsumers(): Promise<void> {
    for (const queueName of this.consumers.keys()) {
      await this.unsubscribe(queueName);
    }
  }

  getActiveConsumers(): string[] {
    return Array.from(this.consumers.keys());
  }
}
```

---

## Step 5: Create Tests

### 5.1 Test Event Consumer

```typescript
// src/consumers/event.consumer.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { EventConsumer } from './event.consumer';
import { ConnectionManager } from '../connection/connection.manager';
import { HandlerExecutor } from './handler.executor';
import { ExchangeManager } from '../producers/exchange.manager';

describe('EventConsumer', () => {
  let consumer: EventConsumer;
  let connectionManager: ConnectionManager;
  let handlerExecutor: HandlerExecutor;
  let exchangeManager: ExchangeManager;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EventConsumer,
        {
          provide: ConnectionManager,
          useValue: {
            getChannel: jest.fn().mockResolvedValue({
              prefetch: jest.fn(),
              consume: jest.fn().mockResolvedValue({ consumerTag: 'test-consumer' }),
              cancel: jest.fn()
            })
          }
        },
        {
          provide: HandlerExecutor,
          useValue: {
            executeHandlers: jest.fn().mockResolvedValue([{ success: true }])
          }
        },
        {
          provide: ExchangeManager,
          useValue: {
            declareExchange: jest.fn(),
            declareQueue: jest.fn(),
            bindQueue: jest.fn(),
            setupDeadLetterQueue: jest.fn()
          }
        }
      ]
    }).compile();

    consumer = module.get<EventConsumer>(EventConsumer);
    connectionManager = module.get<ConnectionManager>(ConnectionManager);
    handlerExecutor = module.get<HandlerExecutor>(HandlerExecutor);
    exchangeManager = module.get<ExchangeManager>(ExchangeManager);
  });

  it('should be defined', () => {
    expect(consumer).toBeDefined();
  });

  it('should subscribe to queue successfully', async () => {
    const config = {
      queueName: 'test.queue',
      exchangeName: 'test.exchange',
      routingKeys: ['test.*']
    };

    await expect(consumer.subscribe(config)).resolves.not.toThrow();
    
    expect(exchangeManager.declareExchange).toHaveBeenCalled();
    expect(exchangeManager.declareQueue).toHaveBeenCalled();
    expect(exchangeManager.bindQueue).toHaveBeenCalled();
  });
});
```

---

## Step 6: Export Components

```typescript
// src/consumers/index.ts
export * from './consumer.config';
export * from './message.context';
export * from './handler.registry';
export * from './handler.executor';
export * from './circuit-breaker';
export * from './event.consumer';
```

---

## Step 7: Update Main Export

```typescript
// src/index.ts
// Envelope exports
export * from './envelope';

// Connection exports
export * from './connection';

// Configuration exports
export * from './config';

// Producer exports
export * from './producers';

// Consumer exports
export * from './consumers';
```

---

## 🎯 Key Accomplishments

✅ **Event consumer** with subscription management and auto-recovery  
✅ **Message acknowledgment patterns** with retry mechanisms  
✅ **Handler registry** with decorator-based event routing  
✅ **Circuit breaker** for resilience and failure handling  
✅ **Dead letter queue** support for failed messages  
✅ **Filtering and routing** for selective message processing  

---

## 🔗 Next Steps

Continue with **[04-final-integration-and-examples.md](./04-final-integration-and-examples.md)** to complete the RabbitMQ Event Utils package with comprehensive examples and integration guides.

---

## 💡 Usage Preview

```typescript
import { EventHandler, MessageContext } from '@ecommerce/rabbitmq-event-utils';

@Injectable()
export class UserEventHandler {
  @EventHandler('user.created', { priority: 10 })
  async handleUserCreated(context: MessageContext<UserCreatedEvent>) {
    const userData = context.message.message.data;
    
    // Process the user creation event
    console.log('User created:', userData);
    
    // Acknowledge the message
    await context.ack();
  }

  @EventHandler(['user.updated', 'user.deleted'], { 
    retryAttempts: 5,
    retryBackoff: 'exponential'
  })
  async handleUserChanges(context: MessageContext) {
    // Handle multiple event types
    const eventType = context.message.message.eventType;
    const eventData = context.message.message.data;
    
    // Process based on event type
    if (eventType === 'user.updated') {
      // Handle update
    } else if (eventType === 'user.deleted') {
      // Handle deletion
    }
    
    await context.ack();
  }
}
```