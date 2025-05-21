# 10: `ConfigurationService` (NestJS @nestjs/config)

Within the Payment Service, robust and secure configuration management is essential, particularly for handling sensitive data like API keys for payment gateways, webhook secrets, and database credentials.

## Recommendation: NestJS `ConfigModule` (`@nestjs/config`)

The primary mechanism for managing configuration within the NestJS application will be the official **`@nestjs/config`** module. This module provides a flexible and powerful way to handle application configuration from various sources.

## Key Features and Usage

1.  **Environment Variables**: The preferred method for supplying configuration, especially in containerized environments (Docker, Kubernetes). `@nestjs/config` seamlessly integrates with environment variables.

2.  **`.env` File Support**: Supports loading configuration from `.env` files (e.g., `.env.development`, `.env.production`), which is useful for local development and can be excluded from version control.

3.  **Custom Configuration Files**: Allows loading of custom configuration files (e.g., `config.ts` or `configuration.ts`) where configuration can be structured and typed.
    ```typescript
    // example: configuration.ts
    export default () => ({
      port: parseInt(process.env.PORT, 10) || 3000,
      database: {
        host: process.env.DATABASE_HOST,
        port: parseInt(process.env.DATABASE_PORT, 10) || 5432
      },
      stripe: {
        apiKey: process.env.STRIPE_API_KEY,
        webhookSecret: process.env.STRIPE_WEBHOOK_SECRET
      }
    });
    ```

4.  **Validation**: Supports schema validation for configuration variables using Joi or `class-validator`. This ensures that all required configurations are present and valid at application startup, preventing runtime errors due to misconfiguration.
    ```typescript
    // Example with Joi validation in app.module.ts
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration], // from configuration.ts
      validationSchema: Joi.object({
        DATABASE_HOST: Joi.string().required(),
        STRIPE_API_KEY: Joi.string().required(),
        STRIPE_WEBHOOK_SECRET: Joi.string().required(),
        // ... other validations
      })
    });
    ```

5.  **Injection**: The `ConfigService` provided by the module can be injected into any service or controller to access configuration values in a type-safe manner.
    ```typescript
    constructor(private configService: ConfigService) {
      const stripeApiKey = this.configService.get<string>('stripe.apiKey');
    }
    ```

6.  **Security for Sensitive Data**: 
    *   Sensitive data like API keys and secrets **must not** be hardcoded or committed to version control.
    *   They should be supplied via environment variables, which can be securely injected into the deployment environment (e.g., using Kubernetes Secrets).
    *   Refer to section `07-deployment-operations/03-configuration-management.md` for broader strategies on how these environment variables are populated and managed in different environments, including integration with secret management systems like HashiCorp Vault or AWS Secrets Manager.

## Role of this "Service"

This `ConfigurationService` is not a custom-built service in the same vein as others in this section. Instead, it refers to the **usage and proper configuration of NestJS's `@nestjs/config` module** as the designated way to handle application configuration within the Payment Service.

All services requiring configuration (e.g., `PaymentGatewayIntegrationService` needing API keys, `WebhookHandlerService` needing webhook secrets) will inject and use the `ConfigService` from `@nestjs/config`.

## Further Details

Detailed strategies for how configurations are managed across different environments (development, staging, production), including the use of Kubernetes ConfigMaps and Secrets, and integration with external secret managers, are covered in the **`08-deployment-operations/03-configuration-management.md`** document.

This approach ensures that configuration is handled consistently, securely, and in a way that is idiomatic to the NestJS framework.
