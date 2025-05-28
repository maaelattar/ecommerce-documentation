# Project Setup - Updated with Shared Libraries

## 🎯 Objective

Create a NestJS microservice for user management and authentication using enterprise-grade shared libraries for consistency and code reuse.

## 🏗️ Architecture Changes

**❌ Before**: Inline authentication, logging, and event handling  
**✅ After**: Shared library dependencies for enterprise patterns

---

## 🔧 Create Project with Shared Libraries

### Initialize Project
```bash
mkdir -p services/user-service && cd services/user-service
npx @nestjs/cli new user-service --package-manager pnpm
cd user-service
```

### Install Shared Libraries FIRST
```bash
# Install our enterprise shared libraries
pnpm add @ecommerce/nestjs-core-utils
pnpm add @ecommerce/rabbitmq-event-utils
pnpm add @ecommerce/testing-utils

# Note: User service creates auth-client-utils, so it doesn't consume it
```

### Install Core Dependencies
```bash
# Core NestJS packages
pnpm add @nestjs/jwt @nestjs/passport passport passport-jwt
pnpm add class-validator class-transformer @nestjs/typeorm typeorm pg
pnpm add @nestjs/microservices @nestjs/config

# Security and utilities
pnpm add bcrypt uuid jwks-rsa

# Dev dependencies  
pnpm add --save-dev @types/pg @types/bcrypt @types/uuid
pnpm add --save-dev @nestjs/testing jest supertest
```

### Updated App Module with Shared Libraries

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

// Import shared libraries
import { CoreUtilsModule } from '@ecommerce/nestjs-core-utils';
import { RabbitMQEventModule } from '@ecommerce/rabbitmq-event-utils';

// Local modules
import { UsersModule } from './modules/users/users.module';
import { AuthModule } from './modules/auth/auth.module';
import { RolesModule } from './modules/roles/roles.module';

import configuration from './config/configuration';

@Module({
  imports: [
    // Configuration
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
    }),
    
    // Shared Libraries
    CoreUtilsModule.forRoot({
      serviceName: 'user-service',
      logLevel: process.env.LOG_LEVEL || 'info',
    }),
    RabbitMQEventModule.forRoot({
      connectionUrl: process.env.RABBITMQ_URL,
      exchange: 'ecommerce.users',
    }),
    
    // Database
    TypeOrmModule.forRootAsync({
      useFactory: () => ({
        type: 'postgres',
        url: process.env.DATABASE_URL,
        autoLoadEntities: true,
        synchronize: process.env.NODE_ENV !== 'production',
      }),
    }),
    
    // Business modules
    UsersModule,
    AuthModule,
    RolesModule,
  ],
})
export class AppModule {}
```

### Environment Setup
```bash
cat > .env.local << EOF
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/user_service

# JWT Configuration  
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters
JWT_EXPIRES_IN=24h
JWT_ISSUER=ecommerce-user-service
JWT_AUDIENCE=ecommerce-platform

# Event Bus
RABBITMQ_URL=amqp://localhost:5672

# Logging
LOG_LEVEL=info
SERVICE_NAME=user-service
EOF
```

---

## 📋 Quality Standards with Shared Libraries

**Following Enterprise Architecture Standards**:
- ✅ **Shared Libraries**: Code reuse and consistency
- ✅ **Standardized Logging**: Structured logging with correlation IDs
- ✅ **Event Publishing**: Transactional outbox pattern
- ✅ **Configuration Management**: Environment validation
- ✅ **Testing Utilities**: Mocks and test helpers

---

## 🎯 Benefits of This Approach

1. **Code Consistency**: All services use same patterns
2. **Reduced Boilerplate**: Shared utilities eliminate duplication  
3. **Maintainability**: Updates in shared libs benefit all services
4. **Enterprise Patterns**: Production-ready implementations
5. **Testing Excellence**: Standardized test utilities

---

## ✅ Next Step

Continue to **[02-database-models-UPDATED.md](./02-database-models-UPDATED.md)** to see how entities use shared base classes.