# User Management

## 🎯 Objective

Implement user profile management and role-based access control.

## 🔧 User Profile Service

### `src/users/users.service.ts`
```typescript
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../entities/user.entity';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
  ) {}

  async findById(id: string): Promise<User> {
    return this.userRepository.findOne({ where: { id } });
  }

  async updateProfile(id: string, updateData: Partial<User>): Promise<User> {
    await this.userRepository.update(id, updateData);
    return this.findById(id);
  }

  async updateLastLogin(id: string): Promise<void> {
    await this.userRepository.update(id, { lastLoginAt: new Date() });
  }
}
```

## 📋 Quality Standards

Following **[API Design Standards](../../architecture/quality-standards/api-design-standards.md)**:
- ✅ Service layer separation
- ✅ Repository pattern for data access
- ✅ Type safety with TypeScript

## ✅ Next Step

Continue to **[05-api-implementation.md](./05-api-implementation.md)**