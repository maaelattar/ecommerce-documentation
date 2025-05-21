# 01: Payment Initiation and Processing Endpoints

These endpoints are responsible for initiating new payments, processing them through gateways, and handling any subsequent actions required from the user or system.

## 1. Create Payment Intent

*   **Endpoint**: `POST /v1/payments/intents`
*   **Purpose**: To create a payment intent, which represents an intention to collect payment from a customer. This is often the first step in a payment flow, especially with gateways like Stripe.
*   **Authentication**: Required (User or service context).
*   **Idempotency**: Supported via `Idempotency-Key` header.
*   **Request Body**:
    ```json
    {
      "orderId": "uuid",
      "amount": 10050, // In cents or smallest currency unit
      "currency": "USD", // ISO 4217
      "paymentMethodTypes": ["card", "paypal"], // Optional: types allowed by client, gateway default otherwise
      "captureMethod": "automatic", // or "manual"
      "description": "Payment for Order #12345",
      "metadata": {
        "userId": "user-uuid",
        "cartId": "cart-uuid"
      },
      "customerGatewayId": "cus_xxxxxxxxxxxxxx", // Optional: Existing gateway customer ID
      "setupFutureUsage": "off_session" // Optional: For saving payment method, e.g., Stripe's setup_future_usage
    }
    ```
*   **Success Response (201 Created)**:
    ```json
    {
      "paymentId": "local-payment-uuid",
      "gatewayPaymentIntentId": "pi_xxxxxxxxxxxxxx", // Gateway's payment intent ID
      "clientSecret": "pi_xxxxxxxxxxxxxx_secret_yyyyyyyyyyy", // If needed by client (e.g., Stripe JS SDK)
      "status": "REQUIRES_PAYMENT_METHOD", // Or other initial status from gateway
      "amount": 10050,
      "currency": "USD",
      "nextAction": null // Or details if further action like redirect is needed immediately
    }
    ```
*   **Error Responses**: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `429 Too Many Requests`, `500 Internal Server Error`.

## 2. Confirm Payment Intent / Process Payment

This endpoint might be used if the client confirms the payment intent with a payment method token, or if the payment is processed directly.

*   **Endpoint**: `POST /v1/payments/intents/{intentId}/confirm` or `POST /v1/payments` (if creating and processing in one go with a source token)
*   **Purpose**: To confirm a payment intent with a payment method or to process a direct charge.
*   **Authentication**: Required.
*   **Request Body (for confirming an intent)**:
    ```json
    {
      "paymentMethodId": "pm_xxxxxxxxxxxxxx", // Gateway payment method ID or token
      "returnUrl": "https://ecommercesite.com/payment/complete" // For redirect-based flows
    }
    ```
*   **Request Body (for direct charge with source)**:
    ```json
    {
        "orderId": "uuid",
        "amount": 10050,
        "currency": "USD",
        "sourceToken": "tok_visa", // Gateway source token (e.g., from Stripe.js, not a saved PM)
        "description": "Direct charge for Order #12345",
        "capture": true, // true for sale, false for auth-only
        "metadata": { "userId": "user-uuid" }
    }
    ```
*   **Success Response (200 OK or 202 Accepted if asynchronous)**:
    ```json
    {
      "paymentId": "local-payment-uuid",
      "status": "SUCCEEDED", // or "PROCESSING", "REQUIRES_ACTION"
      "gatewayTransactionId": "ch_xxxxxxxxxxxxxx", // If charge is direct and successful
      "nextAction": { // If further action is needed (e.g., 3DS redirect)
        "type": "redirect_to_url",
        "redirect_to_url": {
          "url": "https://stripe.com/pay/cs_test_a1...",
          "return_url": "https://ecommercesite.com/payment/complete"
        }
      },
      "lastErrorMessage": null
    }
    ```
*   **Error Responses**: As above.

## 3. Retrieve Payment Status / Details

*   **Endpoint**: `GET /v1/payments/{paymentId}`
*   **Purpose**: To retrieve the current status and details of a specific payment.
*   **Authentication**: Required (User owning the payment or admin/service).
*   **Success Response (200 OK)**:
    ```json
    {
      "paymentId": "local-payment-uuid",
      "orderId": "order-uuid",
      "amount": 10050,
      "currency": "USD",
      "status": "SUCCEEDED", // Current status
      "paymentGateway": "STRIPE",
      "gatewayPaymentIntentId": "pi_xxxxxxxxxxxxxx",
      "transactions": [
        {
          "transactionId": "local-txn-uuid",
          "type": "SALE", // or AUTHORIZATION, CAPTURE
          "status": "SUCCEEDED",
          "amount": 10050,
          "gatewayTransactionId": "ch_xxxxxxxxxxxxxx",
          "processedAt": "2023-10-27T10:20:30Z"
        }
      ],
      "createdAt": "2023-10-27T10:15:00Z",
      "updatedAt": "2023-10-27T10:20:35Z"
    }
    ```
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`.

## 4. Capture Pre-Authorized Payment

*   **Endpoint**: `POST /v1/payments/{paymentId}/capture`
*   **Purpose**: To capture funds for a payment that was previously authorized but not captured.
*   **Authentication**: Required (Typically service or admin role).
*   **Request Body**:
    ```json
    {
      "amountToCapture": 10050 // Optional, defaults to full authorized amount if not provided
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    {
      "paymentId": "local-payment-uuid",
      "status": "SUCCEEDED",
      "gatewayTransactionId": "ch_xxxxxxxx_captured", // ID of the capture transaction
      "amountCaptured": 10050
    }
    ```
*   **Error Responses**: `400 Bad Request` (e.g., payment not in authorizable state, amount exceeds authorized), `401`, `403`, `404`, `500`.

## 5. Void Pre-Authorized Payment

*   **Endpoint**: `POST /v1/payments/{paymentId}/void`
*   **Purpose**: To void a previously authorized payment that has not been captured.
*   **Authentication**: Required (Typically service or admin role).
*   **Success Response (200 OK)**:
    ```json
    {
      "paymentId": "local-payment-uuid",
      "status": "CANCELED" // Or VOIDED depending on internal status mapping
    }
    ```
*   **Error Responses**: `400 Bad Request` (e.g., payment already captured or not authorized), `401`, `403`, `404`, `500`.

These endpoints form the core of initiating and managing the active lifecycle of payments.
