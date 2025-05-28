# Testing

## 🎯 Objective

Implement comprehensive testing for the User Service.

## 🔧 Unit Tests

### `src/auth/auth.service.spec.ts`
```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { AuthService } from './auth.service';
import { getRepositoryToken } from '@nestjs/typeorm';
import { JwtService } from '@nestjs/jwt';
import { User } from '../entities/user.entity';

describe('AuthService', () => {
  let service: AuthService;
  let mockUserRepository;

  beforeEach(async () => {
    mockUserRepository = {
      findOne: jest.fn(),
      create: jest.fn(),
      save: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuthService,
        { provide: getRepositoryToken(User), useValue: mockUserRepository },
        { provide: JwtService, useValue: { sign: jest.fn() } },
      ],
    }).compile();

    service = module.get<AuthService>(AuthService);
  });

  it('should register a new user', async () => {
    mockUserRepository.findOne.mockResolvedValue(null);
    mockUserRepository.create.mockReturnValue({ email: 'test@example.com' });
    mockUserRepository.save.mockResolvedValue({ id: '1', email: 'test@example.com' });

    const result = await service.register('test@example.com', 'password');
    expect(result.email).toBe('test@example.com');
  });
});
```

## 📋 Testing Standards

Following testing best practices:
- ✅ Unit tests for services
- ✅ Integration tests for controllers
- ✅ Mocked dependencies

## ✅ Next Step

Continue to **[08-integration.md](./08-integration.md)**