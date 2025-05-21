# 04: Transaction History Endpoints

These endpoints provide access to the history of payments and individual financial transactions. Access controls are critical to ensure users can only see their own relevant history, while administrators or specific service roles might have broader access for support and auditing.

## 1. List Payments for User/Order

This endpoint is effectively covered by `GET /v1/payments/{paymentId}` if a `paymentId` is known, or a more general list endpoint if needed.

*   **Endpoint**: `GET /v1/payments` (Potentially, if a general list is needed beyond single payment retrieval)
*   **Purpose**: To list payments, filterable by user, order, or other criteria.
*   **Authentication**: Required (User context for their own payments, Admin/Service for broader queries).
*   **Query Parameters (Examples)**:
    *   `orderId` (string): Filter payments associated with a specific order.
    *   `userId` (string): Filter payments associated with a specific user (only accessible by that user or admin).
    *   `status` (string, e.g., `SUCCEEDED`, `FAILED`): Filter by payment status.
    *   `dateFrom` (ISO8601 datetime): Payments created from this date.
    *   `dateTo` (ISO8601 datetime): Payments created up to this date.
    *   `limit` (integer): For pagination.
    *   `offset` (integer): For pagination.
*   **Success Response (200 OK)**:
    ```json
    {
      "data": [
        {
          "paymentId": "local-payment-uuid-1",
          "orderId": "order-uuid-A",
          "amount": 10050,
          "currency": "USD",
          "status": "SUCCEEDED",
          "paymentGateway": "STRIPE",
          "createdAt": "2023-10-27T10:15:00Z",
          "updatedAt": "2023-10-27T10:20:35Z"
        },
        {
          "paymentId": "local-payment-uuid-2",
          "orderId": "order-uuid-B",
          "amount": 7500,
          "currency": "USD",
          "status": "FAILED",
          "paymentGateway": "STRIPE",
          "lastErrorMessage": "Insufficient funds.",
          "createdAt": "2023-10-28T14:00:00Z",
          "updatedAt": "2023-10-28T14:00:10Z"
        }
        // ... other payment objects
      ],
      "pagination": {
        "totalItems": 50,
        "currentPage": 1,
        "pageSize": 10,
        "totalPages": 5
      }
    }
    ```
*   **Error Responses**: `400 Bad Request` (invalid filters), `401 Unauthorized`, `403 Forbidden`, `500 Internal Server Error`.
*   **Note**: The `GET /v1/payments/{paymentId}` endpoint (defined in `01-payment-initiation-processing-endpoints.md`) already provides detailed transaction history for a *specific* payment. This endpoint (`GET /v1/payments`) would be for a broader listing.

## 2. List Transactions for a Specific Payment

This functionality is typically included in the response of `GET /v1/payments/{paymentId}` as a nested array of transactions. No separate endpoint is usually needed unless a very large number of transactions per payment is expected, requiring separate pagination for transactions.

If a separate endpoint were needed:
*   **Endpoint**: `GET /v1/payments/{paymentId}/transactions`
*   **Purpose**: To list all individual financial transactions (authorize, capture, refund, void) associated with a specific payment.
*   **Authentication**: Required (User owning the payment or admin/service).
*   **Query Parameters (Examples for pagination of transactions)**:
    *   `limit` (integer).
    *   `offset` (integer).
*   **Success Response (200 OK)**:
    ```json
    {
      "data": [
        {
          "transactionId": "local-txn-uuid-1",
          "type": "AUTHORIZATION",
          "status": "SUCCEEDED",
          "amount": 10050,
          "currency": "USD",
          "gatewayTransactionId": "auth_xxxxxxxxxxxxxx",
          "processedAt": "2023-10-27T10:18:00Z"
        },
        {
          "transactionId": "local-txn-uuid-2",
          "type": "CAPTURE",
          "status": "SUCCEEDED",
          "amount": 10050,
          "currency": "USD",
          "gatewayTransactionId": "ch_xxxxxxxxxxxxxx",
          "parentTransactionId": "local-txn-uuid-1",
          "processedAt": "2023-10-27T10:20:30Z"
        }
        // ... other transaction objects
      ],
      "pagination": {
        "totalItems": 2,
        "currentPage": 1,
        "pageSize": 10,
        "totalPages": 1
      }
    }
    ```
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (if paymentId doesn't exist), `500 Internal Server Error`.

Providing clear and accessible transaction history is important for user transparency and for administrative auditing and support functions.
