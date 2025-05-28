# 01. Project Setup - Updated with Shared Libraries

## 🎯 Objective

Set up the Order Service with proper shared library integration and hybrid database architecture (PostgreSQL + DynamoDB) for enterprise-grade order management.

## 📚 Architecture Changes

**❌ Before**: Custom implementations for auth, logging, and events  
**✅ After**: Shared library dependencies with consistent patterns

---

## Step 1: Initialize Order Service with Shared Libraries

### 1.1 Create Project Structure

```bash
# Navigate to services directory
cd ecommerce-services

# Create order service
nest new order-service
cd order-service

# Install shared libraries FIRST
npm install @ecommerce/auth-client-utils
npm install @ecommerce/nestjs-core-utils
npm install @ecommerce/rabbitmq-event-utils
npm install @ecommerce/testing-utils

# Install core dependencies
npm install @nestjs/typeorm @nestjs/config
npm install @nestjs/swagger @nestjs/throttler
npm install typeorm pg aws-sdk
npm install class-validator class-transformer

# Install dev dependencies
npm install -D @types/node @types/pg
npm install -D jest @types/jest ts-jest supertest @types/supertest
```

### 1.2 App Module with Shared Libraries

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

// Shared Libraries
import { AuthClientModule } from '@ecommerce/auth-client-utils';
import { CoreUtilsModule } from '@ecommerce/nestjs-core-utils';
import { RabbitMQEventModule } from '@ecommerce/rabbitmq-event-utils';

// Local modules
import { OrdersModule } from './modules/orders/orders.module';
import { OrderItemsModule } from './modules/order-items/order-items.module';
import { AddressesModule } from './modules/addresses/addresses.module';
import { DynamoModule } from './modules/dynamo/dynamo.module';

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
      serviceName: 'order-service',
      logLevel: process.env.LOG_LEVEL || 'info',
    }),
    RabbitMQEventModule.forRoot({
      connectionUrl: process.env.RABBITMQ_URL,
      exchange: 'ecommerce.orders',
    }),
    
    // PostgreSQL Database
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
    OrdersModule,
    OrderItemsModule,
    AddressesModule,
    DynamoModule, // For high-throughput order status tracking
  ],
})
export class AppModule {}
```

### 1.3 Environment Configuration

```typescript
// src/config/configuration.ts
export default () => ({
  app: {
    name: 'order-service',
    port: parseInt(process.env.PORT, 10) || 3004,
    environment: process.env.NODE_ENV || 'development',
  },
  
  database: {
    postgres: {
      host: process.env.DATABASE_HOST || 'localhost',
      port: parseInt(process.env.DATABASE_PORT, 10) || 5432,
      username: process.env.DATABASE_USERNAME || 'postgres',
      password: process.env.DATABASE_PASSWORD || 'password',
      database: process.env.DATABASE_NAME || 'order_service',
    },
    dynamodb: {
      region: process.env.AWS_REGION || 'us-east-1',
      endpoint: process.env.DYNAMODB_ENDPOINT || 'http://localhost:4566',
      tableName: process.env.DYNAMODB_TABLE_NAME || 'order-status-tracking',
    },
  },
  
  services: {
    userService: process.env.USER_SERVICE_URL || 'http://localhost:3001',
    productService: process.env.PRODUCT_SERVICE_URL || 'http://localhost:3002',
    paymentService: process.env.PAYMENT_SERVICE_URL || 'http://localhost:3005',
  },
});
```

---

## Step 2: Order Controller with Shared Auth

```typescript
// src/modules/orders/controllers/order.controller.ts
import { 
  Controller, Get, Post, Body, Patch, Param, 
  UseGuards, Query 
} from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';

// Shared library imports
import { 
  JwtAuthGuard, 
  RolesGuard, 
  Roles, 
  CurrentUser, 
  UserContext 
} from '@ecommerce/auth-client-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { OrderService } from '../services/order.service';
import { CreateOrderDto } from '../dto/create-order.dto';

@ApiTags('orders')
@Controller('orders')
@UseGuards(JwtAuthGuard, RolesGuard)
export class OrderController {
  constructor(
    private readonly orderService: OrderService,
    private readonly logger: LoggerService,
  ) {}

  @Post()
  @Throttle(5, 60) // 5 orders per minute per user
  @Roles('customer', 'admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create a new order' })
  async create(
    @Body() createOrderDto: CreateOrderDto,
    @CurrentUser() user: UserContext,
  ) {
    this.logger.info('Creating order', {
      userId: user.userId,
      customerId: user.customerId,
      itemCount: createOrderDto.items?.length,
    });

    return this.orderService.create({
      ...createOrderDto,
      customerId: user.customerId || user.userId,
    });
  }

  @Get()
  @Roles('customer', 'admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get user orders' })
  async findUserOrders(
    @CurrentUser() user: UserContext,
    @Query() query: any,
  ) {
    return this.orderService.findByCustomer(
      user.customerId || user.userId,
      query,
    );
  }

  @Get(':id')
  @Roles('customer', 'admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get order by ID' })
  async findOne(
    @Param('id') id: string,
    @CurrentUser() user: UserContext,
  ) {
    return this.orderService.findOneForUser(id, user.userId);
  }

  @Patch(':id/cancel')
  @Roles('customer', 'admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Cancel order' })
  async cancel(
    @Param('id') id: string,
    @CurrentUser() user: UserContext,
  ) {
    this.logger.info('Cancelling order', {
      userId: user.userId,
      orderId: id,
    });

    return this.orderService.cancel(id, user.userId);
  }
}
```

---

## 🎯 Benefits of Shared Library Integration

1. **Consistent Authentication**: Same patterns across all services
2. **Standardized Logging**: Structured logs with correlation IDs
3. **Reliable Events**: Transactional outbox for order events
4. **Testing Utilities**: Shared mocks and test helpers
5. **Configuration Management**: Environment validation and defaults

---

## ✅ Next Step

Continue with **[02-core-data-models-UPDATED.md](./02-core-data-models-UPDATED.md)** to see hybrid database entity design.