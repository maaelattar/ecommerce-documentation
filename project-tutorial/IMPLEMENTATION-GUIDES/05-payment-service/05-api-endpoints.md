# 05. API Endpoints & Security

## Overview

This section builds secure REST API endpoints with comprehensive security measures including rate limiting, input validation, authentication, and PCI compliance considerations.

## 🎯 Learning Objectives

- Build secure payment API endpoints
- Implement rate limiting and DDoS protection
- Add comprehensive input validation
- Create webhook endpoints with verification
- Implement proper error handling and logging

---

## Step 1: Payment Controller

### 1.1 Payment Endpoints

```typescript
// src/modules/payments/controllers/payment.controller.ts
import {
  Controller,
  Post,
  Get,
  Body,
  Param,
  UseGuards,
  HttpStatus,
  HttpCode,
  ValidationPipe,
  UseInterceptors,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import { JwtAuthGuard } from '../../../auth/guards/jwt-auth.guard';
import { RolesGuard } from '../../../auth/guards/roles.guard';
import { Roles } from '../../../auth/decorators/roles.decorator';
import { CurrentUser } from '../../../auth/decorators/current-user.decorator';
import { PaymentService } from '../services/payment.service';
import { CreatePaymentDto } from '../dto/create-payment.dto';
import { LoggingInterceptor } from '../../../common/interceptors/logging.interceptor';

@ApiTags('payments')
@Controller('payments')
@UseGuards(JwtAuthGuard, RolesGuard)
@UseInterceptors(LoggingInterceptor)
export class PaymentController {
  constructor(private readonly paymentService: PaymentService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @Throttle(10, 60) // 10 requests per minute for payment processing
  @Roles('customer', 'admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Process a payment' })
  @ApiResponse({ status: 201, description: 'Payment processed successfully' })
  @ApiResponse({ status: 400, description: 'Invalid payment data' })
  @ApiResponse({ status: 429, description: 'Rate limit exceeded' })
  async processPayment(
    @Body(ValidationPipe) createPaymentDto: CreatePaymentDto,
    @CurrentUser() user: any,
  ) {
    return this.paymentService.processPayment({
      ...createPaymentDto,
      customerId: user.customerId,
    });
  }

  @Get(':id')
  @Roles('customer', 'admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get payment details' })
  async getPayment(@Param('id') id: string, @CurrentUser() user: any) {
    return this.paymentService.getPayment(id, user.customerId);
  }

  @Post(':id/capture')
  @HttpCode(HttpStatus.OK)
  @Throttle(5, 60)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Capture a payment' })
  async capturePayment(@Param('id') id: string) {
    return this.paymentService.capturePayment(id);
  }
}
```