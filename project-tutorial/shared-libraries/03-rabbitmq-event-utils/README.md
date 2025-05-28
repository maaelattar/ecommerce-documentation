# RabbitMQ Event Utils - @ecommerce/rabbitmq-event-utils

## Overview

This tutorial builds the event-driven messaging utilities that provide standardized message envelopes, producer/consumer patterns, and RabbitMQ management for all microservices.

## 🎯 Learning Objectives

- Create standard message envelope schemas
- Build event producer and consumer utilities
- Implement RabbitMQ connection management
- Add message serialization and validation
- Support event replay and dead letter queues

## Package Features

### 1. Standard Message Envelope
```typescript
interface StandardMessage<T> {
  eventId: string;
  eventType: string;
  eventTimestamp: Date;
  sourceService: string;
  correlationId?: string;
  version: string;
  data: T;
}
```

### 2. Event Producer
- Reliable message publishing
- Connection pooling and retry logic
- Message durability and persistence
- Routing key management

### 3. Event Consumer
- Subscription management
- Message acknowledgment patterns
- Error handling and retry mechanisms
- Dead letter queue processing

### 4. Configuration & Health
- Environment-based RabbitMQ configuration
- Connection health monitoring
- Queue and exchange management
- Performance metrics

Ready to build robust event-driven messaging? Let's implement the core patterns!