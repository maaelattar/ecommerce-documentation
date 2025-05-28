# Database Models

## 🎯 Objective

Create TypeORM entities based on data model specs.

## 🔧 User Entity

```bash
mkdir -p src/entities
```

### `src/entities/user.entity.ts`
```typescript
import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, DeleteDateColumn } from 'typeorm';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true, length: 255 })
  email: string;

  @Column({ default: false })
  emailVerified: boolean;

  @Column()
  passwordHash: string;

  @Column({ default: 'PENDING_VERIFICATION' })
  status: string;

  @Column({ nullable: true })
  lastLoginAt?: Date;

  @Column({ default: 0 })
  failedLoginAttempts: number;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @DeleteDateColumn()
  deletedAt?: Date;
}
```## 📋 Quality Standards

Following **[Data Integrity Standards](../../architecture/quality-standards/data-integrity-standards.md)**:
- ✅ UUID primary keys for global uniqueness
- ✅ Soft deletes with `deletedAt` for data retention
- ✅ Audit fields (`createdAt`, `updatedAt`) for tracking
- ✅ Unique constraints for business rules

## 📚 Full Specification

Review complete entity specs:
- **[User Entity](../../implementation-specs/user-service/02-data-model-setup/01-user-entity.md)**
- **[UserProfile Entity](../../implementation-specs/user-service/02-data-model-setup/02-user-profile-entity.md)**
- **[Role Entity](../../implementation-specs/user-service/02-data-model-setup/04-role-entity.md)**

## ✅ Next Step

Continue to **[03-authentication.md](./03-authentication.md)**