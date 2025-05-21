# 08: ORM and Migration Strategy

For the Payment Service, which will be developed using Node.js and TypeScript, an Object-Relational Mapper (ORM) will facilitate database interactions, and a robust migration strategy will manage database schema evolution.

## ORM Recommendation: TypeORM

**TypeORM** is recommended as the ORM for the Payment Service.

### Reasons for Recommendation:

1.  **TypeScript Support**: TypeORM is written in TypeScript and offers excellent support for TypeScript projects, enabling strong typing, decorators for entity definitions, and compile-time checks.
2.  **Multiple Database Support**: While PostgreSQL is selected, TypeORM supports various databases, offering flexibility if needed in other contexts (though sticking to one is generally advisable for a service).
3.  **Active Record and Data Mapper Patterns**: Supports both patterns, allowing developers to choose the one that best fits their coding style or project requirements.
4.  **Entity Definition**: Clean and intuitive entity definition using classes and decorators (e.g., `@Entity()`, `@Column()`, `@PrimaryGeneratedColumn()`, `@ManyToOne()`, `@OneToMany()`).
5.  **Connection Management**: Provides robust connection pooling and management capabilities.
6.  **Query Builder and Raw Queries**: Offers a powerful query builder for complex queries and also allows execution of raw SQL queries when needed for performance tuning or highly specific operations.
7.  **Migrations**: Has a built-in migration system that can automatically generate migration scripts based on entity changes or allow manual creation of migration scripts.
8.  **Community and Documentation**: Active community and comprehensive documentation.
9.  **Transaction Management**: Provides easy-to-use APIs for managing database transactions, which is critical for the Payment Service.
    ```typescript
    // Example of a TypeORM transaction
    await getManager().transaction(async transactionalEntityManager => {
        // operations within the transaction
        await transactionalEntityManager.save(payment);
        await transactionalEntityManager.save(transaction);
    });
    ```

## Migration Strategy

Database schema migrations are critical for evolving the application without data loss and ensuring consistency across environments.

1.  **TypeORM Migrations**: Utilize TypeORM's built-in migration capabilities.
    *   Migrations are TypeScript files that contain `up` and `down` methods.
    *   The `up` method applies the schema changes (e.g., creating a table, adding a column).
    *   The `down` method reverts the schema changes (e.g., dropping a table, removing a column).

2.  **Generating Migrations**:
    *   TypeORM can automatically generate migration scripts by comparing the current database schema with the defined entities.
        ```bash
        typeorm migration:generate -n MyMigrationName
        ```
    *   Review auto-generated migrations carefully before applying them. For complex changes or data transformations, manual adjustments or entirely manually written migrations might be necessary.

3.  **Running Migrations**:
    *   Migrations should be run as part of the deployment process, before the new application code that relies on the schema changes is deployed.
        ```bash
        typeorm migration:run
        ```
    *   Ensure that the database user used for running migrations has appropriate DDL (Data Definition Language) privileges.

4.  **Version Control**: Migration files must be committed to the version control system (Git) alongside the application code. This keeps the schema changes synchronized with the codebase.

5.  **Idempotency**: Strive to write idempotent `up` methods where possible, although TypeORM's migration runner typically ensures a migration is only run once.

6.  **Backward Compatibility and Data Migrations**: 
    *   For schema changes that are not backward compatible or require data transformation (e.g., renaming a column that has data, splitting a column), plan carefully.
    *   This might involve multi-step deployments (as discussed in `08-maintenance-and-upgrades.md` under Database Schema Migration Management for the User Service, e.g., expand/contract pattern).
    *   Data migrations (transforming existing data) might be part of a migration script or handled by separate scripts/jobs, depending on complexity and duration.

7.  **Testing Migrations**: Migrations should be thoroughly tested in development and staging environments before being applied to production. Test both `up` and `down` methods if rollback is a planned strategy for certain changes.

8.  **Production Best Practices**:
    *   Always back up the database before running migrations in production.
    *   Monitor the migration process closely.
    *   Have a rollback plan, which might involve restoring from backup for critical issues or running `down` migrations for simpler changes (use `down` migrations with caution in production, especially if they involve data loss).

By using TypeORM and its migration features, the Payment Service can manage its database schema effectively, ensuring that changes are applied consistently and reliably as the application evolves.
