# API Implementation

## 🎯 Objective

Create REST API controllers for authentication and user management.

## 🔧 Auth Controller (`src/auth/auth.controller.ts`)

```typescript
import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { AuthService } from './auth.service';

@Controller('auth')
export class AuthController {
  constructor(private authService: AuthService) {}

  @Post('register')
  async register(@Body() body: { email: string; password: string }) {
    const user = await this.authService.register(body.email, body.password);
    return { id: user.id, email: user.email, status: user.status };
  }

  @Post('login')
  @HttpCode(HttpStatus.OK)
  async login(@Body() body: { email: string; password: string }) {
    return this.authService.login(body.email, body.password);
  }
}
```

## 🔧 Users Controller (`src/users/users.controller.ts`)

```typescript
import { Controller, Get, UseGuards, Request } from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { UsersService } from './users.service';

@Controller('users')
@UseGuards(JwtAuthGuard)
export class UsersController {
  constructor(private usersService: UsersService) {}

  @Get('profile')
  async getProfile(@Request() req) {
    return this.usersService.findById(req.user.sub);
  }
}
```

## 📋 API Standards

Following **[API Design Standards](../../architecture/quality-standards/api-design-standards.md)**:
- ✅ RESTful endpoints, HTTP status codes, JWT auth

## ✅ Next Step

Continue to **[06-event-publishing.md](./06-event-publishing.md)**