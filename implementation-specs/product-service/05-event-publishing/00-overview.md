# Phase 5: Event Publishing - Overview

## 1. Purpose

This phase details the event publishing strategy for the Product Service. In an event-driven architecture, the Product Service is responsible for notifying other interested services (e.g., Order Service, Search Service, Notification Service, Analytics Service) about significant changes to its core entities (Products, Categories, Prices).

This ensures loose coupling between services and allows for asynchronous processing and data synchronization across the platform.

## 2. Key Objectives

- Define the specific domain events that the Product Service will publish.
- Specify the schema and payload for each event.
- Outline the chosen event publishing mechanism and technology (e.g., message broker, event bus).
- Describe patterns for event publishing, including reliability, idempotency, and error handling.

## 3. Types of Events Published

The Product Service will publish events related to the lifecycle and significant state changes of its primary entities:

- **Product Events:** Changes related to products, product variants, and their attributes.
  - Examples: `ProductCreated`, `ProductUpdated`, `ProductDeleted`, `ProductVariantAdded`, `ProductPublished`, `ProductUnpublished`.
  - See: [01-product-events.md](./01-product-events.md)
- **Category Events:** Changes related to product categories and their hierarchy.
  - Examples: `CategoryCreated`, `CategoryUpdated`, `CategoryDeleted`, `CategoryMoved`.
  - See: [02-category-events.md](./02-category-events.md)
- **Price & Discount Events:** Changes related to product pricing and discounts.
  - Examples: `ProductPriceUpdated`, `DiscountCreated`, `DiscountAppliedToProduct`, `DiscountRemovedFromProduct`, `DiscountExpired`.
  - See: [03-price-events.md](./03-price-events.md)

## 4. Event Publishing Mechanism

- **Chosen Technology:** RabbitMQ (via Amazon MQ for RabbitMQ), leveraging the `@ecommerce-platform/rabbitmq-event-utils` shared library. This aligns with ADR-018: Message Broker Strategy and TDAC/03: Message Broker Selection.
- **Key Considerations:**
  - **Reliability:** Guaranteed delivery, at-least-once processing.
  - **Scalability:** Ability to handle a high volume of events.
  - **Ordering:** Ordering guarantees where necessary (e.g., within a partition for a specific entity ID).
  - **Persistence:** How long events are retained.
  - **Monitoring:** Tools and practices for monitoring the event bus and event flow.
- **Detailed Configuration:** See [04-event-publishing-mechanism.md](./04-event-publishing-mechanism.md)

## 5. General Event Structure

All events published by the Product Service should follow the `StandardMessage<T>` structure defined in the `@ecommerce-platform/rabbitmq-event-utils` library:

```json
{
  "messageId": "uuid",          // Unique ID for this specific event instance (formerly eventId)
  "messageType": "string",      // e.g., "ProductCreated", "CategoryUpdated" (formerly eventType)
  "messageVersion": "string",   // e.g., "1.0" (formerly eventVersion)
  "timestamp": "ISO8601",   // Timestamp of when the event occurred (source system time)
  "source": "ProductService",   // Name of the publishing service (formerly sourceService)
  "correlationId": "uuid",    // ID to correlate related operations/requests across services
  "partitionKey": "string",     // Optional: Key for partitioning/routing (e.g., productId, categoryId, tenantId)
  "payload": {
    // Event-specific data (T)
  }
}
```

Note the alignment with `StandardMessage<T>`: `messageId`, `messageType`, `messageVersion`, and `source`. `partitionKey` is used for routing in RabbitMQ, analogous to `entityId`'s previous intent or Kafka's message key.

## 6. Eventual Consistency

Consumers of these events should be designed to handle eventual consistency. The Product Service guarantees to publish events upon successful state changes, but downstream services will update their local views/data asynchronously.

## 7. Idempotency

Event consumers should be designed to be idempotent, meaning processing the same event multiple times should not result in incorrect data or unintended side effects. This is crucial for at-least-once delivery semantics.

## 8. Next Steps

- Detail the schema and payload for each specific event type in the subsequent documents ([01-product-events.md](./01-product-events.md), [02-category-events.md](./02-category-events.md), [03-price-events.md](./03-price-events.md)).
- Document the chosen event publishing technology and its configuration ([04-event-publishing-mechanism.md](./04-event-publishing-mechanism.md)). 