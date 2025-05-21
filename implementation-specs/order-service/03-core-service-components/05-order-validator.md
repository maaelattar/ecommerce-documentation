# Order Validator

## 1. Overview

The `OrderValidator` is a specialized service responsible for validating order data throughout the order lifecycle. This component ensures data integrity, prevents invalid state transitions, and enforces business rules before operations are committed to the database. By centralizing validation logic, the `OrderValidator` provides a consistent approach to data quality across all order operations.

## 2. Responsibilities

- Validating new order requests against business rules
- Ensuring data consistency and integrity
- Preventing invalid order state transitions
- Validating address information for shipping and billing
- Verifying product details and quantities
- Enforcing order update permissions
- Checking preconditions for order operations (cancel, refund, etc.)
- Providing clear validation error messages

## 3. Class Definition

```typescript
@Injectable()
export class OrderValidator {
  constructor(
    private readonly configService: ConfigService,
    private readonly productService: ProductService,
    private readonly userService: UserService,
    private readonly inventoryService: InventoryService
  ) {}

  // Validator methods defined below
}
```

## 4. Core Validation Methods

### 4.1. Validate Create Order Request

```typescript
/**
 * Validates a new order creation request
 */
async validateCreateOrder(
  createOrderDto: CreateOrderDto,
  userId: string
): Promise<ValidationResult> {
  const errors: ValidationError[] = [];

  // Check if user exists
  if (!(await this.userService.userExists(userId))) {
    errors.push({
      field: 'userId',
      message: `User with ID ${userId} does not exist`
    });
    // Return early if user doesn't exist
    return { isValid: errors.length === 0, errors };
  }

  // Validate basic order data
  this.validateBasicOrderData(createOrderDto, errors);

  // Validate shipping information
  this.validateShippingDetails(createOrderDto.shippingDetails, errors);

  // Validate billing information
  this.validateBillingDetails(createOrderDto.billingDetails, errors);

  // Validate order items
  await this.validateOrderItems(createOrderDto.items, errors);

  // Validate totals
  this.validateOrderTotals(createOrderDto, errors);

  // Return validation result
  return {
    isValid: errors.length === 0,
    errors
  };
}
```

### 4.2. Validate Order Update

```typescript
/**
 * Validates an order update request
 */
async validateUpdateOrder(
  order: Order,
  updateOrderDto: UpdateOrderDto,
  userRole: string
): Promise<ValidationResult> {
  const errors: ValidationError[] = [];

  // Validate permission to update based on role and order state
  this.validateUpdatePermission(order, userRole, errors);

  // Only validate fields that are included in the update
  if (updateOrderDto.shippingDetails) {
    this.validateShippingDetails(updateOrderDto.shippingDetails, errors);
  }

  if (updateOrderDto.billingDetails) {
    this.validateBillingDetails(updateOrderDto.billingDetails, errors);
  }

  if (updateOrderDto.items) {
    // Only allow item updates for orders in certain states
    if (!['CREATED', 'PENDING_PAYMENT'].includes(order.status.name)) {
      errors.push({
        field: 'items',
        message: `Cannot update order items when order is in ${order.status.name} state`
      });
    } else {
      await this.validateOrderItems(updateOrderDto.items, errors);
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}
```

### 4.3. Validate Order Status Transition

```typescript
/**
 * Validates if a status transition is allowed
 */
async validateStatusTransition(
  order: Order,
  newStatusId: number,
  userRole: string
): Promise<ValidationResult> {
  const errors: ValidationError[] = [];

  // Get the current status and new status
  const currentStatus = order.status.name;
  const newStatus = await this.getStatusNameById(newStatusId);

  if (!newStatus) {
    errors.push({
      field: 'statusId',
      message: `Invalid status ID: ${newStatusId}`
    });
    return { isValid: false, errors };
  }

  // Define allowed transitions by current status
  const allowedTransitions: Record<string, string[]> = {
    'CREATED': ['PENDING_PAYMENT', 'CANCELLED'],
    'PENDING_PAYMENT': ['PAID', 'PAYMENT_FAILED', 'CANCELLED'],
    'PAID': ['PROCESSING', 'REFUNDED', 'CANCELLED'],
    'PROCESSING': ['READY_FOR_SHIPMENT', 'CANCELLED', 'REFUNDED'],
    'READY_FOR_SHIPMENT': ['SHIPPED', 'CANCELLED', 'REFUNDED'],
    'SHIPPED': ['DELIVERED', 'DELIVERY_FAILED', 'RETURNED'],
    'DELIVERED': ['COMPLETED', 'RETURNED'],
    'DELIVERY_FAILED': ['PROCESSING', 'RETURNED', 'CANCELLED'],
    'RETURNED': ['REFUNDED', 'COMPLETED'],
    'CANCELLED': ['REFUNDED'],
    'REFUNDED': [],
    'COMPLETED': ['RETURNED'],
    'PAYMENT_FAILED': ['PENDING_PAYMENT', 'CANCELLED']
  };

  // Check if the transition is allowed
  if (!allowedTransitions[currentStatus]?.includes(newStatus)) {
    errors.push({
      field: 'statusId',
      message: `Cannot transition from ${currentStatus} to ${newStatus}`
    });
  }

  // Check if user has permission for this transition
  this.validateTransitionPermission(currentStatus, newStatus, userRole, errors);

  // Execute state-specific validation
  await this.validateStateSpecificRules(order, newStatus, errors);

  return {
    isValid: errors.length === 0,
    errors
  };
}
```

### 4.4. Validate Order Cancellation

```typescript
/**
 * Validates if an order can be cancelled
 */
async validateOrderCancellation(
  order: Order,
  userRole: string,
  reason: string
): Promise<ValidationResult> {
  const errors: ValidationError[] = [];

  // Can only cancel orders in certain states
  const cancellableStates = [
    'CREATED',
    'PENDING_PAYMENT',
    'PAID',
    'PROCESSING',
    'READY_FOR_SHIPMENT'
  ];

  if (!cancellableStates.includes(order.status.name)) {
    errors.push({
      field: 'status',
      message: `Cannot cancel order in ${order.status.name} state`
    });
  }

  // Check if user has permission to cancel
  if (userRole === 'customer' && order.status.name === 'SHIPPED') {
    errors.push({
      field: 'userRole',
      message: 'Customers cannot cancel shipped orders'
    });
  }

  // Reason is required
  if (!reason || reason.trim().length === 0) {
    errors.push({
      field: 'reason',
      message: 'Cancellation reason is required'
    });
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}
```

## 5. Field-Specific Validation Methods

### 5.1. Validate Basic Order Data

```typescript
/**
 * Validates basic order fields
 */
private validateBasicOrderData(
  orderData: CreateOrderDto | UpdateOrderDto,
  errors: ValidationError[]
): void {
  // Currency validation
  if (orderData.currency && !this.isValidCurrency(orderData.currency)) {
    errors.push({
      field: 'currency',
      message: `Invalid currency code: ${orderData.currency}`
    });
  }

  // Notes length validation
  if (orderData.notes && orderData.notes.length > 1000) {
    errors.push({
      field: 'notes',
      message: 'Notes cannot exceed 1000 characters'
    });
  }

  // PromoCode validation if provided
  if (orderData.promoCode) {
    if (orderData.promoCode.length < 3 || orderData.promoCode.length > 20) {
      errors.push({
        field: 'promoCode',
        message: 'Promo code must be between 3 and 20 characters'
      });
    }
  }
}
```

### 5.2. Validate Shipping Details

```typescript
/**
 * Validates shipping details
 */
private validateShippingDetails(
  shippingDetails: ShippingDetailsDto,
  errors: ValidationError[]
): void {
  if (!shippingDetails) {
    errors.push({
      field: 'shippingDetails',
      message: 'Shipping details are required'
    });
    return;
  }

  // Required fields
  const requiredFields = [
    'recipientName',
    'shippingAddressLine1',
    'shippingCity',
    'shippingState',
    'shippingPostalCode',
    'shippingCountry'
  ];

  requiredFields.forEach(field => {
    if (!shippingDetails[field]) {
      errors.push({
        field: `shippingDetails.${field}`,
        message: `${this.formatFieldName(field)} is required`
      });
    }
  });

  // Validate shipping method if provided
  if (shippingDetails.shippingMethod) {
    const validShippingMethods = [
      'STANDARD',
      'EXPRESS',
      'OVERNIGHT',
      'TWO_DAY',
      'INTERNATIONAL'
    ];

    if (!validShippingMethods.includes(shippingDetails.shippingMethod)) {
      errors.push({
        field: 'shippingDetails.shippingMethod',
        message: `Invalid shipping method: ${shippingDetails.shippingMethod}`
      });
    }
  }

  // Validate shipping country
  if (shippingDetails.shippingCountry && !this.isValidCountryCode(shippingDetails.shippingCountry)) {
    errors.push({
      field: 'shippingDetails.shippingCountry',
      message: `Invalid country code: ${shippingDetails.shippingCountry}`
    });
  }

  // Validate phone number format if provided
  if (shippingDetails.shippingPhoneNumber && !this.isValidPhoneNumber(shippingDetails.shippingPhoneNumber)) {
    errors.push({
      field: 'shippingDetails.shippingPhoneNumber',
      message: 'Invalid phone number format'
    });
  }
}
```

### 5.3. Validate Billing Details

```typescript
/**
 * Validates billing details
 */
private validateBillingDetails(
  billingDetails: BillingDetailsDto,
  errors: ValidationError[]
): void {
  if (!billingDetails) {
    errors.push({
      field: 'billingDetails',
      message: 'Billing details are required'
    });
    return;
  }

  // Required fields
  const requiredFields = [
    'billingName',
    'billingAddressLine1',
    'billingCity',
    'billingState',
    'billingPostalCode',
    'billingCountry',
    'billingEmail',
    'paymentMethod'
  ];

  requiredFields.forEach(field => {
    if (!billingDetails[field]) {
      errors.push({
        field: `billingDetails.${field}`,
        message: `${this.formatFieldName(field)} is required`
      });
    }
  });

  // Validate email format
  if (billingDetails.billingEmail && !this.isValidEmail(billingDetails.billingEmail)) {
    errors.push({
      field: 'billingDetails.billingEmail',
      message: 'Invalid email format'
    });
  }

  // Validate payment method
  if (billingDetails.paymentMethod) {
    const validPaymentMethods = [
      'CREDIT_CARD',
      'DEBIT_CARD',
      'PAYPAL',
      'APPLE_PAY',
      'GOOGLE_PAY',
      'BANK_TRANSFER',
      'GIFT_CARD'
    ];

    if (!validPaymentMethods.includes(billingDetails.paymentMethod)) {
      errors.push({
        field: 'billingDetails.paymentMethod',
        message: `Invalid payment method: ${billingDetails.paymentMethod}`
      });
    }

    // Validate payment method specific details
    if (billingDetails.paymentMethod === 'CREDIT_CARD' || billingDetails.paymentMethod === 'DEBIT_CARD') {
      this.validateCardDetails(billingDetails.paymentMethodDetails, errors);
    }
  }

  // Validate billing country
  if (billingDetails.billingCountry && !this.isValidCountryCode(billingDetails.billingCountry)) {
    errors.push({
      field: 'billingDetails.billingCountry',
      message: `Invalid country code: ${billingDetails.billingCountry}`
    });
  }
}
```

### 5.4. Validate Order Items

```typescript
/**
 * Validates order items
 */
private async validateOrderItems(
  items: CreateOrderItemDto[] | OrderItemDto[],
  errors: ValidationError[]
): Promise<void> {
  if (!items || items.length === 0) {
    errors.push({
      field: 'items',
      message: 'Order must contain at least one item'
    });
    return;
  }

  // Validate maximum items
  const maxItems = this.configService.get<number>('MAX_ORDER_ITEMS', 100);
  if (items.length > maxItems) {
    errors.push({
      field: 'items',
      message: `Order cannot contain more than ${maxItems} items`
    });
    return;
  }

  // Validate each item
  for (let i = 0; i < items.length; i++) {
    const item = items[i];

    // Required fields
    if (!item.productId) {
      errors.push({
        field: `items[${i}].productId`,
        message: 'Product ID is required'
      });
    }

    // Quantity validation
    if (!item.quantity || item.quantity <= 0) {
      errors.push({
        field: `items[${i}].quantity`,
        message: 'Quantity must be greater than 0'
      });
    }

    // Unit price validation
    if (item.unitPrice !== undefined && item.unitPrice < 0) {
      errors.push({
        field: `items[${i}].unitPrice`,
        message: 'Unit price cannot be negative'
      });
    }

    // Check if product exists and is available
    if (item.productId) {
      try {
        const product = await this.productService.getProductById(item.productId);

        // Check if product is available
        if (!product.isActive) {
          errors.push({
            field: `items[${i}].productId`,
            message: `Product ${item.productId} is not available`
          });
        }

        // Check if variant exists if specified
        if (item.variantId && !product.variants?.some(v => v.id === item.variantId)) {
          errors.push({
            field: `items[${i}].variantId`,
            message: `Variant ${item.variantId} does not exist for product ${item.productId}`
          });
        }

        // Check inventory availability if needed
        const isInStock = await this.inventoryService.checkAvailability(
          item.productId,
          item.variantId,
          item.quantity
        );

        if (!isInStock) {
          errors.push({
            field: `items[${i}].quantity`,
            message: `Insufficient inventory for product ${item.productId}`
          });
        }
      } catch (error) {
        errors.push({
          field: `items[${i}].productId`,
          message: `Product ${item.productId} not found`
        });
      }
    }
  }
}
```

### 5.5. Validate Order Totals

```typescript
/**
 * Validates order totals and calculations
 */
private validateOrderTotals(
  orderData: CreateOrderDto,
  errors: ValidationError[]
): void {
  // Calculate expected subtotal
  const calculatedSubtotal = orderData.items.reduce(
    (sum, item) => sum + item.unitPrice * item.quantity,
    0
  );

  // Validate subtotal if provided
  if (orderData.subtotal !== undefined) {
    // Allow for small floating point differences
    if (Math.abs(orderData.subtotal - calculatedSubtotal) > 0.01) {
      errors.push({
        field: 'subtotal',
        message: `Subtotal does not match sum of item totals. Expected: ${calculatedSubtotal}`
      });
    }
  }

  // Validate total amount if provided
  if (orderData.totalAmount !== undefined) {
    const calculatedTotal =
      calculatedSubtotal +
      (orderData.tax || 0) +
      (orderData.shippingCost || 0) -
      (orderData.discountAmount || 0);

    // Allow for small floating point differences
    if (Math.abs(orderData.totalAmount - calculatedTotal) > 0.01) {
      errors.push({
        field: 'totalAmount',
        message: `Total amount does not match calculation. Expected: ${calculatedTotal}`
      });
    }
  }

  // Validate discount amount
  if (orderData.discountAmount !== undefined && orderData.discountAmount < 0) {
    errors.push({
      field: 'discountAmount',
      message: 'Discount amount cannot be negative'
    });
  }

  // Validate shipping cost
  if (orderData.shippingCost !== undefined && orderData.shippingCost < 0) {
    errors.push({
      field: 'shippingCost',
      message: 'Shipping cost cannot be negative'
    });
  }

  // Validate tax
  if (orderData.tax !== undefined && orderData.tax < 0) {
    errors.push({
      field: 'tax',
      message: 'Tax cannot be negative'
    });
  }
}
```

## 6. Helper Methods

### 6.1. Format Field Name

```typescript
/**
 * Formats field name for error messages
 */
private formatFieldName(camelCase: string): string {
  // Add space before capital letters and uppercase the first letter
  const formatted = camelCase
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase());

  return formatted;
}
```

### 6.2. Validate Email

```typescript
/**
 * Validates email format
 */
private isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}
```

### 6.3. Validate Phone Number

```typescript
/**
 * Validates phone number format
 */
private isValidPhoneNumber(phoneNumber: string): boolean {
  // Simple validation for demonstration
  // In production, consider using a library like libphonenumber-js
  const phoneRegex = /^\+?[0-9]{10,15}$/;
  return phoneRegex.test(phoneNumber);
}
```

### 6.4. Validate Currency Code

```typescript
/**
 * Validates currency code
 */
private isValidCurrency(currency: string): boolean {
  const validCurrencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CNY'];
  return validCurrencies.includes(currency);
}
```

### 6.5. Validate Country Code

```typescript
/**
 * Validates country code
 */
private isValidCountryCode(countryCode: string): boolean {
  // List of ISO 3166-1 alpha-2 country codes
  const validCountryCodes = [
    'US', 'CA', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'CN', 'AU',
    // ... other country codes
  ];

  return validCountryCodes.includes(countryCode);
}
```

### 6.6. Validate Card Details

```typescript
/**
 * Validates credit/debit card details
 */
private validateCardDetails(
  cardDetails: any,
  errors: ValidationError[]
): void {
  if (!cardDetails) {
    errors.push({
      field: 'billingDetails.paymentMethodDetails',
      message: 'Card details are required'
    });
    return;
  }

  // Validate card number if provided
  if (cardDetails.cardNumber) {
    if (!this.isValidCardNumber(cardDetails.cardNumber)) {
      errors.push({
        field: 'billingDetails.paymentMethodDetails.cardNumber',
        message: 'Invalid card number'
      });
    }
  } else if (cardDetails.last4) {
    // If only last4 is provided, make sure it's 4 digits
    if (!/^\d{4}$/.test(cardDetails.last4)) {
      errors.push({
        field: 'billingDetails.paymentMethodDetails.last4',
        message: 'Last 4 digits must be numeric and 4 digits long'
      });
    }
  } else {
    errors.push({
      field: 'billingDetails.paymentMethodDetails',
      message: 'Card number or last 4 digits are required'
    });
  }

  // Validate expiration date
  if (!cardDetails.expiryMonth || !cardDetails.expiryYear) {
    errors.push({
      field: 'billingDetails.paymentMethodDetails.expiry',
      message: 'Expiration date is required'
    });
  } else {
    const expiryMonth = parseInt(cardDetails.expiryMonth, 10);
    const expiryYear = parseInt(cardDetails.expiryYear, 10);

    // Validate month
    if (isNaN(expiryMonth) || expiryMonth < 1 || expiryMonth > 12) {
      errors.push({
        field: 'billingDetails.paymentMethodDetails.expiryMonth',
        message: 'Invalid expiration month'
      });
    }

    // Validate year
    const currentYear = new Date().getFullYear();
    if (isNaN(expiryYear) || expiryYear < currentYear || expiryYear > currentYear + 20) {
      errors.push({
        field: 'billingDetails.paymentMethodDetails.expiryYear',
        message: 'Invalid expiration year'
      });
    }

    // Check if the card is expired
    const currentMonth = new Date().getMonth() + 1; // January is 0
    if (expiryYear === currentYear && expiryMonth < currentMonth) {
      errors.push({
        field: 'billingDetails.paymentMethodDetails.expiry',
        message: 'Card is expired'
      });
    }
  }

  // Validate CVV if provided
  if (cardDetails.cvv && !/^\d{3,4}$/.test(cardDetails.cvv)) {
    errors.push({
      field: 'billingDetails.paymentMethodDetails.cvv',
      message: 'CVV must be 3 or 4 digits'
    });
  }
}
```

## 7. Permission Validation

### 7.1. Validate Update Permission

```typescript
/**
 * Validates permission to update an order
 */
private validateUpdatePermission(
  order: Order,
  userRole: string,
  errors: ValidationError[]
): void {
  // Define which roles can update orders in which states
  const allowedRoles: Record<string, string[]> = {
    'CREATED': ['admin', 'customer', 'customer-service'],
    'PENDING_PAYMENT': ['admin', 'customer', 'customer-service'],
    'PAID': ['admin', 'customer-service'],
    'PROCESSING': ['admin', 'customer-service'],
    'READY_FOR_SHIPMENT': ['admin', 'shipping', 'customer-service'],
    'SHIPPED': ['admin', 'shipping', 'customer-service'],
    'DELIVERED': ['admin', 'customer-service'],
    'CANCELLED': ['admin'],
    'REFUNDED': ['admin'],
    'COMPLETED': ['admin'],
    'PAYMENT_FAILED': ['admin', 'customer', 'customer-service'],
    'DELIVERY_FAILED': ['admin', 'shipping', 'customer-service'],
    'RETURNED': ['admin', 'customer-service']
  };

  const currentStatus = order.status.name;

  // Check if the user role is allowed to update this order
  if (!allowedRoles[currentStatus]?.includes(userRole)) {
    errors.push({
      field: 'userRole',
      message: `User with role ${userRole} cannot update an order in ${currentStatus} state`
    });
  }
}
```

### 7.2. Validate Transition Permission

```typescript
/**
 * Validates permission to transition order status
 */
private validateTransitionPermission(
  currentStatus: string,
  newStatus: string,
  userRole: string,
  errors: ValidationError[]
): void {
  // Define which roles can perform which transitions
  const transitionPermissions: Record<string, Record<string, string[]>> = {
    'CREATED': {
      'PENDING_PAYMENT': ['admin', 'customer', 'customer-service'],
      'CANCELLED': ['admin', 'customer', 'customer-service']
    },
    'PENDING_PAYMENT': {
      'PAID': ['admin', 'payment-service'],
      'PAYMENT_FAILED': ['admin', 'payment-service'],
      'CANCELLED': ['admin', 'customer', 'customer-service']
    },
    'PAID': {
      'PROCESSING': ['admin', 'customer-service'],
      'REFUNDED': ['admin', 'customer-service'],
      'CANCELLED': ['admin', 'customer-service']
    },
    'PROCESSING': {
      'READY_FOR_SHIPMENT': ['admin', 'customer-service'],
      'CANCELLED': ['admin', 'customer-service'],
      'REFUNDED': ['admin', 'customer-service']
    },
    'READY_FOR_SHIPMENT': {
      'SHIPPED': ['admin', 'shipping', 'customer-service'],
      'CANCELLED': ['admin', 'customer-service'],
      'REFUNDED': ['admin', 'customer-service']
    },
    'SHIPPED': {
      'DELIVERED': ['admin', 'shipping', 'customer-service'],
      'DELIVERY_FAILED': ['admin', 'shipping', 'customer-service']
    },
    'DELIVERED': {
      'COMPLETED': ['admin', 'customer-service'],
      'RETURNED': ['admin', 'customer', 'customer-service']
    },
    'DELIVERY_FAILED': {
      'PROCESSING': ['admin', 'customer-service'],
      'RETURNED': ['admin', 'shipping', 'customer-service'],
      'CANCELLED': ['admin', 'customer-service']
    },
    'RETURNED': {
      'REFUNDED': ['admin', 'customer-service'],
      'COMPLETED': ['admin', 'customer-service']
    },
    'CANCELLED': {
      'REFUNDED': ['admin', 'customer-service']
    },
    'PAYMENT_FAILED': {
      'PENDING_PAYMENT': ['admin', 'customer', 'customer-service'],
      'CANCELLED': ['admin', 'customer-service']
    }
  };

  // Check if the user role is allowed to perform this transition
  if (!transitionPermissions[currentStatus]?.[newStatus]?.includes(userRole)) {
    errors.push({
      field: 'userRole',
      message: `User with role ${userRole} cannot transition order from ${currentStatus} to ${newStatus}`
    });
  }
}
```

### 7.3. Validate State-Specific Rules

```typescript
/**
 * Validates state-specific business rules
 */
private async validateStateSpecificRules(
  order: Order,
  newStatus: string,
  errors: ValidationError[]
): Promise<void> {
  switch (newStatus) {
    case 'PAID':
      // Ensure payment ID exists
      if (!order.paymentId) {
        errors.push({
          field: 'paymentId',
          message: 'Payment ID is required to mark order as paid'
        });
      }
      break;

    case 'SHIPPED':
      // Ensure tracking info exists
      if (!order.shippingDetails?.trackingNumber) {
        errors.push({
          field: 'shippingDetails.trackingNumber',
          message: 'Tracking number is required to mark order as shipped'
        });
      }

      if (!order.shippingDetails?.carrier) {
        errors.push({
          field: 'shippingDetails.carrier',
          message: 'Carrier information is required to mark order as shipped'
        });
      }
      break;

    case 'REFUNDED':
      // Ensure refund amount doesn't exceed order total
      if (order.refundAmount && order.refundAmount > order.totalAmount) {
        errors.push({
          field: 'refundAmount',
          message: 'Refund amount cannot exceed order total'
        });
      }
      break;

    case 'DELIVERED':
      // Ensure shipped date exists
      if (!order.shippedAt) {
        errors.push({
          field: 'shippedAt',
          message: 'Shipped date is required to mark order as delivered'
        });
      }
      break;

    case 'RETURNED':
      // Ensure delivered date exists
      if (!order.deliveredAt) {
        errors.push({
          field: 'deliveredAt',
          message: 'Delivered date is required to mark order as returned'
        });
      }

      // Check return eligibility period
      const returnWindowDays = this.configService.get<number>('RETURN_WINDOW_DAYS', 30);
      if (order.deliveredAt) {
        const deliveredDate = new Date(order.deliveredAt);
        const today = new Date();
        const daysSinceDelivery = Math.floor((today.getTime() - deliveredDate.getTime()) / (1000 * 60 * 60 * 24));

        if (daysSinceDelivery > returnWindowDays) {
          errors.push({
            field: 'deliveredAt',
            message: `Return window of ${returnWindowDays} days has expired`
          });
        }
      }
      break;
  }
}
```

## 8. Utility Methods

### 8.1. Get Status Name By ID

```typescript
/**
 * Retrieves status name by ID
 */
private async getStatusNameById(statusId: number): Promise<string | null> {
  // Map of status IDs to names (in a real implementation, this would be fetched from database)
  const statusMap = {
    1: 'CREATED',
    2: 'PENDING_PAYMENT',
    3: 'PAID',
    4: 'PROCESSING',
    5: 'READY_FOR_SHIPMENT',
    6: 'SHIPPED',
    7: 'DELIVERED',
    8: 'CANCELLED',
    9: 'REFUNDED',
    10: 'COMPLETED',
    11: 'PAYMENT_FAILED',
    12: 'DELIVERY_FAILED',
    13: 'RETURNED'
  };

  return statusMap[statusId] || null;
}
```

### 8.2. Validate Card Number

```typescript
/**
 * Validates credit card number using Luhn algorithm
 */
private isValidCardNumber(cardNumber: string): boolean {
  // Remove spaces and dashes
  cardNumber = cardNumber.replace(/[\s-]/g, '');

  // Check if the card number contains only digits
  if (!/^\d+$/.test(cardNumber)) {
    return false;
  }

  // Check length (most card numbers are 13-19 digits)
  if (cardNumber.length < 13 || cardNumber.length > 19) {
    return false;
  }

  // Luhn algorithm (checksum)
  let sum = 0;
  let double = false;

  // Loop through the card number from right to left
  for (let i = cardNumber.length - 1; i >= 0; i--) {
    let digit = parseInt(cardNumber.charAt(i), 10);

    if (double) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }

    sum += digit;
    double = !double;
  }

  // The card is valid if the sum is divisible by 10
  return sum % 10 === 0;
}
```

## 9. References

- [Order Entity Model](../../02-data-model-setup/01-order-entity.md)
- [Order Business Rules](../../requirements/order-business-rules.md)
- [Order Service](./02-order-service.md)
- [Payment Service Integration](../06-integration-points/01-payment-service-integration.md)
- [Product Service](../../product-service/03-core-service-components/01-product-service.md)
