# Database Models - Notification Service

## 🎯 Objective
Design robust database models for notification management with templates, delivery tracking, and user preferences.

## 🏗️ Core Entities

### Notification Entity
```typescript
// src/notification/entities/notification.entity.ts
import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

export enum NotificationType {
  EMAIL = 'email',
  SMS = 'sms', 
  PUSH = 'push',
  IN_APP = 'in_app',
}

export enum NotificationStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered', 
  FAILED = 'failed',
  READ = 'read',
}

export enum NotificationPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent',
}

@Entity('notifications')
@Index(['userId', 'status'])
@Index(['type', 'status'])
export class Notification {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column('uuid')
  userId: string;

  @Column({ type: 'enum', enum: NotificationType })
  type: NotificationType;

  @Column({ type: 'enum', enum: NotificationStatus, default: NotificationStatus.PENDING })
  status: NotificationStatus;

  @Column({ type: 'enum', enum: NotificationPriority, default: NotificationPriority.NORMAL })
  priority: NotificationPriority;

  @Column()
  title: string;

  @Column('text')
  content: string;

  @Column('jsonb', { nullable: true })
  metadata: Record<string, any>;