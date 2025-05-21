# 02: Error Handling Module (`ErrorHandlingModule`)

## 1. Purpose

The `ErrorHandlingModule` in the `nestjs-core-utils` shared library is designed to standardize how errors and exceptions are handled and represented in API responses across all NestJS-based microservices. This consistency improves developer experience for API consumers and simplifies debugging and monitoring.

Key objectives:
*   Provide a global exception filter to catch unhandled exceptions and known NestJS exceptions.
*   Define a standard JSON error response format.
*   Offer base exception classes for common error scenarios.
*   Integrate with the `LoggingModule` to ensure all errors are logged appropriately.

## 2. Features

*   **Global Exception Filter:** A NestJS exception filter that can be applied globally to catch:
    *   Standard `HttpException` instances (and its derivatives like `BadRequestException`, `NotFoundException`, etc.).
    *   Custom exceptions extending a base class provided by this module.
    *   Unhandled non-HTTP exceptions (which would be logged as critical server errors and potentially mapped to a generic 500 error response).
*   **Standardized Error DTO:** A defined TypeScript interface or DTO for error responses. Example structure:
    ```json
    {
      "statusCode": 400,
      "timestamp": "2023-10-27T10:30:00Z",
      "path": "/users",
      "method": "POST",
      "correlationId": "unique-request-id-123",
      "errorCode": "VALIDATION_ERROR", // Optional application-specific error code
      "message": "Input validation failed",
      "details": [ // Optional: for detailed validation errors or multiple issues
        { "field": "email", "message": "Email must be a valid email address" },
        { "field": "password", "message": "Password must be at least 8 characters long" }
      ]
    }
    ```
*   **Common Base Exception Classes:** A set of base exception classes that services can extend:
    *   `BasePlatformException extends HttpException`: For custom business logic errors that should result in specific HTTP status codes.
    *   Perhaps more specific ones like `EntityNotFoundException`, `InvalidInputException`, `UpstreamServiceException`.
*   **Logging Integration:** The global exception filter will use the `LoggingModule` to log:
    *   Full error details, including stack trace for server errors (HTTP 5xx).
    *   Concise error information for client errors (HTTP 4xx).
*   **Configuration:** Ability to configure certain aspects, e.g., whether to include stack traces in 5xx responses (only in non-production environments).

## 3. Implementation Considerations

*   **`AllExceptionsFilter`:**
    ```typescript
    import {
      ExceptionFilter, Catch, ArgumentsHost, HttpException, HttpStatus,
    } from '@nestjs/common';
    import { Request, Response } from 'express';
    import { MyLoggerService } from './logging.service'; // Assuming LoggingModule provides this

    interface IErrorDetail {
      field?: string;
      message: string;
    }

    interface IErrorResponse {
      statusCode: number;
      timestamp: string;
      path: string;
      method: string;
      correlationId?: string;
      errorCode?: string;
      message: string;
      details?: IErrorDetail[] | string[];
    }

    @Catch() // Catch all exceptions
    export class AllExceptionsFilter implements ExceptionFilter {
      constructor(private readonly logger: MyLoggerService) {}

      catch(exception: unknown, host: ArgumentsHost) {
        const ctx = host.switchToHttp();
        const response = ctx.getResponse<Response>();
        const request = ctx.getRequest<Request>();

        const statusCode =
          exception instanceof HttpException
            ? exception.getStatus()
            : HttpStatus.INTERNAL_SERVER_ERROR;

        const correlationId = request.headers['x-correlation-id'] as string; // Example

        let responseMessage: string;
        let errorCode: string | undefined;
        let details: IErrorDetail[] | string[] | undefined;

        if (exception instanceof HttpException) {
          const errorResponse = exception.getResponse();
          if (typeof errorResponse === 'string') {
            responseMessage = errorResponse;
          } else if (typeof errorResponse === 'object' && errorResponse !== null) {
            responseMessage = (errorResponse as any).message || exception.message;
            errorCode = (errorResponse as any).errorCode || (errorResponse as any).error;
            // For NestJS validation pipe errors, `message` is often an array of error strings
            if (Array.isArray((errorResponse as any).message) && statusCode === HttpStatus.BAD_REQUEST) {
              details = (errorResponse as any).message;
              responseMessage = 'Input validation failed'; // Generic message
            }
          }
          else {
            responseMessage = exception.message;
          }
        } else {
          responseMessage = 'Internal server error';
        }

        const errorPayload: IErrorResponse = {
          statusCode,
          timestamp: new Date().toISOString(),
          path: request.url,
          method: request.method,
          correlationId,
          errorCode,
          message: responseMessage,
          details,
        };

        if (statusCode >= 500) {
          this.logger.error(
            `HTTP Exception: ${request.method} ${request.url}`,
            exception instanceof Error ? exception.stack : String(exception),
            'AllExceptionsFilter',
          );
        } else {
          this.logger.warn(
            `HTTP Exception: ${request.method} ${request.url} - ${statusCode} ${responseMessage}`,
            'AllExceptionsFilter',
          );
        }

        // Never send stack trace to client in production for 5xx errors
        // if (process.env.NODE_ENV !== 'production' && statusCode >= 500 && exception instanceof Error) {
        //   errorPayload.details = [exception.stack || ''];
        // }

        response.status(statusCode).json(errorPayload);
      }
    }
    ```
*   **Module Setup:** The `ErrorHandlingModule` would provide the `AllExceptionsFilter` and potentially register it globally, or provide instructions for manual registration.
    ```typescript
    // error-handling.module.ts
    import { Module, Global } from '@nestjs/common';
    import { APP_FILTER } from '@nestjs/core';
    import { AllExceptionsFilter } from './all-exceptions.filter';
    import { MyLoggerService } from '../logging/my-logger.service'; // Assuming it's exported or part of LoggingModule
    import { LoggingModule } from '../logging/logging.module'; // Import LoggingModule

    @Global() // Optional: if you want to make filter available globally by default
    @Module({
      imports: [LoggingModule], // Ensure LoggingModule is imported to make MyLoggerService available
      providers: [
        // MyLoggerService, // Provide MyLoggerService if not globally available from LoggingModule
        {
          provide: APP_FILTER,
          useClass: AllExceptionsFilter,
        },
      ],
      // exports: [AllExceptionsFilter] // If not global and needs to be imported
    })
    export class ErrorHandlingModule {}
    ```

## 4. Usage

1.  **Import Module:** Import `ErrorHandlingModule` into the root `AppModule` of a service.
    ```typescript
    // app.module.ts
    import { Module } from '@nestjs/common';
    import { ErrorHandlingModule } from '@my-org/nestjs-core-utils';
    import { LoggingModule } from '@my-org/nestjs-core-utils'; // Ensure LoggingModule is also imported

    @Module({
      imports: [
        LoggingModule.forRoot({ serviceName: 'my-service' }), // Configure logging first
        ErrorHandlingModule, 
      ],
    })
    export class AppModule {}
    ```
2.  **Throw Standard Exceptions:** Use standard NestJS `HttpException` derivatives or custom exceptions extending `BasePlatformException` in your services and controllers.
    ```typescript
    import { Injectable, NotFoundException } from '@nestjs/common';
    // import { EntityNotFoundException } from '@my-org/nestjs-core-utils'; // If custom exceptions are provided

    @Injectable()
    export class MyService {
      findSomething(id: string) {
        if (!id) {
          // throw new EntityNotFoundException('Resource', `ID ${id} not found`);
          throw new NotFoundException(`Resource with ID ${id} not found`);
        }
        // ...
      }
    }
    ```
The global filter will automatically catch these and format the response according to the standard.

## 5. Considerations

*   **Production vs. Development Error Details:** Be careful about the level of detail exposed in error messages in production environments to avoid leaking sensitive information. Stack traces for 5xx errors should only be considered for non-production environments.
*   **I18n for Error Messages:** Internationalization of error messages is a more advanced topic and might be handled by a separate, dedicated mechanism if required, though `errorCode` can help client-side mapping.
*   **gRPC/Microservice Exceptions:** For non-HTTP microservice communication (e.g., gRPC), exception handling will differ and may require separate filters or interceptors specific to the transport layer, though the core error logging can still use the `LoggingModule`.