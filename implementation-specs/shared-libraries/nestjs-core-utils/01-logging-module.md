# 01: Logging Module (`LoggingModule`)

## 1. Purpose

The `LoggingModule` within the `nestjs-core-utils` shared library aims to provide a standardized, production-ready logging solution for all NestJS-based microservices. It ensures that logs are structured, consistent, and easily integrated with centralized logging systems.

Key objectives:
*   Abstract the underlying logging library choice (e.g., Winston, Pino) for service developers.
*   Enforce structured logging (JSON format by default).
*   Include essential context in every log message (timestamp, level, service name, correlation ID).
*   Provide easy-to-use request logging middleware/interceptors.
*   Allow for configurable log levels.

## 2. Features

*   **Structured Logging:** Logs will be output in JSON format, making them easily parsable by log management systems like ELK Stack, Splunk, or cloud-based logging services.
*   **Default Log Fields:** Each log entry will automatically include:
    *   `timestamp`: ISO 8601 format.
    *   `level`: (e.g., `error`, `warn`, `info`, `debug`, `verbose`).
    *   `message`: The main log message.
    *   `context`: The NestJS context (e.g., class name where the logger is used).
    *   `serviceName`: Name of the microservice (configurable).
    *   `correlationId`: A unique ID to trace a request across services (see Context Propagation).
    *   `stack`: Stack trace for error logs.
*   **Configurable Log Level:** The log level will be configurable via environment variables (e.g., `LOG_LEVEL`), defaulting to `INFO` in production and `DEBUG` or `VERBOSE` in development.
*   **Request Logging:**
    *   An optional NestJS middleware or interceptor to automatically log incoming HTTP requests and their corresponding responses.
    *   Logged request details: method, URL, source IP, user-agent, request body (sanitized).
    *   Logged response details: status code, duration, response body (sanitized).
*   **Context Propagation (Correlation ID):**
    *   The logger will automatically include a `correlationId` in logs if available (e.g., extracted from incoming request headers or generated if not present).
    *   This ID should be propagated to downstream service calls to enable distributed tracing across logs.
*   **Logger Injection:** Provides a simple way to inject the configured logger instance into any service or controller using standard NestJS dependency injection (`@InjectLogger()` decorator or similar).
*   **Pretty Printing (Development):** Optional human-readable console output for local development (while still outputting JSON to files or for production transports).

## 3. Implementation Considerations (using Winston as an example)

While the module abstracts the specific library, Winston is a popular choice for Node.js logging.

*   **Dynamic Module:** The `LoggingModule` could be a NestJS dynamic module (`forRootAsync` or `forRoot`) to allow for configuration (e.g., `serviceName`, global log level) when imported into an application.
    ```typescript
    // Example in a service's AppModule
    import { LoggingModule } from '@my-org/nestjs-core-utils';

    @Module({
      imports: [
        LoggingModule.forRoot({
          serviceName: 'user-service',
          logLevel: process.env.LOG_LEVEL || 'info',
          // other options
        }),
      ],
    })
    export class AppModule {}
    ```
*   **Winston Transports:**
    *   `Console`: For outputting logs to the console. Configured with JSON format for production/staging, and optionally a pretty-print format for development.
    *   File transports (e.g., `winston-daily-rotate-file`) could be included but are often better handled by the container environment redirecting `stdout`/`stderr` to a log collector.
*   **Logger Service:** A custom `MyLoggerService` implementing NestJS `LoggerService` and wrapping the configured Winston instance.
    ```typescript
    // Simplified example
    import { Injectable, Scope, LoggerService } from '@nestjs/common';
    import * as winston from 'winston';

    @Injectable({ scope: Scope.TRANSIENT }) // TRANSIENT for unique context
    export class MyLoggerService implements LoggerService {
      private context?: string;
      private static logger: winston.Logger; // Static logger instance

      public static configure(options: { serviceName: string; logLevel: string }) {
        // Configure the static Winston logger instance here
        // with transports, formats (json, timestamp, serviceName, etc.)
        MyLoggerService.logger = winston.createLogger({ /* ... */ });
      }

      setContext(context: string) {
        this.context = context;
      }

      log(message: any, context?: string) {
        MyLoggerService.logger.info(message, { context: context || this.context });
      }
      error(message: any, trace?: string, context?: string) {
        MyLoggerService.logger.error(message, { trace, context: context || this.context });
      }
      // warn, debug, verbose methods...
    }
    ```
*   **Request Logging Interceptor:**
    ```typescript
    @Injectable()
    export class LoggingInterceptor implements NestInterceptor {
      constructor(private readonly logger: MyLoggerService) {}
      intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
        const request = context.switchToHttp().getRequest();
        const { method, url, ip } = request;
        this.logger.log(`Request: ${method} ${url} from ${ip}`);

        const now = Date.now();
        return next
          .handle()
          .pipe(
            tap(() => {
              const response = context.switchToHttp().getResponse();
              this.logger.log(
                `Response: ${method} ${url} - ${response.statusCode} (${Date.now() - now}ms)`,
              );
            }),
            catchError(err => {
              this.logger.error(`Error in Response: ${method} ${url}`, err.stack);
              return throwError(() => err);
            }),
          );
      }
    }
    ```

## 4. Usage

1.  **Import and Configure:** Import `LoggingModule.forRoot(...)` into the root `AppModule` of a service.
2.  **Inject Logger:**
    ```typescript
    import { Injectable } from '@nestjs/common';
    import { MyLoggerService } from '@my-org/nestjs-core-utils'; // Or an injected token

    @Injectable()
    export class AppService {
      constructor(private readonly logger: MyLoggerService) {
        this.logger.setContext('AppService');
      }

      getHello(): string {
        this.logger.log('getHello was called');
        return 'Hello World!';
      }
    }
    ```
3.  **Apply Request Logger (Optional):** Apply the `LoggingInterceptor` globally or to specific controllers/routes.

## 5. Future Enhancements

*   More sophisticated log redaction for sensitive fields.
*   Direct integration with distributed tracing systems to include `traceId` and `spanId` automatically.
*   Asynchronous logging for very high-throughput scenarios (though often handled by redirecting stdout/stderr from containers).

This module will provide a solid foundation for consistent and effective logging across the platform.