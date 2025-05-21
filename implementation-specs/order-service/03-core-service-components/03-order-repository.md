# Order Repository

## 1. Overview

The `OrderRepository` is responsible for data access and persistence operations for orders in the database. It extends TypeORM's repository pattern to provide type-safe data access methods and custom queries for the Order entity. This repository acts as the persistence layer between the domain model and the database, abstracting the underlying storage details from the service layer.

## 2. Responsibilities

- Providing CRUD operations for Order entities
- Implementing custom queries for order retrieval and filtering
- Supporting transaction management for order operations
- Maintaining data consistency and referential integrity
- Optimizing query performance for order-related operations
- Supporting bulk operations for efficient data access
- Enforcing data access patterns and best practices

## 3. Class Definition

```typescript
@EntityRepository(Order)
export class OrderRepository extends Repository<Order> {
  private readonly logger = new Logger(OrderRepository.name);

  // Repository methods defined below
}
```

## 4. Core Methods

### 4.1. Find Order with Relations

```typescript
/**
 * Finds an order by ID with specified relations
 */
async findOrderWithRelations(
  orderId: string,
  relations: string[] = ['items', 'status']
): Promise<Order> {
  this.logger.debug(`Finding order ${orderId} with relations: ${relations.join(', ')}`);

  const order = await this.findOne({
    where: { id: orderId },
    relations
  });

  if (!order) {
    throw new EntityNotFoundError(Order, orderId);
  }

  return order;
}
```

### 4.2. Find Orders by User

```typescript
/**
 * Finds all orders for a specific user with pagination
 */
async findOrdersByUser(
  userId: string,
  options: {
    page?: number;
    limit?: number;
    status?: string | string[];
    fromDate?: Date;
    toDate?: Date;
    sortBy?: string;
    sortOrder?: 'ASC' | 'DESC';
  } = {}
): Promise<[Order[], number]> {
  const {
    page = 1,
    limit = 10,
    status,
    fromDate,
    toDate,
    sortBy = 'createdAt',
    sortOrder = 'DESC'
  } = options;

  const skip = (page - 1) * limit;

  const queryBuilder = this.createQueryBuilder('order')
    .leftJoinAndSelect('order.items', 'items')
    .leftJoinAndSelect('order.status', 'status')
    .where('order.userId = :userId', { userId });

  // Apply filters
  if (status) {
    if (Array.isArray(status)) {
      queryBuilder.andWhere('status.name IN (:...statusNames)', { statusNames: status });
    } else {
      queryBuilder.andWhere('status.name = :statusName', { statusName: status });
    }
  }

  if (fromDate) {
    queryBuilder.andWhere('order.createdAt >= :fromDate', { fromDate });
  }

  if (toDate) {
    queryBuilder.andWhere('order.createdAt <= :toDate', { toDate });
  }

  // Apply sorting
  queryBuilder.orderBy(`order.${sortBy}`, sortOrder);

  // Apply pagination
  queryBuilder.skip(skip).take(limit);

  // Execute query
  const [orders, total] = await queryBuilder.getManyAndCount();

  return [orders, total];
}
```

### 4.3. Find Orders by Status

```typescript
/**
 * Finds orders by status with pagination
 */
async findOrdersByStatus(
  status: string | string[],
  options: {
    page?: number;
    limit?: number;
    fromDate?: Date;
    toDate?: Date;
  } = {}
): Promise<[Order[], number]> {
  const {
    page = 1,
    limit = 10,
    fromDate,
    toDate
  } = options;

  const skip = (page - 1) * limit;

  const queryBuilder = this.createQueryBuilder('order')
    .leftJoinAndSelect('order.items', 'items')
    .leftJoinAndSelect('order.status', 'status');

  // Apply status filter
  if (Array.isArray(status)) {
    queryBuilder.where('status.name IN (:...statusNames)', { statusNames: status });
  } else {
    queryBuilder.where('status.name = :statusName', { statusName: status });
  }

  // Apply date filters
  if (fromDate) {
    queryBuilder.andWhere('order.createdAt >= :fromDate', { fromDate });
  }

  if (toDate) {
    queryBuilder.andWhere('order.createdAt <= :toDate', { toDate });
  }

  // Apply pagination
  queryBuilder.skip(skip).take(limit);

  // Default sorting by created date
  queryBuilder.orderBy('order.createdAt', 'DESC');

  // Execute query
  const [orders, total] = await queryBuilder.getManyAndCount();

  return [orders, total];
}
```

### 4.4. Advanced Order Search

```typescript
/**
 * Search orders with advanced filtering options
 */
async searchOrders(
  searchParams: {
    userId?: string;
    orderNumber?: string;
    productId?: string;
    status?: string | string[];
    fromAmount?: number;
    toAmount?: number;
    fromDate?: Date;
    toDate?: Date;
    paymentMethod?: string;
    shippingMethod?: string;
    page?: number;
    limit?: number;
    sortBy?: string;
    sortOrder?: 'ASC' | 'DESC';
  }
): Promise<[Order[], number]> {
  const {
    userId,
    orderNumber,
    productId,
    status,
    fromAmount,
    toAmount,
    fromDate,
    toDate,
    paymentMethod,
    shippingMethod,
    page = 1,
    limit = 10,
    sortBy = 'createdAt',
    sortOrder = 'DESC'
  } = searchParams;

  const skip = (page - 1) * limit;

  const queryBuilder = this.createQueryBuilder('order')
    .leftJoinAndSelect('order.items', 'items')
    .leftJoinAndSelect('order.status', 'status')
    .leftJoinAndSelect('order.shippingDetails', 'shippingDetails')
    .leftJoinAndSelect('order.billingDetails', 'billingDetails');

  // Apply filters
  if (userId) {
    queryBuilder.andWhere('order.userId = :userId', { userId });
  }

  if (orderNumber) {
    queryBuilder.andWhere('order.orderNumber LIKE :orderNumber', { orderNumber: `%${orderNumber}%` });
  }

  if (productId) {
    queryBuilder.andWhere('items.productId = :productId', { productId });
  }

  if (status) {
    if (Array.isArray(status)) {
      queryBuilder.andWhere('status.name IN (:...statusNames)', { statusNames: status });
    } else {
      queryBuilder.andWhere('status.name = :statusName', { statusName: status });
    }
  }

  if (fromAmount !== undefined) {
    queryBuilder.andWhere('order.totalAmount >= :fromAmount', { fromAmount });
  }

  if (toAmount !== undefined) {
    queryBuilder.andWhere('order.totalAmount <= :toAmount', { toAmount });
  }

  if (fromDate) {
    queryBuilder.andWhere('order.createdAt >= :fromDate', { fromDate });
  }

  if (toDate) {
    queryBuilder.andWhere('order.createdAt <= :toDate', { toDate });
  }

  if (paymentMethod) {
    queryBuilder.andWhere('billingDetails.paymentMethod = :paymentMethod', { paymentMethod });
  }

  if (shippingMethod) {
    queryBuilder.andWhere('shippingDetails.shippingMethod = :shippingMethod', { shippingMethod });
  }

  // Apply sorting
  if (sortBy === 'totalAmount' || sortBy === 'createdAt' || sortBy === 'updatedAt') {
    queryBuilder.orderBy(`order.${sortBy}`, sortOrder);
  } else if (sortBy === 'status') {
    queryBuilder.orderBy('status.name', sortOrder);
  }

  // Apply pagination
  queryBuilder.skip(skip).take(limit);

  // Execute query with count
  const [orders, total] = await queryBuilder.getManyAndCount();

  return [orders, total];
}
```

### 4.5. Bulk Operations

```typescript
/**
 * Find multiple orders by IDs
 */
async findOrdersByIds(
  orderIds: string[],
  relations: string[] = ['items', 'status']
): Promise<Order[]> {
  if (!orderIds.length) {
    return [];
  }

  return this.find({
    where: { id: In(orderIds) },
    relations
  });
}

/**
 * Update multiple orders' statuses in bulk
 */
async bulkUpdateStatus(
  orderIds: string[],
  statusId: number,
  updateTimestamp: Date = new Date()
): Promise<number> {
  const result = await this.createQueryBuilder()
    .update(Order)
    .set({
      statusId,
      updatedAt: updateTimestamp
    })
    .whereInIds(orderIds)
    .execute();

  return result.affected || 0;
}
```

### 4.6. Analytics and Reporting

```typescript
/**
 * Get order statistics by status
 */
async getOrderStatsByStatus(
  options: {
    fromDate?: Date;
    toDate?: Date;
  } = {}
): Promise<Array<{ status: string; count: number; totalAmount: number }>> {
  const { fromDate, toDate } = options;

  const queryBuilder = this.createQueryBuilder('order')
    .select('status.name', 'status')
    .addSelect('COUNT(order.id)', 'count')
    .addSelect('SUM(order.totalAmount)', 'totalAmount')
    .leftJoin('order.status', 'status')
    .groupBy('status.name');

  if (fromDate) {
    queryBuilder.andWhere('order.createdAt >= :fromDate', { fromDate });
  }

  if (toDate) {
    queryBuilder.andWhere('order.createdAt <= :toDate', { toDate });
  }

  return queryBuilder.getRawMany();
}

/**
 * Get daily order counts for a date range
 */
async getDailyOrderCounts(
  fromDate: Date,
  toDate: Date
): Promise<Array<{ date: string; count: number; totalAmount: number }>> {
  return this.createQueryBuilder('order')
    .select('DATE(order.createdAt)', 'date')
    .addSelect('COUNT(order.id)', 'count')
    .addSelect('SUM(order.totalAmount)', 'totalAmount')
    .where('order.createdAt BETWEEN :fromDate AND :toDate', { fromDate, toDate })
    .groupBy('date')
    .orderBy('date', 'ASC')
    .getRawMany();
}
```

## 5. Helper Methods

### 5.1. Full-text Search

```typescript
/**
 * Performs a full-text search across order fields
 */
async fullTextSearch(
  searchTerm: string,
  options: {
    page?: number;
    limit?: number;
  } = {}
): Promise<[Order[], number]> {
  const { page = 1, limit = 10 } = options;
  const skip = (page - 1) * limit;

  // Create a search across multiple fields
  const queryBuilder = this.createQueryBuilder('order')
    .leftJoinAndSelect('order.items', 'items')
    .leftJoinAndSelect('order.status', 'status')
    .leftJoinAndSelect('order.shippingDetails', 'shippingDetails')
    .where(
      new Brackets(qb => {
        qb.where('order.orderNumber LIKE :search', { search: `%${searchTerm}%` })
          .orWhere('items.productName LIKE :search', { search: `%${searchTerm}%` })
          .orWhere('shippingDetails.recipientName LIKE :search', { search: `%${searchTerm}%` });
      })
    )
    .orderBy('order.createdAt', 'DESC')
    .skip(skip)
    .take(limit);

  return queryBuilder.getManyAndCount();
}
```

### 5.2. Get Recently Created Orders

```typescript
/**
 * Gets recently created orders
 */
async getRecentOrders(
  limit: number = 10
): Promise<Order[]> {
  return this.find({
    order: { createdAt: 'DESC' },
    take: limit,
    relations: ['status', 'items']
  });
}
```

### 5.3. Check Order Existence

```typescript
/**
 * Checks if an order exists by ID
 */
async orderExists(
  orderId: string
): Promise<boolean> {
  const count = await this.count({ where: { id: orderId } });
  return count > 0;
}

/**
 * Checks if an order number already exists
 */
async orderNumberExists(
  orderNumber: string
): Promise<boolean> {
  const count = await this.count({ where: { orderNumber } });
  return count > 0;
}
```

## 6. Performance Optimizations

The `OrderRepository` implements several strategies to optimize query performance:

### 6.1. Indexing Strategy

The underlying Order table should have the following indexes to support efficient queries:

```typescript
@Entity()
@Index(["userId", "createdAt"]) // Support queries for user orders by date
@Index(["statusId", "createdAt"]) // Support queries by status and date
@Index(["orderNumber"], { unique: true }) // Support unique order number lookups
export class Order {
  // Entity fields...
}
```

### 6.2. Query Optimization

- **Selective Relations**: Only load relations that are needed for a specific query
- **Pagination**: All list queries include pagination to limit result sets
- **Projection**: Use column selection to limit data retrieval when appropriate
- **Query Hints**: Add query hints for complex queries based on database-specific optimization

```typescript
/**
 * Example of optimized query with projection
 */
async getOrderSummary(
  orderId: string
): Promise<OrderSummaryDto> {
  return this.createQueryBuilder('order')
    .select('order.id', 'id')
    .addSelect('order.orderNumber', 'orderNumber')
    .addSelect('order.totalAmount', 'totalAmount')
    .addSelect('status.name', 'status')
    .addSelect('order.createdAt', 'createdAt')
    .leftJoin('order.status', 'status')
    .where('order.id = :orderId', { orderId })
    .getRawOne();
}
```

### 6.3. Batch Processing

For operations on multiple orders, the repository provides methods that use SQL batch operations:

```typescript
/**
 * Insert multiple order items efficiently
 */
async bulkInsertOrderItems(
  orderItems: OrderItem[]
): Promise<void> {
  await this.manager.createQueryBuilder()
    .insert()
    .into(OrderItem)
    .values(orderItems)
    .execute();
}
```

## 7. Transaction Management

The `OrderRepository` supports transaction management for operations that require atomic execution:

```typescript
/**
 * Example of transaction use in a service method
 */
async createOrderWithTransaction(
  orderData: CreateOrderDto,
  entityManager?: EntityManager
): Promise<Order> {
  // Use provided entity manager or create a new transaction
  const manager = entityManager || this.manager;

  // Create and save the order within the transaction
  const order = new Order();
  Object.assign(order, orderData);

  return manager.save(order);
}
```

## 8. Error Handling

The repository implements proper error handling for database operations:

```typescript
/**
 * Safe find with error handling
 */
async findOrderSafe(
  orderId: string
): Promise<Order | null> {
  try {
    return await this.findOne({ where: { id: orderId } });
  } catch (error) {
    this.logger.error(`Error finding order ${orderId}: ${error.message}`, error.stack);
    return null;
  }
}
```

## 9. References

- [Order Entity Model](../../02-data-model-setup/01-order-entity.md)
- [Order Item Entity Model](../../02-data-model-setup/02-order-item-entity.md)
- [Order Status Entity Model](../../02-data-model-setup/04-order-status-entity.md)
- [TypeORM Repository Pattern](https://typeorm.io/#/repository-pattern)
- [Order Service](./02-order-service.md)
- [Database Selection](../01-database-selection.md)
