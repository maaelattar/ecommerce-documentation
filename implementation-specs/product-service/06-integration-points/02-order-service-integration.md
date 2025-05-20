# Order Service Integration with Product Service

## 1. Overview

This document outlines how the **Order Service integrates with the Product Service**. The Order Service requires product information (like name, price, attributes, validity) during the order lifecycle. Integration is achieved through a combination of asynchronous event consumption and specific, justified synchronous API calls.

- **Asynchronous Event Consumption (Primary for General Product Data)**: The Order Service subscribes to events published by the Product Service (e.g., `ProductCreated`, `ProductUpdated`, `ProductPriceChanged`, `ProductStatusChanged` - see [Phase 5: Event Publishing](../../05-event-publishing/)) via the central message broker (Amazon MQ for RabbitMQ or Amazon MSK, as per [03-message-broker-selection.md](../../../architecture/technology-decisions-aws-centeric/03-message-broker-selection.md)). These events populate a local, eventually consistent product catalog within the Order Service's database.
- **Synchronous API Calls (Exceptional for Critical Transactional Data)**: In specific, justified scenarios (primarily during order creation), the Order Service makes direct RESTful API calls to the Product Service to get real-time, authoritative product data.

## 2. Business Justification for Synchronous Calls

The primary justification for synchronous calls from Order Service to Product Service at order creation time is to ensure **transactional accuracy**:

- **Price Accuracy**: Capturing the exact, current price at the moment a customer commits to purchase.
- **Product Validity**: Confirming the product/variant is still available for sale (not discontinued or switched to inactive status).
- **Transaction Integrity**: Ensuring the order contains only valid, purchasable items with correct, current prices before finalizing the transaction.

This justification is based on the business requirement for customers to pay the price they saw at checkout, and for the system to reject orders containing products that have just been discontinued.

## 3. Asynchronous Integration (Primary Pattern)

### 3.1. Event Consumption by Order Service

The Order Service maintains a local, eventually consistent product catalog by consuming the following Product Service events:

| Event                  | Purpose for Order Service            | Action Taken                                    |
| ---------------------- | ------------------------------------ | ----------------------------------------------- |
| `ProductCreated`       | Add product to local catalog         | Create new product record in Order Service DB   |
| `ProductUpdated`       | Update local product metadata        | Update product details in Order Service DB      |
| `ProductStatusChanged` | Keep track of product availability   | Update product status in Order Service DB       |
| `ProductPriceUpdated`  | Maintain local price reference       | Update product price in Order Service DB        |
| `ProductDeleted`       | Remove products from local catalog   | Mark product as deleted in Order Service DB     |
| `CategoryUpdated`      | Keep category hierarchy data current | Update category information in Order Service DB |

This local product catalog serves several purposes:

- Enables product search and browsing without calling Product Service.
- Allows for validation of most cart operations without synchronous calls.
- Provides a backup in case the Product Service is temporarily unavailable.
- Improves performance of order history displays that include product details.

### 3.2. Data Model Considerations

The Order Service's local product catalog is a **denormalized projection** optimized for order processing:

- Contains only essential product attributes needed for order processing.
- Does not store full product descriptions, images, etc.
- Maintained by event-driven updates.
- Eventually consistent with the authoritative Product Service.

## 4. Synchronous API Integration (Exceptional Pattern)

For the justified synchronous scenarios, the Order Service will call the following Product Service APIs:

### GET /products/variants/{variantId}

**Purpose**: Get authoritative, real-time product variant data at the moment of order creation.

**When Called**: During checkout/order placement, after payment is authorized but before the order is committed.

**Sample Request**:

```
GET /api/v1/products/variants/39fdca29-1f2b-4f5b-982e-17bcb1284f1b HTTP/1.1
Host: product-service.example.com
Authorization: Bearer {jwt_token}
```

**Sample Success Response (200 OK)**:

```json
{
  "id": "39fdca29-1f2b-4f5b-982e-17bcb1284f1b",
  "productId": "943a49c2-7a30-49e4-93a5-c396e8a7a959",
  "sku": "SHOE-RED-42",
  "name": "Running Shoes - Red, Size 42",
  "status": "ACTIVE",
  "price": {
    "amount": "89.99",
    "currency": "USD",
    "effectiveDate": "2023-05-15T00:00:00Z"
  },
  "attributes": [
    { "name": "color", "value": "Red" },
    { "name": "size", "value": "42" }
  ],
  "inventoryStatus": "IN_STOCK"
}
```

**Error Responses**:

- 404 Not Found: Variant not found
- 400 Bad Request: Invalid request format
- 500 Internal Server Error: Server-side error

### GET /products/variants/{variantId}/price

**Purpose**: Get authoritative, real-time pricing data at the moment of order creation.

**When Called**: During checkout/order placement, as a lightweight alternative to fetching the entire variant if only price data is needed.

**Sample Request**:

```
GET /api/v1/products/variants/39fdca29-1f2b-4f5b-982e-17bcb1284f1b/price HTTP/1.1
Host: product-service.example.com
Authorization: Bearer {jwt_token}
```

**Sample Success Response (200 OK)**:

```json
{
  "variantId": "39fdca29-1f2b-4f5b-982e-17bcb1284f1b",
  "basePrice": "99.99",
  "currentPrice": "89.99",
  "discountAmount": "10.00",
  "discountPercentage": "10",
  "currency": "USD",
  "effectiveDate": "2023-05-15T00:00:00Z"
}
```

## 5. Data Consistency Strategy

The Order Service employs a hybrid approach to maintain data consistency:

1. **Eventual Consistency (General Operations)**:

   - Uses local, eventually consistent data for most operations (browsing, cart management).
   - This data is kept up-to-date via event consumption.

2. **Strong Consistency (Transaction Critical)**:
   - Uses synchronous API calls for the exact moment of order finalization.
   - Creates an immutable "snapshot" of product data at the time of order:
     ```json
     {
       "orderId": "67890",
       "orderDate": "2023-06-01T14:30:00Z",
       "items": [
         {
           "productId": "943a49c2-7a30-49e4-93a5-c396e8a7a959",
           "variantId": "39fdca29-1f2b-4f5b-982e-17bcb1284f1b",
           "productSnapshot": {
             "name": "Running Shoes - Red, Size 42",
             "sku": "SHOE-RED-42",
             "price": {
               "amount": "89.99",
               "currency": "USD",
               "effectiveDate": "2023-05-15T00:00:00Z"
             },
             "attributes": [
               { "name": "color", "value": "Red" },
               { "name": "size", "value": "42" }
             ]
           },
           "quantity": 1,
           "unitPrice": "89.99",
           "totalPrice": "89.99"
         }
       ]
     }
     ```
   - This snapshot ensures that order history always reflects what the customer actually purchased, regardless of subsequent product changes.

## 6. Error Handling

The Order Service implements the resilience patterns defined in [07-general-api-consumption-guidelines.md](./07-general-api-consumption-guidelines.md) when calling Product Service APIs:

- **Circuit Breaker**: Fail fast if Product Service becomes unresponsive.
- **Timeouts**: Abort requests that take too long (e.g., 1-2 seconds maximum).
- **Retries**: Retry transient failures with exponential backoff.
- **Fallback Strategy**:
  - If synchronous calls fail during checkout, the Order Service can fall back to its local data as a last resort, with a clear indication to the user that prices may not be final and will be confirmed.
  - Alternatively, the checkout can be rejected with an appropriate message if real-time product validation is deemed critical.

## 7. Security

- The Order Service authenticates to the Product Service using OAuth 2.0 / JWT.
- All API calls use HTTPS.
- The Order Service is granted a specific service role with permissions limited to reading product data.
- API calls contain correlation IDs for tracing and auditing.
