# RBAC System Implementation

## 🎯 Objective

Implement Role-Based Access Control per implementation specs.

## 📚 Data Models

Based on **[User Service Data Model](../../implementation-specs/user-service/02-data-model-setup/01-user-entities.md)**

### Role Entity (`src/entities/role.entity.ts`)
```typescript
import { Entity, PrimaryGeneratedColumn, Column, ManyToMany, CreateDateColumn, UpdateDateColumn } from 'typeorm';
import { User } from './user.entity';
import { Permission } from './permission.entity';

@Entity('roles')
export class Role {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  name: string;

  @Column({ nullable: true })
  description: string;

  @ManyToMany(() => User, user => user.roles)
  users: User[];

  @ManyToMany(() => Permission, permission => permission.roles)
  permissions: Permission[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
```### Permission Entity (`src/entities/permission.entity.ts`)
```typescript
import { Entity, PrimaryGeneratedColumn, Column, ManyToMany, CreateDateColumn, UpdateDateColumn } from 'typeorm';
import { Role } from './role.entity';

@Entity('permissions')
export class Permission {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  name: string;

  @Column()
  resource: string;

  @Column()
  action: string;

  @ManyToMany(() => Role, role => role.permissions)
  roles: Role[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
```

## 🔧 RBAC Guard

### Permission Guard (`src/guards/permission.guard.ts`)
```typescript
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';

@Injectable()
export class PermissionGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredPermissions = this.reflector.get<string[]>('permissions', context.getHandler());
    if (!requiredPermissions) return true;

    const request = context.switchToHttp().getRequest();
    const user = request.user;
    
    return user.permissions.some(permission => 
      requiredPermissions.includes(permission.name)
    );
  }
}
```

## ✅ Next Step

Continue to **[13-validation-dtos.md](./13-validation-dtos.md)**