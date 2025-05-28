# Monitoring & Logging

## 🎯 Objective

Implement comprehensive monitoring and logging for production readiness.

## 🔧 Install Dependencies

```bash
pnpm add @aws-sdk/client-cloudwatch winston
```

## 📊 CloudWatch Integration

### Logger Service
```typescript
// src/logger/logger.service.ts
import { Injectable } from '@nestjs/common';
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';
import * as winston from 'winston';

@Injectable()
export class LoggerService {
  private cloudWatch: CloudWatchClient;
  private logger: winston.Logger;

  constructor() {
    this.cloudWatch = new CloudWatchClient({
      region: process.env.AWS_REGION,
    });

    this.logger = winston.createLogger({
      level: 'info',
      format: winston.format.json(),
      transports: [new winston.transports.Console()],
    });
  }

  async logMetric(metricName: string, value: number) {
    const command = new PutMetricDataCommand({
      Namespace: 'ECommerce/UserService',
      MetricData: [{
        MetricName: metricName,
        Value: value,
        Unit: 'Count',
      }],
    });

    await this.cloudWatch.send(command);
  }

  info(message: string, meta?: any) {
    this.logger.info(message, meta);
  }

  error(message: string, error?: Error) {
    this.logger.error(message, { error: error?.stack });
  }
}
```