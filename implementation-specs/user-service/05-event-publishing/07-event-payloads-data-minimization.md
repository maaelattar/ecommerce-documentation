# 07 - Event Payloads and Data Minimization

This document provides guidelines for designing event payloads published by the User Service, with a focus on providing sufficient information for consumers while adhering to data minimization principles, especially concerning Personally Identifiable Information (PII).

## 1. General Payload Design Principles

*   **Sufficiency**: Event payloads should contain enough information for most common consumers to act without immediately needing to make a synchronous callback to the User Service for more details. This promotes loose coupling and resilience.
    *   Example: A `UserRegisteredEventV1` should include key identifiers like `userId` and `email`, and perhaps initial status, so a Notification Service can send a welcome/verification email without a callback.
*   **Common Envelope**: All events utilize the common event envelope defined in `01-event-publishing-mechanism.md`, which includes `eventId`, `eventType`, `eventTimestamp`, `sourceService`, `correlationId` (optional), and `version`.
*   **Clarity**: Field names within the `payload` object should be clear, descriptive, and use a consistent casing (e.g., camelCase).
*   **Standard Data Types**: Use standard data types (strings, numbers, booleans, ISO 8601 for timestamps) that are easily serializable to JSON.
*   **Avoid Nulls vs. Omitted Fields**: Decide on a consistent strategy. Generally, if a field is optional and not present, omitting it from the payload is cleaner than sending `fieldName: null`.

## 2. Data Minimization and PII

*   **Principle of Least Information**: Only include data in the event payload that is essential for the known downstream use cases or for general event understanding.
*   **PII Scrutiny**: Be extremely cautious when including PII in event payloads. PII in events can spread sensitive data across multiple systems and storage, increasing risk.
    *   **Avoid Highly Sensitive PII**: Never include passwords, MFA secrets, raw payment details, or government ID numbers in event payloads.
    *   **Consider Identifiers vs. Full Data**: Sometimes, only an identifier (`userId`, `addressId`) is needed. Consumers can then fetch more details if they are authorized and require them. This is the "thin event" approach.
    *   **Justification for PII**: If PII (e.g., email, name, parts of an address) is included, there must be a clear justification based on direct consumer needs that outweigh the risks.
    *   Example: `UserLoggedInEventV1` might include `ipAddress` for security monitoring, but `UserProfileUpdatedEventV1` might only list *which* fields changed rather than including all old/new PII values if consumers don't broadly need them.
*   **Tokenization/Anonymization**: For analytics or less trusted consumers, consider if PII can be tokenized, pseudonymized, or if events can be aggregated/anonymized before reaching them.

## 3. "Fat Events" vs. "Thin Events"

*   **Fat Events**: Contain a rich set of data, including many attributes of the affected aggregate. This reduces the need for consumers to call back to the originating service.
    *   **Pros**: Improved consumer autonomy, reduced load on the publishing service from callbacks.
    *   **Cons**: Larger event sizes, data duplication, higher risk if PII is included, consumers might get more data than they need.
    *   **User Service Approach**: Lean towards fatter events for common, non-sensitive attributes that most consumers would likely need (e.g., `UserRegisteredEventV1` including `userId`, `email`, `status`). For `UserAddressAddedEventV1`, including the `fullAddress` object is generally good practice.

*   **Thin Events (Notification Events)**: Contain minimal data, often just identifiers and an indication of what changed. Consumers must call back to the User Service API to get full details.
    *   **Pros**: Smaller event sizes, less PII in transit/at rest in event logs, data is always fetched fresh (no stale event data).
    *   **Cons**: Increased load on the User Service APIs, tighter coupling (consumers depend on API availability), potential for chatty interactions.
    *   **User Service Approach**: Use for highly sensitive changes or when the payload would be excessively large or complex. For example, a `SecuritySettingsChangedEventV1` might just note `userId` and that "MFA settings were modified" rather than detailing old/new MFA configurations in the event.

*   **Hybrid Approach**: The User Service will generally adopt a hybrid approach:
    *   Include essential identifiers in all events.
    *   Include common, non-sensitive attributes that are frequently needed by direct consumers.
    *   For updates (`UserUpdatedEventV1`, `UserProfileUpdatedEventV1`), indicate *which* fields changed. Optionally include new values for non-sensitive fields. Avoid old values unless critical for a specific, identified consumer pattern.
    *   Avoid embedding large, complex related objects if only their IDs are usually needed.

## 4. Specific Payload Examples

Refer to the detailed event documents for specific payload structures:
*   `02-user-account-events.md`
*   `03-user-profile-events.md`
*   `04-authentication-events.md`
*   `05-role-permission-events.md`

## 5. Payload Immutability

*   Once an event is published, its payload (and schema for that version) should be considered immutable. If changes are needed, a new event version should be created (`UserRegisteredEventV2`).

By carefully designing event payloads, the User Service can effectively communicate changes to the rest of the platform while managing data exposure and system coupling.
