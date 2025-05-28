# Project Setup - Notification Service with Shared Libraries

## 🎯 Objective
Create a NestJS microservice for notification management using enterprise-grade shared libraries.

## 🏗️ Architecture Overview
**Event-Driven Notifications**: React to domain events from other services
**Multi-Channel Support**: Email, SMS, push notifications
**Shared Libraries**: Consistent patterns across all services

---

## 🔧 Create Project with Shared Libraries

### Initialize Project
```bash
mkdir -p services/notification-service && cd services/notification-service
npx @nestjs/cli new notification-service --package-manager pnpm
cd notification-service
```

### Install Shared Libraries FIRST
```bash
# Install our enterprise shared libraries
pnpm add @ecommerce/auth-client-utils
pnpm add @ecommerce/nestjs-core-utils
pnpm add @ecommerce/rabbitmq-event-utils
pnpm add @ecommerce/testing-utils
```

### Install Core Dependencies
```bash
# Core NestJS packages
pnpm add @nestjs/typeorm typeorm pg
pnpm add @nestjs/config @nestjs/microservices
pnpm add class-validator class-transformer

# Notification providers
pnpm add @sendgrid/mail twilio
pnpm add @aws-sdk/client-sns @aws-sdk/client-ses

# Development dependencies  
pnpm add --save-dev @types/pg
pnpm add --save-dev @nestjs/testing jest supertest
```

### App Module with Shared Libraries

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

// Import shared libraries
import { CoreModule } from '@ecommerce/nestjs-core-utils';
import { AuthClientModule } from '@ecommerce/auth-client-utils';
import { EventModule } from '@ecommerce/rabbitmq-event-utils';

import { NotificationModule } from './notification/notification.module';
import { EventHandlerModule } from './events/event-handler.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: `.env.${process.env.NODE_ENV || 'local'}`,
    }),
    
    // Shared enterprise modules
    CoreModule.forRoot({
      service: 'notification-service',
      version: '1.0.0',
      logLevel: 'debug',
    }),
    AuthClientModule.forRoot({
      jwksUri: process.env.AUTH_JWKS_URI,
      audience: process.env.AUTH_AUDIENCE,
      issuer: process.env.AUTH_ISSUER,
    }),
    EventModule.forRoot({
      connectionString: process.env.RABBITMQ_URL,
      serviceName: 'notification-service',
      subscriptions: [
        'user.created',
        'order.created',
        'order.status_changed',
        'payment.completed',
        'payment.failed',
      ],
    }),

    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST,
      port: parseInt(process.env.DB_PORT, 10),
      username: process.env.DB_USERNAME,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME,
      autoLoadEntities: true,
      synchronize: process.env.NODE_ENV === 'development',
    }),

    NotificationModule,
    EventHandlerModule,
  ],
})
export class AppModule {}
```