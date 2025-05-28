# Core Service - Notification Service with Shared Libraries

## 🎯 Objective
Implement the core notification service using shared libraries for logging, event publishing, and consistent error handling.

## 🔧 NotificationService Implementation

```typescript
// src/notification/notification.service.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, DataSource } from 'typeorm';

// Import shared utilities
import { LoggerService } from '@ecommerce/nestjs-core-utils';
import { EventPublisher } from '@ecommerce/rabbitmq-event-utils';

import { Notification, NotificationStatus, NotificationType } from './entities/notification.entity';
import { CreateNotificationDto } from './dto/create-notification.dto';
import { SendGridProvider } from '../providers/email/sendgrid.provider';
import { TwilioProvider } from '../providers/sms/twilio.provider';
import { PushNotificationProvider } from '../providers/push/push.provider';

@Injectable()
export class NotificationService {
  constructor(
    @InjectRepository(Notification)
    private readonly notificationRepository: Repository<Notification>,
    private readonly dataSource: DataSource,
    private readonly logger: LoggerService,
    private readonly eventPublisher: EventPublisher,
    private readonly sendGridProvider: SendGridProvider,
    private readonly twilioProvider: TwilioProvider,
    private readonly pushProvider: PushNotificationProvider,
  ) {}

  async createNotification(createDto: CreateNotificationDto): Promise<Notification> {
    return await this.dataSource.transaction(async (manager) => {
      try {
        const notification = manager.create(Notification, createDto);
        const savedNotification = await manager.save(notification);

        // Queue notification for processing
        await this.queueNotificationProcessing(savedNotification.id);

        this.logger.log('Notification created and queued', 'NotificationService', {
          notificationId: savedNotification.id,
          userId: savedNotification.userId,
          type: savedNotification.type,
        });

        return savedNotification;
      } catch (error) {
        this.logger.error('Failed to create notification', error, 'NotificationService', {
          userId: createDto.userId,
          type: createDto.type,
        });
        throw error;
      }
    });
  }

  async processNotification(notificationId: string): Promise<void> {
    return await this.dataSource.transaction(async (manager) => {
      const notification = await manager.findOne(Notification, {
        where: { id: notificationId },
      });

      if (!notification || notification.status !== NotificationStatus.PENDING) {
        this.logger.warn('Notification not found or already processed', 'NotificationService', {
          notificationId,
          status: notification?.status,
        });
        return;
      }

      try {
        let externalId: string;

        // Send notification based on type
        switch (notification.type) {
          case NotificationType.EMAIL:
            const emailResult = await this.sendGridProvider.sendEmail({
              to: notification.metadata.email,
              subject: notification.title,
              content: notification.content,
            });
            externalId = emailResult.id;
            break;

          case NotificationType.SMS:
            const smsResult = await this.twilioProvider.sendSms({
              to: notification.metadata.phone,
              content: notification.content,
            });
            externalId = smsResult.id;
            break;

          case NotificationType.PUSH:
            const pushResult = await this.pushProvider.sendPush({
              userId: notification.userId,
              title: notification.title,
              content: notification.content,
            });
            externalId = pushResult.id;
            break;

          default:
            throw new Error(`Unsupported notification type: ${notification.type}`);
        }

        // Update notification status
        notification.status = NotificationStatus.SENT;
        notification.externalId = externalId;
        notification.sentAt = new Date();

        await manager.save(notification);

        this.logger.log('Notification sent successfully', 'NotificationService', {
          notificationId,
          type: notification.type,
          externalId,
        });

      } catch (error) {
        // Mark as failed
        notification.status = NotificationStatus.FAILED;
        notification.failedAt = new Date();
        notification.failureReason = error.message;

        await manager.save(notification);

        this.logger.error('Failed to send notification', error, 'NotificationService', {
          notificationId,
          type: notification.type,
        });

        throw error;
      }
    });
  }

  private async queueNotificationProcessing(notificationId: string): Promise<void> {
    // In a real implementation, this would queue the notification for background processing
    // For now, we'll process it immediately
    setTimeout(() => {
      this.processNotification(notificationId).catch((error) => {
        this.logger.error('Background notification processing failed', error, 'NotificationService', {
          notificationId,
        });
      });
    }, 100);
  }
}
```