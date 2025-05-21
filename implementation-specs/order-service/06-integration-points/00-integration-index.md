# Order Service Integration Points

## Introduction

This document provides an overview of all integration points between the Order Service and other services in the e-commerce platform. As a central service in the platform, the Order Service interacts with multiple services to fulfill its responsibilities. These integration points follow the principles established in [ADR-001-microservice-architecture-principles](../../../architecture/adr/ADR-001-microservice-architecture-principles.md).

## Integration Overview

The Order Service has both inbound and outbound integration points with other services:

```
                         ┌───────────────────┐
                         │                   │
       ┌─────────────────┤  Product Service  │
       │                 │                   │
       │                 └───────────────────┘
       │
       │                 ┌───────────────────┐
       │                 │                   │
       ├─────────────────┤  Inventory Service│
       │                 │                   │
       │                 └───────────────────┘
       │
       │                 ┌───────────────────┐
       │                 │                   │
       ├─────────────────┤  Payment Service  │
       │                 │                   │
       │                 └───────────────────┘
       ▼
┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │
│   Order Service   │────>│    User Service   │
│                   │     │                   │
└───────────────────┘     └───────────────────┘
       │
       │                 ┌───────────────────┐
       │                 │                   │
       ├────────────────>│ Notification Svc  │
       │                 │                   │
       │                 └───────────────────┘
       │
       │                 ┌───────────────────┐
       │                 │                   │
       └────────────────>│  Analytics Service│
                         │                   │
                         └───────────────────┘
```

## Integration Types

The Order Service uses the following integration types:

| Integration Type       | Usage                                    | Examples                                    |
| ---------------------- | ---------------------------------------- | ------------------------------------------- |
| REST API (Synchronous) | Direct service-to-service communication  | Get product details, Check inventory        |
| Event-Driven (Async)   | Loosely-coupled communication            | Order status changes, Payment notifications |
| Shared Database        | None (each service has its own database) | -                                           |

## Service Dependencies

### Outbound Dependencies (Order Service calls these services)

| Service              | Integration Type | Purpose                       | Resilience Strategy       |
| -------------------- | ---------------- | ----------------------------- | ------------------------- |
| User Service         | REST API         | Validate user information     | Circuit breaker, fallback |
| Product Service      | REST API         | Get product information       | Circuit breaker, cache    |
| Inventory Service    | REST API         | Check and reserve inventory   | Circuit breaker, retry    |
| Payment Service      | REST API         | Process payments              | Circuit breaker, retry    |
| Notification Service | Event            | Send order notifications      | Guaranteed delivery       |
| Analytics Service    | Event            | Send order data for analytics | Guaranteed delivery       |

### Inbound Dependencies (Services calling Order Service)

| Service           | Integration Type | Purpose                         | Authentication          |
| ----------------- | ---------------- | ------------------------------- | ----------------------- |
| Admin Service     | REST API         | Administrative order management | Service-to-service auth |
| User Service      | REST API         | Get user order history          | Service-to-service auth |
| Analytics Service | REST API         | Get order statistics            | Service-to-service auth |

## Detailed Integration Specifications

Each integration is described in detail in its own specification document:

- [01-user-service-integration.md](./01-user-service-integration.md): User Service integration
- [02-product-service-integration.md](./02-product-service-integration.md): Product Service integration
- [03-inventory-service-integration.md](./03-inventory-service-integration.md): Inventory Service integration
- [04-payment-service-integration.md](./04-payment-service-integration.md): Payment Service integration
- [05-notification-service-integration.md](./05-notification-service-integration.md): Notification Service integration
- [06-analytics-service-integration.md](./06-analytics-service-integration.md): Analytics Service integration
- [07-admin-service-integration.md](./07-admin-service-integration.md): Admin Service integration

## Resilience Patterns

The Order Service implements the following resilience patterns for service integrations:

### Circuit Breaker Pattern

```typescript
// Circuit Breaker implementation using Hystrix
import { CircuitBreaker } from "opossum";

export class ProductServiceClient {
  private circuitBreaker: CircuitBreaker;

  constructor(private readonly httpClient: HttpClient) {
    // Circuit breaker configuration
    const options = {
      timeout: 3000, // 3 seconds
      errorThresholdPercentage: 50,
      resetTimeout: 30000, // 30 seconds
    };

    this.circuitBreaker = new CircuitBreaker(
      this.getProduct.bind(this),
      options
    );

    // Circuit state change listeners for logging/metrics
    this.circuitBreaker.on("open", () => {
      console.warn("Circuit breaker to Product Service opened");
      // Emit metric for monitoring
    });

    this.circuitBreaker.on("close", () => {
      console.info("Circuit breaker to Product Service closed");
      // Emit metric for monitoring
    });
  }

  async getProduct(productId: string): Promise<Product> {
    try {
      const response = await this.httpClient.get(`/products/${productId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching product ${productId}:`, error);
      throw error;
    }
  }

  async getProductWithCircuitBreaker(productId: string): Promise<Product> {
    return this.circuitBreaker.fire(productId);
  }

  // Additional methods...
}
```

### Retry Pattern

```typescript
// Retry logic with exponential backoff
import { retry } from "ts-retry-promise";

export class InventoryServiceClient {
  constructor(private readonly httpClient: HttpClient) {}

  async reserveInventory(
    orderId: string,
    items: OrderItem[]
  ): Promise<boolean> {
    // Retry configuration
    const retryOptions = {
      retries: 3,
      delay: 300,
      backoff: "exponential",
      timeout: 5000,
      logger: (msg: string) => console.warn(msg),
    };

    return retry(async () => {
      try {
        const response = await this.httpClient.post("/inventory/reserve", {
          orderId,
          items: items.map((item) => ({
            productId: item.productId,
            quantity: item.quantity,
          })),
        });

        return response.data.success;
      } catch (error) {
        if (error.response && error.response.status >= 500) {
          // Retry on server errors
          throw error;
        } else if (
          error.code === "ECONNABORTED" ||
          error.code === "ETIMEDOUT"
        ) {
          // Retry on timeouts
          throw error;
        } else {
          // Don't retry on client errors or other issues
          throw new NonRetryableError(error);
        }
      }
    }, retryOptions);
  }

  // Additional methods...
}
```

### Caching Pattern

```typescript
// Caching implementation
import { CacheManager } from "../common/cache/cache-manager";

export class ProductServiceClient {
  constructor(
    private readonly httpClient: HttpClient,
    private readonly cacheManager: CacheManager
  ) {}

  async getProduct(productId: string): Promise<Product> {
    const cacheKey = `product:${productId}`;

    // Try to get from cache first
    const cachedProduct = await this.cacheManager.get<Product>(cacheKey);
    if (cachedProduct) {
      return cachedProduct;
    }

    // If not in cache, fetch from service
    try {
      const response = await this.httpClient.get(`/products/${productId}`);
      const product = response.data;

      // Store in cache with TTL
      await this.cacheManager.set(cacheKey, product, 300); // 5 minutes TTL

      return product;
    } catch (error) {
      console.error(`Error fetching product ${productId}:`, error);
      throw error;
    }
  }

  // Additional methods...
}
```

## Service-to-Service Authentication

The Order Service uses the following approach for service-to-service authentication:

1. **JWT-based Authentication**: Service-specific JWT tokens with limited scopes
2. **Short-lived Tokens**: Tokens are valid for a short period (15 minutes)
3. **Mutual TLS (mTLS)**: For secure service-to-service communication
4. **IP Whitelisting**: Additional layer of security for service communications

Example Authentication Header:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXJ2aWNlIjoib3JkZXItc2VydmljZSIsInNjb3BlIjpbInByb2R1Y3Q6cmVhZCJdLCJpYXQiOjE2MDU5ODI1NjEsImV4cCI6MTYwNTk4MzQ2MSwiaXNzIjoiYXV0aC1zZXJ2aWNlIn0.Hk5b5...
```

## Integration Testing

The Order Service implements the following integration testing approach:

1. **Contract Testing**: Using Pact.js to define and verify service contracts
2. **Mock Services**: Mock dependencies for isolated testing
3. **Integration Test Environment**: Dedicated environment with actual services
4. **Fault Injection**: Testing resilience patterns by simulating failures

## Monitoring Integration Health

The Order Service monitors the health of its integrations through:

1. **Health Checks**: Regular checks of dependent services
2. **Latency Metrics**: Tracking response times for service calls
3. **Error Rates**: Monitoring failure rates for dependencies
4. **Circuit Breaker Status**: Tracking open/closed states of circuit breakers
5. **Distributed Tracing**: End-to-end visibility of requests across services

## References

- [ADR-001-microservice-architecture-principles](../../../architecture/adr/ADR-001-microservice-architecture-principles.md)
- [ADR-007-event-driven-architecture](../../../architecture/adr/ADR-007-event-driven-architecture.md)
- [Order Service Data Model](../02-data-model-setup/00-data-model-index.md)
- [Order Service Components](../03-core-service-components/00-service-components-index.md)
- [Order Service API Endpoints](../04-api-endpoints/00-api-index.md)
- [Order Service Event Publishing](../05-event-publishing/00-events-index.md)
- [Monitoring and Observability Specification](../../infrastructure/05-monitoring-observability-specification.md)
