# Billing Details Entity Specification

## 1. Overview

The BillingDetails entity stores payment and billing information for an order. This entity captures all financial transaction details, including payment method, billing address, and any reference IDs from payment processors. It has a one-to-one relationship with the Order entity.

## 2. Entity Properties

| Property            | Type     | Required | Description                                           |
| ------------------- | -------- | -------- | ----------------------------------------------------- |
| id                  | UUID     | Yes      | Unique identifier for the billing details record      |
| orderId             | UUID     | Yes      | Reference to the associated order                     |
| paymentMethod       | String   | Yes      | Payment method used (e.g., CREDIT_CARD, PAYPAL)       |
| paymentId           | String   | No       | External payment transaction ID from processor        |
| billingAddressLine1 | String   | Yes      | First line of billing address                         |
| billingAddressLine2 | String   | No       | Second line of billing address (optional)             |
| billingCity         | String   | Yes      | City for billing address                              |
| billingState        | String   | No       | State/province for billing address (optional)         |
| billingPostalCode   | String   | Yes      | Postal/ZIP code for billing address                   |
| billingCountry      | String   | Yes      | Country code for billing address (ISO 3166-1 alpha-2) |
| createdAt           | DateTime | Yes      | Timestamp when the record was created                 |
| updatedAt           | DateTime | Yes      | Timestamp when the record was last updated            |

## 3. Relationships

| Relationship | Type       | Entity | Description                       |
| ------------ | ---------- | ------ | --------------------------------- |
| order        | One-to-One | Order  | The order these details belong to |

## 4. Database Schema

```sql
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

-- Indices
CREATE INDEX idx_billing_details_order_id ON billing_details(order_id);
CREATE INDEX idx_billing_details_payment_id ON billing_details(payment_id);
```

## 5. TypeORM Entity Definition

```typescript
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToOne,
  JoinColumn,
} from "typeorm";
import { Order } from "./order.entity";

@Entity("billing_details")
export class BillingDetails {
  @PrimaryGeneratedColumn("uuid")
  id: string;

  @Column({ name: "order_id", type: "uuid" })
  orderId: string;

  @Column({ name: "payment_method", type: "varchar", length: 50 })
  paymentMethod: string;

  @Column({ name: "payment_id", type: "varchar", length: 100, nullable: true })
  paymentId: string | null;

  @Column({ name: "billing_address_line1", type: "varchar", length: 255 })
  billingAddressLine1: string;

  @Column({
    name: "billing_address_line2",
    type: "varchar",
    length: 255,
    nullable: true,
  })
  billingAddressLine2: string | null;

  @Column({ name: "billing_city", type: "varchar", length: 100 })
  billingCity: string;

  @Column({
    name: "billing_state",
    type: "varchar",
    length: 100,
    nullable: true,
  })
  billingState: string | null;

  @Column({ name: "billing_postal_code", type: "varchar", length: 20 })
  billingPostalCode: string;

  @Column({ name: "billing_country", type: "varchar", length: 2 })
  billingCountry: string;

  @CreateDateColumn({ name: "created_at", type: "timestamp with time zone" })
  createdAt: Date;

  @UpdateDateColumn({ name: "updated_at", type: "timestamp with time zone" })
  updatedAt: Date;

  // Relationships
  @OneToOne(() => Order, (order) => order.billingDetails)
  @JoinColumn({ name: "order_id" })
  order: Order;
}
```

## 6. Business Rules and Validations

1. **Payment Method Validation**:

   - Payment method must be one of the supported types (CREDIT_CARD, PAYPAL, BANK_TRANSFER, etc.)
   - Different payment methods may require different validation logic and fields

2. **Address Validation**:

   - Country code must be a valid ISO 3166-1 alpha-2 code
   - Postal code format should be validated based on country
   - Required fields may vary by country (e.g., state is required for US but optional for many other countries)

3. **Data Security**:

   - No sensitive payment card data should be stored (comply with PCI DSS)
   - Only store tokenized payment references and minimal required information

4. **Uniqueness**:
   - Each order must have exactly one billing details record
   - The order_id field must be unique in the billing_details table

## 7. Data Access Patterns

### 7.1. Read Operations

| Operation                       | Access Pattern               | Expected Performance |
| ------------------------------- | ---------------------------- | -------------------- |
| Get billing details by order ID | Direct lookup by order_id    | <10ms                |
| Get billing details by ID       | Direct lookup by primary key | <10ms                |
| Find order by payment ID        | Query by payment_id          | <20ms                |

### 7.2. Write Operations

| Operation              | Access Pattern                | Expected Performance |
| ---------------------- | ----------------------------- | -------------------- |
| Create billing details | Insert with transaction       | <50ms                |
| Update billing details | Update by ID with transaction | <30ms                |
| Delete billing details | Delete by ID with transaction | <20ms                |

## 8. Sample Data

```json
{
  "id": "71f0c4d9-53e7-4d92-9a7e-f401b2e3e45d",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "paymentMethod": "CREDIT_CARD",
  "paymentId": "ch_3OBtP1CZ6qsJgndP0NZUQ1ZW",
  "billingAddressLine1": "123 Main St",
  "billingAddressLine2": "Apt 4B",
  "billingCity": "San Francisco",
  "billingState": "CA",
  "billingPostalCode": "94105",
  "billingCountry": "US",
  "createdAt": "2023-11-21T15:27:30Z",
  "updatedAt": "2023-11-21T15:27:30Z"
}
```

## 9. Integration with Payment Service

The BillingDetails entity works closely with the Payment Service through these interactions:

1. Payment processing requests are made to the Payment Service during order creation
2. Payment Service returns a payment ID that is stored in the BillingDetails entity
3. Payment status updates may trigger updates to BillingDetails and associated Order status

## 10. References

- [Order Service Data Model](./00-data-model-index.md)
- [Order Entity](./01-order-entity.md)
- [TypeORM Documentation](https://typeorm.io/)
- [Payment Service Integration](../06-integration-points/04-payment-service-integration.md)
- [ADR-004-data-persistence-strategy](../../../architecture/adr/ADR-004-data-persistence-strategy.md)
