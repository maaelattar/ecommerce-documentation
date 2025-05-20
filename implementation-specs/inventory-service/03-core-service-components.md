# Inventory Service: Core Service Components

## 1. Overview

This document details the core business logic components for the Inventory Service. These components are responsible for managing inventory levels, handling reservations, and tracking inventory history. They build upon the entities defined in the [Inventory Entity Model Specification](./02-data-model-setup/01-inventory-entity.md) and align with NestJS conventions and established architectural decision records (ADRs).

The primary components are:
- `InventoryManagerService`: For managing overall stock levels and status.
- `ReservationManagerService`: For handling stock reservations and releases.
- `InventoryHistoryService`: For logging and retrieving inventory changes.

These services will interact with `InventoryRepository` and `InventoryHistoryRepository` (as conceptualized in `01-inventory-entity.md`) for data persistence.

## 2. Component Specifications

### 2.1. InventoryManagerService

This service expands on the `InventoryService` concept from `01-inventory-entity.md` with a focus on direct stock management and status.

*   **Primary Responsibilities**:
    *   Managing overall stock quantities (`quantity`, `availableQuantity`) for product variants.
    *   Updating inventory status (e.g., `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `DISCONTINUED`) based on quantity and thresholds.
    *   Handling direct stock adjustments (e.g., receiving new stock, manual corrections).
    *   Providing information about current stock levels and availability.

*   **Key Methods/Operations**:
    *   `updateStock(variantId: string, changeQuantity: number, changeType: InventoryChangeType, reason: string, userId: string): Promise<Inventory>`: Modifies the stock quantity for a product variant. `changeQuantity` can be positive (stock in) or negative (stock out). Records history via `InventoryHistoryService`.
    *   `checkAvailability(variantId: string, requestedQuantity: number): Promise<{ isAvailable: boolean; availableQuantity: number }>`: Checks if a certain quantity of a product variant is available for sale/reservation.
    *   `getProductVariantInventoryDetails(variantId: string): Promise<Inventory | null>`: Retrieves the complete inventory record for a specific product variant.
    *   `setInventoryStatus(variantId: string, status: InventoryStatus, userId: string): Promise<Inventory>`: Manually sets the inventory status (e.g., to `DISCONTINUED`). Records history.
    *   `setLowStockThreshold(variantId: string, threshold: number): Promise<Inventory>`: Sets the low stock threshold for a product variant. (This might also be a global or category-level setting). Updates status if necessary.
    *   `getMultipleProductVariantInventoryDetails(variantIds: string[]): Promise<Inventory[]>`: Retrieves inventory details for a list of product variants.

*   **Main Collaborators**:
    *   `InventoryRepository`: For persisting and retrieving `Inventory` entities.
    *   `InventoryHistoryService`: For logging all changes made by this service.
    *   `ProductService` (potentially, via events or limited API calls): To validate product variant existence or get minimal product details if necessary, though primarily relies on `variantId`.

*   **Important Business Rules/Logic**:
    *   `availableQuantity` is always calculated as `quantity - reservedQuantity`.
    *   `quantity` and `reservedQuantity` cannot be negative. `availableQuantity` cannot be negative.
    *   Status updates automatically based on quantity changes relative to thresholds (e.g., `OUT_OF_STOCK` when `quantity` is 0, `LOW_STOCK` when `quantity` is below threshold).
    *   All operations that change quantity or status must be logged in `InventoryHistory`.
    *   Ensures that adjustments do not lead to negative available stock unless explicitly permitted by specific `changeType` (e.g., backorders, if supported).

### 2.2. ReservationManagerService

This service is responsible for the lifecycle of stock reservations, typically tied to customer orders or shopping carts.

*   **Primary Responsibilities**:
    *   Atomically reserving stock for product variants when an order is initiated or items are added to a cart.
    *   Releasing reserved stock if an order is cancelled, items are removed, or a reservation expires.
    *   Confirming stock reservations when an order is finalized, transitioning reserved stock to sold stock (which is typically handled by `InventoryManagerService.updateStock` with `changeType: SALE`).

*   **Key Methods/Operations**:
    *   `reserveStock(items: { variantId: string; quantity: number }[], orderId: string, reservationId?: string): Promise<{ success: boolean; reservedItems: Inventory[] }>`: Attempts to reserve specified quantities for multiple product variants. Returns success status and details of reserved items.
    *   `releaseStock(items: { variantId: string; quantity: number }[], orderId: string, reservationId?: string): Promise<{ success: boolean; releasedItems: Inventory[] }>`: Releases previously reserved stock.
    *   `confirmStockReservation(orderId: string, reservationId?: string): Promise<{ success: boolean; itemsSold: Inventory[] }>`: This operation would typically trigger a call to `InventoryManagerService.updateStock` to deduct the confirmed reserved quantities from the main `quantity`. The reservation itself is then cleared or marked as fulfilled.
    *   `getReservationDetails(reservationId: string): Promise<Reservation | null>`: Retrieves details of a specific reservation (assuming a `Reservation` entity or similar tracking mechanism).
    *   `expireReservations(olderThan: Date): Promise<void>`: A background process or scheduled job to release expired reservations.

*   **Main Collaborators**:
    *   `InventoryRepository`: For updating `reservedQuantity` and `availableQuantity` on `Inventory` entities.
    *   `InventoryHistoryService`: For logging reservation activities (reservation, release, confirmation).
    *   `OrderService` (via events or API calls): To receive requests for reservations and releases based on order lifecycle events.

*   **Important Business Rules/Logic**:
    *   Cannot reserve more stock than is currently available (`availableQuantity`).
    *   Reservations should be atomic: either all items in a request are reserved, or none are (or handle partial reservations based on policy). This is critical for concurrent requests.
    *   Reservations should have a timeout/expiration period.
    *   Releasing stock increases `availableQuantity` and decreases `reservedQuantity`.
    *   Confirming a reservation decreases both `quantity` and `reservedQuantity` (handled by `InventoryManagerService.updateStock` upon notification from this service or the `OrderService`).
    *   All reservation changes must be logged in `InventoryHistory` with appropriate `changeType` (e.g., `RESERVATION`, `RESERVATION_RELEASED`, `RESERVATION_CONFIRMED`).

### 2.3. InventoryHistoryService

This service is responsible for creating and querying inventory history records, providing an audit trail for all stock movements and changes. It expands on the `InventoryHistoryRepository` concept from `01-inventory-entity.md`.

*   **Primary Responsibilities**:
    *   Creating immutable history records for every change in inventory quantity, status, or reservation.
    *   Providing a queryable interface to retrieve inventory history for auditing, analysis, or customer service purposes.

*   **Key Methods/Operations**:
    *   `recordChange(inventoryId: string, previousQuantity: number, newQuantity: number, quantityChange: number, changeType: InventoryChangeType, reason: string, changedBy: string, metadata?: Record<string, any>): Promise<InventoryHistory>`: Creates a new `InventoryHistory` entry. This is called internally by `InventoryManagerService` and `ReservationManagerService`.
    *   `getInventoryHistory(variantId: string, filters: { page?: number; limit?: number; dateFrom?: Date; dateTo?: Date; changeType?: InventoryChangeType }): Promise<{ history: InventoryHistory[]; total: number }>`: Retrieves a paginated list of history records for a product variant, with optional filters.
    *   `getHistoryForReservation(reservationId: string): Promise<InventoryHistory[]>`: Retrieves history specific to a reservation lifecycle.

*   **Main Collaborators**:
    *   `InventoryHistoryRepository`: For persisting and retrieving `InventoryHistory` entities.
    *   `InventoryRepository` (potentially): To link history records back to specific `Inventory` entities or `productVariantId`.

*   **Important Business Rules/Logic**:
    *   History records are immutable once created.
    *   Must capture all relevant details: previous quantity, new quantity, change amount, type of change, reason for change, user/process responsible, and timestamp.
    *   Provides comprehensive logging for traceability and auditing.

## 3. Data Persistence

*   **InventoryRepository**: Manages CRUD operations for the `Inventory` entity. It will implement methods like `findById`, `findByProductVariantId`, `updateQuantities` (handling atomicity for `quantity`, `reservedQuantity`, `availableQuantity`), etc.
    *   The `updateQuantity` and `reserveQuantity` methods outlined in `01-inventory-entity.md`'s `InventoryRepository` would be refined and used by `InventoryManagerService` and `ReservationManagerService`.
*   **InventoryHistoryRepository**: Manages CRUD operations for the `InventoryHistory` entity. Primarily `create` and `find` with various filters.
    *   The `createHistoryEntry` method from `01-inventory-entity.md`'s `InventoryRepository` would belong here or be directly managed by the `InventoryHistoryService`.

## 4. Alignment with Entities and ADRs

*   **Entities**: These components directly operate on the `Inventory` and `InventoryHistory` entities defined in `implementation-specs/inventory-service/02-data-model-setup/01-inventory-entity.md`.
*   **NestJS Conventions**: The components are designed as injectable services (`@Injectable()`), promoting modularity and testability as per NestJS patterns.
*   **ADRs**:
    *   **Event-Driven Architecture (ADR-002)**: While these core components handle synchronous operations, they will be the source of events (e.g., `StockLevelChanged`, `StockReserved`) published to a message queue (e.g., RabbitMQ via Amazon MQ, as per ADR-002) for other services to consume. Event publishing logic will be part of these services or orchestrated by a dedicated event publishing component.
    *   **Database-per-Service (ADR-020)**: The Inventory Service owns its database and these components interact with its dedicated repositories.
    *   **API-First Design (ADR-007)**: These services will underpin the API layer, providing the business logic for the exposed endpoints.

This component structure provides a clear separation of concerns for managing different aspects of inventory within the Inventory Service.
