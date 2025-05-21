# Order Service Bulk Operations API

## 1. Overview

The Bulk Operations API allows administrators and authorized systems to perform operations on multiple orders simultaneously. These endpoints are designed for operational efficiency in scenarios like batch processing, warehouse operations, and order fulfillment.

## 2. Bulk Status Update

### Endpoint: `POST /api/v1/orders/bulk/status-update`

Updates the status of multiple orders in a single request.

#### Request Schema

```json
{
  "orderIds": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d",
    "7c9e6679-7425-40de-944b-e07fc1f90ae7"
  ],
  "newStatus": "SHIPPED",
  "statusMetadata": {
    "carrier": "UPS",
    "shippingMethod": "EXPRESS",
    "trackingInfo": [
      {
        "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "trackingNumber": "1Z999AA10123456784",
        "estimatedDeliveryDate": "2023-11-26T12:00:00Z"
      },
      {
        "orderId": "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d",
        "trackingNumber": "1Z999AA10123456785",
        "estimatedDeliveryDate": "2023-11-27T12:00:00Z"
      },
      {
        "orderId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "trackingNumber": "1Z999AA10123456786",
        "estimatedDeliveryDate": "2023-11-26T12:00:00Z"
      }
    ]
  },
  "updateReason": "Batch fulfillment completed",
  "notifyCustomers": true,
  "operatedBy": "warehouse-system"
}
```

#### Response Schema

```json
{
  "success": true,
  "data": {
    "totalOrders": 3,
    "successfulUpdates": 2,
    "failedUpdates": 1,
    "results": [
      {
        "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "success": true,
        "status": "SHIPPED",
        "previousStatus": "READY_FOR_SHIPPING"
      },
      {
        "orderId": "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d",
        "success": true,
        "status": "SHIPPED",
        "previousStatus": "READY_FOR_SHIPPING"
      },
      {
        "orderId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "success": false,
        "status": "CANCELLED",
        "previousStatus": "CANCELLED",
        "errorMessage": "Cannot update status: Order is already cancelled"
      }
    ],
    "eventsPublished": [
      {
        "type": "order.shipped",
        "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
      },
      {
        "type": "order.shipped",
        "orderId": "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d"
      }
    ]
  },
  "meta": {
    "timestamp": "2023-11-25T14:35:27.123Z",
    "batchId": "batch-1637854527123"
  }
}
```

#### Status Codes

| Status Code | Description                                     |
| ----------- | ----------------------------------------------- |
| 200         | Updates processed (may include partial success) |
| 400         | Bad request (invalid status transition or data) |
| 401         | Unauthorized access                             |
| 403         | Forbidden (insufficient permissions)            |
| 500         | Server error                                    |

#### Implementation Details

```typescript
@Post('/bulk/status-update')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin', 'shipping', 'system')
async bulkStatusUpdate(
  @Body() bulkUpdateDto: BulkOrderStatusUpdateDto,
  @Request() req
): Promise<BulkStatusUpdateResponseDto> {
  try {
    this.logger.log(`Processing bulk status update for ${bulkUpdateDto.orderIds.length} orders`);

    // Generate a unique batch ID for tracing
    const batchId = `batch-${Date.now()}`;

    // Process each order individually but within a transaction
    const results = await this.orderService.bulkStatusUpdate(
      bulkUpdateDto,
      req.user.id,
      batchId
    );

    return {
      success: true,
      data: {
        totalOrders: bulkUpdateDto.orderIds.length,
        successfulUpdates: results.filter(r => r.success).length,
        failedUpdates: results.filter(r => !r.success).length,
        results,
        eventsPublished: results
          .filter(r => r.success)
          .map(r => ({
            type: `order.${bulkUpdateDto.newStatus.toLowerCase()}`,
            orderId: r.orderId
          }))
      },
      meta: {
        timestamp: new Date().toISOString(),
        batchId
      }
    };
  } catch (error) {
    this.logger.error(
      `Error in bulk status update: ${error.message}`,
      error.stack
    );

    if (error instanceof BadRequestException) {
      throw error;
    }

    throw new InternalServerErrorException(
      'Failed to process bulk status update. Please try again later.'
    );
  }
}
```

## 3. Bulk Order Query

### Endpoint: `POST /api/v1/orders/bulk/query`

Retrieves details for multiple orders in a single request.

#### Request Schema

```json
{
  "orderIds": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d",
    "7c9e6679-7425-40de-944b-e07fc1f90ae7"
  ],
  "includeItems": true,
  "includeShippingDetails": true,
  "includeBillingDetails": false,
  "includeStatusHistory": false
}
```

#### Response Schema

```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "orderNumber": "ORD-12345678",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "SHIPPED",
        "totalAmount": 149.99,
        "createdAt": "2023-11-21T12:34:56.789Z",
        "updatedAt": "2023-11-23T14:35:12.487Z",
        "items": [
          {
            "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
            "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
            "productName": "Wireless Headphones",
            "quantity": 2,
            "unitPrice": 59.99,
            "totalPrice": 119.98
          },
          {
            "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
            "productName": "USB-C Charging Cable",
            "quantity": 1,
            "unitPrice": 20.01,
            "totalPrice": 20.01
          }
        ],
        "shippingDetails": {
          "recipientName": "Jane Doe",
          "shippingAddressLine1": "456 Park Ave",
          "shippingAddressLine2": "Apt 7C",
          "shippingCity": "New York",
          "shippingState": "NY",
          "shippingPostalCode": "10022",
          "shippingCountry": "US",
          "shippingMethod": "EXPRESS",
          "carrier": "UPS",
          "trackingNumber": "1Z999AA10123456784",
          "estimatedDeliveryDate": "2023-11-26T12:00:00Z"
        }
      },
      {
        "id": "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d",
        "orderNumber": "ORD-12345679",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "SHIPPED",
        "totalAmount": 79.99,
        "createdAt": "2023-11-21T14:10:24.123Z",
        "updatedAt": "2023-11-23T14:35:12.487Z",
        "items": [
          {
            "id": "f1e2d3c4-b5a6-4c5d-8e7f-6a5b4c3d2e1f",
            "productId": "5ca474d7-1234-5678-9abc-def012345678",
            "productName": "Portable Bluetooth Speaker",
            "quantity": 1,
            "unitPrice": 79.99,
            "totalPrice": 79.99
          }
        ],
        "shippingDetails": {
          "recipientName": "Jane Doe",
          "shippingAddressLine1": "456 Park Ave",
          "shippingAddressLine2": "Apt 7C",
          "shippingCity": "New York",
          "shippingState": "NY",
          "shippingPostalCode": "10022",
          "shippingCountry": "US",
          "shippingMethod": "EXPRESS",
          "carrier": "UPS",
          "trackingNumber": "1Z999AA10123456785",
          "estimatedDeliveryDate": "2023-11-27T12:00:00Z"
        }
      }
    ],
    "notFound": ["7c9e6679-7425-40de-944b-e07fc1f90ae7"]
  },
  "meta": {
    "timestamp": "2023-11-25T14:40:12.345Z"
  }
}
```

#### Status Codes

| Status Code | Description                          |
| ----------- | ------------------------------------ |
| 200         | Query processed                      |
| 400         | Bad request (invalid request format) |
| 401         | Unauthorized access                  |
| 403         | Forbidden (insufficient permissions) |
| 500         | Server error                         |

#### Implementation Details

```typescript
@Post('/bulk/query')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin', 'customer-service', 'shipping', 'system')
async bulkOrderQuery(
  @Body() queryDto: BulkOrderQueryDto,
  @Request() req
): Promise<BulkOrderQueryResponseDto> {
  try {
    this.logger.log(`Processing bulk query for ${queryDto.orderIds.length} orders`);

    // Check authorization - customer service and admins can view any order
    // Shipping can only view orders in certain statuses
    if (!req.user.roles.includes('admin') && !req.user.roles.includes('customer-service')) {
      // For shipping roles, ensure they're only querying relevant orders
      await this.authorizationService.verifyBulkOrderAccess(queryDto.orderIds, req.user);
    }

    // Execute the bulk query with projection options
    const { orders, notFound } = await this.orderService.bulkFindOrders(
      queryDto.orderIds,
      {
        includeItems: queryDto.includeItems,
        includeShippingDetails: queryDto.includeShippingDetails,
        includeBillingDetails: queryDto.includeBillingDetails,
        includeStatusHistory: queryDto.includeStatusHistory
      }
    );

    // Map orders to DTOs based on requested fields
    const mappedOrders = orders.map(order =>
      this.mapper.toResponseDto(order, queryDto)
    );

    return {
      success: true,
      data: {
        orders: mappedOrders,
        notFound
      },
      meta: {
        timestamp: new Date().toISOString()
      }
    };
  } catch (error) {
    this.logger.error(
      `Error in bulk order query: ${error.message}`,
      error.stack
    );

    if (error instanceof ForbiddenException) {
      throw error;
    }

    if (error instanceof BadRequestException) {
      throw error;
    }

    throw new InternalServerErrorException(
      'Failed to process bulk order query. Please try again later.'
    );
  }
}
```

## 4. Bulk Cancel Orders

### Endpoint: `POST /api/v1/orders/bulk/cancel`

Cancels multiple orders in a single request.

#### Request Schema

```json
{
  "orderIds": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d",
    "7c9e6679-7425-40de-944b-e07fc1f90ae7"
  ],
  "cancellationReason": "INVENTORY_SHORTAGE",
  "cancellationNote": "Products unavailable due to warehouse issue",
  "notifyCustomers": true,
  "processRefunds": true,
  "operatedBy": "admin-system"
}
```

#### Response Schema

```json
{
  "success": true,
  "data": {
    "totalOrders": 3,
    "successfulCancellations": 2,
    "failedCancellations": 1,
    "results": [
      {
        "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "success": true,
        "previousStatus": "PROCESSING",
        "refundInitiated": true,
        "refundAmount": 149.99
      },
      {
        "orderId": "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d",
        "success": true,
        "previousStatus": "PENDING_PAYMENT",
        "refundInitiated": false,
        "refundAmount": null
      },
      {
        "orderId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "success": false,
        "errorMessage": "Cannot cancel order: Order is already DELIVERED"
      }
    ],
    "eventsPublished": [
      {
        "type": "order.cancelled",
        "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
      },
      {
        "type": "order.cancelled",
        "orderId": "a1b2c3d4-e5f6-4a5b-9c0d-1e2f3a4b5c6d"
      }
    ]
  },
  "meta": {
    "timestamp": "2023-11-25T15:12:33.789Z",
    "batchId": "cancel-batch-1637856753789"
  }
}
```

#### Status Codes

| Status Code | Description                          |
| ----------- | ------------------------------------ |
| 200         | Cancellation requests processed      |
| 400         | Bad request (invalid request format) |
| 401         | Unauthorized access                  |
| 403         | Forbidden (insufficient permissions) |
| 500         | Server error                         |

#### Implementation Details

```typescript
@Post('/bulk/cancel')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin', 'system')
async bulkCancelOrders(
  @Body() cancelDto: BulkOrderCancelDto,
  @Request() req
): Promise<BulkCancelResponseDto> {
  try {
    this.logger.log(`Processing bulk cancellation for ${cancelDto.orderIds.length} orders`);

    // Generate a unique batch ID for tracing
    const batchId = `cancel-batch-${Date.now()}`;

    // Process cancellations (handles refunds if needed)
    const results = await this.orderService.bulkCancelOrders(
      cancelDto,
      req.user.id,
      batchId
    );

    // Prepare event publishing summary
    const eventsPublished = results
      .filter(r => r.success)
      .map(r => ({
        type: "order.cancelled",
        orderId: r.orderId
      }));

    return {
      success: true,
      data: {
        totalOrders: cancelDto.orderIds.length,
        successfulCancellations: results.filter(r => r.success).length,
        failedCancellations: results.filter(r => !r.success).length,
        results,
        eventsPublished
      },
      meta: {
        timestamp: new Date().toISOString(),
        batchId
      }
    };
  } catch (error) {
    this.logger.error(
      `Error in bulk order cancellation: ${error.message}`,
      error.stack
    );

    if (error instanceof BadRequestException) {
      throw error;
    }

    throw new InternalServerErrorException(
      'Failed to process bulk cancellation. Please try again later.'
    );
  }
}
```

## 5. Rate Limiting and Security

### 5.1. Rate Limits

| Endpoint                   | User Role        | Rate Limit             |
| -------------------------- | ---------------- | ---------------------- |
| `POST /bulk/status-update` | admin            | 10 requests per minute |
|                            | shipping         | 5 requests per minute  |
|                            | system           | 30 requests per minute |
| `POST /bulk/query`         | admin            | 20 requests per minute |
|                            | customer-service | 10 requests per minute |
|                            | shipping         | 10 requests per minute |
|                            | system           | 50 requests per minute |
| `POST /bulk/cancel`        | admin            | 5 requests per minute  |
|                            | system           | 10 requests per minute |

### 5.2. Batch Size Limits

| Operation     | Maximum Orders Per Request |
| ------------- | -------------------------- |
| Status Update | 100                        |
| Query         | 50                         |
| Cancel        | 25                         |

### 5.3. Security Considerations

1. **Authorization**: Access is restricted to specific roles with appropriate permissions
2. **Audit Logging**: All bulk operations are logged with user ID, timestamp, and affected order IDs
3. **Concurrency Control**: Operations use database transactions to maintain data integrity
4. **Event Consistency**: Failed operations do not publish events to avoid inconsistent state
5. **DDOS Protection**: Rate limits and batch size restrictions prevent abuse

## 6. Validation Logic

### 6.1. Bulk Status Update Validation

- All order IDs must be valid UUIDs
- Maximum 100 orders per request
- Target status must be a valid status value
- Status transitions must be valid according to order status workflow
- If status-specific metadata is required (e.g., tracking info for SHIPPED), it must be provided
- If tracking information is provided, each tracking entry must reference an order ID in the request

### 6.2. Bulk Query Validation

- All order IDs must be valid UUIDs
- Maximum 50 orders per request
- At least one inclusion parameter must be true
- User must have appropriate permissions for requested data

### 6.3. Bulk Cancel Validation

- All order IDs must be valid UUIDs
- Maximum 25 orders per request
- Cancellation reason must be one of the predefined values
- Orders must be in a cancellable state according to business rules
- Refund processing option must align with order payment status

## 7. Business Logic Considerations

### 7.1. Transaction Management

All bulk operations use database transactions to ensure data consistency. If an operation on a single order fails:

1. For status updates and cancellations, the transaction for that specific order is rolled back
2. Other orders in the batch continue to be processed
3. The response includes details of both successful and failed operations

### 7.2. Event Publishing

For each successful order update, the appropriate event is published:

1. Status updates trigger specific events like `order.shipped`, `order.delivered`, etc.
2. Cancellations trigger `order.cancelled` events
3. Events include all necessary context based on the operation type
4. Failed operations do not publish events to prevent inconsistent downstream systems

### 7.3. Notifications

If `notifyCustomers` is set to true:

1. Email/SMS notifications are sent to affected customers
2. Notifications are sent asynchronously after the API response
3. Notification failures are logged but do not affect the API response
4. Notification templates are selected based on the operation type

## 8. References

- [Order Status Workflow](../../02-data-model-setup/04-order-status-entity.md)
- [Order Entity Model](../../02-data-model-setup/01-order-entity.md)
- [Notification Service Integration](../../06-integration-points/02-notification-service-integration.md)
- [Payment Service Integration](../../06-integration-points/01-payment-service-integration.md)
- [Inventory Service Integration](../../06-integration-points/03-inventory-service-integration.md)
