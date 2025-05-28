# Validation & DTOs

## 🎯 Objective

Implement comprehensive validation and DTOs per implementation specs.

## 🔧 Install Validation

```bash
pnpm add class-validator class-transformer
```

## 📚 Auth DTOs

### Register DTO (`src/auth/dto/register.dto.ts`)
```typescript
import { IsEmail, IsString, MinLength, MaxLength, Matches } from 'class-validator';

export class RegisterDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  @MaxLength(128)
  @Matches(/((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$/, {
    message: 'Password must contain uppercase, lowercase, number/special char',
  })
  password: string;

  @IsString()
  @MinLength(2)
  @MaxLength(50)
  firstName: string;

  @IsString()
  @MinLength(2)
  @MaxLength(50)
  lastName: string;
}
```### Login DTO (`src/auth/dto/login.dto.ts`)
```typescript
import { IsEmail, IsString } from 'class-validator';

export class LoginDto {
  @IsEmail()
  email: string;

  @IsString()
  password: string;
}
```

## 📚 User DTOs

### Update Profile DTO (`src/users/dto/update-profile.dto.ts`)
```typescript
import { IsOptional, IsString, MinLength, MaxLength, IsPhoneNumber } from 'class-validator';

export class UpdateProfileDto {
  @IsOptional()
  @IsString()
  @MinLength(2)
  @MaxLength(50)
  firstName?: string;

  @IsOptional()
  @IsString()
  @MinLength(2)
  @MaxLength(50)
  lastName?: string;

  @IsOptional()
  @IsPhoneNumber()
  phoneNumber?: string;
}
```

## 📋 Quality Standards

✅ **[QS-01](../../architecture/quality-standards/01-code-quality-standards.md)** - Input validation  
✅ **[QS-02](../../architecture/quality-standards/02-security-standards.md)** - Security validation

## ✅ Next Step

Continue to **[14-monitoring-logging.md](./14-monitoring-logging.md)**