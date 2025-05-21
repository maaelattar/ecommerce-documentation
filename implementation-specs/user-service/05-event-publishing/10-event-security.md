# 10 - Security of Published Events

Securing published events is crucial, especially since events can carry sensitive information and trigger actions in downstream systems. This document outlines security considerations for events published by the User Service to RabbitMQ (specifically Amazon MQ for RabbitMQ).

## 1. Securing the Message Broker (RabbitMQ/Amazon MQ)

Broker-level security is the first line of defense.

*   **Authentication**: RabbitMQ brokers (including Amazon MQ) require authentication for clients (producers and consumers).
    *   For Amazon MQ, this is typically username/password managed via AWS Secrets Manager or directly.
    *   The User Service (as a producer) will need to be configured with appropriate credentials to authenticate with RabbitMQ, managed via its `ConfigService` and passed to `RabbitMQProducerModule`.
*   **Authorization (Permissions)**: RabbitMQ permissions control which authenticated users can perform specific actions (configure, write, read) on specific resources (vhosts, exchanges, queues).
    *   The User Service producer's RabbitMQ user should have `write` permissions on the target exchanges (e.g., `user.events`) and potentially `configure` if it needs to declare them idempotently (though exchange/queue creation is often better managed via IaC).
    *   Consumer RabbitMQ users should only have `read` permissions on the queues they subscribe to, and `configure` permissions if they declare their own queues.
    *   Administrative access to the RabbitMQ broker/vhost should be tightly restricted.
*   **Encryption in Transit**: Communication between the User Service and RabbitMQ brokers (and between brokers and consumers) must be encrypted using TLS/SSL. Amazon MQ for RabbitMQ enforces TLS.
*   **Encryption at Rest (Broker-Side)**: For Amazon MQ, encryption at rest for broker storage (message data, logs) is managed by AWS, typically using AWS KMS. This protects event data stored on the broker disks.

## 2. Minimizing Sensitive Data in Event Payloads

This is a core principle, detailed in `07-event-payloads-data-minimization.md`.

*   **Avoid PII Where Possible**: Do not include PII in event payloads unless absolutely necessary for direct, identified consumer functionality. Prefer identifiers over full data objects if consumers can fetch details via a secure API call.
*   **No Credentials or Secrets**: Never publish passwords, API keys, MFA secrets, or any form of sensitive credentials in event payloads.
*   **Review and Justify**: Regularly review the data included in event payloads to ensure it's still necessary and that the PII exposure is justified and minimized.

## 3. Event Payload Encryption (Application-Level - Optional, Advanced)

While TLS secures data in transit to/from RabbitMQ, if an extra layer of protection is needed for highly sensitive fields within an event payload *before* it's sent to the broker (and to be decrypted by specific authorized consumers), application-level encryption could be considered.

*   **Mechanism**: Specific fields within the `payload` of an event could be encrypted using a shared secret or asymmetric keys known only to the User Service and authorized consumers.
*   **Complexity**: This adds significant complexity (key management, performance overhead, consumer decryption logic).
*   **User Service Approach**: This is **not** the default approach. Rely on broker-level security (TLS, permissions) and strict data minimization first. Application-level payload encryption would only be considered for extremely sensitive data elements if other protections are deemed insufficient.

## 4. Securing Event Consumers

While the User Service is the publisher, the overall security of the eventing system also depends on secure consumers.

*   **Authenticated and Authorized Consumers**: As mentioned, consumers must authenticate to RabbitMQ and be authorized via permissions to read from specific queues bound to exchanges.
*   **Input Validation**: Consumers should validate the structure and data types of incoming event payloads, even if they trust the source. This protects against malformed events or unexpected changes if schema enforcement is not perfect.
*   **Principle of Least Privilege**: Consumers should only process events and data they legitimately need for their function.

## 5. Audit Logging of Event Publication

*   The User Service should log the fact that an event has been published (e.g., `messageId`, `messageType`, exchange, routing key). This is for internal auditing of the User Service's own actions.
*   Avoid logging the full event payload in general application logs if it contains PII. Sensitive payload details should only go to dedicated, secured audit log systems if required for compliance or security investigations.

## 6. Event Authenticity and Integrity (Advanced)

For very high-security scenarios, ensuring that an event was indeed published by the User Service and has not been tampered with can be achieved by signing events.

*   **Mechanism**: The User Service could sign the event payload (or the entire `StandardMessage<T>` envelope) using a private key. Consumers with the corresponding public key could verify the signature.
*   **Complexity**: Adds significant overhead (key management, signing/verification process).
*   **User Service Approach**: Not implemented by default. This is an advanced security measure for specific, high-assurance requirements.

By focusing on strong broker security (authentication, authorization, TLS), minimizing sensitive data in payloads, and ensuring proper access controls, the User Service aims to maintain a secure event publishing mechanism with RabbitMQ.
