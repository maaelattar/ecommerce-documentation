# 03. Core Payment Processing

## Overview

This section implements the heart of the Payment Service - the core payment processing logic with transaction management, ACID properties, and financial integrity. We'll build a robust system that handles payments, captures, voids, and maintains consistency.

## 🎯 Learning Objectives

- Implement payment processing with ACID transactions
- Build payment intent and capture workflows
- Create transaction state management
- Add idempotency for reliable operations
- Implement proper error handling and rollbacks

---

## Step 1: Payment Processing Service

### 1.1 Payment Service Interface

```typescript
// src/modules/payments/interfaces/payment.interface.ts
export interface CreatePaymentRequest {
  orderId: string;
  customerId: string;
  amount: number;
  currency: string;
  paymentMethodToken: string;
  description?: string;
  metadata?: Record<string, any>;
  captureMethod?: 'automatic' | 'manual';
}

export interface PaymentResult {
  paymentId: string;
  status: PaymentStatus;
  gatewayTransactionId?: string;
  amount: number;
  currency: string;
  fees?: number;
  error?: string;
}
```

### 1.2 Core Payment Service

```typescript
// src/modules/payments/services/payment.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, EntityManager } from 'typeorm';
import { Payment } from '../entities/payment.entity';
import { Transaction } from '../entities/transaction.entity';
import { PaymentGatewayService } from '../../gateways/payment-gateway.service';
import { EventPublisherService } from '../../events/event-publisher.service';

@Injectable()
export class PaymentService {
  private readonly logger = new Logger(PaymentService.name);

  constructor(
    @InjectRepository(Payment)
    private paymentRepository: Repository<Payment>,
    @InjectRepository(Transaction)
    private transactionRepository: Repository<Transaction>,
    private paymentGateway: PaymentGatewayService,
    private eventPublisher: EventPublisherService,
  ) {}

  async processPayment(
    request: CreatePaymentRequest,
  ): Promise<PaymentResult> {
    return this.paymentRepository.manager.transaction(
      async (manager: EntityManager) => {
        try {
          // Create payment record
          const payment = await this.createPaymentRecord(request, manager);
          
          // Process with gateway
          const gatewayResult = await this.paymentGateway.processPayment({
            amount: request.amount,
            currency: request.currency,
            paymentMethodToken: request.paymentMethodToken,
            orderId: request.orderId,
            customerId: request.customerId,
          });

          // Update payment with gateway response
          await this.updatePaymentStatus(
            payment.id,
            gatewayResult.status,
            gatewayResult.gatewayTransactionId,
            manager,
          );

          // Create transaction record
          await this.createTransactionRecord(
            payment.id,
            gatewayResult,
            manager,
          );

          // Publish payment event
          await this.eventPublisher.publishPaymentEvent(
            'payment.processed',
            {
              paymentId: payment.id,
              orderId: request.orderId,
              status: gatewayResult.status,
              amount: request.amount,
              currency: request.currency,
            },
          );

          return {
            paymentId: payment.id,
            status: gatewayResult.status,
            gatewayTransactionId: gatewayResult.gatewayTransactionId,
            amount: request.amount,
            currency: request.currency,
            fees: gatewayResult.fees,
          };
        } catch (error) {
          this.logger.error('Payment processing failed', error);
          throw error;
        }
      },
    );
  }
}
```