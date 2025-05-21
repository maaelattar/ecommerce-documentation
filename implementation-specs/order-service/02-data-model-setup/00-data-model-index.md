# Order Service Data Model

## Introduction

This document provides an overview of the Order Service data model. The Order Service manages the complete lifecycle of customer orders from creation to fulfillment. This data model is designed to support all necessary order operations while maintaining data integrity, performance, and scalability.

## Entity Relationships

The Order Service data model consists of the following primary entities and their relationships:

```
┌───────────────┐     1:N     ┌───────────────┐
│     Order     │────────────>│   OrderItem   │
└───────────────┘             └───────────────┘
        │                             │
        │ 1:1                         │ N:1
        ▼                             │
┌───────────────┐                     │
│ BillingDetails│                     │
└───────────────┘                     │
        │                             │
        │ 1:1                         │
        ▼                             ▼
┌───────────────┐               ┌───────────────┐
│ShippingDetails│               │    Product    │
└───────────────┘               │   (Reference) │
        │                       └───────────────┘
        │ 1:N
        ▼
┌───────────────┐     1:N     ┌───────────────┐
│  OrderStatus  │<────────────│OrderStatusLog │
└───────────────┘             └───────────────┘
```

## Entity Specifications

| Entity          | Primary Data Store | Description                                   |
| --------------- | ------------------ | --------------------------------------------- |
| Order           | PostgreSQL         | Main order entity with core order information |
| OrderItem       | PostgreSQL         | Individual line items in an order             |
| BillingDetails  | PostgreSQL         | Payment and billing information for an order  |
| ShippingDetails | PostgreSQL         | Shipping destination and preferences          |
| OrderStatus     | PostgreSQL         | Current order status                          |
| OrderStatusLog  | DynamoDB           | Complete history of order status changes      |

## Detailed Entity Specifications

Each entity is described in detail in its own specification document:

- [01-order-entity.md](./01-order-entity.md): Defines the Order entity
- [02-order-item-entity.md](./02-order-item-entity.md): Defines the OrderItem entity
- [03-billing-details-entity.md](./03-billing-details-entity.md): Defines the BillingDetails entity
- [04-shipping-details-entity.md](./04-shipping-details-entity.md): Defines the ShippingDetails entity
- [05-order-status-entity.md](./05-order-status-entity.md): Defines the OrderStatus entity
- [06-order-status-log-entity.md](./06-order-status-log-entity.md): Defines the OrderStatusLog entity

## Database Schema

### PostgreSQL Schema

The relational database schema for the Order Service uses the following structure:

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id),
    product_id UUID NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE billing_details (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) UNIQUE,
    payment_method VARCHAR(50) NOT NULL,
    payment_id VARCHAR(100),
    billing_address_line1 VARCHAR(255) NOT NULL,
    billing_address_line2 VARCHAR(255),
    billing_city VARCHAR(100) NOT NULL,
    billing_state VARCHAR(100),
    billing_postal_code VARCHAR(20) NOT NULL,
    billing_country VARCHAR(2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE shipping_details (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) UNIQUE,
    recipient_name VARCHAR(255) NOT NULL,
    shipping_address_line1 VARCHAR(255) NOT NULL,
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100) NOT NULL,
    shipping_state VARCHAR(100),
    shipping_postal_code VARCHAR(20) NOT NULL,
    shipping_country VARCHAR(2) NOT NULL,
    shipping_method VARCHAR(50) NOT NULL,
    shipping_cost DECIMAL(8,2) NOT NULL,
    estimated_delivery_date TIMESTAMP WITH TIME ZONE,
    tracking_number VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE order_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    is_terminal BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Foreign Key Reference
ALTER TABLE orders ADD CONSTRAINT fk_orders_status
    FOREIGN KEY (status_id) REFERENCES order_statuses(id);

-- Indices
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_orders_status_id ON orders(status_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
```

### DynamoDB Schema

For the OrderStatusLog entity stored in DynamoDB, the schema will be:

```json
{
  "TableName": "OrderStatusLogs",
  "KeySchema": [
    {
      "AttributeName": "order_id",
      "KeyType": "HASH"
    },
    {
      "AttributeName": "timestamp",
      "KeyType": "RANGE"
    }
  ],
  "AttributeDefinitions": [
    {
      "AttributeName": "order_id",
      "AttributeType": "S"
    },
    {
      "AttributeName": "timestamp",
      "AttributeType": "S"
    },
    {
      "AttributeName": "status_id",
      "AttributeType": "N"
    }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "status-timestamp-index",
      "KeySchema": [
        {
          "AttributeName": "status_id",
          "KeyType": "HASH"
        },
        {
          "AttributeName": "timestamp",
          "KeyType": "RANGE"
        }
      ],
      "Projection": {
        "ProjectionType": "ALL"
      }
    }
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

## Data Access Patterns

The data model is optimized for the following primary access patterns:

1. Create new order with items, billing, and shipping details
2. Retrieve complete order by ID with all related information
3. Update order status
4. List orders by user ID with pagination
5. List orders by status with pagination
6. Get complete order status history
7. Search orders by various criteria (date range, amount range, etc.)

## ORM Entity Mapping

The data model will be implemented using TypeORM with the entity structure defined in the detailed entity specifications. The mapping between database tables and TypeScript entities will maintain a clean domain model while ensuring efficient database operations.

## References

- [Order Service Database Selection](../01-database-selection.md)
- [TypeORM Documentation](https://typeorm.io/)
- [ADR-004-data-persistence-strategy](../../../architecture/adr/ADR-004-data-persistence-strategy.md)
- [Data Storage and Management Specification](../../infrastructure/06-data-storage-specification.md)
