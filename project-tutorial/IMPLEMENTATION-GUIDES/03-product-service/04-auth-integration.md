# Tutorial 4: Authentication Integration - Updated with Shared Libraries

## 🎯 Objective
Integrate standardized authentication using `@ecommerce/auth-client-utils` for JWT validation, RBAC, and user context management.

## 📚 Architecture Changes

**❌ Before**: Custom JWT implementation in each service  
**✅ After**: Shared authentication utilities with consistent patterns

---

## Step 1: Install ALL Shared Libraries

```bash
# Install all shared libraries for consistency
pnpm add @ecommerce/auth-client-utils
pnpm add @ecommerce/nestjs-core-utils
pnpm add @ecommerce/rabbitmq-event-utils
pnpm add @ecommerce/testing-utils
```

## Step 2: Updated App Module

```typescript
// src/app.module.ts (updated)
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';

// Shared Libraries
import { AuthClientModule } from '@ecommerce/auth-client-utils';
import { CoreUtilsModule } from '@ecommerce/nestjs-core-utils';
import { RabbitMQEventModule } from '@ecommerce/rabbitmq-event-utils';

// Local modules
import { ProductsModule } from './modules/products/products.module';
import { CategoriesModule } from './modules/categories/categories.module';

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
      serviceName: 'product-service',
      logLevel: process.env.LOG_LEVEL || 'info',
    }),
    RabbitMQEventModule.forRoot({
      connectionUrl: process.env.RABBITMQ_URL,
      exchange: 'ecommerce.products',
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
    ProductsModule,
    CategoriesModule,
  ],
})
export class AppModule {}
```

## Step 3: Enhanced Product Controller with Shared Auth

```typescript
// src/modules/products/controllers/product.controller.ts
import { 
  Controller, Get, Post, Body, Patch, Param, Delete, 
  UseGuards, Query 
} from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation } from '@nestjs/swagger';

// Shared library imports
import { 
  JwtAuthGuard, 
  RolesGuard, 
  Roles, 
  CurrentUser, 
  UserContext,
  Public 
} from '@ecommerce/auth-client-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { ProductService } from '../services/product.service';
import { CreateProductDto } from '../dto/create-product.dto';
import { UpdateProductDto } from '../dto/update-product.dto';

@ApiTags('products')
@Controller('products')
@UseGuards(JwtAuthGuard, RolesGuard)
export class ProductController {
  constructor(
    private readonly productService: ProductService,
    private readonly logger: LoggerService,
  ) {}

  @Post()
  @Roles('admin', 'manager')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create a new product' })
  async create(
    @Body() createProductDto: CreateProductDto,
    @CurrentUser() user: UserContext,
  ) {
    this.logger.info('Creating product', {
      userId: user.userId,
      productName: createProductDto.name,
    });

    return this.productService.create(createProductDto, user.userId);
  }

  @Get()
  @Public() // Public endpoint for browsing products
  @ApiOperation({ summary: 'Get all products' })
  async findAll(@Query() query: any) {
    return this.productService.findAll(query);
  }

  @Get(':id')
  @Public() // Public endpoint for product details
  @ApiOperation({ summary: 'Get product by ID' })
  async findOne(@Param('id') id: string) {
    return this.productService.findOne(id);
  }

  @Patch(':id')
  @Roles('admin', 'manager')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update product' })
  async update(
    @Param('id') id: string,
    @Body() updateProductDto: UpdateProductDto,
    @CurrentUser() user: UserContext,
  ) {
    this.logger.info('Updating product', {
      userId: user.userId,
      productId: id,
    });

    return this.productService.update(id, updateProductDto, user.userId);
  }

  @Delete(':id')
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete product' })
  async remove(
    @Param('id') id: string,
    @CurrentUser() user: UserContext,
  ) {
    this.logger.info('Deleting product', {
      userId: user.userId,
      productId: id,
    });

    return this.productService.remove(id, user.userId);
  }
}
```

---

## 🎯 Benefits of Shared Auth Integration

1. **Consistent Authentication**: Same JWT validation across all services
2. **User Context**: Easy access to user info via `@CurrentUser()` decorator
3. **RBAC Support**: Standardized role and permission checking
4. **Security Headers**: Automatic security middleware from shared utilities
5. **Audit Logging**: Integrated logging with user context

---

## ✅ Next Step
Continue with **[05-api-implementation-UPDATED.md](./05-api-implementation-UPDATED.md)** for complete API with shared utilities.