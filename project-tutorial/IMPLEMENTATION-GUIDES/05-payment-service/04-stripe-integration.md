# 04. Stripe Integration & Gateway Abstraction

## Overview

This section implements secure Stripe integration with proper webhook handling, 3D Secure compliance, and a flexible gateway abstraction layer. We'll build patterns that support multiple payment gateways while maintaining PCI compliance.

## 🎯 Learning Objectives

- Design payment gateway abstraction layer
- Implement secure Stripe SDK integration
- Handle webhooks with proper verification
- Add 3D Secure (SCA) compliance
- Create payment intent management

---

## Step 1: Payment Gateway Abstraction

### 1.1 Gateway Interface

```typescript
// src/gateways/interfaces/payment-gateway.interface.ts
export interface PaymentGatewayInterface {
  processPayment(request: ProcessPaymentRequest): Promise<PaymentGatewayResult>;
  capturePayment(paymentIntentId: string): Promise<PaymentGatewayResult>;
  refundPayment(chargeId: string, amount?: number): Promise<RefundResult>;
  createCustomer(customerData: CreateCustomerRequest): Promise<CustomerResult>;
  savePaymentMethod(customerId: string, paymentMethodToken: string): Promise<PaymentMethodResult>;
}

export interface ProcessPaymentRequest {
  amount: number;
  currency: string;
  paymentMethodToken: string;
  customerId?: string;
  orderId: string;
  captureMethod?: 'automatic' | 'manual';
  confirmationMethod?: 'automatic' | 'manual';
}

export interface PaymentGatewayResult {
  success: boolean;
  gatewayTransactionId: string;
  status: PaymentStatus;
  amount: number;
  currency: string;
  fees?: number;
  clientSecret?: string;
  requiresAction?: boolean;
  nextAction?: any;
  error?: string;
}
```

### 1.2 Stripe Gateway Implementation

```typescript
// src/gateways/stripe/stripe-gateway.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import Stripe from 'stripe';
import { PaymentGatewayInterface } from '../interfaces/payment-gateway.interface';

@Injectable()
export class StripeGatewayService implements PaymentGatewayInterface {
  private readonly logger = new Logger(StripeGatewayService.name);
  private readonly stripe: Stripe;

  constructor(private configService: ConfigService) {
    this.stripe = new Stripe(
      this.configService.get<string>('payments.stripe.secretKey'),
      {
        apiVersion: this.configService.get('payments.stripe.apiVersion'),
        typescript: true,
      },
    );
  }

  async processPayment(
    request: ProcessPaymentRequest,
  ): Promise<PaymentGatewayResult> {
    try {
      const paymentIntent = await this.stripe.paymentIntents.create({
        amount: request.amount,
        currency: request.currency,
        payment_method: request.paymentMethodToken,
        customer: request.customerId,
        confirmation_method: request.confirmationMethod || 'automatic',
        capture_method: request.captureMethod || 'automatic',
        confirm: true,
        metadata: {
          orderId: request.orderId,
        },
        return_url: this.configService.get('app.baseUrl') + '/payment/return',
      });

      return this.mapStripePaymentIntent(paymentIntent);
    } catch (error) {
      this.logger.error('Stripe payment processing failed', error);
      return {
        success: false,
        gatewayTransactionId: '',
        status: 'failed',
        amount: request.amount,
        currency: request.currency,
        error: error.message,
      };
    }
  }
}
```