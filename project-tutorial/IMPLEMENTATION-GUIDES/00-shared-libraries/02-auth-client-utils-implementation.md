# Auth Client Utils Implementation Guide 🔐

> **Goal**: Build comprehensive authentication and authorization utilities for secure microservices communication

---

## 🎯 **What You'll Build**

A complete authentication library with:
- **JWT token management** with refresh token rotation
- **Role-based access control** (RBAC) with permissions
- **Auth guards and decorators** for protecting endpoints
- **User context management** across request lifecycle
- **Service-to-service authentication** for microservices

---

## 📦 **Package Setup**

### **1. Initialize Package**
```bash
cd packages/auth-client-utils
npm init -y
```

### **2. Package.json Configuration**
```json
{
  "name": "@ecommerce/auth-client-utils",
  "version": "1.0.0",
  "description": "Authentication utilities for ecommerce microservices",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "test:watch": "jest --watch",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/jwt": "^10.0.0",
    "@nestjs/passport": "^10.0.0",
    "passport": "^0.6.0",
    "passport-jwt": "^4.0.0",
    "passport-local": "^1.0.0",
    "bcrypt": "^5.1.0",
    "class-validator": "^0.14.0",
    "class-transformer": "^0.5.0",
    "reflect-metadata": "^0.1.13"
  },
  "devDependencies": {
    "@types/bcrypt": "^5.0.0",
    "@types/passport-jwt": "^3.0.0",
    "@types/passport-local": "^1.0.0",
    "jest": "^29.0.0",
    "typescript": "^5.0.0"
  }
}
```

---

## 🏗️ **Implementation Structure**

```
packages/auth-client-utils/
├── src/
│   ├── types/
│   │   ├── user.types.ts
│   │   ├── auth.types.ts
│   │   └── index.ts
│   ├── decorators/
│   │   ├── auth.decorators.ts
│   │   ├── roles.decorators.ts
│   │   └── index.ts
│   ├── guards/
│   │   ├── jwt-auth.guard.ts
│   │   ├── roles.guard.ts
│   │   ├── local-auth.guard.ts
│   │   └── index.ts
│   ├── strategies/
│   │   ├── jwt.strategy.ts
│   │   ├── local.strategy.ts
│   │   └── index.ts
│   ├── services/
│   │   ├── auth.service.ts
│   │   ├── token.service.ts
│   │   └── index.ts
│   ├── middleware/
│   │   ├── auth.middleware.ts
│   │   └── index.ts
│   └── index.ts
└── tests/
```

---

## 🏷️ **1. Type Definitions**

### **User Types**
```typescript
// src/types/user.types.ts
export enum UserRole {
  ADMIN = 'admin',
  CUSTOMER = 'customer',
  VENDOR = 'vendor',
  SUPPORT = 'support'
}

export enum Permission {
  // User permissions
  USER_READ = 'user:read',
  USER_WRITE = 'user:write',
  USER_DELETE = 'user:delete',
  
  // Product permissions
  PRODUCT_READ = 'product:read',
  PRODUCT_WRITE = 'product:write',
  PRODUCT_DELETE = 'product:delete',
  
  // Order permissions
  ORDER_READ = 'order:read',
  ORDER_WRITE = 'order:write',
  ORDER_CANCEL = 'order:cancel',
  
  // Admin permissions
  ADMIN_ACCESS = 'admin:access',
  SYSTEM_CONFIG = 'system:config'
}

export interface UserPayload {
  sub: string; // User ID
  email: string;
  roles: UserRole[];
  permissions: Permission[];
  iat?: number;
  exp?: number;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  roles: UserRole[];
  permissions: Permission[];
  isActive: boolean;
  lastLoginAt?: Date;
}
```

### **Auth Types**
```typescript
// src/types/auth.types.ts
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RefreshTokenPayload {
  sub: string;
  tokenId: string;
  type: 'refresh';
}

export interface ServiceAuthPayload {
  serviceName: string;
  permissions: Permission[];
  type: 'service';
}

export interface JwtConfig {
  secret: string;
  accessTokenExpiresIn: string;
  refreshTokenExpiresIn: string;
  issuer: string;
  audience: string;
}
```

---

## 🎨 **2. Decorators Implementation**

### **Auth Decorators**
```typescript
// src/decorators/auth.decorators.ts
import { createParamDecorator, ExecutionContext } from '@nestjs/common';
import { AuthenticatedUser } from '../types/user.types';

export const CurrentUser = createParamDecorator(
  (data: keyof AuthenticatedUser | undefined, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    const user = request.user as AuthenticatedUser;
    
    return data ? user?.[data] : user;
  }
);

export const GetCorrelationId = createParamDecorator(
  (data: unknown, ctx: ExecutionContext): string => {
    const request = ctx.switchToHttp().getRequest();
    return request.correlationId || request.headers['x-correlation-id'];
  }
);

export const RequireServiceAuth = () => {
  return (target: any, propertyName: string, descriptor: PropertyDescriptor) => {
    // Mark endpoint as requiring service authentication
    Reflect.defineMetadata('require-service-auth', true, descriptor.value);
  };
};
```

### **Roles Decorators**
```typescript
// src/decorators/roles.decorators.ts
import { SetMetadata } from '@nestjs/common';
import { UserRole, Permission } from '../types/user.types';

export const ROLES_KEY = 'roles';
export const PERMISSIONS_KEY = 'permissions';

export const Roles = (...roles: UserRole[]) => 
  SetMetadata(ROLES_KEY, roles);

export const RequirePermissions = (...permissions: Permission[]) => 
  SetMetadata(PERMISSIONS_KEY, permissions);

export const Public = () => SetMetadata('isPublic', true);
```

---

## 🛡️ **3. Guards Implementation**

### **JWT Auth Guard**
```typescript
// src/guards/jwt-auth.guard.ts
import {
  Injectable,
  ExecutionContext,
  UnauthorizedException,
  CanActivate
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { JwtService } from '@nestjs/jwt';
import { Request } from 'express';
import { UserPayload } from '../types/user.types';

@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(
    private jwtService: JwtService,
    private reflector: Reflector
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    // Check if endpoint is marked as public
    const isPublic = this.reflector.getAllAndOverride<boolean>('isPublic', [
      context.getHandler(),
      context.getClass()
    ]);

    if (isPublic) {
      return true;
    }

    const request = context.switchToHttp().getRequest<Request>();
    const token = this.extractTokenFromHeader(request);

    if (!token) {
      throw new UnauthorizedException('Access token is required');
    }

    try {
      const payload = await this.jwtService.verifyAsync<UserPayload>(token);
      request.user = {
        id: payload.sub,
        email: payload.email,
        roles: payload.roles,
        permissions: payload.permissions,
        isActive: true
      };
      
      return true;
    } catch (error) {
      throw new UnauthorizedException('Invalid or expired token');
    }
  }

  private extractTokenFromHeader(request: Request): string | undefined {
    const [type, token] = request.headers.authorization?.split(' ') ?? [];
    return type === 'Bearer' ? token : undefined;
  }
}
```

### **Roles Guard**
```typescript
// src/guards/roles.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ROLES_KEY, PERMISSIONS_KEY } from '../decorators/roles.decorators';
import { UserRole, Permission, AuthenticatedUser } from '../types/user.types';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<UserRole[]>(
      ROLES_KEY,
      [context.getHandler(), context.getClass()]
    );

    const requiredPermissions = this.reflector.getAllAndOverride<Permission[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()]
    );

    if (!requiredRoles && !requiredPermissions) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const user: AuthenticatedUser = request.user;

    if (!user) {
      throw new ForbiddenException('User context not found');
    }

    // Check roles
    if (requiredRoles && !this.hasRequiredRoles(user.roles, requiredRoles)) {
      throw new ForbiddenException(
        `Required roles: ${requiredRoles.join(', ')}`
      );
    }

    // Check permissions
    if (requiredPermissions && !this.hasRequiredPermissions(user.permissions, requiredPermissions)) {
      throw new ForbiddenException(
        `Required permissions: ${requiredPermissions.join(', ')}`
      );
    }

    return true;
  }

  private hasRequiredRoles(userRoles: UserRole[], requiredRoles: UserRole[]): boolean {
    return requiredRoles.some(role => userRoles.includes(role));
  }

  private hasRequiredPermissions(userPermissions: Permission[], requiredPermissions: Permission[]): boolean {
    return requiredPermissions.every(permission => 
      userPermissions.includes(permission)
    );
  }
}
```

---

## 🔧 **4. Services Implementation**

### **Token Service**
```typescript
// src/services/token.service.ts
import { Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { 
  UserPayload, 
  TokenPair, 
  RefreshTokenPayload,
  ServiceAuthPayload 
} from '../types/auth.types';
import { v4 as uuidv4 } from 'uuid';

@Injectable()
export class TokenService {
  constructor(
    private jwtService: JwtService,
    private configService: ConfigService
  ) {}

  async generateTokenPair(payload: UserPayload): Promise<TokenPair> {
    const accessTokenExpiresIn = this.configService.get('JWT_ACCESS_EXPIRES_IN', '15m');
    const refreshTokenExpiresIn = this.configService.get('JWT_REFRESH_EXPIRES_IN', '7d');

    const [accessToken, refreshToken] = await Promise.all([
      this.jwtService.signAsync(payload, { expiresIn: accessTokenExpiresIn }),
      this.jwtService.signAsync(
        {
          sub: payload.sub,
          tokenId: uuidv4(),
          type: 'refresh'
        } as RefreshTokenPayload,
        { expiresIn: refreshTokenExpiresIn }
      )
    ]);

    return {
      accessToken,
      refreshToken,
      expiresIn: this.parseExpiresIn(accessTokenExpiresIn)
    };
  }

  async refreshAccessToken(refreshToken: string): Promise<TokenPair> {
    try {
      const payload = await this.jwtService.verifyAsync<RefreshTokenPayload>(refreshToken);
      
      if (payload.type !== 'refresh') {
        throw new Error('Invalid token type');
      }

      // In a real app, you'd validate the refresh token against a database
      // and potentially rotate it for security
      
      // Generate new token pair
      const userPayload: UserPayload = {
        sub: payload.sub,
        email: '', // Would fetch from user service
        roles: [], // Would fetch from user service
        permissions: [] // Would fetch from user service
      };

      return this.generateTokenPair(userPayload);
    } catch (error) {
      throw new Error('Invalid refresh token');
    }
  }

  async generateServiceToken(serviceName: string, permissions: Permission[]): Promise<string> {
    const payload: ServiceAuthPayload = {
      serviceName,
      permissions,
      type: 'service'
    };

    return this.jwtService.signAsync(payload, { expiresIn: '1h' });
  }

  async validateServiceToken(token: string): Promise<ServiceAuthPayload> {
    const payload = await this.jwtService.verifyAsync<ServiceAuthPayload>(token);
    
    if (payload.type !== 'service') {
      throw new Error('Invalid service token');
    }

    return payload;
  }

  private parseExpiresIn(expiresIn: string): number {
    // Convert string like '15m' to seconds
    const unit = expiresIn.slice(-1);
    const value = parseInt(expiresIn.slice(0, -1));

    switch (unit) {
      case 's': return value;
      case 'm': return value * 60;
      case 'h': return value * 3600;
      case 'd': return value * 86400;
      default: return 900; // 15 minutes default
    }
  }
}
```

### **Auth Service**
```typescript
// src/services/auth.service.ts
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { TokenService } from './token.service';
import { 
  LoginCredentials, 
  TokenPair, 
  UserPayload 
} from '../types/auth.types';
import { UserRole, Permission } from '../types/user.types';
import * as bcrypt from 'bcrypt';

@Injectable()
export class AuthService {
  constructor(private tokenService: TokenService) {}

  async validateUser(credentials: LoginCredentials): Promise<UserPayload | null> {
    // In a real app, this would call the user service to validate credentials
    // For now, we'll simulate user validation
    
    const { email, password } = credentials;
    
    // Simulate database lookup
    const user = await this.findUserByEmail(email);
    if (!user) {
      return null;
    }

    const isPasswordValid = await bcrypt.compare(password, user.passwordHash);
    if (!isPasswordValid) {
      return null;
    }

    return {
      sub: user.id,
      email: user.email,
      roles: user.roles,
      permissions: this.getRolePermissions(user.roles)
    };
  }

  async login(credentials: LoginCredentials): Promise<TokenPair> {
    const user = await this.validateUser(credentials);
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    return this.tokenService.generateTokenPair(user);
  }

  async refreshToken(refreshToken: string): Promise<TokenPair> {
    return this.tokenService.refreshAccessToken(refreshToken);
  }

  private async findUserByEmail(email: string) {
    // Simulate user lookup - in real app, this would be a database call
    const users = {
      'admin@example.com': {
        id: '1',
        email: 'admin@example.com',
        passwordHash: await bcrypt.hash('password', 10),
        roles: [UserRole.ADMIN]
      },
      'customer@example.com': {
        id: '2',
        email: 'customer@example.com',
        passwordHash: await bcrypt.hash('password', 10),
        roles: [UserRole.CUSTOMER]
      }
    };

    return users[email] || null;
  }

  private getRolePermissions(roles: UserRole[]): Permission[] {
    const rolePermissions = {
      [UserRole.ADMIN]: [
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.PRODUCT_READ,
        Permission.PRODUCT_WRITE,
        Permission.PRODUCT_DELETE,
        Permission.ORDER_READ,
        Permission.ORDER_WRITE,
        Permission.ORDER_CANCEL,
        Permission.ADMIN_ACCESS,
        Permission.SYSTEM_CONFIG
      ],
      [UserRole.CUSTOMER]: [
        Permission.PRODUCT_READ,
        Permission.ORDER_READ,
        Permission.ORDER_WRITE
      ],
      [UserRole.VENDOR]: [
        Permission.PRODUCT_READ,
        Permission.PRODUCT_WRITE,
        Permission.ORDER_READ
      ],
      [UserRole.SUPPORT]: [
        Permission.USER_READ,
        Permission.ORDER_READ,
        Permission.ORDER_WRITE
      ]
    };

    return roles.reduce((permissions, role) => {
      return [...permissions, ...rolePermissions[role]];
    }, [] as Permission[]);
  }
}
```

---

## 🚀 **5. Strategies Implementation**

### **JWT Strategy**
```typescript
// src/strategies/jwt.strategy.ts
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { ConfigService } from '@nestjs/config';
import { UserPayload, AuthenticatedUser } from '../types/user.types';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(configService: ConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: configService.get('JWT_SECRET'),
      issuer: configService.get('JWT_ISSUER'),
      audience: configService.get('JWT_AUDIENCE')
    });
  }

  async validate(payload: UserPayload): Promise<AuthenticatedUser> {
    if (!payload.sub) {
      throw new UnauthorizedException('Invalid token payload');
    }

    // In a real app, you might want to validate the user still exists
    // and is active in the database

    return {
      id: payload.sub,
      email: payload.email,
      roles: payload.roles,
      permissions: payload.permissions,
      isActive: true
    };
  }
}
```

---

## 📤 **6. Main Export File**

```typescript
// src/index.ts
// Types
export * from './types';

// Decorators
export * from './decorators';

// Guards
export * from './guards';

// Strategies
export * from './strategies';

// Services
export * from './services';

// Auth Module
export { AuthModule } from './auth.module';
```

### **Auth Module**
```typescript
// src/auth.module.ts
import { Global, Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { ConfigModule, ConfigService } from '@nestjs/config';

import { AuthService } from './services/auth.service';
import { TokenService } from './services/token.service';
import { JwtStrategy } from './strategies/jwt.strategy';
import { JwtAuthGuard } from './guards/jwt-auth.guard';
import { RolesGuard } from './guards/roles.guard';

@Global()
@Module({
  imports: [
    PassportModule,
    JwtModule.registerAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        secret: configService.get('JWT_SECRET'),
        signOptions: {
          expiresIn: configService.get('JWT_ACCESS_EXPIRES_IN', '15m'),
          issuer: configService.get('JWT_ISSUER', 'ecommerce-platform'),
          audience: configService.get('JWT_AUDIENCE', 'ecommerce-services')
        }
      }),
      inject: [ConfigService]
    })
  ],
  providers: [
    AuthService,
    TokenService,
    JwtStrategy,
    JwtAuthGuard,
    RolesGuard
  ],
  exports: [
    AuthService,
    TokenService,
    JwtAuthGuard,
    RolesGuard,
    JwtModule
  ]
})
export class AuthModule {}
```

---

## 🧪 **Testing Example**

```typescript
// tests/auth.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { JwtModule } from '@nestjs/jwt';
import { ConfigModule } from '@nestjs/config';
import { AuthService } from '../src/services/auth.service';
import { TokenService } from '../src/services/token.service';

describe('AuthService', () => {
  let service: AuthService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({
          isGlobal: true,
          envFilePath: '.env.test'
        }),
        JwtModule.register({
          secret: 'test-secret',
          signOptions: { expiresIn: '1h' }
        })
      ],
      providers: [AuthService, TokenService]
    }).compile();

    service = module.get<AuthService>(AuthService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should validate user credentials', async () => {
    const credentials = {
      email: 'admin@example.com',
      password: 'password'
    };

    const user = await service.validateUser(credentials);
    expect(user).toBeDefined();
    expect(user?.email).toBe(credentials.email);
  });

  it('should return null for invalid credentials', async () => {
    const credentials = {
      email: 'invalid@example.com',
      password: 'wrongpassword'
    };

    const user = await service.validateUser(credentials);
    expect(user).toBeNull();
  });
});
```

---

## ✅ **Validation Steps**

1. **Build the package**: `npm run build`
2. **Run tests**: `npm run test`
3. **Test token generation** and validation
4. **Verify guard functionality** with test endpoints

---

## 🔗 **Next Step**

Once complete, move to [RabbitMQ Event Utils Implementation](./03-rabbitmq-event-utils-implementation.md) to build event messaging utilities.

This authentication library provides enterprise-grade security for your microservices! 🔐