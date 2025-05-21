# Order Item Entity Specification

## 1. Overview

The OrderItem entity represents individual line items within an order. Each OrderItem corresponds to a specific product and quantity that a customer has purchased as part of their order. These items collectively make up the contents of an order and contribute to its total cost.

## 2. Entity Properties

| Property   | Type     | Required | Description                                            |
| ---------- | -------- | -------- | ------------------------------------------------------ |
| id         | UUID     | Yes      | Unique identifier for the order item                   |
| orderId    | UUID     | Yes      | Reference to the parent order                          |
| productId  | UUID     | Yes      | Reference to the purchased product                     |
| quantity   | Integer  | Yes      | Number of units purchased                              |
| unitPrice  | Decimal  | Yes      | Price per unit at time of purchase                     |
| totalPrice | Decimal  | Yes      | Total price for this line item (quantity \* unitPrice) |
| createdAt  | DateTime | Yes      | Timestamp when the record was created                  |
| updatedAt  | DateTime | Yes      | Timestamp when the record was last updated             |

## 3. Relationships

| Relationship | Type        | Entity  | Description                         |
| ------------ | ----------- | ------- | ----------------------------------- |
| order        | Many-to-One | Order   | The order containing this line item |
| product      | Reference   | Product | Product referenced by this item     |

## 4. Database Schema

```sql
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

-- Indices
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
```

## 5. TypeORM Entity Definition

```typescript
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
} from "typeorm";
import { Order } from "./order.entity";

@Entity("order_items")
export class OrderItem {
  @PrimaryGeneratedColumn("uuid")
  id: string;

  @Column({ name: "order_id", type: "uuid" })
  orderId: string;

  @Column({ name: "product_id", type: "uuid" })
  productId: string;

  @Column({ type: "integer" })
  quantity: number;

  @Column({ name: "unit_price", type: "decimal", precision: 10, scale: 2 })
  unitPrice: number;

  @Column({ name: "total_price", type: "decimal", precision: 10, scale: 2 })
  totalPrice: number;

  @CreateDateColumn({ name: "created_at", type: "timestamp with time zone" })
  createdAt: Date;

  @UpdateDateColumn({ name: "updated_at", type: "timestamp with time zone" })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => Order, (order) => order.orderItems)
  @JoinColumn({ name: "order_id" })
  order: Order;
}
```

## 6. Business Rules and Validations

1. **Quantity Validation**:

   - Quantity must be a positive integer
   - Maximum quantity per line item may be limited by product-specific constraints

2. **Price Calculation**:

   - Total price must equal the unit price multiplied by the quantity
   - Price fields must have appropriate precision for currency values

3. **Product Validation**:

   - Referenced product must exist in the Product Service
   - Product availability should be verified at order creation time

4. **Orphan Prevention**:
   - OrderItem cannot exist without a parent Order
   - Deletion of Order should cascade to its OrderItems

## 7. Data Access Patterns

### 7.1. Read Operations

| Operation                        | Access Pattern                      | Expected Performance |
| -------------------------------- | ----------------------------------- | -------------------- |
| Get order items by order ID      | Query by order_id                   | <20ms                |
| Get order item by ID             | Direct lookup by primary key        | <10ms                |
| Get orders containing product ID | Query by product_id with pagination | <50ms                |

### 7.2. Write Operations

| Operation                  | Access Pattern                     | Expected Performance |
| -------------------------- | ---------------------------------- | -------------------- |
| Create order items (bulk)  | Batch insert with transaction      | <100ms               |
| Update order item quantity | Update with recalculation of total | <30ms                |
| Delete order item          | Delete by ID with transaction      | <20ms                |

## 8. Sample Data

```json
{
  "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
  "quantity": 2,
  "unitPrice": 29.99,
  "totalPrice": 59.98,
  "createdAt": "2023-11-21T15:27:30Z",
  "updatedAt": "2023-11-21T15:27:30Z"
}
```

## 9. References

- [Order Service Data Model](./00-data-model-index.md)
- [Order Entity](./01-order-entity.md)
- [TypeORM Documentation](https://typeorm.io/)
- [Product Service Integration](../06-integration-points/02-product-service-integration.md)
- [ADR-004-data-persistence-strategy](../../../architecture/adr/ADR-004-data-persistence-strategy.md)
