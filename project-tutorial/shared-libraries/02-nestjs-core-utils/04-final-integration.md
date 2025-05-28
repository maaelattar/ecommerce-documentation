# Final Integration and Package Completion

## Overview

Complete the NestJS Core Utils package by integrating all modules, creating the main entry point, and providing comprehensive usage examples for consuming services.

## 🎯 Learning Objectives

- Integrate all utility modules into a cohesive package
- Create a comprehensive main module for easy import
- Document package usage patterns
- Provide complete integration examples
- Set up package publishing and versioning

---

## Step 1: Create Main Core Module

### 1.1 Create the Core Utils Module

```typescript
// src/core-utils.module.ts
import { DynamicModule, Global, Module } from '@nestjs/common';
import { APP_FILTER, APP_INTERCEPTOR, APP_PIPE } from '@nestjs/core';

// Module imports
import { LoggerModule } from './logging/logger.module';
import { ConfigModule } from './config/config.module';
import { HealthModule } from './health/health.module';

// Services and utilities
import { AppLoggerService } from './logging/logger.service';
import { AppConfigService } from './config/config.service';
import { GlobalExceptionFilter } from './exceptions/global-exception.filter';
import { TransformInterceptor } from './interceptors/transform.interceptor';
import { LoggingInterceptor } from './interceptors/logging.interceptor';
import { CustomValidationPipe } from './validation/validation.pipe';

export interface CoreUtilsModuleOptions {
  enableGlobalFilters?: boolean;
  enableGlobalInterceptors?: boolean;
  enableGlobalPipes?: boolean;
  enableLogging?: boolean;
  enableHealthChecks?: boolean;
}

@Global()
@Module({})
export class CoreUtilsModule {
  static forRoot(options: CoreUtilsModuleOptions = {}): DynamicModule {
    const {
      enableGlobalFilters = true,
      enableGlobalInterceptors = true,
      enableGlobalPipes = true,
      enableLogging = true,
      enableHealthChecks = true
    } = options;

    const imports = [ConfigModule];
    const providers = [AppConfigService];
    const exports = [AppConfigService];

    // Add logging if enabled
    if (enableLogging) {
      imports.push(LoggerModule);
      providers.push(AppLoggerService);
      exports.push(AppLoggerService);
    }

    // Add health checks if enabled
    if (enableHealthChecks) {
      imports.push(HealthModule);
    }

    // Global providers
    const globalProviders = [];

    if (enableGlobalFilters) {
      globalProviders.push({
        provide: APP_FILTER,
        useClass: GlobalExceptionFilter
      });
    }

    if (enableGlobalInterceptors) {
      globalProviders.push(
        {
          provide: APP_INTERCEPTOR,
          useClass: LoggingInterceptor
        },
        {
          provide: APP_INTERCEPTOR,
          useClass: TransformInterceptor
        }
      );
    }

    if (enableGlobalPipes) {
      globalProviders.push({
        provide: APP_PIPE,
        useClass: CustomValidationPipe
      });
    }

    return {
      module: CoreUtilsModule,
      imports,
      providers: [...providers, ...globalProviders],
      exports
    };
  }

  static forFeature(): DynamicModule {
    // For feature modules that only need specific utilities
    return {
      module: CoreUtilsModule,
      providers: [AppLoggerService, AppConfigService],
      exports: [AppLoggerService, AppConfigService]
    };
  }
}
```

### 1.2 Update Main Index File

```typescript
// src/index.ts
// Main module export
export * from './core-utils.module';

// Logging exports
export * from './logging';

// Configuration exports
export * from './config';

// Exception handling exports
export * from './exceptions';

// Interceptors exports
export * from './interceptors';

// Validation exports
export * from './validation';

// Health checks exports
export * from './health';

// Decorators exports
export * from './decorators';

// Re-export commonly used types from dependencies
export { HttpStatus, HttpException } from '@nestjs/common';
export { ConfigService } from '@nestjs/config';
export { 
  HealthCheckService, 
  HealthIndicator, 
  HealthIndicatorResult,
  HealthCheckError 
} from '@nestjs/terminus';
```

---

## Step 2: Create Usage Examples

### 2.1 Basic Service Integration Example

```typescript
// examples/basic-service.example.ts
import { Module, Injectable, Controller, Get, Post, Body } from '@nestjs/common';
import { 
  CoreUtilsModule, 
  AppLoggerService, 
  AppConfigService,
  ApiSuccessResponse,
  BusinessException
} from '@ecommerce/nestjs-core-utils';

// Example DTO
export class CreateUserDto {
  name: string;
  email: string;
}

// Example response DTO
export class UserDto {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

@Injectable()
export class UserService {
  constructor(
    private readonly logger: AppLoggerService,
    private readonly config: AppConfigService
  ) {
    // Set service context for logging
    this.logger.setContext({ serviceName: 'UserService' });
  }

  async createUser(createUserDto: CreateUserDto): Promise<UserDto> {
    this.logger.info('Creating new user', { email: createUserDto.email });

    try {
      // Simulate business logic
      if (await this.userExists(createUserDto.email)) {
        throw new BusinessException(
          'User with this email already exists',
          'USER_ALREADY_EXISTS',
          409,
          { email: createUserDto.email }
        );
      }

      // Simulate user creation
      const user: UserDto = {
        id: 'user-123',
        name: createUserDto.name,
        email: createUserDto.email,
        createdAt: new Date()
      };

      this.logger.info('User created successfully', { userId: user.id });
      return user;

    } catch (error) {
      this.logger.error('Failed to create user', error, { email: createUserDto.email });
      throw error;
    }
  }

  async getUsers(): Promise<UserDto[]> {
    this.logger.info('Fetching all users');
    
    // Simulate fetching users
    const users: UserDto[] = [
      {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
        createdAt: new Date()
      }
    ];

    this.logger.info('Users fetched successfully', { count: users.length });
    return users;
  }

  private async userExists(email: string): Promise<boolean> {
    // Simulate database check
    return email === 'existing@example.com';
  }
}

@Controller('users')
export class UserController {
  constructor(
    private readonly userService: UserService,
    private readonly logger: AppLoggerService
  ) {
    this.logger.setContext({ serviceName: 'UserController' });
  }

  @Post()
  @ApiSuccessResponse(UserDto, 'User created successfully')
  async createUser(@Body() createUserDto: CreateUserDto): Promise<UserDto> {
    return this.userService.createUser(createUserDto);
  }

  @Get()
  @ApiSuccessResponse(UserDto, 'Users retrieved successfully', true)
  async getUsers(): Promise<UserDto[]> {
    return this.userService.getUsers();
  }
}

@Module({
  imports: [
    CoreUtilsModule.forRoot({
      enableGlobalFilters: true,
      enableGlobalInterceptors: true,
      enableGlobalPipes: true,
      enableLogging: true,
      enableHealthChecks: true
    })
  ],
  controllers: [UserController],
  providers: [UserService]
})
export class ExampleAppModule {}
```

### 2.2 Custom Health Indicator Example

```typescript
// examples/custom-health.example.ts
import { Injectable } from '@nestjs/common';
import { 
  HealthIndicator, 
  HealthIndicatorResult, 
  HealthCheckError 
} from '@ecommerce/nestjs-core-utils';

@Injectable()
export class CustomServiceHealthIndicator extends HealthIndicator {
  constructor() {
    super();
  }

  async isHealthy(key: string): Promise<HealthIndicatorResult> {
    try {
      // Simulate custom health check logic
      const isServiceUp = await this.checkCustomService();
      
      if (isServiceUp) {
        return this.getStatus(key, true, {
          message: 'Custom service is operational',
          version: '1.0.0'
        });
      } else {
        throw new Error('Custom service is down');
      }
    } catch (error) {
      throw new HealthCheckError(
        'Custom service check failed',
        this.getStatus(key, false, {
          message: error.message
        })
      );
    }
  }

  private async checkCustomService(): Promise<boolean> {
    // Implement your custom health check logic here
    // For example: HTTP request to external service, database query, etc.
    return true;
  }
}
```

### 2.3 Advanced Logging Example

```typescript
// examples/advanced-logging.example.ts
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { AppLoggerService } from '@ecommerce/nestjs-core-utils';

@Injectable()
export class RequestContextMiddleware implements NestMiddleware {
  constructor(private readonly logger: AppLoggerService) {}

  use(req: Request, res: Response, next: NextFunction): void {
    // Extract user information from token (simplified)
    const userId = req.headers['x-user-id'] as string;
    const tenantId = req.headers['x-tenant-id'] as string;

    // Set comprehensive context
    this.logger.setContext({
      correlationId: req.headers['x-correlation-id'] as string,
      userId,
      serviceName: 'UserService',
      operation: `${req.method} ${req.path}`,
      metadata: {
        userAgent: req.headers['user-agent'],
        ip: req.ip,
        tenantId
      }
    });

    next();
  }
}

@Injectable()
export class AdvancedUserService {
  constructor(private readonly logger: AppLoggerService) {}

  async performComplexOperation(userId: string): Promise<void> {
    // Start operation logging
    this.logger.info('Starting complex operation', {
      operation: 'performComplexOperation',
      userId
    });

    try {
      // Step 1
      this.logger.debug('Executing step 1', { step: 1 });
      await this.step1();

      // Step 2
      this.logger.debug('Executing step 2', { step: 2 });
      await this.step2();

      // Success
      this.logger.info('Complex operation completed successfully', {
        operation: 'performComplexOperation',
        userId,
        duration: '1.2s'
      });

    } catch (error) {
      this.logger.error('Complex operation failed', error, {
        operation: 'performComplexOperation',
        userId,
        failurePoint: 'step2'
      });
      throw error;
    }
  }

  private async step1(): Promise<void> {
    // Simulate work
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  private async step2(): Promise<void> {
    // Simulate work that might fail
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}
```

---

## Step 3: Create Documentation

### 3.1 Update README

```markdown
// README.md
# @ecommerce/nestjs-core-utils

Core NestJS utilities package providing logging, error handling, configuration management, health checks, and common decorators for the ecommerce platform.

## 🚀 Quick Start

### Installation

```bash
npm install @ecommerce/nestjs-core-utils
```

### Basic Usage

```typescript
import { CoreUtilsModule } from '@ecommerce/nestjs-core-utils';

@Module({
  imports: [
    CoreUtilsModule.forRoot({
      enableGlobalFilters: true,
      enableGlobalInterceptors: true,
      enableGlobalPipes: true,
      enableLogging: true,
      enableHealthChecks: true
    })
  ]
})
export class AppModule {}
```

## 📦 Features

### ✅ Structured Logging
- JSON logging with correlation IDs
- Context-aware logging
- Environment-based log levels
- Performance timing

### ✅ Error Handling
- Global exception filters
- Custom business exceptions
- Standardized error responses
- Validation error formatting

### ✅ Configuration Management
- Type-safe configuration
- Environment validation
- Default value handling
- Multiple environment support

### ✅ Health Checks
- Database connectivity
- Redis health monitoring
- RabbitMQ health checks
- Kubernetes-ready endpoints

### ✅ Response Transformation
- Standardized API responses
- Pagination support
- Correlation ID tracking
- Request/response logging

## 🔧 Configuration

### Environment Variables

```bash
# Application
NODE_ENV=development
PORT=3000
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql://localhost:5432/db
# or individual components:
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=ecommerce
DATABASE_USERNAME=user
DATABASE_PASSWORD=password

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=15m
JWT_REFRESH_EXPIRES_IN=7d

# Redis
REDIS_URL=redis://localhost:6379
# or individual components:
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=optional

# RabbitMQ
RABBITMQ_URL=amqp://localhost:5672
# or individual components:
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest

# Security
CORS_ORIGIN=*
RATE_LIMIT_TTL=60
RATE_LIMIT_LIMIT=100

# Monitoring
HEALTH_CHECK_TIMEOUT=5000
METRICS_ENABLED=true
```

## 📖 Usage Examples

### Logging Service

```typescript
import { AppLoggerService } from '@ecommerce/nestjs-core-utils';

@Injectable()
export class UserService {
  constructor(private logger: AppLoggerService) {
    this.logger.setContext({ serviceName: 'UserService' });
  }
  
  async createUser(userData: CreateUserDto) {
    this.logger.info('Creating user', { email: userData.email });
    // Implementation...
  }
}
```

### Configuration Service

```typescript
import { AppConfigService } from '@ecommerce/nestjs-core-utils';

@Injectable()
export class DatabaseService {
  constructor(private config: AppConfigService) {
    const dbConfig = this.config.database;
    // Use dbConfig.url, dbConfig.host, etc.
  }
}
```

### Custom Exceptions

```typescript
import { BusinessException } from '@ecommerce/nestjs-core-utils';

throw new BusinessException(
  'User not found',
  'USER_NOT_FOUND',
  404,
  { userId: '123' }
);
```

### API Response Decorators

```typescript
import { ApiSuccessResponse } from '@ecommerce/nestjs-core-utils';

@Controller('users')
export class UserController {
  @Get()
  @ApiSuccessResponse(UserDto, 'Users retrieved', true)
  async getUsers(): Promise<UserDto[]> {
    return this.userService.getUsers();
  }
}
```

## 🏥 Health Endpoints

The package automatically provides these health check endpoints:

- `GET /health` - Comprehensive health check
- `GET /health/ready` - Readiness probe (Kubernetes)
- `GET /health/live` - Liveness probe (Kubernetes)  
- `GET /health/startup` - Startup probe (Kubernetes)

## 🎯 Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "timestamp": "2023-12-01T12:00:00.000Z",
  "correlationId": "uuid-here"
}
```

### Error Response
```json
{
  "success": false,
  "statusCode": 400,
  "message": "Validation failed",
  "errorCode": "VALIDATION_ERROR",
  "timestamp": "2023-12-01T12:00:00.000Z",
  "path": "/api/users",
  "method": "POST",
  "correlationId": "uuid-here",
  "metadata": {
    "validationErrors": [...]
  }
}
```

## 🧪 Testing

```bash
npm test
```

## 🏗️ Building

```bash
npm run build
```

## 📝 License

MIT
```

### 3.2 Create CHANGELOG

```markdown
// CHANGELOG.md
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2023-12-01

### Added
- Initial release of @ecommerce/nestjs-core-utils
- Structured logging with Winston integration
- Global exception handling with custom business exceptions
- Type-safe configuration management with validation
- Comprehensive health check indicators
- Response transformation interceptors
- Correlation ID middleware
- API documentation decorators
- Custom validation pipes

### Features
- **Logging Module**: JSON logging, correlation IDs, context-aware logging
- **Error Handling**: Global filters, custom exceptions, standardized responses
- **Configuration**: Environment validation, type-safe config service
- **Health Checks**: Database, Redis, RabbitMQ, system resource monitoring
- **Interceptors**: Response transformation, request logging, performance tracking
- **Decorators**: API response documentation, performance monitoring

### Documentation
- Complete setup and integration guides
- Usage examples for all features
- Environment configuration reference
- Health endpoint documentation
```

---

## Step 4: Final Package Configuration

### 4.1 Update package.json with Scripts and Metadata

```json
{
  "name": "@ecommerce/nestjs-core-utils",
  "version": "1.0.0",
  "description": "Core NestJS utilities for the ecommerce platform including logging, error handling, configuration, and health checks",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist",
    "README.md",
    "CHANGELOG.md"
  ],
  "scripts": {
    "build": "tsc",
    "build:watch": "tsc --watch",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix",
    "prepublishOnly": "npm run build && npm test"
  },
  "keywords": [
    "nestjs",
    "utilities",
    "logging",
    "error-handling",
    "configuration",
    "health-checks",
    "ecommerce",
    "microservices"
  ],
  "author": "Ecommerce Platform Team",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "git+https://github.com/ecommerce-platform/nestjs-core-utils.git"
  },
  "bugs": {
    "url": "https://github.com/ecommerce-platform/nestjs-core-utils/issues"
  },
  "homepage": "https://github.com/ecommerce-platform/nestjs-core-utils#readme",
  "peerDependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/config": "^3.0.0",
    "@nestjs/terminus": "^10.0.0"
  },
  "dependencies": {
    "winston": "^3.11.0",
    "nest-winston": "^1.9.4",
    "class-validator": "^0.14.0",
    "class-transformer": "^0.5.1",
    "joi": "^17.11.0",
    "uuid": "^9.0.1",
    "ioredis": "^5.3.2",
    "amqplib": "^0.10.3"
  },
  "devDependencies": {
    "@types/uuid": "^9.0.7",
    "@types/amqplib": "^0.10.4",
    "typescript": "^5.2.2",
    "jest": "^29.7.0",
    "@types/jest": "^29.5.8",
    "ts-jest": "^29.1.1",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "eslint": "^8.53.0"
  },
  "jest": {
    "moduleFileExtensions": ["js", "json", "ts"],
    "rootDir": "src",
    "testRegex": ".*\\.spec\\.ts$",
    "transform": {
      "^.+\\.(t|j)s$": "ts-jest"
    },
    "collectCoverageFrom": [
      "**/*.(t|j)s"
    ],
    "coverageDirectory": "../coverage",
    "testEnvironment": "node"
  }
}
```

---

## Step 5: Build and Verify

### 5.1 Run Final Build and Tests

```bash
# Install all dependencies
npm install

# Run tests
npm test

# Run build
npm run build

# Verify package structure
ls -la dist/
```

### 5.2 Test Package Integration

Create a test application to verify the package works:

```typescript
// test-app/app.module.ts
import { Module } from '@nestjs/common';
import { CoreUtilsModule } from '../dist';

@Module({
  imports: [
    CoreUtilsModule.forRoot({
      enableGlobalFilters: true,
      enableGlobalInterceptors: true,
      enableHealthChecks: true
    })
  ]
})
export class TestAppModule {}
```

---

## 🎯 Key Accomplishments

✅ **Integrated core utilities module** with flexible configuration options  
✅ **Comprehensive documentation** with usage examples  
✅ **Package configuration** ready for publishing  
✅ **Health endpoints** for Kubernetes deployment  
✅ **Type-safe exports** for all utilities  
✅ **Test coverage** for all components  

---

## 🔗 Next Steps

This completes the NestJS Core Utils shared library! You can now:

1. **Publish to npm**: `npm publish` (after setting up npm registry)
2. **Use in services**: Install and import in your microservices
3. **Extend functionality**: Add more utilities as needed
4. **Version management**: Follow semantic versioning for updates

---

## 💡 Integration in Services

Once published, services can use it like this:

```typescript
// In any microservice
import { Module } from '@nestjs/common';
import { CoreUtilsModule } from '@ecommerce/nestjs-core-utils';

@Module({
  imports: [
    CoreUtilsModule.forRoot({
      enableGlobalFilters: true,
      enableGlobalInterceptors: true,
      enableHealthChecks: true
    })
  ]
})
export class UserServiceModule {}
```

The shared library provides consistent patterns across all services while reducing code duplication and ensuring standardized error handling, logging, and configuration management.