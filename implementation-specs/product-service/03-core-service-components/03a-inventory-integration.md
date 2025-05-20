# Product Service: Inventory Integration Specification

## 1. Overview

This document outlines how the **Product Service** integrates with the dedicated, external **Inventory Service**. The Product Service does not manage inventory directly but relies on the Inventory Service for all stock-related information and operations.

This integration component within the Product Service is responsible for:
- Fetching stock levels for product variants to be displayed to users.
- Triggering the creation of new inventory records in the Inventory Service when new products or variants are created.
- Handling communication failures and retries when interacting with the Inventory Service.
- Optionally, reacting to relevant events published by the Inventory Service.

## 2. Key Interactions and Flows

### 2.1. Fetching Stock Levels

- **Trigger:** When a user views a product detail page or when product listings need to display stock status.
- **Flow:**
  1. Product Service receives a request that requires stock information for one or more product variant IDs.
  2. The Inventory Integration component within Product Service calls the Inventory Service API (e.g., `GET /inventory?productVariantIds={id1},{id2}`).
  3. Inventory Service returns the current stock levels (e.g., `availableQuantity`, `status`).
  4. Product Service incorporates this information into its response to the original caller.
- **Inventory Service Endpoint (Example):** `GET /inventory?productVariantIds=...`
- **Request DTO (to Inventory Service):** N/A (uses query parameters)
- **Response DTO (from Inventory Service - Example `InventoryStockLevel`):**
  ```json
  [
    {
      "productVariantId": "uuid",
      "availableQuantity": 100,
      "status": "IN_STOCK", // e.g., IN_STOCK, OUT_OF_STOCK, LOW_STOCK
      "updatedAt": "ISO8601"
    }
  ]
  ```

### 2.2. Initializing Inventory for New Products/Variants

- **Trigger:** When a new product or product variant is successfully created within the Product Service.
- **Flow (as seen in `ProductService.createProduct` method):
  1. Product Service successfully creates a new `Product` entity.
  2. The Inventory Integration component is invoked (e.g., `this.inventoryIntegration.initializeInventoryRecord(productVariantId, initialStockDetails)`).
  3. This component calls an endpoint on the Inventory Service (e.g., `POST /inventory`) to create an initial inventory record for the new product variant.
- **Inventory Service Endpoint (Example):** `POST /inventory`
- **Request DTO (to Inventory Service - Example `InitializeInventoryRequest`):
  ```json
  {
    "productVariantId": "uuid",
    "initialQuantity": 0, // Or a default starting quantity
    "lowStockThreshold": 10 // Example initial setting
  }
  ```
- **Response DTO (from Inventory Service - Example `InventoryItem`):
  ```json
  {
    "id": "uuid-inventory-record",
    "productVariantId": "uuid",
    "quantity": 0,
    "availableQuantity": 0,
    "status": "OUT_OF_STOCK",
    "updatedAt": "ISO8601"
  }
  ```

### 2.3. Reacting to Inventory Depletion (Optional - Event-Driven)

- **Trigger:** Inventory Service publishes an `InventoryOutOfStockEvent` or `InventoryLowStockEvent`.
- **Flow:**
  1. Product Service (via its event consumer module) subscribes to these events from the message bus.
  2. Upon receiving an event, the Inventory Integration component might trigger logic within the Product Service, such as:
     - Updating a local cache of product availability (if used).
     - Changing the product's display status (e.g., show "Out of Stock").
     - Notifying relevant internal teams.
- **Consumed Event (Example `InventoryOutOfStockEvent`):
  ```json
  {
    "eventId": "uuid",
    "timestamp": "ISO8601",
    "productVariantId": "uuid"
  }
  ```

## 3. Interface with Inventory Service

### 3.1. API Endpoints Consumed

The Product Service (via this integration component) will primarily consume the following types of endpoints from the Inventory Service API. (Refer to `inventory-service.yaml` for precise definitions):

- **`GET /inventory?productVariantIds={ids}`**: To fetch stock levels for one or more product variants.
- **`GET /inventory/{productVariantId}`**: To fetch stock level for a single product variant.
- **`POST /inventory`**: To request the creation/initialization of an inventory record for a new product variant.
- *(Other endpoints like stock adjustments or reservations are typically called by the Order Service, not directly by Product Service in most scenarios.)*

### 3.2. Key Data Structures (DTOs)

- **`InventoryStockLevel` (Response from Inventory Service):** Contains essential stock information like `productVariantId`, `availableQuantity`, `status`.
- **`InitializeInventoryRequest` (Request to Inventory Service):** Contains `productVariantId` and any initial stock parameters.

### 3.3. Events Consumed (Optional)

- `InventoryOutOfStockEvent`
- `InventoryLowStockEvent`
- `InventoryBackInStockEvent`

## 4. Error Handling and Resilience

- **Timeouts:** API calls to Inventory Service should have appropriate timeouts.
- **Retries:** Implement retry mechanisms (e.g., exponential backoff) for transient network issues when calling Inventory Service.
- **Circuit Breaker:** Consider using a circuit breaker pattern if Inventory Service calls are critical and prone to failure, to prevent cascading failures.
- **Fallback Strategies:** 
  - If Inventory Service is unavailable during a product view, Product Service might display "Stock information unavailable" or rely on a slightly stale cached value (with appropriate caveats).
  - If initializing an inventory record fails during product creation, the Product Service might:
    - Roll back the product creation (if strict consistency is required).
    - Add the product to a retry queue for inventory initialization.
    - Mark the product as not yet orderable.
- **Logging:** All calls to and responses/errors from Inventory Service must be logged with correlation IDs for traceability.

## 5. Responsibilities of this Integration Component

- Encapsulate all logic related to communicating with the external Inventory Service.
- Translate Product Service internal models/requests into the DTOs expected by Inventory Service.
- Handle responses and errors from Inventory Service gracefully.
- Provide clear methods for other parts of the Product Service (e.g., the main `ProductService` class) to interact with inventory data (e.g., `getStockLevel(productVariantId)`, `requestInventoryInitialization(productVariantId)`).

## 6. Security Considerations

- Communication between Product Service and Inventory Service should be secured (e.g., HTTPS/mTLS).
- If the Inventory Service requires authentication/authorization, the Product Service must securely manage and use the necessary credentials/tokens for its calls.

## 7. References

- [Inventory Service API Specification](../../inventory-service/openapi/inventory-service.yaml)
- [Inventory Service Data Models](../../inventory-service/02-data-model-setup/01-inventory-entity.md)
- [Product Service Specification](01-product-service.md)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html) 