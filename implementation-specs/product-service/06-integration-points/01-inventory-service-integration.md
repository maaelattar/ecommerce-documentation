# Product Service Integration with Inventory Service

## 1. Overview

This document details the integration between the **Product Service** and the **Inventory Service**. The primary mode of interaction is **asynchronous and event-driven**, promoting loose coupling and resilience.

- **Product Data to Inventory Service**: Product Service publishes events (e.g., `ProductVariantCreated`, `ProductVariantUpdated`) when product or variant data changes. The Inventory Service consumes these events to create, update, or manage its corresponding inventory records.
- **Inventory Data to Product Service**: Inventory Service publishes events (e.g., `StockLevelChanged`, `InventoryStatusUpdated`) when stock levels or inventory statuses change. The Product Service (specifically its internal [Inventory Integration Component](../../03-core-service-components/03a-inventory-integration.md)) consumes these events to maintain an eventually consistent local cache or denormalized view of stock information. This local view is primarily used for display purposes (e.g., on product detail pages, listings) where near real-time accuracy from Inventory Service is not strictly required for the initial view.

Synchronous API calls from Product Service to Inventory Service are considered **exceptional** and must be clearly justified for specific use cases where immediate consistency is paramount and asynchronous patterns are insufficient.

This document outlines both the primary asynchronous flows and the exceptional synchronous API calls.

## 2. Asynchronous Integration Flows

### 2.1. Product/Variant Creation and Updates (Product Service -> Inventory Service)

- **Event Published by Product Service**: `ProductVariantCreated`, `ProductVariantUpdated`, `ProductVariantDeleted`.
  - Payload includes necessary details like `variantId`, `productId`, `sku`, and potentially other attributes relevant for inventory setup (e.g., `trackingType` if known by Product Service, though Inventory Service might have defaults).
  - See [Phase 5: Event Publishing](../../05-event-publishing/) for event structures.
- **Event Consumed by Inventory Service**:
  - Inventory Service subscribes to these events via the message broker.
  - Upon receiving `ProductVariantCreated`, it initializes a new inventory record (e.g., with zero stock, default thresholds).
  - Upon `ProductVariantUpdated`, it updates any relevant linked information if needed.
  - Upon `ProductVariantDeleted`, it may mark the inventory record as obsolete or handle it according to its business logic.
- **Response/Confirmation (Inventory Service -> Product Service, Optional Asynchronous)**:
  - Inventory Service might publish an `InventoryRecordInitialized` or `InventoryRecordUpdateFailed` event.
  - Product Service could listen to these to update a local status (e.g., variant moves from "Pending Inventory" to "Active" or "Inventory Setup Failed"). This creates a more robust feedback loop than relying on synchronous calls.

### 2.2. Stock Level Updates (Inventory Service -> Product Service)

- **Event Published by Inventory Service**: `StockLevelChanged`, `InventoryStatusUpdated`.
  - Payload includes `productVariantId`, `availableQuantity`, `status` (e.g., IN_STOCK, OUT_OF_STOCK, LOW_STOCK), `updatedAt`.
- **Event Consumed by Product Service**:
  - The [Inventory Integration Component](../../03-core-service-components/03a-inventory-integration.md) within Product Service subscribes to these events.
  - It updates its local, eventually consistent cache/view of inventory information for the specified variants.
  - This cached information is then used for displaying indicative stock levels on product pages and listings. It should always be presented to the user as indicative (e.g., "Usually ships in X days," "Low stock," or "Availability updated at HH:MM").

## 3. Exceptional Synchronous API Calls (Product Service as Client)

These are exceptions to the asynchronous-first approach and require strong justification. Product Service MUST adhere to the [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md) when making these calls.

Refer to the [Inventory Service OpenAPI Specification](../../../inventory-service/openapi/inventory-service.yaml) for authoritative contract details.

### 3.1. Fetch Real-time Stock Levels for Product Variant(s) (Highly Exceptional)

- **Purpose**: To retrieve the absolute current stock levels directly from Inventory Service.
- **Justification (Strictly Limited Use Cases)**:
  - **Critical Administrative Operations**: Internal admin tools within Product Service that require an immediate, authoritative stock view that cannot rely on the eventually consistent local cache.
  - **Rare Fallback**: If the event stream for inventory updates to Product Service is detected as significantly stale or unavailable, a direct call might serve as a temporary, emergency fallback for _critical operations only_, with clear indication to the user/system about the nature of the check.
  - **NOT for general display on product pages/listings** – these should use the event-sourced local view.
- **Inventory Service Endpoint**: `GET /inventory`
- **Key Query Parameters**: `productVariantIds`
- **Request/Response Examples**: (Similar to original document, but emphasize this is exceptional)
  ```json
  // Request from Product Service:
  // GET https://api.inventory.example.com/v1/inventory?productVariantIds=variant-uuid-123,variant-uuid-456
  //
  // Response from Inventory Service:
  // [
  //   {
  //     "productVariantId": "variant-uuid-123",
  //     "availableQuantity": 130,
  //     "status": "IN_STOCK", ...
  //   }
  // ]
  ```
- **Error Handling**: As per [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md). Product Service must handle unavailability of Inventory Service gracefully (e.g., indicate real-time check failed).

### 3.2. Initialize Inventory Record (Strongly Discouraged as Synchronous Call)

- **Purpose**: To synchronously request Inventory Service to create an initial inventory record.
- **General Recommendation**: This should be handled **asynchronously** as described in Section 2.1. Product Service should publish `ProductVariantCreated`, and Inventory Service consumes it. A synchronous call for this creates tight coupling and risks Product Service workflows being blocked by Inventory Service issues.
- **Highly Exceptional Justification (If Asynchronous is Impossible)**: If an unbreakable business rule dictates that a product variant _cannot_ be considered created or be active in ANY capacity until Inventory Service explicitly confirms record creation via a synchronous response, then this _might_ be considered. However, this indicates a potential design flaw that should be addressed (e.g., by introducing a "Pending Inventory" status for the variant in Product Service).
- **Inventory Service Endpoint**: `POST /inventory`
- **Request/Response Examples**: (Similar to original document, but with strong caveats)
- **Error Handling**: If used synchronously (discouraged), failure must be handled robustly. A failure from Inventory Service would mean the product variant creation in Product Service might need to be rolled back or marked as "Inventory Setup Failed". This complicates the Product Service logic significantly.

## 4. Resilience and Error Handling

### 4.1. Asynchronous Flows

- **Product Service (Event Publishing)**:
  - Ensure reliable publishing of events to the message broker (e.g., transactional outbox pattern or reliable event publisher).
- **Product Service (Event Consumption - for stock updates from Inventory Service)**:
  - Idempotent event handlers: Design consumers to handle duplicate events safely.
  - Retry mechanisms for event processing logic (e.g., for transient errors when updating its local cache).
  - Dead-Letter Queues (DLQs) for events that repeatedly fail processing.
  - Monitoring of event queue lengths and processing error rates.
- **Inventory Service (Event Consumption - for product updates from Product Service)**:
  - (Inventory Service's internal responsibility, but Product Service relies on it) Similar principles of idempotency, retries, DLQs.

### 4.2. Synchronous Flows (Exceptional)

- Product Service MUST implement Timeouts, Retries (for idempotent operations), and Circuit Breakers as detailed in [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md).
- Fallback strategies for synchronous call failures must be clearly defined (e.g., for `GET /inventory`, use stale cache with indication, or report failure).

## 5. Security

- **Asynchronous**: Secure access to the message broker (authentication, authorization, encryption of messages in transit/at rest where appropriate).
- **Synchronous (Exceptional)**: All API calls must be authenticated (e.g., service-to-service OAuth 2.0 client credentials token) and occur over HTTPS, as per [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md).

## 6. References

- [Inventory Service OpenAPI Specification](../../../inventory-service/openapi/inventory-service.yaml) (Authoritative contract for any synchronous APIs)
- [Product Service: Core Inventory Integration Component](../../03-core-service-components/03a-inventory-integration.md) (Details how Product Service consumes inventory events)
- [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md)
- [Phase 5: Event Publishing](../../05-event-publishing/) (Defines Product Service events)
