# RabbitMQ Event Utils - Setup and Message Envelope

## Overview

Build the foundational messaging infrastructure with standardized message envelopes, connection management, and type-safe event schemas for reliable event-driven communication.

## 🎯 Learning Objectives

- Set up the RabbitMQ utilities package structure
- Create standardized message envelope schemas
- Implement connection management with resilience
- Build type-safe event definitions
- Add message validation and serialization

---

## Step 1: Initialize the Package

### 1.1 Create Package Structure

```bash
# Create the package directory (if not exists)
mkdir -p shared-libraries/rabbitmq-event-utils
cd shared-libraries/rabbitmq-event-utils

# Initialize npm package
npm init -y
```

### 1.2 Install Dependencies

```bash
# Core dependencies
npm install amqplib @nestjs/common @nestjs/core rxjs

# Event and validation dependencies
npm install class-validator class-transformer uuid

# Development dependencies
npm install -D @types/amqplib @types/uuid typescript jest @types/jest ts-jest
```

### 1.3 Update package.json

```json
{
  "name": "@ecommerce/rabbitmq-event-utils",
  "version": "1.0.0",
  "description": "RabbitMQ event utilities for ecommerce platform",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "test:watch": "jest --watch"
  },
  "keywords": ["rabbitmq", "events", "messaging", "ecommerce"],
  "author": "Ecommerce Platform Team",
  "license": "MIT",
  "peerDependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0"
  }
}
```

### 1.4 Create TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "module": "commonjs",
    "declaration": true,
    "removeComments": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "allowSyntheticDefaultImports": true,
    "target": "ES2021",
    "sourceMap": true,
    "outDir": "./dist",
    "baseUrl": "./",
    "incremental": true,
    "skipLibCheck": true,
    "strictNullChecks": false,
    "noImplicitAny": false,
    "strictBindCallApply": false,
    "forceConsistentCasingInFileNames": false,
    "noFallthroughCasesInSwitch": false
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "test"]
}
```

---

## Step 2: Create Project Structure

```bash
mkdir -p src/{envelope,connection,events,producers,consumers,config,health}
touch src/index.ts
```

Your directory structure should look like:

```
shared-libraries/rabbitmq-event-utils/
├── src/
│   ├── envelope/
│   ├── connection/
│   ├── events/
│   ├── producers/
│   ├── consumers/
│   ├── config/
│   ├── health/
│   └── index.ts
├── package.json
├── tsconfig.json
└── README.md
```

---

## Step 3: Implement Message Envelope

### 3.1 Create Base Message Types

```typescript
// src/envelope/message.types.ts
import { IsString, IsUUID, IsDateString, IsOptional, ValidateNested, IsObject } from 'class-validator';
import { Type, Transform } from 'class-transformer';

export enum MessageStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  RETRY = 'retry'
}

export enum MessagePriority {
  LOW = 1,
  NORMAL = 5,
  HIGH = 8,
  CRITICAL = 10
}

export interface MessageMetadata {
  correlationId?: string;
  causationId?: string;
  userId?: string;
  tenantId?: string;
  sessionId?: string;
  traceId?: string;
  spanId?: string;
  retryCount?: number;
  maxRetries?: number;
  priority?: MessagePriority;
  delayUntil?: Date;
  expiresAt?: Date;
  tags?: string[];
}

export class BaseMessage<T = any> {
  @IsUUID()
  eventId: string;

  @IsString()
  eventType: string;

  @IsString()
  eventVersion: string;

  @IsDateString()
  @Transform(({ value }) => value instanceof Date ? value.toISOString() : value)
  eventTimestamp: string;

  @IsString()
  sourceService: string;

  @IsString()
  aggregateId: string;

  @IsString()
  aggregateType: string;

  @IsOptional()
  @IsObject()
  metadata?: MessageMetadata;

  @ValidateNested()
  @Type(() => Object)
  data: T;

  constructor(
    eventType: string,
    sourceService: string,
    aggregateId: string,
    aggregateType: string,
    data: T,
    metadata?: MessageMetadata
  ) {
    this.eventId = require('uuid').v4();
    this.eventType = eventType;
    this.eventVersion = '1.0.0';
    this.eventTimestamp = new Date().toISOString();
    this.sourceService = sourceService;
    this.aggregateId = aggregateId;
    this.aggregateType = aggregateType;
    this.data = data;
    this.metadata = metadata;
  }
}
```

### 3.2 Create Message Envelope

```typescript
// src/envelope/message.envelope.ts
import { validate } from 'class-validator';
import { plainToClass, Transform } from 'class-transformer';
import { BaseMessage, MessageMetadata } from './message.types';

export class MessageEnvelope<T = any> {
  public readonly message: BaseMessage<T>;
  public readonly routingKey: string;
  public readonly exchange: string;
  public readonly headers: Record<string, any>;

  constructor(
    message: BaseMessage<T>,
    routingKey: string,
    exchange: string,
    headers: Record<string, any> = {}
  ) {
    this.message = message;
    this.routingKey = routingKey;
    this.exchange = exchange;
    this.headers = {
      ...headers,
      messageId: message.eventId,
      messageType: message.eventType,
      timestamp: message.eventTimestamp,
      sourceService: message.sourceService,
      correlationId: message.metadata?.correlationId,
      retryCount: message.metadata?.retryCount || 0
    };
  }

  static async create<T>(
    eventType: string,
    sourceService: string,
    aggregateId: string,
    aggregateType: string,
    data: T,
    routingKey: string,
    exchange: string,
    metadata?: MessageMetadata,
    headers?: Record<string, any>
  ): Promise<MessageEnvelope<T>> {
    const message = new BaseMessage(
      eventType,
      sourceService,
      aggregateId,
      aggregateType,
      data,
      metadata
    );

    // Validate message
    const errors = await validate(message);
    if (errors.length > 0) {
      throw new Error(`Message validation failed: ${JSON.stringify(errors)}`);
    }

    return new MessageEnvelope(message, routingKey, exchange, headers);
  }

  static fromBuffer<T>(buffer: Buffer): MessageEnvelope<T> {
    try {
      const parsed = JSON.parse(buffer.toString());
      return plainToClass(MessageEnvelope, parsed);
    } catch (error) {
      throw new Error(`Failed to deserialize message: ${error.message}`);
    }
  }

  toBuffer(): Buffer {
    return Buffer.from(JSON.stringify(this));
  }

  toJSON(): any {
    return {
      message: this.message,
      routingKey: this.routingKey,
      exchange: this.exchange,
      headers: this.headers
    };
  }

  withCorrelation(correlationId: string): MessageEnvelope<T> {
    const newMetadata = {
      ...this.message.metadata,
      correlationId
    };

    const newMessage = {
      ...this.message,
      metadata: newMetadata
    };

    const newHeaders = {
      ...this.headers,
      correlationId
    };

    return new MessageEnvelope(newMessage as BaseMessage<T>, this.routingKey, this.exchange, newHeaders);
  }

  withRetry(retryCount: number): MessageEnvelope<T> {
    const newMetadata = {
      ...this.message.metadata,
      retryCount
    };

    const newMessage = {
      ...this.message,
      metadata: newMetadata
    };

    const newHeaders = {
      ...this.headers,
      retryCount
    };

    return new MessageEnvelope(newMessage as BaseMessage<T>, this.routingKey, this.exchange, newHeaders);
  }

  withDelay(delayMs: number): MessageEnvelope<T> {
    const delayUntil = new Date(Date.now() + delayMs);
    const newMetadata = {
      ...this.message.metadata,
      delayUntil
    };

    const newMessage = {
      ...this.message,
      metadata: newMetadata
    };

    const newHeaders = {
      ...this.headers,
      'x-delay': delayMs
    };

    return new MessageEnvelope(newMessage as BaseMessage<T>, this.routingKey, this.exchange, newHeaders);
  }
}
```

### 3.3 Create Event Registry

```typescript
// src/envelope/event.registry.ts
import { Type } from '@nestjs/common';

export interface EventDefinition {
  eventType: string;
  eventVersion: string;
  dataSchema: Type<any>;
  routingKey: string;
  exchange: string;
  description?: string;
}

export class EventRegistry {
  private static events = new Map<string, EventDefinition>();

  static register(definition: EventDefinition): void {
    const key = `${definition.eventType}:${definition.eventVersion}`;
    
    if (this.events.has(key)) {
      throw new Error(`Event ${key} is already registered`);
    }

    this.events.set(key, definition);
  }

  static get(eventType: string, version: string = '1.0.0'): EventDefinition | undefined {
    const key = `${eventType}:${version}`;
    return this.events.get(key);
  }

  static getAll(): EventDefinition[] {
    return Array.from(this.events.values());
  }

  static exists(eventType: string, version: string = '1.0.0'): boolean {
    const key = `${eventType}:${version}`;
    return this.events.has(key);
  }

  static getByExchange(exchange: string): EventDefinition[] {
    return Array.from(this.events.values()).filter(event => event.exchange === exchange);
  }

  static clear(): void {
    this.events.clear();
  }
}

// Decorator for registering events
export function RegisterEvent(
  eventType: string,
  routingKey: string,
  exchange: string,
  version: string = '1.0.0',
  description?: string
) {
  return function <T extends Type<any>>(target: T) {
    EventRegistry.register({
      eventType,
      eventVersion: version,
      dataSchema: target,
      routingKey,
      exchange,
      description
    });
    return target;
  };
}
```

---

## Step 4: Connection Management

### 4.1 Create Connection Configuration

```typescript
// src/config/rabbitmq.config.ts
export interface RabbitMQConfig {
  url?: string;
  hostname?: string;
  port?: number;
  username?: string;
  password?: string;
  vhost?: string;
  protocol?: 'amqp' | 'amqps';
  frameMax?: number;
  heartbeat?: number;
  locale?: string;
}

export interface ConnectionPoolConfig {
  minConnections?: number;
  maxConnections?: number;
  acquireTimeoutMillis?: number;
  createTimeoutMillis?: number;
  destroyTimeoutMillis?: number;
  idleTimeoutMillis?: number;
  createRetryIntervalMillis?: number;
}

export interface RabbitMQOptions {
  connection: RabbitMQConfig;
  pool?: ConnectionPoolConfig;
  defaultExchange?: string;
  prefetchCount?: number;
  retryDelayMs?: number;
  maxRetries?: number;
  enableDLQ?: boolean;
  dlqSuffix?: string;
}

export const defaultRabbitMQOptions: Partial<RabbitMQOptions> = {
  pool: {
    minConnections: 1,
    maxConnections: 10,
    acquireTimeoutMillis: 5000,
    createTimeoutMillis: 10000,
    destroyTimeoutMillis: 5000,
    idleTimeoutMillis: 30000,
    createRetryIntervalMillis: 1000
  },
  defaultExchange: 'ecommerce.events',
  prefetchCount: 10,
  retryDelayMs: 1000,
  maxRetries: 3,
  enableDLQ: true,
  dlqSuffix: '.dlq'
};
```

### 4.2 Create Connection Manager

```typescript
// src/connection/connection.manager.ts
import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import * as amqp from 'amqplib';
import { RabbitMQOptions, defaultRabbitMQOptions } from '../config/rabbitmq.config';

export interface ChannelWrapper {
  channel: amqp.Channel;
  isActive: boolean;
  lastUsed: Date;
  id: string;
}

@Injectable()
export class ConnectionManager implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(ConnectionManager.name);
  private connection: amqp.Connection | null = null;
  private channels: Map<string, ChannelWrapper> = new Map();
  private options: RabbitMQOptions;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;

  constructor(options: Partial<RabbitMQOptions>) {
    this.options = { ...defaultRabbitMQOptions, ...options };
  }

  async onModuleInit(): Promise<void> {
    await this.connect();
  }

  async onModuleDestroy(): Promise<void> {
    await this.disconnect();
  }

  async connect(): Promise<amqp.Connection> {
    if (this.connection && !this.connection.connection.destroyed) {
      return this.connection;
    }

    if (this.isConnecting) {
      // Wait for existing connection attempt
      while (this.isConnecting) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      return this.connection!;
    }

    this.isConnecting = true;

    try {
      const { connection: connConfig } = this.options;
      
      let connectionUrl: string;
      if (connConfig.url) {
        connectionUrl = connConfig.url;
      } else {
        const protocol = connConfig.protocol || 'amqp';
        const hostname = connConfig.hostname || 'localhost';
        const port = connConfig.port || 5672;
        const username = connConfig.username || 'guest';
        const password = connConfig.password || 'guest';
        const vhost = connConfig.vhost || '/';
        
        connectionUrl = `${protocol}://${username}:${password}@${hostname}:${port}${vhost}`;
      }

      this.logger.log('Connecting to RabbitMQ...');
      this.connection = await amqp.connect(connectionUrl, {
        frameMax: connConfig.frameMax,
        heartbeat: connConfig.heartbeat || 60,
        locale: connConfig.locale || 'en_US'
      });

      this.connection.on('error', this.handleConnectionError.bind(this));
      this.connection.on('close', this.handleConnectionClose.bind(this));

      this.logger.log('Connected to RabbitMQ successfully');
      this.isConnecting = false;
      
      return this.connection;

    } catch (error) {
      this.isConnecting = false;
      this.logger.error('Failed to connect to RabbitMQ', error);
      this.scheduleReconnect();
      throw error;
    }
  }

  async createChannel(): Promise<ChannelWrapper> {
    const connection = await this.connect();
    
    try {
      const channel = await connection.createChannel();
      const channelId = require('uuid').v4();
      
      await channel.prefetch(this.options.prefetchCount || 10);
      
      const wrapper: ChannelWrapper = {
        channel,
        isActive: true,
        lastUsed: new Date(),
        id: channelId
      };

      channel.on('error', (error) => {
        this.logger.error(`Channel ${channelId} error:`, error);
        wrapper.isActive = false;
        this.channels.delete(channelId);
      });

      channel.on('close', () => {
        this.logger.warn(`Channel ${channelId} closed`);
        wrapper.isActive = false;
        this.channels.delete(channelId);
      });

      this.channels.set(channelId, wrapper);
      this.logger.debug(`Created channel ${channelId}`);
      
      return wrapper;

    } catch (error) {
      this.logger.error('Failed to create channel', error);
      throw error;
    }
  }

  async getChannel(): Promise<amqp.Channel> {
    const wrapper = await this.createChannel();
    return wrapper.channel;
  }

  async closeChannel(channelId: string): Promise<void> {
    const wrapper = this.channels.get(channelId);
    if (wrapper && wrapper.isActive) {
      try {
        await wrapper.channel.close();
        this.channels.delete(channelId);
        this.logger.debug(`Closed channel ${channelId}`);
      } catch (error) {
        this.logger.error(`Error closing channel ${channelId}:`, error);
      }
    }
  }

  async disconnect(): Promise<void> {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Close all channels
    for (const [channelId, wrapper] of this.channels) {
      if (wrapper.isActive) {
        try {
          await wrapper.channel.close();
        } catch (error) {
          this.logger.error(`Error closing channel ${channelId}:`, error);
        }
      }
    }
    this.channels.clear();

    // Close connection
    if (this.connection && !this.connection.connection.destroyed) {
      try {
        await this.connection.close();
        this.logger.log('Disconnected from RabbitMQ');
      } catch (error) {
        this.logger.error('Error closing connection:', error);
      } finally {
        this.connection = null;
      }
    }
  }

  isConnected(): boolean {
    return this.connection !== null && !this.connection.connection.destroyed;
  }

  getConnectionInfo(): any {
    if (!this.connection) {
      return { status: 'disconnected' };
    }

    return {
      status: 'connected',
      activeChannels: this.channels.size,
      serverProperties: this.connection.connection.serverProperties
    };
  }

  private handleConnectionError(error: Error): void {
    this.logger.error('RabbitMQ connection error:', error);
    this.connection = null;
    this.scheduleReconnect();
  }

  private handleConnectionClose(): void {
    this.logger.warn('RabbitMQ connection closed');
    this.connection = null;
    this.scheduleReconnect();
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return; // Already scheduled
    }

    const delay = 5000; // 5 seconds
    this.logger.log(`Scheduling reconnect in ${delay}ms`);
    
    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      try {
        await this.connect();
      } catch (error) {
        // Will schedule another reconnect
      }
    }, delay);
  }
}
```

---

## Step 5: Export Components

```typescript
// src/envelope/index.ts
export * from './message.types';
export * from './message.envelope';
export * from './event.registry';

// src/connection/index.ts
export * from './connection.manager';

// src/config/index.ts
export * from './rabbitmq.config';
```

---

## Step 6: Create Tests

### 6.1 Test Message Envelope

```typescript
// src/envelope/message.envelope.spec.ts
import { MessageEnvelope, BaseMessage } from './message.envelope';

describe('MessageEnvelope', () => {
  it('should create a valid message envelope', async () => {
    const envelope = await MessageEnvelope.create(
      'user.created',
      'user-service',
      'user-123',
      'User',
      { email: 'test@example.com', name: 'Test User' },
      'user.created',
      'ecommerce.events'
    );

    expect(envelope.message.eventType).toBe('user.created');
    expect(envelope.message.sourceService).toBe('user-service');
    expect(envelope.message.aggregateId).toBe('user-123');
    expect(envelope.message.data.email).toBe('test@example.com');
    expect(envelope.routingKey).toBe('user.created');
    expect(envelope.exchange).toBe('ecommerce.events');
  });

  it('should serialize and deserialize correctly', async () => {
    const envelope = await MessageEnvelope.create(
      'user.updated',
      'user-service',
      'user-123',
      'User',
      { email: 'updated@example.com' },
      'user.updated',
      'ecommerce.events'
    );

    const buffer = envelope.toBuffer();
    const deserialized = MessageEnvelope.fromBuffer(buffer);

    expect(deserialized.message.eventType).toBe(envelope.message.eventType);
    expect(deserialized.message.data.email).toBe(envelope.message.data.email);
  });

  it('should add correlation ID', async () => {
    const envelope = await MessageEnvelope.create(
      'user.created',
      'user-service',
      'user-123',
      'User',
      { email: 'test@example.com' },
      'user.created',
      'ecommerce.events'
    );

    const correlationId = 'correlation-123';
    const withCorrelation = envelope.withCorrelation(correlationId);

    expect(withCorrelation.message.metadata?.correlationId).toBe(correlationId);
    expect(withCorrelation.headers.correlationId).toBe(correlationId);
  });
});
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
```

---

## Step 8: Build and Verify

```bash
# Build the package
npm run build

# Run tests
npm test

# Verify build outputs
ls -la dist/
```

---

## 🎯 Key Accomplishments

✅ **Standardized message envelope** with validation and metadata support  
✅ **Type-safe event definitions** with registry pattern  
✅ **Robust connection management** with automatic reconnection  
✅ **Message serialization/deserialization** with proper error handling  
✅ **Correlation ID support** for request tracing  
✅ **Retry mechanisms** and delay support built-in  

---

## 🔗 Next Steps

Continue with **[02-producers-and-publishers.md](./02-producers-and-publishers.md)** to build event producers and publishing utilities with reliability patterns.

---

## 💡 Usage Preview

Once complete, services will publish events like this:

```typescript
import { MessageEnvelope, EventProducer } from '@ecommerce/rabbitmq-event-utils';

const envelope = await MessageEnvelope.create(
  'user.created',
  'user-service',
  'user-123',
  'User',
  { email: 'user@example.com', name: 'John Doe' },
  'user.created',
  'ecommerce.events'
);

await eventProducer.publish(envelope);
```