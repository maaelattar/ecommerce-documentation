# Shared Libraries Tutorial

## Overview

This section teaches you how to build and use shared libraries that promote code reuse, consistency, and maintainability across all microservices in the ecommerce platform.

## 🎯 Learning Objectives

- Create reusable TypeScript packages for common functionality
- Implement proper versioning and distribution strategies
- Build authentication, configuration, and event utilities
- Establish testing patterns for shared code
- Maintain architectural consistency across services

## 📦 Shared Libraries

### [01. Auth Client Utils](./01-auth-client-utils/)
**`@ecommerce/auth-client-utils`**
- JWT validation modules and guards
- `@CurrentUser()` decorator for user context
- RBAC utilities and permission checks
- Used by: All services requiring authentication

### [02. NestJS Core Utils](./02-nestjs-core-utils/)
**`@ecommerce/nestjs-core-utils`**
- Standardized logging configuration
- Error handling and response formatting
- Configuration management utilities
- Health check modules
- Used by: All services

### [03. RabbitMQ Event Utils](./03-rabbitmq-event-utils/)
**`@ecommerce/rabbitmq-event-utils`**
- Standard message envelope patterns
- Event producer and consumer utilities
- RabbitMQ connection management
- Used by: All event-driven services

### [04. Testing Utils](./04-testing-utils/)
**`@ecommerce/testing-utils`**
- Mock implementations for services
- Common test setup and teardown utilities
- Database testing helpers
- Used by: All services for testing

## 🔄 Development Workflow

1. **Create Library**: Build shared functionality in isolation
2. **Version & Publish**: Use semantic versioning for releases
3. **Consume in Services**: Import and use in microservices
4. **Update & Maintain**: Centralized updates benefit all services

## 🎓 Key Principles

- **Single Responsibility**: Each library has a focused purpose
- **Loose Coupling**: Libraries are independent and composable
- **Backward Compatibility**: Follow semantic versioning strictly
- **Comprehensive Testing**: High test coverage for shared code
- **Clear Documentation**: Well-documented APIs and usage examples

Ready to build enterprise-grade shared libraries? Start with [Auth Client Utils](./01-auth-client-utils/)!