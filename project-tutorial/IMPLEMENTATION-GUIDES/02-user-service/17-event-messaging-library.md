# Tutorial 17: Create Event Messaging Library

## 🎯 Objective
Create a shared RabbitMQ event library for consistent event publishing across all microservices.

## 📚 Why This is Needed
Product Service needs standardized event publishing for ProductCreated, ProductUpdated, PriceChanged events.

## Step 1: Setup Package
```bash
mkdir -p shared-libraries/rabbitmq-event-utils
cd shared-libraries/rabbitmq-event-utils
npm init -y
npm install @nestjs/common @nestjs/microservices amqplib
npm install -D typescript @types/amqplib
```

## Step 2: Core Event Infrastructure

### 2.1 Base Event Interface
```typescript
// src/interfaces/base-event.interface.ts
export interface BaseEvent {
  id: string;
  type: string;
  aggregateId: string;
  aggregateType: string;
  version: number;
  timestamp: Date;
  data: any;
  metadata?: {
    correlationId?: string;
    userId?: string;
  };
}
```

### 2.2 Event Publisher
```typescript
// src/services/event-publisher.service.ts
import { Injectable } from '@nestjs/common';
import { ClientProxy } from '@nestjs/microservices';
import { BaseEvent } from '../interfaces/base-event.interface';
import { v4 as uuidv4 } from 'uuid';

@Injectable()
export class EventPublisher {
  constructor(private readonly client: ClientProxy) {}

  async publish(eventType: string, aggregateId: string, data: any): Promise<void> {
    const event: BaseEvent = {
      id: uuidv4(),
      type: eventType,
      aggregateId,
      aggregateType: eventType.split('.')[0],
      version: 1,
      timestamp: new Date(),
      data,
    };

    await this.client.emit(eventType, event).toPromise();
  }
}
```

## Step 3: Export Module
```typescript
// src/index.ts
export * from './interfaces/base-event.interface';
export * from './services/event-publisher.service';
```

## ✅ Next Step
Continue to **[18-testing-integration.md](./18-testing-integration.md)**