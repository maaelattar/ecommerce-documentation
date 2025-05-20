# ADR-049: Inventory Management Approach

**Status:** Proposed
**Date:** 2025-05-19

## 1. Context

As part of Milestone 2, an MVP Inventory Service is being introduced to track stock levels for products. This is crucial for preventing overselling, providing accurate product availability to customers, and managing warehouse stock. This ADR defines the core approach to inventory management, including data models, key operations (stock updates, reservations), and interaction patterns with other services like Product Catalog and Order Service.

Key requirements:
*   Maintain accurate real-time (or near real-time) stock levels for each product/SKU.
*   Prevent orders from being placed for out-of-stock items.
*   Support stock reservations during the checkout process to avoid race conditions.
*   Allow for stock adjustments (e.g., initial seeding, manual corrections - though full admin UI for this might be post-MVP).
*   Integrate seamlessly with Product Catalog (e.g., when new products are added) and Order Service (when orders are placed, paid, or cancelled).

## 2. Decision Drivers

*   **Accuracy & Consistency:** Ensuring inventory data is a reliable source of truth is paramount.
*   **Performance & Scalability:** The system must handle frequent reads (checking stock) and writes (updating stock, reservations) efficiently, especially during peak sales periods.
*   **Resilience:** Operations like stock decrement should be robust against failures.
*   **Complexity of MVP Implementation:** Strive for a solution that meets core MVP needs without over-engineering.
*   **Atomicity:** Operations like reserving stock and decrementing it upon order completion should be atomic where possible to prevent data inconsistencies.

## 3. Considered Options

### Option 1: Centralized Inventory Service with Synchronous Checks & Updates
*   Order Service directly calls Inventory Service API to check stock and then to reserve/decrement stock.
*   *Pros:* Simpler to reason about for basic flows. Immediate feedback on stock availability.
*   *Cons:* Can lead to tight coupling. Performance bottlenecks if Inventory Service is slow or unavailable. Distributed transactions are hard.

### Option 2: Centralized Inventory Service with Eventual Consistency (Event-Driven Approach)
*   Product Service publishes `ProductCreated` / `ProductUpdated` events. Inventory Service subscribes to initialize/update stock records.
*   Order Service publishes `OrderCreated` event (with items). Inventory Service subscribes to reserve stock.
*   Payment Service publishes `PaymentSucceeded` event. Inventory Service (or Order Service, which then commands Inventory Service) subscribes to decrement stock from reserved.
*   If `OrderFailed` or `PaymentFailed`, an event triggers stock release.
*   Stock checks might still be synchronous APIs, but updates are primarily event-driven.
*   *Pros:* Loose coupling, improved resilience (services can operate even if another is temporarily down, events queued in message broker like Kafka - ADR-002).
*   *Cons:* Increased complexity due to asynchronous nature. Eventual consistency means there might be a slight delay in stock updates reflecting everywhere (though usually minimal with efficient processing).

### Option 3: Optimistic Locking with Compensating Transactions
*   Allow order placement assuming stock is available (optimistic). Attempt to decrement stock afterwards.
*   If stock decrement fails, trigger a compensating transaction (e.g., cancel order, notify user, refund if payment taken).
*   *Pros:* Can improve perceived performance for order placement.
*   *Cons:* Significantly more complex to implement correctly, especially compensation logic. Poor user experience if orders are frequently cancelled post-payment.

## 4. Decision Outcome

**Chosen Option:** [To be decided - Leaning towards Option 2: Centralized Inventory Service with Eventual Consistency for updates, potentially synchronous checks for critical paths like 'add to cart' or 'initiate checkout', and robust reservation mechanism.]

Rationale:
*   Balances decoupling and resilience (via events for updates) with the need for reasonably real-time stock information (via direct API checks for reads).
*   Aligns with ADR-002 (Asynchronous Communication with Kafka) for inter-service communication, promoting scalability.
*   Reservation pattern is crucial to handle concurrency during checkout.

## 5. Inventory Management Details

*   **Data Model (ProductInventory):**
    *   `product_id` (links to Product Catalog)
    *   `sku` (if supporting product variants)
    *   `quantity_on_hand` (actual physical stock)
    *   `quantity_reserved` (stock reserved for pending orders)
    *   `quantity_available` (calculated: `on_hand - reserved`)
    *   `last_updated_at`
*   **Key Operations / API Endpoints / Event Handlers:**
    *   **Initialize/Update Stock:** (e.g., on `ProductCreated` event or manual adjustment) - Updates `quantity_on_hand`.
    *   **Check Availability:** (API for Order Service/Frontend) - Returns `quantity_available`.
    *   **Reserve Stock:** (API called by Order Service during checkout initiation) - Increments `quantity_reserved`. Fails if `quantity_available` is insufficient.
    *   **Confirm/Decrement Stock:** (e.g., on `PaymentSucceeded` event) - Decrements `quantity_on_hand` and `quantity_reserved`.
    *   **Release Reserved Stock:** (e.g., on `OrderCancelled`, `PaymentFailed` events, or reservation timeout) - Decrements `quantity_reserved`.
*   **Preventing Overselling:** The `Reserve Stock` operation is key. It must atomically check `quantity_available` and update `quantity_reserved` if sufficient. Database-level constraints or optimistic locking within the Inventory service for this operation might be needed.
*   **Interaction with Product Catalog:** Inventory Service subscribes to product creation/update events to create/update inventory records. (ADR-002)
*   **Interaction with Order Service:** Order Service calls Inventory Service to check availability and reserve stock. Order Service informs Inventory Service (likely via events handled by Inventory Service) about order completion or cancellation to confirm or release reservations. (ADR-002, ADR-033)

## 6. Pros and Cons of the Decision

### Pros
*   ...

### Cons
*   ...

## 7. Consequences

*   Requires a reliable message broker (Kafka - ADR-002) for event-driven updates.
*   Careful design of reservation expiry and cleanup mechanisms is needed.
*   Potential for eventual consistency in stock levels, which needs to be managed in terms of user experience.

## 8. Links

*   ADR-002: Asynchronous Communication (Kafka)
*   ADR-004: PostgreSQL for Relational Data (for Inventory Service DB)
*   ADR-033: Inter-Service Communication Patterns
*   Milestone 2, Sprint 1 & 3 Plans (Inventory Service PBIs)

---
