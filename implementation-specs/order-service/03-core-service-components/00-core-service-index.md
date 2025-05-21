# Order Service Core Components

This directory contains the core service components for the Order Service. These components form the foundation of the Order Service's business logic and data management capabilities.

## Component Overview

| Component       | Description                                              | File                                               |
| --------------- | -------------------------------------------------------- | -------------------------------------------------- |
| OrderController | REST API controller handling HTTP requests and responses | [01-order-controller.md](./01-order-controller.md) |
| OrderService    | Main business logic component for order management       | [02-order-service.md](./02-order-service.md)       |
| OrderRepository | Data access component for order persistence              | [03-order-repository.md](./03-order-repository.md) |
| OrderMapper     | Transforms data between domain entities and DTOs         | [04-order-mapper.md](./04-order-mapper.md)         |
| OrderValidator  | Validates order data and state transitions               | [05-order-validator.md](./05-order-validator.md)   |

## Component Architecture

The Order Service follows a layered architecture pattern:

1. **Controller Layer**: HTTP request/response handling (OrderController)
2. **Service Layer**: Business logic and orchestration (OrderService)
3. **Repository Layer**: Data access and persistence (OrderRepository)
4. **Mapper Layer**: Data transformation between layers (OrderMapper)
5. **Validation Layer**: Ensuring data integrity and business rules (OrderValidator)

## Component Relationships

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  API Clients    │ HTTP │ OrderController │ DTO  │  OrderService   │
│                 │──────►                 │──────►                 │
│                 │      │                 │      │                 │
└─────────────────┘      └────────┬────────┘      └────┬──────┬────┘
                                  │                     │      │
                                  │                     │      │
                        DTO       │                     │      │ Entity
                                  │                     │      │
                         ┌────────▼────────┐            │      │
                         │                 │    Entity  │      │
                         │   OrderMapper   ◄────────────┘      │
                         │                 │                   │
                         └─────────────────┘                   │
                                                              │
                                                              │
                         ┌─────────────────┐                  │
                         │                 │                  │
                         │ OrderValidator  ◄──────────────────┘
                         │                 │    Entity
                         └────────┬────────┘
                                  │
                                  │ Business Rules
                                  │
                         ┌────────▼────────┐      ┌─────────────────┐
                         │                 │      │                 │
                         │    External     │      │OrderRepository  │
                         │    Services     │      │                 │
                         │                 │      └────────┬────────┘
                         └─────────────────┘               │
                                                          │
                                                          │
                                                 ┌────────▼────────┐
                                                 │                 │
                                                 │    Database     │
                                                 │                 │
                                                 └─────────────────┘
```

## Dependency Flow

The components depend on each other in the following way:

- **OrderController** depends on OrderService and OrderMapper
- **OrderService** depends on OrderRepository, OrderMapper, and OrderValidator
- **OrderValidator** depends on external services (ProductService, UserService)
- **OrderMapper** has minimal dependencies, primarily on configuration
- **OrderRepository** depends only on the database and entity models

## Transaction Management

Transactions flow through the components as follows:

1. The OrderController receives an HTTP request
2. The request is mapped to a DTO using OrderMapper
3. The OrderService processes the business logic
4. The OrderValidator validates the data
5. The OrderRepository persists the changes
6. The OrderService completes the transaction
7. The response is mapped back to a DTO using OrderMapper
8. The OrderController returns the HTTP response

## References

- [Data Model Setup](../02-data-model-setup/00-data-model-index.md)
- [API Endpoints](../04-api-endpoints/00-api-index.md)
- [Event Publishing](../05-event-publishing/00-event-publishing-index.md)
- [Integration Points](../06-integration-points/00-integration-points-index.md)
