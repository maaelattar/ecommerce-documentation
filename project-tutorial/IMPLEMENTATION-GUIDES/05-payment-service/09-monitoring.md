# 09. Monitoring & Observability

## Overview

Implement comprehensive monitoring and observability for payment operations with financial transaction tracking, performance monitoring, and security alerting.

## 🎯 Learning Objectives

- Financial transaction monitoring
- Payment success/failure dashboards
- Alerting for payment anomalies
- Performance monitoring
- Audit logging implementation

---

## Step 1: Metrics Collection

```typescript
// src/monitoring/metrics.service.ts
import { Injectable } from '@nestjs/common';
import { Counter, Histogram, Gauge } from 'prom-client';

@Injectable()
export class MetricsService {
  private readonly paymentCounter = new Counter({
    name: 'payments_total',
    help: 'Total number of payment attempts',
    labelNames: ['status', 'gateway', 'currency'],
  });

  private readonly paymentDuration = new Histogram({
    name: 'payment_processing_duration_seconds',
    help: 'Payment processing duration',
    labelNames: ['gateway', 'status'],
    buckets: [0.1, 0.5, 1, 2, 5, 10],
  });

  private readonly paymentAmount = new Histogram({
    name: 'payment_amount',
    help: 'Payment amounts processed',
    labelNames: ['currency', 'status'],
    buckets: [1, 10, 50, 100, 500, 1000, 5000],
  });

  recordPayment(status: string, gateway: string, currency: string, amount: number, duration: number) {
    this.paymentCounter.inc({ status, gateway, currency });
    this.paymentDuration.observe({ gateway, status }, duration);
    this.paymentAmount.observe({ currency, status }, amount / 100); // Convert cents to dollars
  }
}
```