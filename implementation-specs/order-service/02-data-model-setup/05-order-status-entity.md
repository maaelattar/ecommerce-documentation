# Order Status Entity Specification

## 1. Overview

The OrderStatus entity defines the possible states of an order throughout its lifecycle. This entity serves as a reference table that contains predefined status values and their descriptions. Each Order references a specific status from this entity to indicate its current state in the order fulfillment workflow.

## 2. Entity Properties

| Property    | Type     | Required | Description                                          |
| ----------- | -------- | -------- | ---------------------------------------------------- |
| id          | Integer  | Yes      | Unique identifier for the status (auto-increment)    |
| name        | String   | Yes      | Machine-readable status code (e.g., PENDING_PAYMENT) |
| description | Text     | Yes      | Human-readable description of the status             |
| isTerminal  | Boolean  | Yes      | Indicates if this is a terminal (final) status       |
| createdAt   | DateTime | Yes      | Timestamp when the record was created                |
| updatedAt   | DateTime | Yes      | Timestamp when the record was last updated           |

## 3. Relationships

| Relationship | Type        | Entity | Description                  |
| ------------ | ----------- | ------ | ---------------------------- |
| orders       | One-to-Many | Order  | Orders that have this status |

## 4. Database Schema

```sql
CREATE TABLE order_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    is_terminal BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indices
CREATE INDEX idx_order_statuses_name ON order_statuses(name);
CREATE INDEX idx_order_statuses_is_terminal ON order_statuses(is_terminal);
```

## 5. TypeORM Entity Definition

```typescript
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
} from "typeorm";
import { Order } from "./order.entity";

@Entity("order_statuses")
export class OrderStatus {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: "varchar", length: 50, unique: true })
  name: string;

  @Column({ type: "text" })
  description: string;

  @Column({ name: "is_terminal", type: "boolean", default: false })
  isTerminal: boolean;

  @CreateDateColumn({ name: "created_at", type: "timestamp with time zone" })
  createdAt: Date;

  @UpdateDateColumn({ name: "updated_at", type: "timestamp with time zone" })
  updatedAt: Date;

  // Relationships
  @OneToMany(() => Order, (order) => order.status)
  orders: Order[];
}
```

## 6. Predefined Order Statuses

The system defines the following order statuses:

| ID  | Name                 | Description                                           | Is Terminal |
| --- | -------------------- | ----------------------------------------------------- | ----------- |
| 1   | PENDING_PAYMENT      | Order created but payment not yet processed           | No          |
| 2   | PAYMENT_PROCESSING   | Payment is being processed                            | No          |
| 3   | PAYMENT_FAILED       | Payment processing failed                             | Yes         |
| 4   | PAYMENT_COMPLETED    | Payment successfully processed                        | No          |
| 5   | AWAITING_FULFILLMENT | Order ready for fulfillment                           | No          |
| 6   | PROCESSING           | Order is being processed (picking/packing)            | No          |
| 7   | PARTIALLY_SHIPPED    | Some items have been shipped                          | No          |
| 8   | SHIPPED              | All items have been shipped                           | No          |
| 9   | OUT_FOR_DELIVERY     | Order is out for delivery                             | No          |
| 10  | DELIVERED            | Order has been delivered                              | Yes         |
| 11  | CANCELLED            | Order has been cancelled                              | Yes         |
| 12  | REFUND_REQUESTED     | Customer has requested a refund                       | No          |
| 13  | PARTIALLY_REFUNDED   | Order has been partially refunded                     | No          |
| 14  | REFUNDED             | Order has been fully refunded                         | Yes         |
| 15  | ON_HOLD              | Order is on hold (e.g., fraud check, inventory issue) | No          |

## 7. Status Transition Rules

Not all status transitions are valid. The following table defines the allowed transitions between statuses:

| Current Status       | Valid Next Statuses                                              |
| -------------------- | ---------------------------------------------------------------- |
| PENDING_PAYMENT      | PAYMENT_PROCESSING, CANCELLED                                    |
| PAYMENT_PROCESSING   | PAYMENT_COMPLETED, PAYMENT_FAILED                                |
| PAYMENT_FAILED       | PENDING_PAYMENT, CANCELLED                                       |
| PAYMENT_COMPLETED    | AWAITING_FULFILLMENT, REFUND_REQUESTED, CANCELLED, ON_HOLD       |
| AWAITING_FULFILLMENT | PROCESSING, REFUND_REQUESTED, CANCELLED, ON_HOLD                 |
| PROCESSING           | PARTIALLY_SHIPPED, SHIPPED, REFUND_REQUESTED, CANCELLED, ON_HOLD |
| PARTIALLY_SHIPPED    | SHIPPED, REFUND_REQUESTED, PARTIALLY_REFUNDED                    |
| SHIPPED              | OUT_FOR_DELIVERY, DELIVERED, REFUND_REQUESTED                    |
| OUT_FOR_DELIVERY     | DELIVERED, REFUND_REQUESTED                                      |
| DELIVERED            | REFUND_REQUESTED                                                 |
| REFUND_REQUESTED     | PARTIALLY_REFUNDED, REFUNDED, CANCELLED                          |
| PARTIALLY_REFUNDED   | REFUNDED                                                         |
| ON_HOLD              | AWAITING_FULFILLMENT, CANCELLED, REFUND_REQUESTED                |

## 8. Business Rules and Validations

1. **Status Code Uniqueness**:

   - Each status name must be unique in the system
   - Status names should follow a consistent convention (UPPERCASE_WITH_UNDERSCORES)

2. **Status Transitions**:

   - Status transitions must follow the defined transition rules
   - Invalid transitions should be rejected with appropriate error messages

3. **Terminal Statuses**:

   - Terminal statuses represent the end of an order's lifecycle
   - Orders in terminal status cannot transition to non-terminal statuses

4. **Status History**:

   - All status changes must be recorded in the OrderStatusLog (in DynamoDB)
   - Each log entry must include the previous status, new status, timestamp, and user/system that made the change

5. **Status References**:
   - Status records are pre-populated and should not be deleted
   - New statuses may be added but existing ones should not be removed

## 9. Data Access Patterns

### 9.1. Read Operations

| Operation             | Access Pattern                | Expected Performance |
| --------------------- | ----------------------------- | -------------------- |
| Get all statuses      | Full table scan (small table) | <20ms                |
| Get status by ID      | Direct lookup by primary key  | <5ms                 |
| Get status by name    | Lookup by unique index        | <5ms                 |
| Get terminal statuses | Filter by is_terminal = true  | <10ms                |

### 9.2. Write Operations

The OrderStatus table is primarily reference data that is initialized during system setup and rarely modified:

| Operation                 | Access Pattern | Expected Performance |
| ------------------------- | -------------- | -------------------- |
| Initialize status table   | Batch insert   | <100ms               |
| Add new status            | Single insert  | <20ms                |
| Update status description | Update by ID   | <20ms                |

## 10. Status Initialization SQL

```sql
-- Insert initial order statuses
INSERT INTO order_statuses (name, description, is_terminal) VALUES
('PENDING_PAYMENT', 'Order created but payment not yet processed', FALSE),
('PAYMENT_PROCESSING', 'Payment is being processed', FALSE),
('PAYMENT_FAILED', 'Payment processing failed', TRUE),
('PAYMENT_COMPLETED', 'Payment successfully processed', FALSE),
('AWAITING_FULFILLMENT', 'Order ready for fulfillment', FALSE),
('PROCESSING', 'Order is being processed (picking/packing)', FALSE),
('PARTIALLY_SHIPPED', 'Some items have been shipped', FALSE),
('SHIPPED', 'All items have been shipped', FALSE),
('OUT_FOR_DELIVERY', 'Order is out for delivery', FALSE),
('DELIVERED', 'Order has been delivered', TRUE),
('CANCELLED', 'Order has been cancelled', TRUE),
('REFUND_REQUESTED', 'Customer has requested a refund', FALSE),
('PARTIALLY_REFUNDED', 'Order has been partially refunded', FALSE),
('REFUNDED', 'Order has been fully refunded', TRUE),
('ON_HOLD', 'Order is on hold (e.g., fraud check, inventory issue)', FALSE);
```

## 11. Status Workflow Diagram

```
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│                  │         │                  │         │                  │
│  PENDING_PAYMENT ├────────>│PAYMENT_PROCESSING├────────>│PAYMENT_COMPLETED │
│                  │         │                  │         │                  │
└──────────────────┘         └──────────────────┘         └────────┬─────────┘
        │                             │                            │
        │                             │                            │
        │                             ▼                            ▼
        │                    ┌──────────────────┐         ┌──────────────────┐
        │                    │                  │         │                  │
        └───────────────────>│  PAYMENT_FAILED  │         │AWAITING_FULFILLMENT
                             │                  │         │                  │
                             └──────────────────┘         └────────┬─────────┘
                                                                   │
                                                                   │
                                                                   ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│                  │         │                  │         │                  │
│   CANCELLED      │<────────┤     ON_HOLD      │<────────┤    PROCESSING    │
│                  │         │                  │         │                  │
└──────────────────┘         └──────────────────┘         └────────┬─────────┘
        ▲                                                          │
        │                                                          │
        │                                                          ▼
        │                    ┌──────────────────┐         ┌──────────────────┐
        │                    │                  │         │                  │
        │                    │PARTIALLY_SHIPPED │<────────┤     SHIPPED      │
        │                    │                  │         │                  │
        │                    └────────┬─────────┘         └────────┬─────────┘
        │                             │                            │
        │                             │                            │
        │                             ▼                            ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│                  │         │                  │         │                  │
│     REFUNDED     │<────────┤PARTIALLY_REFUNDED│<────────┤ OUT_FOR_DELIVERY │
│                  │         │                  │         │                  │
└──────────────────┘         └──────────────────┘         └────────┬─────────┘
        ▲                             ▲                            │
        │                             │                            │
        │                             │                            ▼
        │                    ┌──────────────────┐         ┌──────────────────┐
        │                    │                  │         │                  │
        └────────────────────┤REFUND_REQUESTED  │<────────┤    DELIVERED     │
                             │                  │         │                  │
                             └──────────────────┘         └──────────────────┘
```

## 12. References

- [Order Service Data Model](./00-data-model-index.md)
- [Order Entity](./01-order-entity.md)
- [Order Status Log Entity](./06-order-status-log-entity.md)
- [TypeORM Documentation](https://typeorm.io/)
- [ADR-004-data-persistence-strategy](../../../architecture/adr/ADR-004-data-persistence-strategy.md)
