# 03: Configuration Management

Effective configuration management is essential for the User Service to operate consistently and reliably across different deployment environments (Development, Staging, Production). This document outlines the strategies for managing application configuration.

## 1. Sources of Configuration

The User Service will primarily draw its configuration from the following sources, following the 12-Factor App methodology (Store config in the environment):

*   **Environment Variables**: The most common and recommended way to supply configuration to the application, especially within containerized environments like Kubernetes.
    *   Examples: Database connection strings (or components thereof), Kafka broker addresses, port numbers, log levels, JWT issuer/audience, external service URLs (HIBP, CAPTCHA).
    *   In Kubernetes, environment variables can be injected into pods directly in the Deployment manifest or via ConfigMaps and Secrets.

*   **Configuration Files (Limited Use)**:
    *   While environment variables are preferred, static configurations that don't change per environment or rarely change can be bundled with the application (e.g., default settings, static lookup tables if small).
    *   If used, these should be read-only and potentially overridable by environment variables.
    *   Example: Default pagination size, default role names (if not managed via DB).
    *   Framework-specific configuration files (e.g., NestJS module configurations) are part of the application code but can be parameterized using environment variables.

*   **Command-Line Arguments (Minimal Use)**:
    *   Typically not the primary method for service configuration but might be used for very specific overrides during startup or for CLI tools associated with the service (if any).

## 2. Kubernetes ConfigMaps and Secrets

Kubernetes provides native resources for managing configuration:

*   **ConfigMaps**: Used to store non-confidential configuration data as key-value pairs or as embedded configuration files.
    *   Can be mounted as volumes into pods or injected as environment variables.
    *   Suitable for: Log levels, external service URLs (non-sensitive parts), feature flags, application behavior settings.
    *   **Example (`ConfigMap` YAML)**:
        ```yaml
        apiVersion: v1
        kind: ConfigMap
        metadata:
          name: user-service-config
        data:
          LOG_LEVEL: "info"
          KAFKA_CLIENT_ID: "user-service"
          PAGINATION_DEFAULT_LIMIT: "20"
        ```

*   **Secrets**: Used for sensitive data like passwords, API keys, and TLS certificates.
    *   Stored more securely by Kubernetes (though etcd encryption should be enabled for true at-rest protection).
    *   Can also be mounted as volumes or injected as environment variables.
    *   Suitable for: Database credentials, JWT signing keys, API tokens for external services.
    *   **Example (Injecting Secret as Env Var)**:
        ```yaml
        # ... (Deployment Spec) ...
        env:
          - name: DATABASE_PASSWORD
            valueFrom:
              secretKeyRef:
                name: user-service-db-credentials
                key: password
        ```

## 3. Centralized Configuration Service (Future Consideration)

For more complex scenarios or as the system scales, integrating with a dedicated centralized configuration service might be beneficial:

*   **Examples**: HashiCorp Consul, AWS AppConfig, Azure App Configuration, Spring Cloud Config Server (if a Java-based config server is acceptable in a polyglot environment).
*   **Benefits**:
    *   Dynamic configuration updates without service restarts.
    *   Version control for configurations.
    *   Hierarchical configuration management.
    *   Auditing and access control for configuration changes.
*   **Integration**: The User Service would need a client library to fetch configuration from such a service at startup and potentially subscribe to updates.
*   **Current Stance**: While not a day-1 requirement, the architecture should be flexible enough to accommodate this in the future if needed. Initially, Kubernetes ConfigMaps and Secrets provide sufficient capability.

## 4. Configuration Schema and Validation

*   It's good practice to define a clear schema for the application's configuration (e.g., using a TypeScript interface or class with decorators like `class-validator` in NestJS).
*   The application should validate its configuration at startup and fail fast if required configurations are missing or invalid. This prevents runtime errors due to misconfiguration.
*   NestJS provides robust mechanisms for configuration management (e.g., `@nestjs/config` module) that supports environment variables, `.env` files, and custom configuration file loading, along with validation using Joi or `class-validator`.

### Example (NestJS Config with Validation)

```typescript
// config.schema.ts
import * as Joi from 'joi';

export const validationSchema = Joi.object({
  NODE_ENV: Joi.string().valid('development', 'production', 'test').default('development'),
  PORT: Joi.number().default(3000),
  DATABASE_HOST: Joi.string().required(),
  DATABASE_PORT: Joi.number().default(5432),
  DATABASE_USER: Joi.string().required(),
  DATABASE_PASSWORD: Joi.string().required(),
  DATABASE_NAME: Joi.string().required(),
  KAFKA_BROKERS: Joi.string().required(), // e.g., "broker1:9092,broker2:9092"
  JWT_SECRET: Joi.string().required(),
  JWT_EXPIRES_IN: Joi.string().default('1h'),
});

// app.module.ts (excerpt)
import { ConfigModule } from '@nestjs/config';
import { validationSchema } from './config.schema';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      validationSchema: validationSchema,
      // load: [configuration], // Optional: for custom config loading logic
    }),
    // ... other modules
  ],
})
export class AppModule {}
```

## 5. Best Practices

*   **Environment Specificity**: Configurations should be easily adaptable per environment without code changes.
*   **Security**: Sensitive data must always be managed through secure mechanisms (Kubernetes Secrets, external secret managers).
*   **Auditability**: Changes to configurations, especially in production, should be auditable (provided by Kubernetes API audit logs or version control if using GitOps for manifests).
*   **Clarity**: Configuration keys should be clearly named and documented.

By adhering to these principles, the User Service's configuration will be manageable, secure, and adaptable to the needs of various deployment environments.
