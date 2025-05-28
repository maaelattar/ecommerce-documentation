# Testing - Notification Service with Shared Libraries

## 🎯 Objective
Implement comprehensive testing using shared testing utilities for consistent test patterns and mock implementations.

## 🧪 Unit Tests with Shared Testing Utilities

```typescript
// src/notification/notification.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';

// Import shared testing utilities
import { 
  createMockRepository,
  createMockDataSource,
  createMockLogger,
  createMockEventPublisher
} from '@ecommerce/testing-utils';

import { NotificationService } from './notification.service';
import { Notification, NotificationType, NotificationStatus } from './entities/notification.entity';
import { SendGridProvider } from '../providers/email/sendgrid.provider';
import { TwilioProvider } from '../providers/sms/twilio.provider';

describe('NotificationService', () => {
  let service: NotificationService;
  let mockRepository: any;
  let mockDataSource: any;
  let mockLogger: any;
  let mockEventPublisher: any;
  let mockSendGridProvider: any;
  let mockTwilioProvider: any;

  beforeEach(async () => {
    // Use shared testing utilities for consistent mocks
    mockRepository = createMockRepository();
    mockDataSource = createMockDataSource();
    mockLogger = createMockLogger();
    mockEventPublisher = createMockEventPublisher();

    // Create provider mocks
    mockSendGridProvider = {
      sendEmail: jest.fn(),
    };

    mockTwilioProvider = {
      sendSms: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        NotificationService,
        {
          provide: getRepositoryToken(Notification),
          useValue: mockRepository,
        },
        {
          provide: 'DataSource',
          useValue: mockDataSource,
        },
        {
          provide: 'LoggerService',
          useValue: mockLogger,
        },
        {
          provide: 'EventPublisher',
          useValue: mockEventPublisher,
        },
        {
          provide: SendGridProvider,
          useValue: mockSendGridProvider,
        },
        {
          provide: TwilioProvider,
          useValue: mockTwilioProvider,
        },
      ],
    }).compile();

    service = module.get<NotificationService>(NotificationService);
  });

  describe('createNotification', () => {
    it('should create notification successfully', async () => {
      const createDto = {
        userId: 'user-123',
        type: NotificationType.EMAIL,
        title: 'Test Notification',
        content: 'Test content',
        metadata: { email: 'test@example.com' },
      };

      const savedNotification = {
        id: 'notification-123',
        ...createDto,
        status: NotificationStatus.PENDING,
        createdAt: new Date(),
      };

      mockDataSource.transaction.mockImplementation(async (callback) => {
        const manager = {
          create: jest.fn().mockReturnValue(savedNotification),
          save: jest.fn().mockResolvedValue(savedNotification),
        };
        return callback(manager);
      });

      const result = await service.createNotification(createDto);

      expect(result).toEqual(savedNotification);
      expect(mockLogger.log).toHaveBeenCalledWith(
        'Notification created and queued',
        'NotificationService',
        {
          notificationId: savedNotification.id,
          userId: createDto.userId,
          type: createDto.type,
        }
      );
    });

    it('should handle creation failure', async () => {
      const createDto = {
        userId: 'user-123',
        type: NotificationType.EMAIL,
        title: 'Test Notification',
        content: 'Test content',
      };

      const error = new Error('Database error');
      mockDataSource.transaction.mockRejectedValue(error);

      await expect(service.createNotification(createDto)).rejects.toThrow(error);
      
      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to create notification',
        error,
        'NotificationService',
        {
          userId: createDto.userId,
          type: createDto.type,
        }
      );
    });
  });

  describe('processNotification', () => {
    it('should process email notification successfully', async () => {
      const notification = {
        id: 'notification-123',
        userId: 'user-123',
        type: NotificationType.EMAIL,
        title: 'Test Email',
        content: 'Test content',
        status: NotificationStatus.PENDING,
        metadata: { email: 'test@example.com' },
      };

      mockSendGridProvider.sendEmail.mockResolvedValue({ id: 'sg-message-123' });

      mockDataSource.transaction.mockImplementation(async (callback) => {
        const manager = {
          findOne: jest.fn().mockResolvedValue(notification),
          save: jest.fn().mockImplementation((entity) => Promise.resolve(entity)),
        };
        return callback(manager);
      });

      await service.processNotification(notification.id);

      expect(mockSendGridProvider.sendEmail).toHaveBeenCalledWith({
        to: notification.metadata.email,
        subject: notification.title,
        content: notification.content,
      });

      expect(mockLogger.log).toHaveBeenCalledWith(
        'Notification sent successfully',
        'NotificationService',
        {
          notificationId: notification.id,
          type: notification.type,
          externalId: 'sg-message-123',
        }
      );
    });
  });
});
```