# E-commerce Platform Data Model Diagrams

This directory contains Entity-Relationship Diagrams (ERDs) for the e-commerce platform, created using PlantUML. These diagrams provide a visual representation of the data models for different domains within the microservices architecture.

**NEW**: This directory now includes data flow integration documentation that shows how the data models relate to the dynamic flow of information in the system.

## Overview

The data model diagrams are organized by domain contexts to align with the microservices architecture of the platform. Each diagram represents a specific bounded context with its entities and relationships.

## Available Diagrams

### Core Entities Diagram

`core-entities.puml` - A comprehensive overview of all major entities across domains and their relationships. This diagram provides a high-level view of how different domains interact with each other.

### Domain-Specific Diagrams

1. `user-domain.puml` - Detailed model of the User domain, including user accounts, addresses, preferences, sessions, roles, and permissions.

2. `product-domain.puml` - Detailed model of the Product domain, including products, categories, variants, attributes, images, reviews, and related entities.

3. `order-domain.puml` - Detailed model of the Order domain, including carts, orders, payments, shipments, refunds, and returns.

4. `inventory-promotion-domain.puml` - Detailed model of the Inventory and Promotion domains, including inventory management, warehouses, promotions, and coupons.

5. `notification-domain.puml` - Detailed model of the Notification domain, including notifications, templates, preferences, events, and delivery attempts.

### Data Flow Integration

`data-flow-integration.md` - Documentation that explains how the data models relate to the data flow diagrams, providing a comprehensive view of both static data structure and dynamic information flow.

### Legacy Diagram

`erd.puml` - The original ERD template with basic entities (User, Product, Order, OrderItem).

## How to Use

These PlantUML files can be rendered into visual diagrams using:

1. PlantUML extension in various IDEs (VS Code, IntelliJ, etc.)
2. PlantUML server (http://www.plantuml.com/plantuml/)
3. Command-line PlantUML jar

## Diagram Conventions

- Entities are represented with their attributes and data types
- Primary keys are marked with an asterisk (*)
- Relationships show cardinality (one-to-one, one-to-many, many-to-many)
- Domain contexts are grouped using packages
- Consistent naming conventions are used across all diagrams

## Relationship to Microservices

These data models align with the microservices identified in the architecture documentation:

- User Service: Represented in the User domain diagram
- Product Service: Represented in the Product domain diagram
- Order Service: Represented in the Order domain diagram
- Inventory Service: Represented in the Inventory section of the Inventory-Promotion domain diagram
- Payment Service: Represented within the Order domain diagram
- Notification Service: Represented in the Notification domain diagram
- Promotion Service: Represented in the Promotion section of the Inventory-Promotion domain diagram

Each microservice owns and manages its own data, following the principle of decentralized data management as outlined in the architecture overview.

## Data Flow Diagrams

This directory now includes data flow diagrams that complement the data models by showing how information moves through the system:

- `data_flow_diagram.jpg` - Visual representation of data flows between components
- `data_flow_diagram.md` - Documentation explaining the data flow components and processes
- `data_flow_diagram.py` - Python code using the 'diagrams' library to generate the data flow visualization
- `data-flow-integration.md` - Documentation explaining how data models and data flows relate to each other

The data flow diagrams provide insight into how the static data structures represented in the ERDs are used in dynamic processes across the system.