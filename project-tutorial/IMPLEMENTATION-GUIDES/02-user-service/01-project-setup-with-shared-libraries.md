# User Service Project Setup with Shared Libraries 🚀

> **Goal**: Create a production-ready NestJS User Service using all shared libraries for authentication, logging, events, and testing

---

## 🎯 **What You'll Build**

A complete User Service that demonstrates:
- **Zero-config setup** using shared libraries
- **Enterprise authentication** with JWT and RBAC
- **Structured logging** with correlation IDs
- **Event-driven architecture** with reliable messaging
- **Comprehensive testing** with shared utilities

---

## 📋 **Prerequisites** 

✅ **Completed**: [Shared Libraries Implementation](../00-shared-libraries/)
✅ **Infrastructure**: LocalStack and CDK setup
✅ **Tools**: Node.js 18+, Docker, pnpm

---

## 🏗️ **Project Structure**

```
services/user-service/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   ├── repositories/
│   │   └── events/
│   ├── application/
│   │   ├── dto/
│   │   ├── services/
│   │   └── use-cases/
│   ├── infrastructure/
│   │   ├── database/
│   │   ├── repositories/
│   │   └── messaging/
│   ├── presentation/
│   │   ├── controllers/
│   │   └── guards/
│   └── main.ts
├── test/
├── package.json
├── docker-compose.yml
└── Dockerfile
```

---

## 📦 **1. Initialize Project**

### **Create Service Directory**
```bash
mkdir -p services/user-service
cd services/user-service
```

### **Initialize Package**
```bash
npm init -y
```

### **Package.json Configuration**
```json
{
  "name": "@ecommerce/user-service",
  "version": "1.0.0",
  "description": "User management microservice",
  "scripts": {
    "build": "nest build",
    "format": "prettier --write \"src/**/*.ts\" \"test/**/*.ts\"",
    "start": "nest start",
    "start:dev": "nest start --watch",
    "start:debug": "nest start --debug --watch",
    "start:prod": "node dist/main",
    "lint": "eslint \"{src,apps,libs,test}/**/*.ts\" --fix",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:cov": "jest --coverage",
    "test:debug": "node --inspect-brk -r tsconfig-paths/register -r ts-node/register node_modules/.bin/jest --runInBand",
    "test:e2e": "jest --config ./test/jest-e2e.json",
    "migration:generate": "npm run typeorm migration:generate",
    "migration:run": "npm run typeorm migration:run",
    "migration:revert": "npm run typeorm migration:revert",
    "typeorm": "typeorm-ts-node-commonjs"
  },
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/platform-express": "^10.0.0",
    "@nestjs/config": "^3.0.0",
    "@nestjs/typeorm": "^10.0.0",
    "@nestjs/swagger": "^7.0.0",
    "typeorm": "^0.3.17",
    "pg": "^8.11.0",
    "class-validator": "^0.14.0",
    "class-transformer": "^0.5.0",
    "bcrypt": "^5.1.0",
    "uuid": "^9.0.0",
    "reflect-metadata": "^0.1.13",
    "rxjs": "^7.8.1",
    
    "@ecommerce/nestjs-core-utils": "file:../../packages/nestjs-core-utils",
    "@ecommerce/auth-client-utils": "file:../../packages/auth-client-utils",
    "@ecommerce/rabbitmq-event-utils": "file:../../packages/rabbitmq-event-utils",
    "@ecommerce/testing-utils": "file:../../packages/testing-utils"
  },
  "devDependencies": {
    "@nestjs/cli": "^10.0.0",
    "@nestjs/schematics": "^10.0.0",
    "@nestjs/testing": "^10.0.0",
    "@types/bcrypt": "^5.0.0",
    "@types/express": "^4.17.17",
    "@types/jest": "^29.5.2",
    "@types/node": "^20.3.1",
    "@types/pg": "^8.10.0",
    "@types/supertest": "^2.0.12",
    "@types/uuid": "^9.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.42.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-prettier": "^5.0.0",
    "jest": "^29.5.0",
    "prettier": "^3.0.0",
    "source-map-support": "^0.5.21",
    "supertest": "^6.3.0",
    "ts-jest": "^29.1.0",
    "ts-loader": "^9.4.3",
    "ts-node": "^10.9.1",
    "tsconfig-paths": "^4.2.1",
    "typescript": "^5.1.3"
  }
}
```

---

## ⚙️ **2. Configuration Setup**

### **Environment Configuration**
```bash
# .env.development
NODE_ENV=development
PORT=3001
LOG_LEVEL=debug

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/user_service_dev

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_EXPIRES_IN=15m
JWT_REFRESH_EXPIRES_IN=7d
JWT_ISSUER=ecommerce-platform
JWT_AUDIENCE=ecommerce-services

# Event Messaging
RABBITMQ_URL=amqp://localhost:5672

# Caching
REDIS_URL=redis://localhost:6379

# Service Configuration
SERVICE_NAME=user-service
CORS_ORIGIN=http://localhost:3000
```

### **TypeScript Configuration**
```json
{
  "compilerOptions": {
    "module": "commonjs",
    "declaration": true,
    "removeComments": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "allowSyntheticDefaultImports": true,
    "target": "ES2021",
    "sourceMap": true,
    "outDir": "./dist",
    "baseUrl": "./",
    "incremental": true,
    "skipLibCheck": true,
    "strictNullChecks": false,
    "noImplicitAny": false,
    "strictBindCallApply": false,
    "forceConsistentCasingInFileNames": false,
    "noFallthroughCasesInSwitch": false,
    "paths": {
      "@/*": ["src/*"],
      "@domain/*": ["src/domain/*"],
      "@application/*": ["src/application/*"],
      "@infrastructure/*": ["src/infrastructure/*"],
      "@presentation/*": ["src/presentation/*"]
    }
  }
}
```

---

## 🏛️ **3. Domain Layer Implementation**

### **User Entity**
```typescript
// src/domain/entities/user.entity.ts
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToOne,
  ManyToMany,
  JoinTable
} from 'typeorm';
import { UserRole } from '@ecommerce/auth-client-utils';
import { UserProfile } from './user-profile.entity';
import { Role } from './role.entity';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  email: string;

  @Column()
  passwordHash: string;

  @Column({ default: true })
  isActive: boolean;

  @Column({ type: 'boolean', default: false })
  isEmailVerified: boolean;

  @Column({ type: 'timestamp', nullable: true })
  lastLoginAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  emailVerifiedAt: Date;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @OneToOne(() => UserProfile, profile => profile.user, { cascade: true })
  profile: UserProfile;

  @ManyToMany(() => Role)
  @JoinTable({
    name: 'user_roles',
    joinColumn: { name: 'user_id', referencedColumnName: 'id' },
    inverseJoinColumn: { name: 'role_id', referencedColumnName: 'id' }
  })
  roles: Role[];

  // Domain methods
  hasRole(roleName: UserRole): boolean {
    return this.roles.some(role => role.name === roleName);
  }

  activate(): void {
    this.isActive = true;
  }

  deactivate(): void {
    this.isActive = false;
  }

  verifyEmail(): void {
    this.isEmailVerified = true;
    this.emailVerifiedAt = new Date();
  }

  updateLastLogin(): void {
    this.lastLoginAt = new Date();
  }
}
```

### **User Profile Entity**
```typescript
// src/domain/entities/user-profile.entity.ts
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  OneToOne,
  JoinColumn
} from 'typeorm';
import { User } from './user.entity';

@Entity('user_profiles')
export class UserProfile {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ nullable: true })
  firstName: string;

  @Column({ nullable: true })
  lastName: string;

  @Column({ nullable: true })
  phoneNumber: string;

  @Column({ type: 'date', nullable: true })
  dateOfBirth: Date;

  @Column({ type: 'jsonb', nullable: true })
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };

  @Column({ nullable: true })
  avatarUrl: string;

  @Column({ type: 'text', nullable: true })
  bio: string;

  @Column({ type: 'jsonb', nullable: true })
  preferences: {
    language: string;
    timezone: string;
    currency: string;
    notifications: {
      email: boolean;
      sms: boolean;
      push: boolean;
    };
  };

  @OneToOne(() => User, user => user.profile)
  @JoinColumn({ name: 'user_id' })
  user: User;

  // Helper methods
  get fullName(): string {
    return `${this.firstName || ''} ${this.lastName || ''}`.trim();
  }

  updateAddress(address: Partial<UserProfile['address']>): void {
    this.address = { ...this.address, ...address };
  }

  updatePreferences(preferences: Partial<UserProfile['preferences']>): void {
    this.preferences = { ...this.preferences, ...preferences };
  }
}
```

### **Role Entity**
```typescript
// src/domain/entities/role.entity.ts
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToMany,
  JoinTable,
  CreateDateColumn,
  UpdateDateColumn
} from 'typeorm';
import { UserRole, Permission } from '@ecommerce/auth-client-utils';
import { User } from './user.entity';

@Entity('roles')
export class Role {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'enum', enum: UserRole, unique: true })
  name: UserRole;

  @Column()
  description: string;

  @Column({ type: 'enum', enum: Permission, array: true })
  permissions: Permission[];

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @ManyToMany(() => User, user => user.roles)
  users: User[];

  hasPermission(permission: Permission): boolean {
    return this.permissions.includes(permission);
  }

  addPermission(permission: Permission): void {
    if (!this.hasPermission(permission)) {
      this.permissions.push(permission);
    }
  }

  removePermission(permission: Permission): void {
    this.permissions = this.permissions.filter(p => p !== permission);
  }
}
```

---

## 📨 **4. Domain Events**

### **User Domain Events**
```typescript
// src/domain/events/user.events.ts
import { DomainEvent } from '@ecommerce/rabbitmq-event-utils';

export class UserRegisteredEvent implements DomainEvent {
  eventId: string;
  eventType = 'UserRegisteredEvent';
  aggregateId: string;
  aggregateType = 'User';
  eventVersion = 1;
  occurredAt: Date;
  correlationId?: string;
  causationId?: string;

  constructor(
    public data: {
      userId: string;
      email: string;
      firstName?: string;
      lastName?: string;
    },
    correlationId?: string
  ) {
    this.eventId = require('uuid').v4();
    this.aggregateId = data.userId;
    this.occurredAt = new Date();
    this.correlationId = correlationId;
  }
}

export class UserProfileUpdatedEvent implements DomainEvent {
  eventId: string;
  eventType = 'UserProfileUpdatedEvent';
  aggregateId: string;
  aggregateType = 'User';
  eventVersion = 1;
  occurredAt: Date;
  correlationId?: string;
  causationId?: string;

  constructor(
    public data: {
      userId: string;
      email: string;
      profileChanges: Record<string, any>;
    },
    correlationId?: string
  ) {
    this.eventId = require('uuid').v4();
    this.aggregateId = data.userId;
    this.occurredAt = new Date();
    this.correlationId = correlationId;
  }
}

export class UserDeactivatedEvent implements DomainEvent {
  eventId: string;
  eventType = 'UserDeactivatedEvent';
  aggregateId: string;
  aggregateType = 'User';
  eventVersion = 1;
  occurredAt: Date;
  correlationId?: string;
  causationId?: string;

  constructor(
    public data: {
      userId: string;
      email: string;
      reason?: string;
    },
    correlationId?: string
  ) {
    this.eventId = require('uuid').v4();
    this.aggregateId = data.userId;
    this.occurredAt = new Date();
    this.correlationId = correlationId;
  }
}
```

---

## 📄 **5. Application Layer - DTOs**

### **User DTOs**
```typescript
// src/application/dto/user.dto.ts
import { 
  IsEmail, 
  IsString, 
  IsOptional, 
  MinLength, 
  IsBoolean,
  IsEnum,
  ValidateNested,
  IsDateString,
  IsPhoneNumber
} from 'class-validator';
import { Type } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { UserRole } from '@ecommerce/auth-client-utils';

export class CreateUserDto {
  @ApiProperty({ example: 'user@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ example: 'SecurePassword123!', minLength: 8 })
  @IsString()
  @MinLength(8)
  password: string;

  @ApiPropertyOptional({ example: 'John' })
  @IsOptional()
  @IsString()
  firstName?: string;

  @ApiPropertyOptional({ example: 'Doe' })
  @IsOptional()
  @IsString()
  lastName?: string;

  @ApiPropertyOptional({ example: '+1234567890' })
  @IsOptional()
  @IsPhoneNumber()
  phoneNumber?: string;
}

export class UpdateUserProfileDto {
  @ApiPropertyOptional({ example: 'John' })
  @IsOptional()
  @IsString()
  firstName?: string;

  @ApiPropertyOptional({ example: 'Doe' })
  @IsOptional()
  @IsString()
  lastName?: string;

  @ApiPropertyOptional({ example: '+1234567890' })
  @IsOptional()
  @IsPhoneNumber()
  phoneNumber?: string;

  @ApiPropertyOptional({ example: '1990-01-01' })
  @IsOptional()
  @IsDateString()
  dateOfBirth?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @ValidateNested()
  @Type(() => AddressDto)
  address?: AddressDto;

  @ApiPropertyOptional({ example: 'Software developer passionate about technology' })
  @IsOptional()
  @IsString()
  bio?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @ValidateNested()
  @Type(() => UserPreferencesDto)
  preferences?: UserPreferencesDto;
}

export class AddressDto {
  @ApiProperty({ example: '123 Main St' })
  @IsString()
  street: string;

  @ApiProperty({ example: 'New York' })
  @IsString()
  city: string;

  @ApiProperty({ example: 'NY' })
  @IsString()
  state: string;

  @ApiProperty({ example: '10001' })
  @IsString()
  zipCode: string;

  @ApiProperty({ example: 'USA' })
  @IsString()
  country: string;
}

export class UserPreferencesDto {
  @ApiPropertyOptional({ example: 'en' })
  @IsOptional()
  @IsString()
  language?: string;

  @ApiPropertyOptional({ example: 'America/New_York' })
  @IsOptional()
  @IsString()
  timezone?: string;

  @ApiPropertyOptional({ example: 'USD' })
  @IsOptional()
  @IsString()
  currency?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @ValidateNested()
  @Type(() => NotificationPreferencesDto)
  notifications?: NotificationPreferencesDto;
}

export class NotificationPreferencesDto {
  @ApiPropertyOptional({ example: true })
  @IsOptional()
  @IsBoolean()
  email?: boolean;

  @ApiPropertyOptional({ example: false })
  @IsOptional()
  @IsBoolean()
  sms?: boolean;

  @ApiPropertyOptional({ example: true })
  @IsOptional()
  @IsBoolean()
  push?: boolean;
}

export class AssignRoleDto {
  @ApiProperty({ enum: UserRole })
  @IsEnum(UserRole)
  role: UserRole;
}

export class UserResponseDto {
  @ApiProperty()
  id: string;

  @ApiProperty()
  email: string;

  @ApiProperty()
  isActive: boolean;

  @ApiProperty()
  isEmailVerified: boolean;

  @ApiProperty()
  createdAt: Date;

  @ApiProperty()
  updatedAt: Date;

  @ApiPropertyOptional()
  profile?: UserProfileResponseDto;

  @ApiPropertyOptional({ type: [String] })
  roles?: string[];
}

export class UserProfileResponseDto {
  @ApiPropertyOptional()
  firstName?: string;

  @ApiPropertyOptional()
  lastName?: string;

  @ApiPropertyOptional()
  fullName?: string;

  @ApiPropertyOptional()
  phoneNumber?: string;

  @ApiPropertyOptional()
  dateOfBirth?: Date;

  @ApiPropertyOptional()
  address?: AddressDto;

  @ApiPropertyOptional()
  avatarUrl?: string;

  @ApiPropertyOptional()
  bio?: string;

  @ApiPropertyOptional()
  preferences?: UserPreferencesDto;
}
```

---

## 🔧 **6. Application Services**

### **User Service**
```typescript
// src/application/services/user.service.ts
import { Injectable, ConflictException, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import * as bcrypt from 'bcrypt';
import { 
  AppLoggerService, 
  BusinessException 
} from '@ecommerce/nestjs-core-utils';
import { 
  EventPublisherService,
  TransactionalOutbox 
} from '@ecommerce/rabbitmq-event-utils';
import { UserRole } from '@ecommerce/auth-client-utils';

import { User } from '@domain/entities/user.entity';
import { UserProfile } from '@domain/entities/user-profile.entity';
import { Role } from '@domain/entities/role.entity';
import { 
  CreateUserDto, 
  UpdateUserProfileDto, 
  UserResponseDto 
} from '@application/dto/user.dto';
import { 
  UserRegisteredEvent, 
  UserProfileUpdatedEvent,
  UserDeactivatedEvent 
} from '@domain/events/user.events';

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
    @InjectRepository(UserProfile)
    private profileRepository: Repository<UserProfile>,
    @InjectRepository(Role)
    private roleRepository: Repository<Role>,
    private logger: AppLoggerService,
    private eventPublisher: EventPublisherService,
    private transactionalOutbox: TransactionalOutbox
  ) {
    this.logger.setContext({ serviceName: 'UserService' });
  }

  async createUser(
    createUserDto: CreateUserDto,
    correlationId?: string
  ): Promise<UserResponseDto> {
    this.logger.setContext({ correlationId, operation: 'createUser' });
    this.logger.info('Creating new user', { email: createUserDto.email });

    // Check if user already exists
    const existingUser = await this.userRepository.findOne({
      where: { email: createUserDto.email }
    });

    if (existingUser) {
      throw new ConflictException(`User with email ${createUserDto.email} already exists`);
    }

    // Hash password
    const passwordHash = await bcrypt.hash(createUserDto.password, 12);

    // Create user with profile
    const user = new User();
    user.email = createUserDto.email;
    user.passwordHash = passwordHash;

    const profile = new UserProfile();
    profile.firstName = createUserDto.firstName;
    profile.lastName = createUserDto.lastName;
    profile.phoneNumber = createUserDto.phoneNumber;
    profile.preferences = {
      language: 'en',
      timezone: 'UTC',
      currency: 'USD',
      notifications: {
        email: true,
        sms: false,
        push: true
      }
    };
    
    user.profile = profile;

    // Assign default role
    const customerRole = await this.roleRepository.findOne({
      where: { name: UserRole.CUSTOMER }
    });
    
    if (customerRole) {
      user.roles = [customerRole];
    }

    // Save user and publish event using transactional outbox
    const operation = {
      async execute(): Promise<User> {
        return await this.userRepository.save(user);
      },
      getEvents: () => [
        new UserRegisteredEvent({
          userId: user.id,
          email: user.email,
          firstName: profile.firstName,
          lastName: profile.lastName
        }, correlationId)
      ]
    };

    const savedUser = await this.transactionalOutbox.executeWithEvents(
      user.id,
      operation
    );

    this.logger.info('User created successfully', { 
      userId: savedUser.id,
      email: savedUser.email 
    });

    return this.mapToResponseDto(savedUser);
  }

  async findById(id: string): Promise<UserResponseDto> {
    this.logger.info('Finding user by ID', { userId: id });

    const user = await this.userRepository.findOne({
      where: { id },
      relations: ['profile', 'roles']
    });

    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found`);
    }

    return this.mapToResponseDto(user);
  }

  async findByEmail(email: string): Promise<UserResponseDto | null> {
    this.logger.info('Finding user by email', { email });

    const user = await this.userRepository.findOne({
      where: { email },
      relations: ['profile', 'roles']
    });

    return user ? this.mapToResponseDto(user) : null;
  }

  async updateProfile(
    userId: string,
    updateDto: UpdateUserProfileDto,
    correlationId?: string
  ): Promise<UserResponseDto> {
    this.logger.setContext({ correlationId, operation: 'updateProfile' });
    this.logger.info('Updating user profile', { userId });

    const user = await this.userRepository.findOne({
      where: { id: userId },
      relations: ['profile', 'roles']
    });

    if (!user) {
      throw new NotFoundException(`User with ID ${userId} not found`);
    }

    // Track changes for event
    const profileChanges: Record<string, any> = {};

    // Update profile
    if (updateDto.firstName !== undefined) {
      profileChanges.firstName = { from: user.profile.firstName, to: updateDto.firstName };
      user.profile.firstName = updateDto.firstName;
    }
    
    if (updateDto.lastName !== undefined) {
      profileChanges.lastName = { from: user.profile.lastName, to: updateDto.lastName };
      user.profile.lastName = updateDto.lastName;
    }
    
    if (updateDto.phoneNumber !== undefined) {
      profileChanges.phoneNumber = { from: user.profile.phoneNumber, to: updateDto.phoneNumber };
      user.profile.phoneNumber = updateDto.phoneNumber;
    }
    
    if (updateDto.dateOfBirth !== undefined) {
      profileChanges.dateOfBirth = { from: user.profile.dateOfBirth, to: updateDto.dateOfBirth };
      user.profile.dateOfBirth = new Date(updateDto.dateOfBirth);
    }
    
    if (updateDto.bio !== undefined) {
      profileChanges.bio = { from: user.profile.bio, to: updateDto.bio };
      user.profile.bio = updateDto.bio;
    }

    if (updateDto.address) {
      profileChanges.address = { from: user.profile.address, to: updateDto.address };
      user.profile.updateAddress(updateDto.address);
    }

    if (updateDto.preferences) {
      profileChanges.preferences = { from: user.profile.preferences, to: updateDto.preferences };
      user.profile.updatePreferences(updateDto.preferences);
    }

    // Save and publish event
    const operation = {
      async execute(): Promise<User> {
        return await this.userRepository.save(user);
      },
      getEvents: () => [
        new UserProfileUpdatedEvent({
          userId: user.id,
          email: user.email,
          profileChanges
        }, correlationId)
      ]
    };

    const updatedUser = await this.transactionalOutbox.executeWithEvents(
      user.id,
      operation
    );

    this.logger.info('User profile updated successfully', { userId });

    return this.mapToResponseDto(updatedUser);
  }

  async deactivateUser(
    userId: string,
    reason?: string,
    correlationId?: string
  ): Promise<void> {
    this.logger.setContext({ correlationId, operation: 'deactivateUser' });
    this.logger.info('Deactivating user', { userId, reason });

    const user = await this.userRepository.findOne({
      where: { id: userId },
      relations: ['profile']
    });

    if (!user) {
      throw new NotFoundException(`User with ID ${userId} not found`);
    }

    if (!user.isActive) {
      throw new BusinessException(`User ${userId} is already deactivated`, 'USER_ALREADY_INACTIVE');
    }

    user.deactivate();

    // Save and publish event
    const operation = {
      async execute(): Promise<User> {
        return await this.userRepository.save(user);
      },
      getEvents: () => [
        new UserDeactivatedEvent({
          userId: user.id,
          email: user.email,
          reason
        }, correlationId)
      ]
    };

    await this.transactionalOutbox.executeWithEvents(
      user.id,
      operation
    );

    this.logger.info('User deactivated successfully', { userId });
  }

  private mapToResponseDto(user: User): UserResponseDto {
    return {
      id: user.id,
      email: user.email,
      isActive: user.isActive,
      isEmailVerified: user.isEmailVerified,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt,
      profile: user.profile ? {
        firstName: user.profile.firstName,
        lastName: user.profile.lastName,
        fullName: user.profile.fullName,
        phoneNumber: user.profile.phoneNumber,
        dateOfBirth: user.profile.dateOfBirth,
        address: user.profile.address,
        avatarUrl: user.profile.avatarUrl,
        bio: user.profile.bio,
        preferences: user.profile.preferences
      } : undefined,
      roles: user.roles?.map(role => role.name) || []
    };
  }
}
```

---

## 🎮 **7. Controllers**

### **User Controller**
```typescript
// src/presentation/controllers/user.controller.ts
import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  UseGuards,
  HttpCode,
  HttpStatus
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
  ApiParam
} from '@nestjs/swagger';
import {
  JwtAuthGuard,
  RolesGuard,
  CurrentUser,
  GetCorrelationId,
  Roles,
  RequirePermissions,
  AuthenticatedUser,
  UserRole,
  Permission
} from '@ecommerce/auth-client-utils';
import { 
  TransformInterceptor,
  ApiSuccessResponse 
} from '@ecommerce/nestjs-core-utils';

import { UserService } from '@application/services/user.service';
import {
  CreateUserDto,
  UpdateUserProfileDto,
  UserResponseDto,
  AssignRoleDto
} from '@application/dto/user.dto';

@ApiTags('Users')
@Controller('users')
@UseGuards(JwtAuthGuard, RolesGuard)
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create a new user' })
  @ApiSuccessResponse(UserResponseDto, 'User created successfully')
  @RequirePermissions(Permission.USER_WRITE)
  async createUser(
    @Body() createUserDto: CreateUserDto,
    @GetCorrelationId() correlationId: string
  ): Promise<UserResponseDto> {
    return await this.userService.createUser(createUserDto, correlationId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  @ApiParam({ name: 'id', description: 'User ID' })
  @ApiSuccessResponse(UserResponseDto, 'User found')
  @RequirePermissions(Permission.USER_READ)
  async getUserById(@Param('id') id: string): Promise<UserResponseDto> {
    return await this.userService.findById(id);
  }

  @Get('profile/me')
  @ApiOperation({ summary: 'Get current user profile' })
  @ApiSuccessResponse(UserResponseDto, 'Current user profile')
  @ApiBearerAuth()
  async getMyProfile(@CurrentUser() user: AuthenticatedUser): Promise<UserResponseDto> {
    return await this.userService.findById(user.id);
  }

  @Put('profile/me')
  @ApiOperation({ summary: 'Update current user profile' })
  @ApiSuccessResponse(UserResponseDto, 'Profile updated successfully')
  @ApiBearerAuth()
  async updateMyProfile(
    @CurrentUser() user: AuthenticatedUser,
    @Body() updateDto: UpdateUserProfileDto,
    @GetCorrelationId() correlationId: string
  ): Promise<UserResponseDto> {
    return await this.userService.updateProfile(user.id, updateDto, correlationId);
  }

  @Put(':id/profile')
  @ApiOperation({ summary: 'Update user profile (Admin only)' })
  @ApiParam({ name: 'id', description: 'User ID' })
  @ApiSuccessResponse(UserResponseDto, 'Profile updated successfully')
  @RequirePermissions(Permission.USER_WRITE)
  @Roles(UserRole.ADMIN)
  async updateUserProfile(
    @Param('id') id: string,
    @Body() updateDto: UpdateUserProfileDto,
    @GetCorrelationId() correlationId: string
  ): Promise<UserResponseDto> {
    return await this.userService.updateProfile(id, updateDto, correlationId);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Deactivate user (Admin only)' })
  @ApiParam({ name: 'id', description: 'User ID' })
  @ApiResponse({ status: 204, description: 'User deactivated successfully' })
  @RequirePermissions(Permission.USER_DELETE)
  @Roles(UserRole.ADMIN)
  async deactivateUser(
    @Param('id') id: string,
    @GetCorrelationId() correlationId: string
  ): Promise<void> {
    await this.userService.deactivateUser(id, 'Admin deactivation', correlationId);
  }
}
```

---

## 🏗️ **8. Main Application Module**

### **User Module**
```typescript
// src/user.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { 
  LoggerModule, 
  ConfigModule as CoreConfigModule,
  HealthModule 
} from '@ecommerce/nestjs-core-utils';
import { AuthModule } from '@ecommerce/auth-client-utils';
import { RabbitMQEventModule } from '@ecommerce/rabbitmq-event-utils';

import { User } from '@domain/entities/user.entity';
import { UserProfile } from '@domain/entities/user-profile.entity';
import { Role } from '@domain/entities/role.entity';
import { UserService } from '@application/services/user.service';
import { UserController } from '@presentation/controllers/user.controller';

@Module({
  imports: [
    // Core modules from shared libraries
    LoggerModule,
    CoreConfigModule,
    AuthModule,
    RabbitMQEventModule,
    HealthModule,

    // Database
    TypeOrmModule.forRootAsync({
      useFactory: () => ({
        type: 'postgres',
        url: process.env.DATABASE_URL,
        entities: [User, UserProfile, Role],
        synchronize: process.env.NODE_ENV === 'development',
        logging: process.env.NODE_ENV === 'development'
      })
    }),
    TypeOrmModule.forFeature([User, UserProfile, Role])
  ],
  controllers: [UserController],
  providers: [UserService],
  exports: [UserService]
})
export class UserModule {}
```

### **Main Application File**
```typescript
// src/main.ts
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { 
  AppLoggerService,
  GlobalExceptionFilter,
  TransformInterceptor 
} from '@ecommerce/nestjs-core-utils';
import { UserModule } from './user.module';

async function bootstrap() {
  const app = await NestFactory.create(UserModule);

  // Get logger instance
  const logger = app.get(AppLoggerService);
  logger.setContext({ serviceName: 'user-service' });

  // Global pipes
  app.useGlobalPipes(new ValidationPipe({
    transform: true,
    whitelist: true,
    forbidNonWhitelisted: true
  }));

  // Global filters and interceptors
  app.useGlobalFilters(new GlobalExceptionFilter(logger));
  app.useGlobalInterceptors(new TransformInterceptor());

  // CORS
  app.enableCors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true
  });

  // Swagger documentation
  const config = new DocumentBuilder()
    .setTitle('User Service API')
    .setDescription('User management microservice')
    .setVersion('1.0')
    .addBearerAuth()
    .build();
  
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api/docs', app, document);

  const port = process.env.PORT || 3001;
  await app.listen(port);

  logger.info(`User Service started successfully`, { 
    port, 
    environment: process.env.NODE_ENV,
    docsUrl: `http://localhost:${port}/api/docs`
  });
}

bootstrap().catch(error => {
  console.error('Failed to start User Service:', error);
  process.exit(1);
});
```

---

## 🐳 **9. Docker Configuration**

### **Dockerfile**
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build application
RUN pnpm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install only production dependencies
RUN pnpm install --frozen-lockfile --prod

# Copy built application
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nestjs -u 1001

USER nestjs

EXPOSE 3001

CMD ["node", "dist/main"]
```

### **Docker Compose for Development**
```yaml
# docker-compose.yml
version: '3.8'

services:
  user-service:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/user_service
      - RABBITMQ_URL=amqp://rabbitmq:5672
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=development-secret-key
    depends_on:
      - postgres
      - rabbitmq
      - redis
    volumes:
      - .:/app
      - /app/node_modules
    command: pnpm run start:dev

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=user_service
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS=password

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## ✅ **10. Validation & Testing**

### **Install Dependencies**
```bash
pnpm install
```

### **Start Development Environment**
```bash
docker-compose up -d
pnpm run start:dev
```

### **Test API Endpoints**
```bash
# Health check
curl http://localhost:3001/health

# API documentation
open http://localhost:3001/api/docs

# Create user (you'll need to implement auth first)
curl -X POST http://localhost:3001/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!","firstName":"John","lastName":"Doe"}'
```

---

## 🎉 **Success!**

You've successfully created a User Service that:

✅ **Uses all shared libraries** for consistent patterns
✅ **Implements proper domain-driven design** with clean architecture
✅ **Has comprehensive authentication and authorization**
✅ **Publishes domain events** using transactional outbox pattern
✅ **Includes proper logging and error handling**
✅ **Has API documentation** with Swagger
✅ **Is containerized** and ready for deployment

---

## 🔗 **Next Steps**

1. **[Authentication Implementation](./02-authentication-implementation.md)** - Add login/logout endpoints
2. **[Role Management](./03-role-management.md)** - Implement role assignment
3. **[Testing Strategy](./04-testing-implementation.md)** - Comprehensive test suite
4. **[Integration Testing](./05-integration-testing.md)** - End-to-end testing

Your User Service is now the foundation for your entire microservices platform! 🚀