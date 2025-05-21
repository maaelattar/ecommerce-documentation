# Order Service Integration

## Overview

The integration between the Inventory Service and Order Service is a critical component of the e-commerce platform. This integration enables inventory allocation for orders, inventory updates upon order status changes, and coordination of fulfillment processes.

## Integration Patterns

The integration uses both event-driven asynchronous communication and direct API calls for synchronous operations.

```
┌───────────────────┐                   ┌───────────────────┐
│                   │                   │                   │
│   Order Service   │◀──── Events ─────▶│ Inventory Service │
│                   │                   │                   │
└────────┬──────────┘                   └────────┬──────────┘
         │                                       │
         │                                       │
         └───────── API Calls ─────────────────▶│
                                                 │
                                                 │
         ┌───────── API Calls ◀─────────────────┘
         │
┌────────▼──────────┐
│                   │
│  Message Broker   │
│  (RabbitMQ)       │
│                   │
└───────────────────┘
```

## Event-Driven Integration

### Events Published by Inventory Service

These events inform the Order Service about allocation status changes.

1. **AllocationCreatedEvent**
   - **Purpose**: Notifies that inventory has been successfully allocated for an order item
   - **Consumer Action**: Order Service updates the order item to reflect allocation status
   - **Exchange**: `inventory.events`
   - **Routing Key**: `inventory.allocationcreated.allocation`

   ```typescript
   // Example payload
   {
     "eventId": "e1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
     "eventType": "AllocationCreated",
     "eventVersion": "1.0.0",
     "aggregateId": "alloc_01NXYZ901EFG",
     "aggregateType": "Allocation",
     "timestamp": "2023-05-23T11:30:00Z",
     "metadata": {
       "correlationId": "ord_01OXYZ012HIJ",
       "source": "inventory-service"
     },
     "payload": {
       "allocationId": "alloc_01NXYZ901EFG",
       "orderId": "ord_01OXYZ012HIJ",
       "orderItemId": "item_01PXYZ123KLM",
       "inventoryItemId": "inv_01GXYZ234DEF",
       "sku": "WIDGET-2",
       "productId": "prod_01FXYZ789ABC",
       "warehouseId": "wh_01HXYZ789GHI",
       "quantity": 2,
       "status": "PENDING",
       "expiresAt": "2023-05-24T23:59:59Z",
       "inventoryItemDetails": {
         "previousAvailableQuantity": 70,
         "newAvailableQuantity": 70,
         "previousReservedQuantity": 0,
         "newReservedQuantity": 2
       }
     }
   }
   ```

2. **AllocationConfirmedEvent**
   - **Purpose**: Notifies that a previously created allocation has been confirmed
   - **Consumer Action**: Order Service updates the order item to confirmed allocation status
   - **Exchange**: `inventory.events`
   - **Routing Key**: `inventory.allocationconfirmed.allocation`

3. **AllocationCancelledEvent**
   - **Purpose**: Notifies that an allocation has been cancelled
   - **Consumer Action**: Order Service updates the order item to reflect unavailable inventory
   - **Exchange**: `inventory.events`
   - **Routing Key**: `inventory.allocationcancelled.allocation`

4. **AllocationFulfilledEvent**
   - **Purpose**: Notifies that an allocation has been fulfilled (picked, packed, shipped)
   - **Consumer Action**: Order Service updates the order item to fulfilled status
   - **Exchange**: `inventory.events`
   - **Routing Key**: `inventory.allocationfulfilled.allocation`

5. **InsufficientStockEvent**
   - **Purpose**: Notifies that an allocation cannot be created due to insufficient stock
   - **Consumer Action**: Order Service updates the order item to backorder status
   - **Exchange**: `inventory.notifications`
   - **Routing Key**: `inventory.insufficientstock.inventoryitem`

### Events Consumed by Inventory Service

These events allow the Inventory Service to react to order lifecycle changes.

1. **OrderCreatedEvent**
   - **Purpose**: Triggers the creation of preliminary allocations (if auto-allocation is enabled)
   - **Producer**: Order Service
   - **Exchange**: `order.events`
   - **Routing Key**: `order.ordercreated.order`
   - **Handler**: `OrderCreatedEventHandler`

   ```typescript
   // Implementation of event handler
   @Injectable()
   export class OrderCreatedEventHandler implements IEventHandler<OrderCreatedEvent> {
     constructor(
       private readonly allocationService: IAllocationManagementService,
       private readonly logger: Logger
     ) {}

     async handle(event: OrderCreatedEvent): Promise<void> {
       this.logger.log(`Handling OrderCreatedEvent: ${event.payload.orderId}`);
       
       if (!event.payload.items || event.payload.items.length === 0) {
         return;
       }
       
       // Only process if auto-allocation is enabled
       if (!event.payload.requiresPreAllocation) {
         return;
       }
       
       try {
         // Create allocations for all order items
         const allocations = event.payload.items.map(item => ({
           orderItemId: item.orderItemId,
           inventoryItemId: item.inventoryItemId,
           quantity: item.quantity
         }));
         
         await this.allocationService.createBulkAllocations({
           orderId: event.payload.orderId,
           items: allocations,
           metadata: {
             correlationId: event.eventId,
             source: 'order-event-handler'
           }
         });
         
         this.logger.log(`Created preliminary allocations for order ${event.payload.orderId}`);
       } catch (error) {
         this.logger.error(
           `Failed to create allocations for order ${event.payload.orderId}`,
           error
         );
       }
     }
   }
   ```

2. **OrderConfirmedEvent**
   - **Purpose**: Triggers the confirmation of allocated inventory
   - **Producer**: Order Service
   - **Exchange**: `order.events`
   - **Routing Key**: `order.orderconfirmed.order`
   - **Handler**: `OrderConfirmedEventHandler`

3. **OrderCancelledEvent**
   - **Purpose**: Triggers the cancellation of allocations and release of reserved inventory
   - **Producer**: Order Service
   - **Exchange**: `order.events`
   - **Routing Key**: `order.ordercancelled.order`
   - **Handler**: `OrderCancelledEventHandler`

4. **OrderReturnInitiatedEvent**
   - **Purpose**: Prepares the inventory system for handling returned items
   - **Producer**: Order Service
   - **Exchange**: `order.events`
   - **Routing Key**: `order.orderreturninitiated.order`
   - **Handler**: `OrderReturnInitiatedEventHandler`

## API-Based Integration

### APIs Exposed by Inventory Service

These endpoints allow the Order Service to directly interact with inventory allocations.

1. **Create Allocation**
   - **Endpoint**: `POST /allocations`
   - **Purpose**: Create an inventory allocation for an order item
   - **Request Body**:
     ```json
     {
       "orderId": "ord_01OXYZ012HIJ",
       "orderItemId": "item_01PXYZ123KLM",
       "inventoryItemId": "inv_01GXYZ234DEF",
       "quantity": 2,
       "warehouseId": "wh_01HXYZ789GHI",
       "expiresAt": "2023-05-24T23:59:59Z"
     }
     ```
   - **Response**:
     ```json
     {
       "success": true,
       "data": {
         "id": "alloc_01NXYZ901EFG",
         "orderId": "ord_01OXYZ012HIJ",
         "orderItemId": "item_01PXYZ123KLM",
         "inventoryItemId": "inv_01GXYZ234DEF",
         "warehouseId": "wh_01HXYZ789GHI",
         "quantity": 2,
         "status": "PENDING",
         "expiresAt": "2023-05-24T23:59:59Z",
         "createdAt": "2023-05-23T11:30:00Z",
         "updatedAt": "2023-05-23T11:30:00Z"
       }
     }
     ```

2. **Create Bulk Allocations**
   - **Endpoint**: `POST /allocations/bulk`
   - **Purpose**: Create multiple allocations in a single request

3. **Get Allocations by Order**
   - **Endpoint**: `GET /allocations/by-order/{orderId}`
   - **Purpose**: Retrieve all allocations for a specific order

4. **Confirm Allocation**
   - **Endpoint**: `PUT /allocations/{id}/confirm`
   - **Purpose**: Confirm a pending allocation

5. **Cancel Allocation**
   - **Endpoint**: `PUT /allocations/{id}/cancel`
   - **Purpose**: Cancel an allocation and release inventory

6. **Fulfill Allocation**
   - **Endpoint**: `PUT /allocations/{id}/fulfill`
   - **Purpose**: Mark an allocation as fulfilled

### APIs Consumed by Inventory Service

These endpoints allow the Inventory Service to fetch order information.

1. **Get Order Details**
   - **Endpoint**: `GET /orders/{orderId}`
   - **Purpose**: Retrieve order information for validation and processing
   - **Implementation**:
     ```typescript
     @Injectable()
     export class OrderServiceClient {
       constructor(
         private readonly httpService: HttpService,
         private readonly configService: ConfigService,
         private readonly logger: Logger
       ) {}
       
       async getOrder(orderId: string): Promise<Order> {
         const orderServiceUrl = this.configService.get<string>('integration.orderService.url');
         
         try {
           const response = await this.httpService.axiosRef.get(
             `${orderServiceUrl}/orders/${orderId}`
           );
           
           return response.data.data;
         } catch (error) {
           this.logger.error(`Failed to fetch order ${orderId}`, error);
           throw new OrderServiceIntegrationError(`Failed to fetch order: ${error.message}`);
         }
       }
     }
     ```

2. **Get Order Line Items**
   - **Endpoint**: `GET /orders/{orderId}/items`
   - **Purpose**: Retrieve specific line items for allocation

## Authentication and Authorization

Service-to-service authentication uses JWT tokens with service-specific roles:

1. **Inventory Service → Order Service**
   - Token includes the `inventory-service` role
   - Limited to specific order-related endpoints

2. **Order Service → Inventory Service**
   - Token includes the `order-service` role
   - Access limited to allocation endpoints
   - No access to warehouse or inventory management functions

## Error Handling

### Synchronous Error Handling

For API-based communication, standard error responses are used:

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Not enough inventory available",
    "details": {
      "inventoryItemId": "inv_01GXYZ234DEF",
      "warehouseId": "wh_01HXYZ789GHI",
      "requested": 5,
      "available": 2
    }
  }
}
```

The Order Service implements retry logic with exponential backoff for transient errors.

### Asynchronous Error Handling

For event-driven communication:

1. **Dead Letter Queues**
   - Failed event processing is sent to a dead letter queue
   - Administrative interface allows for manual resolution

2. **Reconciliation Process**
   - Scheduled job compares Order Service and Inventory Service states
   - Resolves inconsistencies through compensation actions

## Resilience Patterns

1. **Circuit Breaker**
   - Prevents cascading failures between services
   - Implemented for both API calls and event consumers

2. **Fallback Mechanisms**
   - Order Service can proceed with "optimistic allocation" if Inventory Service is unavailable
   - Reconciliation processes correct any inconsistencies later

3. **Correlation IDs**
   - All requests and events include correlation IDs
   - Enables end-to-end tracing across services

## Example Code: Order Service Client

```typescript
@Injectable()
export class OrderServiceClient {
  private circuitBreaker: CircuitBreaker;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
    private readonly jwtTokenService: JwtTokenService,
    private readonly logger: Logger
  ) {
    // Initialize circuit breaker
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 3,
      resetTimeout: 30000,
      name: 'orderService'
    });
  }

  async getOrder(orderId: string): Promise<Order> {
    return this.circuitBreaker.execute(async () => {
      const orderServiceUrl = this.configService.get<string>('integration.orderService.url');
      const token = await this.jwtTokenService.generateServiceToken();
      
      try {
        const response = await this.httpService.axiosRef.get(
          `${orderServiceUrl}/orders/${orderId}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        
        return response.data.data;
      } catch (error) {
        if (error.response) {
          if (error.response.status === 404) {
            throw new OrderNotFoundException(orderId);
          } else if (error.response.status >= 500) {
            throw new OrderServiceUnavailableError(`Order service error: ${error.message}`);
          }
        }
        
        this.logger.error(`Failed to fetch order ${orderId}`, error);
        throw new OrderServiceIntegrationError(`Failed to fetch order: ${error.message}`);
      }
    });
  }
}
```

## Monitoring and Observability

1. **Distributed Tracing**
   - Jaeger implementation traces requests across service boundaries
   - Correlation IDs link events and API calls

2. **Health Checks**
   - Inventory Service exposes a health endpoint for the Order Service to check
   - Configuration: `GET /health/integration/order-service`

3. **Integration Metrics**
   - Request counts, latencies, and error rates
   - Event processing times and failure rates
   - Allocation success/failure rates by order