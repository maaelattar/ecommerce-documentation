# API Endpoints - Notification Service

## 🎯 Objective
Build REST API endpoints for notification management using shared authentication and validation utilities.

## 🔐 NotificationController Implementation

```typescript
// src/notification/notification.controller.ts
import { Controller, Get, Post, Put, Param, Body, Query, UseGuards, Req } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiQuery } from '@nestjs/swagger';

// Import shared utilities
import { JwtAuthGuard } from '@ecommerce/auth-client-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { NotificationService } from './notification.service';
import { CreateNotificationDto } from './dto/create-notification.dto';
import { NotificationListDto } from './dto/notification-list.dto';

@ApiTags('notifications')
@Controller('notifications')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class NotificationController {
  constructor(
    private readonly notificationService: NotificationService,
    private readonly logger: LoggerService,
  ) {}

  @Get()
  @ApiOperation({ summary: 'Get user notifications' })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiQuery({ name: 'type', required: false, enum: ['email', 'sms', 'push', 'in_app'] })
  @ApiQuery({ name: 'status', required: false, enum: ['pending', 'sent', 'delivered', 'failed', 'read'] })
  async getUserNotifications(
    @Req() req: any,
    @Query() query: NotificationListDto,
  ) {
    const userId = req.user.sub;
    
    this.logger.log('Fetching user notifications', 'NotificationController', {
      userId,
      filters: query,
    });

    return await this.notificationService.getUserNotifications(userId, query);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get notification by ID' })
  async getNotification(@Param('id') id: string, @Req() req: any) {
    const userId = req.user.sub;
    return await this.notificationService.getNotificationById(id, userId);
  }

  @Put(':id/read')
  @ApiOperation({ summary: 'Mark notification as read' })
  async markAsRead(@Param('id') id: string, @Req() req: any) {
    const userId = req.user.sub;
    
    this.logger.log('Marking notification as read', 'NotificationController', {
      notificationId: id,
      userId,
    });

    return await this.notificationService.markAsRead(id, userId);
  }

  @Post('test')
  @ApiOperation({ summary: 'Send test notification (admin only)' })
  async sendTestNotification(
    @Body() createDto: CreateNotificationDto,
    @Req() req: any,
  ) {
    // In real implementation, check for admin role
    this.logger.log('Sending test notification', 'NotificationController', {
      type: createDto.type,
      userId: createDto.userId,
    });

    return await this.notificationService.createNotification(createDto);
  }

  @Get('stats/summary')
  @ApiOperation({ summary: 'Get notification statistics' })
  async getNotificationStats(@Req() req: any) {
    const userId = req.user.sub;
    return await this.notificationService.getNotificationStats(userId);
  }
}
```

## 📊 DTOs and Validation

```typescript
// src/notification/dto/create-notification.dto.ts
import { IsString, IsEnum, IsUUID, IsOptional, IsObject } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';
import { NotificationType, NotificationPriority } from '../entities/notification.entity';

export class CreateNotificationDto {
  @ApiProperty()
  @IsUUID()
  userId: string;

  @ApiProperty({ enum: NotificationType })
  @IsEnum(NotificationType)
  type: NotificationType;

  @ApiProperty()
  @IsString()
  title: string;

  @ApiProperty()
  @IsString()
  content: string;

  @ApiProperty({ enum: NotificationPriority, required: false })
  @IsEnum(NotificationPriority)
  @IsOptional()
  priority?: NotificationPriority;

  @ApiProperty({ required: false })
  @IsObject()
  @IsOptional()
  metadata?: Record<string, any>;

  @ApiProperty({ required: false })
  @IsString()
  @IsOptional()
  templateId?: string;
}
```