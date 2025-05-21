# Update Order API Endpoint

## 1. Overview

This document specifies the API endpoint for updating an existing order. This endpoint allows for limited modifications to an order after it has been created, respecting business rules about which fields can be modified based on the current order status.

## 2. Endpoint Specification

| Method | Endpoint                 | Description                           |
| ------ | ------------------------ | ------------------------------------- |
| PATCH  | /api/v1/orders/{orderId} | Update an existing order's properties |

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
  "shippingDetails": {
    "recipientName": "Jane Doe",
    "shippingAddressLine1": "456 Park Ave",
    "shippingAddressLine2": "Apt 7C",
    "shippingCity": "New York",
    "shippingState": "NY",
    "shippingPostalCode": "10022",
    "shippingCountry": "US",
    "shippingMethod": "EXPRESS"
  },
  "billingDetails": {
    "billingAddressLine1": "456 Park Ave",
    "billingAddressLine2": "Apt 7C",
    "billingCity": "New York",
    "billingState": "NY",
    "billingPostalCode": "10022",
    "billingCountry": "US"
  },
  "notes": "Please leave package at front desk"
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
    "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "PENDING_PAYMENT",
    "statusId": 1,
    "statusDescription": "Order created, awaiting payment",
    "createdAt": "2023-11-21T15:27:30.123Z",
    "updatedAt": "2023-11-21T15:35:12.487Z",
    "totalAmount": 149.99,
    "subtotal": 139.99,
    "tax": 10.0,
    "currency": "USD",
    "promoCode": "SUMMER10",
    "discountAmount": 15.0,
    "notes": "Please leave package at front desk",
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
    "billingDetails": {
      "id": "71f0c4d9-53e7-4d92-9a7e-f401b2e3e45d",
      "paymentMethod": "CREDIT_CARD",
      "paymentId": "ch_3OBtP1CZ6qsJgndP0NZUQ1ZW",
      "billingAddressLine1": "456 Park Ave",
      "billingAddressLine2": "Apt 7C",
      "billingCity": "New York",
      "billingState": "NY",
      "billingPostalCode": "10022",
      "billingCountry": "US"
    },
    "shippingDetails": {
      "id": "1d2ca47d-8a7c-4b1a-b12c-0e99e252f295",
      "recipientName": "Jane Doe",
      "shippingAddressLine1": "456 Park Ave",
      "shippingAddressLine2": "Apt 7C",
      "shippingCity": "New York",
      "shippingState": "NY",
      "shippingPostalCode": "10022",
      "shippingCountry": "US",
      "shippingMethod": "EXPRESS",
      "shippingCost": 15.99,
      "estimatedDeliveryDate": "2023-11-24T12:00:00Z"
    }
  },
  "meta": {
    "timestamp": "2023-11-21T15:35:12.487Z",
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
    "code": "INVALID_REQUEST_BODY",
    "message": "Invalid request body: shippingMethod must be one of [STANDARD, EXPRESS, OVERNIGHT]",
    "details": {
      "fields": {
        "shippingDetails.shippingMethod": "Must be one of [STANDARD, EXPRESS, OVERNIGHT]"
      }
    }
  },
  "meta": {
    "timestamp": "2023-11-21T15:35:12.487Z",
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
    "timestamp": "2023-11-21T15:35:12.487Z",
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
    "message": "You do not have permission to update this order"
  },
  "meta": {
    "timestamp": "2023-11-21T15:35:12.487Z",
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
    "timestamp": "2023-11-21T15:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

##### 409 Conflict

```json
{
  "success": false,
  "error": {
    "code": "ORDER_UPDATE_CONFLICT",
    "message": "Cannot update shipping address for an order that has been shipped",
    "details": {
      "currentStatus": "SHIPPED",
      "allowedStatuses": [
        "PENDING_PAYMENT",
        "PAYMENT_PROCESSING",
        "PAYMENT_COMPLETED",
        "AWAITING_FULFILLMENT"
      ]
    }
  },
  "meta": {
    "timestamp": "2023-11-21T15:35:12.487Z",
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
    "timestamp": "2023-11-21T15:35:12.487Z",
    "requestId": "req-987654321"
  }
}
```

## 3. Request Processing

### 3.1. Authorization Rules

1. **Customer Access**:

   - Customers can update only their own orders
   - User ID from JWT token must match the userId on the order

2. **Administrator Access**:

   - Users with ADMIN role can update any order
   - Users with CUSTOMER_SERVICE role can update specific fields (e.g., shipping address, notes)

3. **Partner Limited Access**:
   - Fulfillment partners can update fulfillment-related fields
   - Payment partners can update payment-related fields
   - Access is restricted to specific fields based on partner type

### 3.2. Updateable Fields

The fields that can be updated depend on the current order status:

| Field                     | Eligible Statuses                                                            | Allowed Roles            |
| ------------------------- | ---------------------------------------------------------------------------- | ------------------------ |
| shippingDetails (address) | PENDING_PAYMENT, PAYMENT_PROCESSING, PAYMENT_COMPLETED, AWAITING_FULFILLMENT | CUSTOMER, ADMIN, CS      |
| shippingDetails (method)  | PENDING_PAYMENT, PAYMENT_PROCESSING                                          | CUSTOMER, ADMIN, CS      |
| billingDetails (address)  | PENDING_PAYMENT, PAYMENT_PROCESSING                                          | CUSTOMER, ADMIN, CS      |
| notes                     | Any status                                                                   | CUSTOMER, ADMIN, CS      |
| items                     | PENDING_PAYMENT only                                                         | ADMIN only               |
| promoCode                 | PENDING_PAYMENT only                                                         | CUSTOMER, ADMIN, CS      |
| paymentMethod             | PENDING_PAYMENT, PAYMENT_FAILED                                              | CUSTOMER, ADMIN, PAYMENT |
| status                    | Any status (following valid transitions)                                     | ADMIN only               |

### 3.3. Validation Rules

1. **Shipping Address Validation**:

   - Required fields: recipientName, shippingAddressLine1, shippingCity, shippingPostalCode, shippingCountry
   - Country must be a valid ISO country code
   - Postal code format validation based on country
   - Address line length validation (max 100 chars)

2. **Billing Address Validation**:

   - Required fields: billingAddressLine1, billingCity, billingPostalCode, billingCountry
   - Country must be a valid ISO country code
   - Postal code format validation based on country
   - Address line length validation (max 100 chars)

3. **Shipping Method Validation**:

   - Must be one of the supported shipping methods: STANDARD, EXPRESS, OVERNIGHT
   - Shipping method changes may affect total price

4. **Status Transition Validation**:

   - Status changes must follow the allowed transitions in the Order Status Entity
   - Some transitions may require additional information (e.g., tracking number for SHIPPED status)

5. **Notes Validation**:
   - Maximum length: 500 characters
   - No HTML or script tags allowed

### 3.4. Processing Steps

1. **Request Validation**:

   - Validate order exists
   - Validate authorization
   - Validate request body against schema
   - Validate fields can be updated based on current status

2. **Database Updates**:

   - Apply changes to appropriate database entities
   - Update related entities if needed (shipping details, billing details)
   - Update audit trail for tracking changes

3. **Price Recalculation** (if applicable):

   - Recalculate shipping costs if shipping method changed
   - Recalculate total amount

4. **Event Publishing**:

   - Publish OrderUpdated event with changes

5. **Response Assembly**:
   - Retrieve updated order with all related entities
   - Construct the complete order representation
   - Format the response according to the API response structure

## 4. Service Interactions

The update order endpoint interacts with the following services:

1. **Shipping Service** (if shipping method changed):

   - Calculate updated shipping costs
   - Update delivery estimates

2. **Payment Service** (if billing address changed):

   - Update payment method details
   - Update billing address on payment provider

3. **Notification Service**:

   - Send order update notification to customer
   - Send internal notifications for significant changes

4. **Warehouse/Fulfillment Service** (if address changed before shipping):
   - Update shipping information for fulfillment

## 5. Performance Considerations

1. **Partial Updates**:

   - Update only the fields that have changed
   - Use database transactions to ensure atomicity
   - Consider optimistic concurrency control for high-volume scenarios

2. **Caching Strategy**:

   - Invalidate caches for updated orders
   - Update cache with new order data

3. **Background Processing**:
   - Consider processing non-critical updates asynchronously
   - Use a queue for notifications and non-critical service interactions

## 6. Implementation Example

```typescript
@Patch(':orderId')
@UseGuards(JwtAuthGuard)
async updateOrder(
  @Param('orderId') orderId: string,
  @Body() updateOrderDto: UpdateOrderDto,
  @Req() request,
  @User() user: UserDto
): Promise<OrderDetailResponseDto> {
  const correlationId = request.headers['x-correlation-id'] || uuidv4();
  this.logger.log(`Updating order ${orderId}`, { correlationId, userId: user.id });

  try {
    // Validate UUID format
    if (!isUUID(orderId, 4)) {
      throw new BadRequestException({
        code: 'INVALID_ORDER_ID',
        message: 'Invalid order ID format'
      });
    }

    // Retrieve order with related entities
    const order = await this.orderService.findOrderById(orderId, {
      relations: ['items', 'billingDetails', 'shippingDetails', 'status']
    });

    if (!order) {
      throw new NotFoundException({
        code: 'ORDER_NOT_FOUND',
        message: `Order with ID ${orderId} not found`
      });
    }

    // Check authorization
    this.checkUpdateAuthorization(user, order);

    // Validate update is allowed based on status
    await this.validateOrderUpdateEligibility(order, updateOrderDto);

    // Apply updates
    const updatedOrder = await this.orderService.updateOrder(orderId, updateOrderDto);

    // Recalculate prices if needed
    if (updateOrderDto.shippingDetails?.shippingMethod &&
        updateOrderDto.shippingDetails.shippingMethod !== order.shippingDetails.shippingMethod) {
      await this.recalculateOrderTotals(updatedOrder);
    }

    // Publish event
    await this.eventPublisher.publish('order.updated', {
      orderId: updatedOrder.id,
      userId: updatedOrder.userId,
      changes: this.determineChanges(order, updatedOrder),
      timestamp: new Date().toISOString()
    });

    // Return updated order
    return {
      success: true,
      data: this.mapOrderToResponse(updatedOrder),
      meta: {
        timestamp: new Date().toISOString(),
        requestId: correlationId
      }
    };
  } catch (error) {
    this.logger.error(`Error updating order: ${error.message}`, {
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

private checkUpdateAuthorization(user: UserDto, order: Order): void {
  const isAdmin = user.role === 'ADMIN';
  const isCustomerService = user.role === 'CUSTOMER_SERVICE';
  const isOrderOwner = order.userId === user.id;

  if (!isAdmin && !isCustomerService && !isOrderOwner) {
    throw new ForbiddenException({
      code: 'FORBIDDEN',
      message: 'You do not have permission to update this order'
    });
  }

  // Additional role-based field validation
  if (!isAdmin && this.requestContainsAdminOnlyFields()) {
    throw new ForbiddenException({
      code: 'FORBIDDEN_FIELDS',
      message: 'You do not have permission to update certain fields'
    });
  }
}

private async validateOrderUpdateEligibility(order: Order, updates: UpdateOrderDto): Promise<void> {
  const currentStatus = order.status.name;

  // Check shipping address updates
  if (updates.shippingDetails && updates.shippingDetails.shippingAddressLine1) {
    const allowedStatusesForAddressUpdate = [
      'PENDING_PAYMENT', 'PAYMENT_PROCESSING', 'PAYMENT_COMPLETED', 'AWAITING_FULFILLMENT'
    ];

    if (!allowedStatusesForAddressUpdate.includes(currentStatus)) {
      throw new ConflictException({
        code: 'ORDER_UPDATE_CONFLICT',
        message: 'Cannot update shipping address for an order that has been processed for fulfillment',
        details: {
          currentStatus,
          allowedStatuses: allowedStatusesForAddressUpdate
        }
      });
    }
  }

  // Similar checks for other fields...
}

private async recalculateOrderTotals(order: Order): Promise<Order> {
  // Recalculate shipping costs based on method
  const shippingCost = await this.shippingService.calculateShippingCost({
    method: order.shippingDetails.shippingMethod,
    destination: {
      country: order.shippingDetails.shippingCountry,
      postalCode: order.shippingDetails.shippingPostalCode
    },
    items: order.items.map(item => ({
      productId: item.productId,
      quantity: item.quantity
    }))
  });

  // Update order with new totals
  const updatedTotals = {
    shippingCost,
    totalAmount: order.subtotal + shippingCost + order.tax - order.discountAmount
  };

  return this.orderService.updateOrderTotals(order.id, updatedTotals);
}

private determineChanges(oldOrder: Order, newOrder: Order): Record<string, any> {
  // Compare and return changed fields
  const changes = {};

  if (oldOrder.shippingDetails.recipientName !== newOrder.shippingDetails.recipientName) {
    changes['shipping.recipientName'] = {
      old: oldOrder.shippingDetails.recipientName,
      new: newOrder.shippingDetails.recipientName
    };
  }

  // Compare other fields

  return changes;
}
```

## 7. References

- [Order Service API Index](./00-api-index.md)
- [Order Entity Specification](../02-data-model-setup/01-order-entity.md)
- [Order Status Entity Specification](../02-data-model-setup/05-order-status-entity.md)
- [ADR-002-rest-api-standards-openapi](../../../architecture/adr/ADR-002-rest-api-standards-openapi.md)
