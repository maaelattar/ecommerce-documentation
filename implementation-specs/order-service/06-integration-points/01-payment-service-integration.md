# Order Service Integration with Payment Service

## 1. Overview

This document specifies the integration between the Order Service and Payment Service. This integration is crucial for managing payment processing, authorization, capture, refunds, and reconciliation throughout the order lifecycle. The Order Service interacts with the Payment Service both synchronously during order creation and asynchronously for payment status updates.

## 2. Integration Points

### 2.1. Synchronous Integrations (REST API)

| Operation             | Endpoint                              | Method | Purpose                                            |
| --------------------- | ------------------------------------- | ------ | -------------------------------------------------- |
| Create Payment Intent | `/api/v1/payments/intent`             | POST   | Initialize payment process during checkout         |
| Get Payment Status    | `/api/v1/payments/{paymentId}/status` | GET    | Check current status of a payment                  |
| Void Authorization    | `/api/v1/payments/{paymentId}/void`   | POST   | Cancel payment authorization if order is cancelled |

### 2.2. Asynchronous Integrations (Events)

| Event                       | Publisher       | Subscriber      | Purpose                                         |
| --------------------------- | --------------- | --------------- | ----------------------------------------------- |
| `order.created`             | Order Service   | Payment Service | Trigger payment capture when order is confirmed |
| `order.cancelled`           | Order Service   | Payment Service | Signal to void authorization or process refund  |
| `order.returned`            | Order Service   | Payment Service | Signal to process refund for returned items     |
| `payment.capture_requested` | Order Service   | Payment Service | Request to capture a payment after confirmation |
| `payment.refund_requested`  | Order Service   | Payment Service | Request to process refund for order             |
| `payment.completed`         | Payment Service | Order Service   | Update order to payment completed status        |
| `payment.failed`            | Payment Service | Order Service   | Update order to payment failed status           |
| `payment.refunded`          | Payment Service | Order Service   | Update order to refunded status                 |
| `payment.capture_succeeded` | Payment Service | Order Service   | Confirm that payment capture was successful     |
| `payment.capture_failed`    | Payment Service | Order Service   | Notify that payment capture failed              |

## 3. Data Models

### 3.1. Request/Response Models

#### Create Payment Intent Request

```json
{
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "amount": 149.99,
  "currency": "USD",
  "paymentMethod": "CREDIT_CARD",
  "paymentMethodDetails": {
    "cardToken": "tok_visa",
    "saveCard": true
  },
  "customerDetails": {
    "customerId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "customer@example.com"
  },
  "billingDetails": {
    "name": "Jane Doe",
    "addressLine1": "456 Park Ave",
    "addressLine2": "Apt 7C",
    "city": "New York",
    "state": "NY",
    "postalCode": "10022",
    "country": "US"
  },
  "metadata": {
    "source": "WEB"
  }
}
```

#### Create Payment Intent Response

```json
{
  "success": true,
  "data": {
    "paymentIntentId": "pi_3OBtP1CZ6qsJgndP0NZUQ1ZW",
    "clientSecret": "pi_3OBtP1CZ6qsJgndP0NZUQ1ZW_secret_aBcDeFgHiJkLmNoP",
    "status": "REQUIRES_CONFIRMATION",
    "amount": 149.99,
    "currency": "USD",
    "paymentMethod": "CREDIT_CARD",
    "expiresAt": "2023-11-21T16:27:30.123Z"
  },
  "meta": {
    "timestamp": "2023-11-21T15:27:30.123Z"
  }
}
```

#### Capture Payment Request

```json
{
  "paymentIntentId": "pi_3OBtP1CZ6qsJgndP0NZUQ1ZW",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "amount": 149.99,
  "idempotencyKey": "ord_f47ac10b-58cc-4372-a567-0e02b2c3d479_capture"
}
```

#### Process Refund Request

```json
{
  "paymentId": "pi_3OBtP1CZ6qsJgndP0NZUQ1ZW",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "amount": 149.99,
  "reason": "ORDER_CANCELLED",
  "refundItems": [
    {
      "orderItemId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "amount": 119.98,
      "quantity": 2
    },
    {
      "orderItemId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "amount": 20.01,
      "quantity": 1
    }
  ],
  "idempotencyKey": "ord_f47ac10b-58cc-4372-a567-0e02b2c3d479_refund"
}
```

### 3.2. Event Payloads

#### Payment Completed Event

```json
{
  "eventType": "payment.completed",
  "paymentId": "pi_3OBtP1CZ6qsJgndP0NZUQ1ZW",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "amount": 149.99,
  "currency": "USD",
  "paymentMethod": "CREDIT_CARD",
  "paymentMethodDetails": {
    "cardBrand": "visa",
    "last4": "4242",
    "expiryMonth": 12,
    "expiryYear": 2025
  },
  "status": "COMPLETED",
  "transactionId": "txn_1OBtP1CZ6qsJgndP0NZUQ1ZW",
  "timestamp": "2023-11-21T15:29:30.123Z",
  "metadata": {
    "customerIp": "192.168.1.1",
    "gatewayResponse": "approved"
  }
}
```

#### Payment Failed Event

```json
{
  "eventType": "payment.failed",
  "paymentId": "pi_3OBtP1CZ6qsJgndP0NZUQ1ZW",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "amount": 149.99,
  "currency": "USD",
  "paymentMethod": "CREDIT_CARD",
  "paymentMethodDetails": {
    "cardBrand": "visa",
    "last4": "0341",
    "expiryMonth": 12,
    "expiryYear": 2025
  },
  "status": "FAILED",
  "errorCode": "card_declined",
  "errorMessage": "Your card has insufficient funds",
  "timestamp": "2023-11-21T15:29:30.123Z",
  "metadata": {
    "attemptCount": 1,
    "gatewayResponse": "declined"
  }
}
```

## 4. Sequence Diagrams

### 4.1. Order Creation with Payment Flow

```
┌─────────┐          ┌─────────────┐          ┌────────────────┐
│  User   │          │Order Service │          │Payment Service │
└────┬────┘          └──────┬──────┘          └────────┬───────┘
     │                       │                          │
     │ Create Order Request  │                          │
     │──────────────────────>│                          │
     │                       │                          │
     │                       │ Create Payment Intent    │
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │ Payment Intent Response  │
     │                       │<─────────────────────────│
     │                       │                          │
     │                       │ Validate Order Details   │
     │                       │ (inventory, pricing, etc)│
     │                       │                          │
     │ Order + Payment Intent│                          │
     │<──────────────────────│                          │
     │                       │                          │
     │ Submit Payment        │                          │
     │─────────────────────────────────────────────────>│
     │                       │                          │
     │                       │                          │ Process Payment
     │                       │                          │
     │ Payment Confirmation  │                          │
     │<─────────────────────────────────────────────────│
     │                       │                          │
     │ Confirm Order         │                          │
     │──────────────────────>│                          │
     │                       │                          │
     │                       │ Publish payment.capture_requested │
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │ Finalize Order           │
     │                       │                          │
     │ Order Confirmation    │                          │
     │<──────────────────────│                          │
     │                       │                          │
     │                       │ Publish order.created    │
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │                          │ Process and record
     │                       │                          │ confirmed order
     │                       │                          │
     │                       │ Publish payment.capture_succeeded |
     │                       │<─────────────────────────│
     │                       │                          │
     │                       │ Update order status      │
     │                       │ to PAYMENT_COMPLETED     │
     │                       │                          │
┌────┴────┐          ┌──────┴──────┐          ┌────────┴───────┐
│  User   │          │Order Service │          │Payment Service │
└─────────┘          └─────────────┘          └────────────────┘
```

### 4.2. Order Refund Flow

```
┌─────────┐          ┌─────────────┐          ┌────────────────┐
│  User   │          │Order Service │          │Payment Service │
└────┬────┘          └──────┬──────┘          └────────┬───────┘
     │                       │                          │
     │ Cancel Order Request  │                          │
     │──────────────────────>│                          │
     │                       │                          │
     │                       │ Validate Cancellation    │
     │                       │ (check eligibility)      │
     │                       │                          │
     │                       │ Publish payment.refund_requested |
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │                          │ Process Refund
     │                       │                          │ with Payment Gateway
     │                       │                          │
     │                       │ Update Order Status      │
     │                       │ to CANCELLATION_PENDING  │
     │                       │                          │
     │ Cancellation Initiated│                          │
     │<──────────────────────│                          │
     │                       │                          │
     │                       │ Publish order.cancelled  │
     │                       │─────────────────────────>│
     │                       │                          │
     │                       │                          │ Update payment
     │                       │                          │ records with
     │                       │                          │ cancellation
     │                       │                          │
     │                       │ Publish payment.refunded │
     │                       │<─────────────────────────│
     │                       │                          │
     │                       │ Update order status      │
     │                       │ to CANCELLED/REFUNDED    │
     │                       │                          │
     │ Cancellation Confirmed│                          │
     │<──────────────────────│                          │
     │                       │                          │
┌────┴────┐          ┌──────┴──────┐          ┌────────┴───────┐
│  User   │          │Order Service │          │Payment Service │
└─────────┘          └─────────────┘          └────────────────┘
```

## 5. Service Client Implementation

The Order Service implements a Payment Service client to handle the synchronous communication, while using event-driven patterns for asynchronous operations:

```typescript
@Injectable()
export class PaymentServiceClient {
  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
    private readonly logger: Logger,
    private readonly eventBus: EventBus
  ) {}

  private readonly baseUrl = this.configService.get<string>(
    "PAYMENT_SERVICE_URL"
  );
  private readonly timeout =
    this.configService.get<number>("PAYMENT_SERVICE_TIMEOUT") || 5000;

  /**
   * Create payment intent for an order
   */
  async createPaymentIntent(
    orderData: CreateOrderDto,
    userId: string
  ): Promise<PaymentIntentResponseDto> {
    this.logger.log(`Creating payment intent for user ${userId}`);

    try {
      const payload = this.buildPaymentIntentPayload(orderData, userId);

      const response = await firstValueFrom(
        this.httpService
          .post<ApiResponse<PaymentIntentResponseDto>>(
            `${this.baseUrl}/api/v1/payments/intent`,
            payload
          )
          .pipe(
            timeout(this.timeout),
            catchError((error) => {
              this.logger.error(
                `Error creating payment intent: ${error.message}`,
                error.stack
              );

              if (error.response) {
                if (error.response.status === 400) {
                  throw new BadRequestException(
                    error.response.data.error || "Invalid payment request"
                  );
                }
              }

              throw new ServiceUnavailableException(
                "Payment service is currently unavailable"
              );
            })
          )
      );

      return response.data.data;
    } catch (error) {
      if (
        error instanceof BadRequestException ||
        error instanceof ServiceUnavailableException
      ) {
        throw error;
      }

      throw new InternalServerErrorException("Failed to create payment intent");
    }
  }

  /**
   * Request payment capture asynchronously through events
   */
  async requestPaymentCapture(
    paymentIntentId: string,
    orderId: string,
    amount: number
  ): Promise<void> {
    this.logger.log(
      `Requesting payment capture for ${paymentIntentId} (order ${orderId})`
    );

    try {
      // Publish event to request payment capture
      await this.eventBus.publish({
        id: uuidv4(),
        type: "payment.capture_requested",
        source: "order-service",
        dataVersion: "1.0",
        timestamp: new Date().toISOString(),
        correlationId: orderId,
        data: {
          paymentIntentId,
          orderId,
          amount,
          idempotencyKey: `ord_${orderId}_capture`,
        },
      });
    } catch (error) {
      this.logger.error(
        `Error publishing payment capture event: ${error.message}`,
        error.stack
      );
      throw new InternalServerErrorException(
        "Failed to request payment capture"
      );
    }
  }

  /**
   * Request refund asynchronously through events
   */
  async requestRefund(
    paymentId: string,
    orderId: string,
    amount: number,
    reason: string,
    items?: OrderItemDto[]
  ): Promise<void> {
    this.logger.log(`Requesting refund for order ${orderId}`);

    try {
      const refundItems = items?.map((item) => ({
        orderItemId: item.id,
        amount: item.totalPrice,
        quantity: item.quantity,
      }));

      // Publish event to request refund
      await this.eventBus.publish({
        id: uuidv4(),
        type: "payment.refund_requested",
        source: "order-service",
        dataVersion: "1.0",
        timestamp: new Date().toISOString(),
        correlationId: orderId,
        data: {
          paymentId,
          orderId,
          amount,
          reason,
          refundItems,
          idempotencyKey: `ord_${orderId}_refund`,
        },
      });
    } catch (error) {
      this.logger.error(
        `Error publishing refund request event: ${error.message}`,
        error.stack
      );
      throw new InternalServerErrorException("Failed to request refund");
    }
  }

  /**
   * Helper method to build payment intent payload
   */
  private buildPaymentIntentPayload(
    orderData: CreateOrderDto,
    userId: string
  ): Record<string, any> {
    const totalAmount = this.calculateOrderTotal(orderData);

    return {
      orderId: undefined, // Will be assigned after order creation
      amount: totalAmount,
      currency: "USD", // Could be configurable
      paymentMethod: orderData.billingDetails.paymentMethod,
      paymentMethodDetails: orderData.billingDetails.paymentMethodDetails,
      customerDetails: {
        customerId: userId,
        email: orderData.billingDetails.email || undefined,
      },
      billingDetails: {
        name: orderData.billingDetails.billingName,
        addressLine1: orderData.billingDetails.billingAddressLine1,
        addressLine2: orderData.billingDetails.billingAddressLine2,
        city: orderData.billingDetails.billingCity,
        state: orderData.billingDetails.billingState,
        postalCode: orderData.billingDetails.billingPostalCode,
        country: orderData.billingDetails.billingCountry,
      },
      metadata: orderData.metadata || {},
    };
  }

  /**
   * Helper method to calculate order total
   */
  private calculateOrderTotal(orderData: CreateOrderDto): number {
    // This would be replaced with actual calculation logic
    // including shipping, tax, discounts, etc.
    return 149.99;
  }
}
```

## 6. Event Handlers

The Order Service implements handlers for payment-related events:

```typescript
@Injectable()
export class PaymentEventHandlers {
  constructor(
    private readonly orderService: OrderService,
    private readonly logger: Logger
  ) {}

  @EventPattern("payment.capture_succeeded")
  async handlePaymentCaptureSucceeded(
    @Payload() event: PaymentCaptureSucceededEvent,
    @Ctx() context: NatsContext
  ): Promise<void> {
    const { id: eventId, data } = event;
    const { orderId, paymentIntentId, transactionId } = data;

    this.logger.log(
      `Processing payment.capture_succeeded event ${eventId} for order ${orderId}`
    );

    try {
      // Update order with payment completed status
      await this.orderService.updateOrderPaymentStatus(
        orderId,
        "PAYMENT_COMPLETED",
        {
          transactionId,
          paymentTimestamp: new Date().toISOString(),
          paymentReference: paymentIntentId,
        }
      );

      // Acknowledge event
      context.getMessage().ack();
    } catch (error) {
      this.logger.error(
        `Error processing payment capture success event: ${error.message}`,
        error.stack
      );
      // Negative acknowledge to trigger retry
      context.getMessage().nak();
    }
  }

  @EventPattern("payment.capture_failed")
  async handlePaymentCaptureFailed(
    @Payload() event: PaymentCaptureFailedEvent,
    @Ctx() context: NatsContext
  ): Promise<void> {
    const { id: eventId, data } = event;
    const { orderId, paymentIntentId, errorCode, errorMessage } = data;

    this.logger.log(
      `Processing payment.capture_failed event ${eventId} for order ${orderId}`
    );

    try {
      // Update order with payment failed status
      await this.orderService.updateOrderPaymentStatus(
        orderId,
        "PAYMENT_FAILED",
        {
          errorCode,
          errorMessage,
          paymentReference: paymentIntentId,
        }
      );

      // Flag order for review
      await this.orderService.flagOrderForReview(
        orderId,
        "PAYMENT_CAPTURE_FAILED",
        `Payment capture failed: ${errorMessage}`
      );

      // Acknowledge event
      context.getMessage().ack();
    } catch (error) {
      this.logger.error(
        `Error processing payment capture failed event: ${error.message}`,
        error.stack
      );
      // Negative acknowledge to trigger retry
      context.getMessage().nak();
    }
  }

  @EventPattern("payment.refunded")
  async handlePaymentRefunded(
    @Payload() event: PaymentRefundedEvent,
    @Ctx() context: NatsContext
  ): Promise<void> {
    const { id: eventId, data } = event;
    const { orderId, amount, refundId, reason } = data;

    this.logger.log(
      `Processing payment.refunded event ${eventId} for order ${orderId}`
    );

    try {
      // Update order with refunded status
      await this.orderService.updateOrderRefundStatus(
        orderId,
        amount,
        refundId,
        reason
      );

      // Acknowledge event
      context.getMessage().ack();
    } catch (error) {
      this.logger.error(
        `Error processing payment refunded event: ${error.message}`,
        error.stack
      );
      // Negative acknowledge to trigger retry
      context.getMessage().nak();
    }
  }
}
```

## 7. Resilience Patterns

### 7.1. Circuit Breaker

The Order Service implements a circuit breaker pattern for Payment Service calls:

```typescript
@Injectable()
export class PaymentServiceWithCircuitBreaker {
  constructor(
    private readonly paymentServiceClient: PaymentServiceClient,
    private readonly logger: Logger
  ) {}

  @CircuitBreaker({
    resetTimeout: 30000, // 30 seconds
    errorThresholdPercentage: 50,
    rollingCountTimeout: 10000,
    rollingCountBuckets: 10,
    name: "paymentServiceIntent",
  })
  async createPaymentIntent(
    orderData: CreateOrderDto,
    userId: string
  ): Promise<PaymentIntentResponseDto> {
    return this.paymentServiceClient.createPaymentIntent(orderData, userId);
  }

  @CircuitBreaker({
    resetTimeout: 30000, // 30 seconds
    errorThresholdPercentage: 50,
    rollingCountTimeout: 10000,
    rollingCountBuckets: 10,
    name: "paymentServiceCapture",
  })
  async capturePayment(
    paymentIntentId: string,
    orderId: string,
    amount: number
  ): Promise<PaymentResponseDto> {
    return this.paymentServiceClient.capturePayment(
      paymentIntentId,
      orderId,
      amount
    );
  }

  @CircuitBreaker({
    resetTimeout: 30000, // 30 seconds
    errorThresholdPercentage: 50,
    rollingCountTimeout: 10000,
    rollingCountBuckets: 10,
    name: "paymentServiceRefund",
  })
  async processRefund(
    paymentId: string,
    orderId: string,
    amount: number,
    reason: string,
    items?: OrderItemDto[]
  ): Promise<RefundResponseDto> {
    return this.paymentServiceClient.processRefund(
      paymentId,
      orderId,
      amount,
      reason,
      items
    );
  }
}
```

### 7.2. Retry with Backoff

For payment operations, especially captures and refunds, a robust retry strategy is implemented:

```typescript
// Example of enhanced retry logic for payment capture
async capturePaymentWithRetry(
  paymentIntentId: string,
  orderId: string,
  amount: number
): Promise<PaymentResponseDto> {
  const retryConfig = {
    retries: 3,
    minTimeout: 1000, // 1 second
    maxTimeout: 10000, // 10 seconds
    factor: 2, // exponential backoff factor
  };

  const operation = retry.operation(retryConfig);

  return new Promise((resolve, reject) => {
    operation.attempt(async (attemptNumber) => {
      try {
        this.logger.log(
          `Capturing payment attempt ${attemptNumber} for order ${orderId}`
        );

        const result = await this.paymentServiceClient.capturePayment(
          paymentIntentId,
          orderId,
          amount
        );

        resolve(result);
      } catch (error) {
        // Determine if error is retryable
        const isRetryable = this.isRetryableError(error);

        if (operation.retry(error) && isRetryable) {
          // Will retry
          this.logger.warn(
            `Retrying payment capture for order ${orderId} after error: ${error.message}`
          );
          return;
        }

        // Max retries reached or non-retryable error
        reject(operation.mainError() || error);
      }
    });
  });
}

// Helper method to determine if an error is retryable
private isRetryableError(error: any): boolean {
  // Network errors and specific payment service errors are retryable
  if (error instanceof ServiceUnavailableException) {
    return true;
  }

  // Gateway timeouts or connection errors
  if (error.code === 'ECONNRESET' || error.code === 'ETIMEDOUT') {
    return true;
  }

  // Payment provider temporary failures
  if (error.message && error.message.includes('temporarily unavailable')) {
    return true;
  }

  // Business logic errors should not be retried
  if (
    error instanceof BadRequestException ||
    error instanceof ConflictException ||
    error instanceof UnprocessableEntityException
  ) {
    return false;
  }

  return false;
}
```

### 7.3. Fallback Mechanisms

When payment integration fails, the Order Service implements fallbacks:

1. **Payment Intent Creation Failures**:

   - Create order in "pending payment verification" state
   - Provide alternative payment instructions to customer
   - Set up a background job to retry or request manual intervention

2. **Payment Capture Failures**:

   - Flag order for manual review
   - Notify operations team for follow-up
   - Send customer notification about pending payment status

3. **Refund Processing Failures**:
   - Queue refund request in local database
   - Implement background retry
   - Notify customer of refund status with estimated timeline

## 8. Error Handling

### 8.1. Error Codes and Messages

| Error Code                     | HTTP Status | Description                            | Action                            |
| ------------------------------ | ----------- | -------------------------------------- | --------------------------------- |
| `PAYMENT_SERVICE_UNAVAILABLE`  | 503         | Payment service is unavailable         | Retry after delay                 |
| `PAYMENT_AUTHORIZATION_FAILED` | 422         | Payment authorization failed           | Notify user to try another method |
| `PAYMENT_CAPTURE_FAILED`       | 422         | Payment capture failed                 | Retry or manual review            |
| `PAYMENT_ALREADY_CAPTURED`     | 409         | Payment has already been captured      | Reconcile payment records         |
| `PAYMENT_NOT_FOUND`            | 404         | Payment ID doesn't exist               | Verify payment records            |
| `REFUND_FAILED`                | 422         | Refund could not be processed          | Manual refund process             |
| `REFUND_LIMIT_EXCEEDED`        | 400         | Refund amount exceeds original payment | Adjust refund amount              |

### 8.2. Error Handling Strategy

The Order Service implements the following error handling approach for payment operations:

1. **Validation Errors**: Pre-validate all payment requests before sending to Payment Service
2. **Transient Errors**: Use retry mechanism with exponential backoff
3. **Business Logic Errors**: Handle with appropriate user feedback
4. **Critical Failures**: Implement fallbacks and manual intervention triggers

## 9. Monitoring and Alerting

### 9.1. Key Metrics

1. **Payment Success Rate** - Percentage of successful payment operations
2. **Payment Service Response Time** - Latency of payment operations
3. **Payment Failures by Type** - Breakdown of payment failures by error type
4. **Refund Processing Time** - Average time to process refunds
5. **Circuit Breaker Status** - Open/closed status of Payment Service circuit breaker

### 9.2. Alerts

1. **High Payment Failure Rate** - Alert when failure rate exceeds 5%
2. **Payment Service Latency** - Alert when latency exceeds 2 seconds
3. **Circuit Breaker Open** - Alert when Payment Service circuit breaker trips
4. **Failed Refunds** - Alert on refunds that fail multiple retry attempts
5. **Payment/Order Mismatch** - Alert when payment amount doesn't match order total

## 10. References

- [Order Service API Specifications](../04-api-endpoints/00-api-index.md)
- [Payment Service API Specifications](../../payment-service/04-api-endpoints/01-payment-api.md)
- [Order Entity Model](../02-data-model-setup/01-order-entity.md)
- [Billing Details Entity Model](../02-data-model-setup/03-billing-details-entity.md)
- [Circuit Breaker Pattern](../../../architecture/adr/ADR-009-resilience-patterns.md)
- [Event-Driven Architecture](../../../architecture/adr/ADR-007-event-driven-architecture.md)
- [Payment Gateway Integration Best Practices](https://stripe.com/docs/payments/best-practices)
