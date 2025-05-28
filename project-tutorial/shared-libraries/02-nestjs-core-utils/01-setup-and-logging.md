# NestJS Core Utils - Setup and Logging Module

## Overview

Build the foundational logging module with structured JSON logging, correlation IDs, and environment-based configuration that will be used across all microservices.

## 🎯 Learning Objectives

- Set up the shared library package structure
- Implement structured logging with Winston
- Create correlation ID middleware
- Build environment-based configuration
- Export reusable logging utilities

---

## Step 1: Initialize the Package

### 1.1 Create Package Structure

```bash
# Create the package directory (if not exists)
mkdir -p shared-libraries/nestjs-core-utils
cd shared-libraries/nestjs-core-utils

# Initialize npm package
npm init -y
```

### 1.2 Install Dependencies

```bash
# Core NestJS dependencies
npm install @nestjs/common @nestjs/core @nestjs/config @nestjs/terminus

# Logging dependencies
npm install winston nest-winston

# Validation and utility dependencies
npm install class-validator class-transformer joi uuid

# Development dependencies
npm install -D @types/uuid typescript jest @types/jest ts-jest
```

### 1.3 Update package.json

```json
{
  "name": "@ecommerce/nestjs-core-utils",
  "version": "1.0.0",
  "description": "Core NestJS utilities for ecommerce platform",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "test:watch": "jest --watch"
  },
  "keywords": ["nestjs", "utilities", "logging", "ecommerce"],
  "author": "Ecommerce Platform Team",
  "license": "MIT",
  "peerDependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0"
  }
}
```

### 1.4 Create TypeScript Configuration

```json
// tsconfig.json
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
    "noFallthroughCasesInSwitch": false
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "test"]
}
```

---

## Step 2: Create Project Structure

```bash
mkdir -p src/{logging,config,health,exceptions,interceptors,decorators}
touch src/index.ts
```

Your directory structure should look like:

```
shared-libraries/nestjs-core-utils/
├── src/
│   ├── logging/
│   ├── config/
│   ├── health/
│   ├── exceptions/
│   ├── interceptors/
│   ├── decorators/
│   └── index.ts
├── package.json
├── tsconfig.json
└── README.md
```

---

## Step 3: Implement Logging Module

### 3.1 Create Logger Service

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
        new transports.Console({
          format: process.env.NODE_ENV === 'development' 
            ? format.combine(
                format.colorize(),
                format.simple()
              )
            : format.json()
        })
      ]
    });
  }

  setContext(context: Partial<LogContext>): void {
    this.context = { ...this.context, ...context };
  }

  getContext(): LogContext {
    return { ...this.context };
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

### 3.2 Create Correlation Middleware

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
    // Extract or generate correlation ID
    const correlationId = 
      (req.headers['x-correlation-id'] as string) || 
      this.logger.generateCorrelationId();
    
    // Add to request object
    req.correlationId = correlationId;
    
    // Add to response headers
    res.setHeader('x-correlation-id', correlationId);
    
    // Set logger context
    this.logger.setContext({
      correlationId,
      operation: `${req.method} ${req.path}`
    });

    next();
  }
}
```

### 3.3 Create Logger Module

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

### 3.4 Export Logging Components

```typescript
// src/logging/index.ts
export * from './logger.service';
export * from './correlation.middleware';
export * from './logger.module';
```

---

## Step 4: Test the Logger Implementation

### 4.1 Create Test File

```typescript
// src/logging/logger.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { AppLoggerService } from './logger.service';

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
    expect(correlationId.length).toBeGreaterThan(0);
  });

  it('should set and get context', () => {
    const context = {
      correlationId: '123',
      userId: 'user-456',
      serviceName: 'test-service'
    };
    
    service.setContext(context);
    const retrievedContext = service.getContext();
    
    expect(retrievedContext).toEqual(expect.objectContaining(context));
  });

  it('should log info message', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    service.info('Test message', { key: 'value' });
    
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
```

### 4.2 Add Jest Configuration

```json
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

### 4.3 Run Tests

```bash
npm test
```

---

## Step 5: Update Main Export

```typescript
// src/index.ts
// Logging exports
export * from './logging';
```

---

## Step 6: Build and Verify

```bash
# Build the package
npm run build

# Verify build outputs
ls -la dist/
```

You should see:
- `dist/index.js` - Compiled JavaScript
- `dist/index.d.ts` - TypeScript declarations
- `dist/logging/` - Compiled logging modules

---

## 🎯 Key Accomplishments

✅ **Structured logging** with Winston integration  
✅ **Correlation ID tracking** across requests  
✅ **Context-aware logging** with metadata support  
✅ **Environment-based configuration** for log levels  
✅ **Middleware integration** for automatic correlation  
✅ **Test coverage** for core functionality  

---

## 🔗 Next Steps

Continue with **[02-error-handling-and-validation.md](./02-error-handling-and-validation.md)** to build error handling utilities that work seamlessly with the logging system.

---

## 💡 Usage Preview

Once complete, services will use the logger like this:

```typescript
import { AppLoggerService } from '@ecommerce/nestjs-core-utils';

@Injectable()
export class UserService {
  constructor(private logger: AppLoggerService) {
    this.logger.setContext({ serviceName: 'UserService' });
  }
  
  async createUser(userData: CreateUserDto) {
    this.logger.info('Creating new user', { email: userData.email });
    // Implementation...
  }
}
```