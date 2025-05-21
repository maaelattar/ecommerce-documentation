# 02 - UserService (or UserAccountService)

The `UserService` (sometimes named `UserAccountService` to be more specific) is responsible for the direct management of user account data. It handles the Create, Read, Update, and Delete (CRUD) operations for the core `User` entity, distinct from authentication or profile-specific details which are handled by `AuthService` and `UserProfileService` respectively.

## 1. Responsibilities

*   **User Creation (Internal)**:
    *   Provides an internal method, typically called by `AuthService` during registration, to persist a new `User` entity to the database.
    *   Ensures essential fields are present and valid before saving.
*   **User Retrieval**:
    *   Fetching a user by their unique ID.
    *   Fetching a user by email (often used by `AuthService` during login or registration checks).
    *   Fetching a list of users (e.g., for administrative purposes, with pagination and filtering).
*   **User Update**:
    *   Updating core user account information. This is typically limited to fields directly on the `User` entity that are not managed by other specialized services.
    *   Examples:
        *   Updating `username` (if distinct from email and changeable).
        *   Updating `email` (may require a verification process).
        *   Updating `status` (e.g., `active`, `suspended`, `pending_verification`, `banned`).
        *   Updating `lastLoginAt` timestamp.
    *   Password updates are specifically handled via `AuthService` or a dedicated method that ensures hashing.
*   **User Deletion/Anonymization**:
    *   Handling requests to delete a user account.
    *   This can involve a soft delete (marking the user as `deleted` or `inactive`) or a hard delete (permanently removing the record), depending on data retention policies and legal requirements (e.g., GDPR).
    *   May also involve anonymizing user data instead of outright deletion to maintain referential integrity in other services (e.g., order history).
*   **Account Status Management**:
    *   Explicit methods to change a user's account status (e.g., activate, suspend, ban, verify email).
    *   These actions might be triggered by administrative actions, automated processes (e.g., after email verification), or by other services.
*   **Internal Data Integrity**:
    *   Ensuring that operations do not violate database constraints or business rules related to the user account itself.

## 2. Key Methods (Conceptual NestJS Example)

```typescript
import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm'; // Assuming TypeORM
import { Repository } from 'typeorm';
import { User } from '../entities/user.entity';
import { CreateUserInternalDto } from '../dto/create-user-internal.dto'; // DTO for internal creation
import { UpdateUserDto } from '../dto/update-user.dto';
import { UserEventPublisher } from './user-event-publisher.service'; // For publishing events

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
    private readonly userEventPublisher: UserEventPublisher,
  ) {}

  // Called by AuthService during registration
  async createUser(createUserDto: CreateUserInternalDto): Promise<User> {
    // Ensure email is unique (database constraint should also exist)
    const existingUser = await this.findByEmail(createUserDto.email);
    if (existingUser) {
      throw new BadRequestException('Email already exists.');
    }

    const user = this.userRepository.create(createUserDto);
    const savedUser = await this.userRepository.save(user);

    await this.userEventPublisher.publishUserCreated(savedUser);
    return savedUser;
  }

  async findById(id: string): Promise<User | null> {
    const user = await this.userRepository.findOneBy({ id });
    if (!user) {
      // Optionally throw NotFoundException or return null based on use case
      // For internal services, returning null might be preferred to allow calling service to handle.
    }
    return user;
  }

  async findByEmail(email: string): Promise<User | null> {
    return this.userRepository.findOneBy({ email });
  }

  async findAll(options: { page?: number; limit?: number; filter?: any }): Promise<[User[], number]> {
    // Implement pagination and filtering for admin use cases
    const { page = 1, limit = 10, filter = {} } = options;
    return this.userRepository.findAndCount({
      where: filter,
      take: limit,
      skip: (page - 1) * limit,
    });
  }

  async updateUser(id: string, updateUserDto: UpdateUserDto): Promise<User> {
    const user = await this.findById(id);
    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found.`);
    }

    // Prevent changing email directly if it requires verification, handle that separately
    if (updateUserDto.email && updateUserDto.email !== user.email) {
      // Logic for email change: e.g., set as unverified, trigger verification email
      // This might be a more complex flow handled by a dedicated method or AuthService
      console.warn('Email change requires a separate verification process.');
      // For simplicity here, we might allow it or disallow it based on policy
      // throw new BadRequestException('Email change requires verification.');
    }

    // Do not update password here, use AuthService.updatePassword
    if (updateUserDto.password) {
        delete updateUserDto.password; // Or throw an error
        console.warn('Password updates should go through AuthService or a dedicated method.');
    }

    Object.assign(user, updateUserDto); // Apply updates
    const updatedUser = await this.userRepository.save(user);

    await this.userEventPublisher.publishUserUpdated(updatedUser);
    return updatedUser;
  }

  async updatePassword(userId: string, hashedPassword: string): Promise<void> {
    const user = await this.findById(userId);
    if (!user) {
      throw new NotFoundException(`User with ID ${userId} not found.`);
    }
    user.password = hashedPassword;
    user.passwordLastChangedAt = new Date();
    await this.userRepository.save(user);
    // Event for password change might be published by AuthService which orchestrates this
  }

  async updateLastLogin(userId: string): Promise<void> {
    await this.userRepository.update(userId, { lastLoginAt: new Date() });
  }

  async changeUserStatus(userId: string, status: 'active' | 'suspended' | 'banned' | 'pending_verification'): Promise<User> {
    const user = await this.findById(userId);
    if (!user) {
      throw new NotFoundException(`User with ID ${userId} not found.`);
    }
    user.status = status;
    const updatedUser = await this.userRepository.save(user);
    await this.userEventPublisher.publishUserStatusChanged(updatedUser);
    return updatedUser;
  }

  async deleteUser(id: string, softDelete: boolean = true): Promise<void> {
    const user = await this.findById(id);
    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found.`);
    }

    if (softDelete) {
      user.status = 'deleted';
      user.deletedAt = new Date();
      await this.userRepository.save(user);
      await this.userEventPublisher.publishUserSoftDeleted(user);
    } else {
      // Hard delete - ensure cascading or related data handling is considered
      await this.userRepository.remove(user);
      await this.userEventPublisher.publishUserHardDeleted({ userId: id, email: user.email });
    }
  }
}
```

## 3. Interactions

*   **`AuthService`**: Relies on `UserService` to fetch user details during login (`findByEmail`) and to create user records during registration (`createUser`). `AuthService` also calls `updatePassword` or similar methods on `UserService` after verifying the user and hashing the new password.
*   **`UserProfileService`**: May retrieve user IDs or basic user context from `UserService` but primarily manages its own entities (`UserProfile`, `Address`).
*   **`UserEventPublisher`**: `UserService` calls this component to publish events such as `UserCreated`, `UserUpdated`, `UserStatusChanged`, `UserDeleted`.
*   **Database**: Directly interacts with the `User` table (or collection) in the database via an ORM like TypeORM or a database driver.
*   **Administrative Interfaces/Tools**: Admin UIs or CLI tools would interact with `UserService` to manage users (list, view details, change status, delete).

## 4. Data Management & Integrity

*   **Uniqueness Constraints**: Email (and potentially username, if used) should have uniqueness constraints at the database level, and checks within the service logic.
*   **Data Validation**: Use DTOs with validation decorators (e.g., from `class-validator`) for all input data.
*   **Transactional Integrity**: For operations that involve multiple database changes (though less common for simple CRUD in `UserService` itself, more so if it coordinated other entities), transactions should be used to ensure atomicity.
*   **Sensitive Data**: While the password hash is stored, avoid logging or unnecessarily exposing sensitive fields like `password` or `mfaSecret` (if stored directly on User entity, which is often not the case).

## 5. Security Considerations

*   **Authorization for Management**: Ensure that only authorized personnel (e.g., administrators) can access methods like `findAll`, `deleteUser`, or `changeUserStatus` for arbitrary users. This is typically handled by guards at the controller layer or higher-level services.
*   **Preventing Mass Data Exposure**: When implementing `findAll` or similar list-based methods, always include pagination and consider carefully what fields are returned by default.
*   **Email Change Process**: If `UserService` handles email updates directly, it must be a secure process, ideally involving verification of the new email address to prevent account takeovers. Often, `AuthService` would orchestrate this.
*   **Account Deletion/Anonymization**: Comply with data privacy regulations (e.g., GDPR Right to Erasure). Ensure that deletion/anonymization processes are thorough and correctly implemented.

## 6. Future Enhancements

*   **User Impersonation**: For administrators to log in as a user for troubleshooting (requires strict controls and auditing).
*   **Account Linking**: For users who might have multiple accounts that need to be linked (e.g., personal and business under one umbrella).
*   **More Granular User Statuses**: For more complex lifecycle management.

This `UserService` is the backbone for user data, providing foundational CRUD operations and status management that other services build upon.
