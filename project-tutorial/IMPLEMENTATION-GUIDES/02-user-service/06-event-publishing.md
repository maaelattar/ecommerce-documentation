# Event Publishing - Updated with Shared Libraries

## 🎯 Objective

Implement event publishing using `@ecommerce/rabbitmq-event-utils` for reliable, standardized event handling with transactional outbox pattern.

## 📚 Architecture Changes

**❌ Before**: Direct RabbitMQ client usage  
**✅ After**: Shared event utilities with transactional outbox

---

## 🔧 Event Service with Shared Libraries

### User Service Events

```typescript
// src/events/user-events.service.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, EntityManager } from 'typeorm';
import { EventPublisher } from '@ecommerce/rabbitmq-event-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { User } from '../modules/users/entities/user.entity';

@Injectable()
export class UserEventsService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
    private eventPublisher: EventPublisher,
    private logger: LoggerService,
  ) {}

  async publishUserCreated(user: User, manager?: EntityManager): Promise<void> {
    const eventData = {
      userId: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      roles: user.roles?.map(r => r.name) || [],
      isActive: user.isActive,
      createdAt: user.createdAt,
    };

    await this.eventPublisher.publish(
      'user.created',
      eventData,
      {
        correlationId: user.id,
        source: 'user-service',
      },
      manager, // Pass transaction manager for outbox pattern
    );

    this.logger.info('User created event published', {
      userId: user.id,
      email: user.email,
    });
  }

  async publishUserUpdated(user: User, manager?: EntityManager): Promise<void> {
    const eventData = {
      userId: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      isActive: user.isActive,
      updatedAt: user.updatedAt,
    };

    await this.eventPublisher.publish(
      'user.updated',
      eventData,
      {
        correlationId: user.id,
        source: 'user-service',
      },
      manager,
    );

    this.logger.info('User updated event published', {
      userId: user.id,
    });
  }

  async publishUserLoggedIn(userId: string): Promise<void> {
    const eventData = {
      userId,
      loginTimestamp: new Date(),
      source: 'user-service',
    };

    // No transaction manager needed for login events
    await this.eventPublisher.publish(
      'user.logged_in',
      eventData,
      {
        correlationId: userId,
        source: 'user-service',
      },
    );

    this.logger.info('User login event published', { userId });
  }
}
```

### Updated User Service with Events

```typescript
// src/modules/users/services/users.service.ts (updated)
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { User } from '../entities/user.entity';
import { CreateUserDto } from '../dto/create-user.dto';
import { UserEventsService } from '../../../events/user-events.service';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
    private userEventsService: UserEventsService,
    private logger: LoggerService,
  ) {}

  async create(createUserDto: CreateUserDto): Promise<User> {
    return this.userRepository.manager.transaction(async (manager) => {
      // Create user within transaction
      const user = manager.create(User, createUserDto);
      const savedUser = await manager.save(user);

      // Publish event within same transaction (outbox pattern)
      await this.userEventsService.publishUserCreated(savedUser, manager);

      this.logger.info('User created successfully', {
        userId: savedUser.id,
        email: savedUser.email,
      });

      return savedUser;
    });
  }

  async update(id: string, updateData: Partial<User>): Promise<User> {
    return this.userRepository.manager.transaction(async (manager) => {
      await manager.update(User, id, updateData);
      const updatedUser = await manager.findOne(User, { where: { id } });

      if (updatedUser) {
        await this.userEventsService.publishUserUpdated(updatedUser, manager);
      }

      return updatedUser;
    });
  }
}
```