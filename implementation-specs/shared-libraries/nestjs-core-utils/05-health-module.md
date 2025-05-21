# 05: Health Module (`HealthModule`)

## 1. Purpose

The `HealthModule` in the `nestjs-core-utils` shared library aims to simplify the setup and standardization of health check endpoints in NestJS microservices. It leverages the `@nestjs/terminus` package to provide a consistent way for services to report their health status, including the status of their dependencies (e.g., database, message brokers, external services).

Key objectives:
*   Provide a simple way to expose a standardized health check endpoint (e.g., `/health`).
*   Integrate common health indicators for typical dependencies (PostgreSQL, Kafka, HTTP services).
*   Allow services to easily add custom health indicators.
*   Ensure health check responses are informative and can be consumed by orchestration platforms like Kubernetes.

## 2. Features

*   **Built on `@nestjs/terminus`:** Uses the robust and extensible `@nestjs/terminus` module as its foundation.
*   **Standardized Health Endpoint:** Provides a default `/health` (or configurable) endpoint that returns the overall health status of the service.
*   **Common Health Indicators:** Includes pre-built or easy-to-configure health indicators for:
    *   **Database Connectivity:** (e.g., `TypeOrmHealthIndicator` for PostgreSQL via TypeORM, `MongooseHealthIndicator` for MongoDB).
    *   **Message Broker Connectivity:** (e.g., a custom Kafka health indicator).
    *   **External HTTP Service Reachability:** (`HttpHealthIndicator` from `@nestjs/terminus`).
    *   **Disk Space:** (`DiskHealthIndicator`).
    *   **Memory Usage:** (`MemoryHealthIndicator`).
*   **Extensibility:** Allows services to easily register their own custom health indicators specific to their internal logic or unique dependencies.
*   **Informative Response Format:** Returns a JSON response detailing the status of each checked component and an overall status (e.g., `ok`, `error`). Example:
    ```json
    {
      "status": "ok", // or "error"
      "info": {
        "database": { "status": "up" },
        "kafka": { "status": "up" },
        "disk_space": { "status": "up", "total": "100GB", "free": "50GB" }
      },
      "error": {}, // Populated if status is "error"
      "details": { // Same as info, but NestJS Terminus uses 'details' when status is 'ok'
        "database": { "status": "up" },
        "kafka": { "status": "up" }
      }
    }
    ```

## 3. Implementation Considerations

*   **Dynamic Module:** The `HealthModule` could be a dynamic module allowing services to easily enable/disable or configure specific default indicators.
    ```typescript
    // health.module.ts (simplified)
    import { DynamicModule, Module } from '@nestjs/common';
    import { TerminusModule, TerminusModuleOptions } from '@nestjs/terminus';
    import { HealthController } from './health.controller';
    // import { TypeOrmHealthIndicator, HttpHealthIndicator, ... } from '@nestjs/terminus';
    // Potentially custom indicators like KafkaHealthIndicator

    // Function to build TerminusModuleOptions based on SharedHealthModuleOptions
    const createTerminusOptions = (options: SharedHealthModuleOptions): TerminusModuleOptions => {
      const indicators = [];
      // if (options.checkDatabase) { indicators.push(/* database indicator setup */); }
      // if (options.checkKafka) { indicators.push(/* kafka indicator setup */); }
      // ... and so on
      return {
        endpoints: [{
          url: options.endpointUrl || '/health',
          healthIndicators: indicators,
        }],
      };
    };

    export interface SharedHealthModuleOptions {
      endpointUrl?: string;
      checkDatabase?: boolean; // Or more specific DB options
      checkKafka?: boolean;    // Or more specific Kafka options
      // ... other common checks
    }

    @Module({})
    export class SharedHealthModule {
      static forRoot(options: SharedHealthModuleOptions = {}): DynamicModule {
        return {
          module: SharedHealthModule,
          imports: [
            TerminusModule.forRootAsync({
              useFactory: () => createTerminusOptions(options),
            }),
          ],
          controllers: [HealthController], // HealthController would use HealthCheckService from Terminus
        };
      }
    }
    ```
*   **`HealthController`:** A controller provided by the module that uses `@nestjs/terminus`'s `HealthCheckService` and `HealthCheck` decorator.
    ```typescript
    // health.controller.ts
    import { Controller, Get } from '@nestjs/common';
    import {
      HealthCheckService,
      HealthCheck,
      TypeOrmHealthIndicator, // Example
      // KafkaHealthIndicator, // Custom example
    } from '@nestjs/terminus';

    @Controller('health') // Path can be made configurable via module options
    export class HealthController {
      constructor(
        private health: HealthCheckService,
        private db: TypeOrmHealthIndicator, // Injected if enabled
        // private kafka: KafkaHealthIndicator, // Injected if enabled
      ) {}

      @Get()
      @HealthCheck()
      check() {
        // Build the array of checks dynamically based on module configuration
        const checks = [];
        if (this.db) { // Check if db indicator was provided/enabled
          checks.push(() => this.db.pingCheck('database', { timeout: 300 }));
        }
        // if (this.kafka) {
        //   checks.push(() => this.kafka.isHealthy('kafka'));
        // }
        // checks.push(() => this.memory.checkHeap('memory_heap', 150 * 1024 * 1024));
        // checks.push(() => this.disk.checkStorage('storage', { thresholdPercent: 0.5, path: '/' }));
        
        return this.health.check(checks);
      }
    }
    ```
*   **Custom Indicators:** Services can still inject `HealthCheckService` and their own custom Terminus indicators if they have unique health check needs not covered by the shared module.

## 4. Usage

1.  **Import and Configure:** Import `SharedHealthModule.forRoot(...)` into the root `AppModule` of a service, specifying which common checks to enable.
    ```typescript
    // app.module.ts
    import { Module } from '@nestjs/common';
    import { SharedHealthModule } from '@my-org/nestjs-core-utils';
    import { TypeOrmModule } from '@nestjs/typeorm'; // Assuming TypeORM is used

    @Module({
      imports: [
        // ... other modules like TypeOrmModule.forRootAsync(...)
        SharedHealthModule.forRoot({
          endpointUrl: '/healthz', // Optional: override default /health
          checkDatabase: true,      // Enable default DB check
          // checkKafka: true,
        }),
      ],
    })
    export class AppModule {}
    ```
2.  **Kubernetes Probes:** Configure Kubernetes liveness and readiness probes to use the exposed health check endpoint.
    *   **Liveness Probe:** Typically points to the health endpoint. If it fails, the container is restarted.
    *   **Readiness Probe:** Also points to the health endpoint. If it fails, the container is not sent traffic. This ensures dependencies are healthy before the service accepts requests.

## 5. Benefits

*   **Standardization:** Consistent health check endpoint and response format across all services.
*   **Simplified Setup:** Reduces boilerplate for setting up health checks in each service.
*   **Improved Reliability:** Helps orchestration platforms like Kubernetes manage application lifecycle more effectively, leading to higher availability.
*   **Operational Insight:** Provides a quick way to check the status of a service and its key dependencies.

This `HealthModule` will be an important component for ensuring the operational robustness of the microservices.