# Security Considerations Specification

## Overview

This document outlines the security considerations and implementations for the Product Service data model, including data protection, access control, and audit logging.

## Data Protection

### 1. Data Encryption

```typescript
// src/common/security/encryption.service.ts
@Injectable()
export class EncryptionService {
    private readonly algorithm = 'aes-256-gcm';
    private readonly key: Buffer;

    constructor(private readonly configService: ConfigService) {
        this.key = Buffer.from(configService.get('ENCRYPTION_KEY'), 'hex');
    }

    async encrypt(data: string): Promise<string> {
        const iv = crypto.randomBytes(12);
        const cipher = crypto.createCipheriv(this.algorithm, this.key, iv);
        
        let encrypted = cipher.update(data, 'utf8', 'hex');
        encrypted += cipher.final('hex');
        
        const authTag = cipher.getAuthTag();
        
        return JSON.stringify({
            iv: iv.toString('hex'),
            encrypted,
            authTag: authTag.toString('hex')
        });
    }

    async decrypt(encryptedData: string): Promise<string> {
        const { iv, encrypted, authTag } = JSON.parse(encryptedData);
        
        const decipher = crypto.createDecipheriv(
            this.algorithm,
            this.key,
            Buffer.from(iv, 'hex')
        );
        
        decipher.setAuthTag(Buffer.from(authTag, 'hex'));
        
        let decrypted = decipher.update(encrypted, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        
        return decrypted;
    }
}
```

### 2. Sensitive Data Handling

```typescript
// src/common/security/sensitive-data.decorator.ts
export function SensitiveData() {
    return function (target: any, propertyKey: string) {
        const metadata = Reflect.getMetadata('design:type', target, propertyKey);
        
        if (metadata === String) {
            const originalValue = target[propertyKey];
            Object.defineProperty(target, propertyKey, {
                get: function() {
                    return this.encryptionService.decrypt(originalValue);
                },
                set: function(value: string) {
                    this.encryptionService.encrypt(value).then(encrypted => {
                        originalValue = encrypted;
                    });
                }
            });
        }
    };
}
```

## Access Control

### 1. Role-Based Access Control (RBAC)

```typescript
// src/common/security/rbac.guard.ts
@Injectable()
export class RbacGuard implements CanActivate {
    constructor(
        private readonly reflector: Reflector,
        private readonly userService: UserService
    ) {}

    async canActivate(context: ExecutionContext): Promise<boolean> {
        const requiredRoles = this.reflector.get<string[]>('roles', context.getHandler());
        if (!requiredRoles) {
            return true;
        }

        const request = context.switchToHttp().getRequest();
        const user = await this.userService.findById(request.user.id);

        return requiredRoles.some(role => user.roles.includes(role));
    }
}
```

### 2. Resource-Based Access Control

```typescript
// src/common/security/resource.guard.ts
@Injectable()
export class ResourceGuard implements CanActivate {
    constructor(
        private readonly reflector: Reflector,
        private readonly productService: ProductService
    ) {}

    async canActivate(context: ExecutionContext): Promise<boolean> {
        const request = context.switchToHttp().getRequest();
        const productId = request.params.id;
        const user = request.user;

        const product = await this.productService.findById(productId);
        return this.hasAccess(user, product);
    }

    private hasAccess(user: User, product: Product): boolean {
        // Implement access control logic
        return user.roles.includes('admin') || 
               product.ownerId === user.id;
    }
}
```

## Audit Logging

### 1. Audit Logger

```typescript
// src/common/security/audit.logger.ts
@Injectable()
export class AuditLogger {
    constructor(
        @InjectRepository(AuditLog)
        private readonly repository: Repository<AuditLog>
    ) {}

    async log(
        action: string,
        entity: string,
        entityId: string,
        userId: string,
        changes: any
    ): Promise<void> {
        const log = this.repository.create({
            action,
            entity,
            entityId,
            userId,
            changes,
            timestamp: new Date()
        });

        await this.repository.save(log);
    }
}
```

### 2. Audit Decorator

```typescript
// src/common/security/audit.decorator.ts
export function Audit(action: string) {
    return function (
        target: any,
        propertyKey: string,
        descriptor: PropertyDescriptor
    ) {
        const originalMethod = descriptor.value;

        descriptor.value = async function (...args: any[]) {
            const result = await originalMethod.apply(this, args);
            
            const auditLogger = this.auditLogger;
            const request = this.request;
            
            await auditLogger.log(
                action,
                target.constructor.name,
                result.id,
                request.user.id,
                args[0]
            );

            return result;
        };

        return descriptor;
    };
}
```

## Input Validation

### 1. Validation Pipes

```typescript
// src/common/validation/validation.pipe.ts
@Injectable()
export class ValidationPipe implements PipeTransform {
    constructor(private readonly schema: any) {}

    transform(value: any) {
        const { error, value: validatedValue } = this.schema.validate(value);
        
        if (error) {
            throw new BadRequestException(error.details);
        }
        
        return validatedValue;
    }
}
```

### 2. Custom Validators

```typescript
// src/common/validation/custom.validators.ts
export const customValidators = {
    isPrice: (value: number) => {
        return value > 0 && value <= 1000000;
    },
    
    isSku: (value: string) => {
        return /^[A-Z0-9]{3,10}$/.test(value);
    },
    
    isProductName: (value: string) => {
        return value.length >= 3 && value.length <= 100;
    }
};
```

## SQL Injection Prevention

### 1. Query Builder

```typescript
// src/common/security/query.builder.ts
export class SecureQueryBuilder {
    constructor(private readonly repository: Repository<any>) {}

    async findWithFilters(filters: any): Promise<any[]> {
        const queryBuilder = this.repository.createQueryBuilder('entity');

        for (const [key, value] of Object.entries(filters)) {
            if (this.isValidFilter(key)) {
                queryBuilder.andWhere(`entity.${key} = :${key}`, { [key]: value });
            }
        }

        return queryBuilder.getMany();
    }

    private isValidFilter(key: string): boolean {
        // Implement filter validation
        return true;
    }
}
```

### 2. Parameter Binding

```typescript
// src/common/security/parameter.binding.ts
export class ParameterBinding {
    static bindParameters(query: string, params: any): string {
        let boundQuery = query;
        
        for (const [key, value] of Object.entries(params)) {
            const placeholder = `:${key}`;
            const escapedValue = this.escapeValue(value);
            boundQuery = boundQuery.replace(placeholder, escapedValue);
        }
        
        return boundQuery;
    }

    private static escapeValue(value: any): string {
        if (typeof value === 'string') {
            return `'${value.replace(/'/g, "''")}'`;
        }
        return value;
    }
}
```

## Rate Limiting

### 1. Rate Limiter

```typescript
// src/common/security/rate.limiter.ts
@Injectable()
export class RateLimiter {
    private readonly store: Map<string, number[]> = new Map();
    private readonly windowMs: number = 60000; // 1 minute
    private readonly maxRequests: number = 100;

    async checkLimit(key: string): Promise<boolean> {
        const now = Date.now();
        const timestamps = this.store.get(key) || [];
        
        // Remove old timestamps
        const validTimestamps = timestamps.filter(
            timestamp => now - timestamp < this.windowMs
        );
        
        if (validTimestamps.length >= this.maxRequests) {
            return false;
        }
        
        validTimestamps.push(now);
        this.store.set(key, validTimestamps);
        
        return true;
    }
}
```

### 2. Rate Limit Guard

```typescript
// src/common/security/rate-limit.guard.ts
@Injectable()
export class RateLimitGuard implements CanActivate {
    constructor(
        private readonly rateLimiter: RateLimiter,
        private readonly configService: ConfigService
    ) {}

    async canActivate(context: ExecutionContext): Promise<boolean> {
        const request = context.switchToHttp().getRequest();
        const key = this.getKey(request);
        
        const allowed = await this.rateLimiter.checkLimit(key);
        
        if (!allowed) {
            throw new HttpException(
                'Too Many Requests',
                HttpStatus.TOO_MANY_REQUESTS
            );
        }
        
        return true;
    }

    private getKey(request: any): string {
        return `${request.ip}-${request.path}`;
    }
}
```

## Security Headers

### 1. Security Middleware

```typescript
// src/common/security/security.middleware.ts
@Injectable()
export class SecurityMiddleware implements NestMiddleware {
    use(req: Request, res: Response, next: Function) {
        // Set security headers
        res.setHeader('X-Content-Type-Options', 'nosniff');
        res.setHeader('X-Frame-Options', 'DENY');
        res.setHeader('X-XSS-Protection', '1; mode=block');
        res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
        res.setHeader('Content-Security-Policy', "default-src 'self'");
        
        next();
    }
}
```

### 2. CORS Configuration

```typescript
// src/config/cors.config.ts
export const corsConfig: CorsOptions = {
    origin: process.env.ALLOWED_ORIGINS.split(','),
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    exposedHeaders: ['X-Total-Count'],
    credentials: true,
    maxAge: 3600
};
```

## Best Practices

1. **Data Protection**
   - Encrypt sensitive data
   - Use secure storage
   - Implement data masking
   - Regular security audits

2. **Access Control**
   - Implement RBAC
   - Use resource-based access
   - Regular access reviews
   - Principle of least privilege

3. **Input Validation**
   - Validate all inputs
   - Use parameter binding
   - Implement rate limiting
   - Sanitize user input

4. **Audit Logging**
   - Log all sensitive operations
   - Include user context
   - Regular log reviews
   - Secure log storage

## References

- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [NestJS Security](https://docs.nestjs.com/security)
- [TypeORM Security](https://typeorm.io/#/security)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html) 