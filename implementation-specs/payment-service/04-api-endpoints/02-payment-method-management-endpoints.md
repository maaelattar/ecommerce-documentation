# 02: Payment Method Management Endpoints

These endpoints allow authenticated users to manage their saved payment methods securely. All operations rely on gateway tokenization, meaning sensitive payment details are not directly handled by these backend endpoints.

## 1. Add Payment Method

*   **Endpoint**: `POST /v1/payment-methods`
*   **Purpose**: To allow a user to add and save a new payment method.
*   **Authentication**: Required (User context).
*   **Request Body**:
    ```json
    {
      "gateway": "STRIPE", // Or "PAYPAL", etc. Specifies which gateway to use.
      "paymentMethodClientToken": "tok_xxxxxxxxxxxxxx" // Token obtained from client-side gateway SDK (e.g., Stripe.js, PayPal SDK after user enters details).
      "billingDetails": { // Optional, but recommended for fraud prevention and display
        "name": "Jane Doe",
        "addressLine1": "123 Main St",
        "addressLine2": "Apt 4B",
        "city": "Anytown",
        "state": "CA",
        "postalCode": "90210",
        "country": "US"
      },
      "isDefault": false // Optional: whether to set this as the default payment method
    }
    ```
*   **Success Response (201 Created)**:
    ```json
    {
      "paymentMethodId": "local-pm-uuid", // Internal ID for the saved payment method
      "userId": "user-uuid",
      "type": "CARD", // e.g., CARD, PAYPAL
      "gateway": "STRIPE",
      "gatewayPaymentMethodId": "pm_xxxxxxxxxxxxxx", // Gateway's token for the saved payment method
      "isDefault": false,
      "cardBrand": "Visa",
      "cardLastFour": "4242",
      "cardExpiryMonth": 12,
      "cardExpiryYear": 2025,
      "billingName": "Jane Doe",
      "status": "ACTIVE"
    }
    ```
*   **Error Responses**: `400 Bad Request` (e.g., invalid token, validation errors), `401 Unauthorized`, `403 Forbidden`, `500 Internal Server Error`.

## 2. List Payment Methods

*   **Endpoint**: `GET /v1/payment-methods`
*   **Purpose**: To retrieve a list of saved payment methods for the authenticated user.
*   **Authentication**: Required (User context).
*   **Query Parameters**:
    *   `type` (optional, e.g., `CARD`, `PAYPAL`): Filter by payment method type.
    *   `gateway` (optional, e.g., `STRIPE`): Filter by payment gateway.
*   **Success Response (200 OK)**:
    ```json
    {
      "data": [
        {
          "paymentMethodId": "local-pm-uuid-1",
          "type": "CARD",
          "gateway": "STRIPE",
          "gatewayPaymentMethodId": "pm_xxxxxxxxxxxxxx1",
          "isDefault": true,
          "cardBrand": "Visa",
          "cardLastFour": "4242",
          "cardExpiryMonth": 12,
          "cardExpiryYear": 2025,
          "billingName": "Jane Doe",
          "status": "ACTIVE"
        },
        {
          "paymentMethodId": "local-pm-uuid-2",
          "type": "PAYPAL", // Example if PayPal also tokenized
          "gateway": "PAYPAL",
          "gatewayPaymentMethodId": "paypal_token_abc",
          "isDefault": false,
          "billingName": "Jane Doe", // Could be PayPal account email or name
          "status": "ACTIVE"
        }
      ],
      "pagination": {
        "totalItems": 2,
        "currentPage": 1,
        "pageSize": 10,
        "totalPages": 1
      }
    }
    ```
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `500 Internal Server Error`.

## 3. Set Default Payment Method

*   **Endpoint**: `PUT /v1/payment-methods/{paymentMethodId}/default`
*   **Purpose**: To set a specific saved payment method as the default for the authenticated user.
*   **Authentication**: Required (User context, user must own the payment method).
*   **Success Response (200 OK)**:
    ```json
    {
      "paymentMethodId": "local-pm-uuid-updated",
      "isDefault": true,
      // ... other payment method details ...
    }
    ```
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden` (if not owner), `404 Not Found`, `500 Internal Server Error`.

## 4. Delete Payment Method

*   **Endpoint**: `DELETE /v1/payment-methods/{paymentMethodId}`
*   **Purpose**: To remove a saved payment method for the authenticated user.
*   **Authentication**: Required (User context, user must own the payment method).
*   **Success Response (204 No Content)**
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden` (if not owner), `404 Not Found`, `500 Internal Server Error`.

## 5. Update Payment Method Details (Limited)

*   **Endpoint**: `PATCH /v1/payment-methods/{paymentMethodId}`
*   **Purpose**: To update certain details of a payment method, such as billing address or expiry date (if supported by the gateway without re-tokenization).
*   **Authentication**: Required (User context, user must own the payment method).
*   **Request Body**:
    ```json
    {
      "billingDetails": { // Only fields to update
        "name": "Jane M. Doe",
        "postalCode": "90211"
      },
      "cardExpiryMonth": 1, // If expiry updated
      "cardExpiryYear": 2026
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    {
      "paymentMethodId": "local-pm-uuid",
      // ... updated payment method details ...
    }
    ```
*   **Error Responses**: `400 Bad Request` (e.g., update not supported by gateway, validation failed), `401`, `403`, `404`, `500`.
*   **Note**: Capabilities for updating are highly dependent on the payment gateway. Often, significant changes like a new card number require adding a new payment method and deleting the old one.

These endpoints provide a comprehensive interface for users to manage their payment preferences securely.
