# Event Publishing Mechanism

## 1. Overview

This document specifies the chosen event publishing mechanism and technology for the Product Service, in line with the platform's overall event-driven architecture strategy (see ADR-002 and potentially ADR-015 or similar for specific technology choice).

## 2. Chosen Technology

**_[Placeholder: This section needs to be filled in once the specific event bus technology is finalized. Examples: Apache Kafka, RabbitMQ, AWS SNS/SQS, Google Cloud Pub/Sub, Azure Event Grid/Hubs.]_**

- **Technology Name**: e.g., Apache Kafka
- **Version**: e.g., 3.x
- **Rationale for Choice**: Briefly summarize why this technology was chosen (refer to ADRs if applicable).

## 3. Configuration and Setup

**_[Placeholder: Details specific to the chosen technology]_**

### 3.1. Connection Details
- Broker URLs / Endpoints
- Authentication/Authorization mechanisms (e.g., SASL, SSL certificates, IAM roles)

### 3.2. Topics / Exchanges / Queues

- **Naming Convention**: e.g., `product-service.events`, or more granular like `product.product-created`, `product.category-updated`.
- **List of Key Topics/Exchanges for Product Service Events**:
  - `product_events` (for `ProductCreated`, `ProductUpdated`, `ProductDeleted`, `ProductStatusChanged`, etc.)
  - `category_events` (for `CategoryCreated`, `CategoryUpdated`, `CategoryDeleted`, `CategoryMoved`)
  - `price_events` (for `ProductPriceUpdated`, `DiscountCreated`, `DiscountStatusChanged`, etc.)
  *(Note: The actual topic strategy - one topic per service vs. one per event type vs. one per entity - depends on the chosen technology and consumption patterns.)*

### 3.3. Partitions and Consumer Groups (if applicable)
- Strategy for partitioning (e.g., by `entityId` to ensure ordered processing for a given entity).
- Naming conventions for consumer groups.

### 3.4. Message Format
- Serialization format (e.g., JSON, Avro, Protobuf). JSON is assumed as per the General Event Structure in the overview.
- Schema management/registry if applicable (e.g., Confluent Schema Registry for Avro/Protobuf with Kafka).

## 4. Reliability and Resilience

**_[Placeholder: Details specific to the chosen technology]_**

### 4.1. Message Persistence
- Replication factor for topics.
- Message retention policies.

### 4.2. Delivery Guarantees
- Publisher acknowledgments (e.g., `ack=all` in Kafka).
- At-least-once delivery semantics are assumed.

### 4.3. Dead Letter Queues (DLQs) / Error Handling
- Strategy for handling messages that cannot be processed by consumers after multiple retries.
- Configuration of DLQs and monitoring.

### 4.4. Idempotent Producers (if supported/configured)
- Ensuring that publishing the same logical event multiple times (e.g., due to retries) doesn't create duplicate messages on the bus if the broker supports it.

## 5. Monitoring and Alerting

**_[Placeholder: Details specific to the chosen technology]_**

- Key metrics to monitor (e.g., message throughput, latency, error rates, consumer lag).
- Tools used for monitoring (e.g., Prometheus, Grafana, CloudWatch, Datadog).
- Alerting setup for critical issues (e.g., high consumer lag, high error rates, broker unavailability).

## 6. Security

- **Encryption in Transit**: (e.g., SSL/TLS for communication with the event bus).
- **Encryption at Rest**: (if messages are persisted by the broker).
- **Access Control**: Who can publish to / subscribe from topics.

## 7. References

- [Event Publishing Overview](./00-overview.md)
- [ADR-002: Event-Driven Architecture](../../../architecture/adr/ADR-002-event-driven-architecture.md)
- [ADR-015: Event Bus Technology Choice](../../../architecture/adr/ADR-015-event-bus-technology-choice.md) *(Hypothetical ADR)* 