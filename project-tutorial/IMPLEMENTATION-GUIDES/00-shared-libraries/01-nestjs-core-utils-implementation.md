# NestJS Core Utils Implementation Guide 🛠️

> **Goal**: Build foundational utilities that every microservice will use for logging, error handling, configuration, and health checks

---

## 🎯 **What You'll Build**

A comprehensive NestJS utilities library with:
- **Structured logging** with correlation IDs and context
- **Centralized error handling** with custom exceptions
- **Configuration management** with environment validation
- **Health checks** with dependency monitoring
- **Common decorators** and interceptors for cross-cutting concerns

---

## 📦 **Package Setup**

### **1. Initialize Package**
```bash
cd packages/nestjs-core-utils
npm init -y
```

### **2. Package.json Configuration**
```json
{
  "name": "@ecommerce/nestjs-core-utils",
  "version": "1.0.0",
  "description": "Core NestJS utilities for ecommerce microservices",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "test:watch": "jest --watch",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/config": "^3.0.0",
    "@nestjs/terminus": "^10.0.0",
    "winston": "^3.10.0",
    "nest-winston": "^1.9.0",
    "class-validator": "^0.14.0",
    "class-transformer": "^0.5.0",
    "joi": "^17.9.0",
    "uuid": "^9.0.0"
  },
  "devDependencies": {
    "@types/uuid": "^9.0.0",
    "jest": "^29.0.0",
    "typescript": "^5.0.0"
  }
}
```

---

## 🏗️ **Implementation Structure**

```
packages/nestjs-core-utils/
├── src/
│   ├── logging/
│   │   ├── logger.module.ts
│   │   ├── logger.service.ts
│   │   ├── correlation.middleware.ts
│   │   └── index.ts
│   ├── errors/
│   │   ├── exceptions/
│   │   ├── filters/
│   │   └── index.ts
│   ├── config/
│   │   ├── config.module.ts
│   │   ├── validation.schemas.ts
│   │   └── index.ts
│   ├── health/
│   │   ├── health.module.ts
│   │   ├── health.controller.ts
│   │   └── index.ts
│   ├── decorators/
│   ├── interceptors/
│   └── index.ts
└── tests/
```

---

## 🪵 **1. Logging Module Implementation**

### **Logger Service**
```typescript
// src/logging/logger.service.ts
import { Injectable, Scope } from '@nestjs/common';
import { createLogger, format, transports, Logger } from 'winston';
import { v4 as uuidv4 } from 'uuid';

export interface LogContext {
  correlationId?: string;
  userId?: string;
  serviceName?: string;
  operation?: string;
  metadata?: Record<string, any>;
}

@Injectable({ scope: Scope.TRANSIENT })
export class AppLoggerService {
  private readonly logger: Logger;
  private context: LogContext = {};

  constructor() {
    this.logger = createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: format.combine(
        format.timestamp(),
        format.errors({ stack: true }),
        format.json(),
        format.printf((info) => {
          return JSON.stringify({
            timestamp: info.timestamp,
            level: info.level,
            message: info.message,
            correlationId: this.context.correlationId,
            userId: this.context.userId,
            serviceName: this.context.serviceName,
            operation: this.context.operation,
            metadata: this.context.metadata,
            stack: info.stack,
            ...info
          });
        })
      ),
      transports: [
        new transports.Console(),
        new transports.File({ 
          filename: 'logs/error.log', 
          level: 'error' 
        }),
        new transports.File({ 
          filename: 'logs/combined.log' 
        })
      ]
    });
  }

  setContext(context: Partial<LogContext>): void {
    this.context = { ...this.context, ...context };
  }

  info(message: string, metadata?: Record<string, any>): void {
    this.logger.info(message, { metadata });
  }

  error(message: string, error?: Error, metadata?: Record<string, any>): void {
    this.logger.error(message, {
      error: error?.message,
      stack: error?.stack,
      metadata
    });
  }

  warn(message: string, metadata?: Record<string, any>): void {
    this.logger.warn(message, { metadata });
  }

  debug(message: string, metadata?: Record<string, any>): void {
    this.logger.debug(message, { metadata });
  }

  generateCorrelationId(): string {
    return uuidv4();
  }
}
```

### **Correlation Middleware**
```typescript
// src/logging/correlation.middleware.ts
import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { AppLoggerService } from './logger.service';

export interface RequestWithCorrelation extends Request {
  correlationId: string;
}

@Injectable()
export class CorrelationMiddleware implements NestMiddleware {
  constructor(private readonly logger: AppLoggerService) {}

  use(req: RequestWithCorrelation, res: Response, next: NextFunction): void {
    const correlationId = req.headers['x-correlation-id'] as string || 
                         this.logger.generateCorrelationId();
    
    req.correlationId = correlationId;
    res.setHeader('x-correlation-id', correlationId);
    
    this.logger.setContext({
      correlationId,
      operation: `${req.method} ${req.path}`
    });

    next();
  }
}
```

### **Logger Module**
```typescript
// src/logging/logger.module.ts
import { Global, Module, MiddlewareConsumer } from '@nestjs/common';
import { AppLoggerService } from './logger.service';
import { CorrelationMiddleware } from './correlation.middleware';

@Global()
@Module({
  providers: [AppLoggerService],
  exports: [AppLoggerService]
})
export class LoggerModule {
  configure(consumer: MiddlewareConsumer): void {
    consumer.apply(CorrelationMiddleware).forRoutes('*');
  }
}
```

---

## ⚠️ **2. Error Handling Implementation**

### **Custom Exceptions**
```typescript
// src/errors/exceptions/business.exception.ts
import { HttpException, HttpStatus } from '@nestjs/common';

export class BusinessException extends HttpException {
  constructor(
    message: string,
    errorCode: string,
    statusCode: HttpStatus = HttpStatus.BAD_REQUEST,
    metadata?: Record<string, any>
  ) {
    super(
      {
        message,
        errorCode,
        timestamp: new Date().toISOString(),
        metadata
      },
      statusCode
    );
  }
}

export class ValidationException extends BusinessException {
  constructor(message: string, validationErrors: any[]) {
    super(message, 'VALIDATION_ERROR', HttpStatus.BAD_REQUEST, {
      validationErrors
    });
  }
}

export class NotFoundBusinessException extends BusinessException {
  constructor(resource: string, identifier: string) {
    super(
      `${resource} with identifier ${identifier} not found`,
      'RESOURCE_NOT_FOUND',
      HttpStatus.NOT_FOUND,
      { resource, identifier }
    );
  }
}
```

### **Global Exception Filter**
```typescript
// src/errors/filters/global-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Injectable
} from '@nestjs/common';
import { Request, Response } from 'express';
import { AppLoggerService } from '../../logging/logger.service';

@Injectable()
@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  constructor(private readonly logger: AppLoggerService) {}

  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const request = ctx.getRequest<Request>();
    const response = ctx.getResponse<Response>();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = 'Internal server error';
    let errorCode = 'INTERNAL_ERROR';
    let metadata: any = {};

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const exceptionResponse = exception.getResponse();
      
      if (typeof exceptionResponse === 'object') {
        message = (exceptionResponse as any).message || message;
        errorCode = (exceptionResponse as any).errorCode || 'HTTP_EXCEPTION';
        metadata = (exceptionResponse as any).metadata || {};
      } else {
        message = exceptionResponse;
      }
    }

    const errorResponse = {
      statusCode: status,
      message,
      errorCode,
      timestamp: new Date().toISOString(),
      path: request.url,
      method: request.method,
      metadata
    };

    this.logger.error(
      `Exception caught: ${message}`,
      exception instanceof Error ? exception : new Error(String(exception)),
      {
        url: request.url,
        method: request.method,
        statusCode: status,
        errorCode,
        metadata
      }
    );

    response.status(status).json(errorResponse);
  }
}
```

---

## ⚙️ **3. Configuration Management**

### **Configuration Module**
```typescript
// src/config/config.module.ts
import { Global, Module } from '@nestjs/common';
import { ConfigModule as NestConfigModule } from '@nestjs/config';
import { validationSchema } from './validation.schemas';

@Global()
@Module({
  imports: [
    NestConfigModule.forRoot({
      isGlobal: true,
      validationSchema,
      validationOptions: {
        allowUnknown: true,
        abortEarly: false
      }
    })
  ]
})
export class ConfigModule {}
```

### **Validation Schemas**
```typescript
// src/config/validation.schemas.ts
import * as Joi from 'joi';

export const validationSchema = Joi.object({
  NODE_ENV: Joi.string()
    .valid('development', 'production', 'test')
    .default('development'),
  
  PORT: Joi.number().default(3000),
  
  LOG_LEVEL: Joi.string()
    .valid('error', 'warn', 'info', 'debug')
    .default('info'),
    
  DATABASE_URL: Joi.string().required(),
  
  JWT_SECRET: Joi.string().required(),
  JWT_EXPIRES_IN: Joi.string().default('1h'),
  
  REDIS_URL: Joi.string().required(),
  
  RABBITMQ_URL: Joi.string().required()
});

export interface AppConfig {
  nodeEnv: string;
  port: number;
  logLevel: string;
  databaseUrl: string;
  jwtSecret: string;
  jwtExpiresIn: string;
  redisUrl: string;
  rabbitmqUrl: string;
}
```

---

## 🏥 **4. Health Checks Implementation**

### **Health Controller**
```typescript
// src/health/health.controller.ts
import { Controller, Get } from '@nestjs/common';
import {
  HealthCheckService,
  HealthCheck,
  TypeOrmHealthIndicator,
  MemoryHealthIndicator
} from '@nestjs/terminus';

@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private db: TypeOrmHealthIndicator,
    private memory: MemoryHealthIndicator
  ) {}

  @Get()
  @HealthCheck()
  check() {
    return this.health.check([
      () => this.db.pingCheck('database'),
      () => this.memory.checkHeap('memory_heap', 150 * 1024 * 1024),
      () => this.memory.checkRSS('memory_rss', 150 * 1024 * 1024)
    ]);
  }

  @Get('ready')
  @HealthCheck()
  readiness() {
    return this.health.check([
      () => this.db.pingCheck('database')
    ]);
  }

  @Get('live')
  @HealthCheck()
  liveness() {
    return this.health.check([
      () => this.memory.checkHeap('memory_heap', 200 * 1024 * 1024)
    ]);
  }
}
```

---

## 🎨 **5. Common Decorators and Interceptors**

### **API Response Decorator**
```typescript
// src/decorators/api-response.decorator.ts
import { applyDecorators, Type } from '@nestjs/common';
import { ApiResponse, ApiProperty } from '@nestjs/swagger';

export class BaseResponse<T> {
  @ApiProperty()
  success: boolean;

  @ApiProperty()
  message: string;

  @ApiProperty()
  timestamp: string;

  @ApiProperty()
  correlationId: string;

  data: T;
}

export const ApiSuccessResponse = <TModel extends Type<any>>(
  model: TModel,
  description?: string
) => {
  return applyDecorators(
    ApiResponse({
      status: 200,
      description: description || 'Success',
      type: model
    })
  );
};
```

### **Transform Interceptor**
```typescript
// src/interceptors/transform.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Request } from 'express';

export interface Response<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  correlationId: string;
}

@Injectable()
export class TransformInterceptor<T>
  implements NestInterceptor<T, Response<T>>
{
  intercept(
    context: ExecutionContext,
    next: CallHandler
  ): Observable<Response<T>> {
    const request = context.switchToHttp().getRequest<Request>();
    const correlationId = request.headers['x-correlation-id'] as string;

    return next.handle().pipe(
      map((data) => ({
        success: true,
        message: 'Operation completed successfully',
        data,
        timestamp: new Date().toISOString(),
        correlationId
      }))
    );
  }
}
```

---

## 📤 **6. Main Export File**

```typescript
// src/index.ts
// Logging
export * from './logging';

// Error handling
export * from './errors';

// Configuration
export * from './config';

// Health checks
export * from './health';

// Decorators
export * from './decorators';

// Interceptors
export * from './interceptors';

// Types and interfaces
export interface ServiceContext {
  correlationId: string;
  userId?: string;
  serviceName: string;
}
```

---

## 🧪 **Testing Setup**

### **Jest Configuration**
```typescript
// jest.config.js
module.exports = {
  moduleFileExtensions: ['js', 'json', 'ts'],
  rootDir: 'src',
  testRegex: '.*\\.spec\\.ts$',
  transform: {
    '^.+\\.(t|j)s$': 'ts-jest'
  },
  collectCoverageFrom: [
    '**/*.(t|j)s'
  ],
  coverageDirectory: '../coverage',
  testEnvironment: 'node'
};
```

### **Example Test**
```typescript
// tests/logging/logger.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { AppLoggerService } from '../../src/logging/logger.service';

describe('AppLoggerService', () => {
  let service: AppLoggerService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [AppLoggerService]
    }).compile();

    service = module.get<AppLoggerService>(AppLoggerService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should generate correlation ID', () => {
    const correlationId = service.generateCorrelationId();
    expect(correlationId).toBeDefined();
    expect(typeof correlationId).toBe('string');
  });

  it('should set context', () => {
    const context = {
      correlationId: '123',
      userId: 'user-456',
      serviceName: 'test-service'
    };
    
    service.setContext(context);
    // Test would verify context is applied to logs
  });
});
```

---

## ✅ **Validation Steps**

1. **Build the package**: `npm run build`
2. **Run tests**: `npm run test`
3. **Check TypeScript compilation**: `npx tsc --noEmit`
4. **Test integration** with a sample NestJS app

---

## 🔗 **Next Step**

Once this is complete, move to [Auth Client Utils Implementation](./02-auth-client-utils-implementation.md) to build authentication utilities.

This foundational library will be used by every microservice in your platform! 🚀