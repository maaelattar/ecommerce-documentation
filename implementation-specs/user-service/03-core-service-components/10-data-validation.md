# 10 - Data Validation (Using NestJS Pipes)

In a NestJS application like the User Service, data validation is typically handled declaratively using built-in and custom Pipes, particularly the `ValidationPipe`. A dedicated `DataValidationService` is often unnecessary because NestJS provides robust mechanisms for this out-of-the-box, leveraging libraries like `class-validator` and `class-transformer`.

This document outlines how data validation is generally approached in the User Service, focusing on the use of DTOs (Data Transfer Objects) and NestJS Pipes.

## 1. Responsibilities (Achieved by NestJS Pipes & DTOs)

*   **Input Validation**: Ensure that incoming data (e.g., in request bodies, query parameters) conforms to expected types, formats, and constraints before it reaches service logic or controllers.
*   **Type Transformation**: Convert incoming plain JavaScript objects into typed DTO instances.
*   **Error Reporting**: Provide clear and structured error messages when validation fails, typically returned as part of the HTTP response (e.g., a 400 Bad Request with details).
*   **Sanitization (Optional)**: While primary validation is the focus, pipes can also be used for basic sanitization if needed, though extensive sanitization is often handled separately or by specific libraries if dealing with rich text or HTML.

## 2. Core Concepts & Tools

*   **Data Transfer Objects (DTOs)**:
    *   Classes that define the shape of data moving into and out of the application.
    *   Decorated with `class-validator` decorators to specify validation rules for each property.
    *   Example `CreateUserDto`:
        ```typescript
        import { IsEmail, IsString, MinLength, MaxLength, IsNotEmpty, IsOptional, IsEnum } from 'class-validator';
        import { UserStatus } from '../entities/user.entity'; // Assuming UserStatus enum

        export class CreateUserDto {
          @IsNotEmpty({ message: 'Email should not be empty.' })
          @IsEmail({}, { message: 'Please provide a valid email address.' })
          email: string;

          @IsNotEmpty({ message: 'Password is required.' })
          @IsString()
          @MinLength(10, { message: 'Password must be at least 10 characters long.' })
          @MaxLength(128, { message: 'Password cannot be longer than 128 characters.' })
          // Further complexity rules might be checked by PasswordPolicyService
          password: string;

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
          @IsEnum(UserStatus)
          status?: UserStatus; // e.g., 'pending_verification' on creation
        }
        ```
*   **`ValidationPipe` (`@nestjs/common`)**:
    *   A built-in pipe that uses `class-validator` and `class-transformer` to validate and transform incoming request payloads against DTOs.
    *   Typically applied globally in `main.ts` or on a per-controller/per-handler basis.
    *   Configuration options:
        *   `whitelist: true`: Automatically strips any properties from the input object that are not defined in the DTO.
        *   `forbidNonWhitelisted: true`: Throws an error if non-whitelisted properties are present.
        *   `transform: true`: Transforms the plain JavaScript object into an instance of the DTO class.
        *   `disableErrorMessages: false`: Ensures validation error messages are returned.
        *   `exceptionFactory`: Allows customization of the exception thrown when validation fails.
*   **`class-validator`**: A library providing a wide range of decorators for defining validation rules on class properties (e.g., `@IsEmail()`, `@IsString()`, `@MinLength()`, `@IsEnum()`, `@IsOptional()`, etc.).
*   **`class-transformer`**: A library used by `ValidationPipe` to transform plain objects to class instances and vice-versa. It can also handle type conversions (e.g., string to number if `@Type(() => Number)` is used).
*   **Custom Validation Decorators/Pipes**: For complex or reusable validation logic not covered by `class-validator` defaults, custom validation decorators or even custom pipes can be created.

## 3. Implementation Strategy

1.  **Define DTOs**: For every type of input data (e.g., request bodies for creating users, updating profiles, login credentials), define a DTO class with `class-validator` decorators.
    *   `src/user/dto/create-user.dto.ts`
    *   `src/user/dto/update-user-profile.dto.ts`
    *   `src/user/dto/login.dto.ts`
    *   `src/user/dto/create-address.dto.ts`
    *   etc.

2.  **Apply `ValidationPipe`**: Usually, `ValidationPipe` is applied globally for consistency.
    *   In `main.ts`:
        ```typescript
        import { NestFactory } from '@nestjs/core';
        import { AppModule } from './app.module';
        import { ValidationPipe } from '@nestjs/common';

        async function bootstrap() {
          const app = await NestFactory.create(AppModule);
          app.useGlobalPipes(
            new ValidationPipe({
              whitelist: true,
              // forbidNonWhitelisted: true, // Optional: stricter validation
              transform: true, // Automatically transform payloads to DTO instances
              transformOptions: {
                enableImplicitConversion: true, // Allows automatic conversion of primitive types
              },
            }),
          );
          await app.listen(3000);
        }
        bootstrap();
        ```

3.  **Use DTOs in Controllers/Handlers**: Type-hint controller method parameters with the DTOs. NestJS will automatically apply the `ValidationPipe`.
    *   Example in `UserController`:
        ```typescript
        import { Controller, Post, Body, Get, Param, Patch } from '@nestjs/common';
        import { AuthService } from './auth.service';
        import { CreateUserDto } from './dto/create-user.dto';
        import { LoginDto } from './dto/login.dto';
        // ... other imports

        @Controller('users')
        export class UserController {
          constructor(private readonly authService: AuthService) {}

          @Post('register')
          async register(@Body() createUserDto: CreateUserDto) {
            // If validation fails, ValidationPipe throws an error before this handler is reached.
            // createUserDto is a validated and transformed instance of CreateUserDto.
            return this.authService.register(createUserDto);
          }

          @Post('login')
          async login(@Body() loginDto: LoginDto) {
            return this.authService.login(loginDto);
          }

          // Example for path parameters or query parameters
          @Get(':id')
          async findUserById(@Param('id') id: string) { // Use ParseUUIDPipe for ID validation if it's a UUID
              // ...
          }
        }
        ```

## 4. Benefits of this Approach

*   **Declarative**: Validation rules are defined alongside the data structure (DTOs), making them easy to understand and maintain.
*   **Reusable**: DTOs can be reused across different parts of the application.
*   **Type Safety**: Ensures that service logic receives data in the expected shape and type.
*   **Early Failure**: Validation occurs before the core business logic is executed, preventing invalid data from propagating further.
*   **Standardized Error Responses**: `ValidationPipe` provides consistent error responses for client-side handling.
*   **Clean Controllers/Services**: Keeps validation logic separate from the main application logic, leading to cleaner and more focused components.

## 5. Custom Validations

For more complex scenarios:

*   **Custom Validation Decorators**: Create custom decorators using `registerDecorator` from `class-validator`.
    ```typescript
    // Example: src/common/validators/is-not-common-password.decorator.ts
    import { registerDecorator, ValidationOptions, ValidatorConstraint, ValidatorConstraintInterface, ValidationArguments } from 'class-validator';

    @ValidatorConstraint({ async: false })
    export class IsNotCommonPasswordConstraint implements ValidatorConstraintInterface {
      validate(password: any, args: ValidationArguments) {
        const commonPasswords = ['password', '123456', 'qwerty']; // Example list
        return !commonPasswords.includes(password?.toLowerCase());
      }

      defaultMessage(args: ValidationArguments) {
        return 'Password is too common.';
      }
    }

    export function IsNotCommonPassword(validationOptions?: ValidationOptions) {
      return function (object: Object, propertyName: string) {
        registerDecorator({
          target: object.constructor,
          propertyName: propertyName,
          options: validationOptions,
          constraints: [],
          validator: IsNotCommonPasswordConstraint,
        });
      };
    }
    ```
    Usage in DTO: `@IsNotCommonPassword({ message: 'This password is not allowed.' })`

*   **Custom Pipes**: For highly specialized transformation or validation logic that doesn't fit well into decorators, create a custom pipe by implementing the `PipeTransform` interface.

## 6. Security Considerations

*   **`whitelist: true`**: Essential for security to prevent mass assignment vulnerabilities by stripping unexpected properties.
*   **Input Source**: Be aware of the source of data being validated. Data from untrusted sources (like public API requests) requires rigorous validation.
*   **Error Message Verbosity**: While helpful for developers, detailed validation error messages in production might leak information about internal structures. Consider customizing error messages or logging details server-side while providing generic messages to the client.

By leveraging NestJS's built-in `ValidationPipe` along with `class-validator` and `class-transformer`, the User Service can achieve robust and maintainable data validation without needing a separate, custom-built validation service.
