# Error Handling and Resilience in Event Processing

## Overview

Event-driven architectures must be resilient to failures. When the Search Service consumes events, various issues can arise: network problems, invalid event payloads, temporary unavailability of Elasticsearch, bugs in transformation logic, etc. Robust error handling and resilience mechanisms are crucial to prevent data loss, ensure eventual consistency, and maintain service stability.

## Key Principles

*   **Identify Failure Types**: Differentiate between transient errors (retriable) and permanent errors (non-retriable without intervention).
*   **Retry Mechanism**: For transient errors, implement a retry strategy with backoff.
*   **Dead Letter Queue (DLQ)**: For permanent errors or events that fail repeatedly even after retries, send them to a DLQ for manual inspection and potential reprocessing.
*   **Idempotency**: Ensure that retrying an event (or processing a duplicate from the broker) does not cause unintended side effects (as covered in `07-index-update-logic.md`).
*   **Monitoring & Alerting**: Actively monitor error rates, DLQ size, and processing latencies to detect and diagnose issues quickly.
*   **Circuit Breaker**: Optionally, implement a circuit breaker pattern if downstream services (like Elasticsearch) become overwhelmed or consistently unavailable.

## Error Handling Stages and Strategies

### 1. Event Deserialization & Validation Failure

*   **Issue**: Event message is malformed (e.g., not valid JSON) or fails schema/business validation (e.g., missing required fields).
*   **Strategy**:
    *   These are often permanent errors for the given message.
    *   Log the error with the full event payload (or a reference to it if it's too large) for debugging.
    *   Send the problematic message directly to a Dead Letter Queue (DLQ) with metadata about the failure (e.g., "DeserializationError", "ValidationError").
    *   Acknowledge the message to the broker to prevent it from being redelivered (if using manual acknowledgment).

### 2. Transformation Logic Failure

*   **Issue**: An error occurs while transforming the validated event data into the search document format (e.g., unexpected null value, failed lookup for enrichment data).
*   **Strategy**:
    *   Log the error with event details and the state of transformation.
    *   Depending on the error's nature:
        *   If it's a bug in the transformer, it's likely a permanent error for that event type until fixed. Send to DLQ.
        *   If it's due to transient issues (e.g., a temporary failure in a cached lookup), it might be retriable.
    *   Generally, transformation errors after validation point to unexpected data shapes or bugs and are best sent to a DLQ.

### 3. Elasticsearch Operation Failure (Indexing, Update, Delete)

*   **Issue**: The Elasticsearch client throws an error when attempting to modify an index.
    *   **Transient Errors**: Network issues, temporary Elasticsearch unavailability (e.g., node restarting, brief cluster overload), request timeouts.
    *   **Permanent Errors**: Mapping conflicts (e.g., trying to index a string into a number field), malformed queries (should be caught earlier), authentication/authorization issues, document too large.

*   **Strategy**:
    *   **Retry Mechanism (for Transient Errors)**:
        *   The NestJS Kafka transporter (or `kafkajs` client) can be configured for retries.
        *   **Configuration (Conceptual - NestJS Kafka Client Options)**:
            ```typescript
            // In Kafka client options for the microservice
            consumer: {
              groupId: 'search-service-consumer-group',
              retry: { // kafkajs retry options
                initialRetryTime: 3000, // 3 seconds
                retries: 5, // Number of retries
                maxRetryTime: 30000, // Max wait 30 seconds between retries
                multiplier: 2, // Exponential backoff
                factor: 0, // No randomization factor by default for kafkajs, NestJS might add its layer
              },
              // recoverCommittingOffsets: true, // Ensure offsets are not committed for retried messages until success
            },
            // It's important to ensure that NestJS microservice retry logic correctly handles errors thrown
            // by @MessagePattern or @EventPattern handlers to trigger these retries.
            // If an error is thrown from the handler, NestJS (depending on version and specific transporter behavior)
            // might NACK the message, making it eligible for redelivery by Kafka, subject to broker config.
            // Or, it might rely on client-side retries configured above if those are part of the client lib Nest uses.
            ```
        *   Ensure the retry attempts an operation that is genuinely transient. Retrying a mapping conflict indefinitely is futile.
        *   Log each retry attempt.

    *   **Dead Letter Queue (DLQ) (for Permanent Errors or After Max Retries)**:
        *   If retries are exhausted or the error is identified as non-retriable (e.g., `4xx` HTTP status codes from Elasticsearch like mapping errors, bad requests), the event must be moved to a DLQ.
        *   **DLQ Implementation**: Usually a separate Kafka topic (e.g., `search-service-dlq`).
        *   The DLQ message should include:
            *   The original event payload.
            *   Error information (stack trace, error message, type of error).
            *   Metadata (original topic, partition, offset, timestamp of failure, number of retries).
        *   **DLQ Producer**: A dedicated Kafka producer within the Search Service to send messages to the DLQ topic.

        ```typescript
        // Conceptual DLQ Service
        import { Injectable, Logger } from '@nestjs/common';
        import { KafkaProducerService } from './kafka-producer.service'; // A generic Kafka producer wrapper
        import { ConfigService } from '@nestjs/config';

        @Injectable()
        export class DlqService {
          private readonly logger = new Logger(DlqService.name);
          private dlqTopic: string;

          constructor(
            private readonly kafkaProducer: KafkaProducerService,
            private readonly configService: ConfigService,
          ) {
            this.dlqTopic = this.configService.get<string>('kafka.dlqTopic', 'search-service-dlq');
          }

          async sendToDlq(originalEvent: any, errorDetails: any, metadata: any): Promise<void> {
            const dlqMessage = {
              originalEvent,
              error: {
                message: errorDetails.message,
                stack: errorDetails.stack,
                type: errorDetails.constructor.name,
              },
              processingMetadata: metadata, // original topic, offset, retry attempts, etc.
              failedAt: new Date().toISOString(),
            };
            try {
              await this.kafkaProducer.send(this.dlqTopic, dlqMessage);
              this.logger.log(`Message sent to DLQ topic ${this.dlqTopic} (Event ID: ${metadata.eventId || 'N/A'})`);
            } catch (producerError) {
              this.logger.error(`FATAL: Could not send message to DLQ ${this.dlqTopic}:`, producerError);
              // This is a critical failure; may need to crash/alert aggressively
            }
          }
        }
        ```

### 4. Idempotency Revisited

*   Crucial when retries or redeliveries occur. If an event is processed successfully but the acknowledgment to the broker fails, it might be redelivered.
*   The `IndexingService` (see `07-index-update-logic.md`) should use a persistent store for processed `eventId`s to prevent duplicate Elasticsearch operations.
*   The check for `hasProcessed(eventId)` should happen before attempting the ES operation.
*   `markAsProcessed(eventId)` should happen only after the ES operation is successful.

## Consumer Lifecycle and Graceful Shutdown

*   **Graceful Shutdown**: When a service instance is shutting down (e.g., during deployment, scaling down), it should stop consuming new messages, finish processing in-flight messages, and commit their offsets before exiting.
*   NestJS provides lifecycle hooks (`onApplicationShutdown`) that can be used for this.
    ```typescript
    import { Injectable, OnApplicationShutdown } from '@nestjs/common';
    import { KafkaConsumerService } from './kafka-consumer.service'; // Assuming a wrapper around your consumer

    @Injectable()
    export class GracefulShutdownService implements OnApplicationShutdown {
      constructor(private kafkaConsumerService: KafkaConsumerService) {}

      async onApplicationShutdown(signal?: string) {
        console.log(`Application is shutting down (signal: ${signal}). Cleaning up Kafka consumer...`);
        // await this.kafkaConsumerService.disconnect(); // Example method to gracefully stop consumer
        console.log('Kafka consumer disconnected.');
      }
    }
    ```
*   This prevents messages from being lost or processed twice due to abrupt shutdowns and rebalances.

## Circuit Breaker Pattern (Optional)

*   **Purpose**: If Elasticsearch becomes unstable or unresponsive for an extended period, continuing to hammer it with requests can worsen the situation or cause the Search Service itself to become unstable.
*   **Mechanism**: A circuit breaker monitors failures to a downstream service. If failures exceed a threshold, it "opens" the circuit, causing subsequent calls to fail immediately without attempting the actual operation for a configured cool-down period. After the timeout, it enters a "half-open" state to test connectivity with a few requests. If successful, it closes the circuit; otherwise, it remains open.
*   **Implementation**: Libraries like `opossum` can be used in a Node.js/NestJS environment.
*   **Consideration**: Adds complexity. Assess if the retry and DLQ mechanisms are sufficient first. Useful if Elasticsearch has known periods of high load where backing off is beneficial.

## Monitoring and Alerting for Resilience

*   **DLQ Size**: Monitor the number of messages in the DLQ. A growing DLQ indicates persistent problems.
*   **Error Rates**: Track the rate of processing errors (retries, DLQ entries) per event type or topic.
*   **Consumer Lag**: Monitor Kafka consumer lag to ensure the Search Service is keeping up with event production.
*   Set up alerts for high DLQ sizes, sustained high error rates, or significant consumer lag.

## Next Steps

*   `09-monitoring-and-logging.md`: Focus on comprehensive logging and monitoring strategies for event processing.
*   `10-data-consistency-strategies.md`: Discuss maintaining data consistency in an event-driven system.
