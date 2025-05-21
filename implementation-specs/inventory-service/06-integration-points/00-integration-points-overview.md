# Inventory Service Integration Points

## Overview

The Inventory Service integrates with several other services in the e-commerce platform. These integrations follow two primary patterns:

1. **Event-Driven Integration**: Asynchronous communication using domain events
2. **API-Based Integration**: Synchronous communication using RESTful APIs

This document outlines the key integration points, patterns, and considerations for each.

## Integration Architecture

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │
│  Inventory    │◀───▶│  Order        │     │  Product      │
│  Service      │     │  Service      │     │  Service      │
│               │     │               │     │               │
└───┬───────┬───┘     └───────┬───────┘     └───────┬───────┘
    │       │                 │                     │
    │       │                 ▼                     ▼
    │       │         ┌───────────────┐     ┌───────────────┐
    │       │         │               │     │               │
    │       └────────▶│  Notification │     │  Analytics    │
    │                 │  Service      │     │  Service      │
    │                 │               │     │               │
    │                 └───────────────┘     └───────────────┘
    │
    │         ┌───────────────┐
    │         │               │
    └────────▶│  Purchasing   │
              │  Service      │
              │               │
              └───────────────┘
```

## Service Integrations

### 1. Order Service Integration

#### Event-Driven Patterns
- **Inventory Service Publishes:**
  - `AllocationCreatedEvent`
  - `AllocationConfirmedEvent`
  - `AllocationCancelledEvent`
  - `AllocationFulfilledEvent`
  - `InsufficientStockEvent`

- **Inventory Service Consumes:**
  - `OrderCreatedEvent`
  - `OrderConfirmedEvent`
  - `OrderCancelledEvent`
  - `OrderReturnInitiatedEvent`

#### API-Based Patterns
- **Inventory Service Exposes:**
  - `GET /allocations/by-order/{orderId}` - Get all allocations for an order
  - `POST /allocations` - Create allocation for order item

- **Inventory Service Consumes:**
  - `GET /orders/{orderId}` - Get order details
  - `GET /orders/{orderId}/items` - Get order line items

### 2. Product Service Integration

#### Event-Driven Patterns
- **Inventory Service Publishes:**
  - `StockLevelChangedEvent`
  - `LowStockThresholdReachedEvent`
  - `OutOfStockEvent`

- **Inventory Service Consumes:**
  - `ProductCreatedEvent`
  - `ProductUpdatedEvent`
  - `ProductDeletedEvent`

#### API-Based Patterns
- **Inventory Service Exposes:**
  - `GET /inventory-items/by-product/{productId}` - Get inventory for product
  - `GET /inventory-items/{id}/availability` - Check product availability

- **Inventory Service Consumes:**
  - `GET /products/{productId}` - Get product details
  - `GET /products/{productId}/variants` - Get product variants

### 3. Notification Service Integration

#### Event-Driven Patterns
- **Inventory Service Publishes:**
  - `LowStockThresholdReachedEvent`
  - `OutOfStockEvent`
  - `StockReplenishedEvent`
  - `AllocationFailedEvent`

- **Inventory Service Consumes:**
  - None

#### API-Based Patterns
- **Inventory Service Exposes:**
  - None

- **Inventory Service Consumes:**
  - `POST /notifications` - Create notification

### 4. Analytics Service Integration

#### Event-Driven Patterns
- **Inventory Service Publishes:**
  - All inventory domain events for analytics processing

- **Inventory Service Consumes:**
  - None

#### API-Based Patterns
- **Inventory Service Exposes:**
  - `GET /reports/inventory-value` - Get inventory valuation
  - `GET /reports/stock-movements` - Get stock movement report

- **Inventory Service Consumes:**
  - None

### 5. Purchasing Service Integration

#### Event-Driven Patterns
- **Inventory Service Publishes:**
  - `LowStockThresholdReachedEvent`
  - `OutOfStockEvent`

- **Inventory Service Consumes:**
  - `PurchaseOrderCreatedEvent`
  - `PurchaseOrderReceivedEvent`

#### API-Based Patterns
- **Inventory Service Exposes:**
  - `GET /reports/low-stock` - Get low stock report
  - `GET /inventory-items/{id}/reorder-suggestion` - Get reorder quantities

- **Inventory Service Consumes:**
  - `GET /purchase-orders/by-product/{productId}` - Get purchase orders
  - `POST /purchase-orders` - Create purchase order