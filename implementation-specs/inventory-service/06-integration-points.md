# Inventory Service: Integration Points

## 1. Introduction

Effective integration between the Inventory Service and other microservices is essential for the seamless operation of the e-commerce platform. This document outlines the various integration points, detailing both asynchronous (event-driven) and synchronous (API-based) communication patterns.

The primary communication style will be **event-driven**, aligning with **ADR-002 (Event-Driven Architecture)**, to promote loose coupling and resilience. Services will consume events published by the Inventory Service (as detailed in [05-event-publishing.md](./05-event-publishing.md)) and vice-versa. Synchronous REST API calls will be used for specific request/response scenarios where immediate feedback is necessary, such as stock reservation attempts during an order checkout process. All API integrations will adhere to **ADR-007 (API-First Design)**.

## 2. Consumed Events (Asynchronous Integrations)

The Inventory Service subscribes to events from other services to stay informed about relevant changes in their domains.

### 2.1. From Product Service

The Inventory Service needs to react to changes in the product catalog. It will consume events published by the Product Service to a shared message broker (RabbitMQ via Amazon MQ, as per **ADR-018**).

*   **`ProductVariantCreatedEvent`**
    *   **Description**: Triggered when a new product variant is created in the Product Service.
    *   **Action by Inventory Service**:
        1.  Create a new `Inventory` record associated with the `productVariantId`.
        2.  Initialize `quantity` to 0 (or a specified default initial stock).
        3.  Initialize `reservedQuantity` to 0.
        4.  Calculate `availableQuantity` (initially 0).
        5.  Set `status` to `OUT_OF_STOCK` (or `AWAITING_INITIAL_STOCK`).
        6.  Store `sku` (if provided and needed for reference, though `productVariantId` is the primary key).
    *   **Key Payload Fields Needed**:
        *   `productVariantId`: `string` (UUID) - Mandatory.
        *   `sku`: `string` (optional) - For reference.
        *   `initialStock`: `number` (optional) - If the event carries information about initial stock.
    *   **Idempotency**: Handled by checking if an inventory record for `productVariantId` already exists.

*   **`ProductVariantUpdatedEvent`**
    *   **Description**: Triggered when details of an existing product variant are updated.
    *   **Action by Inventory Service**:
        1.  Evaluate the changes.
        2.  If the `productVariant` is marked as discontinued (e.g., a `status` field in the event payload indicates this), the Inventory Service may update its corresponding `Inventory` record's status to `DISCONTINUED`. This might also involve business rules like preventing discontinuation if active stock exists.
        3.  Other product detail changes (e.g., name, description) usually do not directly impact inventory records unless specific business rules are defined (e.g., related to stockability).
    *   **Key Payload Fields Needed**:
        *   `productVariantId`: `string` (UUID) - Mandatory.
        *   Fields indicating relevant changes (e.g., `status`, `isOrderable`).
    *   **Idempotency**: Updates are applied based on the current state of the inventory record.

*   **`ProductVariantDeletedEvent`**
    *   **Description**: Triggered when a product variant is marked for deletion in the Product Service.
    *   **Action by Inventory Service**:
        1.  Locate the `Inventory` record for the `productVariantId`.
        2.  Business logic will determine the exact action:
            *   If `quantity` is 0, the `Inventory` record might be soft-deleted or marked as `DISCONTINUED`.
            *   If `quantity` > 0, the deletion might be flagged, and an administrative alert raised. The system might prevent actual deletion of the product variant in the Product Service if active stock exists, or the Inventory Service might just change status to `DISCONTINUED` and prevent further operations.
    *   **Key Payload Fields Needed**:
        *   `productVariantId`: `string` (UUID) - Mandatory.
    *   **Idempotency**: Handled by checking the current state of the inventory record.

### 2.2. From Order Service

Direct event consumption from the Order Service by the Inventory Service is less common for core inventory operations like reservations or stock deduction, as these are typically handled via direct API calls from the Order Service to ensure immediate feedback and atomicity for the order process.

However, certain events could be considered:
*   **`OrderPaymentFailedEvent` or `OrderFraudulentEvent`**:
    *   **Action**: If reservations are long-lived and not immediately released by an API call from Order Service upon payment failure, such an event could trigger a stock release. However, the more common pattern is for the Order Service to explicitly call the `POST /inventory/{variantId}/release` API.
*   **`ReturnProcessedEvent`**:
    *   **Action**: When a customer return is fully processed and accepted by the Order Service (or a dedicated Returns Service), this event could trigger the `InventoryManagerService.updateStock()` method with `changeType: RETURN` to add the item back to sellable inventory.
    *   **Key Payload Fields Needed**: `productVariantId`, `quantityReturned`.

The primary interaction model remains the Order Service calling Inventory Service APIs.

## 3. Exposed APIs for Integration (Synchronous Integrations)

The Inventory Service exposes RESTful APIs for other services that require immediate, synchronous interaction. These APIs are defined in `implementation-specs/inventory-service/04-api-endpoints/01-inventory-api.md` and documented in the OpenAPI specification (`openapi/inventory-service.yaml`).

### 3.1. Used by Order Service

*   **`POST /api/v1/inventory/{productVariantId}/reserve`**:
    *   **Purpose**: Allows the Order Service to reserve a specific quantity of a product variant during the checkout process or when items are added to a cart with reservation capabilities.
    *   **Expected Outcome**: Decreases `availableQuantity` and increases `reservedQuantity`. Returns success or failure (e.g., insufficient stock).
*   **`POST /api/v1/inventory/{productVariantId}/release`**:
    *   **Purpose**: Allows the Order Service to release previously reserved stock. This is used if an order is cancelled, items are removed from the cart, or a reservation expires.
    *   **Expected Outcome**: Increases `availableQuantity` and decreases `reservedQuantity`.
*   **`POST /api/v1/inventory/adjust-stock` (or similar for recording sales, using `StockLevelChangedEvent`'s `SALE` type)**:
    *   **Purpose**: After an order is confirmed and payment is processed (or at the point of shipment), the Order Service informs the Inventory Service to deduct the sold items from the physical stock. This operation reduces both `quantity` and `reservedQuantity`.
    *   **Payload typically includes**: `productVariantId`, `quantitySold`, `orderId`.
    *   **Alternative**: This could also be triggered by an event from Order Service (`OrderConfirmedForShipmentEvent`), but often an API call is preferred for immediate confirmation.

### 3.2. Used by Product Service / Search Service

*   **`GET /api/v1/inventory/{productVariantId}`**:
    *   **Purpose**: Allows the Product Service (or a Search Service that indexes product information) to fetch the current stock level, availability, and status for a specific product variant. This data is used for display on product detail pages, product listing pages, and for search result accuracy.
    *   **Expected Outcome**: Returns the inventory details (quantity, availableQuantity, status, etc.).
*   **`GET /api/v1/inventory?productVariantIds={id1},{id2}` (Batch endpoint)**:
    *   **Purpose**: To allow fetching inventory details for multiple product variants in a single call, improving efficiency.
    *   **Expected Outcome**: Returns a list of inventory details.

### 3.3. General Event Consumption

While not an API exposed *by* Inventory Service, other services (e.g., Notification Service, Analytics Service, Reordering Service) will consume events published by the Inventory Service as detailed in [05-event-publishing.md](./05-event-publishing.md). For example:
*   `StockStatusChangedEvent` (e.g., to `OUT_OF_STOCK`) might be consumed by a Notification Service to alert staff or customers.
*   `StockLevelChangedEvent` might be consumed by an Analytics Service.

## 4. Internal API Consumptions

The Inventory Service should strive to be as autonomous as possible and rely on its own data and events consumed from other services.

*   **Product Service API Calls**:
    *   Generally, the Inventory Service should **avoid** making synchronous API calls to the Product Service (e.g., to validate `productVariantId` upon every API request it receives). It should trust that the `productVariantId` it receives (either via API or event) is valid, having been created by the Product Service.
    *   Initial creation of inventory records is handled by consuming `ProductVariantCreatedEvent`. If a request comes for a `productVariantId` for which no inventory record exists, it might indicate a data consistency issue or a race condition, which should be logged and handled appropriately (e.g., return a 404 or specific error).

Minimizing outbound synchronous calls improves the resilience and reduces coupling of the Inventory Service.

## 5. Data Consistency

Maintaining data consistency across distributed services is a key challenge. The Inventory Service will employ several strategies:

*   **Eventual Consistency**: For many integration scenarios, particularly those driven by event consumption, data will become consistent eventually. For example, when a `ProductVariantCreatedEvent` is consumed, there's a brief period where the product variant exists but its inventory record doesn't. This is acceptable for many use cases.
*   **Idempotent Event Handlers**: As mentioned in event consumption sections, handlers for consumed events must be idempotent to prevent issues from duplicate event delivery. This means processing the same event multiple times has the same effect as processing it once.
*   **Transactional Outbox Pattern**: Used for publishing events (see [05-event-publishing.md](./05-event-publishing.md)) to ensure that events are published if and only if the business transaction commits.
*   **Compensating Transactions**: For critical operations that span services and might fail, compensating transactions (Sagas) might be necessary. For example, if reserving stock succeeds but a subsequent step in the Order Service fails, the Order Service would be responsible for explicitly calling the Inventory Service's `/release` endpoint to roll back the stock reservation.
*   **API Atomicity**: Critical operations like stock reservation should be designed to be as atomic as possible within the Inventory Service.

## 6. Security Considerations for Integrations

Inter-service communication must be secured.

*   **Authentication**:
    *   **Service-to-Service API Calls**: All synchronous API calls between services (e.g., Order Service calling Inventory Service) must be authenticated. This will be achieved using **OAuth 2.0 client credentials flow** or **service-to-service JWTs**, where each service has its own identity. This aligns with **ADR-005 (Authentication and Authorization)** and **ADR-019 (API Gateway and Service Mesh Security)**.
    *   An API Gateway (as per **ADR-006**) will be the entry point for external requests and can also handle authentication for internal service-to-service calls or delegate it to a service mesh.
*   **Authorization**:
    *   Once authenticated, a service must be authorized to perform the requested operation. This will be based on scopes or permissions associated with the service's identity. For example, the Order Service would have permission to call reserve/release endpoints, but the Product Service might only have read-only access to inventory data.
    *   This aligns with **ADR-014 (Role-Based Access Control - RBAC)**, extended for service identities.
*   **Message Security (Events)**:
    *   While events are typically broadcast, ensuring the integrity and authenticity of messages on the broker can be considered, though often the trust boundary is within the internal network where the message broker resides. If messages traverse untrusted networks, message-level encryption or signing might be used.
*   **Network Policies**: If a service mesh is used, network policies can further restrict which services can communicate with each other.

By implementing these integration patterns and security measures, the Inventory Service can effectively and securely collaborate with other microservices in the platform.
