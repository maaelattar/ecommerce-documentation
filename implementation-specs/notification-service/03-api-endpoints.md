# Notification Service - API Endpoints

## 1. Overview

The Notification Service primarily operates by consuming events from other microservices. However, it may expose a limited set of internal (service-to-service) or administrative API endpoints for specific functionalities.

These APIs are not intended for general public consumption by end-users or client applications. Client applications typically interact with other services (like User Service for preference management, or an Admin Portal frontend), which then might trigger actions that result in this service sending notifications.

All APIs exposed by the Notification Service must be secured, typically using JWT-based authentication and authorization mechanisms provided by the `@ecommerce-platform/auth-client-utils` shared library, ensuring only authorized internal services or admin tools can access them.

## 2. Potential API Endpoints

The following are potential API endpoints. The necessity and exact specification of these will be determined by concrete use cases and administrative requirements.

### 2.1. Administrative Endpoints

These endpoints would be used by an internal admin portal or CLI tools.

*   **`POST /admin/notifications/send-test`**
    *   **Description**: Sends a test notification to a specified recipient via a chosen channel and template. Useful for verifying provider integrations and template rendering.
    *   **Request Body**: `{ "channel": "EMAIL" | "SMS", "recipient": "test@example.com" | "+1234567890", "templateId": "template-name-or-id", "context": { "variable": "value" } }`
    *   **Responses**:
        *   `202 ACCEPTED`: Test notification request accepted for processing.
        *   `400 BAD REQUEST`: Invalid request parameters.
        *   `401 UNAUTHORIZED`: Missing or invalid authentication.
        *   `403 FORBIDDEN`: Insufficient permissions.
*   **`GET /admin/notifications/logs`**
    *   **Description**: Retrieves a paginated list of notification logs, with filtering options (e.g., by recipient, channel, status, date range).
    *   **Query Parameters**: `page`, `limit`, `userId`, `channel`, `status`, `startDate`, `endDate`.
    *   **Responses**:
        *   `200 OK`: Returns a list of notification logs.
        *   `401 UNAUTHORIZED`, `403 FORBIDDEN`.
*   **`GET /admin/notifications/logs/{logId}`**
    *   **Description**: Retrieves details for a specific notification log entry.
    *   **Responses**:
        *   `200 OK`.
        *   `404 NOT FOUND`.
        *   `401 UNAUTHORIZED`, `403 FORBIDDEN`.
*   **`GET /admin/templates`**
    *   **Description**: Lists available notification templates.
    *   **Responses**: `200 OK`.
*   **`POST /admin/templates`**
    *   **Description**: Creates a new notification template.
    *   **Request Body**: Template content, name, channel, etc.
    *   **Responses**: `201 CREATED`.
*   **`PUT /admin/templates/{templateId}`**
    *   **Description**: Updates an existing notification template.
    *   **Responses**: `200 OK`.
*   **`GET /admin/preferences/user/{userId}`**
    *   **Description**: Retrieves communication preferences for a specific user.
    *   **Responses**: `200 OK`.
*   **`PUT /admin/preferences/user/{userId}`**
    *   **Description**: Updates communication preferences for a specific user (admin override).
    *   **Request Body**: Preference settings.
    *   **Responses**: `200 OK`.

### 2.2. Internal Service Endpoints (Use with Caution)

While event-driven communication is preferred, very specific, synchronous use cases might warrant an internal API. These should be rare.

*   **`POST /internal/notifications/trigger-immediate` (Hypothetical)**
    *   **Description**: Allows another authenticated internal service to trigger an immediate, high-priority notification. This bypasses the standard event queue and should be used sparingly for critical, synchronous needs where event processing latency is unacceptable.
    *   **Considerations**: This endpoint introduces tighter coupling. The use case must be strong to justify it over event-based triggers.
    *   **Request Body**: Similar to `/admin/notifications/send-test` but with stricter validation and context for a known internal event type.
    *   **Responses**: `202 ACCEPTED` or `200 OK` if a direct status is returned (less likely for notifications).

### 2.3. Provider Callback Endpoints (Webhooks)

These are not APIs *exposed* by the Notification Service for other services to call, but rather endpoints *hosted* by the Notification Service for external notification providers to send delivery status updates.

*   **`POST /callbacks/email/aws-ses`**
    *   **Description**: Receives webhook callbacks from AWS SES (e.g., delivery, bounce, complaint).
    *   **Security**: Must be secured (e.g., AWS SNS subscription confirmation, signature verification).
*   **`POST /callbacks/sms/twilio`**
    *   **Description**: Receives webhook callbacks from Twilio for SMS status updates.
    *   **Security**: Twilio request validation (signature verification).

## 3. API Design Principles

*   **RESTful**: APIs should follow REST principles where applicable.
*   **Stateless**: Each API request should contain all information needed to process it.
*   **Standard HTTP Status Codes**: Use appropriate HTTP status codes for responses.
*   **Consistent Error Formatting**: Use a standard error response format, potentially from `@ecommerce-platform/nestjs-core-utils`.
*   **Versioning**: API versioning (e.g., `/v1/admin/...`) if significant breaking changes are anticipated.

## 4. OpenAPI Specification

The detailed OpenAPI specification for these endpoints will be maintained in:
`./openapi/openapi.yaml`

This file will provide formal definitions for request/response schemas, parameters, and authentication methods.
