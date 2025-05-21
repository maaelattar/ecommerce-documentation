# Notification Service - Data Model and Persistence

## 1. Overview

The Notification Service needs to persist several types of data to fulfill its responsibilities, including notification templates, user communication preferences, and logs of dispatched notifications. This document outlines the proposed data models and persistence strategy.

## 2. Persistence Technology

*   **Primary Database**: **PostgreSQL** (managed via Amazon RDS or equivalent).
    *   Chosen for its relational integrity, transactional capabilities, and mature tooling.
    *   Suitable for storing structured data like templates, preferences, and detailed notification logs that might require querying and joins.
*   **ORM**: **TypeORM** will be used for interacting with PostgreSQL, consistent with other NestJS services in the platform.
*   **Potential for NoSQL (Conditional)**:
    *   For extremely high-volume, simple notification status logs (e.g., just `messageId`, `status`, `timestamp`), a NoSQL solution like **Amazon DynamoDB** could be considered in the future if PostgreSQL becomes a bottleneck for this specific type of write-heavy, query-simple data. This would be a separate optimization and not part of the initial design.
    *   The Outbox table for event publishing (`notification_event_outbox`) will reside in PostgreSQL to leverage transactional consistency with other operational data if needed.

## 3. Key Data Entities

Below are the primary TypeORM entities. Specific fields are illustrative and will be refined.

### 3.1. `NotificationTemplate` Entity

Stores reusable notification templates for different channels and locales.

```typescript
import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index, VersionColumn } from 'typeorm';

export enum NotificationChannel { // Also defined in DTOs/Interfaces
  EMAIL = 'EMAIL',
  SMS = 'SMS',
  PUSH = 'PUSH',
  WEBHOOK = 'WEBHOOK',
}

@Entity('notification_templates')
@Index(['name', 'channel', 'locale', 'versionTag'], { unique: true })
export class NotificationTemplate {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ length: 255 })
  name: string; // e.g., "order_confirmation", "password_reset"

  @Column({ type: 'enum', enum: NotificationChannel })
  channel: NotificationChannel;

  @Column({ length: 255, nullable: true })
  subjectTemplate?: string; // For EMAIL: Handlebars/Liquid template for the subject

  @Column({ type: 'text' })
  bodyTemplate: string; // Handlebars/Liquid template for the body (HTML for email, text for SMS)

  @Column({ length: 10, default: 'en-US' })
  @Index()
  locale: string; // e.g., "en-US", "fr-FR"

  @Column({ length: 50, default: 'latest' })
  @Index()
  versionTag: string; // e.g., "v1.0", "latest", "stable"

  @Column({ type: 'jsonb', nullable: true })
  defaultContextSchema?: Record<string, any>; // Optional: JSON schema for expected context variables

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @VersionColumn()
  objectVersion: number;

  @Column({ length: 255, nullable: true })
  description?: string;
}
```

### 3.2. `UserCommunicationPreference` Entity

Stores user-defined preferences for receiving notifications.

```typescript
import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index, ManyToOne } from 'typeorm';
// Assume a User entity exists elsewhere, or just use userId as a foreign key concept.

@Entity('user_communication_preferences')
@Index(['userId', 'channel', 'notificationType'], { unique: true })
export class UserCommunicationPreference {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column('uuid')
  @Index()
  userId: string; // Foreign key to the User entity in User Service

  @Column({ type: 'enum', enum: NotificationChannel, nullable: true })
  // If null, preference applies to this notificationType across all channels user is subscribed to
  channel?: NotificationChannel;

  @Column({ length: 255 })
  // e.g., "ORDER_UPDATES", "MARKETING_PROMOTIONS", "SECURITY_ALERTS", "ALL_TRANSACTIONAL"
  notificationType: string; 

  @Column({ default: true })
  isEnabled: boolean; // true = opted-in, false = opted-out

  @Column({ type: 'jsonb', nullable: true })
  // Store additional channel-specific details, e.g., specific email address or phone if different from primary
  channelSettings?: Record<string, any>; 

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @Column({ length: 255, nullable: true })
  sourceOfChange?: string; // e.g., "user_settings_page", "admin_override", "initial_default"
}
```

### 3.3. `NotificationLog` Entity

Records each notification dispatch attempt and its outcome.

```typescript
import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from 'typeorm';

export enum NotificationStatus {
  PENDING_PREFERENCES = 'PENDING_PREFERENCES',
  PENDING_TEMPLATE = 'PENDING_TEMPLATE',
  PENDING_DISPATCH = 'PENDING_DISPATCH',
  SENT_TO_PROVIDER = 'SENT_TO_PROVIDER',
  DELIVERED = 'DELIVERED', // Confirmed delivery by provider
  FAILED_PROVIDER = 'FAILED_PROVIDER', // Provider rejected or failed to send
  FAILED_INTERNAL = 'FAILED_INTERNAL', // Internal error before sending to provider
  BOUNCED = 'BOUNCED',
  SPAM_COMPLAINT = 'SPAM_COMPLAINT',
  OPENED = 'OPENED', // If tracking is enabled and provider supports it
  CLICKED = 'CLICKED', // If tracking is enabled and provider supports it
  USER_OPTED_OUT = 'USER_OPTED_OUT',
  TEMPLATE_NOT_FOUND = 'TEMPLATE_NOT_FOUND',
}

@Entity('notification_logs')
export class NotificationLog {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column('uuid', { nullable: true, comment: 'Corresponds to messageId of triggering event if applicable' })
  @Index()
  triggeringEventId?: string;

  @Column('uuid', { nullable: true, comment: 'Internal reference for this notification job/instance' })
  @Index()
  notificationJobId?: string; 

  @Column({ length: 255, nullable: true })
  correlationId?: string;

  @Column('uuid', { nullable: true })
  @Index()
  userId?: string; // Recipient User ID, if applicable

  @Column({ type: 'enum', enum: NotificationChannel })
  channel: NotificationChannel;

  @Column({ length: 500 })
  recipientAddress: string; // e.g., email, phone number, device token, webhook URL

  @Column({ length: 255, nullable: true })
  templateId?: string; // ID of the NotificationTemplate used

  @Column({ length: 255, nullable: true })
  templateVersionTag?: string;

  @Column({ type: 'enum', enum: NotificationStatus, default: NotificationStatus.PENDING_DISPATCH })
  @Index()
  status: NotificationStatus;

  @Column({ type: 'text', nullable: true })
  statusReason?: string; // Details for failure, bounce reason, etc.

  @CreateDateColumn()
  createdAt: Date; // When the log entry was created (notification processing started)

  @Column({ type: 'timestamp with time zone', nullable: true })
  scheduledDispatchTime?: Date; // If the notification was scheduled
  
  @Column({ type: 'timestamp with time zone', nullable: true })
  sentToProviderAt?: Date; // When it was handed off to the external provider

  @Column({ type: 'timestamp with time zone', nullable: true })
  @Index()
  lastStatusUpdateAt?: Date; // When the status field was last updated (e.g., delivery confirmation)

  @Column({ nullable: true })
  providerMessageId?: string; // ID from the external provider (e.g., SES Message ID)

  @Column({ type: 'text', nullable: true })
  renderedSubject?: string; // Actual subject sent

  // Storing the full rendered body can be very large. Consider:
  // 1. Not storing it at all (re-render from template + context if needed for audit).
  // 2. Storing it in a separate table or object storage (S3) linked by ID.
  // 3. Storing a hash or truncated version.
  // For now, let's assume it's not stored directly in this main log table to keep it lean.
  // @Column({ type: 'text', nullable: true }) 
  // renderedBody?: string; 

  @Column({ type: 'jsonb', nullable: true })
  contextDataSnapshot?: Record<string, any>; // Snapshot of data used for templating (for debugging/audit)
}
```

### 3.4. `EventOutbox` Entity

As defined in `./05-event-publishing/02-event-publisher-implementation.md` (and mirrored from other services like Inventory Service), specific to `notification_event_outbox` table. This stores events that the Notification Service itself needs to publish.

## 4. Data Access Layer

*   Standard TypeORM repositories will be created for each entity (`NotificationTemplateRepository`, `UserCommunicationPreferenceRepository`, `NotificationLogRepository`).
*   Service classes will use these repositories to perform CRUD operations and custom queries.

## 5. Database Migrations

*   TypeORM migrations will be used to manage schema changes and evolution.
*   Initial migrations will create the tables for the entities defined above.

## 6. Data Archival and Purging (Future Consideration)

*   `NotificationLog` data can grow very large over time.
*   A strategy for archiving old logs (e.g., to S3 Glacier) and purging them from the operational PostgreSQL database will be needed eventually to maintain performance.
*   This strategy will define retention periods based on business and regulatory requirements.
