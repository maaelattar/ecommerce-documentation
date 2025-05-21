# Product Events Specification

## 1. Overview

This document details the domain events published by the Product Service related to the lifecycle and state changes of Products and Product Variants.

All events follow the `StandardMessage<T>` structure as detailed in the [Event Publishing Overview](./00-overview.md#5-general-event-structure), using RabbitMQ as the message broker.

## 2. Product Events

### 2.1. `ProductCreated`

- **`messageType`**: `ProductCreated`
- **`messageVersion`**: `1.0`
- **Description**: Published when a new product (including its initial variant(s)) is successfully created in the Product Service.
- **Trigger**: Successful completion of the `createProduct` method in `ProductService`.
- **`partitionKey`**: The `productId` of the newly created product.
- **Payload Schema**:
  ```json
  {
    "productId": "uuid",
    "name": "string",
    "description": "string",
    "sku": "string", // SKU of the main/default variant if applicable, or just product-level SKU
    "brand": "string",
    "tags": ["string"],
    "status": "string", // e.g., "DRAFT", "ACTIVE", "ARCHIVED"
    "isHazardousMaterial": false,
    "countryOfOrigin": "string",
    "listPrice": {
        "amount": "decimal",
        "currency": "string"
    },
    "categories": [
      {
        "categoryId": "uuid",
        "name": "string"
      }
    ],
    "variants": [
      {
        "variantId": "uuid",
        "sku": "string",
        "name": "string", // e.g., "Red, Large"
        "attributes": {"key": "value"}, // e.g., {"color": "Red", "size": "Large"}
        "listPrice": {
            "amount": "decimal",
            "currency": "string"
        },
        "stockKeepingUnit": "string"
        // Initial stock information might be handled by Inventory Service directly or via a separate event
      }
    ],
    "metadata": {"key": "value"},
    "createdAt": "ISO8601",
    "createdBy": "string" // User or system that created it
  }
  ```
- **Potential Consumers**: Search Service (index new product), Analytics Service, Notification Service (e.g., to merchandising team).

### 2.2. `ProductUpdated`

- **`messageType`**: `ProductUpdated`
- **`messageVersion`**: `1.0`
- **Description**: Published when significant attributes of an existing product or its variants are updated.
- **Trigger**: Successful completion of methods like `updateProduct`, `updateProductVariant` in `ProductService`.
- **`partitionKey`**: The `productId` of the updated product.
- **Payload Schema**:
  ```json
  {
    "productId": "uuid",
    "updatedFields": ["string"], // e.g., ["name", "description", "variants.attributes"], can be specific
    "name": "string", // Current value
    "description": "string", // Current value
    "brand": "string", // Current value
    "tags": ["string"], // Current value
    "status": "string", // Current value
    // ... other potentially updated top-level fields ...
    "variants": [
      {
        "variantId": "uuid",
        "sku": "string",
        "name": "string",
        "attributes": {"key": "value"},
        "listPrice": {
            "amount": "decimal",
            "currency": "string"
        },
        "updatedFields": ["string"] // Specific to this variant, e.g., ["attributes.color", "listPrice.amount"]
      }
    ],
    "metadata": {"key": "value"},
    "updatedAt": "ISO8601",
    "updatedBy": "string"
  }
  ```
- **Note**: The payload should contain enough information for most consumers to act without needing to call back to the Product Service immediately. It might include both changed fields and key identifiers.
- **Potential Consumers**: Search Service (re-index product), Cache invalidation services, Analytics Service.

### 2.3. `ProductDeleted`

- **`messageType`**: `ProductDeleted`
- **`messageVersion`**: `1.0`
- **Description**: Published when a product is successfully marked as deleted or archived (soft delete usually preferred).
- **Trigger**: Successful completion of `deleteProduct` method.
- **`partitionKey`**: The `productId` of the deleted product.
- **Payload Schema**:
  ```json
  {
    "productId": "uuid",
    "deletedAt": "ISO8601",
    "deletedBy": "string",
    "deletionReason": "string" // Optional
  }
  ```
- **Potential Consumers**: Search Service (remove product from index), Order Service (handle implications for existing orders if any), Analytics Service.

### 2.4. `ProductStatusChanged`

- **`messageType`**: `ProductStatusChanged`
- **`messageVersion`**: `1.0`
- **Description**: Published specifically when a product's primary status changes (e.g., Draft -> Active, Active -> Archived).
- **Trigger**: Successful update of product status.
- **`partitionKey`**: The `productId`.
- **Payload Schema**:
  ```json
  {
    "productId": "uuid",
    "oldStatus": "string",
    "newStatus": "string",
    "changedAt": "ISO8601",
    "changedBy": "string"
  }
  ```
- **Potential Consumers**: Search Service, Order Service (e.g., prevent orders for inactive products), UI update services.

### 2.5. `ProductVariantAdded`

- **`messageType`**: `ProductVariantAdded`
- **`messageVersion`**: `1.0`
- **Description**: Published when a new variant is added to an existing product.
- **Trigger**: Successful completion of `addProductVariant`.
- **`partitionKey`**: The `productId` to which the variant was added.
- **Payload Schema**:
  ```json
  {
    "productId": "uuid",
    "variant": {
      "variantId": "uuid",
      "sku": "string",
      "name": "string",
      "attributes": {"key": "value"},
      "listPrice": {
        "amount": "decimal",
        "currency": "string"
      },
      "createdAt": "ISO8601"
    }
  }
  ```
- **Potential Consumers**: Inventory Service (to initialize stock record - though this might be an internal call or a direct API call too), Search Service.

### 2.6. `ProductVariantUpdated`

- **`messageType`**: `ProductVariantUpdated`
- **`messageVersion`**: `1.0`
- **Description**: Published when attributes of a specific product variant are updated.
- **Trigger**: Successful completion of `updateProductVariant`.
- **`partitionKey`**: The `productId`.
- **Payload Schema**:
  ```json
  {
    "productId": "uuid",
    "variantId": "uuid",
    "updatedFields": ["string"], // e.g., ["sku", "attributes.size", "listPrice.amount"]
    "variant": {
      // Current state of the variant, similar to ProductVariantAdded payload
      "sku": "string",
      "name": "string",
      "attributes": {"key": "value"},
      "listPrice": {
        "amount": "decimal",
        "currency": "string"
      },
      "updatedAt": "ISO8601"
    }
  }
  ```
- **Potential Consumers**: Search Service, Cache invalidation services.

### 2.7. `ProductVariantRemoved`

- **`messageType`**: `ProductVariantRemoved`
- **`messageVersion`**: `1.0`
- **Description**: Published when a product variant is removed from a product.
- **Trigger**: Successful completion of `removeProductVariant`.
- **`partitionKey`**: The `productId`.
- **Payload Schema**:
  ```json
  {
    "productId": "uuid",
    "variantId": "uuid",
    "removedAt": "ISO8601",
    "removedBy": "string"
  }
  ```
- **Potential Consumers**: Search Service, Inventory Service (to archive stock record).

## 3. Considerations

- **Granularity**: The `ProductUpdated` event can be broad. Depending on consumer needs, more granular events (e.g., `ProductInventoryDetailsUpdated` if Product Service were to cache/reflect some inventory summary) might be considered, but the current model defers inventory specifics to the Inventory Service.
- **Payload Size**: Payloads should be comprehensive enough to be useful but not excessively large. For very large objects or frequent updates, consider publishing only key identifiers and a list of changed fields, requiring consumers to fetch details if needed (though this increases coupling).
- **Relationship to Event Sourcing**: The Product Service is implemented using an event sourcing pattern, where all state changes are first recorded as domain events in an internal event store (DynamoDB). The integration events detailed in this document (e.g., `ProductCreated`, `ProductUpdated`) are published to RabbitMQ for consumption by other services and are derived from, or directly correspond to, these internal domain events. The Product Service builds its queryable state (read models, likely in PostgreSQL) by projecting from its internal event stream.

## 4. References

- [Event Publishing Overview](./00-overview.md)
- [Product Entity Model](../../02-data-model-setup/02a-product-entity.md) 