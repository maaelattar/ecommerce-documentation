# API Endpoints - Order Service with Shared Libraries

## 🎯 Objective
Build REST API endpoints using shared authentication and validation utilities.

## 🔐 Order Controller Implementation

```typescript
// src/order/order.controller.ts
import { Controller, Get, Post, Put, Param, Body, UseGuards, Req } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';

// Import shared utilities
import { JwtAuthGuard } from '@ecommerce/auth-client-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { OrderService } from './order.service';
import { CreateOrderDto } from './dto/create-order.dto';
import { UpdateOrderStatusDto } from './dto/update-order-status.dto';

@ApiTags('orders')
@Controller('orders')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class OrderController {
  constructor(
    private readonly orderService: OrderService,
    private readonly logger: LoggerService,
  ) {}

  @Post()
  @ApiOperation({ summary: 'Create new order' })
  async createOrder(
    @Body() createOrderDto: CreateOrderDto,
    @Req() req: any,
  ) {
    const customerId = req.user.sub;
    
    this.logger.log('Creating order', 'OrderController', {
      customerId,
      itemCount: createOrderDto.items.length,
    });

    return await this.orderService.createOrder(createOrderDto, customerId);
  }

  @Get()
  @ApiOperation({ summary: 'Get customer orders' })
  async getCustomerOrders(@Req() req: any) {
    const customerId = req.user.sub;
    return await this.orderService.getCustomerOrders(customerId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get order by ID' })
  async getOrder(@Param('id') id: string, @Req() req: any) {
    const customerId = req.user.sub;
    return await this.orderService.getOrderById(id, customerId);
  }

  @Put(':id/status')
  @ApiOperation({ summary: 'Update order status' })
  async updateOrderStatus(
    @Param('id') id: string,
    @Body() updateStatusDto: UpdateOrderStatusDto,
    @Req() req: any,
  ) {
    const customerId = req.user.sub;
    return await this.orderService.updateOrderStatus(id, updateStatusDto.status, customerId);
  }
}
```