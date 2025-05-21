# 01: Mock Core Utilities

## 1. Introduction

This document details mock implementations for core utilities that are typically provided by the `nestjs-core-utils` shared library. The purpose of these mocks is to allow services to easily and consistently test components that depend on these core utilities without relying on their actual implementations (e.g., avoiding actual log I/O or complex configuration loading during tests).

These mocks are fundamental for unit testing and some integration testing scenarios.

## 2. MockLogger (`MockLoggerService`)

Services often inject a logger service (e.g., `MyLoggerService` provided by `nestjs-core-utils` via `LoggingModule`). The `MockLoggerService` provides a test double for this.

### 2.1. Purpose

*   Prevent actual log output (console, file, etc.) during tests.
*   Allow tests to assert that specific log methods (log, error, warn, debug, verbose) were called with expected messages or contexts.
*   Provide a simple, in-memory store of log calls if detailed inspection is needed (though often, spies on methods are sufficient).

### 2.2. Implementation Sketch

```typescript
// In @your-org/testing-utils/src/mocks/mock-logger.service.ts

import { LoggerService, LogLevel } from '@nestjs/common'; // Or your custom logger interface

export class MockLoggerService implements LoggerService {
  // Optional: Store logs in memory if direct inspection is needed
  // private logs: Array<{ level: LogLevel; message: any; context?: string; args: any[] }> = [];

  log(message: any, context?: string, ...args: any[]) {
    // this.logs.push({ level: 'log', message, context, args });
    // Typically, methods are spied upon by Jest/Sinon, so no internal logging needed
  }

  error(message: any, trace?: string, context?: string, ...args: any[]) {
    // this.logs.push({ level: 'error', message, context, args });
  }

  warn(message: any, context?: string, ...args: any[]) {
    // this.logs.push({ level: 'warn', message, context, args });
  }

  debug?(message: any, context?: string, ...args: any[]) {
    // this.logs.push({ level: 'debug', message, context, args });
  }

  verbose?(message: any, context?: string, ...args: any[]) {
    // this.logs.push({ level: 'verbose', message, context, args });
  }

  // Optional: Method to retrieve logs for complex assertions
  // getLoggedMessages() { return this.logs; }
  // clearLogs() { this.logs = []; }

  // Optional: For NestJS 8+ compatibility if your LoggerService has setLogLevels
  setLogLevels?(levels: LogLevel[]) {}
}
```

*   **Interface Compliance:** Implements `LoggerService` from `@nestjs/common` or your custom logger interface defined in `nestjs-core-utils`.
*   **Spies over In-Memory Storage:** While an in-memory log store is an option, it's often more idiomatic in Jest/Sinon to use spies (`jest.spyOn` or `sinon.spy`) on the mock logger's methods. The methods can thus have empty implementations.

### 2.3. Usage

In a NestJS testing module:

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { YourService } from './your.service'; // The service being tested
import { MyLoggerService } from '@your-org/nestjs-core-utils'; // Actual logger token/class
import { MockLoggerService } from '@your-org/testing-utils'; // Path to mock

describe('YourService', () => {
  let service: YourService;
  let logger: MockLoggerService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        YourService,
        {
          provide: MyLoggerService, // Or the actual token/class used for injection
          useClass: MockLoggerService,
        },
      ],
    }).compile();

    service = module.get<YourService>(YourService);
    logger = module.get<MockLoggerService>(MyLoggerService as any); // Cast for spy access
  });

  it('should log an error when something fails', () => {
    const errorSpy = jest.spyOn(logger, 'error');
    
    service.doSomethingThatFails(); // Assuming this method calls this.logger.error()

    expect(errorSpy).toHaveBeenCalledWith('Specific error message', expect.anything(), 'YourServiceContext');
  });
});
```

## 3. MockConfigService

Services rely on `@nestjs/config`'s `ConfigService` (or a wrapper from `nestjs-core-utils`) to access configuration values.

### 3.1. Purpose

*   Provide controlled and predictable configuration values during tests without reading actual environment variables or `.env` files.
*   Simplify testing of components that behave differently based on configuration.

### 3.2. Implementation Sketch

```typescript
// In @your-org/testing-utils/src/mocks/mock-config.service.ts

export class MockConfigService {
  private config: Record<string, any> = {};

  constructor(initialConfig?: Record<string, any>) {
    if (initialConfig) {
      this.config = { ...initialConfig };
    }
  }

  get<T = any>(propertyPath: string, defaultValue?: T): T | undefined {
    const value = this.config[propertyPath];
    return value !== undefined ? value : defaultValue;
  }

  // Method to set or override config values for a specific test
  set(propertyPath: string, value: any): void {
    this.config[propertyPath] = value;
  }

  // Method to provide all config for a test
  setConfig(config: Record<string, any>): void {
    this.config = { ...config };
  }
}
```

### 3.3. Usage

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { YourComponent } from './your.component';
import { ConfigService } from '@nestjs/config'; // Or your custom config service token
import { MockConfigService } from '@your-org/testing-utils';

describe('YourComponent', () => {
  let component: YourComponent;
  let mockConfigService: MockConfigService;

  beforeEach(async () => {
    // Provide initial default mock config if needed
    const initialMockConfig = { FEATURE_FLAG_X: true, API_URL: 'http://test-url.com' };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        YourComponent,
        {
          provide: ConfigService, // Use the actual token your app uses
          useValue: new MockConfigService(initialMockConfig),
        },
      ],
    }).compile();

    component = module.get<YourComponent>(YourComponent);
    mockConfigService = module.get<MockConfigService>(ConfigService as any);
  });

  it('should behave correctly when feature flag is on', () => {
    // mockConfigService.set('FEATURE_FLAG_X', true); // Already set in initial, or override here
    // ... test logic ...
  });

  it('should use a different URL when configured', () => {
    mockConfigService.set('API_URL', 'http://another-url.com');
    // ... test logic that depends on API_URL ...
    expect(component.getApiUrl()).toBe('http://another-url.com');
  });
});
```

These mock utilities provide a foundational layer for writing effective and isolated tests for your microservice components.
