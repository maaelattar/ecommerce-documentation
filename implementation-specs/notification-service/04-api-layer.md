# Notification Service: API Layer Specification

## 1. Introduction

*   **Primary Mode of Operation**: The Notification Service is designed to be primarily **event-driven**. It listens to events published by other microservices (e.g., User Service, Order Service) and triggers notifications accordingly. This aligns with **ADR-002 (Event-Driven Architecture)**.

*   **Purpose of Exposed APIs**: While its core functionality is event-triggered, the Notification Service may expose a minimal set of synchronous RESTful API endpoints for specific purposes, such as:
    *   Administrative tasks or manual operational interventions.
    *   Allowing authorized systems or personnel to trigger ad-hoc notifications.
    *   Checking the status of specific notification dispatches (if tracked).
    *   Facilitating testing and debugging.

*   **Initial API Scope**: For the initial version of the Notification Service, the API surface will be kept minimal. Complex functionalities like direct template management or runtime channel configuration via API will be deferred. Template management will be detailed in `09-template-management.md` and likely handled via deployment or direct data manipulation in early phases. Channel configuration will adhere to **ADR-016 (Configuration Management)**, using secure deployment practices.

## 2. API Endpoints

The following API endpoints are proposed for the Notification Service. All endpoints are subject to authentication and authorization as per **ADR-005 (Authentication and Authorization)** and **ADR-019 (API Gateway and Service Mesh Security)**.

### 2.1. Manually Trigger a Notification

*   **Endpoint**: `POST /api/v1/notifications/send`
*   **Purpose**: Allows an authorized administrator or another designated service to manually trigger a specific notification. This can be useful for testing notification templates, resending a failed notification after manual correction of an issue, or for ad-hoc operational communications.
*   **Request Body**:
    ```json
    {
      "recipientDetails": { // Option 1: Provide direct contact info
        "emailAddress": "user@example.com", // Required if email channel is used
        "phoneNumber": "+1234567890" // Required if sms channel is used
        // Other channel-specific identifiers like device tokens could be added here
      },
      // "userId": "user-uuid-123", // Option 2: Provide userId to look up contact details & preferences
      "templateName": "custom-admin-alert", // Name/key of the notification template to use
      "data": { // Data to be injected into the template
        "subject": "Important System Update",
        "message": "The system will undergo maintenance tonight at 2 AM.",
        "callToActionLink": "https://status.example.com"
      },
      "channels": ["email"] // Array specifying which channels to use (e.g., "email", "sms", "push")
    }
    ```
    *   **Note**: The service should support either direct `recipientDetails` or a `userId` (if a user lookup mechanism is integrated). If `userId` is provided, the service would attempt to fetch the user's contact information and notification preferences.
*   **Responses**:
    *   `202 Accepted`: The notification request has been successfully queued for processing. The response body might include a unique `notificationRequestId` if the system generates one for tracking.
        ```json
        {
          "message": "Notification request queued successfully.",
          "notificationRequestId": "notif-req-uuid-789" // Optional tracking ID
        }
        ```
    *   `400 Bad Request`: Invalid request payload (e.g., missing required fields, invalid email/phone format, template not found, invalid channel specified). See `ErrorResponse` schema in OpenAPI spec.
    *   `401 Unauthorized`: Authentication credentials missing or invalid.
    *   `403 Forbidden`: Authenticated user/service does not have permission to trigger notifications.
    *   `500 Internal Server Error`: An unexpected error occurred while processing the request.

### 2.2. Check Notification Status (Conditional)

This endpoint is contingent upon the implementation of the `NotificationAttemptRepository` (detailed in `02-data-model-setup.md` and `03-core-service-components.md`) which would log individual notification attempts and their statuses.

*   **Endpoint**: `GET /api/v1/notifications/status/{notificationAttemptId}`
*   **Purpose**: Allows an authorized user or service to check the delivery status of a specific notification attempt that was previously logged by the system.
*   **Parameters**:
    *   `notificationAttemptId` (path parameter): The unique identifier of the notification attempt (likely a UUID, returned from the `/send` endpoint or logged internally).
*   **Responses**:
    *   `200 OK`: Successfully retrieved the notification attempt status.
        ```json
        {
          "notificationAttemptId": "notif-attempt-uuid-123",
          "status": "SENT", // e.g., PENDING, SENT, FAILED, DELIVERED
          "channel": "email",
          "recipient": "user@example.com",
          "sentAt": "2023-10-27T10:30:00Z", // Timestamp when sent/attempted
          "providerResponse": { /* Optional: sanitized response from provider */ },
          "errorDetails": null // Or error message if status is FAILED
        }
        ```
    *   `401 Unauthorized`: Authentication credentials missing or invalid.
    *   `403 Forbidden`: Authenticated user/service does not have permission to view notification statuses.
    *   `404 Not Found`: No notification attempt found with the given ID.
    *   `500 Internal Server Error`: An unexpected error occurred.

## 3. API Design Principles

*   **RESTful Principles**: The API will adhere to RESTful design principles where applicable, using standard HTTP methods (POST, GET).
*   **Standard HTTP Status Codes**: The API will use standard HTTP status codes to indicate the outcome of requests (e.g., 202, 400, 401, 403, 404, 500).
*   **JSON Payload**: Request and response bodies will use JSON.
*   **Authentication**: All API endpoints will be protected and require authentication. This will likely involve JWT Bearer tokens for users/admins or OAuth2 client credentials for service-to-service communication, as defined in **ADR-005 (Authentication and Authorization)**.
*   **Authorization**: Role-based access control (RBAC) or scope-based authorization will be implemented to ensure that only authorized principals (users, services, administrators) can access specific endpoints. For example, triggering manual notifications might be restricted to admin roles or specific service accounts.
*   **Error Handling**: Error responses will follow a standardized structure, as will be defined in the OpenAPI specification (`10-openapi-specification.md`), including a `correlationId` for traceability.
*   **API Gateway**: These endpoints will be exposed via the platform's API Gateway, which can handle cross-cutting concerns like rate limiting, request validation, and further security enforcement, as per **ADR-006 (API Gateway Usage)** and **ADR-019 (API Gateway and Service Mesh Security)**.

## 4. Decision on API Exposure for Initial Version

For the **initial version (MVP)** of the Notification Service:

*   The `POST /api/v1/notifications/send` endpoint **will be implemented**. This provides essential functionality for testing, manual intervention, and ad-hoc operational needs.
*   The `GET /api/v1/notifications/status/{notificationAttemptId}` endpoint **will be implemented if and only if** the `NotificationAttemptRepository` for detailed status logging is also part of the initial scope (as per `02-data-model-setup.md`). If detailed status tracking is deferred, this endpoint will also be deferred.
*   **API-driven template management** (e.g., `/templates/...`) is **deferred** for the initial version. Template creation and updates will be handled through deployment processes or direct data manipulation (e.g., seeding templates in the database or managing them in a version-controlled file store that the service reads from). This will be further elaborated in `09-template-management.md`.
*   **API-driven configuration viewing/updating** (e.g., `/config/channels`) is **deferred**. Channel configurations (API keys, etc.) will be managed via environment variables and secure deployment practices as per **ADR-016**. Monitoring of channel health will be done through operational metrics and logging, not a runtime API endpoint.

This approach keeps the initial API surface of the Notification Service lean and focused on core operational needs, while acknowledging its primary role as an event-driven service. Future iterations may expand the API based on evolving requirements.
The OpenAPI specification for these chosen endpoints will be detailed in `10-openapi-specification.md`.
