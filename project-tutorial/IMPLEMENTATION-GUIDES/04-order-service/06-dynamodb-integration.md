# Tutorial 6: Strategic DynamoDB Integration
## When PostgreSQL Isn't Enough: Hybrid Database Patterns

## 🎯 Objective
Learn **strategic hybrid database architecture** by adding DynamoDB for high-throughput order status tracking while keeping PostgreSQL for transactional data.

## 🤔 Why This Tutorial Is Critical

In the previous tutorials, you built order management with PostgreSQL. But you've likely noticed some **emerging pain points**:

- ✅ **High-frequency status updates** - Orders change status constantly (pending → processing → shipped → delivered)
- ✅ **Status history tracking** - Need complete audit trail of every status change
- ✅ **Read-heavy analytics** - Dashboards querying status data frequently
- ✅ **Performance concerns** - Status updates causing lock contention in PostgreSQL

**This is where strategic polyglot persistence shines!**

## 📊 Pain Point Analysis

### Problem 1: Status Update Frequency
```sql
-- PostgreSQL struggles with this pattern:
UPDATE orders SET status = 'PROCESSING', updated_at = NOW() WHERE id = ?;
INSERT INTO order_status_log (order_id, old_status, new_status, timestamp) VALUES (?, ?, ?, NOW());

-- This happens hundreds of times per minute!
-- Each update locks the row and creates write contention
```

### Problem 2: Status History Queries
```sql
-- Complex queries for status analytics:
SELECT status, COUNT(*) as count 
FROM order_status_log 
WHERE timestamp BETWEEN ? AND ? 
GROUP BY status;

-- These queries scan large tables and impact transaction performance
```

### Problem 3: Mixed Workloads
- **Transactional operations** (create order, update items) need ACID compliance
- **Status tracking** needs high throughput and eventual consistency is fine
- **Analytics queries** should not impact order processing performance

## 🔄 Solution: Strategic Database Separation

### PostgreSQL for: 
- **Order core data** (financial, items, addresses)
- **Transactional operations** (ACID requirements)
- **Complex relationships** (joins between orders, items, users)

### DynamoDB for:
- **Order status tracking** (high-frequency updates)
- **Status history** (time-series data)
- **Real-time analytics** (status counters, metrics)

## 🛠️ Implementation Strategy

### Step 1: Add DynamoDB Dependencies
```bash
npm install @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb
npm install --save-dev @types/aws-sdk
```

### Step 2: Create DynamoDB Configuration
**src/config/dynamodb.config.ts:**
```typescript
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';

export const createDynamoDBClient = () => {
  const client = new DynamoDBClient({
    region: process.env.AWS_REGION || 'us-east-1',
    endpoint: process.env.DYNAMODB_ENDPOINT || undefined, // LocalStack
    credentials: process.env.NODE_ENV === 'development' ? {
      accessKeyId: 'test',
      secretAccessKey: 'test'
    } : undefined
  });

  return DynamoDBDocumentClient.from(client);
};
```

### Step 3: Create Order Status Log Entity
**src/modules/orders/entities/order-status-log.entity.ts:**
```typescript
export interface OrderStatusLogEntry {
  orderId: string;          // Partition Key
  timestamp: string;        // Sort Key (ISO string)
  statusId: number;
  statusName: string;
  previousStatusId?: number;
  previousStatusName?: string;
  userId: string;
  metadata?: Record<string, any>;
  ttl?: number;            // Auto-expire old logs
}

export interface OrderStatusMetrics {
  statusId: number;         // Partition Key  
  timestamp: string;        // Sort Key (day/hour granularity)
  count: number;
  totalValue: number;
  updatedAt: string;
}
```### Step 4: Create DynamoDB Service
**src/modules/orders/services/order-status-dynamo.service.ts:**
```typescript
import { Injectable } from '@nestjs/common';
import { DynamoDBDocumentClient, PutCommand, QueryCommand, BatchWriteCommand } from '@aws-sdk/lib-dynamodb';
import { createDynamoDBClient } from '../../../config/dynamodb.config';

@Injectable()
export class OrderStatusDynamoService {
  private readonly client: DynamoDBDocumentClient;
  private readonly statusLogTable = 'OrderStatusLogs';
  private readonly metricsTable = 'OrderStatusMetrics';

  constructor() {
    this.client = createDynamoDBClient();
  }

  async logStatusChange(entry: OrderStatusLogEntry): Promise<void> {
    const command = new PutCommand({
      TableName: this.statusLogTable,
      Item: {
        ...entry,
        timestamp: new Date().toISOString(),
        ttl: Math.floor(Date.now() / 1000) + (365 * 24 * 60 * 60) // 1 year TTL
      }
    });

    await this.client.send(command);
  }

  async getOrderStatusHistory(orderId: string): Promise<OrderStatusLogEntry[]> {
    const command = new QueryCommand({
      TableName: this.statusLogTable,
      KeyConditionExpression: 'orderId = :orderId',
      ExpressionAttributeValues: {
        ':orderId': orderId
      },
      ScanIndexForward: false // Most recent first
    });

    const result = await this.client.send(command);
    return result.Items as OrderStatusLogEntry[];
  }

  async updateStatusMetrics(statusId: number, increment: number = 1, orderValue: number = 0): Promise<void> {
    const now = new Date();
    const hourKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}`;

    const command = new PutCommand({
      TableName: this.metricsTable,
      Item: {
        statusId,
        timestamp: hourKey,
        count: increment,
        totalValue: orderValue,
        updatedAt: now.toISOString()
      },
      ConditionExpression: 'attribute_not_exists(statusId)',
      // If exists, we'll handle it with an update expression
    });

    try {
      await this.client.send(command);
    } catch (error) {
      if (error.name === 'ConditionalCheckFailedException') {
        // Update existing metrics
        await this.incrementExistingMetrics(statusId, hourKey, increment, orderValue);
      } else {
        throw error;
      }
    }
  }

  private async incrementExistingMetrics(statusId: number, timestamp: string, increment: number, orderValue: number): Promise<void> {
    // Implementation for atomic counter updates
    // Using UpdateCommand with ADD expression
  }
}
```### Step 5: Update Order Service with Hybrid Pattern
**src/modules/orders/services/order.service.ts:**
```typescript
@Injectable()
export class OrderService {
  constructor(
    @InjectRepository(Order)
    private orderRepository: Repository<Order>,
    private statusDynamoService: OrderStatusDynamoService,
    private eventPublisher: EventPublisher
  ) {}

  async updateOrderStatus(orderId: string, newStatusId: number, userId: string): Promise<Order> {
    // Start with PostgreSQL transaction for ACID compliance
    return this.orderRepository.manager.transaction(async manager => {
      const order = await manager.findOne(Order, { 
        where: { id: orderId },
        relations: ['status']
      });

      if (!order) {
        throw new NotFoundException('Order not found');
      }

      const previousStatus = order.status;
      const newStatus = await manager.findOne(OrderStatus, { where: { id: newStatusId } });
      
      if (!newStatus) {
        throw new BadRequestException('Invalid status');
      }

      // Update PostgreSQL (transactional)
      order.status = newStatus;
      order.updatedAt = new Date();
      const updatedOrder = await manager.save(order);

      // After successful PostgreSQL update, log to DynamoDB (async)
      // This follows the "write to primary DB first" pattern
      this.logStatusChangeToDynamoDB(order.id, previousStatus, newStatus, userId).catch(error => {
        // Log error but don't fail the transaction
        console.error('Failed to log status change to DynamoDB:', error);
      });

      // Publish event for other services
      await this.eventPublisher.publish(new OrderStatusUpdatedEvent({
        orderId: order.id,
        previousStatus: previousStatus.name,
        newStatus: newStatus.name,
        userId,
        timestamp: new Date()
      }));

      return updatedOrder;
    });
  }

  private async logStatusChangeToDynamoDB(
    orderId: string, 
    previousStatus: OrderStatus, 
    newStatus: OrderStatus, 
    userId: string
  ): Promise<void> {
    await this.statusDynamoService.logStatusChange({
      orderId,
      statusId: newStatus.id,
      statusName: newStatus.name,
      previousStatusId: previousStatus.id,
      previousStatusName: previousStatus.name,
      userId,
      metadata: {
        source: 'order_service',
        version: '1.0'
      }
    });

    // Update real-time metrics
    await this.statusDynamoService.updateStatusMetrics(newStatus.id, 1);
  }

  async getOrderStatusHistory(orderId: string): Promise<OrderStatusLogEntry[]> {
    // Read from DynamoDB for status history
    return this.statusDynamoService.getOrderStatusHistory(orderId);
  }
}
```## 🎯 Key Learning Outcomes

### **1. When to Use Hybrid Databases**
```typescript
// ✅ ACID Required → PostgreSQL
async createOrder(data: CreateOrderDto) {
  // Financial transactions need ACID compliance
  return this.postgresRepo.save(data);
}

// ✅ High Throughput → DynamoDB  
async updateOrderStatus(orderId: string, status: OrderStatus) {
  // Status changes are high-frequency, eventual consistency OK
  return this.dynamoService.logStatusChange({...});
}
```

### **2. Consistency Patterns**
- **Strong Consistency**: PostgreSQL for financial data
- **Eventual Consistency**: DynamoDB for status tracking
- **Write Order**: Primary DB first, then secondary (failure resilience)

### **3. Performance Benefits**
- **PostgreSQL**: No longer blocked by high-frequency status updates
- **DynamoDB**: Handles thousands of status updates per second
- **Analytics**: Fast time-series queries without impacting transactions

## 🚨 Production Considerations

### **Data Consistency Strategy**
```typescript
// Pattern: Write to primary first, secondary async
try {
  const result = await this.primaryDB.save(data);
  // Don't await secondary writes - use async background processing
  this.secondaryDB.save(data).catch(error => this.handleSecondaryFailure(error));
  return result;
} catch (error) {
  // Primary failure = operation fails
  throw error;
}
```

### **Failure Handling**
- **Primary DB failure**: Operation fails (correct behavior)
- **Secondary DB failure**: Log and retry, don't fail operation
- **Sync issues**: Background reconciliation processes

### **Monitoring Strategy**
- **Lag monitoring**: Track delay between primary and secondary writes
- **Error rates**: Monitor DynamoDB write failures
- **Data drift**: Periodic consistency checks

## 🔥 Real-World Examples

This pattern is used by:
- **Amazon**: Order data in RDS, status tracking in DynamoDB
- **Uber**: Ride data in PostgreSQL, location updates in high-throughput stores
- **Netflix**: User data in Cassandra, viewing data in specialized stores

## ✅ Next Step
Continue with **[07-product-service-integration.md](./07-product-service-integration.md)** to integrate with the Product Service for inventory validation.