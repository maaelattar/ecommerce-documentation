# Order Entity Specification

## 1. Overview

The Order entity is the core data structure in the Order Service, representing a customer's purchase. It contains essential information about the order, including references to the customer, order items, payment details, shipping information, and current status.

## 2. Entity Properties

| Property    | Type     | Required | Description                                            |
| ----------- | -------- | -------- | ------------------------------------------------------ |
| id          | UUID     | Yes      | Unique identifier for the order                        |
| userId      | UUID     | Yes      | Reference to the customer who placed the order         |
| orderDate   | DateTime | Yes      | Timestamp when the order was placed                    |
| totalAmount | Decimal  | Yes      | Total order amount including all items and taxes       |
| currency    | String   | Yes      | Three-letter currency code (e.g., USD, EUR)            |
| statusId    | Integer  | Yes      | Current status of the order (reference to OrderStatus) |
| createdAt   | DateTime | Yes      | Timestamp when the record was created                  |
| updatedAt   | DateTime | Yes      | Timestamp when the record was last updated             |

## 3. Relationships

| Relationship    | Type        | Entity          | Description                           |
| --------------- | ----------- | --------------- | ------------------------------------- |
| orderItems      | One-to-Many | OrderItem       | Items included in the order           |
| billingDetails  | One-to-One  | BillingDetails  | Payment and billing information       |
| shippingDetails | One-to-One  | ShippingDetails | Shipping destination and preferences  |
| status          | Many-to-One | OrderStatus     | Current status of the order           |
| statusLogs      | One-to-Many | OrderStatusLog  | Complete status history (in DynamoDB) |

## 4. Database Schema

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status_id INTEGER NOT NULL REFERENCES order_statuses(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indices
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status_id ON orders(status_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
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
  OneToOne,
  ManyToOne,
  JoinColumn,
} from "typeorm";
import { OrderItem } from "./order-item.entity";
import { BillingDetails } from "./billing-details.entity";
import { ShippingDetails } from "./shipping-details.entity";
import { OrderStatus } from "./order-status.entity";

@Entity("orders")
export class Order {
  @PrimaryGeneratedColumn("uuid")
  id: string;

  @Column({ name: "user_id", type: "uuid" })
  userId: string;

  @Column({ name: "order_date", type: "timestamp with time zone" })
  orderDate: Date;

  @Column({ name: "total_amount", type: "decimal", precision: 12, scale: 2 })
  totalAmount: number;

  @Column({ type: "varchar", length: 3 })
  currency: string;

  @Column({ name: "status_id" })
  statusId: number;

  @CreateDateColumn({ name: "created_at", type: "timestamp with time zone" })
  createdAt: Date;

  @UpdateDateColumn({ name: "updated_at", type: "timestamp with time zone" })
  updatedAt: Date;

  // Relationships
  @OneToMany(() => OrderItem, (orderItem) => orderItem.order, { cascade: true })
  orderItems: OrderItem[];

  @OneToOne(() => BillingDetails, (billingDetails) => billingDetails.order, {
    cascade: true,
  })
  billingDetails: BillingDetails;

  @OneToOne(() => ShippingDetails, (shippingDetails) => shippingDetails.order, {
    cascade: true,
  })
  shippingDetails: ShippingDetails;

  @ManyToOne(() => OrderStatus, (status) => status.orders)
  @JoinColumn({ name: "status_id" })
  status: OrderStatus;
}
```

## 6. Business Rules and Validations

1. **Order Creation**:

   - An order must have at least one order item
   - Total amount must be the sum of all order item totals plus any taxes or fees
   - Currency must be a valid ISO 4217 code

2. **Status Transitions**:

   - Orders can only transition between allowed statuses (defined in the OrderStatus entity)
   - Each status change must be logged in the OrderStatusLog

3. **User Association**:

   - An order must be associated with a valid user
   - The order service must verify user existence via the User Service API

4. **Uniqueness**:
   - Order IDs must be globally unique
   - UUID v4 will be used for ID generation

## 7. Data Access Patterns

### 7.1. Read Operations

| Operation                          | Access Pattern                            | Expected Performance |
| ---------------------------------- | ----------------------------------------- | -------------------- |
| Get order by ID                    | Direct lookup by primary key              | <10ms                |
| List orders by user                | Query by user_id with pagination          | <50ms                |
| List orders by status              | Query by status_id with pagination        | <50ms                |
| List orders by date range          | Range query on order_date with pagination | <100ms               |
| Search orders by multiple criteria | Filtered query with compound conditions   | <200ms               |

### 7.2. Write Operations

| Operation               | Access Pattern                                     | Expected Performance |
| ----------------------- | -------------------------------------------------- | -------------------- |
| Create order            | Transactional insert of order and related entities | <200ms               |
| Update order status     | Update status_id field and create status log       | <50ms                |
| Update shipping details | Update specific fields in shipping_details         | <50ms                |
| Cancel order            | Update status to 'cancelled' and create status log | <50ms                |

## 8. Sample Data

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "orderDate": "2023-11-21T15:27:30Z",
  "totalAmount": 149.99,
  "currency": "USD",
  "statusId": 2,
  "createdAt": "2023-11-21T15:27:30Z",
  "updatedAt": "2023-11-21T15:27:30Z",
  "orderItems": [
    {
      "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "productId": "0e8dddc7-9ebf-41f3-b08a-5a3f91f1c3c0",
      "quantity": 1,
      "unitPrice": 129.99,
      "totalPrice": 129.99
    },
    {
      "id": "098f6bcd-4621-3373-8ade-4e832627b4f6",
      "productId": "9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23",
      "quantity": 2,
      "unitPrice": 10.0,
      "totalPrice": 20.0
    }
  ],
  "billingDetails": {
    "id": "71f0c4d9-53e7-4d92-9a7e-f401b2e3e45d",
    "paymentMethod": "CREDIT_CARD",
    "paymentId": "ch_3OBtP1CZ6qsJgndP0NZUQ1ZW",
    "billingAddressLine1": "123 Main St",
    "billingAddressLine2": "Apt 4B",
    "billingCity": "San Francisco",
    "billingState": "CA",
    "billingPostalCode": "94105",
    "billingCountry": "US"
  },
  "shippingDetails": {
    "id": "1d2ca47d-8a7c-4b1a-b12c-0e99e252f295",
    "recipientName": "John Doe",
    "shippingAddressLine1": "123 Main St",
    "shippingAddressLine2": "Apt 4B",
    "shippingCity": "San Francisco",
    "shippingState": "CA",
    "shippingPostalCode": "94105",
    "shippingCountry": "US",
    "shippingMethod": "STANDARD",
    "shippingCost": 0.0,
    "estimatedDeliveryDate": "2023-11-25T12:00:00Z"
  }
}
```

## 9. References

- [Order Service Data Model](./00-data-model-index.md)
- [Order Item Entity](./02-order-item-entity.md)
- [Billing Details Entity](./03-billing-details-entity.md)
- [Shipping Details Entity](./04-shipping-details-entity.md)
- [Order Status Entity](./05-order-status-entity.md)
- [TypeORM Documentation](https://typeorm.io/)
- [ADR-004-data-persistence-strategy](../../../architecture/adr/ADR-004-data-persistence-strategy.md)
