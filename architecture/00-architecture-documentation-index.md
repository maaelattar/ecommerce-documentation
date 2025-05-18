# Architecture Documentation Index

Date: 2025-05-12  
Status: Maintained

## Introduction

This document serves as an index and navigator for the architectural documentation of the E-commerce Platform. It provides an overview of the documentation structure and helps orient team members and stakeholders to the available architectural resources.

## Documentation Overview

### 1. System Architecture Overview

- **[00-system-architecture-overview.md](./00-system-architecture-overview.md)** - The primary document describing the overall architectural approach and principles.

### 2. Domain Model & Bounded Contexts

- **[01-bounded-contexts-and-domain-model.md](./01-bounded-contexts-and-domain-model.md)** - Defines the core domain model and bounded contexts based on Domain-Driven Design principles.

### 3. Technology Decisions

Documents capturing specific implementation technology choices:

- **[API Gateway Selection (Kong)](./technology-decisions/01-api-gateway-selection.md)** - Detailed reasoning for selecting Kong as our API Gateway.
- **[Identity Provider Selection (Keycloak)](./technology-decisions/02-identity-provider-selection.md)** - Detailed reasoning for selecting Keycloak as our Identity Provider.
- **[Message Broker Selection](./technology-decisions/03-message-broker-selection.md)** - Detailed reasoning for selecting a message broker.
- **[NoSQL Database Selection](./technology-decisions/04-nosql-database-selection.md)** - Detailed reasoning for selecting a NoSQL database.
- **[Relational Database Selection (PostgreSQL)](./technology-decisions/05-relational-database-postgresql.md)** - Detailed reasoning for selecting PostgreSQL as our relational database.
- **[Service Mesh Selection](./technology-decisions/06-service-mesh-selection.md)** - Detailed reasoning for selecting a service mesh.
- **[Caching Implementation Details](./technology-decisions/07-caching-implementation-details.md)** - Detailed reasoning for selecting a caching implementation.
- **[Monitoring and Observability Stack](./technology-decisions/08-monitoring-observability-stack.md)** - Detailed reasoning for selecting a monitoring and observability stack.
- **[Future Off-AWS Migration Considerations](./technology-decisions/09-future-off-aws-migration-considerations.md)** - Detailed reasoning for future off-AWS migration considerations.

### 4. C4 Model Diagrams

The system is documented using the C4 model, with diagrams organized in increasing levels of detail:

#### 4.1. C1 - System Context
- **[c4/c1 (Context)/c1-system-context.md](./diagrams/c4/c1%20(Context)/c1-system-context.md)** - High-level view showing the E-commerce system and its interactions with users and external systems.

#### 4.2. C2 - Container
- **[c4/c2 (Container)/c2-container-diagram.md](./diagrams/c4/c2%20(Container)/c2-container-diagram.md)** - Shows the major containers (applications, data stores) that make up the system.

#### 4.3. C3 - Component
Component-level diagrams for each major service:
- **[c4/c3 (Component)/user-service/c3-component-diagram-user-service.md](./diagrams/c4/c3%20(Component)/user-service/c3-component-diagram-user-service.md)**
- **[c4/c3 (Component)/product-service/...](./diagrams/c4/c3%20(Component)/product-service/)** 
- **[c4/c3 (Component)/order-service/...](./diagrams/c4/c3%20(Component)/order-service/)**
- **[c4/c3 (Component)/payment-service/...](./diagrams/c4/c3%20(Component)/payment-service/)**
- **[c4/c3 (Component)/inventory-service/...](./diagrams/c4/c3%20(Component)/inventory-service/)**
- **[c4/c3 (Component)/search-service/...](./diagrams/c4/c3%20(Component)/search-service/)**
- **[c4/c3 (Component)/notification-service/...](./diagrams/c4/c3%20(Component)/notification-service/)**

#### 4.4. C4 - Sequence Diagrams
Key interaction flows:
- **[c4/c4 (sequence)/user-registration-auth.png](./diagrams/c4/c4%20(sequence)/user-registration-auth.png)** - User registration and authentication flow.
- **[c4/c4 (sequence)/checkout-process.png](./diagrams/c4/c4%20(sequence)/checkout-process.png)** - Customer checkout process.
- **[c4/c4 (sequence)/order-fulfillment.png](./diagrams/c4/c4%20(sequence)/order-fulfillment.png)** - Order fulfillment flow.
- **[c4/c4 (sequence)/inventory-management-flow.png](./diagrams/c4/c4%20(sequence)/inventory-management-flow.png)** - Inventory management flow.
- **[c4/c4 (sequence)/promotional-discount-flow.png](./diagrams/c4/c4%20(sequence)/promotional-discount-flow.png)** - Promotional discount application flow.
- **[c4/c4 (sequence)/return-refund-process.png](./diagrams/c4/c4%20(sequence)/return-refund-process.png)** - Return and refund processing flow.
- **[c4/c4 (sequence)/product-search-simple.png](./diagrams/c4/c4%20(sequence)/product-search-simple.png)** - Product search flow.

### 5. Architecture Decision Records (ADRs)

Significant architecture decisions are documented as ADRs in the `/architecture/adr/` directory:

- **[ADR-001: Adoption of Microservices Architecture](./adr/ADR-001-adoption-of-microservices-architecture.md)**
- **[ADR-002: Adoption of Event-Driven Architecture](./adr/ADR-002-adoption-of-event-driven-architecture.md)**
- **[ADR-003: Node.js/NestJS for Initial Services](./adr/ADR-003-nodejs-nestjs-for-initial-services.md)**
- **[ADR-004: PostgreSQL for Relational Data](./adr/ADR-004-postgresql-for-relational-data.md)**
- **[ADR-005: JWT-based Authentication & Authorization](./adr/ADR-005-jwt-based-authentication-authorization.md)**
- **[ADR-014: API Gateway Strategy](./adr/ADR-014-api-gateway-strategy.md)**
- **[ADR-018: Message Broker Strategy](./adr/ADR-018-message-broker-strategy.md)**
- And [many other ADRs](./adr/)

## How to Navigate This Documentation

1. **New team members** should start with the [System Architecture Overview](./00-system-architecture-overview.md), then review the [C1 System Context Diagram](./diagrams/c4/c1%20(Context)/c1-system-context.md) and the [Bounded Contexts document](./01-bounded-contexts-and-domain-model.md).

2. **Service developers** should focus on the relevant C3 Component diagrams for their service area, and the [ADRs](./adr/) that affect their development practices.

3. **Solution architects** should review all major documents, with special attention to the Bounded Contexts, ADRs, and the interfaces between services shown in sequence diagrams.

4. **DevOps engineers** should prioritize the technology decisions, deployment-related ADRs, and C2 Container diagrams.

## Next Steps in Documentation

1. Development of OpenAPI specifications for core service APIs
2. Integration patterns documentation for cross-service communications
3. Enhanced Component (C3) diagrams for newer services
4. Context Map visualizing the relationships between Bounded Contexts

## Document Maintenance

Architecture documentation is maintained by the Architecture team. Significant updates to architectural decisions should follow the ADR process, and diagram updates should maintain consistency with the C4 model hierarchy.
