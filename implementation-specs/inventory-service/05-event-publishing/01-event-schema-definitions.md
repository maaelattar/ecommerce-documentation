# Inventory Service Event Schema Definitions

## 1. Overview

This document defines the schemas for the **payloads** of events published by the Inventory Service. All events adhere to the `StandardMessage<T>` envelope provided by the `@ecommerce-platform/rabbitmq-event-utils` shared library. This ensures a consistent event structure across the platform, facilitates validation, and supports schema evolution.

## 2. Standard Event Envelope

All events published by the Inventory Service use the `StandardMessage<T>` envelope. The `T` represents the specific event payload defined in this document.

```typescript
// From @ecommerce-platform/rabbitmq-event-utils
export interface StandardMessage<P> {
  messageId: string;      // UUID v4, unique for this message
  messageType: string;    // e.g., "InventoryItemCreated", "StockLevelChanged"
  timestamp: string;      // ISO-8601 UTC timestamp of event occurrence
  source: "inventory-service"; // Originating service
  partitionKey?: string;   // e.g., productId, sku, or warehouseId for routing/partitioning
  correlationId?: string;  // Optional: for tracing operations across services
  payload: P;             // Event-specific data (defined below)
  version: string;        // Schema version of the P (payload), e.g., "1.0", "1.1", "2.0"
}
```

Key fields in `StandardMessage<T>`:
*   `messageId`: Unique identifier for the message.
*   `messageType`: Defines the kind of event (e.g., `InventoryItemCreated`).
*   `source`: Hardcoded to `inventory-service` for events from this service.
*   `payload`: The actual data specific to the event (see payload definitions below).
*   `version`: The version of the *payload schema*. This allows consumers to handle different versions of an event payload correctly.

## 3. Payload Schema Versioning Strategy

Payload schemas (the `P` in `StandardMessage<P>`) use a versioning scheme (e.g., "1.0", "1.1", "2.0") stored in the `version` field of the `StandardMessage` envelope. This typically follows semantic versioning principles for the payload:

1.  **MAJOR (e.g., 1.x to 2.0)**: Breaking changes to the payload that require consumers to update their processing logic (e.g., removing a field, changing a field's type non-compatibly).
2.  **MINOR (e.g., 1.0 to 1.1)**: Backward-compatible additions to the payload schema (e.g., adding new optional fields).
3.  **PATCH (e.g., 1.0.0 to 1.0.1, if using SemVer strictly for payload)**: Backward-compatible fixes or clarifications to the schema description (often, minor version increments are sufficient for payload changes).

## 4. Inventory Management Event Payloads

These interfaces define the structure of the `payload` field for various inventory-related events.

### 4.1. InventoryItemCreated Event

*   **`messageType`**: `InventoryItemCreated`
*   **Description**: Published when a new inventory item (e.g., a specific SKU in a specific warehouse) is first registered in the system.

```typescript
// Payload for StandardMessage<InventoryItemCreatedPayload>
// where version might be "1.0"
export interface InventoryItemCreatedPayload {
  inventoryItemId: string; // UUID, Unique ID for this inventory record
  productId: string;       // UUID, Reference to the global Product ID
  sku: string;             // Stock Keeping Unit
  variantId?: string;      // Optional: If the product has variants
  warehouseId: string;     // UUID, Warehouse where this item is stocked
  location?: string;       // Optional: Specific bin, shelf, etc.
  initialQuantityAvailable: number;
  reorderThreshold?: number;
  targetStockLevel?: number;
  itemStatus: "active" | "inactive" | "discontinued";
  attributes?: Record<string, any>; // e.g., color, size if not part of variantId
  supplierId?: string;     // Optional: Primary supplier for this item
  costPrice?: number;      // Optional: Cost of the item
  currency?: string;       // Optional: Currency for costPrice
}
```

### 4.2. StockLevelChanged Event

*   **`messageType`**: `StockLevelChanged`
*   **Description**: Published whenever the available quantity of an inventory item changes due to sales, returns, new stock arrivals, adjustments, etc.

```typescript
// Payload for StandardMessage<StockLevelChangedPayload>
// where version might be "1.0"
export interface StockLevelChangedPayload {
  inventoryItemId: string; // UUID
  productId: string;       // UUID
  sku: string;
  variantId?: string;
  warehouseId: string;     // UUID
  location?: string;
  changeType: "sale" | "return" | "receipt" | "adjustment" | "shrinkage" | "transferIn" | "transferOut";
  previousQuantityAvailable: number;
  newQuantityAvailable: number;
  quantityChanged: number; // (newQuantityAvailable - previousQuantityAvailable)
  quantityReserved?: number; // Current reserved quantity (informational)
  quantityOnHand?: number;   // Current on-hand quantity (available + reserved)
  transactionId?: string;  // Optional: ID of the transaction causing the change (e.g., orderId, shipmentId, adjustmentId)
  reason?: string;         // Optional: For adjustments or shrinkage
  notes?: string;          // Optional: Additional details
}
```

### 4.3. InventoryReserved Event

*   **`messageType`**: `InventoryReserved`
*   **Description**: Published when a specific quantity of an inventory item is reserved, typically for a customer order.

```typescript
// Payload for StandardMessage<InventoryReservedPayload>
// where version might be "1.0"
export interface InventoryReservedPayload {
  reservationId: string;   // UUID, Unique ID for this reservation
  inventoryItemId: string; // UUID
  productId: string;       // UUID
  sku: string;
  variantId?: string;
  warehouseId: string;     // UUID
  orderId: string;         // UUID, The order this reservation is for
  orderItemId?: string;    // Optional: Specific item within the order
  quantityReserved: number;
  reservationTimestamp: string; // ISO-8601 UTC
  expiresAt?: string;      // Optional: ISO-8601 UTC, if reservation has an expiry
  previousQuantityAvailable: number;
  newQuantityAvailable: number; // (previousQuantityAvailable - quantityReserved)
  previousQuantityReserved: number;
  newQuantityReserved: number; // (previousQuantityReserved + quantityReserved)
}
```

### 4.4. InventoryReservationCancelled Event

*   **`messageType`**: `InventoryReservationCancelled`
*   **Description**: Published when a previously made reservation is cancelled (e.g., order cancelled, item removed from order).

```typescript
// Payload for StandardMessage<InventoryReservationCancelledPayload>
// where version might be "1.0"
export interface InventoryReservationCancelledPayload {
  reservationId: string;   // UUID, The reservation that was cancelled
  inventoryItemId: string; // UUID
  productId: string;       // UUID
  sku: string;
  variantId?: string;
  warehouseId: string;     // UUID
  orderId: string;         // UUID
  quantityReleased: number; // The quantity that was un-reserved
  cancellationReason?: string;
  previousQuantityAvailable: number;
  newQuantityAvailable: number; // (previousQuantityAvailable + quantityReleased)
  previousQuantityReserved: number;
  newQuantityReserved: number; // (previousQuantityReserved - quantityReleased)
}
```

### 4.5. InventoryReservationFulfilled Event (or use StockLevelChanged)

*   **`messageType`**: `InventoryReservationFulfilled` (Alternatively, a `StockLevelChanged` event with `changeType: "fulfillment"` might cover this)
*   **Description**: Published when reserved stock is confirmed as shipped or picked up, effectively consuming it from on-hand stock.

```typescript
// Payload for StandardMessage<InventoryReservationFulfilledPayload>
// where version might be "1.0"
export interface InventoryReservationFulfilledPayload {
  reservationId: string;   // UUID
  inventoryItemId: string; // UUID
  productId: string;       // UUID
  sku: string;
  variantId?: string;
  warehouseId: string;     // UUID
  orderId: string;         // UUID
  quantityFulfilled: number;
  fulfillmentTimestamp: string; // ISO-8601 UTC
  previousQuantityReserved: number;
  newQuantityReserved: number; // (previousQuantityReserved - quantityFulfilled)
  previousQuantityOnHand: number; // If tracking on-hand separately
  newQuantityOnHand: number;   // (previousQuantityOnHand - quantityFulfilled)
  shipmentId?: string;      // Optional: ID of the shipment
}
```

### 4.6. LowStockThresholdReached Event

*   **`messageType`**: `LowStockThresholdReached`
*   **Description**: Published when an inventory item's available quantity drops below its defined reorder threshold.

```typescript
// Payload for StandardMessage<LowStockThresholdReachedPayload>
// where version might be "1.0"
export interface LowStockThresholdReachedPayload {
  inventoryItemId: string; // UUID
  productId: string;       // UUID
  sku: string;
  variantId?: string;
  warehouseId: string;     // UUID
  currentQuantityAvailable: number;
  reorderThreshold: number;
  targetStockLevel?: number;
  productName?: string; // Informational
}
```

### 4.7. OutOfStock Event

*   **`messageType`**: `OutOfStock`
*   **Description**: Published when an inventory item's available quantity reaches zero (or less, if overselling is possible and then corrected).

```typescript
// Payload for StandardMessage<OutOfStockPayload>
// where version might be "1.0"
export interface OutOfStockPayload {
  inventoryItemId: string; // UUID
  productId: string;       // UUID
  sku: string;
  variantId?: string;
  warehouseId: string;     // UUID
  productName?: string; // Informational
  lastAvailableTimestamp?: string; // When it became out of stock
}
```

## 5. Example: `StockLevelChanged` Event

Below is an example of what a complete `StockLevelChanged` event message would look like, using the `StandardMessage<T>` envelope.

```json
{
  "messageId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "messageType": "StockLevelChanged",
  "timestamp": "2023-10-27T10:30:00Z",
  "source": "inventory-service",
  "partitionKey": "prod-98765", // Assuming productId is used as partitionKey
  "correlationId": "corr-order-001",
  "payload": {
    "inventoryItemId": "inv-item-00123",
    "productId": "prod-98765",
    "sku": "TSHIRT-BLK-LG",
    "warehouseId": "wh-main-01",
    "changeType": "sale",
    "previousQuantityAvailable": 100,
    "newQuantityAvailable": 99,
    "quantityChanged": -1,
    "quantityReserved": 5,
    "quantityOnHand": 104,
    "transactionId": "order-001-item-1"
  },
  "version": "1.0"
}
```

## 6. JSON Schema for Payloads (Conceptual)

While TypeScript interfaces define the structure, for cross-language validation or when consumers don't use TypeScript, JSON Schemas for each payload version can be derived.

**Example Snippet for `StockLevelChangedPayload` v1.0 JSON Schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StockLevelChangedPayloadV1",
  "description": "Payload for the StockLevelChanged event, version 1.0",
  "type": "object",
  "properties": {
    "inventoryItemId": { "type": "string", "format": "uuid" },
    "productId": { "type": "string", "format": "uuid" },
    "sku": { "type": "string" },
    "variantId": { "type": ["string", "null"] },
    "warehouseId": { "type": "string", "format": "uuid" },
    "location": { "type": ["string", "null"] },
    "changeType": { "type": "string", "enum": ["sale", "return", "receipt", "adjustment", "shrinkage", "transferIn", "transferOut"] },
    "previousQuantityAvailable": { "type": "integer" },
    "newQuantityAvailable": { "type": "integer" },
    "quantityChanged": { "type": "integer" },
    "quantityReserved": { "type": ["integer", "null"], "minimum": 0 },
    "quantityOnHand": { "type": ["integer", "null"], "minimum": 0 },
    "transactionId": { "type": ["string", "null"] },
    "reason": { "type": ["string", "null"] },
    "notes": { "type": ["string", "null"] }
  },
  "required": [
    "inventoryItemId",
    "productId",
    "sku",
    "warehouseId",
    "changeType",
    "previousQuantityAvailable",
    "newQuantityAvailable",
    "quantityChanged"
  ]
}
```

This JSON schema would describe the `payload` part of the `StandardMessage` when `messageType` is `StockLevelChanged` and `version` is `"1.0"`.
Consumers can use the `messageType` and `version` from the `StandardMessage` envelope to select the correct payload schema for validation.
