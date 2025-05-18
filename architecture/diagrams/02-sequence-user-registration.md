```markdown
# Sequence Diagram: User Registration

Date: {{TIMESTAMP}}
Status: Draft

## Diagram

This sequence diagram illustrates the high-level flow of events when a new customer registers on the E-commerce Platform.

![User Registration Sequence](./sequence_user_registration.jpg)

## Participants

*   **Customer (Browser/App):** The end-user initiating the registration process.
*   **API Gateway:** The entry point for all client requests, routing them to the appropriate backend services.
*   **User Service:** Part of the Identity & Access Management Context, responsible for creating and managing user accounts.
*   **User DB:** The database storing user information.
*   **Message Broker:** (e.g., RabbitMQ, Kafka, AWS SQS) Facilitates asynchronous communication between services.
*   **Notification Service:** Part of the Notification Context, responsible for sending communications like welcome emails.

## Flow

1.  **POST /users (Register Request):** The Customer submits their registration details (e.g., email, password, name) to the API Gateway.
2.  **Forward Request:** The API Gateway forwards the registration request to the User Service.
3.  **Validate & Create User:** The User Service validates the input data and creates a new user record in the User DB.
4.  **User Record Created:** The User DB confirms the creation of the user record.
5.  **Publish UserRegistered Event:** The User Service publishes a `UserRegistered` event to the Message Broker. This allows other interested services to react to the new registration asynchronously.
6.  **Registration Success Response:** The User Service returns a success response (e.g., HTTP 201 Created) to the API Gateway.
7.  **Forward Response:** The API Gateway forwards the success response back to the Customer.
8.  **UserRegistered Event Consumed:** The Notification Service, subscribed to `UserRegistered` events, consumes the event from the Message Broker.
9.  **Send Welcome Email:** The Notification Service sends a welcome email to the newly registered Customer.

## Notes

*   Error handling and alternative flows (e.g., email already exists) are not detailed in this high-level diagram.
*   The exact mechanism of email delivery (direct SMTP, third-party service) by the Notification Service is abstracted.
```
