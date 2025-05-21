# Shipping Details Entity Specification

## 1. Overview

The ShippingDetails entity stores delivery information for an order, including the recipient's address, shipping method, cost, and tracking information. This entity has a one-to-one relationship with the Order entity and contains all data necessary for order fulfillment.

## 2. Entity Properties

| Property              | Type     | Required | Description                                            |
| --------------------- | -------- | -------- | ------------------------------------------------------ |
| id                    | UUID     | Yes      | Unique identifier for the shipping details             |
| orderId               | UUID     | Yes      | Reference to the associated order                      |
| recipientName         | String   | Yes      | Name of the recipient                                  |
| shippingAddressLine1  | String   | Yes      | First line of shipping address                         |
| shippingAddressLine2  | String   | No       | Second line of shipping address (optional)             |
| shippingCity          | String   | Yes      | City for shipping address                              |
| shippingState         | String   | No       | State/province for shipping address (optional)         |
| shippingPostalCode    | String   | Yes      | Postal/ZIP code for shipping address                   |
| shippingCountry       | String   | Yes      | Country code for shipping address (ISO 3166-1 alpha-2) |
| shippingMethod        | String   | Yes      | Selected shipping method (e.g., STANDARD, EXPRESS)     |
| shippingCost          | Decimal  | Yes      | Cost of shipping                                       |
| estimatedDeliveryDate | DateTime | No       | Estimated date of delivery                             |
| trackingNumber        | String   | No       | Shipment tracking number (once available)              |
| createdAt             | DateTime | Yes      | Timestamp when the record was created                  |
| updatedAt             | DateTime | Yes      | Timestamp when the record was last updated             |

## 3. Relationships

| Relationship | Type       | Entity | Description                       |
| ------------ | ---------- | ------ | --------------------------------- |
| order        | One-to-One | Order  | The order these details belong to |

## 4. Database Schema

```sql
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

-- Indices
CREATE INDEX idx_shipping_details_order_id ON shipping_details(order_id);
CREATE INDEX idx_shipping_details_tracking_number ON shipping_details(tracking_number);
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

@Entity("shipping_details")
export class ShippingDetails {
  @PrimaryGeneratedColumn("uuid")
  id: string;

  @Column({ name: "order_id", type: "uuid" })
  orderId: string;

  @Column({ name: "recipient_name", type: "varchar", length: 255 })
  recipientName: string;

  @Column({ name: "shipping_address_line1", type: "varchar", length: 255 })
  shippingAddressLine1: string;

  @Column({
    name: "shipping_address_line2",
    type: "varchar",
    length: 255,
    nullable: true,
  })
  shippingAddressLine2: string | null;

  @Column({ name: "shipping_city", type: "varchar", length: 100 })
  shippingCity: string;

  @Column({
    name: "shipping_state",
    type: "varchar",
    length: 100,
    nullable: true,
  })
  shippingState: string | null;

  @Column({ name: "shipping_postal_code", type: "varchar", length: 20 })
  shippingPostalCode: string;

  @Column({ name: "shipping_country", type: "varchar", length: 2 })
  shippingCountry: string;

  @Column({ name: "shipping_method", type: "varchar", length: 50 })
  shippingMethod: string;

  @Column({ name: "shipping_cost", type: "decimal", precision: 8, scale: 2 })
  shippingCost: number;

  @Column({
    name: "estimated_delivery_date",
    type: "timestamp with time zone",
    nullable: true,
  })
  estimatedDeliveryDate: Date | null;

  @Column({
    name: "tracking_number",
    type: "varchar",
    length: 100,
    nullable: true,
  })
  trackingNumber: string | null;

  @CreateDateColumn({ name: "created_at", type: "timestamp with time zone" })
  createdAt: Date;

  @UpdateDateColumn({ name: "updated_at", type: "timestamp with time zone" })
  updatedAt: Date;

  // Relationships
  @OneToOne(() => Order, (order) => order.shippingDetails)
  @JoinColumn({ name: "order_id" })
  order: Order;
}
```

## 6. Business Rules and Validations

1. **Shipping Method Validation**:

   - Shipping method must be one of the supported methods (STANDARD, EXPRESS, OVERNIGHT, etc.)
   - Different shipping methods may have different cost calculations and estimated delivery times

2. **Address Validation**:

   - Country code must be a valid ISO 3166-1 alpha-2 code
   - Postal code format should be validated based on country
   - Required fields may vary by country (e.g., state is required for US but optional for many other countries)

3. **Shipping Cost Rules**:

   - Shipping cost must be calculated based on destination, weight, dimensions, and selected shipping method
   - Free shipping may apply based on order total or promotions

4. **Tracking Information**:

   - Tracking number format validation should be based on the carrier
   - Tracking information should be updated when available from logistics provider

5. **Uniqueness**:
   - Each order must have exactly one shipping details record
   - The order_id field must be unique in the shipping_details table

## 7. Data Access Patterns

### 7.1. Read Operations

| Operation                          | Access Pattern                         | Expected Performance |
| ---------------------------------- | -------------------------------------- | -------------------- |
| Get shipping details by order ID   | Direct lookup by order_id              | <10ms                |
| Get shipping details by ID         | Direct lookup by primary key           | <10ms                |
| Find order by tracking number      | Query by tracking_number               | <20ms                |
| List orders by shipping method     | Query by shipping_method               | <50ms                |
| List orders by delivery date range | Range query on estimated_delivery_date | <50ms                |

### 7.2. Write Operations

| Operation                     | Access Pattern               | Expected Performance |
| ----------------------------- | ---------------------------- | -------------------- |
| Create shipping details       | Insert with transaction      | <50ms                |
| Update tracking information   | Update specific fields by ID | <30ms                |
| Update delivery estimate      | Update specific fields by ID | <30ms                |
| Complete shipping information | Update multiple fields by ID | <50ms                |

## 8. Shipping Method Options

The system supports the following shipping methods:

| Method Code   | Name          | Description                                  | Typical Delivery Time |
| ------------- | ------------- | -------------------------------------------- | --------------------- |
| STANDARD      | Standard      | Regular shipping with no priority            | 5-7 business days     |
| EXPRESS       | Express       | Faster shipping with higher priority         | 2-3 business days     |
| OVERNIGHT     | Overnight     | Next-day delivery for urgent orders          | 1 business day        |
| INTERNATIONAL | International | International shipping with customs handling | 7-14 business days    |
| STORE_PICKUP  | Store Pickup  | Customer collects from physical location     | Same day (when ready) |

## 9. Sample Data

```json
{
  "id": "1d2ca47d-8a7c-4b1a-b12c-0e99e252f295",
  "orderId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "recipientName": "John Doe",
  "shippingAddressLine1": "123 Main St",
  "shippingAddressLine2": "Apt 4B",
  "shippingCity": "San Francisco",
  "shippingState": "CA",
  "shippingPostalCode": "94105",
  "shippingCountry": "US",
  "shippingMethod": "STANDARD",
  "shippingCost": 5.99,
  "estimatedDeliveryDate": "2023-11-27T12:00:00Z",
  "trackingNumber": "1ZW470X56892747254",
  "createdAt": "2023-11-21T15:27:30Z",
  "updatedAt": "2023-11-21T15:27:30Z"
}
```

## 10. Shipping Lifecycle Events

The shipping details entity participates in the following lifecycle events:

1. **Creation**: Initial shipping information recorded during order placement
2. **Dispatch Preparation**: Updated when order is being prepared for shipment
3. **Shipment**: Updated with tracking information when the order is shipped
4. **Delivery Status Updates**: Updated as delivery status changes
5. **Delivery Confirmation**: Updated when delivery is confirmed

## 11. References

- [Order Service Data Model](./00-data-model-index.md)
- [Order Entity](./01-order-entity.md)
- [TypeORM Documentation](https://typeorm.io/)
- [Order Fulfillment Process](../03-core-service-components/05-fulfillment-process.md)
- [ADR-004-data-persistence-strategy](../../../architecture/adr/ADR-004-data-persistence-strategy.md)
