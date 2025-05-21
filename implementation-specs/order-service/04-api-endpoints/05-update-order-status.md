# Update Order Status API Endpoint

## 1. Overview

This document specifies the API endpoint for updating the status of an existing order. This endpoint enables order status progression through the order lifecycle, from creation to fulfillment and delivery. Status updates are restricted based on role permissions and valid status transitions.

## 2. Endpoint Specification

| Method | Endpoint                        | Description         |
| ------ | ------------------------------- | ------------------- |
| PATCH  | /api/v1/orders/{orderId}/status | Update order status |

### 2.1. Request Format

#### Path Parameters

| Parameter | Type | Required | Description             |
| --------- | ---- | -------- | ----------------------- |
| orderId   | UUID | Yes      | Unique order identifier |

#### Headers

| Header           | Type   | Required | Description                       |
| ---------------- | ------ | -------- | --------------------------------- |
| Authorization    | String | Yes      | Bearer token for authentication   |
| Content-Type     | String | Yes      | application/json                  |
| Accept           | String | No       | application/json (default)        |
| X-Correlation-ID | String | No       | Unique ID for distributed tracing |

#### Request Body

```json
{
  "status": "SHIPPED",
  "statusId": 8,
  "reason": "Order has been shipped via UPS",
  "metadata": {
    "carrier": "UPS",
    "trackingNumber": "1Z999AA10123456784",
    "estimatedDeliveryDate": "2023-12-01T12:00:00Z"
  }
}
```

### 2.2. Response Format

#### Success Response (200 OK)

##### Headers

| Header           | Type   | Description                                  |
| ---------------- | ------ | -------------------------------------------- |
| Content-Type     | String | application/json                             |
| X-Correlation-ID | String | Same correlation ID from request if provided |

##### Response Body

```json
{
  "success": true,
  "data": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "SHIPPED",
    "statusId": 8,
    "statusDescription": "Order has been shipped to the customer",
    "previousStatus": "PROCESSING",
    "previousStatusId": 6,
    "updatedAt": "2023-11-23T14:35:12.487Z",
    "updatedBy": "shipping-service",
    "metadata": {
      "carrier": "UPS",
      "trackingNumber": "1Z999AA10123456784",
      "estimatedDeliveryDate": "2023-12-01T12:00:00Z"
    },
    "statusHistory": [
      {
        "timestamp": "2023-11-21T15:27:30.123Z",
        "statusName": "PENDING_PAYMENT",
        "statusId": 1,
        "changedBy": "SYSTEM"
      },
      {
        "timestamp": "2023-11-21T15:28:45.367Z",
        "statusName": "PAYMENT_PROCESSING",
        "statusId": 2,
        "previousStatusName": "PENDING_PAYMENT",
        "previousStatusId": 1,
        "changedBy": "PAYMENT_SERVICE"
      },
      {
        "timestamp": "2023-11-21T15:29:12.589Z",
        "statusName": "PAYMENT_COMPLETED",
        "statusId": 4,
        "previousStatusName": "PAYMENT_PROCESSING",
        "previousStatusId": 2,
        "changedBy": "PAYMENT_SERVICE"
      },
      {
        "timestamp": "2023-11-21T15:30:00.123Z",
        "statusName": "AWAITING_FULFILLMENT",
        "statusId": 5,
        "previousStatusName": "PAYMENT_COMPLETED",
        "previousStatusId": 4,
        "changedBy": "ORDER_PROCESSOR"
      },
      {
        "timestamp": "2023-11-22T10:14:32.874Z",
        "statusName": "PROCESSING",
        "statusId": 6,
        "previousStatusName": "AWAITING_FULFILLMENT",
        "previousStatusId": 5,
        "changedBy": "FULFILLMENT_SERVICE"
      },
      {
        "timestamp": "2023-11-23T14:35:12.487Z",
        "statusName": "SHIPPED",
        "statusId": 8,
        "previousStatusName": "PROCESSING",
        "previousStatusId": 6,
        "changedBy": "shipping-service",
        "metadata": {
          "carrier": "UPS",
          "trackingNumber": "1Z999AA10123456784",
          "estimatedDeliveryDate": "2023-12-01T12:00:00Z"
        }
      }
    ]
  },
  "meta": {
    "timestamp": "2023-11-23T14:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

#### Error Responses

##### 400 Bad Request

```json
{
  "success": false,
  "error": {
    "code": "INVALID_STATUS",
    "message": "Invalid status value: status must be one of the defined order statuses",
    "details": {
      "allowedStatuses": [
        "PENDING_PAYMENT",
        "PAYMENT_PROCESSING",
        "PAYMENT_FAILED",
        "PAYMENT_COMPLETED",
        "AWAITING_FULFILLMENT",
        "PROCESSING",
        "ON_HOLD",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED",
        "REFUNDED",
        "PARTIALLY_REFUNDED"
      ]
    }
  },
  "meta": {
    "timestamp": "2023-11-23T14:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

##### 401 Unauthorized

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2023-11-23T14:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

##### 403 Forbidden

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to update the status of this order"
  },
  "meta": {
    "timestamp": "2023-11-23T14:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

##### 404 Not Found

```json
{
  "success": false,
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "Order with ID f47ac10b-58cc-4372-a567-0e02b2c3d479 not found"
  },
  "meta": {
    "timestamp": "2023-11-23T14:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

##### 409 Conflict

```json
{
  "success": false,
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "Cannot transition from DELIVERED to PROCESSING",
    "details": {
      "currentStatus": "DELIVERED",
      "requestedStatus": "PROCESSING",
      "allowedTransitions": ["REFUNDED", "PARTIALLY_REFUNDED"]
    }
  },
  "meta": {
    "timestamp": "2023-11-23T14:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

##### 422 Unprocessable Entity

```json
{
  "success": false,
  "error": {
    "code": "MISSING_REQUIRED_METADATA",
    "message": "Status SHIPPED requires trackingNumber in metadata",
    "details": {
      "requiredFields": ["carrier", "trackingNumber"]
    }
  },
  "meta": {
    "timestamp": "2023-11-23T14:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

##### 500 Internal Server Error

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred"
  },
  "meta": {
    "timestamp": "2023-11-23T14:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

## 3. Request Processing

### 3.1. Authorization Rules

1. **Administrator Access**:

   - Users with ADMIN role can update any order status
   - Users with CUSTOMER_SERVICE role can update specific status transitions (e.g., cannot mark as REFUNDED)

2. **Partner Limited Access**:

   - Fulfillment partners can update order status for fulfillment-related statuses only:
     - AWAITING_FULFILLMENT → PROCESSING
     - PROCESSING → SHIPPED
     - SHIPPED → DELIVERED
   - Payment partners can update payment-related statuses only:
     - PENDING_PAYMENT → PAYMENT_PROCESSING
     - PAYMENT_PROCESSING → PAYMENT_COMPLETED
     - PAYMENT_PROCESSING → PAYMENT_FAILED
     - Various statuses → REFUNDED/PARTIALLY_REFUNDED

3. **Customer Access**:
   - Regular customers cannot directly update order status
   - Cancellation requests from customers go through a separate endpoint

### 3.2. Status Transition Rules

The status transitions follow the rules defined in the [Order Status Entity](../02-data-model-setup/05-order-status-entity.md) specification:

1. **Valid Transitions**:

   - PENDING_PAYMENT → PAYMENT_PROCESSING, CANCELLED
   - PAYMENT_PROCESSING → PAYMENT_COMPLETED, PAYMENT_FAILED, CANCELLED
   - PAYMENT_FAILED → PAYMENT_PROCESSING, CANCELLED
   - PAYMENT_COMPLETED → AWAITING_FULFILLMENT, CANCELLED, REFUNDED
   - AWAITING_FULFILLMENT → PROCESSING, ON_HOLD, CANCELLED, REFUNDED
   - PROCESSING → SHIPPED, ON_HOLD, CANCELLED, REFUNDED
   - ON_HOLD → PROCESSING, AWAITING_FULFILLMENT, CANCELLED, REFUNDED
   - SHIPPED → DELIVERED, RETURNED
   - DELIVERED → RETURNED, REFUNDED, PARTIALLY_REFUNDED
   - RETURNED → REFUNDED, PARTIALLY_REFUNDED
   - CANCELLED → No further transitions allowed
   - REFUNDED → No further transitions allowed
   - PARTIALLY_REFUNDED → REFUNDED

2. **Terminal States**:
   - CANCELLED, REFUNDED, and PARTIALLY_REFUNDED are considered terminal states
   - Orders in terminal states require special handling for any further changes

### 3.3. Metadata Requirements

Different status updates require specific metadata to be provided:

1. **SHIPPED Status**:

   - Required fields: carrier, trackingNumber
   - Optional fields: estimatedDeliveryDate, shippingNotes

2. **DELIVERED Status**:

   - Required fields: deliveryDate
   - Optional fields: signedBy, deliveryNotes

3. **PAYMENT_COMPLETED Status**:

   - Required fields: paymentId, paymentMethod
   - Optional fields: paymentNotes

4. **REFUNDED/PARTIALLY_REFUNDED Status**:
   - Required fields: refundId, refundAmount
   - Optional fields: refundReason, refundNotes

### 3.4. Processing Steps

1. **Request Validation**:

   - Validate order exists
   - Validate authorization
   - Validate status value is a valid order status
   - Validate required metadata for specific status changes

2. **Transition Validation**:

   - Check if the requested transition is allowed from the current status
   - Validate business rules for specific transitions

3. **Status Update**:

   - Update order status in the database
   - Create a status history log entry in DynamoDB
   - Include metadata and reason in the history entry

4. **Side Effects**:

   - Execute relevant side effects based on status change
   - Update inventory if status change affects inventory (e.g., cancellation)
   - Update payment status if needed

5. **Event Publishing**:

   - Publish OrderStatusChanged event
   - Include relevant metadata for downstream systems

6. **Response Assembly**:
   - Retrieve updated order with status details
   - Include status history in the response
   - Format response according to API response structure

## 4. Service Interactions

The update order status endpoint interacts with the following services:

1. **Inventory Service**:

   - Status changes to CANCELLED, RETURNED: Release reserved inventory
   - Status changes to SHIPPED: Confirm inventory deduction

2. **Payment Service**:

   - Status changes to CANCELLED: Initiate refund if payment was processed
   - Status changes to REFUNDED: Process refund for the order

3. **Notification Service**:

   - Send status update notification to customer
   - Send internal notifications to relevant teams
   - Notification content is tailored to the specific status change

4. **Analytics Service**:
   - Send order status data for tracking and reporting
   - Update conversion metrics based on status changes

## 5. Performance Considerations

1. **Status History Management**:

   - Store order status history in DynamoDB for efficient querying
   - Use GSI on order ID for fast retrieval
   - Consider time-to-live (TTL) for very old status records

2. **Concurrent Updates**:

   - Implement optimistic locking to prevent concurrent status updates
   - Use version numbers or timestamps for concurrency control

3. **Event Processing**:

   - Process side effects asynchronously where possible
   - Use event-driven architecture for status change propagation
   - Set up retry mechanisms for failed downstream service calls

4. **Caching Strategy**:
   - Invalidate caches when status changes
   - Consider caching allowed transitions matrix for fast lookup

## 6. Implementation Example

```typescript
@Patch(':orderId/status')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('ADMIN', 'CUSTOMER_SERVICE', 'FULFILLMENT_PARTNER', 'PAYMENT_PARTNER')
async updateOrderStatus(
  @Param('orderId') orderId: string,
  @Body() updateStatusDto: UpdateOrderStatusDto,
  @Req() request,
  @User() user: UserDto
): Promise<OrderStatusResponseDto> {
  const correlationId = request.headers['x-correlation-id'] || uuidv4();
  this.logger.log(`Updating order status for order ${orderId}`, {
    correlationId,
    userId: user.id,
    requestedStatus: updateStatusDto.status
  });

  try {
    // Validate UUID format
    if (!isUUID(orderId, 4)) {
      throw new BadRequestException({
        code: 'INVALID_ORDER_ID',
        message: 'Invalid order ID format'
      });
    }

    // Retrieve order with current status
    const order = await this.orderService.findOrderById(orderId, {
      relations: ['status']
    });

    if (!order) {
      throw new NotFoundException({
        code: 'ORDER_NOT_FOUND',
        message: `Order with ID ${orderId} not found`
      });
    }

    // Check authorization for status update
    this.checkStatusUpdateAuthorization(user, order, updateStatusDto.status);

    // Validate status transition
    const currentStatus = order.status.name;
    const requestedStatus = updateStatusDto.status;

    const isValidTransition = await this.orderStatusService.isValidTransition(
      currentStatus,
      requestedStatus
    );

    if (!isValidTransition) {
      const allowedTransitions = await this.orderStatusService.getAllowedTransitions(currentStatus);

      throw new ConflictException({
        code: 'INVALID_STATUS_TRANSITION',
        message: `Cannot transition from ${currentStatus} to ${requestedStatus}`,
        details: {
          currentStatus,
          requestedStatus,
          allowedTransitions
        }
      });
    }

    // Validate required metadata for status
    this.validateStatusMetadata(requestedStatus, updateStatusDto.metadata);

    // Update order status
    const updatedOrder = await this.orderService.updateOrderStatus(
      orderId,
      updateStatusDto.status,
      updateStatusDto.statusId,
      updateStatusDto.reason,
      updateStatusDto.metadata,
      user.id
    );

    // Execute side effects based on status change
    await this.executeStatusChangeEffects(
      order,
      updatedOrder,
      updateStatusDto.metadata
    );

    // Publish event
    await this.eventPublisher.publish('order.status.changed', {
      orderId: updatedOrder.id,
      userId: updatedOrder.userId,
      previousStatus: currentStatus,
      newStatus: requestedStatus,
      reason: updateStatusDto.reason,
      metadata: updateStatusDto.metadata,
      changedBy: user.id,
      timestamp: new Date().toISOString()
    });

    // Get status history
    const statusHistory = await this.orderStatusLogRepository.getStatusLogsByOrderId(orderId);

    // Return response
    return {
      success: true,
      data: {
        id: updatedOrder.id,
        status: updatedOrder.status.name,
        statusId: updatedOrder.status.id,
        statusDescription: updatedOrder.status.description,
        previousStatus: currentStatus,
        previousStatusId: order.status.id,
        updatedAt: updatedOrder.updatedAt,
        updatedBy: user.id,
        metadata: updateStatusDto.metadata,
        statusHistory
      },
      meta: {
        timestamp: new Date().toISOString(),
        requestId: correlationId
      }
    };
  } catch (error) {
    this.logger.error(`Error updating order status: ${error.message}`, {
      correlationId,
      stack: error.stack
    });

    if (error instanceof HttpException) {
      throw error;
    }

    throw new InternalServerErrorException({
      code: 'INTERNAL_SERVER_ERROR',
      message: 'An unexpected error occurred'
    });
  }
}

private checkStatusUpdateAuthorization(user: UserDto, order: Order, requestedStatus: string): void {
  // Full access for admins
  if (user.role === 'ADMIN') {
    return;
  }

  // Customer service has limited privileges
  if (user.role === 'CUSTOMER_SERVICE') {
    const restrictedStatuses = ['REFUNDED', 'PARTIALLY_REFUNDED'];
    if (restrictedStatuses.includes(requestedStatus)) {
      throw new ForbiddenException({
        code: 'FORBIDDEN',
        message: `Customer service cannot set order to ${requestedStatus} status`
      });
    }
    return;
  }

  // Fulfillment partner restrictions
  if (user.role === 'FULFILLMENT_PARTNER') {
    const allowedTransitions = [
      { from: 'AWAITING_FULFILLMENT', to: 'PROCESSING' },
      { from: 'PROCESSING', to: 'SHIPPED' },
      { from: 'SHIPPED', to: 'DELIVERED' }
    ];

    const isAllowed = allowedTransitions.some(
      t => t.from === order.status.name && t.to === requestedStatus
    );

    if (!isAllowed) {
      throw new ForbiddenException({
        code: 'FORBIDDEN',
        message: 'Fulfillment partner cannot perform this status transition'
      });
    }
    return;
  }

  // Payment partner restrictions
  if (user.role === 'PAYMENT_PARTNER') {
    const allowedStatuses = [
      'PAYMENT_PROCESSING', 'PAYMENT_COMPLETED', 'PAYMENT_FAILED',
      'REFUNDED', 'PARTIALLY_REFUNDED'
    ];

    if (!allowedStatuses.includes(requestedStatus)) {
      throw new ForbiddenException({
        code: 'FORBIDDEN',
        message: 'Payment partner cannot set this status'
      });
    }
    return;
  }

  // Default: no access
  throw new ForbiddenException({
    code: 'FORBIDDEN',
    message: 'You do not have permission to update the status of this order'
  });
}

private validateStatusMetadata(status: string, metadata: Record<string, any>): void {
  const metadataRequirements = {
    'SHIPPED': ['carrier', 'trackingNumber'],
    'DELIVERED': ['deliveryDate'],
    'PAYMENT_COMPLETED': ['paymentId', 'paymentMethod'],
    'REFUNDED': ['refundId', 'refundAmount'],
    'PARTIALLY_REFUNDED': ['refundId', 'refundAmount']
  };

  const requiredFields = metadataRequirements[status];
  if (requiredFields) {
    const missingFields = requiredFields.filter(field => !metadata || !metadata[field]);

    if (missingFields.length > 0) {
      throw new UnprocessableEntityException({
        code: 'MISSING_REQUIRED_METADATA',
        message: `Status ${status} requires ${missingFields.join(', ')} in metadata`,
        details: {
          requiredFields
        }
      });
    }
  }
}

private async executeStatusChangeEffects(
  oldOrder: Order,
  newOrder: Order,
  metadata: Record<string, any>
): Promise<void> {
  const oldStatus = oldOrder.status.name;
  const newStatus = newOrder.status.name;

  // Handle inventory side effects
  if (newStatus === 'CANCELLED' || newStatus === 'RETURNED') {
    // Release reserved inventory
    await this.inventoryService.releaseInventory(oldOrder.items);
  }

  // Handle payment side effects
  if (newStatus === 'CANCELLED' &&
      ['PAYMENT_COMPLETED', 'AWAITING_FULFILLMENT', 'PROCESSING'].includes(oldStatus)) {
    // Initiate refund for cancelled order
    await this.paymentService.initiateRefund(oldOrder.id, oldOrder.totalAmount);
  }

  // Handle shipping side effects
  if (newStatus === 'SHIPPED' && metadata.trackingNumber) {
    // Update shipping records
    await this.shippingService.recordShipment(
      newOrder.id,
      metadata.carrier,
      metadata.trackingNumber
    );
  }

  // Send notifications
  await this.notificationService.sendOrderStatusNotification(
    newOrder.userId,
    newOrder.id,
    oldStatus,
    newStatus,
    metadata
  );
}
```

## 7. References

- [Order Service API Index](./00-api-index.md)
- [Order Entity Specification](../02-data-model-setup/01-order-entity.md)
- [Order Status Entity Specification](../02-data-model-setup/05-order-status-entity.md)
- [Order Status Log Entity Specification](../02-data-model-setup/06-order-status-log-entity.md)
- [ADR-002-rest-api-standards-openapi](../../../architecture/adr/ADR-002-rest-api-standards-openapi.md)
- [ADR-007-event-driven-architecture](../../../architecture/adr/ADR-007-event-driven-architecture.md)
