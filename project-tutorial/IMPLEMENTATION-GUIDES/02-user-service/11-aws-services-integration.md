# AWS Services Integration

## 🎯 Objective

Integrate AWS services for production-ready operations.

## 🔧 AWS SES for Email

```bash
pnpm add @aws-sdk/client-ses
```

### Email Service (`src/email/email.service.ts`)
```typescript
import { Injectable } from '@nestjs/common';
import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';

@Injectable()
export class EmailService {
  private sesClient: SESClient;

  constructor() {
    this.sesClient = new SESClient({
      region: process.env.AWS_REGION,
      endpoint: process.env.AWS_ENDPOINT_URL,
    });
  }

  async sendPasswordResetEmail(email: string, token: string) {
    const resetUrl = `${process.env.FRONTEND_URL}/reset-password?token=${token}`;
    
    const command = new SendEmailCommand({
      Source: process.env.SES_FROM_EMAIL,
      Destination: { ToAddresses: [email] },
      Message: {
        Subject: { Data: 'Password Reset Request' },
        Body: {
          Html: { Data: `<p>Click <a href="${resetUrl}">here</a> to reset.</p>` },
        },
      },
    });

    return this.sesClient.send(command);
  }
}
```## 🔐 AWS Secrets Manager

```bash
pnpm add @aws-sdk/client-secrets-manager
```

### Config Service (`src/config/config.service.ts`)
```typescript
import { Injectable } from '@nestjs/common';
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

@Injectable()
export class ConfigService {
  private secretsClient: SecretsManagerClient;

  constructor() {
    this.secretsClient = new SecretsManagerClient({
      region: process.env.AWS_REGION,
    });
  }

  async getDatabasePassword(): Promise<string> {
    const command = new GetSecretValueCommand({
      SecretId: process.env.DB_PASSWORD_SECRET_NAME,
    });
    
    const result = await this.secretsClient.send(command);
    return JSON.parse(result.SecretString || '{}').password;
  }
}
```

## 📊 Benefits

- **SES** - Reliable email delivery with bounce/complaint handling
- **Secrets Manager** - Secure credential storage and rotation
- **CloudWatch** - Comprehensive monitoring and alerting

## ✅ Next Step

Continue to **[12-rbac-system.md](./12-rbac-system.md)**