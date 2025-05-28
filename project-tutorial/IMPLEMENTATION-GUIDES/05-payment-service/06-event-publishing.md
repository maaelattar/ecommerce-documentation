# 06. Event Publishing & Financial Events

## Overview

This section implements the transactional outbox pattern for reliable event publishing, ensuring financial events are published with strong consistency guarantees and proper ordering.

## 🎯 Learning Objectives

- Implement transactional outbox pattern
- Create payment event schemas
- Build reliable event publishing with RabbitMQ
- Ensure event ordering and idempotency
- Add event replay capabilities

---

## Step 1: Event Schemas

### 1.1 Payment Event Types

```typescript
// src/events/schemas/payment-events.schema.ts
export interface BasePaymentEvent {
  eventId: string;
  eventType: string;
  timestamp: Date;
  version: string;
  source: 'payment-service';
  correlationId?: string;
}

export interface PaymentProcessedEvent extends BasePaymentEvent {
  eventType: 'payment.processed';
  data: {
    paymentId: string;
    orderId: string;
    customerId: string;
    amount: number;
    currency: string;
    status: 'succeeded' | 'failed' | 'requires_action';
    gatewayTransactionId?: string;
    paymentMethodType: string;
    fees?: number;
  };
}

export interface PaymentCapturedEvent extends BasePaymentEvent {
  eventType: 'payment.captured';
  data: {
    paymentId: string;
    orderId: string;
    amount: number;
    currency: string;
    capturedAt: Date;
  };
}

export interface RefundProcessedEvent extends BasePaymentEvent {
  eventType: 'refund.processed';
  data: {
    refundId: string;
    paymentId: string;
    orderId: string;
    amount: number;
    currency: string;
    reason?: string;
    status: 'succeeded' | 'failed' | 'pending';
  };
}
```

### 1.2 Transactional Outbox Implementation

```typescript
// src/events/services/event-publisher.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, EntityManager } from 'typeorm';
import { OutboxEvent } from '../entities/outbox-event.entity';
import { RabbitMQService } from './rabbitmq.service';

@Injectable()
export class EventPublisherService {
  private readonly logger = new Logger(EventPublisherService.name);

  constructor(
    @InjectRepository(OutboxEvent)
    private outboxRepository: Repository<OutboxEvent>,
    private rabbitMQService: RabbitMQService,
  ) {}

  async publishPaymentEvent(
    eventType: string,
    eventData: any,
    manager?: EntityManager,
  ): Promise<void> {
    const repository = manager 
      ? manager.getRepository(OutboxEvent) 
      : this.outboxRepository;

    // Store event in outbox within the same transaction
    const outboxEvent = repository.create({
      eventType,
      eventData,
      aggregateId: eventData.paymentId || eventData.orderId,
      status: 'pending',
    });

    await repository.save(outboxEvent);

    // If no transaction manager, publish immediately
    if (!manager) {
      await this.processOutboxEvents();
    }
  }

  async processOutboxEvents(): Promise<void> {
    const pendingEvents = await this.outboxRepository.find({
      where: { status: 'pending' },
      order: { createdAt: 'ASC' },
      take: 100,
    });

    for (const event of pendingEvents) {
      try {
        await this.rabbitMQService.publishEvent(
          event.eventType,
          event.eventData,
          event.id,
        );

        await this.outboxRepository.update(event.id, {
          status: 'published',
          publishedAt: new Date(),
        });

        this.logger.log(`Published event ${event.id} of type ${event.eventType}`);
      } catch (error) {
        this.logger.error(`Failed to publish event ${event.id}`, error);
        
        await this.outboxRepository.update(event.id, {
          status: 'failed',
          error: error.message,
          retryCount: () => 'retry_count + 1',
        });
      }
    }
  }
}
```