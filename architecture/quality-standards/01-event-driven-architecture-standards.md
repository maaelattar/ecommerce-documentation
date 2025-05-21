# Event-Driven Architecture Standards

## 1. Overview

This document outlines the standards and best practices for implementing event-driven architecture across the e-commerce platform. Event-driven architecture enables loose coupling between services, improves scalability, and creates a more resilient system. These standards ensure consistent implementation across all microservices.

## 2. Core Principles

### 2.1. Asynchronous by Default

- All service-to-service communication should be asynchronous by default
- Synchronous API calls should be used only when immediate response is absolutely necessary
- Services should be designed to operate without requiring immediate responses from other services

### 2.2. Event Ownership

- Each domain owns its events and defines the schema
- Events should represent domain facts that have occurred, not commands or requests
- Event names should be in past tense (e.g., `order.created`, not `create.order`)

### 2.3. Decoupled Services

- Services should not have direct runtime dependencies on other services
- Services should maintain their own read models of data they frequently need from other domains
- Domain boundaries should be respected in event design

## 3. Event Design Standards

### 3.1. Event Schema

All events must follow this standardized envelope format:

```json
{
  "id": "string", // UUID v4 unique event identifier
  "type": "string", // Event type in format "domain.event_name"
  "source": "string", // Source service name
  "dataVersion": "string", // Schema version (semver)
  "timestamp": "string", // ISO-8601 timestamp
  "correlationId": "string", // For event tracing
  "data": {} // Event payload
}
```

### 3.2. Versioning

- All event schemas must include a version number
- Breaking changes require incrementing the major version number
- Events should be backward compatible when possible
- Services must support at least one previous major version of events

### 3.3. Event Documentation

- All events must have corresponding documentation that includes:
  - Complete schema definition
  - Example payloads
  - Publishing scenarios
  - Expected consumer behaviors
  - List of producing and consuming services

## 4. Implementation Patterns

### 4.1. CQRS (Command Query Responsibility Segregation)

- Services should maintain read models for data from other domains they need frequently
- These models should be updated based on events from the authoritative service
- Read models should be optimized for the specific query patterns of the service

### 4.2. Saga Pattern for Distributed Transactions

- Complex operations spanning multiple services should use the saga pattern
- Each step in the saga should be triggered by events
- Compensating transactions should be implemented for rollback scenarios
- Saga orchestrator should track and manage the overall transaction state

```
┌───────────┐         ┌───────────┐         ┌───────────┐         ┌───────────┐
│   Order   │         │  Payment  │         │ Inventory │         │  Shipping │
│  Service  │         │  Service  │         │  Service  │         │  Service  │
└─────┬─────┘         └─────┬─────┘         └─────┬─────┘         └─────┬─────┘
      │                     │                     │                     │
      │ order.created       │                     │                     │
      │ ──────────────────> │                     │                     │
      │                     │                     │                     │
      │                     │ payment.completed   │                     │
      │ <─────────────────────────────────────────│                     │
      │                     │                     │                     │
      │ order.payment_      │                     │                     │
      │ completed           │                     │                     │
      │ ──────────────────────────────────────────>                     │
      │                     │                     │                     │
      │                     │                     │ inventory.reserved  │
      │ <─────────────────────────────────────────────────────────────────────>
      │                     │                     │                     │
      │ order.ready_for_    │                     │                     │
      │ shipping            │                     │                     │
      │ ────────────────────────────────────────────────────────────────────> │
      │                     │                     │                     │
      │                     │                     │                     │ shipping.created
      │ <─────────────────────────────────────────────────────────────────────│
```

### 4.3. Event Sourcing

- Consider event sourcing for domains with complex state transitions and audit requirements
- Store the sequence of events as the source of truth
- Rebuild state by replaying events
- Implement snapshots for performance optimization

### 4.4. Outbox Pattern

- Use the outbox pattern to ensure reliable event publishing
- Store outgoing events in a local transaction with domain changes
- A separate process reliably publishes events from the outbox
- Mark events as published once successfully delivered

## 5. Resilience Patterns

### 5.1. Idempotent Consumers

- All event consumers must implement idempotency
- Events may be delivered multiple times and should be safely processed
- Store event IDs with processed status to detect duplicates
- Include enough context in events to enable idempotent processing

### 5.2. Dead Letter Queues

- Implement dead letter queues for events that fail processing
- Configure retry policies with exponential backoff
- Monitor dead letter queues as part of operational health checks
- Implement recovery mechanisms for events in dead letter queues

### 5.3. Circuit Breakers

- Implement circuit breakers for any remaining synchronous dependencies
- Include fallback mechanisms using cached data
- Gracefully degrade functionality when dependencies are unavailable

### 5.4. Eventual Consistency Management

- Design systems to handle temporary inconsistencies between services
- Implement compensating actions for detected inconsistencies
- Provide appropriate user feedback during eventual consistency windows

## 6. Data Caching and Replication

### 6.1. Local Cache Standards

- Services should maintain local caches of frequently needed data
- Cache invalidation should be event-driven
- TTL (Time To Live) should be defined for all cached data
- Cache hit/miss ratios should be monitored

### 6.2. Read Replicas

- Services should build and maintain their own read models of external data
- These models should be optimized for the service's specific query needs
- Read models should be updated based on domain events
- Periodic reconciliation jobs should verify consistency

## 7. Testing Standards

### 7.1. Event Contract Testing

- Define and maintain event contracts between producers and consumers
- Implement automated contract tests for all event interfaces
- Version contracts alongside event schemas
- Run contract tests as part of CI/CD pipelines

### 7.2. Event Flow Testing

- Test complete event flows through all relevant services
- Verify event payload transformations across service boundaries
- Include timing and out-of-order event scenarios in tests
- Test compensating transactions and recovery paths

### 7.3. Chaos Testing

- Intentionally introduce failures in message processing and publishing
- Test system behavior with delayed events, duplicate events, and out-of-order events
- Verify system recovery after broker outages

## 8. Monitoring and Observability

### 8.1. Event Tracing

- Include correlation IDs in all events for distributed tracing
- Log event production and consumption with correlation context
- Implement trace visualization across service boundaries
- Enable tracing of complete business transactions across services

### 8.2. Event Metrics

- Track event production and consumption rates
- Monitor processing latency for critical event flows
- Alert on backlog growth or processing delays
- Measure end-to-end latency of business processes

### 8.3. Event Replay Capability

- Implement capabilities to replay events from a specific point in time
- Support service recovery through event replay
- Enable data reconstruction through selective event replay
- Document replay procedures for different scenarios

## 9. Implementation Examples

### 9.1. Order Creation Flow

Replace synchronous product validation with:

```typescript
// Instead of this synchronous approach:
async createOrder(createOrderDto: CreateOrderDto): Promise<Order> {
  // Synchronous product validation
  await this.productService.validateProducts(createOrderDto.items);

  // Create order
  const order = await this.orderRepository.create({
    ...createOrderDto,
    status: 'CREATED'
  });

  return order;
}

// Use this asynchronous approach:
async createOrder(createOrderDto: CreateOrderDto): Promise<Order> {
  // Create order in pending validation state
  const order = await this.orderRepository.create({
    ...createOrderDto,
    status: 'PENDING_VALIDATION'
  });

  // Publish event for product validation
  await this.eventPublisher.publish('order.pending_validation', {
    orderId: order.id,
    items: order.items
  });

  return order;
}

// Then handle the validation asynchronously:
@EventPattern('product.validation_completed')
async handleProductValidationCompleted(
  @Payload() event: ProductValidationCompletedEvent
): Promise<void> {
  const { orderId, isValid, invalidItems } = event.data;

  if (isValid) {
    await this.orderService.progressOrderToNextStage(orderId, 'VALIDATED');
  } else {
    await this.orderService.rejectOrder(orderId, 'INVALID_PRODUCTS', invalidItems);
  }
}
```

### 9.2. User Data Caching

```typescript
// Subscribe to user events to maintain local cache
@EventPattern('user.updated')
async handleUserUpdated(
  @Payload() event: UserUpdatedEvent
): Promise<void> {
  const { userId, fields, ...userData } = event.data;

  // Update local user cache
  await this.userCacheRepository.upsert(userId, {
    ...userData,
    updatedAt: new Date()
  });

  // Check if any orders need updates based on user changes
  if (fields.includes('email') || fields.includes('phone')) {
    await this.orderService.updateOrdersWithLatestUserContact(userId, userData);
  }
}
```

## 10. References

- [Event-Driven Architecture Infrastructure](../infrastructure/event-driven-architecture.md)
- [Message Broker Configuration](../../infrastructure/message-broker-setup.md)
- [Saga Implementation Guidelines](../../architecture/patterns/saga-pattern.md)
- [Distributed Tracing Setup](../../infrastructure/observability/distributed-tracing.md)
