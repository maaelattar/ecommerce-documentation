# 04: RabbitMQ Configuration

## 1. Purpose

This document outlines how NestJS microservices will configure their connection to RabbitMQ (specifically Amazon MQ for RabbitMQ) and other related settings for the `rabbitmq-event-utils` shared library. Standardized configuration management is key for consistency across environments and ease of deployment.

Key objectives:
*   Leverage environment variables for RabbitMQ connection details and other parameters.
*   Integrate with the `SharedConfigModule` from `nestjs-core-utils` for validation and typed access if possible.
*   Provide clear guidance on essential configuration parameters for both producers and consumers.

## 2. Core Configuration Parameters

The following are essential configuration parameters needed by services to interact with RabbitMQ:

*   **`RABBITMQ_URL` (or `AMQP_URL`):**
    *   The AMQP connection string for the RabbitMQ broker (e.g., Amazon MQ endpoint).
    *   Example: `amqps://username:password@b-xxxx-yyyy-zzzz.mq.us-east-1.amazonaws.com:5671`
    *   This should include credentials. For local development, it might point to a local Dockerized RabbitMQ instance.
*   **`RABBITMQ_DEFAULT_SOURCE_SERVICE` (for Producer Module):**
    *   The name of the service publishing messages (e.g., "OrderService", "UserService"). Used to populate the `sourceService` field in the standard message envelope.
*   **`RABBITMQ_CONSUMER_QUEUE_NAME` (for Consumers using NestJS RMQ Transport):**
    *   The name of the primary queue the service instance will consume from.
*   **`RABBITMQ_PREFETCH_COUNT` (for Consumers using NestJS RMQ Transport):**
    *   The number of messages the broker will deliver to a consumer at a time before acknowledgements. Controls consumer throughput and fairness.
    *   Example: `10`
*   **`RABBITMQ_DEFAULT_EXCHANGE_NAME` (Optional, for Producer):**
    *   A default exchange name if services predominantly publish to one common exchange. However, it's often better to specify the exchange explicitly during publishing.
*   **Retry and DLX Configuration (Conceptual, for Consumer-side logic or queue setup):**
    *   `RABBITMQ_MAX_RETRIES`: Number of times to retry processing a message.
    *   `RABBITMQ_DLX_NAME`: Name of the Dead Letter Exchange to send failed messages to.
    *   These might not be direct library configs but rather conventions for services to implement using environment variables for their queue/retry setup.

## 3. Integration with `SharedConfigModule`

The `rabbitmq-event-utils` library, particularly its `RabbitMQProducerModule` and any consumer setup helpers, should be designed to easily consume these environment variables via NestJS's `ConfigService` (which is enhanced by our `SharedConfigModule` from `nestjs-core-utils`).

*   **Validation:** The `SharedConfigModule` in each service can be extended to validate these RabbitMQ-specific environment variables.

    ```typescript
    // Example: In a service's environment validation schema (e.g., my-service/config/environment.ts)
    // This would be used with SharedConfigModule.forRoot({ validationSchema: MyServiceEnvVars })
    import { IsString, IsNotEmpty, IsUrl, IsOptional, IsInt, Min } from 'class-validator';
    // import { BaseEnvironmentVariables } from '@my-org/nestjs-core-utils'; // Assuming this exists

    export class MyServiceEnvVars /* extends BaseEnvironmentVariables */ {
      @IsUrl({ protocols: ['amqp', 'amqps'], require_tld: false })
      @IsNotEmpty()
      RABBITMQ_URL: string;

      @IsString()
      @IsNotEmpty()
      RABBITMQ_DEFAULT_SOURCE_SERVICE: string; // For producer

      @IsString()
      @IsNotEmpty()
      @IsOptional() // Only if this service is a consumer
      RABBITMQ_CONSUMER_QUEUE_NAME?: string;

      @IsInt()
      @Min(1)
      @IsOptional() // Only if this service is a consumer
      RABBITMQ_PREFETCH_COUNT?: number;
    }
    ```

*   **Module Configuration:** The `RabbitMQProducerModule.forRootAsync()` (and any potential consumer module) would use `ConfigService` to fetch these validated variables:

    ```typescript
    // From 02-rabbitmq-producer-module.md example
    // RabbitMQProducerModule.forRootAsync factory:
    // ...
    useFactory: async (configService: ConfigService<MyServiceEnvVars>) => {
      const amqpUrl = configService.get('RABBITMQ_URL', { infer: true });
      const sourceService = configService.get('RABBITMQ_DEFAULT_SOURCE_SERVICE', { infer: true });
      // ... create and return RabbitMQProducerService instance
    }
    // ...
    ```

## 4. NestJS Microservice RMQ Transport Configuration (Consumers)

When configuring the NestJS RMQ transport for consumers, environment variables should also be used:

```typescript
// main.ts (or a dedicated module for microservice setup)
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { MicroserviceOptions, Transport } from '@nestjs/microservices';
import { ConfigService } from '@nestjs/config'; // Standard NestJS ConfigService
// import { MyServiceEnvVars } from './config/environment'; // For typed config

async function bootstrap() {
  const appContext = await NestFactory.createApplicationContext(AppModule); // Create context to access ConfigService
  const configService = appContext.get(ConfigService/*<MyServiceEnvVars>*/);

  const app = await NestFactory.createMicroservice<MicroserviceOptions>(AppModule, {
    transport: Transport.RMQ,
    options: {
      urls: [configService.get('RABBITMQ_URL')!],
      queue: configService.get('RABBITMQ_CONSUMER_QUEUE_NAME'),
      queueOptions: {
        durable: true,
        // It's good practice to define DLX arguments here if not done via IaC
        // arguments: {
        //   'x-dead-letter-exchange': configService.get('MY_SERVICE_DLX_NAME'),
        //   'x-dead-letter-routing-key': configService.get('MY_SERVICE_DLX_ROUTING_KEY')
        // }
      },
      noAck: false, // Explicitly require message acknowledgment
      prefetchCount: configService.get('RABBITMQ_PREFETCH_COUNT') || 10,
      persistent: true, // Ensure messages are persistent
    },
  });
  await app.listen();
  await appContext.close();
}
bootstrap();
```

## 5. Local Development Overrides

*   For local development, developers can use `.env` files (e.g., `.env.development.local` or `.env`) to specify connection details for a local RabbitMQ instance (e.g., running in Docker).
    *   `RABBITMQ_URL=amqp://guest:guest@localhost:5672`
    *   These `.env` files should be git-ignored.

## 6. Security of Credentials

*   The `RABBITMQ_URL` contains credentials.
*   In deployed environments (staging, production), this URL will be injected as an environment variable into the containers/pods by the orchestration platform (e.g., Kubernetes from a Secret).
*   Avoid committing `.env` files with production credentials to version control.

By standardizing how RabbitMQ connections and settings are configured, services can be set up more quickly and consistently, reducing the chances of misconfiguration across different environments.