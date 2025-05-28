# Payment Service - Complete Implementation Guide

## 🎯 Architecture Overview

This Payment Service implementation demonstrates:
- **Shared Library Usage**: Proper integration of `@ecommerce/*` packages
- **PCI Compliance**: Tokenization and secure data handling
- **Financial Integrity**: ACID transactions and audit trails
- **Enterprise Security**: Authentication, authorization, and fraud detection
- **Event-Driven Architecture**: Reliable event publishing with transactional outbox

---

## 🏗️ Core Implementation

### 1. Payment Controller with Shared Auth

```typescript
// src/modules/payments/controllers/payment.controller.ts
import { Controller, Post, Get, Body, Param, UseGuards } from '@nestjs/common';
import { ApiTags, ApiBearerAuth } from '@nestjs/swagger';
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

import { PaymentService } from '../services/payment.service';
import { CreatePaymentDto } from '../dto/create-payment.dto';

@ApiTags('payments')
@Controller('payments')
@UseGuards(JwtAuthGuard, RolesGuard)
export class PaymentController {
  constructor(
    private readonly paymentService: PaymentService,
    private readonly logger: LoggerService,
  ) {}

  @Post()
  @Throttle(10, 60) // 10 payments per minute per user
  @Roles('customer', 'admin')
  @ApiBearerAuth()
  async processPayment(
    @Body() createPaymentDto: CreatePaymentDto,
    @CurrentUser() user: UserContext,
  ) {
    this.logger.info('Processing payment request', {
      userId: user.userId,
      orderId: createPaymentDto.orderId,
      amount: createPaymentDto.amount,
    });

    return this.paymentService.processPayment({
      ...createPaymentDto,
      customerId: user.customerId || user.userId,
    });
  }

  @Get(':id')
  @Roles('customer', 'admin')
  @ApiBearerAuth()
  async getPayment(
    @Param('id') id: string,
    @CurrentUser() user: UserContext,
  ) {
    return this.paymentService.getPaymentForUser(id, user.userId);
  }
}
```