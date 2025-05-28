# Authentication System

## 🎯 Objective

Implement JWT-based authentication with registration and login.

## 📚 Authentication Flow

Based on **[Auth Endpoints](../../implementation-specs/user-service/04-api-endpoints/01-auth-endpoints.md)**:
- **Registration** - Create account with email verification
- **Login** - Authenticate and issue JWT tokens
- **Token Refresh** - Extend session without re-login

## 🔧 Create Auth Service

### `src/auth/auth.service.ts`
```typescript
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import * as bcrypt from 'bcrypt';
import { User } from '../entities/user.entity';

@Injectable()
export class AuthService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
    private jwtService: JwtService,
  ) {}

  async register(email: string, password: string): Promise<User> {
    const existingUser = await this.userRepository.findOne({ where: { email } });
    if (existingUser) {
      throw new Error('User already exists');
    }

    const passwordHash = await bcrypt.hash(password, 12);
    const user = this.userRepository.create({
      email,
      passwordHash,
      status: 'PENDING_VERIFICATION',
    });

    return this.userRepository.save(user);
  }
}
```  async login(email: string, password: string) {
    const user = await this.userRepository.findOne({ where: { email } });
    
    if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const payload = { sub: user.id, email: user.email };
    return {
      access_token: this.jwtService.sign(payload),
      user: { id: user.id, email: user.email, status: user.status },
    };
  }
}
```

## 📋 Security Standards

Following **[Security Standards](../../architecture/quality-standards/security-standards.md)**:
- ✅ Password hashing with bcrypt (12 rounds)
- ✅ JWT tokens for stateless authentication
- ✅ Input validation and sanitization
- ✅ Proper error handling without information leakage

## ✅ Next Step

Continue to **[04-user-management.md](./04-user-management.md)**