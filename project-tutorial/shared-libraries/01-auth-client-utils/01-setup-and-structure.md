# 01. Setup and Package Structure

## Overview

Initialize the `@ecommerce/auth-client-utils` package with proper TypeScript configuration, dependencies, and project structure for a professional shared library.

## Package Structure

```
auth-client-utils/
├── src/
│   ├── guards/           # Authentication guards
│   ├── decorators/       # Parameter decorators
│   ├── interfaces/       # TypeScript interfaces
│   ├── modules/          # NestJS modules
│   ├── strategies/       # Passport strategies
│   └── index.ts          # Public API exports
├── test/                 # Test files
├── package.json
├── tsconfig.json
└── jest.config.js
```

## TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "declaration": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "test"]
}
```

## Core Interfaces

```typescript
// src/interfaces/user-context.interface.ts
export interface UserContext {
  userId: string;
  email: string;
  roles: string[];
  permissions: string[];
  customerId?: string;
  isActive: boolean;
  tokenIat: number;
  tokenExp: number;
}

export interface JwtPayload {
  sub: string;
  email: string;
  roles: string[];
  permissions: string[];
  customerId?: string;
  iat: number;
  exp: number;
  iss: string;
  aud: string;
}
```