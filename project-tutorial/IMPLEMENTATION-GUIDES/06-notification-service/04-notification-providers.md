# Notification Providers - Multi-Channel Delivery

## 🎯 Objective
Implement multi-channel notification delivery using various providers (SendGrid, Twilio, AWS SNS) with shared utilities.

## 📧 Email Provider (SendGrid)

```typescript
// src/providers/email/sendgrid.provider.ts
import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as sgMail from '@sendgrid/mail';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

export interface EmailNotification {
  to: string;
  subject: string;
  content: string;
  templateId?: string;
  templateData?: Record<string, any>;
}

@Injectable()
export class SendGridProvider {
  constructor(
    private readonly configService: ConfigService,
    private readonly logger: LoggerService,
  ) {
    sgMail.setApiKey(this.configService.get('SENDGRID_API_KEY'));
  }

  async sendEmail(notification: EmailNotification): Promise<{ id: string }> {
    try {
      const msg = {
        to: notification.to,
        from: this.configService.get('FROM_EMAIL'),
        subject: notification.subject,
        html: notification.content,
        ...(notification.templateId && {
          templateId: notification.templateId,
          dynamicTemplateData: notification.templateData,
        }),
      };

      const [response] = await sgMail.send(msg);

      this.logger.log('Email sent successfully', 'SendGridProvider', {
        to: notification.to,
        subject: notification.subject,
        messageId: response.headers['x-message-id'],
      });

      return { id: response.headers['x-message-id'] };
    } catch (error) {
      this.logger.error('Failed to send email', error, 'SendGridProvider', {
        to: notification.to,
        subject: notification.subject,
      });
      throw error;
    }
  }
}
```

## 📱 SMS Provider (Twilio)

```typescript
// src/providers/sms/twilio.provider.ts
import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Twilio } from 'twilio';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

export interface SmsNotification {
  to: string;
  content: string;
}

@Injectable()
export class TwilioProvider {
  private client: Twilio;

  constructor(
    private readonly configService: ConfigService,
    private readonly logger: LoggerService,
  ) {
    this.client = new Twilio(
      this.configService.get('TWILIO_ACCOUNT_SID'),
      this.configService.get('TWILIO_AUTH_TOKEN'),
    );
  }

  async sendSms(notification: SmsNotification): Promise<{ id: string }> {
    try {
      const message = await this.client.messages.create({
        body: notification.content,
        from: this.configService.get('TWILIO_PHONE_NUMBER'),
        to: notification.to,
      });

      this.logger.log('SMS sent successfully', 'TwilioProvider', {
        to: notification.to,
        messageSid: message.sid,
      });

      return { id: message.sid };
    } catch (error) {
      this.logger.error('Failed to send SMS', error, 'TwilioProvider', {
        to: notification.to,
      });
      throw error;
    }
  }
}
```