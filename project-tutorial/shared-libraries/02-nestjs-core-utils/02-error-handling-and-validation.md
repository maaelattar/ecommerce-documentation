# Error Handling and Validation Module

## Overview

Build comprehensive error handling utilities including global exception filters, custom business exceptions, validation error formatting, and standardized HTTP response patterns.

## 🎯 Learning Objectives

- Create custom business exception classes
- Build global exception filters with logging integration
- Implement validation error formatting
- Create standardized API response interceptors
- Handle different error scenarios gracefully

---

## Step 1: Custom Exception Classes

### 1.1 Create Base Business Exception

```typescript
// src/exceptions/business.exception.ts
import { HttpException, HttpStatus } from '@nestjs/common';

export class BusinessException extends HttpException {
  constructor(
    message: string,
    public readonly errorCode: string,
    statusCode: HttpStatus = HttpStatus.BAD_REQUEST,
    public readonly metadata?: Record<string, any>
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
```

### 1.2 Create Specific Exception Types

```typescript
// src/exceptions/validation.exception.ts
import { HttpStatus } from '@nestjs/common';
import { BusinessException } from './business.exception';

export class ValidationException extends BusinessException {
  constructor(message: string, validationErrors: any[]) {
    super(
      message,
      'VALIDATION_ERROR',
      HttpStatus.BAD_REQUEST,
      { validationErrors }
    );
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

export class ConflictBusinessException extends BusinessException {
  constructor(message: string, conflictData?: Record<string, any>) {
    super(
      message,
      'CONFLICT_ERROR',
      HttpStatus.CONFLICT,
      conflictData
    );
  }
}

export class UnauthorizedBusinessException extends BusinessException {
  constructor(message: string = 'Unauthorized access') {
    super(
      message,
      'UNAUTHORIZED_ACCESS',
      HttpStatus.UNAUTHORIZED
    );
  }
}

export class ForbiddenBusinessException extends BusinessException {
  constructor(message: string = 'Forbidden access', requiredPermissions?: string[]) {
    super(
      message,
      'FORBIDDEN_ACCESS',
      HttpStatus.FORBIDDEN,
      { requiredPermissions }
    );
  }
}
```

---

## Step 2: Global Exception Filter

### 2.1 Create Global Exception Filter

```typescript
// src/exceptions/global-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Injectable
} from '@nestjs/common';
import { Request, Response } from 'express';
import { AppLoggerService } from '../logging/logger.service';
import { BusinessException } from './business.exception';

export interface ErrorResponse {
  success: boolean;
  statusCode: number;
  message: string;
  errorCode: string;
  timestamp: string;
  path: string;
  method: string;
  correlationId?: string;
  metadata?: Record<string, any>;
}

@Injectable()
@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  constructor(private readonly logger: AppLoggerService) {}

  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const request = ctx.getRequest<Request>();
    const response = ctx.getResponse<Response>();

    const correlationId = request.headers['x-correlation-id'] as string;
    const errorResponse = this.buildErrorResponse(exception, request, correlationId);

    // Log the error with appropriate level
    this.logError(exception, errorResponse, correlationId);

    response.status(errorResponse.statusCode).json(errorResponse);
  }

  private buildErrorResponse(
    exception: unknown, 
    request: Request, 
    correlationId?: string
  ): ErrorResponse {
    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = 'Internal server error';
    let errorCode = 'INTERNAL_ERROR';
    let metadata: any = {};

    if (exception instanceof BusinessException) {
      // Custom business exceptions
      status = exception.getStatus();
      const exceptionResponse = exception.getResponse() as any;
      message = exceptionResponse.message || message;
      errorCode = exception.errorCode;
      metadata = exception.metadata || {};
    } else if (exception instanceof HttpException) {
      // Standard HTTP exceptions
      status = exception.getStatus();
      const exceptionResponse = exception.getResponse();
      
      if (typeof exceptionResponse === 'object') {
        message = (exceptionResponse as any).message || message;
        errorCode = this.mapHttpStatusToErrorCode(status);
        
        // Handle validation errors
        if ((exceptionResponse as any).message && Array.isArray((exceptionResponse as any).message)) {
          errorCode = 'VALIDATION_ERROR';
          metadata = { validationErrors: (exceptionResponse as any).message };
        }
      } else {
        message = exceptionResponse;
        errorCode = this.mapHttpStatusToErrorCode(status);
      }
    } else if (exception instanceof Error) {
      // Generic errors
      message = exception.message || message;
      errorCode = 'APPLICATION_ERROR';
      metadata = { originalError: exception.name };
    }

    return {
      success: false,
      statusCode: status,
      message,
      errorCode,
      timestamp: new Date().toISOString(),
      path: request.url,
      method: request.method,
      correlationId,
      metadata
    };
  }

  private logError(exception: unknown, errorResponse: ErrorResponse, correlationId?: string): void {
    const logContext = {
      correlationId,
      url: errorResponse.path,
      method: errorResponse.method,
      statusCode: errorResponse.statusCode,
      errorCode: errorResponse.errorCode
    };

    if (errorResponse.statusCode >= 500) {
      // Server errors - log as error with full stack
      this.logger.error(
        `Server Error: ${errorResponse.message}`,
        exception instanceof Error ? exception : new Error(String(exception)),
        logContext
      );
    } else if (errorResponse.statusCode >= 400) {
      // Client errors - log as warning
      this.logger.warn(
        `Client Error: ${errorResponse.message}`,
        { ...logContext, metadata: errorResponse.metadata }
      );
    } else {
      // Other status codes - log as info
      this.logger.info(
        `Request Error: ${errorResponse.message}`,
        { ...logContext, metadata: errorResponse.metadata }
      );
    }
  }

  private mapHttpStatusToErrorCode(status: HttpStatus): string {
    const statusMap: Record<HttpStatus, string> = {
      [HttpStatus.BAD_REQUEST]: 'BAD_REQUEST',
      [HttpStatus.UNAUTHORIZED]: 'UNAUTHORIZED',
      [HttpStatus.FORBIDDEN]: 'FORBIDDEN',
      [HttpStatus.NOT_FOUND]: 'NOT_FOUND',
      [HttpStatus.CONFLICT]: 'CONFLICT',
      [HttpStatus.UNPROCESSABLE_ENTITY]: 'UNPROCESSABLE_ENTITY',
      [HttpStatus.INTERNAL_SERVER_ERROR]: 'INTERNAL_ERROR',
      [HttpStatus.BAD_GATEWAY]: 'BAD_GATEWAY',
      [HttpStatus.SERVICE_UNAVAILABLE]: 'SERVICE_UNAVAILABLE'
    };

    return statusMap[status] || 'UNKNOWN_ERROR';
  }
}
```

---

## Step 3: Response Interceptors

### 3.1 Create Transform Interceptor

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

export interface SuccessResponse<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  correlationId?: string;
  metadata?: {
    page?: number;
    limit?: number;
    total?: number;
    hasNextPage?: boolean;
    hasPreviousPage?: boolean;
  };
}

@Injectable()
export class TransformInterceptor<T> implements NestInterceptor<T, SuccessResponse<T>> {
  intercept(context: ExecutionContext, next: CallHandler): Observable<SuccessResponse<T>> {
    const request = context.switchToHttp().getRequest<Request>();
    const correlationId = request.headers['x-correlation-id'] as string;

    return next.handle().pipe(
      map((data) => {
        // Handle paginated responses
        if (data && typeof data === 'object' && 'items' in data && 'total' in data) {
          const paginatedData = data as any;
          return {
            success: true,
            message: 'Operation completed successfully',
            data: paginatedData.items,
            timestamp: new Date().toISOString(),
            correlationId,
            metadata: {
              page: paginatedData.page,
              limit: paginatedData.limit,
              total: paginatedData.total,
              hasNextPage: paginatedData.hasNextPage,
              hasPreviousPage: paginatedData.hasPreviousPage
            }
          };
        }

        // Handle regular responses
        return {
          success: true,
          message: 'Operation completed successfully',
          data,
          timestamp: new Date().toISOString(),
          correlationId
        };
      })
    );
  }
}
```

### 3.2 Create Logging Interceptor

```typescript
// src/interceptors/logging.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request, Response } from 'express';
import { AppLoggerService } from '../logging/logger.service';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  constructor(private readonly logger: AppLoggerService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest<Request>();
    const response = context.switchToHttp().getResponse<Response>();
    const startTime = Date.now();

    const { method, url, ip, headers } = request;
    const userAgent = headers['user-agent'] || '';

    this.logger.info('Incoming request', {
      method,
      url,
      ip,
      userAgent
    });

    return next.handle().pipe(
      tap({
        next: (data) => {
          const duration = Date.now() - startTime;
          this.logger.info('Request completed successfully', {
            method,
            url,
            statusCode: response.statusCode,
            duration: `${duration}ms`,
            responseSize: JSON.stringify(data).length
          });
        },
        error: (error) => {
          const duration = Date.now() - startTime;
          this.logger.error('Request failed', error, {
            method,
            url,
            duration: `${duration}ms`
          });
        }
      })
    );
  }
}
```

---

## Step 4: Validation Utilities

### 4.1 Create Validation Pipe

```typescript
// src/validation/validation.pipe.ts
import { 
  ArgumentMetadata, 
  Injectable, 
  PipeTransform 
} from '@nestjs/common';
import { validate } from 'class-validator';
import { plainToClass } from 'class-transformer';
import { ValidationException } from '../exceptions/validation.exception';

@Injectable()
export class CustomValidationPipe implements PipeTransform<any> {
  async transform(value: any, { metatype }: ArgumentMetadata) {
    if (!metatype || !this.toValidate(metatype)) {
      return value;
    }

    const object = plainToClass(metatype, value);
    const errors = await validate(object);
    
    if (errors.length > 0) {
      const validationErrors = errors.map(error => ({
        property: error.property,
        value: error.value,
        constraints: error.constraints,
        children: error.children
      }));

      throw new ValidationException(
        'Validation failed',
        validationErrors
      );
    }
    
    return object;
  }

  private toValidate(metatype: Function): boolean {
    const types: Function[] = [String, Boolean, Number, Array, Object];
    return !types.includes(metatype);
  }
}
```

---

## Step 5: Export Exception Components

```typescript
// src/exceptions/index.ts
export * from './business.exception';
export * from './validation.exception';
export * from './global-exception.filter';

// src/interceptors/index.ts
export * from './transform.interceptor';
export * from './logging.interceptor';

// src/validation/index.ts
export * from './validation.pipe';
```

---

## Step 6: Create Tests

### 6.1 Test Global Exception Filter

```typescript
// src/exceptions/global-exception.filter.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { HttpStatus } from '@nestjs/common';
import { GlobalExceptionFilter } from './global-exception.filter';
import { BusinessException } from './business.exception';
import { AppLoggerService } from '../logging/logger.service';

describe('GlobalExceptionFilter', () => {
  let filter: GlobalExceptionFilter;
  let logger: AppLoggerService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        GlobalExceptionFilter,
        {
          provide: AppLoggerService,
          useValue: {
            error: jest.fn(),
            warn: jest.fn(),
            info: jest.fn()
          }
        }
      ]
    }).compile();

    filter = module.get<GlobalExceptionFilter>(GlobalExceptionFilter);
    logger = module.get<AppLoggerService>(AppLoggerService);
  });

  it('should be defined', () => {
    expect(filter).toBeDefined();
  });

  it('should handle BusinessException correctly', () => {
    const exception = new BusinessException(
      'Test error',
      'TEST_ERROR',
      HttpStatus.BAD_REQUEST
    );

    const mockResponse = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn()
    };

    const mockRequest = {
      url: '/test',
      method: 'GET',
      headers: { 'x-correlation-id': '123' }
    };

    const mockHost = {
      switchToHttp: () => ({
        getRequest: () => mockRequest,
        getResponse: () => mockResponse
      })
    };

    filter.catch(exception, mockHost as any);

    expect(mockResponse.status).toHaveBeenCalledWith(HttpStatus.BAD_REQUEST);
    expect(mockResponse.json).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        statusCode: HttpStatus.BAD_REQUEST,
        message: 'Test error',
        errorCode: 'TEST_ERROR'
      })
    );
  });
});
```

---

## Step 7: Update Main Exports

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
```

---

## Step 8: Build and Test

```bash
# Run tests
npm test

# Build the package
npm run build
```

---

## 🎯 Key Accomplishments

✅ **Custom business exceptions** with error codes and metadata  
✅ **Global exception filter** with comprehensive error handling  
✅ **Response transformation** with standardized API formats  
✅ **Request/response logging** with performance metrics  
✅ **Validation integration** with detailed error messages  
✅ **Error categorization** and appropriate logging levels  

---

## 🔗 Next Steps

Continue with **[03-configuration-and-health.md](./03-configuration-and-health.md)** to build configuration management and health check utilities.

---

## 💡 Usage Preview

```typescript
// In your main application
import { 
  GlobalExceptionFilter, 
  TransformInterceptor,
  AppLoggerService 
} from '@ecommerce/nestjs-core-utils';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const logger = app.get(AppLoggerService);
  
  app.useGlobalFilters(new GlobalExceptionFilter(logger));
  app.useGlobalInterceptors(new TransformInterceptor());
  
  await app.listen(3000);
}
```