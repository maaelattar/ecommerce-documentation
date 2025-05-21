# Create Order API Endpoint

## 1. Overview

This document specifies the API endpoint for creating a new order in the Order Service. This is one of the most critical endpoints in the e-commerce platform, as it initiates the order fulfillment process and involves multiple service interactions.

## 2. Endpoint Specification

| Method | Endpoint       | Description        |
| ------ | -------------- | ------------------ |
| POST   | /api/v1/orders | Create a new order |

### 2.1. Request Format

#### Headers

| Header           | Type   | Required | Description                       |
| ---------------- | ------ | -------- | --------------------------------- |
| Authorization    | String | Yes      | Bearer token for authentication   |
| Content-Type     | String | Yes      | application/json                  |
| X-Correlation-ID | String | No       | Unique ID for distributed tracing |
| X-Client-ID      | String | No       | Client application identifier     |

#### Request Body

```json
{
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "items": [
    {
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "quantity": 2
    },
    {
      "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
      "quantity": 1
    }
  ],
  "billingDetails": {
    "paymentMethod": "CREDIT_CARD",
    "paymentToken": "tok_visa",
    "billingAddressLine1": "123 Main St",
    "billingAddressLine2": "Apt 4B",
    "billingCity": "San Francisco",
    "billingState": "CA",
    "billingPostalCode": "94105",
    "billingCountry": "US"
  },
  "shippingDetails": {
    "recipientName": "John Doe",
    "shippingAddressLine1": "123 Main St",
    "shippingAddressLine2": "Apt 4B",
    "shippingCity": "San Francisco",
    "shippingState": "CA",
    "shippingPostalCode": "94105",
    "shippingCountry": "US",
    "shippingMethod": "STANDARD"
  },
  "currency": "USD",
  "promoCode": "SUMMER10"
}
```

#### Request Parameters

| Field                          | Type    | Required | Description                                    |
| ------------------------------ | ------- | -------- | ---------------------------------------------- |
| userId                         | UUID    | Yes      | Identifier of the user placing the order       |
| items                          | Array   | Yes      | Array of order items                           |
| items[].productId              | UUID    | Yes      | Product identifier                             |
| items[].quantity               | Integer | Yes      | Quantity of the product                        |
| billingDetails                 | Object  | Yes      | Billing and payment information                |
| billingDetails.paymentMethod   | String  | Yes      | Payment method (CREDIT_CARD, PAYPAL, etc.)     |
| billingDetails.paymentToken    | String  | Yes      | Payment processor token for the payment method |
| billingDetails._Address_       | String  | Yes      | Billing address fields (see schema)            |
| shippingDetails                | Object  | Yes      | Shipping information                           |
| shippingDetails.recipientName  | String  | Yes      | Name of the recipient                          |
| shippingDetails._Address_      | String  | Yes      | Shipping address fields (see schema)           |
| shippingDetails.shippingMethod | String  | Yes      | Shipping method code (STANDARD, EXPRESS, etc.) |
| currency                       | String  | Yes      | Three-letter currency code (e.g., USD, EUR)    |
| promoCode                      | String  | No       | Promotional code for discounts                 |

### 2.2. Response Format

#### Success Response (201 Created)

##### Headers

| Header           | Type   | Description                                  |
| ---------------- | ------ | -------------------------------------------- |
| Content-Type     | String | application/json                             |
| Location         | String | URL to the newly created order resource      |
| X-Correlation-ID | String | Same correlation ID from request if provided |

##### Response Body

```json
{
  "success": true,
  "data": {
    "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "PENDING_PAYMENT",
    "createdAt": "2023-11-21T15:27:30.123Z",
    "totalAmount": 149.99,
    "estimatedShippingDate": "2023-11-25T12:00:00Z",
    "itemCount": 2
  },
  "meta": {
    "timestamp": "2023-11-21T15:27:30.456Z",
    "requestId": "req-123456789"
  }
}
```

#### Error Responses

##### 400 Bad Request

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid request parameters",
    "details": {
      "items": "At least one item is required",
      "billingDetails.paymentMethod": "Unsupported payment method"
    }
  },
  "meta": {
    "timestamp": "2023-11-21T15:27:30.456Z",
    "requestId": "req-123456789"
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
    "timestamp": "2023-11-21T15:27:30.456Z",
    "requestId": "req-123456789"
  }
}
```

##### 409 Conflict

```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_OUT_OF_STOCK",
    "message": "One or more products are out of stock",
    "details": {
      "productIds": ["0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0"]
    }
  },
  "meta": {
    "timestamp": "2023-11-21T15:27:30.456Z",
    "requestId": "req-123456789"
  }
}
```

##### 422 Unprocessable Entity

```json
{
  "success": false,
  "error": {
    "code": "PAYMENT_PROCESSING_ERROR",
    "message": "Payment processing failed",
    "details": {
      "paymentError": "Card declined"
    }
  },
  "meta": {
    "timestamp": "2023-11-21T15:27:30.456Z",
    "requestId": "req-123456789"
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
    "timestamp": "2023-11-21T15:27:30.456Z",
    "requestId": "req-123456789"
  }
}
```

## 3. Request Processing

### 3.1. Validation Rules

1. **User Validation**:

   - User must exist and be active
   - User must have permission to create orders

2. **Product Validation**:

   - All products must exist in the Product Service
   - Products must be available for purchase (not discontinued)

3. **Inventory Validation**:

   - Requested quantities must be available in inventory
   - Inventory must be successfully reserved

4. **Payment Validation**:

   - Payment method must be supported
   - Payment token must be valid
   - Payment must be successfully processed

5. **Address Validation**:

   - Shipping address must be valid and supported for delivery
   - Country and postal code must be valid
   - Required address fields must be present based on country

6. **Shipping Method Validation**:
   - Shipping method must be supported for the destination
   - Shipping method must be valid for the items (weight, dimensions)

### 3.2. Processing Steps

1. **Request Validation**:

   - Validate all required fields and data formats
   - Validate user existence and permissions

2. **Product Information Retrieval**:

   - Retrieve product details from Product Service
   - Get current prices, availability, and metadata

3. **Inventory Check**:

   - Check product availability in Inventory Service
   - Reserve inventory for the order

4. **Price Calculation**:

   - Calculate item prices based on current product prices
   - Apply any applicable promotions or discounts
   - Calculate shipping cost based on shipping method and destination
   - Calculate taxes based on shipping destination
   - Calculate order total

5. **Order Creation**:

   - Create order record with PENDING_PAYMENT status
   - Create order items records
   - Create billing and shipping detail records

6. **Payment Processing**:

   - Process payment using Payment Service
   - Update order with payment results

7. **Confirmation**:

   - Update order status based on payment result
   - Release inventory if payment fails
   - Generate and return order confirmation

8. **Event Publishing**:
   - Publish order.created event
   - Publish payment events based on payment result

## 4. Service Interactions

The create order endpoint interacts with multiple services:

1. **User Service**:

   - Verify user existence and status
   - Get user preferences for shipping and billing

2. **Product Service**:

   - Retrieve product details (name, price, tax category)
   - Validate product availability for purchase

3. **Inventory Service**:

   - Check inventory availability
   - Reserve inventory for the order

4. **Payment Service**:

   - Process payment using the provided payment token
   - Get payment confirmation or failure details

5. **Notification Service** (via events):
   - Send order confirmation to customer
   - Send order notifications to relevant parties

## 5. Security Considerations

1. **Authentication and Authorization**:

   - JWT token validation
   - Scope validation for order creation
   - User verification for the provided userId

2. **Payment Security**:

   - No sensitive payment details stored
   - Payment tokenization for PCI DSS compliance
   - Secure communication with Payment Service

3. **Rate Limiting**:

   - IP-based rate limiting to prevent abuse
   - User-based rate limiting for order creation

4. **Input Validation**:
   - Strict validation of all input fields
   - Prevention of injection attacks
   - Data sanitization

## 6. Error Handling

The API implements robust error handling with:

1. **Validation Errors**:

   - Field-specific error messages
   - Clear instructions for correction

2. **Business Logic Errors**:

   - Inventory availability issues
   - Payment processing failures
   - Shipping restrictions

3. **System Errors**:

   - Graceful handling of system failures
   - Appropriate error responses
   - Internal error logging

4. **Idempotency**:
   - Support for client-generated idempotency keys
   - Prevention of duplicate order creation

## 7. Implementation Example

```typescript
@Post()
@UseGuards(JwtAuthGuard)
async createOrder(@Body() createOrderDto: CreateOrderDto, @Req() request): Promise<OrderResponseDto> {
  const correlationId = request.headers['x-correlation-id'] || uuidv4();
  this.logger.log(`Creating order for user ${createOrderDto.userId}`, { correlationId });

  try {
    // Validate user
    await this.userService.verifyUser(createOrderDto.userId);

    // Get product details and validate availability
    const productDetails = await this.productService.getProductDetails(
      createOrderDto.items.map(item => item.productId)
    );

    // Validate and calculate prices
    const priceCalculation = this.orderCalculationService.calculateOrderTotals(
      createOrderDto.items,
      productDetails,
      createOrderDto.shippingDetails.shippingMethod,
      createOrderDto.shippingDetails.shippingCountry,
      createOrderDto.promoCode
    );

    // Check and reserve inventory
    await this.inventoryService.reserveInventory(
      createOrderDto.items.map(item => ({
        productId: item.productId,
        quantity: item.quantity
      }))
    );

    // Create order in pending payment status
    const order = await this.orderService.createOrder({
      userId: createOrderDto.userId,
      items: createOrderDto.items.map(item => ({
        productId: item.productId,
        quantity: item.quantity,
        unitPrice: productDetails.find(p => p.id === item.productId).price,
        totalPrice: item.quantity * productDetails.find(p => p.id === item.productId).price
      })),
      billingDetails: createOrderDto.billingDetails,
      shippingDetails: createOrderDto.shippingDetails,
      totalAmount: priceCalculation.totalAmount,
      currency: createOrderDto.currency,
      statusId: OrderStatusEnum.PENDING_PAYMENT
    });

    // Process payment
    const paymentResult = await this.paymentService.processPayment({
      orderId: order.id,
      amount: priceCalculation.totalAmount,
      currency: createOrderDto.currency,
      paymentMethod: createOrderDto.billingDetails.paymentMethod,
      paymentToken: createOrderDto.billingDetails.paymentToken
    });

    // Update order based on payment result
    if (paymentResult.success) {
      await this.orderService.updateOrderStatus(
        order.id,
        OrderStatusEnum.PAYMENT_COMPLETED,
        'Payment processed successfully',
        {
          paymentId: paymentResult.paymentId,
          transactionId: paymentResult.transactionId
        }
      );
    } else {
      await this.inventoryService.releaseInventory(
        createOrderDto.items.map(item => ({
          productId: item.productId,
          quantity: item.quantity
        }))
      );

      await this.orderService.updateOrderStatus(
        order.id,
        OrderStatusEnum.PAYMENT_FAILED,
        'Payment processing failed',
        {
          paymentError: paymentResult.error
        }
      );

      throw new UnprocessableEntityException({
        code: 'PAYMENT_PROCESSING_ERROR',
        message: 'Payment processing failed',
        details: {
          paymentError: paymentResult.error
        }
      });
    }

    // Publish events
    this.eventPublisher.publishOrderCreatedEvent(order);

    // Return response
    return {
      success: true,
      data: {
        orderId: order.id,
        status: OrderStatusEnum[OrderStatusEnum.PAYMENT_COMPLETED],
        createdAt: order.createdAt,
        totalAmount: priceCalculation.totalAmount,
        estimatedShippingDate: this.shippingService.estimateDeliveryDate(
          createOrderDto.shippingDetails.shippingMethod,
          createOrderDto.shippingDetails.shippingCountry
        ),
        itemCount: order.items.length
      },
      meta: {
        timestamp: new Date().toISOString(),
        requestId: correlationId
      }
    };
  } catch (error) {
    this.logger.error(`Error creating order: ${error.message}`, {
      correlationId,
      stack: error.stack
    });

    if (error instanceof HttpException) {
      throw error;
    }

    if (error.code === 'INVENTORY_NOT_AVAILABLE') {
      throw new ConflictException({
        code: 'PRODUCT_OUT_OF_STOCK',
        message: 'One or more products are out of stock',
        details: {
          productIds: error.details.productIds
        }
      });
    }

    throw new InternalServerErrorException({
      code: 'INTERNAL_SERVER_ERROR',
      message: 'An unexpected error occurred'
    });
  }
}
```

## 8. References

- [Order Service API Index](./00-api-index.md)
- [Order Entity Specification](../02-data-model-setup/01-order-entity.md)
- [Order Item Entity Specification](../02-data-model-setup/02-order-item-entity.md)
- [Order Status Entity Specification](../02-data-model-setup/05-order-status-entity.md)
- [Product Service Integration](../06-integration-points/02-product-service-integration.md)
- [Inventory Service Integration](../06-integration-points/03-inventory-service-integration.md)
- [Payment Service Integration](../06-integration-points/04-payment-service-integration.md)
- [ADR-002-rest-api-standards-openapi](../../../architecture/adr/ADR-002-rest-api-standards-openapi.md)
