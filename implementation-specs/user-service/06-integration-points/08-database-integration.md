# 08 - Database Integration

This document describes how the User Service integrates with its primary database, which is the authoritative source for all user, profile, role, and permission data.

## 1. Database Technology

*   **Chosen Database**: PostgreSQL (as recommended in `02-data-model-setup/07-database-selection.md`).
*   **Rationale**: Relational database with strong ACID properties, support for complex queries and relationships, robust security features, and good performance. Managed cloud versions (e.g., AWS RDS for PostgreSQL, Google Cloud SQL for PostgreSQL) are preferred for operational ease.
*   **Alternatives**: Other relational databases like MySQL could be used. NoSQL databases (e.g., MongoDB, DynamoDB) might be considered if the data model were significantly different (e.g., highly denormalized, document-centric user profiles with no complex relations), but for the defined User Service entities and their relationships, a relational DB is a better fit.

## 2. ORM (Object-Relational Mapper)

*   **Chosen ORM**: TypeORM (as recommended in `02-data-model-setup/08-orm-migrations.md`).
*   **Rationale**: TypeORM is a mature ORM for TypeScript and JavaScript, integrates well with NestJS, supports multiple database systems (including PostgreSQL), and provides features like entity definition via decorators, repository pattern, query builder, and migrations.
*   **Integration in NestJS**:
    *   The `@nestjs/typeorm` module is used to integrate TypeORM.
    *   Database connection options (host, port, username, password, database name) are configured via `ConfigModule` (typically from environment variables).
    *   Entities (e.g., `User`, `UserProfile`, `Address`, `Role`, `Permission`, `RolePermissionLink`) are defined as classes with TypeORM decorators (`@Entity()`, `@Column()`, `@PrimaryGeneratedColumn()`, `@ManyToOne()`, `@ManyToMany()`, etc.).
    *   Repositories for each entity are injected into services (`AuthService`, `UserService`, `UserProfileService`, `RoleService`, `PermissionService`) to perform CRUD operations.

    ```typescript
    // Example: app.module.ts (or a dedicated DatabaseModule)
    import { Module } from '@nestjs/common';
    import { TypeOrmModule } from '@nestjs/typeorm';
    import { ConfigModule, ConfigService } from '@nestjs/config';
    import { User } from './user/entities/user.entity';
    // ... import other entities

    @Module({
      imports: [
        TypeOrmModule.forRootAsync({
          imports: [ConfigModule],
          useFactory: (configService: ConfigService) => ({
            type: 'postgres',
            host: configService.get<string>('DB_HOST'),
            port: configService.get<number>('DB_PORT'),
            username: configService.get<string>('DB_USERNAME'),
            password: configService.get<string>('DB_PASSWORD'),
            database: configService.get<string>('DB_NAME'),
            entities: [User, /* other entities */],
            synchronize: configService.get<boolean>('DB_SYNCHRONIZE', false), // false for production, true for dev
            autoLoadEntities: true, // If entities are in different modules
            // ssl: configService.get('DB_SSL') ? { rejectUnauthorized: false } : false, // For cloud DBs
          }),
          inject: [ConfigService],
        }),
        // ... other modules
      ],
    })
    export class AppModule {}
    ```

## 3. Schema Management & Migrations

*   **TypeORM Migrations**: Database schema changes (e.g., adding tables, altering columns, creating indexes) are managed using TypeORM's migration system.
    *   Migrations are written in TypeScript.
    *   `typeorm migration:generate -n MyMigrationName` creates a new migration file with detected schema changes (based on entity definitions).
    *   `typeorm migration:run` applies pending migrations to the database.
*   **Production Deployments**: `synchronize: false` MUST be set in TypeORM configuration for production. Schema changes are applied by running migration scripts as part of the deployment process, not automatically by the application.
*   **Development**: `synchronize: true` can be used in local development for convenience, but it's better to get used to the migration workflow early.

## 4. Data Access Patterns

*   **Repository Pattern**: Services use TypeORM repositories to interact with the database. This abstracts the direct database interaction logic.
    *   Example: `this.userRepository.save(user)`, `this.userRepository.findOneBy({ email })`.
*   **Query Builder**: For more complex queries not easily expressed by simple repository methods, TypeORM's query builder is used.
*   **Transactions**: For operations that involve multiple database writes that must succeed or fail together (atomicity), TypeORM transactions are used (`@Transaction()` decorator or `EntityManager` manual transaction control).
    *   Example: Creating a `User` and their initial `UserProfile` in a single transaction.

## 5. Security Considerations

*   **Connection Security**: Use SSL/TLS to encrypt connections between the User Service and the PostgreSQL database, especially if the database is hosted remotely.
*   **Credentials Management**: Database credentials (username, password) must be securely managed (e.g., via Kubernetes Secrets, HashiCorp Vault) and injected as environment variables, not hardcoded.
*   **Principle of Least Privilege**: The database user account used by the User Service should only have the necessary permissions (SELECT, INSERT, UPDATE, DELETE) on the specific tables/schemas it owns. It should not have superuser privileges.
*   **SQL Injection Prevention**: Using an ORM like TypeORM significantly reduces the risk of SQL injection vulnerabilities, as it typically uses parameterized queries or properly escapes input. Avoid raw SQL queries with concatenated user input.
*   **Data Encryption at Rest**: Sensitive data stored in the database (beyond password hashes which are already one-way encrypted) might require column-level encryption or full-disk encryption at the database/infrastructure level, depending on compliance requirements (e.g., for PII in `UserProfile`). PostgreSQL extensions like `pgcrypto` can facilitate this.

## 6. Performance and Scalability

*   **Indexing**: Proper database indexing is crucial for query performance. Indexes should be created on frequently queried columns (e.g., `users.email`, `users.id`, foreign key columns).
*   **Connection Pooling**: TypeORM manages a database connection pool. Configure pool size appropriately based on expected load and database capacity.
*   **Read Replicas**: For read-heavy workloads, consider using PostgreSQL read replicas. The User Service could be configured to direct read queries to replicas and write queries to the primary instance (TypeORM supports this).
*   **Query Optimization**: Regularly analyze and optimize slow queries.

This direct database integration is fundamental to the User Service's operation, serving as the persistent store for all its critical data.
