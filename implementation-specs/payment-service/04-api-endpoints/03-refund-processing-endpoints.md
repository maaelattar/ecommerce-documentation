# 03: Refund Processing Endpoints

These endpoints are used to initiate and manage the refund process for payments. Access to these endpoints is typically restricted to administrative users or specific service roles due to their financial implications.

## 1. Initiate Refund

*   **Endpoint**: `POST /v1/refunds`
*   **Purpose**: To initiate a refund for a previously successful payment.
*   **Authentication**: Required (Admin or authorized service role).
*   **Idempotency**: Supported via `Idempotency-Key` header.
*   **Request Body**:
    ```json
    {
      "paymentId": "local-payment-uuid", // The internal ID of the payment to be refunded
      "amount": 5025, // Amount to refund, in cents or smallest currency unit. Can be partial or full.
      "currency": "USD", // Must match the original payment currency
      "reason": "Customer request: product returned.", // Reason for the refund
      "metadata": {
        "initiatedByAdminId": "admin-user-uuid",
        "notes": "Customer called support to request refund."
      }
    }
    ```
*   **Success Response (202 Accepted)**: Indicates the refund request has been accepted and is being processed. Refunds are often asynchronous.
    ```json
    {
      "refundId": "local-refund-uuid",
      "paymentId": "local-payment-uuid",
      "amount": 5025,
      "currency": "USD",
      "status": "PENDING", // Or "PROCESSING"
      "reason": "Customer request: product returned.",
      "createdAt": "2023-10-27T11:00:00Z"
    }
    ```
*   **Error Responses**:
    *   `400 Bad Request`: Invalid input (e.g., amount exceeds refundable amount, payment not found or not in refundable state, currency mismatch).
    *   `401 Unauthorized`: Missing or invalid authentication.
    *   `403 Forbidden`: Authenticated user does not have permission to initiate refunds.
    *   `404 Not Found`: Original payment not found.
    *   `409 Conflict`: A refund for this specific scope/idempotency key is already in progress or completed.
    *   `500 Internal Server Error`: General server-side error or issue communicating with the payment gateway.

## 2. Retrieve Refund Status / Details

*   **Endpoint**: `GET /v1/refunds/{refundId}`
*   **Purpose**: To retrieve the current status and details of a specific refund.
*   **Authentication**: Required (Admin or authorized service role, or user who owns the original payment if refunds are user-visible).
*   **Success Response (200 OK)**:
    ```json
    {
      "refundId": "local-refund-uuid",
      "paymentId": "local-payment-uuid",
      "amount": 5025,
      "currency": "USD",
      "status": "SUCCEEDED", // Current status, e.g., PENDING, PROCESSING, SUCCEEDED, FAILED
      "reason": "Customer request: product returned.",
      "gatewayRefundId": "re_xxxxxxxxxxxxxx", // Gateway's refund ID, if available
      "gatewayStatus": "succeeded", // Status from the gateway
      "processedAt": "2023-10-27T11:05:00Z", // If SUCCEEDED
      "createdAt": "2023-10-27T11:00:00Z",
      "updatedAt": "2023-10-27T11:05:00Z",
      "metadata": {
        "initiatedByAdminId": "admin-user-uuid",
        "notes": "Customer called support to request refund."
      }
    }
    ```
*   **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`.

## 3. List Refunds

*   **Endpoint**: `GET /v1/refunds`
*   **Purpose**: To retrieve a list of refunds, typically with filtering capabilities.
*   **Authentication**: Required (Admin or authorized service role).
*   **Query Parameters (Examples)**:
    *   `paymentId` (string): Filter by the original payment ID.
    *   `status` (string, e.g., `PENDING`, `SUCCEEDED`, `FAILED`): Filter by refund status.
    *   `gateway` (string): Filter by the payment gateway used for the original payment.
    *   `dateFrom` (ISO8601 datetime): Filter refunds created from this date.
    *   `dateTo` (ISO8601 datetime): Filter refunds created up to this date.
    *   `limit` (integer): For pagination.
    *   `offset` (integer): For pagination.
*   **Success Response (200 OK)**:
    ```json
    {
      "data": [
        // Array of refund objects, similar to the GET /v1/refunds/{refundId} response
      ],
      "pagination": {
        "totalItems": 150,
        "currentPage": 1,
        "pageSize": 20,
        "totalPages": 8
      }
    }
    ```
*   **Error Responses**: `400 Bad Request` (invalid filter parameters), `401 Unauthorized`, `403 Forbidden`, `500 Internal Server Error`.

These refund processing endpoints provide necessary controls for managing post-payment financial adjustments, crucial for customer service and financial operations.
