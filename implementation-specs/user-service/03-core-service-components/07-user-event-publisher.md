# 07 - UserEventPublisher

The `UserEventPublisher` service is responsible for publishing domain events related to user management and activities. These events can be consumed by other microservices within the platform (e.g., Search Service, Order Service, Notification Service) or by internal components for auditing, analytics, or triggering further workflows.

This service might be a standalone component or its functionality could be integrated directly into the services that originate the events (e.g., `UserService`, `AuthService` methods could publish their own events).

## 1. Responsibilities

*   **Event Formulation**: Constructing event payloads with relevant data for different user-related occurrences.
*   **Event Publishing**: Sending these events to a message broker (e.g., Kafka, RabbitMQ, AWS SNS/SQS) or an event bus.
*   **Standardization**: Ensuring events follow a consistent schema and naming convention across the User Service.
*   **Resilience (Optional)**: Implementing retry mechanisms or dead-letter queue (DLQ) strategies for event publishing if the message broker is temporarily unavailable, though often this is handled by the messaging library itself.

## 2. Key Events Published

Examples of events that the `UserEventPublisher` (or the User Service in general) would publish:

*   **`UserCreatedEvent` / `UserRegisteredEvent`**: When a new user account is successfully created.
    *   Payload: `userId`, `email`, `username` (if applicable), `registrationTimestamp`, `status`.
*   **`UserUpdatedEvent`**: When core user information (excluding sensitive data like password changes if handled separately) is updated.
    *   Payload: `userId`, changed fields (e.g., `email`, `username`), `updateTimestamp`.
*   **`UserProfileUpdatedEvent`**: When a user's profile information (name, contact, preferences) changes.
    *   Payload: `userId`, changed profile fields, `updateTimestamp`.
*   **`UserAddressAddedEvent` / `UserAddressUpdatedEvent` / `UserAddressDeletedEvent`**: When a user's address is managed.
    *   Payload: `userId`, `addressId`, address details, `timestamp`.
*   **`UserPasswordChangedEvent`**: When a user successfully changes their password.
    *   Payload: `userId`, `passwordChangeTimestamp` (NO password data).
*   **`UserPasswordResetRequestedEvent`**: When a user initiates a password reset process.
    *   Payload: `userId`, `email`, `requestTimestamp`.
*   **`UserLoggedInEvent`**: When a user successfully logs in.
    *   Payload: `userId`, `loginTimestamp`, `ipAddress`, `userAgent`.
*   **`UserLoginFailedEvent`**: When a login attempt fails.
    *   Payload: `email` (or `username`), `attemptTimestamp`, `ipAddress`, `reasonForFailure`.
*   **`UserEmailVerificationRequestedEvent`**: When an email verification is initiated.
    *   Payload: `userId`, `email`, `requestTimestamp`.
*   **`UserEmailVerifiedEvent`**: When a user successfully verifies their email.
    *   Payload: `userId`, `email`, `verificationTimestamp`.
*   **`UserAccountStatusChangedEvent`**: When a user's account status changes (e.g., activated, suspended, banned, deleted).
    *   Payload: `userId`, `newStatus`, `previousStatus`, `changeTimestamp`, `reason` (if applicable).
*   **`UserRoleAssignedEvent` / `UserRoleRemovedEvent`**: When roles are assigned to or removed from a user.
    *   Payload: `userId`, `roleId` (or `roleName`), `timestamp`.
*   **`MfaEnabledEvent` / `MfaDisabledEvent`**: When MFA status changes for a user.
    *   Payload: `userId`, `mfaType` (if applicable), `timestamp`.

## 3. Key Methods (Conceptual NestJS Example)

This example assumes a message broker like Kafka, using `@nestjs/microservices`.

```typescript
import { Injectable, Inject } from '@nestjs/common';
import { ClientKafka } from '@nestjs/microservices';
import { User } from '../entities/user.entity';
import { UserProfile } from '../entities/user-profile.entity';
import { Address } from '../entities/address.entity';
import { Role } from '../entities/role.entity';

// Define event topic names or patterns
export const USER_EVENTS_TOPIC = 'user.events';

// Define event types (could be an enum or string constants)
export enum UserEventType {
  USER_CREATED = 'user.created',
  USER_UPDATED = 'user.updated',
  USER_PROFILE_UPDATED = 'user.profile.updated',
  USER_LOGGED_IN = 'user.loggedin',
  // ... other event types
}

@Injectable()
export class UserEventPublisher {
  constructor(
    @Inject('USER_MICROSERVICE_CLIENT') // Kafka client injected via DI
    private readonly kafkaClient: ClientKafka,
  ) {}

  // Ensure client is connected before publishing (can be handled in onModuleInit)
  async onModuleInit() {
    await this.kafkaClient.connect();
  }

  private async publishEvent(eventType: UserEventType, payload: any): Promise<void> {
    try {
      // The key for Kafka messages could be userId for partitioning
      const key = payload.userId || Date.now().toString(); 
      await this.kafkaClient.emit(USER_EVENTS_TOPIC, { 
          key: key,
          value: {
            type: eventType,
            timestamp: new Date().toISOString(),
            data: payload,
          }
      }).toPromise();
      console.log(`Event ${eventType} published for user ${payload.userId || 'system'}`);
    } catch (error) {
      console.error(`Failed to publish event ${eventType}:`, error);
      // Implement retry logic or DLQ if necessary, or rely on KafkaJS resilience
    }
  }

  async publishUserCreated(user: User): Promise<void> {
    await this.publishEvent(UserEventType.USER_CREATED, { 
        userId: user.id, 
        email: user.email, 
        status: user.status 
    });
  }

  async publishUserUpdated(user: User, changes: Partial<User>): Promise<void> {
    await this.publishEvent(UserEventType.USER_UPDATED, { 
        userId: user.id, 
        updatedFields: Object.keys(changes) 
    });
  }

  async publishUserProfileUpdated(profile: UserProfile): Promise<void> {
    await this.publishEvent(UserEventType.USER_PROFILE_UPDATED, { 
        userId: profile.user.id, // Assuming profile entity has user relation
        profileId: profile.id 
    });
  }

  async publishUserLoggedIn(userId: string, ipAddress: string, userAgent: string): Promise<void> {
    await this.publishEvent(UserEventType.USER_LOGGED_IN, { 
        userId, 
        ipAddress, 
        userAgent 
    });
  }
  
  // ... other specific event publishing methods for each event type
  // e.g., publishPasswordChanged, publishAccountStatusChanged, etc.
}
```

## 4. Interactions

*   **Core Services (`UserService`, `AuthService`, `UserProfileService`, `RoleService`)**: These services call methods on `UserEventPublisher` after successfully completing an operation that warrants an event (e.g., after a user is created, `UserService` calls `userEventPublisher.publishUserCreated()`).
*   **Message Broker (e.g., Kafka, RabbitMQ)**: `UserEventPublisher` interacts directly with the message broker to send events.
*   **Event Consumers (Other Microservices)**: Services like Search, Notification, Order, Analytics, etc., subscribe to the relevant topics/exchanges on the message broker to receive and process these user events.

## 5. Event Design Considerations

*   **Granularity**: Events should be granular enough to be meaningful but not so chatty that they overwhelm the system.
*   **Idempotency**: Consumers should be designed to handle duplicate events gracefully, as message brokers can sometimes deliver an event more than once.
*   **Schema & Versioning**: Define clear schemas for event payloads (e.g., using Avro, Protobuf, or JSON Schema). Plan for schema evolution and versioning to avoid breaking consumers as events change over time.
*   **Payload Content**: Include enough information in the event payload for most consumers to act without needing to immediately call back to the User Service for more details (to reduce coupling and improve performance). However, avoid including overly sensitive data unless strictly necessary and secured.
*   **Event Sourcing**: While this component is an event *publisher*, if the User Service itself uses Event Sourcing as its persistence mechanism, the nature of event publishing would be inherent to its design.

## 6. Security Considerations

*   **Sensitive Data in Events**: Be extremely cautious about including PII or other sensitive information in event payloads. If necessary, use techniques like tokenization or ensure the event bus is secured and only authorized consumers can access specific topics.
*   **Event Authenticity/Integrity**: In high-security environments, consider signing events to ensure their authenticity and integrity, though this adds complexity.
*   **Access Control to Topics**: Ensure that only authorized services can publish to or consume from specific event topics/queues in the message broker.

## 7. Future Enhancements

*   **Dead Letter Queue (DLQ) Management**: Robust handling for events that cannot be published successfully after retries.
*   **Event Auditing/Logging**: Storing a log of all published events (or at least critical ones) for auditing and debugging purposes, separate from the main application logs.
*   **Schema Registry Integration**: For managing and validating event schemas (e.g., Confluent Schema Registry for Kafka).

`UserEventPublisher` plays a crucial role in a microservices architecture by enabling asynchronous communication and data propagation based on user-related activities, fostering loose coupling between services.
