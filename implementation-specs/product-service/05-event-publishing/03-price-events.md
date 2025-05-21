# Price & Discount Events Specification

## 1. Overview

This document details the domain events published by the Product Service related to product prices and discounts.

All events follow the `StandardMessage<T>` structure as detailed in the [Event Publishing Overview](./00-overview.md#5-general-event-structure), using RabbitMQ as the message broker.

## 2. Price Events

### 2.1. `ProductPriceUpdated`

- **`messageType`**: `ProductPriceUpdated`
- **`messageVersion`**: `1.0`
- **Description**: Published when the price of a product variant is updated (e.g., base price, sale price).
- **Trigger**: Successful completion of `updatePrice` or similar methods in `PriceDiscountService`.
- **`partitionKey`**: The `productVariantId` for which the price was updated. (Note: The payload can also include `productId` for easier context if needed by consumers).
- **Payload Schema**:
  ```json
  {
    "productVariantId": "uuid",
    "productId": "uuid", // Parent product ID for context
    "oldPrice": {
      "baseAmount": "decimal",
      "saleAmount": "decimal", // Optional
      "currency": "string"
    },
    "newPrice": {
      "baseAmount": "decimal",
      "saleAmount": "decimal", // Optional
      "currency": "string",
      "effectiveFrom": "ISO8601", // Optional, if prices can be scheduled
      "effectiveUntil": "ISO8601" // Optional
    },
    "updatedAt": "ISO8601",
    "updatedBy": "string"
  }
  ```
- **Potential Consumers**: Search Service (update displayed price), Order Service (validate prices at checkout if needed, though typically Order Service might fetch current price), Analytics Service, Notification Service (e.g., for price drop alerts if subscribed by users).

## 3. Discount Events

### 3.1. `DiscountCreated`

- **`messageType`**: `DiscountCreated`
- **`messageVersion`**: `1.0`
- **Description**: Published when a new discount rule or promotion is created.
- **Trigger**: Successful completion of `createDiscount` in `PriceDiscountService`.
- **`partitionKey`**: The `discountId` of the newly created discount.
- **Payload Schema**:
  ```json
  {
    "discountId": "uuid",
    "name": "string",
    "description": "string",
    "type": "string", // e.g., "PERCENTAGE", "FIXED_AMOUNT", "BUY_X_GET_Y"
    "value": "decimal", // e.g., 10.00 (for 10% or $10)
    "conditions": "json_string_or_object", // e.g., { "minPurchaseAmount": 50, "applicableCategoryIds": ["uuid"] }
    "validFrom": "ISO8601",
    "validUntil": "ISO8601",
    "maxUses": "integer", // Optional
    "maxUsesPerUser": "integer", // Optional
    "isActive": "boolean",
    "createdAt": "ISO8601",
    "createdBy": "string"
  }
  ```
- **Potential Consumers**: Promotion Engine (if separate), Marketing tools, Analytics Service.

### 3.2. `DiscountUpdated`

- **`messageType`**: `DiscountUpdated`
- **`messageVersion`**: `1.0`
- **Description**: Published when an existing discount rule is updated.
- **Trigger**: Successful completion of `updateDiscount`.
- **`partitionKey`**: The `discountId`.
- **Payload Schema**:
  ```json
  {
    "discountId": "uuid",
    "updatedFields": ["string"], // e.g., ["description", "value", "validUntil"]
    // Include current state of all fields, similar to DiscountCreated payload
    "name": "string",
    "description": "string",
    "type": "string",
    "value": "decimal",
    "conditions": "json_string_or_object",
    "validFrom": "ISO8601",
    "validUntil": "ISO8601",
    "isActive": "boolean",
    "updatedAt": "ISO8601",
    "updatedBy": "string"
  }
  ```
- **Potential Consumers**: Promotion Engine, Marketing tools, Cache invalidation services.

### 3.3. `DiscountDeleted`

- **`messageType`**: `DiscountDeleted`
- **`messageVersion`**: `1.0`
- **Description**: Published when a discount rule is deleted or deactivated.
- **Trigger**: Successful completion of `deleteDiscount` or changing `isActive` to false.
- **`partitionKey`**: The `discountId`.
- **Payload Schema**:
  ```json
  {
    "discountId": "uuid",
    "deletedAt": "ISO8601", // Or "deactivatedAt"
    "deletedBy": "string"
  }
  ```
- **Potential Consumers**: Promotion Engine, Marketing tools.

### 3.4. `DiscountAppliedToProduct` (More Granular - Optional)

- **`messageType`**: `DiscountAppliedToProduct`
- **`messageVersion`**: `1.0`
- **Description**: Published when a specific discount is explicitly linked to a product or product variant (if the discount system supports direct assignment rather than only rule-based application).
- **Trigger**: Successful linking of a discount to a product.
- **`partitionKey`**: The `productVariantId` or `productId`.
- **Payload Schema**:
  ```json
  {
    "productVariantId": "uuid", // Or productId
    "discountId": "uuid",
    "appliedAt": "ISO8601",
    "appliedBy": "string"
  }
  ```
- **Potential Consumers**: Search Service (to show discounted prices), UI update services.

### 3.5. `DiscountRemovedFromProduct` (More Granular - Optional)

- **`messageType`**: `DiscountRemovedFromProduct`
- **`messageVersion`**: `1.0`
- **Description**: Published when a specific discount is unlinked from a product/variant.
- **Trigger**: Successful unlinking of a discount from a product.
- **`partitionKey`**: The `productVariantId` or `productId`.
- **Payload Schema**:
  ```json
  {
    "productVariantId": "uuid", // Or productId
    "discountId": "uuid",
    "removedAt": "ISO8601",
    "removedBy": "string"
  }
  ```
- **Potential Consumers**: Search Service, UI update services.

## 4. Considerations

- **Price vs. Discount Events**: `ProductPriceUpdated` is about the actual price stored for a variant. Discount events are about the rules that *might* affect the final calculated price. Systems consuming these might need both to accurately reflect pricing.
- **Dynamic Pricing**: If the system has very dynamic pricing or complex rule-based discount applications, the event strategy might need to be more sophisticated, potentially with events indicating a re-evaluation of a product's price is needed.

## 5. References

- [Event Publishing Overview](./00-overview.md)
- [Price and Discount Models](../../02-data-model-setup/02c-price-models.md) 