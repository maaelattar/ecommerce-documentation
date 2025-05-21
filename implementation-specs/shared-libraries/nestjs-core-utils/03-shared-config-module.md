# 03: Shared Configuration Module (`SharedConfigModule`)

## 1. Purpose

The `SharedConfigModule` within the `nestjs-core-utils` library aims to provide a standardized and simplified way for NestJS microservices to load, validate, and access environment-specific configurations. It builds upon NestJS's own `@nestjs/config` module, offering common patterns and potentially base validation schemas.

Key objectives:
*   Promote a consistent approach to configuration management across all services.
*   Simplify the setup of typed configurations.
*   Provide out-of-the-box validation for common environment variables.
*   Integrate seamlessly with Kubernetes ConfigMaps and Secrets (via environment variables).

## 2. Features

*   **Wrapper around `@nestjs/config`:** Provides a pre-configured dynamic module that sets up common options for `@nestjs/config`.
*   **Environment Variable Prioritization:** Primarily sources configuration from environment variables, aligning with 12-factor app principles and containerized deployments.
*   **`.env` File Support:** Supports `.env` files for local development convenience (e.g., `development.env`, `.env`). These should be ignored by Git.
*   **Typed Configuration:** Facilitates the use of strongly-typed configuration objects, improving developer experience and reducing runtime errors.
*   **Validation:**
    *   Integrates `class-validator` for validating the structure and values of configuration variables at application startup.
    *   Optionally provides a base validation schema for common platform-wide environment variables (e.g., `NODE_ENV`, `PORT`, `LOG_LEVEL`, `SERVICE_NAME`).
*   **Expandable:** Allows individual services to easily extend the base configuration with their own service-specific variables and validation rules.

## 3. Implementation Considerations

*   **Dynamic Module (`forRoot` or `forRootAsync`):**
    ```typescript
    // shared-config.module.ts (simplified example)
    import { DynamicModule, Global, Module } from '@nestjs/common';
    import { ConfigModule, ConfigService } from '@nestjs/config';
    import { plainToClass } from 'class-transformer';
    import { validateSync } from 'class-validator';

    // Example Base Environment Variables Class (can be part of the shared library)
    // Services can extend this or provide their own specific to their needs
    export class BaseEnvironmentVariables {
      // @IsString()
      // @IsNotEmpty()
      NODE_ENV: string = 'development';

      // @IsInt()
      // @Min(0)
      // @Max(65535)
      // @IsOptional()
      PORT: number = 3000;

      // @IsString()
      // @IsNotEmpty()
      LOG_LEVEL: string = 'info';
      
      // @IsString()
      // @IsNotEmpty()
      SERVICE_NAME: string;
    }

    export interface SharedConfigModuleOptions {
      // Schema for service-specific environment variables
      validationSchema?: new () => any; 
      // Path to .env file, e.g., `development.env` or `test.env`
      envFilePath?: string | string[]; 
    }

    @Global() // Make ConfigService available globally
    @Module({})
    export class SharedConfigModule {
      static forRoot(options: SharedConfigModuleOptions = {}): DynamicModule {
        const { validationSchema, envFilePath } = options;

        return {
          module: SharedConfigModule,
          imports: [
            ConfigModule.forRoot({
              isGlobal: true, // Make ConfigService available globally without importing ConfigModule everywhere
              envFilePath: envFilePath || [`.env.${process.env.NODE_ENV}.local`, `.env.${process.env.NODE_ENV}`, '.env.local', '.env'],
              ignoreEnvFile: process.env.NODE_ENV === 'production', // In prod, rely solely on env vars from orchestrator
              validate: (config) => {
                // Combine base validation with service-specific validation if provided
                const schemaToValidate = validationSchema 
                  ? class extends BaseEnvironmentVariables { constructor() { super(); Object.assign(this, new validationSchema()); } } 
                  : BaseEnvironmentVariables;
                
                const validatedConfig = plainToClass(schemaToValidate, config, {
                  enableImplicitConversion: true,
                });
                const errors = validateSync(validatedConfig, {
                  skipMissingProperties: false,
                });

                if (errors.length > 0) {
                  throw new Error(`Configuration validation error: ${errors.toString()}`);
                }
                return validatedConfig;
              },
            }),
          ],
          providers: [ConfigService], // Ensure ConfigService is explicitly provided and exported
          exports: [ConfigService],
        };
      }
    }
    ```
*   **`ConfigService` Usage:** Services will inject NestJS's standard `ConfigService` to access configuration values.
*   **Service-Specific Configuration:** Services can define their own `class` with `class-validator` decorators for their specific environment variables and pass this class to the `SharedConfigModule.forRoot({ validationSchema: MyServiceEnvVariables })`.

## 4. Usage

1.  **Define Service-Specific Env Class (Optional but Recommended):**
    ```typescript
    // in my-service/src/config/environment.ts
    import { IsString, IsNotEmpty, IsUrl } from 'class-validator';
    // import { BaseEnvironmentVariables } from '@my-org/nestjs-core-utils'; // If Base is provided

    export class MyServiceEnvironmentVariables /* extends BaseEnvironmentVariables */ {
      @IsUrl({ require_tld: false }) // Example: for localhost URLs too
      DATABASE_URL: string;

      @IsString()
      @IsNotEmpty()
      PAYMENT_GATEWAY_API_KEY: string;
    }
    ```

2.  **Import and Configure in `AppModule`:**
    ```typescript
    // app.module.ts
    import { Module } from '@nestjs/common';
    import { SharedConfigModule } from '@my-org/nestjs-core-utils';
    import { MyServiceEnvironmentVariables } from './config/environment';

    @Module({
      imports: [
        SharedConfigModule.forRoot({
          validationSchema: MyServiceEnvironmentVariables,
          // envFilePath: process.env.NODE_ENV === 'test' ? '.env.test' : undefined
        }),
        // ... other modules
      ],
    })
    export class AppModule {}
    ```

3.  **Inject `ConfigService` and Access Typed Config:**
    ```typescript
    // my.service.ts
    import { Injectable } from '@nestjs/common';
    import { ConfigService } from '@nestjs/config';
    import { MyServiceEnvironmentVariables } from './config/environment'; // For typing
    import { BaseEnvironmentVariables } from '@my-org/nestjs-core-utils'; // For typing base vars

    // Combine types for ConfigService.get()
    type AppEnvVars = MyServiceEnvironmentVariables & BaseEnvironmentVariables;

    @Injectable()
    export class MyDatabaseService {
      private dbUrl: string;
      private serviceName: string;

      constructor(private readonly configService: ConfigService<AppEnvVars>) {
        this.dbUrl = this.configService.get('DATABASE_URL', { infer: true });
        this.serviceName = this.configService.get('SERVICE_NAME', { infer: true });
        console.log(`Connecting to database at ${this.dbUrl} for service ${this.serviceName}`);
      }

      // ... service logic
    }
    ```

## 5. Key Benefits

*   **Early Validation:** Catches configuration errors at application startup rather than at runtime when a variable is first accessed.
*   **Type Safety:** Provides autocompletion and type checking for configuration variables within the service code.
*   **Consistency:** Ensures all services load and validate configurations in a similar manner.
*   **Reduced Boilerplate:** Minimizes the amount of configuration setup code required in each service.

This module streamlines configuration management, making services more robust and easier to develop and maintain.