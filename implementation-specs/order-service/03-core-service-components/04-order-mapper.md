# Order Mapper

## 1. Overview

The `OrderMapper` is a critical component responsible for transforming data between the domain entities (internal data models) and the Data Transfer Objects (DTOs) used in API requests and responses. This mapper ensures a clean separation between the application's internal data structures and the external API contracts, allowing each to evolve independently while maintaining compatibility.

## 2. Responsibilities

- Converting domain entities to response DTOs for API endpoints
- Transforming input DTOs to domain entities for business logic processing
- Filtering sensitive data from response objects
- Adapting data representations based on context (e.g., user role, requested fields)
- Implementing data transformation rules consistently across the application
- Handling nested relationships and complex object mappings
- Supporting partial mappings for operations that don't require complete objects

## 3. Class Definition

```typescript
@Injectable()
export class OrderMapper {
  constructor(
    private readonly configService: ConfigService,
    private readonly userService: UserService
  ) {}

  // Mapper methods defined below
}
```

## 4. Core Mapping Methods

### 4.1. Entity to Response DTO

```typescript
/**
 * Maps an Order entity to OrderResponseDto
 */
async toResponseDto(
  order: Order,
  options: {
    includeItems?: boolean;
    includeShippingDetails?: boolean;
    includeBillingDetails?: boolean;
    includeStatusHistory?: boolean;
  } = {
    includeItems: true,
    includeShippingDetails: true,
    includeBillingDetails: true,
    includeStatusHistory: false
  }
): Promise<OrderResponseDto> {
  const {
    includeItems,
    includeShippingDetails,
    includeBillingDetails,
    includeStatusHistory
  } = options;

  // Base order data mapping
  const responseDto: OrderResponseDto = {
    id: order.id,
    orderNumber: order.orderNumber,
    userId: order.userId,
    status: order.status.name,
    statusId: order.status.id,
    totalAmount: order.totalAmount,
    subtotal: order.subtotal,
    tax: order.tax,
    shippingCost: order.shippingCost,
    discountAmount: order.discountAmount,
    currency: order.currency || 'USD',
    promoCode: order.promoCode,
    notes: order.notes,
    paymentId: order.paymentId,
    createdAt: order.createdAt,
    updatedAt: order.updatedAt,
    paidAt: order.paidAt,
    shippedAt: order.shippedAt,
    deliveredAt: order.deliveredAt,
    cancelledAt: order.cancelledAt,
    refundedAt: order.refundedAt
  };

  // Include items if requested and available
  if (includeItems && order.items) {
    responseDto.items = order.items.map(item => this.mapOrderItemToDto(item));
  }

  // Include shipping details if requested and available
  if (includeShippingDetails && order.shippingDetails) {
    responseDto.shippingDetails = this.mapShippingDetailsToDto(order.shippingDetails);
  }

  // Include billing details if requested and available
  if (includeBillingDetails && order.billingDetails) {
    responseDto.billingDetails = this.mapBillingDetailsToDto(order.billingDetails);
  }

  // Include status history if requested and available
  if (includeStatusHistory && order.statusHistory) {
    responseDto.statusHistory = order.statusHistory.map(history =>
      this.mapStatusHistoryToDto(history)
    );
  }

  return responseDto;
}
```

### 4.2. Order Item Entity to DTO

```typescript
/**
 * Maps an OrderItem entity to OrderItemDto
 */
mapOrderItemToDto(item: OrderItem): OrderItemDto {
  return {
    id: item.id,
    productId: item.productId,
    variantId: item.variantId,
    productName: item.productName,
    quantity: item.quantity,
    unitPrice: item.unitPrice,
    totalPrice: item.totalPrice,
    metadata: item.metadata
  };
}
```

### 4.3. Shipping Details Entity to DTO

```typescript
/**
 * Maps OrderShippingDetails entity to ShippingDetailsDto
 */
mapShippingDetailsToDto(
  shippingDetails: OrderShippingDetails
): ShippingDetailsDto {
  return {
    recipientName: shippingDetails.recipientName,
    shippingAddressLine1: shippingDetails.shippingAddressLine1,
    shippingAddressLine2: shippingDetails.shippingAddressLine2,
    shippingCity: shippingDetails.shippingCity,
    shippingState: shippingDetails.shippingState,
    shippingPostalCode: shippingDetails.shippingPostalCode,
    shippingCountry: shippingDetails.shippingCountry,
    shippingPhoneNumber: shippingDetails.shippingPhoneNumber,
    shippingMethod: shippingDetails.shippingMethod,
    carrier: shippingDetails.carrier,
    trackingNumber: shippingDetails.trackingNumber,
    trackingUrl: this.generateTrackingUrl(
      shippingDetails.carrier,
      shippingDetails.trackingNumber
    ),
    estimatedDeliveryDate: shippingDetails.estimatedDeliveryDate,
    deliveryType: shippingDetails.deliveryType,
    specialInstructions: shippingDetails.specialInstructions
  };
}
```

### 4.4. Billing Details Entity to DTO

```typescript
/**
 * Maps OrderBillingDetails entity to BillingDetailsDto
 */
mapBillingDetailsToDto(
  billingDetails: OrderBillingDetails
): BillingDetailsDto {
  // Filter out sensitive payment details based on configuration
  const maskCardDetails = this.configService.get<boolean>('MASK_PAYMENT_DETAILS', true);

  return {
    billingName: billingDetails.billingName,
    billingAddressLine1: billingDetails.billingAddressLine1,
    billingAddressLine2: billingDetails.billingAddressLine2,
    billingCity: billingDetails.billingCity,
    billingState: billingDetails.billingState,
    billingPostalCode: billingDetails.billingPostalCode,
    billingCountry: billingDetails.billingCountry,
    billingPhoneNumber: billingDetails.billingPhoneNumber,
    billingEmail: billingDetails.billingEmail,
    paymentMethod: billingDetails.paymentMethod,
    // If masking is enabled, only return masked version of payment details
    paymentMethodDetails: maskCardDetails ?
      this.maskPaymentMethodDetails(billingDetails.paymentMethodDetails) :
      billingDetails.paymentMethodDetails
  };
}
```

### 4.5. Status History Entity to DTO

```typescript
/**
 * Maps OrderStatusHistory entity to StatusHistoryDto
 */
mapStatusHistoryToDto(
  history: OrderStatusHistory
): StatusHistoryDto {
  return {
    id: history.id,
    statusId: history.statusId,
    statusName: history.status?.name,
    changedAt: history.createdAt,
    changedBy: history.changedBy,
    notes: history.notes,
    metadata: history.metadata
  };
}
```

### 4.6. Create Order DTO to Entity

```typescript
/**
 * Maps CreateOrderDto to Order entity
 */
createDtoToEntity(
  createOrderDto: CreateOrderDto,
  userId: string,
  initialStatus: OrderStatus
): Order {
  const order = new Order();
  order.userId = userId;
  order.orderNumber = this.generateOrderNumber();
  order.status = initialStatus;
  order.statusId = initialStatus.id;
  order.totalAmount = this.calculateOrderTotal(createOrderDto);
  order.subtotal = this.calculateSubtotal(createOrderDto.items);
  order.tax = createOrderDto.tax || 0;
  order.shippingCost = createOrderDto.shippingCost || 0;
  order.discountAmount = createOrderDto.discountAmount || 0;
  order.currency = createOrderDto.currency || 'USD';
  order.promoCode = createOrderDto.promoCode;
  order.notes = createOrderDto.notes;
  order.metadata = createOrderDto.metadata;

  return order;
}
```

## 5. Helper Methods

### 5.1. Mask Payment Details

```typescript
/**
 * Masks sensitive payment method details
 */
private maskPaymentMethodDetails(
  details: any
): any {
  if (!details) {
    return details;
  }

  const maskedDetails = { ...details };

  // Mask card number if present
  if (maskedDetails.cardNumber) {
    maskedDetails.cardNumber = this.maskCardNumber(maskedDetails.cardNumber);
  }

  // Only expose last 4 digits if full card number is present
  if (maskedDetails.last4 && maskedDetails.cardNumber) {
    delete maskedDetails.cardNumber;
  }

  // Remove CVV if present
  if (maskedDetails.cvv) {
    delete maskedDetails.cvv;
  }

  return maskedDetails;
}

/**
 * Masks a credit card number
 */
private maskCardNumber(cardNumber: string): string {
  if (!cardNumber) {
    return cardNumber;
  }

  // Keep only first 6 and last 4 digits visible
  const visibleDigits = 10; // 6 at start + 4 at end
  const maskedLength = cardNumber.length - visibleDigits;

  if (maskedLength <= 0) {
    return cardNumber;
  }

  return cardNumber.substring(0, 6) +
         '*'.repeat(maskedLength) +
         cardNumber.substring(cardNumber.length - 4);
}
```

### 5.2. Shipping Tracking URL Generation

```typescript
/**
 * Generate carrier-specific tracking URL
 */
private generateTrackingUrl(carrier: string, trackingNumber: string): string {
  if (!carrier || !trackingNumber) {
    return null;
  }

  const carrierUrls = {
    'UPS': `https://www.ups.com/track?tracknum=${trackingNumber}`,
    'FEDEX': `https://www.fedex.com/fedextrack/?trknbr=${trackingNumber}`,
    'USPS': `https://tools.usps.com/go/TrackConfirmAction?tLabels=${trackingNumber}`,
    'DHL': `https://www.dhl.com/en/express/tracking.html?AWB=${trackingNumber}`,
  };

  return carrierUrls[carrier.toUpperCase()] || null;
}
```

### 5.3. Order Number Generation

```typescript
/**
 * Generates a unique order number
 */
private generateOrderNumber(): string {
  const prefix = 'ORD';
  const timestamp = Date.now().toString().slice(-8);
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
  return `${prefix}-${timestamp}${random}`;
}
```

### 5.4. Total Calculation

```typescript
/**
 * Calculates the total amount for an order
 */
private calculateOrderTotal(createOrderDto: CreateOrderDto): number {
  const subtotal = this.calculateSubtotal(createOrderDto.items);
  const tax = createOrderDto.tax || 0;
  const shippingCost = createOrderDto.shippingCost || 0;
  const discountAmount = createOrderDto.discountAmount || 0;

  return +(subtotal + tax + shippingCost - discountAmount).toFixed(2);
}

/**
 * Calculates the subtotal for order items
 */
private calculateSubtotal(items: CreateOrderItemDto[]): number {
  return +(items.reduce(
    (sum, item) => sum + (item.unitPrice * item.quantity),
    0
  )).toFixed(2);
}
```

## 6. Role-Based Mapping

The OrderMapper also supports role-based mapping to control what data is visible to different user roles:

```typescript
/**
 * Maps an order entity to an appropriate DTO based on user role
 */
async toRoleBasedResponseDto(
  order: Order,
  userRole: string
): Promise<OrderResponseDto> {
  // Default options for field inclusion
  const options = {
    includeItems: true,
    includeShippingDetails: true,
    includeBillingDetails: true,
    includeStatusHistory: false
  };

  // Customize options based on user role
  switch (userRole) {
    case 'admin':
      // Admins can see everything
      options.includeStatusHistory = true;
      break;

    case 'customer-service':
      // Customer service can see most details but not full payment info
      options.includeStatusHistory = true;
      break;

    case 'shipping':
      // Shipping only needs order items and shipping details
      options.includeBillingDetails = false;
      break;

    case 'customer':
      // Customers see their order details but not internal history
      break;

    default:
      // Minimal access for other roles
      options.includeBillingDetails = false;
  }

  return this.toResponseDto(order, options);
}
```

## 7. Bulk Mapping

For operations involving multiple orders, the mapper provides efficient bulk mapping methods:

```typescript
/**
 * Maps multiple order entities to DTOs
 */
async toBulkResponseDto(
  orders: Order[],
  options: {
    includeItems?: boolean;
    includeShippingDetails?: boolean;
    includeBillingDetails?: boolean;
    includeStatusHistory?: boolean;
  } = {}
): Promise<OrderResponseDto[]> {
  return Promise.all(
    orders.map(order => this.toResponseDto(order, options))
  );
}
```

## 8. Testing Strategy

The `OrderMapper` should be thoroughly tested to ensure accurate data transformation:

```typescript
describe("OrderMapper", () => {
  let mapper: OrderMapper;
  let configService: ConfigService;
  let userService: UserService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        OrderMapper,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn().mockImplementation((key, defaultValue) => {
              if (key === "MASK_PAYMENT_DETAILS") {
                return true;
              }
              return defaultValue;
            }),
          },
        },
        {
          provide: UserService,
          useValue: {
            getUserById: jest.fn(),
          },
        },
      ],
    }).compile();

    mapper = module.get<OrderMapper>(OrderMapper);
    configService = module.get<ConfigService>(ConfigService);
    userService = module.get<UserService>(UserService);
  });

  describe("toResponseDto", () => {
    it("should map an order entity to response DTO", async () => {
      // Test implementation
    });

    it("should properly mask payment details", async () => {
      // Test implementation
    });

    it("should include only requested relations", async () => {
      // Test implementation
    });
  });

  // Additional test cases
});
```

## 9. Performance Considerations

- **Lazy Loading**: Map only necessary fields to minimize processing
- **Cached Lookups**: Cache reference data used in mapping (e.g., user names)
- **Field Selection**: Support inclusion/exclusion of specific fields for efficiency
- **Batch Processing**: Use bulk mapping for collections to minimize overhead

## 10. References

- [Order Entity Model](../../02-data-model-setup/01-order-entity.md)
- [Order Item Entity Model](../../02-data-model-setup/02-order-item-entity.md)
- [Order DTO Definitions](../../04-api-endpoints/00-api-index.md)
- [Order Service](./02-order-service.md)
- [Order Controller](./01-order-controller.md)
