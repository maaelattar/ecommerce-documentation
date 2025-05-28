# Event Producers and Publishers

## Overview

Build robust event producers with reliability patterns including transactional outbox, retry mechanisms, dead letter queues, and performance monitoring for reliable message publishing.

## 🎯 Learning Objectives

- Create transactional outbox pattern implementation
- Build event producers with retry and DLQ support
- Implement batch publishing for performance
- Add message acknowledgment patterns
- Create exchange and queue management utilities

---

## Step 1: Transactional Outbox Implementation

### 1.1 Create Outbox Event Entity

```typescript
// src/producers/outbox.entity.ts
export interface OutboxEvent {
  id: string;
  eventType: string;
  aggregateId: string;
  aggregateType: string;
  eventData: any;
  routingKey: string;
  exchange: string;
  status: OutboxStatus;
  createdAt: Date;
  updatedAt: Date;
  publishedAt?: Date;
  retryCount: number;
  maxRetries: number;
  nextRetryAt?: Date;
  lastError?: string;
  correlationId?: string;
  metadata?: Record<string, any>;
}

export enum OutboxStatus {
  PENDING = 'pending',
  PUBLISHED = 'published',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export class OutboxEventBuilder {
  private event: Partial<OutboxEvent> = {
    retryCount: 0,
    maxRetries: 3,
    status: OutboxStatus.PENDING,
    createdAt: new Date(),
    updatedAt: new Date()
  };

  withId(id: string): this {
    this.event.id = id;
    return this;
  }

  withEventType(eventType: string): this {
    this.event.eventType = eventType;
    return this;
  }

  withAggregate(aggregateId: string, aggregateType: string): this {
    this.event.aggregateId = aggregateId;
    this.event.aggregateType = aggregateType;
    return this;
  }

  withData(data: any): this {
    this.event.eventData = data;
    return this;
  }

  withRouting(routingKey: string, exchange: string): this {
    this.event.routingKey = routingKey;
    this.event.exchange = exchange;
    return this;
  }

  withCorrelation(correlationId: string): this {
    this.event.correlationId = correlationId;
    return this;
  }

  withMetadata(metadata: Record<string, any>): this {
    this.event.metadata = metadata;
    return this;
  }

  withRetryConfig(maxRetries: number): this {
    this.event.maxRetries = maxRetries;
    return this;
  }

  build(): OutboxEvent {
    if (!this.event.id) this.event.id = require('uuid').v4();
    if (!this.event.eventType) throw new Error('Event type is required');
    if (!this.event.aggregateId) throw new Error('Aggregate ID is required');
    if (!this.event.aggregateType) throw new Error('Aggregate type is required');
    if (!this.event.routingKey) throw new Error('Routing key is required');
    if (!this.event.exchange) throw new Error('Exchange is required');

    return this.event as OutboxEvent;
  }
}
```

### 1.2 Create Outbox Repository Interface

```typescript
// src/producers/outbox.repository.ts
import { OutboxEvent, OutboxStatus } from './outbox.entity';

export interface OutboxRepository {
  save(event: OutboxEvent): Promise<OutboxEvent>;
  saveMany(events: OutboxEvent[]): Promise<OutboxEvent[]>;
  findById(id: string): Promise<OutboxEvent | null>;
  findPendingEvents(limit?: number): Promise<OutboxEvent[]>;
  findRetryableEvents(limit?: number): Promise<OutboxEvent[]>;
  updateStatus(id: string, status: OutboxStatus, publishedAt?: Date, error?: string): Promise<void>;
  incrementRetryCount(id: string, nextRetryAt?: Date, error?: string): Promise<void>;
  deletePublishedEvents(olderThan: Date): Promise<number>;
  getStatistics(): Promise<{
    pending: number;
    published: number;
    failed: number;
    totalRetries: number;
  }>;
}

// Example implementation for TypeORM (you can implement for your chosen ORM)
export class TypeORMOutboxRepository implements OutboxRepository {
  constructor(private repository: any) {} // TypeORM repository

  async save(event: OutboxEvent): Promise<OutboxEvent> {
    return this.repository.save(event);
  }

  async saveMany(events: OutboxEvent[]): Promise<OutboxEvent[]> {
    return this.repository.save(events);
  }

  async findById(id: string): Promise<OutboxEvent | null> {
    return this.repository.findOne({ where: { id } });
  }

  async findPendingEvents(limit: number = 100): Promise<OutboxEvent[]> {
    return this.repository.find({
      where: { status: OutboxStatus.PENDING },
      order: { createdAt: 'ASC' },
      take: limit
    });
  }

  async findRetryableEvents(limit: number = 100): Promise<OutboxEvent[]> {
    return this.repository.find({
      where: {
        status: OutboxStatus.FAILED,
        nextRetryAt: { $lte: new Date() },
        retryCount: { $lt: this.maxRetries }
      },
      order: { nextRetryAt: 'ASC' },
      take: limit
    });
  }

  async updateStatus(id: string, status: OutboxStatus, publishedAt?: Date, error?: string): Promise<void> {
    const updateData: any = { 
      status, 
      updatedAt: new Date() 
    };
    
    if (publishedAt) updateData.publishedAt = publishedAt;
    if (error) updateData.lastError = error;

    await this.repository.update(id, updateData);
  }

  async incrementRetryCount(id: string, nextRetryAt?: Date, error?: string): Promise<void> {
    await this.repository.increment({ id }, 'retryCount', 1);
    
    const updateData: any = { 
      updatedAt: new Date(),
      status: OutboxStatus.FAILED
    };
    
    if (nextRetryAt) updateData.nextRetryAt = nextRetryAt;
    if (error) updateData.lastError = error;

    await this.repository.update(id, updateData);
  }

  async deletePublishedEvents(olderThan: Date): Promise<number> {
    const result = await this.repository.delete({
      status: OutboxStatus.PUBLISHED,
      publishedAt: { $lt: olderThan }
    });
    return result.affected || 0;
  }

  async getStatistics(): Promise<any> {
    const pending = await this.repository.count({ where: { status: OutboxStatus.PENDING } });
    const published = await this.repository.count({ where: { status: OutboxStatus.PUBLISHED } });
    const failed = await this.repository.count({ where: { status: OutboxStatus.FAILED } });
    const totalRetries = await this.repository.sum('retryCount');

    return { pending, published, failed, totalRetries };
  }
}
```

---

## Step 2: Create Event Producer

### 2.1 Build Core Event Producer

```typescript
// src/producers/event.producer.ts
import { Injectable, Logger } from '@nestjs/common';
import { ConnectionManager } from '../connection/connection.manager';
import { MessageEnvelope } from '../envelope/message.envelope';
import { OutboxRepository, OutboxEvent, OutboxStatus, OutboxEventBuilder } from './outbox.entity';

export interface PublishOptions {
  persistent?: boolean;
  mandatory?: boolean;
  immediate?: boolean;
  expiration?: string;
  userId?: string;
  CC?: string | string[];
  BCC?: string | string[];
  priority?: number;
  correlationId?: string;
  replyTo?: string;
  messageId?: string;
  timestamp?: number;
  type?: string;
  appId?: string;
  headers?: Record<string, any>;
}

export interface BatchPublishOptions extends PublishOptions {
  batchSize?: number;
  flushInterval?: number;
  maxWaitTime?: number;
}

@Injectable()
export class EventProducer {
  private readonly logger = new Logger(EventProducer.name);
  private batchQueue: MessageEnvelope[] = [];
  private batchTimer: NodeJS.Timeout | null = null;

  constructor(
    private connectionManager: ConnectionManager,
    private outboxRepository?: OutboxRepository
  ) {}

  async publish<T>(envelope: MessageEnvelope<T>, options: PublishOptions = {}): Promise<void> {
    if (this.outboxRepository) {
      await this.publishWithOutbox(envelope, options);
    } else {
      await this.publishDirect(envelope, options);
    }
  }

  async publishBatch<T>(envelopes: MessageEnvelope<T>[], options: BatchPublishOptions = {}): Promise<void> {
    const { batchSize = 100 } = options;
    
    for (let i = 0; i < envelopes.length; i += batchSize) {
      const batch = envelopes.slice(i, i + batchSize);
      await Promise.all(batch.map(envelope => this.publish(envelope, options)));
    }
  }

  async publishWithBuffer<T>(envelope: MessageEnvelope<T>, options: BatchPublishOptions = {}): Promise<void> {
    this.batchQueue.push(envelope);

    const { 
      batchSize = 10, 
      flushInterval = 1000, 
      maxWaitTime = 5000 
    } = options;

    // Auto-flush if batch size reached
    if (this.batchQueue.length >= batchSize) {
      await this.flushBatch(options);
      return;
    }

    // Schedule flush if not already scheduled
    if (!this.batchTimer) {
      this.batchTimer = setTimeout(async () => {
        await this.flushBatch(options);
      }, flushInterval);
    }

    // Force flush after max wait time
    setTimeout(async () => {
      if (this.batchQueue.length > 0) {
        await this.flushBatch(options);
      }
    }, maxWaitTime);
  }

  async flushBatch(options: PublishOptions = {}): Promise<void> {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    if (this.batchQueue.length === 0) {
      return;
    }

    const batch = [...this.batchQueue];
    this.batchQueue = [];

    this.logger.debug(`Flushing batch of ${batch.length} messages`);

    try {
      await this.publishBatch(batch, options);
    } catch (error) {
      this.logger.error('Failed to flush batch', error);
      // Re-queue failed messages
      this.batchQueue.unshift(...batch);
      throw error;
    }
  }

  private async publishWithOutbox<T>(envelope: MessageEnvelope<T>, options: PublishOptions): Promise<void> {
    // First, save to outbox
    const outboxEvent = new OutboxEventBuilder()
      .withEventType(envelope.message.eventType)
      .withAggregate(envelope.message.aggregateId, envelope.message.aggregateType)
      .withData(envelope.message.data)
      .withRouting(envelope.routingKey, envelope.exchange)
      .withCorrelation(envelope.message.metadata?.correlationId)
      .withMetadata(envelope.message.metadata)
      .build();

    const savedEvent = await this.outboxRepository!.save(outboxEvent);

    // Then try to publish
    try {
      await this.publishDirect(envelope, options);
      
      // Mark as published on success
      await this.outboxRepository!.updateStatus(
        savedEvent.id, 
        OutboxStatus.PUBLISHED, 
        new Date()
      );

    } catch (error) {
      this.logger.error('Failed to publish message, will retry later', error);
      
      // Calculate next retry time with exponential backoff
      const nextRetryAt = new Date(Date.now() + Math.pow(2, savedEvent.retryCount) * 1000);
      
      await this.outboxRepository!.incrementRetryCount(
        savedEvent.id, 
        nextRetryAt, 
        error.message
      );
      
      throw error;
    }
  }

  private async publishDirect<T>(envelope: MessageEnvelope<T>, options: PublishOptions): Promise<void> {
    const channel = await this.connectionManager.getChannel();

    try {
      // Ensure exchange exists
      await this.ensureExchange(envelope.exchange);

      const publishOptions = {
        persistent: options.persistent ?? true,
        mandatory: options.mandatory ?? false,
        immediate: options.immediate ?? false,
        ...options,
        headers: {
          ...envelope.headers,
          ...options.headers
        }
      };

      const messageBuffer = envelope.toBuffer();
      
      const result = channel.publish(
        envelope.exchange,
        envelope.routingKey,
        messageBuffer,
        publishOptions
      );

      if (!result) {
        throw new Error('Failed to publish message - channel buffer full');
      }

      this.logger.debug(`Published message ${envelope.message.eventId} to ${envelope.exchange}/${envelope.routingKey}`);

    } catch (error) {
      this.logger.error('Failed to publish message', error);
      throw error;
    }
  }

  private async ensureExchange(exchangeName: string): Promise<void> {
    const channel = await this.connectionManager.getChannel();
    
    try {
      await channel.assertExchange(exchangeName, 'topic', {
        durable: true,
        autoDelete: false
      });
    } catch (error) {
      this.logger.error(`Failed to assert exchange ${exchangeName}`, error);
      throw error;
    }
  }
}
```

### 2.2 Create Outbox Processor

```typescript
// src/producers/outbox.processor.ts
import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { EventProducer } from './event.producer';
import { OutboxRepository, OutboxStatus } from './outbox.entity';
import { MessageEnvelope } from '../envelope/message.envelope';

@Injectable()
export class OutboxProcessor {
  private readonly logger = new Logger(OutboxProcessor.name);
  private isProcessing = false;

  constructor(
    private eventProducer: EventProducer,
    private outboxRepository: OutboxRepository
  ) {}

  @Cron(CronExpression.EVERY_10_SECONDS)
  async processPendingEvents(): Promise<void> {
    if (this.isProcessing) {
      return;
    }

    this.isProcessing = true;

    try {
      const pendingEvents = await this.outboxRepository.findPendingEvents(50);
      
      if (pendingEvents.length > 0) {
        this.logger.debug(`Processing ${pendingEvents.length} pending events`);
        
        for (const event of pendingEvents) {
          await this.processEvent(event);
        }
      }

      // Also process retryable events
      const retryableEvents = await this.outboxRepository.findRetryableEvents(20);
      
      if (retryableEvents.length > 0) {
        this.logger.debug(`Processing ${retryableEvents.length} retryable events`);
        
        for (const event of retryableEvents) {
          await this.processEvent(event);
        }
      }

    } catch (error) {
      this.logger.error('Error processing outbox events', error);
    } finally {
      this.isProcessing = false;
    }
  }

  @Cron(CronExpression.EVERY_HOUR)
  async cleanupPublishedEvents(): Promise<void> {
    try {
      const olderThan = new Date(Date.now() - 24 * 60 * 60 * 1000); // 24 hours ago
      const deleted = await this.outboxRepository.deletePublishedEvents(olderThan);
      
      if (deleted > 0) {
        this.logger.log(`Cleaned up ${deleted} published events`);
      }
    } catch (error) {
      this.logger.error('Error cleaning up published events', error);
    }
  }

  async processEvent(outboxEvent: any): Promise<void> {
    try {
      const envelope = await MessageEnvelope.create(
        outboxEvent.eventType,
        'outbox-processor',
        outboxEvent.aggregateId,
        outboxEvent.aggregateType,
        outboxEvent.eventData,
        outboxEvent.routingKey,
        outboxEvent.exchange,
        outboxEvent.metadata
      );

      // Publish directly (bypass outbox to avoid recursion)
      await (this.eventProducer as any).publishDirect(envelope, {});

      // Mark as published
      await this.outboxRepository.updateStatus(
        outboxEvent.id,
        OutboxStatus.PUBLISHED,
        new Date()
      );

      this.logger.debug(`Successfully published outbox event ${outboxEvent.id}`);

    } catch (error) {
      this.logger.error(`Failed to publish outbox event ${outboxEvent.id}`, error);

      // Check if we should retry
      if (outboxEvent.retryCount < outboxEvent.maxRetries) {
        const nextRetryAt = new Date(Date.now() + Math.pow(2, outboxEvent.retryCount) * 1000);
        
        await this.outboxRepository.incrementRetryCount(
          outboxEvent.id,
          nextRetryAt,
          error.message
        );
      } else {
        // Max retries reached, mark as failed
        await this.outboxRepository.updateStatus(
          outboxEvent.id,
          OutboxStatus.FAILED,
          undefined,
          `Max retries reached: ${error.message}`
        );
      }
    }
  }

  async getStatistics(): Promise<any> {
    return this.outboxRepository.getStatistics();
  }
}
```

---

## Step 3: Exchange and Queue Management

### 3.1 Create Exchange Manager

```typescript
// src/producers/exchange.manager.ts
import { Injectable, Logger } from '@nestjs/common';
import { ConnectionManager } from '../connection/connection.manager';

export interface ExchangeConfig {
  name: string;
  type: 'direct' | 'topic' | 'fanout' | 'headers';
  durable?: boolean;
  autoDelete?: boolean;
  internal?: boolean;
  alternateExchange?: string;
  arguments?: Record<string, any>;
}

export interface QueueConfig {
  name: string;
  durable?: boolean;
  exclusive?: boolean;
  autoDelete?: boolean;
  arguments?: Record<string, any>;
}

export interface BindingConfig {
  queue: string;
  exchange: string;
  routingKey?: string;
  arguments?: Record<string, any>;
}

@Injectable()
export class ExchangeManager {
  private readonly logger = new Logger(ExchangeManager.name);

  constructor(private connectionManager: ConnectionManager) {}

  async declareExchange(config: ExchangeConfig): Promise<void> {
    const channel = await this.connectionManager.getChannel();

    try {
      await channel.assertExchange(config.name, config.type, {
        durable: config.durable ?? true,
        autoDelete: config.autoDelete ?? false,
        internal: config.internal ?? false,
        alternateExchange: config.alternateExchange,
        arguments: config.arguments
      });

      this.logger.log(`Declared exchange: ${config.name} (${config.type})`);
    } catch (error) {
      this.logger.error(`Failed to declare exchange ${config.name}`, error);
      throw error;
    }
  }

  async declareQueue(config: QueueConfig): Promise<void> {
    const channel = await this.connectionManager.getChannel();

    try {
      await channel.assertQueue(config.name, {
        durable: config.durable ?? true,
        exclusive: config.exclusive ?? false,
        autoDelete: config.autoDelete ?? false,
        arguments: config.arguments
      });

      this.logger.log(`Declared queue: ${config.name}`);
    } catch (error) {
      this.logger.error(`Failed to declare queue ${config.name}`, error);
      throw error;
    }
  }

  async bindQueue(config: BindingConfig): Promise<void> {
    const channel = await this.connectionManager.getChannel();

    try {
      await channel.bindQueue(
        config.queue,
        config.exchange,
        config.routingKey || '',
        config.arguments
      );

      this.logger.log(`Bound queue ${config.queue} to exchange ${config.exchange} with key ${config.routingKey}`);
    } catch (error) {
      this.logger.error(`Failed to bind queue ${config.queue} to exchange ${config.exchange}`, error);
      throw error;
    }
  }

  async setupDeadLetterQueue(originalQueue: string, exchange: string): Promise<void> {
    const dlqName = `${originalQueue}.dlq`;
    const dlxName = `${exchange}.dlx`;

    // Declare DLX (Dead Letter Exchange)
    await this.declareExchange({
      name: dlxName,
      type: 'direct',
      durable: true
    });

    // Declare DLQ (Dead Letter Queue)
    await this.declareQueue({
      name: dlqName,
      durable: true
    });

    // Bind DLQ to DLX
    await this.bindQueue({
      queue: dlqName,
      exchange: dlxName,
      routingKey: originalQueue
    });

    this.logger.log(`Setup dead letter queue for ${originalQueue}`);
  }

  async deleteExchange(name: string, ifUnused: boolean = false): Promise<void> {
    const channel = await this.connectionManager.getChannel();

    try {
      await channel.deleteExchange(name, { ifUnused });
      this.logger.log(`Deleted exchange: ${name}`);
    } catch (error) {
      this.logger.error(`Failed to delete exchange ${name}`, error);
      throw error;
    }
  }

  async deleteQueue(name: string, ifUnused: boolean = false, ifEmpty: boolean = false): Promise<void> {
    const channel = await this.connectionManager.getChannel();

    try {
      await channel.deleteQueue(name, { ifUnused, ifEmpty });
      this.logger.log(`Deleted queue: ${name}`);
    } catch (error) {
      this.logger.error(`Failed to delete queue ${name}`, error);
      throw error;
    }
  }

  async purgeQueue(name: string): Promise<number> {
    const channel = await this.connectionManager.getChannel();

    try {
      const result = await channel.purgeQueue(name);
      this.logger.log(`Purged ${result.messageCount} messages from queue ${name}`);
      return result.messageCount;
    } catch (error) {
      this.logger.error(`Failed to purge queue ${name}`, error);
      throw error;
    }
  }
}
```

---

## Step 4: Create Tests

### 4.1 Test Event Producer

```typescript
// src/producers/event.producer.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { EventProducer } from './event.producer';
import { ConnectionManager } from '../connection/connection.manager';
import { MessageEnvelope } from '../envelope/message.envelope';

describe('EventProducer', () => {
  let producer: EventProducer;
  let connectionManager: ConnectionManager;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EventProducer,
        {
          provide: ConnectionManager,
          useValue: {
            getChannel: jest.fn().mockResolvedValue({
              assertExchange: jest.fn(),
              publish: jest.fn().mockReturnValue(true)
            })
          }
        }
      ]
    }).compile();

    producer = module.get<EventProducer>(EventProducer);
    connectionManager = module.get<ConnectionManager>(ConnectionManager);
  });

  it('should be defined', () => {
    expect(producer).toBeDefined();
  });

  it('should publish message successfully', async () => {
    const envelope = await MessageEnvelope.create(
      'test.event',
      'test-service',
      'test-123',
      'Test',
      { message: 'test data' },
      'test.event',
      'test.exchange'
    );

    await expect(producer.publish(envelope)).resolves.not.toThrow();
  });

  it('should handle publish failures', async () => {
    const mockChannel = {
      assertExchange: jest.fn(),
      publish: jest.fn().mockReturnValue(false)
    };

    (connectionManager.getChannel as jest.Mock).mockResolvedValue(mockChannel);

    const envelope = await MessageEnvelope.create(
      'test.event',
      'test-service',
      'test-123',
      'Test',
      { message: 'test data' },
      'test.event',
      'test.exchange'
    );

    await expect(producer.publish(envelope)).rejects.toThrow('Failed to publish message - channel buffer full');
  });
});
```

---

## Step 5: Export Components

```typescript
// src/producers/index.ts
export * from './outbox.entity';
export * from './outbox.repository';
export * from './event.producer';
export * from './outbox.processor';
export * from './exchange.manager';
```

---

## Step 6: Update Main Export

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
```

---

## 🎯 Key Accomplishments

✅ **Transactional outbox pattern** for reliable message publishing  
✅ **Event producer** with retry mechanisms and DLQ support  
✅ **Batch publishing** for improved performance  
✅ **Exchange and queue management** utilities  
✅ **Automatic retry** with exponential backoff  
✅ **Dead letter queue setup** for failed messages  

---

## 🔗 Next Steps

Continue with **[03-consumers-and-handlers.md](./03-consumers-and-handlers.md)** to build event consumers and message handling patterns.

---

## 💡 Usage Preview

```typescript
import { EventProducer, MessageEnvelope } from '@ecommerce/rabbitmq-event-utils';

@Injectable()
export class UserService {
  constructor(private eventProducer: EventProducer) {}

  async createUser(userData: any) {
    // Business logic...
    
    // Publish event with outbox pattern
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