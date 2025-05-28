# Tutorial 16: Create Shared Authentication Library

## 🎯 Objective

Create a reusable authentication library that other services (like Product Service) can use to validate JWT tokens and check user permissions.

## 📚 Why This is Needed

The Product Service needs to:
- ✅ Validate JWT tokens from User Service
- ✅ Check user permissions for admin operations
- ✅ Extract user context from requests
- ✅ Share authentication logic without code duplication

## Step 1: Create Shared Library Structure

### 1.1 Create Auth Library Package
```bash
# In the workspace root
mkdir -p shared-libraries/auth-client-utils
cd shared-libraries/auth-client-utils

# Initialize npm package
npm init -y
```

### 1.2 Install Dependencies
```bash
npm install @nestjs/common @nestjs/jwt @nestjs/passport passport-jwt
npm install -D typescript @types/passport-jwt
```

### 1.3 Package Configuration
```json
{
  "name": "@ecommerce/auth-client-utils",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  },
  "peerDependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/jwt": "^10.0.0"
  }
}
```## Step 2: JWT Validation Guard

### 2.1 JWT Strategy
```typescript
// src/strategies/jwt.strategy.ts
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';

export interface JwtPayload {
  sub: string;
  email: string;
  roles: string[];
  permissions: string[];
}

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor() {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: process.env.JWT_SECRET,
    });
  }

  async validate(payload: JwtPayload) {
    if (!payload.sub || !payload.email) {
      throw new UnauthorizedException('Invalid token payload');
    }
    
    return {
      userId: payload.sub,
      email: payload.email,
      roles: payload.roles || [],
      permissions: payload.permissions || [],
    };
  }
}
```

### 2.2 Authentication Guard
```typescript
// src/guards/jwt-auth.guard.ts
import { Injectable } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {}
```

### 2.3 Role Guard
```typescript
// src/guards/roles.guard.ts
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<string[]>('roles', [
      context.getHandler(),
      context.getClass(),
    ]);

    if (!requiredRoles) {
      return true;
    }

    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some((role) => user.roles?.includes(role));
  }
}
```## Step 3: Decorators and Module

### 3.1 Role Decorator
```typescript
// src/decorators/roles.decorator.ts
import { SetMetadata } from '@nestjs/common';

export const Roles = (...roles: string[]) => SetMetadata('roles', roles);
```

### 3.2 User Decorator
```typescript
// src/decorators/user.decorator.ts
import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export const CurrentUser = createParamDecorator(
  (data: unknown, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    return request.user;
  },
);
```

### 3.3 Auth Module
```typescript
// src/auth.module.ts
import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { JwtStrategy } from './strategies/jwt.strategy';
import { JwtAuthGuard } from './guards/jwt-auth.guard';
import { RolesGuard } from './guards/roles.guard';

@Module({
  imports: [
    PassportModule,
    JwtModule.register({
      secret: process.env.JWT_SECRET,
      signOptions: { expiresIn: '1h' },
    }),
  ],
  providers: [JwtStrategy, JwtAuthGuard, RolesGuard],
  exports: [JwtAuthGuard, RolesGuard, JwtModule],
})
export class AuthClientModule {}
```

### 3.4 Main Export File
```typescript
// src/index.ts
export * from './auth.module';
export * from './guards/jwt-auth.guard';
export * from './guards/roles.guard';
export * from './decorators/roles.decorator';
export * from './decorators/user.decorator';
export * from './strategies/jwt.strategy';
```

## Step 4: Build and Publish

### 4.1 TypeScript Configuration
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### 4.2 Build the Library
```bash
npm run build
```

## ✅ Next Step

Auth library ready? Continue to **[17-event-messaging-library.md](./17-event-messaging-library.md)**