# Configuration and Health Check Module

## Overview

Build configuration management utilities with environment validation and health check modules for monitoring service dependencies and system status.

## 🎯 Learning Objectives

- Create type-safe configuration management
- Implement environment validation schemas
- Build comprehensive health check indicators
- Create Kubernetes-ready health endpoints
- Monitor external service dependencies

---

## Step 1: Configuration Management

### 1.1 Create Configuration Schema

```typescript
// src/config/validation.schemas.ts
import * as Joi from 'joi';

export const validationSchema = Joi.object({
  // Application settings
  NODE_ENV: Joi.string()
    .valid('development', 'test', 'staging', 'production')
    .default('development'),
  
  PORT: Joi.number().default(3000),
  
  LOG_LEVEL: Joi.string()
    .valid('error', 'warn', 'info', 'debug', 'verbose')
    .default('info'),
    
  // Database configuration
  DATABASE_URL: Joi.string().required(),
  DATABASE_HOST: Joi.string().when('DATABASE_URL', {
    is: Joi.exist(),
    then: Joi.optional(),
    otherwise: Joi.required()
  }),
  DATABASE_PORT: Joi.number().default(5432),
  DATABASE_NAME: Joi.string().when('DATABASE_URL', {
    is: Joi.exist(),
    then: Joi.optional(),
    otherwise: Joi.required()
  }),
  DATABASE_USERNAME: Joi.string().when('DATABASE_URL', {
    is: Joi.exist(),
    then: Joi.optional(),
    otherwise: Joi.required()
  }),
  DATABASE_PASSWORD: Joi.string().when('DATABASE_URL', {
    is: Joi.exist(),
    then: Joi.optional(),
    otherwise: Joi.required()
  }),
  
  // JWT Configuration
  JWT_SECRET: Joi.string().required(),
  JWT_EXPIRES_IN: Joi.string().default('15m'),
  JWT_REFRESH_EXPIRES_IN: Joi.string().default('7d'),
  
  // Cache configuration
  REDIS_URL: Joi.string().required(),
  REDIS_HOST: Joi.string().when('REDIS_URL', {
    is: Joi.exist(),
    then: Joi.optional(),
    otherwise: Joi.required()
  }),
  REDIS_PORT: Joi.number().default(6379),
  REDIS_PASSWORD: Joi.string().optional(),
  
  // Message queue configuration
  RABBITMQ_URL: Joi.string().required(),
  RABBITMQ_HOST: Joi.string().when('RABBITMQ_URL', {
    is: Joi.exist(),
    then: Joi.optional(),
    otherwise: Joi.required()
  }),
  RABBITMQ_PORT: Joi.number().default(5672),
  RABBITMQ_USERNAME: Joi.string().default('guest'),
  RABBITMQ_PASSWORD: Joi.string().default('guest'),
  
  // External services
  EMAIL_SERVICE_URL: Joi.string().optional(),
  EMAIL_API_KEY: Joi.string().optional(),
  
  // Security
  CORS_ORIGIN: Joi.string().default('*'),
  RATE_LIMIT_TTL: Joi.number().default(60),
  RATE_LIMIT_LIMIT: Joi.number().default(100),
  
  // Monitoring
  HEALTH_CHECK_TIMEOUT: Joi.number().default(5000),
  METRICS_ENABLED: Joi.boolean().default(true)
});
```

### 1.2 Create Configuration Types

```typescript
// src/config/config.types.ts
export interface DatabaseConfig {
  url?: string;
  host?: string;
  port?: number;
  name?: string;
  username?: string;
  password?: string;
}

export interface JwtConfig {
  secret: string;
  expiresIn: string;
  refreshExpiresIn: string;
}

export interface RedisConfig {
  url?: string;
  host?: string;
  port?: number;
  password?: string;
}

export interface RabbitMQConfig {
  url?: string;
  host?: string;
  port?: number;
  username?: string;
  password?: string;
}

export interface SecurityConfig {
  corsOrigin: string;
  rateLimitTtl: number;
  rateLimitLimit: number;
}

export interface AppConfig {
  nodeEnv: string;
  port: number;
  logLevel: string;
  database: DatabaseConfig;
  jwt: JwtConfig;
  redis: RedisConfig;
  rabbitmq: RabbitMQConfig;
  security: SecurityConfig;
  healthCheckTimeout: number;
  metricsEnabled: boolean;
}
```

### 1.3 Create Configuration Service

```typescript
// src/config/config.service.ts
import { Injectable } from '@nestjs/common';
import { ConfigService as NestConfigService } from '@nestjs/config';
import { 
  AppConfig, 
  DatabaseConfig, 
  JwtConfig, 
  RedisConfig, 
  RabbitMQConfig,
  SecurityConfig 
} from './config.types';

@Injectable()
export class AppConfigService {
  constructor(private configService: NestConfigService) {}

  get app(): AppConfig {
    return {
      nodeEnv: this.configService.get<string>('NODE_ENV', 'development'),
      port: this.configService.get<number>('PORT', 3000),
      logLevel: this.configService.get<string>('LOG_LEVEL', 'info'),
      database: this.database,
      jwt: this.jwt,
      redis: this.redis,
      rabbitmq: this.rabbitmq,
      security: this.security,
      healthCheckTimeout: this.configService.get<number>('HEALTH_CHECK_TIMEOUT', 5000),
      metricsEnabled: this.configService.get<boolean>('METRICS_ENABLED', true)
    };
  }

  get database(): DatabaseConfig {
    return {
      url: this.configService.get<string>('DATABASE_URL'),
      host: this.configService.get<string>('DATABASE_HOST'),
      port: this.configService.get<number>('DATABASE_PORT', 5432),
      name: this.configService.get<string>('DATABASE_NAME'),
      username: this.configService.get<string>('DATABASE_USERNAME'),
      password: this.configService.get<string>('DATABASE_PASSWORD')
    };
  }

  get jwt(): JwtConfig {
    return {
      secret: this.configService.get<string>('JWT_SECRET'),
      expiresIn: this.configService.get<string>('JWT_EXPIRES_IN', '15m'),
      refreshExpiresIn: this.configService.get<string>('JWT_REFRESH_EXPIRES_IN', '7d')
    };
  }

  get redis(): RedisConfig {
    return {
      url: this.configService.get<string>('REDIS_URL'),
      host: this.configService.get<string>('REDIS_HOST'),
      port: this.configService.get<number>('REDIS_PORT', 6379),
      password: this.configService.get<string>('REDIS_PASSWORD')
    };
  }

  get rabbitmq(): RabbitMQConfig {
    return {
      url: this.configService.get<string>('RABBITMQ_URL'),
      host: this.configService.get<string>('RABBITMQ_HOST'),
      port: this.configService.get<number>('RABBITMQ_PORT', 5672),
      username: this.configService.get<string>('RABBITMQ_USERNAME', 'guest'),
      password: this.configService.get<string>('RABBITMQ_PASSWORD', 'guest')
    };
  }

  get security(): SecurityConfig {
    return {
      corsOrigin: this.configService.get<string>('CORS_ORIGIN', '*'),
      rateLimitTtl: this.configService.get<number>('RATE_LIMIT_TTL', 60),
      rateLimitLimit: this.configService.get<number>('RATE_LIMIT_LIMIT', 100)
    };
  }

  get isDevelopment(): boolean {
    return this.app.nodeEnv === 'development';
  }

  get isProduction(): boolean {
    return this.app.nodeEnv === 'production';
  }

  get isTest(): boolean {
    return this.app.nodeEnv === 'test';
  }
}
```

### 1.4 Create Configuration Module

```typescript
// src/config/config.module.ts
import { Global, Module } from '@nestjs/common';
import { ConfigModule as NestConfigModule } from '@nestjs/config';
import { validationSchema } from './validation.schemas';
import { AppConfigService } from './config.service';

@Global()
@Module({
  imports: [
    NestConfigModule.forRoot({
      isGlobal: true,
      validationSchema,
      validationOptions: {
        allowUnknown: true,
        abortEarly: false
      },
      envFilePath: [
        `.env.${process.env.NODE_ENV || 'development'}`,
        '.env'
      ]
    })
  ],
  providers: [AppConfigService],
  exports: [AppConfigService]
})
export class ConfigModule {}
```

---

## Step 2: Health Check Implementation

### 2.1 Create Custom Health Indicators

```typescript
// src/health/indicators/redis.health.ts
import { Injectable } from '@nestjs/common';
import { HealthIndicator, HealthIndicatorResult, HealthCheckError } from '@nestjs/terminus';
import Redis from 'ioredis';
import { AppConfigService } from '../../config/config.service';

@Injectable()
export class RedisHealthIndicator extends HealthIndicator {
  private redis: Redis;

  constructor(private configService: AppConfigService) {
    super();
    const redisConfig = this.configService.redis;
    this.redis = new Redis(redisConfig.url || {
      host: redisConfig.host,
      port: redisConfig.port,
      password: redisConfig.password,
      retryDelayOnFailover: 100,
      enableReadyCheck: false,
      maxRetriesPerRequest: null
    });
  }

  async isHealthy(key: string): Promise<HealthIndicatorResult> {
    try {
      const start = Date.now();
      const result = await this.redis.ping();
      const duration = Date.now() - start;
      
      if (result === 'PONG') {
        return this.getStatus(key, true, {
          message: 'Redis is available',
          responseTime: `${duration}ms`
        });
      } else {
        throw new Error('Redis ping failed');
      }
    } catch (error) {
      throw new HealthCheckError(
        'Redis check failed',
        this.getStatus(key, false, {
          message: error.message
        })
      );
    }
  }
}
```

```typescript
// src/health/indicators/rabbitmq.health.ts
import { Injectable } from '@nestjs/common';
import { HealthIndicator, HealthIndicatorResult, HealthCheckError } from '@nestjs/terminus';
import * as amqp from 'amqplib';
import { AppConfigService } from '../../config/config.service';

@Injectable()
export class RabbitMQHealthIndicator extends HealthIndicator {
  constructor(private configService: AppConfigService) {
    super();
  }

  async isHealthy(key: string): Promise<HealthIndicatorResult> {
    try {
      const start = Date.now();
      const rabbitmqConfig = this.configService.rabbitmq;
      
      const connection = await amqp.connect(
        rabbitmqConfig.url || {
          hostname: rabbitmqConfig.host,
          port: rabbitmqConfig.port,
          username: rabbitmqConfig.username,
          password: rabbitmqConfig.password
        }
      );
      
      await connection.close();
      const duration = Date.now() - start;
      
      return this.getStatus(key, true, {
        message: 'RabbitMQ is available',
        responseTime: `${duration}ms`
      });
    } catch (error) {
      throw new HealthCheckError(
        'RabbitMQ check failed',
        this.getStatus(key, false, {
          message: error.message
        })
      );
    }
  }
}
```

### 2.2 Create Health Controller

```typescript
// src/health/health.controller.ts
import { Controller, Get } from '@nestjs/common';
import {
  HealthCheckService,
  HealthCheck,
  TypeOrmHealthIndicator,
  MemoryHealthIndicator,
  DiskHealthIndicator
} from '@nestjs/terminus';
import { RedisHealthIndicator } from './indicators/redis.health';
import { RabbitMQHealthIndicator } from './indicators/rabbitmq.health';
import { AppConfigService } from '../config/config.service';

@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private db: TypeOrmHealthIndicator,
    private memory: MemoryHealthIndicator,
    private disk: DiskHealthIndicator,
    private redis: RedisHealthIndicator,
    private rabbitmq: RabbitMQHealthIndicator,
    private configService: AppConfigService
  ) {}

  @Get()
  @HealthCheck()
  check() {
    const timeout = this.configService.app.healthCheckTimeout;
    
    return this.health.check([
      () => this.db.pingCheck('database', { timeout }),
      () => this.redis.isHealthy('redis'),
      () => this.rabbitmq.isHealthy('rabbitmq'),
      () => this.memory.checkHeap('memory_heap', 150 * 1024 * 1024),
      () => this.memory.checkRSS('memory_rss', 150 * 1024 * 1024),
      () => this.disk.checkStorage('storage', { 
        thresholdPercent: 0.9, 
        path: '/' 
      })
    ]);
  }

  @Get('ready')
  @HealthCheck()
  readiness() {
    // Readiness probe - check if service can handle requests
    return this.health.check([
      () => this.db.pingCheck('database'),
      () => this.redis.isHealthy('redis')
    ]);
  }

  @Get('live')
  @HealthCheck()
  liveness() {
    // Liveness probe - check if service is alive
    return this.health.check([
      () => this.memory.checkHeap('memory_heap', 200 * 1024 * 1024),
      () => this.disk.checkStorage('storage', { 
        thresholdPercent: 0.95, 
        path: '/' 
      })
    ]);
  }

  @Get('startup')
  @HealthCheck()
  startup() {
    // Startup probe - check if service has started successfully
    return this.health.check([
      () => this.db.pingCheck('database'),
      () => this.redis.isHealthy('redis'),
      () => this.rabbitmq.isHealthy('rabbitmq')
    ]);
  }
}
```

### 2.3 Create Health Module

```typescript
// src/health/health.module.ts
import { Module } from '@nestjs/common';
import { TerminusModule } from '@nestjs/terminus';
import { HealthController } from './health.controller';
import { RedisHealthIndicator } from './indicators/redis.health';
import { RabbitMQHealthIndicator } from './indicators/rabbitmq.health';

@Module({
  imports: [TerminusModule],
  controllers: [HealthController],
  providers: [
    RedisHealthIndicator,
    RabbitMQHealthIndicator
  ],
  exports: [
    RedisHealthIndicator,
    RabbitMQHealthIndicator
  ]
})
export class HealthModule {}
```

---

## Step 3: Common Decorators

### 3.1 Create API Response Decorators

```typescript
// src/decorators/api-response.decorator.ts
import { applyDecorators, Type } from '@nestjs/common';
import { ApiResponse, ApiProperty } from '@nestjs/swagger';

export class BaseResponse<T> {
  @ApiProperty({ example: true })
  success: boolean;

  @ApiProperty({ example: 'Operation completed successfully' })
  message: string;

  @ApiProperty({ example: '2023-12-01T12:00:00.000Z' })
  timestamp: string;

  @ApiProperty({ example: 'uuid-correlation-id' })
  correlationId?: string;

  data: T;
}

export class PaginatedResponse<T> extends BaseResponse<T[]> {
  @ApiProperty({
    type: 'object',
    properties: {
      page: { type: 'number', example: 1 },
      limit: { type: 'number', example: 10 },
      total: { type: 'number', example: 100 },
      hasNextPage: { type: 'boolean', example: true },
      hasPreviousPage: { type: 'boolean', example: false }
    }
  })
  metadata: {
    page: number;
    limit: number;
    total: number;
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
}

export class ErrorResponse {
  @ApiProperty({ example: false })
  success: boolean;

  @ApiProperty({ example: 400 })
  statusCode: number;

  @ApiProperty({ example: 'Validation failed' })
  message: string;

  @ApiProperty({ example: 'VALIDATION_ERROR' })
  errorCode: string;

  @ApiProperty({ example: '2023-12-01T12:00:00.000Z' })
  timestamp: string;

  @ApiProperty({ example: '/api/users' })
  path: string;

  @ApiProperty({ example: 'POST' })
  method: string;

  @ApiProperty({ example: 'uuid-correlation-id' })
  correlationId?: string;

  @ApiProperty()
  metadata?: Record<string, any>;
}

export const ApiSuccessResponse = <TModel extends Type<any>>(
  model: TModel,
  description?: string,
  isArray?: boolean
) => {
  return applyDecorators(
    ApiResponse({
      status: 200,
      description: description || 'Success',
      schema: {
        allOf: [
          { $ref: '#/components/schemas/BaseResponse' },
          {
            properties: {
              data: isArray 
                ? { type: 'array', items: { $ref: `#/components/schemas/${model.name}` } }
                : { $ref: `#/components/schemas/${model.name}` }
            }
          }
        ]
      }
    })
  );
};

export const ApiPaginatedResponse = <TModel extends Type<any>>(
  model: TModel,
  description?: string
) => {
  return applyDecorators(
    ApiResponse({
      status: 200,
      description: description || 'Paginated success',
      schema: {
        allOf: [
          { $ref: '#/components/schemas/PaginatedResponse' },
          {
            properties: {
              data: {
                type: 'array',
                items: { $ref: `#/components/schemas/${model.name}` }
              }
            }
          }
        ]
      }
    })
  );
};

export const ApiErrorResponse = (
  status: number,
  description: string,
  errorCode?: string
) => {
  return applyDecorators(
    ApiResponse({
      status,
      description,
      schema: {
        allOf: [
          { $ref: '#/components/schemas/ErrorResponse' },
          errorCode ? {
            properties: {
              errorCode: { example: errorCode }
            }
          } : {}
        ]
      }
    })
  );
};
```

### 3.2 Create Performance Decorator

```typescript
// src/decorators/performance.decorator.ts
import { SetMetadata } from '@nestjs/common';

export const PERFORMANCE_METADATA_KEY = 'performance';

export interface PerformanceOptions {
  logSlowRequests?: boolean;
  slowThreshold?: number; // in milliseconds
  trackMemory?: boolean;
}

export const Performance = (options: PerformanceOptions = {}) =>
  SetMetadata(PERFORMANCE_METADATA_KEY, {
    logSlowRequests: options.logSlowRequests ?? true,
    slowThreshold: options.slowThreshold ?? 1000,
    trackMemory: options.trackMemory ?? false
  });
```

---

## Step 4: Export All Components

```typescript
// src/config/index.ts
export * from './config.service';
export * from './config.module';
export * from './config.types';
export * from './validation.schemas';

// src/health/index.ts
export * from './health.controller';
export * from './health.module';
export * from './indicators/redis.health';
export * from './indicators/rabbitmq.health';

// src/decorators/index.ts
export * from './api-response.decorator';
export * from './performance.decorator';
```

---

## Step 5: Create Tests

### 5.1 Test Configuration Service

```typescript
// src/config/config.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { ConfigModule } from '@nestjs/config';
import { AppConfigService } from './config.service';

describe('AppConfigService', () => {
  let service: AppConfigService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({
          envFilePath: '.env.test'
        })
      ],
      providers: [AppConfigService]
    }).compile();

    service = module.get<AppConfigService>(AppConfigService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should return app configuration', () => {
    const config = service.app;
    expect(config).toBeDefined();
    expect(config.nodeEnv).toBeDefined();
    expect(config.port).toBeDefined();
  });

  it('should identify development environment', () => {
    process.env.NODE_ENV = 'development';
    expect(service.isDevelopment).toBe(true);
    expect(service.isProduction).toBe(false);
  });
});
```

---

## Step 6: Update Main Exports

```typescript
// src/index.ts
// Logging exports
export * from './logging';

// Exception handling exports
export * from './exceptions';

// Interceptors
export * from './interceptors';

// Validation
export * from './validation';

// Configuration
export * from './config';

// Health checks
export * from './health';

// Decorators
export * from './decorators';
```

---

## Step 7: Build and Test

```bash
# Run tests
npm test

# Build the package
npm run build

# Verify health endpoints work (when integrated)
curl http://localhost:3000/health
curl http://localhost:3000/health/ready
curl http://localhost:3000/health/live
```

---

## 🎯 Key Accomplishments

✅ **Type-safe configuration** with environment validation  
✅ **Comprehensive health checks** for all dependencies  
✅ **Kubernetes-ready endpoints** (ready, live, startup probes)  
✅ **Custom health indicators** for Redis and RabbitMQ  
✅ **API documentation helpers** with standardized responses  
✅ **Performance monitoring** decorators  

---

## 🔗 Next Steps

Continue with **[04-final-integration.md](./04-final-integration.md)** to put everything together and create the complete shared library package.

---

## 💡 Usage Preview

```typescript
// In your service
import { 
  AppConfigService, 
  HealthModule,
  ApiSuccessResponse 
} from '@ecommerce/nestjs-core-utils';

@Module({
  imports: [HealthModule],
  // ...
})
export class AppModule {}

@Controller('users')
export class UserController {
  constructor(private config: AppConfigService) {}
  
  @Get()
  @ApiSuccessResponse(UserDto, 'Users retrieved successfully', true)
  async getUsers() {
    // Implementation using config.database, etc.
  }
}
```