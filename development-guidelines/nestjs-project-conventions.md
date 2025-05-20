# NestJS Project Conventions and Guidelines

This document outlines the standard conventions and guidelines to be followed for all NestJS microservice development within the e-commerce platform. Adhering to these conventions will ensure consistency, maintainability, and collaboration efficiency.

## 1. Coding Standards & Style Guide

*   **Automated Code Formatting:** Use **Prettier** for automated code formatting. A `.prettierrc.json` (or similar) file should be present in each project.
*   **Linting (ESLint):**
    *   Base Configuration: `eslint:recommended`.
    *   TypeScript Support: `plugin:@typescript-eslint/recommended`.
    *   Recommended Style Guide: Consider `eslint-config-airbnb-typescript` for a robust set of rules, adapting as necessary.
    *   Ensure ESLint configuration (e.g., `.eslintrc.js`) is present in each project.
*   **Naming Conventions:**
    *   **Modules, Services, Controllers, Entities, DTOs, Guards, Interceptors, Pipes:** PascalCase (e.g., `ProductModule`, `ProductService`, `CreateProductDto`).
    *   **Filenames:** Kebab-case (e.g., `product.module.ts`, `product.service.ts`, `create-product.dto.ts`).
    *   **Variables & Functions (including methods):** camelCase.
    *   **Constants & Enums:** UPPER_SNAKE_CASE for constants, PascalCase for Enum names and UPPER_SNAKE_CASE for enum members.
    *   **Interfaces:** Prefix with `I` (e.g., `IProductService`) or use PascalCase without a prefix if preferred by the team (decide and be consistent).

## 2. Directory Structure (Standard for a Microservice)

The NestJS CLI generates a good baseline. We will adopt the following extended structure:

```
service-name/
├── dist/                     # Compiled JavaScript files
├── node_modules/             # Project dependencies
├── src/                      # Source code
│   ├── app.controller.ts     # Root controller (often minimal)
│   ├── app.module.ts         # Root module
│   ├── app.service.ts        # Root service (often minimal)
│   ├── main.ts                 # Application bootstrap file
│   │
│   ├── config/                 # Configuration (e.g., database, env vars, using @nestjs/config)
│   │   ├── index.ts
│   │   └── app-config.module.ts
│   │
│   ├── common/                 # Shared utilities, interceptors, guards, decorators, pipes, constants
│   │   ├── decorators/
│   │   ├── guards/
│   │   ├── interceptors/
│   │   ├── pipes/
│   │   └── constants/
│   │
│   ├── modules/                # Feature modules (domain modules)
│   │   └── example-feature/    # Example: 'products' feature module
│   │       ├── controllers/
│   │       │   └── example-feature.controller.ts
│   │       ├── services/
│   │       │   └── example-feature.service.ts
│   │       ├── entities/
│   │       │   └── example-feature.entity.ts
│   │       ├── dto/
│   │       │   ├── create-example-feature.dto.ts
│   │       │   └── update-example-feature.dto.ts
│   │       ├── mappers/            # Optional: for mapping between DTOs and entities
│   │       │   └── example-feature.mapper.ts
│   │       └── example-feature.module.ts
│   │
│   └── database/               # Database related files (if service owns a DB)
│       ├── migrations/         # Database migrations (e.g., TypeORM)
│       └── typeorm.config.ts   # TypeORM configuration (example)
│
├── test/                     # Test files
│   ├── app.e2e-spec.ts       # End-to-end tests
│   ├── unit/                 # Unit tests, mirroring src structure (e.g., example-feature.service.spec.ts)
│   └── jest-e2e.json         # Jest config for E2E tests
│
├── .env.example              # Example environment file
├── .eslintrc.js              # ESLint configuration
├── .gitignore
├── .prettierrc.json          # Prettier configuration
├── nest-cli.json             # NestJS CLI configuration
├── package.json
├── README.md
├── tsconfig.build.json
└── tsconfig.json
```

## 3. Git & Version Control

*   **Branching Model:** Use Gitflow or GitHub flow (to be decided and documented separately if needed).
*   **Commit Messages:** Follow [Conventional Commits](https://www.conventionalcommits.org/) format (e.g., `feat: add product listing endpoint`, `fix: resolve issue with product price calculation`, `docs: update product API swagger`).
*   **`.gitignore`:** Ensure comprehensive `.gitignore` to exclude `node_modules/`, `dist/`, `.env` files (actual secrets), OS-specific files, IDE-specific files, and log files.

## 4. Configuration Management

*   **Environment Variables:** All external configurations (database credentials, API keys, ports, external service URLs, etc.) MUST be managed via environment variables.
*   **`@nestjs/config`:** Utilize the `@nestjs/config` module for loading and providing configuration. Support `.env` files for local development (ensure `.env` is in `.gitignore`).
*   **Validation:** Validate environment variables using Joi or class-validator with `@nestjs/config`.
*   **No Hardcoding:** Absolutely no hardcoding of secrets or environment-specific configurations in the codebase.

## 5. Logging

*   **Standard Logger:** Use NestJS's built-in `Logger` service as a baseline. For more advanced needs, consider `Winston` or `Pino`, ensuring consistent integration.
*   **JSON Format:** Configure logging to output in JSON format for easier parsing and ingestion by centralized logging systems (as per ADR-010).
*   **Correlation IDs:** Implement correlation IDs for tracing requests across services.
*   **Sensitive Data:** Ensure sensitive data (passwords, PII, API keys) is NOT logged.
*   **Log Levels:** Use appropriate log levels (DEBUG, INFO, WARN, ERROR).

## 6. Error Handling

*   **Built-in Exception Filters:** Leverage NestJS's built-in exception filters for common HTTP errors.
*   **Custom Exception Filters:** Create custom exception filters for application-specific errors or to standardize error response formats.
*   **Consistent Error Responses:** Define a standard JSON structure for error responses.

## 7. API Design

*   **RESTful Principles:** Adhere to RESTful API design principles.
*   **DTOs (Data Transfer Objects):** Use DTOs for request body validation (using `class-validator`) and for shaping response payloads.
*   **API Versioning:** Implement API versioning from the start (e.g., URI versioning: `/api/v1/products`). Refer to ADR-024 and ADR-034.
*   **OpenAPI/Swagger:** Automatically generate API documentation using `@nestjs/swagger`. Ensure DTOs and controllers are well-documented with decorators.

## 8. Asynchronous Programming

*   Utilize `async/await` for all asynchronous operations.
*   Leverage RxJS where appropriate if it simplifies complex event-based or stream-based logic, but use simple Promises for most cases.

## 9. Security

*   **Input Validation:** Always validate incoming data (DTOs with `class-validator`).
*   **Authentication & Authorization:** Implement as per ADR-005 (JWT-based) and ADR-019.
*   **Helmet:** Use Helmet.js for setting various HTTP headers to secure your application.
*   **CORS:** Configure CORS appropriately.
*   **Rate Limiting:** Implement rate limiting for public-facing APIs.
*   Refer to ADR-026 (Security Hardening) and ADR-036 (Application Security Deep Dive).

---
This document is a living document and will be updated as our practices evolve.
