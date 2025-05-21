# Order Status Log Entity Specification

## 1. Overview

The OrderStatusLog entity records the complete history of status changes for each order. Unlike other entities in the Order Service data model, the OrderStatusLog is stored in Amazon DynamoDB to efficiently handle high-volume append operations with fast retrieval by order ID. This entity implements an audit trail for order status changes, which is essential for operational visibility and customer support.

## 2. Entity Properties

| Property           | Type    | Required | Description                                         |
| ------------------ | ------- | -------- | --------------------------------------------------- |
| orderId            | UUID    | Yes      | Reference to the order (partition key)              |
| timestamp          | String  | Yes      | ISO 8601 timestamp of the status change (sort key)  |
| statusId           | Integer | Yes      | ID of the new status                                |
| statusName         | String  | Yes      | Name of the new status                              |
| previousStatusId   | Integer | No       | ID of the previous status (null for first status)   |
| previousStatusName | String  | No       | Name of the previous status (null for first status) |
| changedBy          | String  | Yes      | User ID or system identifier that made the change   |
| reason             | String  | No       | Optional reason for the status change               |
| metadata           | JSON    | No       | Additional contextual information about the change  |

## 3. Relationships

This entity is stored in DynamoDB and doesn't have foreign key relationships in the traditional sense, but it logically relates to:

| Related Entity | Relationship Type | Description                                      |
| -------------- | ----------------- | ------------------------------------------------ |
| Order          | Reference         | The order this status log entry belongs to       |
| OrderStatus    | Reference         | The status referenced by statusId and statusName |

## 4. DynamoDB Table Schema

```json
{
  "TableName": "OrderStatusLogs",
  "KeySchema": [
    {
      "AttributeName": "order_id",
      "KeyType": "HASH"
    },
    {
      "AttributeName": "timestamp",
      "KeyType": "RANGE"
    }
  ],
  "AttributeDefinitions": [
    {
      "AttributeName": "order_id",
      "AttributeType": "S"
    },
    {
      "AttributeName": "timestamp",
      "AttributeType": "S"
    },
    {
      "AttributeName": "status_id",
      "AttributeType": "N"
    }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "status-timestamp-index",
      "KeySchema": [
        {
          "AttributeName": "status_id",
          "KeyType": "HASH"
        },
        {
          "AttributeName": "timestamp",
          "KeyType": "RANGE"
        }
      ],
      "Projection": {
        "ProjectionType": "ALL"
      }
    }
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

## 5. AWS SDK Implementation

```typescript
import { DynamoDB } from "aws-sdk";
import { v4 as uuidv4 } from "uuid";
import { DocumentClient } from "aws-sdk/clients/dynamodb";

export class OrderStatusLogRepository {
  private readonly tableName = "OrderStatusLogs";
  private readonly docClient: DocumentClient;

  constructor(private readonly dynamodbClient: DynamoDB.DocumentClient) {
    this.docClient = dynamodbClient;
  }

  async createStatusLogEntry(params: {
    orderId: string;
    statusId: number;
    statusName: string;
    previousStatusId?: number;
    previousStatusName?: string;
    changedBy: string;
    reason?: string;
    metadata?: Record<string, any>;
  }): Promise<void> {
    const timestamp = new Date().toISOString();

    const item = {
      order_id: params.orderId,
      timestamp,
      status_id: params.statusId,
      status_name: params.statusName,
      previous_status_id: params.previousStatusId,
      previous_status_name: params.previousStatusName,
      changed_by: params.changedBy,
      reason: params.reason,
      metadata: params.metadata ? JSON.stringify(params.metadata) : null,
    };

    await this.docClient
      .put({
        TableName: this.tableName,
        Item: item,
      })
      .promise();
  }

  async getStatusLogsByOrderId(orderId: string): Promise<any[]> {
    const result = await this.docClient
      .query({
        TableName: this.tableName,
        KeyConditionExpression: "order_id = :orderId",
        ExpressionAttributeValues: {
          ":orderId": orderId,
        },
        ScanIndexForward: false, // descending order (newest first)
      })
      .promise();

    return result.Items || [];
  }

  async getOrdersByStatus(
    statusId: number,
    limit: number = 100
  ): Promise<any[]> {
    const result = await this.docClient
      .query({
        TableName: this.tableName,
        IndexName: "status-timestamp-index",
        KeyConditionExpression: "status_id = :statusId",
        ExpressionAttributeValues: {
          ":statusId": statusId,
        },
        Limit: limit,
        ScanIndexForward: false, // descending order (newest first)
      })
      .promise();

    return result.Items || [];
  }
}
```

## 6. Business Rules and Validations

1. **Timestamp Validation**:

   - Timestamps must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.sssZ)
   - Timestamps serve as the sort key and must be unique per order

2. **Status Reference Integrity**:

   - Status IDs and names must reference valid entries in the OrderStatus entity
   - Both ID and name are stored for data consistency and readability

3. **Changed By Validation**:

   - Must contain a valid user ID for user-initiated changes
   - For system-initiated changes, use a consistent identifier (e.g., "SYSTEM", "PAYMENT_PROCESSOR")

4. **First Log Entry**:

   - The first status log entry for an order will have null values for previousStatusId and previousStatusName
   - All subsequent entries must include previous status information

5. **Automatic Logging**:
   - Status changes must be automatically logged whenever an order's status changes
   - Log entries should never be modified or deleted (append-only)

## 7. Data Access Patterns

### 7.1. Read Operations

| Operation                                | Access Pattern                            | Expected Performance |
| ---------------------------------------- | ----------------------------------------- | -------------------- |
| Get status history for an order          | Query by order_id with sort by timestamp  | <20ms                |
| Get recent orders with a specific status | Query GSI by status_id, sort by timestamp | <50ms                |
| Get latest status change for an order    | Query by order_id, limit 1                | <10ms                |
| Count orders transitioning to a status   | Query GSI, count results                  | <100ms               |

### 7.2. Write Operations

| Operation                         | Access Pattern | Expected Performance |
| --------------------------------- | -------------- | -------------------- |
| Create status log entry           | Put item       | <20ms                |
| Batch log multiple status changes | BatchWriteItem | <50ms                |

## 8. Sample Data

```json
{
  "order_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "timestamp": "2023-11-21T15:27:30.123Z",
  "status_id": 4,
  "status_name": "PAYMENT_COMPLETED",
  "previous_status_id": 2,
  "previous_status_name": "PAYMENT_PROCESSING",
  "changed_by": "PAYMENT_SERVICE",
  "reason": "Payment successfully processed by payment gateway",
  "metadata": {
    "payment_id": "ch_3OBtP1CZ6qsJgndP0NZUQ1ZW",
    "payment_provider": "stripe",
    "transaction_id": "txn_1K2OuRCZ6qsJgndP0ko2cnni"
  }
}
```

## 9. Retention and Archiving

The OrderStatusLog table implements the following data lifecycle policies:

1. **Active Data**: All status logs for orders created in the last 90 days remain in the active DynamoDB table for fast access
2. **Archived Data**: Older logs are automatically archived to S3 using DynamoDB Time-to-Live (TTL) and DynamoDB Streams
3. **Data Retrieval**: Archived logs can be retrieved for historical analysis or compliance purposes

## 10. Data Consistency Considerations

1. **Eventually Consistent Reads**:

   - Standard queries use eventually consistent reads for better performance
   - When immediate consistency is required (e.g., immediately after a status change), strongly consistent reads should be used

2. **Write Consistency**:

   - Status log entries should be written within the same transaction as the status change when possible
   - In cases where this isn't possible, the application must ensure that the log entry is still created even if retries are needed

3. **Error Handling**:
   - Failed log writes should trigger alerts and retry mechanisms
   - The system should never skip logging a status change even under high load

## 11. References

- [Order Service Data Model](./00-data-model-index.md)
- [Order Entity](./01-order-entity.md)
- [Order Status Entity](./05-order-status-entity.md)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [Data Storage and Management Specification](../../infrastructure/06-data-storage-specification.md)
- [ADR-004-data-persistence-strategy](../../../architecture/adr/ADR-004-data-persistence-strategy.md)
