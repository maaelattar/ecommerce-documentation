# 01. Project Setup & Security Architecture

## Overview

This tutorial establishes a secure foundation for the Payment Service using shared libraries and enterprise-grade security patterns. We'll build a hardened NestJS application that leverages our standardized utilities for authentication, logging, and event handling.

## 🎯 Learning Objectives

- Set up Payment Service with shared library dependencies
- Configure enterprise-grade security for financial transactions
- Implement PCI compliance patterns and tokenization
- Establish comprehensive audit logging
- Add rate limiting and fraud protection foundations

---

## Step 1: Initialize Project with Shared Libraries

### 1.1 Create Project Structure

```bash
# Navigate to services directory
cd ecommerce-services

# Create payment service
nest new payment-service
cd payment-service

# Install shared libraries FIRST
npm install @ecommerce/auth-client-utils
npm install @ecommerce/nestjs-core-utils
npm install @ecommerce/rabbitmq-event-utils
npm install @ecommerce/testing-utils
```### 1.2 Install Additional Dependencies

```bash
# Install core dependencies
npm install @nestjs/typeorm @nestjs/config @nestjs/jwt
npm install @nestjs/swagger @nestjs/throttler
npm install typeorm pg bcryptjs stripe
npm install class-validator class-transformer helmet

# Install security dependencies
npm install crypto-js rate-limiter-flexible
npm install express-rate-limit express-slow-down

# Install dev dependencies
npm install -D @types/node @types/pg @types/bcryptjs
npm install -D jest @types/jest ts-jest supertest @types/supertest
```

### 1.3 App Module with Shared Libraries

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

// Import shared libraries
import { AuthClientModule } from '@ecommerce/auth-client-utils';
import { CoreUtilsModule } from '@ecommerce/nestjs-core-utils';
import { RabbitMQEventModule } from '@ecommerce/rabbitmq-event-utils';

// Local modules
import { PaymentsModule } from './modules/payments/payments.module';
import { TransactionsModule } from './modules/transactions/transactions.module';
import { RefundsModule } from './modules/refunds/refunds.module';
import { WebhooksModule } from './modules/webhooks/webhooks.module';
import { StripeGatewayModule } from './gateways/stripe/stripe-gateway.module';

import configuration from './config/configuration';

@Module({
  imports: [
    // Configuration
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
    }),
    
    // Shared Libraries
    AuthClientModule.forRoot({
      jwtSecret: process.env.JWT_SECRET,
      issuer: 'ecommerce-user-service',
      audience: 'ecommerce-platform',
    }),
    CoreUtilsModule.forRoot({
      serviceName: 'payment-service',
      logLevel: process.env.LOG_LEVEL || 'info',
    }),
    RabbitMQEventModule.forRoot({
      connectionUrl: process.env.RABBITMQ_URL,
      exchange: 'ecommerce.payments',
    }),
    
    // Database
    TypeOrmModule.forRootAsync({
      useFactory: () => ({
        type: 'postgres',
        host: process.env.DATABASE_HOST,
        port: parseInt(process.env.DATABASE_PORT, 10),
        username: process.env.DATABASE_USERNAME,
        password: process.env.DATABASE_PASSWORD,
        database: process.env.DATABASE_NAME,
        autoLoadEntities: true,
        synchronize: process.env.NODE_ENV !== 'production',
      }),
    }),
    
    // Business modules
    PaymentsModule,
    TransactionsModule,
    RefundsModule,
    WebhooksModule,
    StripeGatewayModule,
  ],
})
export class AppModule {}
```

---

## Step 2: Security Configuration

### 2.1 Environment Configuration

```typescript
// src/config/configuration.ts
export default () => ({
  app: {
    name: 'payment-service',
    port: parseInt(process.env.PORT, 10) || 3005,
    environment: process.env.NODE_ENV || 'development',
  },
  
  security: {
    rateLimit: {
      ttl: parseInt(process.env.RATE_LIMIT_TTL, 10) || 60,
      limit: parseInt(process.env.RATE_LIMIT_MAX, 10) || 100,
      paymentLimit: parseInt(process.env.PAYMENT_RATE_LIMIT, 10) || 10,
    },
  },
  
  payments: {
    stripe: {
      secretKey: process.env.STRIPE_SECRET_KEY,
      webhookSecret: process.env.STRIPE_WEBHOOK_SECRET,
      apiVersion: '2023-10-16' as const,
    },
    currency: process.env.DEFAULT_CURRENCY || 'USD',
    minimumAmount: parseInt(process.env.MINIMUM_PAYMENT_AMOUNT, 10) || 50,
    maximumAmount: parseInt(process.env.MAXIMUM_PAYMENT_AMOUNT, 10) || 1000000,
  },
});
```