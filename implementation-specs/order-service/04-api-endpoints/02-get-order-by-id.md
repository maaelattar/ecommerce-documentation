# Get Order by ID API Endpoint

## 1. Overview

This document specifies the API endpoint for retrieving a single order by its unique identifier. This endpoint provides detailed information about an order including its items, billing details, shipping details, and current status.

## 2. Endpoint Specification

| Method | Endpoint                 | Description             |
| ------ | ------------------------ | ----------------------- |
| GET    | /api/v1/orders/{orderId} | Retrieve an order by ID |

### 2.1. Request Format

#### Path Parameters

| Parameter | Type | Required | Description             |
| --------- | ---- | -------- | ----------------------- |
| orderId   | UUID | Yes      | Unique order identifier |

#### Headers

| Header           | Type   | Required | Description                       |
| ---------------- | ------ | -------- | --------------------------------- |
| Authorization    | String | Yes      | Bearer token for authentication   |
| Accept           | String | No       | application/json (default)        |
| X-Correlation-ID | String | No       | Unique ID for distributed tracing |

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
    "status": "SHIPPED",
    "statusId": 8,
    "statusDescription": "All items have been shipped",
    "createdAt": "2023-11-21T15:27:30.123Z",
    "updatedAt": "2023-11-23T14:35:12.487Z",
    "totalAmount": 149.99,
    "subtotal": 139.99,
    "tax": 10.0,
    "currency": "USD",
    "promoCode": "SUMMER10",
    "discountAmount": 15.0,
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
      "billingAddressLine1": "123 Main St",
      "billingAddressLine2": "Apt 4B",
      "billingCity": "San Francisco",
      "billingState": "CA",
      "billingPostalCode": "94105",
      "billingCountry": "US"
    },
    "shippingDetails": {
      "id": "1d2ca47d-8a7c-4b1a-b12c-0e99e252f295",
      "recipientName": "John Doe",
      "shippingAddressLine1": "123 Main St",
      "shippingAddressLine2": "Apt 4B",
      "shippingCity": "San Francisco",
      "shippingState": "CA",
      "shippingPostalCode": "94105",
      "shippingCountry": "US",
      "shippingMethod": "STANDARD",
      "shippingCost": 5.99,
      "estimatedDeliveryDate": "2023-11-27T12:00:00Z",
      "trackingNumber": "1ZW470X56892747254"
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
        "changedBy": "FULFILLMENT_SERVICE",
        "metadata": {
          "carrier": "UPS",
          "tracking_number": "1ZW470X56892747254"
        }
      }
    ]
  },
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
    "requestId": "req-987654321"
  }
}
```

#### Error Responses

##### 404 Not Found

```json
{
  "success": false,
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "Order with ID f47ac10b-58cc-4372-a567-0e02b2c3d479 not found"
  },
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
    "requestId": "req-987654321"
  }
}
```

##### 400 Bad Request

```json
{
  "success": false,
  "error": {
    "code": "INVALID_ORDER_ID",
    "message": "Invalid order ID format"
  },
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
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
    "timestamp": "2023-11-24T08:12:45.123Z",
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
    "message": "You do not have permission to access this order"
  },
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
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
    "timestamp": "2023-11-24T08:12:45.123Z",
    "requestId": "req-987654321"
  }
}
```

## 3. Request Processing

### 3.1. Authorization Rules

1. **Self-Access**:

   - Users can access their own orders
   - User ID from the JWT token must match the userId on the requested order

2. **Administrator Access**:

   - Users with the ADMIN role can access any order
   - Users with the CUSTOMER_SERVICE role can access any order

3. **Partner Limited Access**:
   - Fulfillment partners can access orders assigned to them with limited fields
   - Payment partners can access payment-related details with limited fields

### 3.2. Processing Steps

1. **Request Validation**:

   - Validate orderId format (must be a valid UUID)
   - Validate authorization token

2. **Authorization Check**:

   - Determine if the requester has permission to access the order
   - Filter response fields based on requester's role if necessary

3. **Data Retrieval**:

   - Query order by ID from database
   - Retrieve related records (items, billing details, shipping details)
   - Retrieve status history from DynamoDB

4. **Response Assembly**:

   - Construct the complete order representation with all related data
   - Format the response according to the API response structure
   - Include product names from product service (if available)

5. **Auditing**:
   - Log the access for audit purposes

## 4. Service Interactions

The get order by ID endpoint interacts with the following services:

1. **Product Service**:

   - Optional: Enrich order items with current product names if requested

2. **DynamoDB**:
   - Retrieve status history logs for the order

## 5. Performance Considerations

1. **Caching Strategy**:

   - Orders that have reached terminal status (DELIVERED, CANCELLED, REFUNDED) may be cached
   - Cache TTL: 1 hour for active orders, 24 hours for terminal orders
   - Cache key: order ID
   - Cache invalidation on order updates

2. **Query Optimization**:

   - Use eager loading for related entities to minimize database roundtrips
   - Selectively load status history based on query parameters

3. **Response Size Management**:
   - Pagination for status history if extensive (with option to load full history)
   - Optional fields can be requested via query parameters

## 6. Implementation Example

```typescript
@Get(':orderId')
@UseGuards(JwtAuthGuard)
async getOrderById(
  @Param('orderId') orderId: string,
  @Req() request,
  @Query('includeStatusHistory') includeStatusHistory: boolean = false,
  @Query('includeProductDetails') includeProductDetails: boolean = false
): Promise<OrderDetailResponseDto> {
  const correlationId = request.headers['x-correlation-id'] || uuidv4();
  this.logger.log(`Retrieving order ${orderId}`, { correlationId });

  try {
    // Validate UUID format
    if (!isUUID(orderId, 4)) {
      throw new BadRequestException({
        code: 'INVALID_ORDER_ID',
        message: 'Invalid order ID format'
      });
    }

    // Get user from JWT token
    const user = request.user;

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
    if (user.role !== 'ADMIN' && user.role !== 'CUSTOMER_SERVICE' && order.userId !== user.id) {
      throw new ForbiddenException({
        code: 'FORBIDDEN',
        message: 'You do not have permission to access this order'
      });
    }

    // Retrieve status history if requested
    let statusHistory = [];
    if (includeStatusHistory) {
      statusHistory = await this.orderStatusLogRepository.getStatusLogsByOrderId(orderId);
    }

    // Optionally enrich with product details
    if (includeProductDetails && order.items.length > 0) {
      const productIds = order.items.map(item => item.productId);
      const productDetails = await this.productService.getProductDetails(productIds);

      // Merge product names into order items
      order.items = order.items.map(item => {
        const product = productDetails.find(p => p.id === item.productId);
        return {
          ...item,
          productName: product ? product.name : 'Unknown Product'
        };
      });
    }

    // Construct response
    return {
      success: true,
      data: {
        id: order.id,
        userId: order.userId,
        status: order.status.name,
        statusId: order.status.id,
        statusDescription: order.status.description,
        createdAt: order.createdAt,
        updatedAt: order.updatedAt,
        totalAmount: order.totalAmount,
        subtotal: order.subtotal,
        tax: order.tax,
        currency: order.currency,
        promoCode: order.promoCode,
        discountAmount: order.discountAmount,
        items: order.items,
        billingDetails: order.billingDetails,
        shippingDetails: order.shippingDetails,
        statusHistory: statusHistory
      },
      meta: {
        timestamp: new Date().toISOString(),
        requestId: correlationId
      }
    };
  } catch (error) {
    this.logger.error(`Error retrieving order: ${error.message}`, {
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
```

## 7. References

- [Order Service API Index](./00-api-index.md)
- [Order Entity Specification](../02-data-model-setup/01-order-entity.md)
- [Order Item Entity Specification](../02-data-model-setup/02-order-item-entity.md)
- [Order Status Entity Specification](../02-data-model-setup/05-order-status-entity.md)
- [Order Status Log Entity Specification](../02-data-model-setup/06-order-status-log-entity.md)
- [ADR-002-rest-api-standards-openapi](../../../architecture/adr/ADR-002-rest-api-standards-openapi.md)
