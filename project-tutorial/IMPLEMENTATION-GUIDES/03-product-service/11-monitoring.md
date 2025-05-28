# Tutorial 11: Monitoring & Logging

## 🎯 Objective
Implement CloudWatch monitoring, logging, and health checks for production readiness.

## Step 1: CloudWatch Integration

```bash
pnpm add aws-sdk winston winston-cloudwatch
```

**src/config/logger.config.ts:**
```typescript
import { WinstonModule } from 'nest-winston';
import * as winston from 'winston';
import * as CloudWatchTransport from 'winston-cloudwatch';

export const loggerConfig = WinstonModule.createLogger({
  transports: [
    new winston.transports.Console(),
    new CloudWatchTransport({
      logGroupName: 'ecommerce-product-service',
      logStreamName: `${process.env.NODE_ENV}-${new Date().toISOString().split('T')[0]}`,
      awsRegion: process.env.AWS_REGION || 'us-east-1',
    }),
  ],
});
```

## Step 2: Health Check

**src/modules/health/health.controller.ts:**
```typescript
import { Controller, Get } from '@nestjs/common';
import { HealthCheck, HealthCheckService, TypeOrmHealthIndicator } from '@nestjs/terminus';

@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private db: TypeOrmHealthIndicator,
  ) {}

  @Get()
  @HealthCheck()
  check() {
    return this.health.check([
      () => this.db.pingCheck('database'),
    ]);
  }
}
```

## Step 3: Metrics Collection

**src/modules/metrics/metrics.service.ts:**
```typescript
import { Injectable } from '@nestjs/common';
import { CloudWatch } from 'aws-sdk';

@Injectable()
export class MetricsService {
  private cloudWatch = new CloudWatch();

  async recordProductCreated() {
    await this.cloudWatch.putMetricData({
      Namespace: 'ECommerce/ProductService',
      MetricData: [{
        MetricName: 'ProductsCreated',
        Value: 1,
        Unit: 'Count',
      }],
    }).promise();
  }
}
```

## ✅ Next Steps
Complete with **[12-deployment.md](./12-deployment.md)** for production deployment.