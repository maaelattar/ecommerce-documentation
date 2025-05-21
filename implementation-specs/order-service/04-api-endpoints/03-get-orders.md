# List Orders API Endpoint

## 1. Overview

This document specifies the API endpoint for retrieving a list of orders with filtering, sorting, and pagination capabilities. This endpoint allows customers to view their order history and enables administrators to access and manage all orders in the system.

## 2. Endpoint Specification

| Method | Endpoint       | Description                            |
| ------ | -------------- | -------------------------------------- |
| GET    | /api/v1/orders | Retrieve a list of orders with filters |

### 2.1. Request Format

#### Query Parameters

| Parameter  | Type    | Required | Description                                                   | Default   |
| ---------- | ------- | -------- | ------------------------------------------------------------- | --------- |
| page       | Integer | No       | Page number for pagination                                    | 1         |
| pageSize   | Integer | No       | Number of orders per page (max 100)                           | 20        |
| status     | String  | No       | Filter by order status (comma-separated for multiple)         | All       |
| fromDate   | String  | No       | Filter by orders created after this date (ISO format)         | None      |
| toDate     | String  | No       | Filter by orders created before this date (ISO format)        | None      |
| minAmount  | Number  | No       | Filter by minimum order amount                                | None      |
| maxAmount  | Number  | No       | Filter by maximum order amount                                | None      |
| sortBy     | String  | No       | Field to sort by (createdAt, updatedAt, totalAmount)          | createdAt |
| sortOrder  | String  | No       | Sort direction (asc, desc)                                    | desc      |
| productId  | UUID    | No       | Filter by orders containing specific product                  | None      |
| searchTerm | String  | No       | Search term to match against order IDs or shipping recipients | None      |

#### Headers

| Header           | Type   | Required | Description                       |
| ---------------- | ------ | -------- | --------------------------------- |
| Authorization    | String | Yes      | Bearer token for authentication   |
| Accept           | String | No       | application/json (default)        |
| X-Correlation-ID | String | No       | Unique ID for distributed tracing |

### 2.2. Response Format

#### Success Response (200 OK)

##### Headers

| Header           | Type   | Description                                  |
| ---------------- | ------ | -------------------------------------------- |
| Content-Type     | String | application/json                             |
| X-Correlation-ID | String | Same correlation ID from request if provided |
| X-Total-Count    | Number | Total number of orders matching the filters  |
| X-Total-Pages    | Number | Total number of pages                        |

##### Response Body

```json
{
  "success": true,
  "data": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "status": "SHIPPED",
      "statusId": 8,
      "createdAt": "2023-11-21T15:27:30.123Z",
      "updatedAt": "2023-11-23T14:35:12.487Z",
      "totalAmount": 149.99,
      "currency": "USD",
      "itemCount": 3,
      "shippingDetails": {
        "recipientName": "John Doe",
        "shippingMethod": "STANDARD",
        "trackingNumber": "1ZW470X56892747254"
      }
    },
    {
      "id": "a6be674b-5c66-47aa-8834-c3c2b4e211ab",
      "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "status": "DELIVERED",
      "statusId": 9,
      "createdAt": "2023-11-15T10:12:45.789Z",
      "updatedAt": "2023-11-18T09:25:11.456Z",
      "totalAmount": 89.95,
      "currency": "USD",
      "itemCount": 2,
      "shippingDetails": {
        "recipientName": "John Doe",
        "shippingMethod": "EXPRESS",
        "trackingNumber": "1ZW470X56892747255"
      }
    }
  ],
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
    "requestId": "req-987654321",
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalItems": 42,
      "totalPages": 3
    }
  }
}
```

#### Error Responses

##### 400 Bad Request

```json
{
  "success": false,
  "error": {
    "code": "INVALID_QUERY_PARAMETER",
    "message": "Invalid query parameter: sortBy must be one of [createdAt, updatedAt, totalAmount]"
  },
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
    "requestId": "req-987654321"
  }
}
```

##### 401 Unauthorized

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
    "requestId": "req-987654321"
  }
}
```

##### 403 Forbidden

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to access orders for this user"
  },
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
    "requestId": "req-987654321"
  }
}
```

##### 500 Internal Server Error

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred"
  },
  "meta": {
    "timestamp": "2023-11-24T08:12:45.123Z",
    "requestId": "req-987654321"
  }
}
```

## 3. Request Processing

### 3.1. Authorization Rules

1. **Customer Access**:

   - Customers can access only their own orders
   - User ID from JWT token is used to filter orders by userId

2. **Administrator Access**:

   - Users with ADMIN or CUSTOMER_SERVICE roles can access all orders
   - Can apply any filtering without user restrictions

3. **Partner Access**:
   - Fulfillment partners can access orders assigned to them
   - Payment partners can access orders they processed
   - Results are filtered to show only relevant information

### 3.2. Filter Processing

1. **Status Filtering**:

   - Single status: `status=PROCESSING`
   - Multiple statuses: `status=PROCESSING,SHIPPED,DELIVERED`
   - Status mappings follow the Order Status Entity specification

2. **Date Range Filtering**:

   - Format: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
   - Example: `fromDate=2023-11-01T00:00:00Z&toDate=2023-11-30T23:59:59Z`
   - Server timezone: UTC

3. **Amount Range Filtering**:

   - Currency normalization: All amounts are stored and filtered in the base currency
   - Format: Decimal values with 2 digits precision
   - Example: `minAmount=50.00&maxAmount=150.00`

4. **Product Filtering**:

   - Filter orders containing specific products
   - Example: `productId=9e3a3ca9-4c41-4c3c-8e82-3b323d9a3e23`

5. **Search Term Processing**:
   - Searches across order ID (partial match)
   - Searches across recipient names (partial match)
   - Case insensitive

### 3.3. Pagination and Sorting

1. **Pagination**:

   - Default page size: 20 items
   - Maximum page size: 100 items
   - First page index: 1

2. **Sorting**:
   - Default sort: createdAt (newest first)
   - Allowed sort fields: createdAt, updatedAt, totalAmount
   - Sort directions: asc (ascending), desc (descending)

### 3.4. Response Assembly

1. **Data Transformation**:

   - Orders are transformed into a condensed format for list views
   - Detailed order information is available via the single order endpoint
   - Sensitive data is filtered based on user role

2. **Metadata**:
   - Total count and pagination information is included in metadata
   - Performance metrics may be included for administrative users

## 4. Service Interactions

The list orders endpoint interacts with the following services:

1. **Authentication Service**:

   - Validate JWT tokens
   - Extract user roles and permissions

2. **Product Service** (optional):

   - Enrich response with product information when filtering by product

3. **User Service** (for administrators):
   - Fetch user information to enrich order summaries

## 5. Performance Considerations

1. **Query Optimization**:

   - Use database indexes on frequently filtered fields:
     - userId
     - status
     - createdAt
     - totalAmount
   - Implement composite indexes for common filter combinations

2. **Caching Strategy**:

   - Cache query results with a short TTL (1-5 minutes)
   - Cache key based on query parameters and user ID
   - Invalidate cache on order updates
   - Consider different cache strategies for customers vs. administrators

3. **Pagination Implementation**:

   - Use cursor-based pagination for large result sets
   - Implement keyset pagination for better performance with large offsets
   - Use COUNT queries judiciously, especially for administrative views

4. **Response Size Management**:
   - Limit response fields for list views
   - Use lean representations for order objects
   - Support field selection via query parameters for advanced use cases

## 6. Implementation Example

```typescript
@Controller("orders")
@UseGuards(JwtAuthGuard)
export class OrderController {
  constructor(
    private readonly orderService: OrderService,
    private readonly logger: Logger
  ) {}

  @Get()
  async getOrders(
    @Query() queryParams: GetOrdersDto,
    @Req() request,
    @User() user: UserDto
  ): Promise<OrderListResponseDto> {
    const correlationId = request.headers["x-correlation-id"] || uuidv4();
    this.logger.log(`Retrieving orders with filters`, {
      correlationId,
      queryParams,
    });

    try {
      // Set default values
      const filters = {
        page: queryParams.page || 1,
        pageSize: Math.min(queryParams.pageSize || 20, 100),
        sortBy: ["createdAt", "updatedAt", "totalAmount"].includes(
          queryParams.sortBy
        )
          ? queryParams.sortBy
          : "createdAt",
        sortOrder: queryParams.sortOrder === "asc" ? "ASC" : "DESC",
        status: queryParams.status ? queryParams.status.split(",") : undefined,
        fromDate: queryParams.fromDate
          ? new Date(queryParams.fromDate)
          : undefined,
        toDate: queryParams.toDate ? new Date(queryParams.toDate) : undefined,
        minAmount: queryParams.minAmount
          ? parseFloat(queryParams.minAmount)
          : undefined,
        maxAmount: queryParams.maxAmount
          ? parseFloat(queryParams.maxAmount)
          : undefined,
        productId: queryParams.productId,
        searchTerm: queryParams.searchTerm,
      };

      // Apply user-based restrictions
      if (!["ADMIN", "CUSTOMER_SERVICE"].includes(user.role)) {
        // Regular customers can only see their own orders
        filters.userId = user.id;
      } else if (queryParams.userId) {
        // Admins can filter by user if requested
        filters.userId = queryParams.userId;
      }

      // Get paginated orders
      const [orders, totalItems] = await this.orderService.findOrders(filters);
      const totalPages = Math.ceil(totalItems / filters.pageSize);

      // Transform to response format
      const orderList = orders.map((order) => ({
        id: order.id,
        userId: order.userId,
        status: order.status.name,
        statusId: order.status.id,
        createdAt: order.createdAt,
        updatedAt: order.updatedAt,
        totalAmount: order.totalAmount,
        currency: order.currency,
        itemCount: order.items.length,
        shippingDetails: {
          recipientName: order.shippingDetails.recipientName,
          shippingMethod: order.shippingDetails.shippingMethod,
          trackingNumber: order.shippingDetails.trackingNumber || null,
        },
      }));

      // Set pagination headers
      request.res.set({
        "X-Total-Count": totalItems.toString(),
        "X-Total-Pages": totalPages.toString(),
      });

      return {
        success: true,
        data: orderList,
        meta: {
          timestamp: new Date().toISOString(),
          requestId: correlationId,
          pagination: {
            page: filters.page,
            pageSize: filters.pageSize,
            totalItems: totalItems,
            totalPages: totalPages,
          },
        },
      };
    } catch (error) {
      this.logger.error(`Error retrieving orders: ${error.message}`, {
        correlationId,
        stack: error.stack,
      });

      if (error instanceof BadRequestException) {
        throw error;
      }

      if (error instanceof ForbiddenException) {
        throw error;
      }

      throw new InternalServerErrorException({
        code: "INTERNAL_SERVER_ERROR",
        message: "An unexpected error occurred",
      });
    }
  }
}
```

## 7. References

- [Order Service API Index](./00-api-index.md)
- [Order Entity Specification](../02-data-model-setup/01-order-entity.md)
- [Order Status Entity Specification](../02-data-model-setup/05-order-status-entity.md)
- [ADR-002-rest-api-standards-openapi](../../../architecture/adr/ADR-002-rest-api-standards-openapi.md)
