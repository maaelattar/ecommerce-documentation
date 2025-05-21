# ORM/ODM and Schema Migration Strategy

## 1. Overview

Following the recommendation of using a Relational Database Management System (RDBMS) like PostgreSQL for the User Service (as detailed in `07-database-selection.md`), this document outlines the strategy for interacting with the database using an Object-Relational Mapper (ORM) and managing database schema changes through migrations.

## 2. Object-Relational Mapper (ORM) Selection

An ORM simplifies database interactions by allowing developers to work with objects and classes that map to database tables and records, abstracting much of the direct SQL query writing.

*   **Primary Choice for NestJS & TypeScript**: **TypeORM**
    *   **Website**: [https://typeorm.io/](https://typeorm.io/)
    *   **Rationale**:
        *   **Maturity and Popularity**: Widely used in the NestJS and TypeScript ecosystem.
        *   **Strong TypeScript Support**: Leverages decorators and TypeScript features for defining entities and relationships.
        *   **Database Support**: Supports PostgreSQL, MySQL, MariaDB, SQLite, MS SQL Server, Oracle, and others.
        *   **Features**: Data-mapping, automatic table creation (for development), connection pooling, query builder, transaction management, and a robust migrations system.
        *   **NestJS Integration**: `@nestjs/typeorm` package provides seamless integration with NestJS modules, dependency injection for repositories, etc.
*   **Alternatives**: 
    *   **Sequelize**: Another popular ORM for Node.js, also with TypeScript support. Mature and feature-rich.
    *   **Prisma**: A newer ORM that offers a different approach with its schema-first design and auto-generated query builder. Gaining popularity.
    *   **Knex.js (Query Builder)**: Not a full ORM, but a flexible SQL query builder. Can be used if finer control over SQL is desired, but requires more manual mapping to objects.

**Recommendation**: **TypeORM** is the recommended ORM for the User Service due to its excellent integration with NestJS, strong TypeScript features, and comprehensive support for PostgreSQL.

## 3. Schema Migration Strategy

Schema migrations are essential for evolving the database schema in a controlled, versioned, and repeatable manner as the application develops and new requirements emerge. They allow changes (e.g., adding a table, altering a column, adding an index) to be applied systematically across different environments (development, staging, production).

### Using TypeORM Migrations

TypeORM has a built-in migration system that works well with its entity definitions.

*   **How it Works**: 
    1.  **Entity Definitions**: Developers define entities using TypeORM decorators (e.g., `@Entity()`, `@Column()`, `@PrimaryGeneratedColumn()`, `@OneToMany()`).
    2.  **Generating Migrations**: TypeORM can automatically generate migration files (SQL or TypeScript code) by comparing the current state of your entities with the state of the database schema (or the last applied migration).
        *   Command (conceptual): `typeorm migration:generate -n MyNewMigrationName`
    3.  **Migration Files**: These files contain `up()` and `down()` methods:
        *   `up(queryRunner: QueryRunner): Promise<void>`: Contains the logic to apply the schema changes (e.g., `CREATE TABLE`, `ALTER TABLE ADD COLUMN`).
        *   `down(queryRunner: QueryRunner): Promise<void>`: Contains the logic to revert the schema changes (e.g., `DROP TABLE`, `ALTER TABLE DROP COLUMN`). This is crucial for rollbacks.
    4.  **Running Migrations**: Migrations are applied to the database using a CLI command.
        *   Command (conceptual): `typeorm migration:run`
    5.  **Migration Tracking**: TypeORM keeps track of which migrations have been applied to the database in a special table (e.g., `migrations` or `typeorm_metadata`).

### Migration Workflow:

1.  **Development**: 
    *   Modify TypeORM entities in your NestJS application.
    *   Use `typeorm migration:generate` to create a new migration file. **Always review the generated migration file carefully** to ensure it accurately reflects the intended changes and doesn't cause unintended data loss.
    *   Manually adjust the generated migration if necessary (e.g., for complex data transformations, adding specific index types not auto-detected, or ensuring default values are set correctly).
    *   Run the migration locally: `typeorm migration:run`.
    *   Test the application with the new schema.
    *   Commit the entity changes *and* the new migration file to version control.
2.  **CI/CD Pipeline**: 
    *   **Build Step**: The application code (including entities) is built.
    *   **Deployment Step (before application starts or as a dedicated step)**:
        *   The CI/CD pipeline connects to the target database (staging, production) with appropriate credentials.
        *   It runs `typeorm migration:run` to apply any pending migrations.
        *   **Important**: The database user configured for running migrations needs permissions to alter the schema (e.g., `CREATE TABLE`, `ALTER TABLE`). This might be a different, more privileged user than the application's runtime database user (which should ideally have only DML permissions like `SELECT`, `INSERT`, `UPDATE`, `DELETE` on its tables).
3.  **Production Deployment**: 
    *   Migrations are applied automatically by the CI/CD pipeline before the new application version is started or traffic is routed to it.
    *   **Rollback**: If a deployment fails or a critical bug is found post-deployment that is related to a schema change:
        *   Roll back the application code.
        *   Run `typeorm migration:revert` to apply the `down()` method of the last applied migration(s). This requires well-written and tested `down()` methods.
        *   **Caution**: Reverting migrations that involve destructive changes (e.g., dropping columns/tables) can lead to data loss if not handled carefully. Backups are essential.

### Best Practices for Migrations:

*   **Version Control**: Always commit migration files to your Git repository along with code changes.
*   **Review Generated Migrations**: Never blindly trust auto-generated migrations. Review them for correctness and potential data loss.
*   **Write Reversible Migrations**: Ensure the `down()` method correctly reverses the `up()` method. Test reversions in a development/staging environment.
*   **Non-Destructive Changes Where Possible**: For changes like renaming a column, consider a multi-step process if zero-downtime is critical and the application is live: 
    1.  Add new column.
    2.  Modify application to write to both old and new columns, read from new (falling back to old).
    3.  Run a data migration script to copy data from old to new column.
    4.  Modify application to read/write only to new column.
    5.  Create a migration to drop the old column (after a safe period).
*   **Backup Before Migrating (Production)**: Always ensure a valid database backup exists before applying migrations to a production database.
*   **Idempotency**: Migration scripts should ideally be written so that running them multiple times (if the tracking mechanism failed) wouldn't cause errors, though TypeORM's tracking table usually prevents this.
*   **Small, Incremental Changes**: Prefer smaller, more frequent migrations over large, complex ones. This reduces risk and makes rollbacks easier.
*   **Seed Data**: Initial seed data (e.g., default roles, permissions, admin user) can also be managed via TypeORM migrations or dedicated seeding scripts run after migrations.

## 4. Tooling Configuration (Conceptual)

*   **`ormconfig.json` or `DataSource` Options (TypeORM)**: Configure database connection details, entity paths, and migration file paths for TypeORM.
    ```typescript
    // Example TypeORM DataSource options (typeorm.config.ts)
    import { DataSource, DataSourceOptions } from 'typeorm';
    import { ConfigService } from '@nestjs/config'; // To load from environment

    // Load environment variables (e.g., using dotenv for local dev)
    // require('dotenv').config(); 

    export const typeOrmConfig = (configService: ConfigService): DataSourceOptions => ({
      type: 'postgres',
      host: configService.get<string>('DB_HOST', 'localhost'),
      port: configService.get<number>('DB_PORT', 5432),
      username: configService.get<string>('DB_USERNAME'),
      password: configService.get<string>('DB_PASSWORD'),
      database: configService.get<string>('DB_DATABASE_NAME'),
      entities: [__dirname + '/../**/*.entity{.ts,.js}'], // Path to entities
      synchronize: false, // IMPORTANT: Never use true in production! Use migrations instead.
      migrationsTableName: 'migrations', // Optional: custom name for migrations table
      migrations: [__dirname + '/../migrations/*{.ts,.js}'], // Path to migration files
      // logging: true, // Enable for debugging
    });

    // For CLI usage, TypeORM needs a DataSource instance exported
    // export default new DataSource(typeOrmConfig(new ConfigService())); // Simplified for example
    ```
*   **`package.json` Scripts**: Add npm scripts for common TypeORM CLI migration commands.
    ```json
    "scripts": {
      "typeorm": "ts-node -r tsconfig-paths/register ./node_modules/typeorm/cli.js --dataSource path/to/your/datasource-config.ts",
      "migration:generate": "npm run typeorm -- migration:generate src/migrations/$npm_config_name",
      "migration:run": "npm run typeorm -- migration:run",
      "migration:revert": "npm run typeorm -- migration:revert"
    }
    ```

By using TypeORM and its migration system, the User Service can manage its database schema effectively throughout the development lifecycle, ensuring consistency and control across all environments.
