# Order Domain Events

## Overview

This document defines the domain events used in the Order Service. These events represent significant state changes in the order domain and are used for both event sourcing and integration with other services.

## Event Structure

All order domain events follow a common structure:

```typescript
export interface DomainEvent {
  eventId: string;           // Unique identifier for the event
  aggregateId: string;       // ID of the entity this event relates to (orderId)
  aggregateType: string;     // Type of entity (always "ORDER" for this service)
  eventType: string;         // Type of event
  timestamp: Date;           // When the event occurred
  version: number;           // Schema version for the event
  metadata: {                // Additional contextual information
    userId: string;          // User who triggered the event
    correlationId: string;   // ID linking related operations
    causationId: string;     // ID of event that caused this event
    source: string;          // Service that generated the event
  };
  data: any;                 // Event-specific payload
}
```

## Order Lifecycle Events

### OrderCreatedEvent

Emitted when a new order is created.

```typescript
export interface OrderCreatedEvent extends DomainEvent {
  eventType: 'ORDER_CREATED';
  aggregateType: 'ORDER';
  data: {
    customerId: string;
    orderNumber: string;
    items: Array<{
      productId: string;
      sku: string;
      name: string;
      quantity: number;
      unitPrice: number;
      totalPrice: number;
    }>;
    billingDetails: {
      firstName: string;
      lastName: string;
      address: {
        line1: string;
        line2?: string;
        city: string;
        state: string;
        postalCode: string;
        country: string;
      };
      paymentMethod: string;
    };
    shippingDetails: {
      firstName: string;
      lastName: string;
      address: {
        line1: string;
        line2?: string;
        city: string;
        state: string;
        postalCode: string;
        country: string;
      };
      shippingMethod: string;
      shippingCost: number;
    };
    subtotal: number;
    tax: number;
    shippingCost: number;
    discount: number;
    total: number;
    couponCodes?: string[];
    notes?: string;
  };
}
```

### OrderPaymentPendingEvent

Emitted when an order is awaiting payment.

```typescript
export interface OrderPaymentPendingEvent extends DomainEvent {
  eventType: 'ORDER_PAYMENT_PENDING';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    paymentMethod: string;
    amount: number;
    paymentDueBy?: Date;
    paymentUrl?: string;
  };
}
```

### OrderPaymentCompletedEvent

Emitted when payment for an order has been successfully processed.

```typescript
export interface OrderPaymentCompletedEvent extends DomainEvent {
  eventType: 'ORDER_PAYMENT_COMPLETED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    paymentId: string;
    paymentMethod: string;
    amount: number;
    transactionReference: string;
    paymentTime: Date;
  };
}
```

### OrderPaymentFailedEvent

Emitted when a payment attempt fails.

```typescript
export interface OrderPaymentFailedEvent extends DomainEvent {
  eventType: 'ORDER_PAYMENT_FAILED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    paymentMethod: string;
    amount: number;
    failureReason: string;
    failureCode?: string;
    attemptCount: number;
  };
}
```

### OrderProcessingEvent

Emitted when the order moves to processing stage (after payment is completed).

```typescript
export interface OrderProcessingEvent extends DomainEvent {
  eventType: 'ORDER_PROCESSING';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    processedBy?: string;
    estimatedShippingDate?: Date;
    warehouseId?: string;
  };
}
```

### OrderItemsAllocatedEvent

Emitted when inventory has been allocated for the order items.

```typescript
export interface OrderItemsAllocatedEvent extends DomainEvent {
  eventType: 'ORDER_ITEMS_ALLOCATED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    allocations: Array<{
      productId: string;
      sku: string;
      quantity: number;
      warehouseId: string;
      allocationId: string;
    }>;
    allocationCompleteTime: Date;
    allAllocationSuccessful: boolean;
    partialAllocationDetails?: {
      fullyAllocatedItems: string[];
      partiallyAllocatedItems: Array<{
        sku: string;
        requested: number;
        allocated: number;
      }>;
      unallocatedItems: string[];
    };
  };
}
```

### OrderShippedEvent

Emitted when an order has been shipped.

```typescript
export interface OrderShippedEvent extends DomainEvent {
  eventType: 'ORDER_SHIPPED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    trackingNumber: string;
    carrier: string;
    shippingMethod: string;
    shippingDate: Date;
    estimatedDeliveryDate?: Date;
    parcels: Array<{
      trackingNumber: string;
      weight: number;
      dimensions?: {
        length: number;
        width: number;
        height: number;
        unit: string;
      };
      items: Array<{
        sku: string;
        quantity: number;
      }>;
    }>;
    shippedFrom: {
      warehouseId: string;
      warehouseName: string;
    };
  };
}
```

### OrderDeliveredEvent

Emitted when an order has been delivered.

```typescript
export interface OrderDeliveredEvent extends DomainEvent {
  eventType: 'ORDER_DELIVERED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    deliveryDate: Date;
    signedBy?: string;
    deliveryNotes?: string;
    proofOfDeliveryUrl?: string;
  };
}
```

### OrderCancelledEvent

Emitted when an order is cancelled.

```typescript
export interface OrderCancelledEvent extends DomainEvent {
  eventType: 'ORDER_CANCELLED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    cancellationReason: string;
    cancelledBy: string;
    cancelledItems: Array<{
      sku: string;
      quantity: number;
    }>;
    refundInitiated: boolean;
    refundAmount?: number;
    refundTransactionId?: string;
  };
}
```

### OrderRefundedEvent

Emitted when a refund is processed for an order.

```typescript
export interface OrderRefundedEvent extends DomainEvent {
  eventType: 'ORDER_REFUNDED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    refundAmount: number;
    refundReason: string;
    refundedBy: string;
    refundTransactionId: string;
    fullRefund: boolean;
    refundedItems?: Array<{
      sku: string;
      quantity: number;
      amount: number;
    }>;
  };
}
```

## Order Modification Events

### OrderItemsAddedEvent

Emitted when items are added to an existing order.

```typescript
export interface OrderItemsAddedEvent extends DomainEvent {
  eventType: 'ORDER_ITEMS_ADDED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    addedItems: Array<{
      productId: string;
      sku: string;
      name: string;
      quantity: number;
      unitPrice: number;
      totalPrice: number;
    }>;
    previousSubtotal: number;
    newSubtotal: number;
    previousTotal: number;
    newTotal: number;
    addedBy: string;
  };
}
```

### OrderItemsRemovedEvent

Emitted when items are removed from an existing order.

```typescript
export interface OrderItemsRemovedEvent extends DomainEvent {
  eventType: 'ORDER_ITEMS_REMOVED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    removedItems: Array<{
      productId: string;
      sku: string;
      quantity: number;
    }>;
    previousSubtotal: number;
    newSubtotal: number;
    previousTotal: number;
    newTotal: number;
    removedBy: string;
    removalReason: string;
  };
}
```

### ShippingAddressChangedEvent

Emitted when the shipping address for an order is changed.

```typescript
export interface ShippingAddressChangedEvent extends DomainEvent {
  eventType: 'SHIPPING_ADDRESS_CHANGED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    previousAddress: {
      line1: string;
      line2?: string;
      city: string;
      state: string;
      postalCode: string;
      country: string;
    };
    newAddress: {
      line1: string;
      line2?: string;
      city: string;
      state: string;
      postalCode: string;
      country: string;
    };
    changedBy: string;
    reasonForChange: string;
    shippingCostChanged: boolean;
    previousShippingCost?: number;
    newShippingCost?: number;
  };
}
```

## Order Processing Events

### OrderNoteAddedEvent

Emitted when a note is added to an order.

```typescript
export interface OrderNoteAddedEvent extends DomainEvent {
  eventType: 'ORDER_NOTE_ADDED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    note: string;
    addedBy: string;
    visibleToCustomer: boolean;
    noteType: string; // CUSTOMER_SERVICE, FULFILLMENT, SYSTEM, etc.
  };
}
```

### OrderPriorityChangedEvent

Emitted when an order's priority level is changed.

```typescript
export interface OrderPriorityChangedEvent extends DomainEvent {
  eventType: 'ORDER_PRIORITY_CHANGED';
  aggregateType: 'ORDER';
  data: {
    orderNumber: string;
    previousPriority: string; // STANDARD, EXPEDITED, RUSH, etc.
    newPriority: string;
    changedBy: string;
    reasonForChange: string;
  };
}
```

## Event Usage

These domain events serve multiple purposes within the Order Service and the broader e-commerce system:

1. **Event Sourcing**: Events are used to reconstruct order state
2. **Integration**: Events provide integration points with other services
3. **Analytics**: Events feed into analytics systems for business intelligence
4. **Audit**: Events provide a complete audit trail for compliance and investigation

## Event Storage

All events are stored in the event store with appropriate indexing to support:

1. Retrieval of all events for a specific order
2. Retrieval of events by type
3. Retrieval of events within a time window
4. Retrieval of events for analytics queries