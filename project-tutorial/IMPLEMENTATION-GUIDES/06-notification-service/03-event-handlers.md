# Event Handlers - Notification Service with Shared Libraries

## 🎯 Objective
Implement event-driven notification triggers using shared event utilities to react to domain events from other services.

## 🔄 Event Handler Implementation

```typescript
// src/events/handlers/user-events.handler.ts
import { Injectable } from '@nestjs/common';
import { EventHandler } from '@ecommerce/rabbitmq-event-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { NotificationService } from '../notification/notification.service';
import { NotificationType } from '../notification/entities/notification.entity';

@Injectable()
export class UserEventsHandler {
  constructor(
    private readonly notificationService: NotificationService,
    private readonly logger: LoggerService,
  ) {}

  @EventHandler('user.created')
  async handleUserCreated(event: any) {
    try {
      await this.notificationService.createNotification({
        userId: event.userId,
        type: NotificationType.EMAIL,
        title: 'Welcome to Our Platform!',
        content: `Welcome ${event.firstName}! Your account has been successfully created.`,
        metadata: {
          eventType: 'user.created',
          userEmail: event.email,
          timestamp: event.timestamp,
        },
      });

      this.logger.log('Welcome notification queued', 'UserEventsHandler', {
        userId: event.userId,
        email: event.email,
      });
    } catch (error) {
      this.logger.error('Failed to handle user created event', error, 'UserEventsHandler', {
        userId: event.userId,
        eventId: event.id,
      });
    }
  }

  @EventHandler('user.password_reset_requested')
  async handlePasswordResetRequested(event: any) {
    try {
      await this.notificationService.createNotification({
        userId: event.userId,
        type: NotificationType.EMAIL,
        title: 'Password Reset Request',
        content: `Click the link to reset your password: ${event.resetLink}`,
        metadata: {
          eventType: 'password_reset',
          resetToken: event.resetToken,
          expiresAt: event.expiresAt,
        },
      });

      this.logger.log('Password reset notification queued', 'UserEventsHandler', {
        userId: event.userId,
      });
    } catch (error) {
      this.logger.error('Failed to handle password reset event', error, 'UserEventsHandler', {
        userId: event.userId,
        eventId: event.id,
      });
    }
  }
}
```