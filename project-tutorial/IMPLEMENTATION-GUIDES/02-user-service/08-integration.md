# Integration

## 🎯 Objective

Connect the User Service to infrastructure and other services.

## 🔧 Database Configuration

### `src/app.module.ts`
```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule } from '@nestjs/config';
import { User } from './entities/user.entity';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';

@Module({
  imports: [
    ConfigModule.forRoot(),
    TypeOrmModule.forRoot({
      type: 'postgres',
      url: process.env.DATABASE_URL,
      entities: [User],
      synchronize: true, // Only for development
    }),
    AuthModule,
    UsersModule,
  ],
})
export class AppModule {}
```

## 🔧 Start Service

```bash
# Run database migrations
pnpm run migration:run

# Start development server
pnpm run start:dev

# Test endpoints
curl -X POST http://localhost:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

## 📋 Integration Standards

Following **[Microservice Architecture Standards](../../architecture/quality-standards/microservice-architecture-standards.md)**:
- ✅ Environment-based configuration
- ✅ Health checks
- ✅ Service discovery ready

## 🎉 User Service Complete!

Your User Service is now ready! Continue to **[Product Service Tutorial](../03-product-service/README.md)**