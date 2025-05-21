# Product Domain Events for Event Sourcing

## 1. Overview

This document specifies the domain events that represent state changes to product aggregates in our event sourcing implementation. These events are stored in the event store and form the basis for reconstructing product state, creating audit trails, and driving projections.

## 2. Event Naming Convention

All product events follow this naming convention:
- Format: `Product{Action}{Entity}` where:
  - `Product` is the aggregate type prefix
  - `Action` describes what happened (past tense)
  - `Entity` identifies the subentity affected (optional)

## 3. Base Event Interface

All events share a common structure:

```typescript
interface DomainEvent<T> {
  eventId: string;       // UUID for the event
  entityId: string;      // ID of the aggregate this event applies to
  eventType: string;     // Type of event (class name)
  eventTime: string;     // ISO 8601 timestamp
  version: string;       // Schema version
  userId: string;        // User who triggered the event
  correlationId: string; // For tracing related events
  data: T;               // Event-specific payload
}
```

## 4. Product Lifecycle Events

### 4.1. ProductCreated

**Event Type:** `ProductCreated`  
**Description:** A new product has been created.

```typescript
interface ProductCreatedData {
  name: string;
  description: string;
  brand: string;
  status: ProductStatus; // "DRAFT" | "ACTIVE" | "INACTIVE" | "DISCONTINUED"
  sku: string;
  tags: string[];
  attributes: Record<string, string | number | boolean>; // Product-level attributes
  metadata: Record<string, any>;
  categoryIds: string[];
  listPrice?: {
    amount: number;
    currency: string;
  };
  createdBy: string; // User ID
}
```

### 4.2. ProductBasicInfoUpdated

**Event Type:** `ProductBasicInfoUpdated`  
**Description:** Basic product information has been updated.

```typescript
interface ProductBasicInfoUpdatedData {
  name?: string;
  description?: string;
  brand?: string;
  sku?: string;
  tags?: string[];
  attributes?: Record<string, string | number | boolean>;
  metadata?: Record<string, any>;
  updatedBy: string; // User ID
}
```

### 4.3. ProductStatusChanged

**Event Type:** `ProductStatusChanged`  
**Description:** Product status has changed.

```typescript
interface ProductStatusChangedData {
  oldStatus: ProductStatus;
  newStatus: ProductStatus;
  reason?: string;
  effectiveDate?: string; // ISO 8601 timestamp, if scheduled
  updatedBy: string; // User ID
}
```

### 4.4. ProductCategoriesUpdated

**Event Type:** `ProductCategoriesUpdated`  
**Description:** Product category assignments have changed.

```typescript
interface ProductCategoriesUpdatedData {
  addedCategoryIds: string[];
  removedCategoryIds: string[];
  updatedBy: string; // User ID
}
```

### 4.5. ProductDeleted

**Event Type:** `ProductDeleted`  
**Description:** Product was marked as deleted (logical delete).

```typescript
interface ProductDeletedData {
  reason?: string;
  deletedBy: string; // User ID
}
```

## 5. Product Variant Events

### 5.1. ProductVariantAdded

**Event Type:** `ProductVariantAdded`  
**Description:** A new variant has been added to a product.

```typescript
interface ProductVariantAddedData {
  variantId: string;
  sku: string;
  name?: string;
  attributes: Record<string, string | number | boolean>;
  listPrice?: {
    amount: number;
    currency: string;
  };
  stockKeepingUnit: string;
  isDefault: boolean;
  createdBy: string; // User ID
}
```

### 5.2. ProductVariantUpdated

**Event Type:** `ProductVariantUpdated`  
**Description:** A variant has been updated.

```typescript
interface ProductVariantUpdatedData {
  variantId: string;
  sku?: string;
  name?: string;
  attributes?: Record<string, string | number | boolean>;
  stockKeepingUnit?: string;
  isDefault?: boolean;
  updatedBy: string; // User ID
}
```

### 5.3. ProductVariantRemoved

**Event Type:** `ProductVariantRemoved`  
**Description:** A variant has been removed from a product.

```typescript
interface ProductVariantRemovedData {
  variantId: string;
  reason?: string;
  removedBy: string; // User ID
}
```

## 6. Product Price Events

### 6.1. ProductPriceUpdated

**Event Type:** `ProductPriceUpdated`  
**Description:** The base price of a product has been updated.

```typescript
interface ProductPriceUpdatedData {
  oldPrice?: {
    amount: number;
    currency: string;
  };
  newPrice: {
    amount: number;
    currency: string;
  };
  effectiveDate?: string; // ISO 8601 timestamp, if scheduled
  updatedBy: string; // User ID
}
```

### 6.2. ProductVariantPriceUpdated

**Event Type:** `ProductVariantPriceUpdated`  
**Description:** The price of a specific variant has been updated.

```typescript
interface ProductVariantPriceUpdatedData {
  variantId: string;
  oldPrice?: {
    amount: number;
    currency: string;
  };
  newPrice: {
    amount: number;
    currency: string;
  };
  effectiveDate?: string; // ISO 8601 timestamp, if scheduled
  updatedBy: string; // User ID
}
```

### 6.3. ProductDiscountApplied

**Event Type:** `ProductDiscountApplied`  
**Description:** A discount has been applied to a product.

```typescript
interface ProductDiscountAppliedData {
  discountId: string;
  discountType: string; // "PERCENTAGE" | "FIXED_AMOUNT" | "FREE_SHIPPING"
  discountValue: number;
  startDate: string; // ISO 8601 timestamp
  endDate?: string; // ISO 8601 timestamp
  conditions?: {
    minQuantity?: number;
    minOrderValue?: number;
    applicableSkus?: string[];
    userGroups?: string[];
  };
  appliedBy: string; // User ID
}
```

### 6.4. ProductDiscountRemoved

**Event Type:** `ProductDiscountRemoved`  
**Description:** A discount has been removed from a product.

```typescript
interface ProductDiscountRemovedData {
  discountId: string;
  reason?: string;
  removedBy: string; // User ID
}
```

## 7. Product Relation Events

### 7.1. ProductRelatedProductsUpdated

**Event Type:** `ProductRelatedProductsUpdated`  
**Description:** Related products for cross-selling/up-selling have been updated.

```typescript
interface ProductRelatedProductsUpdatedData {
  addedRelations: Array<{
    productId: string;
    relationType: string; // "SIMILAR" | "ACCESSORY" | "REPLACEMENT" | "UPSELL"
  }>;
  removedRelations: Array<{
    productId: string;
    relationType: string;
  }>;
  updatedBy: string; // User ID
}
```

### 7.2. ProductMediaAdded

**Event Type:** `ProductMediaAdded`  
**Description:** Media (image, video, document) has been added to a product.

```typescript
interface ProductMediaAddedData {
  mediaId: string;
  mediaType: string; // "IMAGE" | "VIDEO" | "DOCUMENT"
  url: string;
  title?: string;
  altText?: string;
  sortOrder?: number;
  variantId?: string; // If specific to a variant
  isPrimary: boolean;
  addedBy: string; // User ID
}
```

### 7.3. ProductMediaUpdated

**Event Type:** `ProductMediaUpdated`  
**Description:** Media item has been updated.

```typescript
interface ProductMediaUpdatedData {
  mediaId: string;
  url?: string;
  title?: string;
  altText?: string;
  sortOrder?: number;
  isPrimary?: boolean;
  updatedBy: string; // User ID
}
```

### 7.4. ProductMediaRemoved

**Event Type:** `ProductMediaRemoved`  
**Description:** Media item has been removed from a product.

```typescript
interface ProductMediaRemovedData {
  mediaId: string;
  removedBy: string; // User ID
}
```

## 8. Using Events to Reconstruct State

When loading a product entity, the system:

1. Retrieves all events for the product in sequence order
2. Applies each event to build the current state
3. Optionally uses snapshots to optimize loading

Example:

```typescript
class Product {
  // State properties
  id: string;
  name: string;
  description: string;
  // ... other properties
  variants: Map<string, ProductVariant>;
  
  // Keep track of version for optimistic concurrency
  version: number = 0;
  
  // Apply method processes events to reconstruct state
  apply(event: DomainEvent<any>): void {
    switch (event.eventType) {
      case 'ProductCreated':
        this.applyProductCreated(event.data);
        break;
      case 'ProductBasicInfoUpdated':
        this.applyProductBasicInfoUpdated(event.data);
        break;
      case 'ProductVariantAdded':
        this.applyProductVariantAdded(event.data);
        break;
      // ... other event handlers
    }
    this.version++;
  }
  
  private applyProductCreated(data: ProductCreatedData): void {
    this.name = data.name;
    this.description = data.description;
    this.brand = data.brand;
    this.status = data.status;
    // ... set other properties
  }
  
  // ... other apply methods
}