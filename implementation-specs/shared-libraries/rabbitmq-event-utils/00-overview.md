# 00: RabbitMQ Event Utilities - Overview

## 1. Purpose

The `rabbitmq-event-utils` shared library is designed to provide a standardized and robust set of tools and patterns for producing and consuming RabbitMQ messages within the NestJS-based microservices of the e-commerce platform. This aligns with the platform's primary choice of **Amazon MQ for RabbitMQ** as the message broker (see ADR-018 and TDAC/03-message-broker-selection.md).

Asynchronous event-driven communication is a core aspect of the architecture, and this library aims to ensure consistency, reliability, and developer efficiency when working with RabbitMQ.

Key objectives:
*   Define a standard event envelope/schema for all messages.
*   Provide easy-to-use NestJS modules and services for producing messages to RabbitMQ exchanges.
*   Offer standardized patterns and utilities for consuming messages from RabbitMQ queues, including error handling (e.g., Dead Letter Exchanges - DLX).
*   Simplify serialization and deserialization of message payloads (primarily JSON).
*   Promote best practices for RabbitMQ integration, particularly with Amazon MQ.

## 2. Scope and Key Components

This library will likely include:

1.  **Standard Message Envelope:**
    *   A TypeScript interface or class defining the structure of all messages. This envelope would typically include metadata like `messageId` (or `eventId`), `messageType` (or `eventType`), `messageVersion` (or `eventVersion`), `timestamp`, `sourceService`, `correlationId`, and the actual `payload`.

2.  **Event Producer Module/Service (`RabbitMQProducerModule`):**
    *   A NestJS module that configures and provides a `RabbitMQProducerService`.
    *   The service will abstract complexities of interacting with an AMQP client library (e.g., `amqplib`).
    *   Methods to easily publish messages to specified exchanges with routing keys, automatically wrapping payloads in the standard envelope.
    *   Handles connection and channel management, and basic error handling during publishing (e.g., publisher confirms).

3.  **Event Consumer Utilities/Decorators (`RabbitMQConsumerModule` or Patterns):
    *   NestJS provides `@nestjs/microservices` with RabbitMQ transport. This library may offer additional utilities or decorators for common consumer patterns if `@nestjs/microservices` is not used directly for all consumers, or to enhance it.
    *   Standardized deserialization of the message envelope.
    *   Helpers for common consumer-side tasks: idempotent processing, context extraction (e.g., `correlationId` from message properties to logger context).
    *   Guidance or utilities for Dead Letter Exchange (DLX) and retry strategies.

4.  **Serialization/Deserialization:**
    *   Default serializers/deserializers (JSON for payloads) that work with the standard message envelope.

5.  **Configuration:**
    *   Utilities to help configure AMQP client settings (e.g., connection URI including username/password for Amazon MQ, exchange/queue names) via environment variables, integrating with the `SharedConfigModule` from `nestjs-core-utils`.

## 3. Technical Stack

*   **Language:** TypeScript
*   **Framework:** NestJS
*   **Key Dependencies (Examples):** An AMQP client library (e.g., `amqplib`), `@nestjs/microservices` (if enhancing its RabbitMQ transport).

## 4. Non-Goals

*   **RabbitMQ Broker Management:** This library does not deal with the provisioning or management of the Amazon MQ for RabbitMQ brokers themselves.
*   **Complex Routing Logic Definition:** While it facilitates publishing to exchanges, the definition of complex exchange/queue topologies might reside in infrastructure-as-code or service-specific setup, though the library might provide helpers to declare them idempotently.
*   **Service-Specific Business Logic:** The actual handling of message payloads and the business logic reacting to messages reside within the individual consuming services.

## 5. Versioning and Distribution

*   **Versioning:** The library will follow Semantic Versioning (SemVer) to ensure consumers can manage updates predictably.
*   **Distribution:** It will be published as a private NPM package to the organization's package registry.

## 6. Stability and Testing

*   **Stability:** The `rabbitmq-event-utils` library aims for high stability in its core functionalities to ensure reliable event-driven communication. Changes will be managed carefully.
*   **Testing:** Each component within this library will undergo thorough testing, including integration tests with a RabbitMQ instance, to ensure correctness and robustness.

This library will be crucial for consistent and reliable inter-service communication using RabbitMQ on the platform.