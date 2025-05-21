# Indexing Management API

**Base Path:** `/v1/admin/search/indexing`

## Overview

This set of API endpoints provides administrative functionalities for managing the search indexes. These are typically protected endpoints intended for internal use, system administrators, or automated maintenance processes. They allow for operations like triggering re-indexing, checking indexing status, and managing index configurations or aliases.

**Authentication & Authorization:** These endpoints MUST be protected with robust authentication (e.g., Admin OAuth2 scope, API Key with admin privileges) and authorization mechanisms to ensure only permitted users/systems can access them.

## Endpoints

### 1. Trigger Re-indexing

*   **Endpoint:** `POST /v1/admin/search/indexing/reindex`
*   **Description:** Initiates a re-indexing process for specified indexes or all configured indexes.

#### Request Body

```json
{
  "indexes": ["products", "categories"], // Optional. If empty or null, re-index all target indexes.
  "mode": "full" // Optional. "full" or "incremental". Defaults to "full". "incremental" might require additional parameters like a timestamp.
}
```

| Parameter | Type        | Required | Description                                                                                             |
| --------- | ----------- | -------- | ------------------------------------------------------------------------------------------------------- |
| `indexes` | string[]    | No       | An array of index names to re-index (e.g., `["products", "categories", "content"]`). If omitted, re-indexes all. |
| `mode`    | string      | No       | `full`: Rebuilds the index from scratch. `incremental`: Updates the index (not always applicable).    |

#### Response

*   **202 Accepted**

    ```json
    {
      "message": "Re-indexing process initiated for specified indexes.",
      "taskId": "reindex-task-xyz123", // An ID to track the background task status
      "indexes": ["products", "categories"],
      "mode": "full"
    }
    ```
*   **400 Bad Request** (e.g., invalid index name)
*   **401 Unauthorized / 403 Forbidden**
*   **500 Internal Server Error**

### 2. Get Indexing Status

*   **Endpoint:** `GET /v1/admin/search/indexing/status`
*   **Description:** Retrieves the current status of indexing processes or specific indexes.

#### Query Parameters

| Parameter | Type   | Required | Description                                                                      |
| --------- | ------ | -------- | -------------------------------------------------------------------------------- |
| `indexName`| string | No       | Get status for a specific index. If omitted, returns status for all managed indexes. |
| `taskId`  | string | No       | Get status for a specific background re-indexing task.                              |

#### Response

*   **200 OK**

    **Example (Specific Index):**
    ```json
    {
      "indexName": "products",
      "status": "completed", // e.g., idle, indexing, completed, failed
      "lastIndexedAt": "2023-11-10T10:00:00Z",
      "documentsCount": 150000,
      "health": "green", // From Elasticsearch cluster health for this index
      "activeAlias": "products_v2"
    }
    ```

    **Example (Specific Task):**
    ```json
    {
      "taskId": "reindex-task-xyz123",
      "status": "in-progress", // e.g., pending, in-progress, completed, failed
      "progress": 65.5, // Percentage complete
      "startedAt": "2023-11-15T14:00:00Z",
      "details": "Re-indexing 'products' index..."
    }
    ```
*   **404 Not Found** (e.g., index name or task ID not found)
*   **401 Unauthorized / 403 Forbidden**
*   **500 Internal Server Error**

### 3. Manage Index Aliases (Conceptual)

*   **Endpoint:** `POST /v1/admin/search/indexing/aliases`
*   **Description:** Allows switching an alias to point to a different version of an index, typically used for zero-downtime re-indexing and deployments.

#### Request Body

```json
{
  "actions": [
    {
      "remove": {
        "index": "products_v1",
        "alias": "products_live"
      }
    },
    {
      "add": {
        "index": "products_v2",
        "alias": "products_live"
      }
    }
  ]
}
```

#### Response

*   **200 OK**
    ```json
    {
      "message": "Aliases updated successfully."
    }
    ```
*   **400 Bad Request**
*   **401 Unauthorized / 403 Forbidden**
*   **500 Internal Server Error**

### 4. Create Index (Advanced/Manual)

*   **Endpoint:** `PUT /v1/admin/search/indexing/indices/{indexName}`
*   **Description:** Manually creates an index with a specific mapping and settings. Generally, index creation is automated, but this provides fine-grained control if needed.

#### Path Parameters

| Parameter   | Type   | Description        |
| ----------- | ------ | ------------------ |
| `indexName` | string | Name of the index to create. |

#### Request Body (Elasticsearch Index Settings & Mappings)

```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "analysis": { 
      // Custom analyzers, tokenizers, filters
    }
  },
  "mappings": {
    // Document type mappings
  }
}
```

#### Response

*   **201 Created**
*   **400 Bad Request** (e.g., index already exists, invalid mapping)
*   **401 Unauthorized / 403 Forbidden**
*   **500 Internal Server Error**

### 5. Delete Index (Advanced/Manual)

*   **Endpoint:** `DELETE /v1/admin/search/indexing/indices/{indexName}`
*   **Description:** Deletes an index. This is a destructive operation and should be used with extreme caution.

#### Path Parameters

| Parameter   | Type   | Description        |
| ----------- | ------ | ------------------ |
| `indexName` | string | Name of the index to delete. |

#### Response

*   **200 OK** or **204 No Content**
*   **404 Not Found**
*   **401 Unauthorized / 403 Forbidden**
*   **500 Internal Server Error**

## NestJS Controller Example (Conceptual for Re-indexing)

```typescript
import { Controller, Post, Body, Get, Query, Param, UseGuards, Put, Delete } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth, ApiBody, ApiParam } from '@nestjs/swagger';
import { IndexingManagementService } from '../services/indexing-management.service';
// import { AdminAuthGuard } from '../../auth/guards/admin-auth.guard'; // Example Admin Guard
import { ReindexRequestDto, IndexStatusQueryDto, AliasActionDto, CreateIndexDto } from './dto/indexing-admin.dto';

@ApiTags('Admin - Search Indexing')
@ApiBearerAuth() // Indicates that Bearer token is expected for these endpoints
// @UseGuards(AdminAuthGuard) // Apply admin guard to the entire controller
@Controller('v1/admin/search/indexing')
export class IndexingManagementController {
  constructor(private readonly indexingService: IndexingManagementService) {}

  @Post('reindex')
  @ApiOperation({ summary: 'Trigger re-indexing for specified search indexes' })
  @ApiBody({ type: ReindexRequestDto })
  @ApiResponse({ status: 202, description: 'Re-indexing process initiated.' })
  async triggerReindex(@Body() reindexRequest: ReindexRequestDto) {
    const result = await this.indexingService.startReindex(reindexRequest);
    return result;
  }

  @Get('status')
  @ApiOperation({ summary: 'Get the status of indexing processes or specific indexes' })
  @ApiResponse({ status: 200, description: 'Current indexing status.' })
  async getIndexingStatus(@Query() query: IndexStatusQueryDto) {
    if (query.taskId) {
      return this.indexingService.getTaskStatus(query.taskId);
    }
    return this.indexingService.getIndexStatus(query.indexName);
  }
  
  @Post('aliases')
  @ApiOperation({ summary: 'Manage index aliases (e.g., for zero-downtime updates)' })
  @ApiBody({ type: AliasActionDto, isArray: true }) // Assuming body is an array of actions or a wrapper DTO
  @ApiResponse({ status: 200, description: 'Aliases updated successfully.' })
  async updateAliases(@Body() aliasActions: /* Define DTO, e.g., AliasActionDto[] or a wrapper */ any) {
    // const result = await this.indexingService.updateAliases(aliasActions);
    // return result;
    return { message: "Alias management endpoint conceptual." };
  }

  @Put('indices/:indexName')
  @ApiOperation({ summary: 'Create a new search index with specified mappings and settings' })
  @ApiParam({ name: 'indexName', type: String, description: 'Name of the index to create' })
  @ApiBody({ type: CreateIndexDto })
  @ApiResponse({ status: 201, description: 'Index created successfully.' })
  @ApiResponse({ status: 400, description: 'Index already exists or invalid mapping.' })
  async createIndex(@Param('indexName') indexName: string, @Body() createIndexDto: CreateIndexDto) {
    // const result = await this.indexingService.createIndex(indexName, createIndexDto);
    // return result;
    return { message: `Index ${indexName} creation endpoint conceptual.` };
  }

  @Delete('indices/:indexName')
  @ApiOperation({ summary: 'Delete a search index (use with caution)' })
  @ApiParam({ name: 'indexName', type: String, description: 'Name of the index to delete' })
  @ApiResponse({ status: 200, description: 'Index deleted successfully.' })
  @ApiResponse({ status: 404, description: 'Index not found.' })
  async deleteIndex(@Param('indexName') indexName: string) {
    // const result = await this.indexingService.deleteIndex(indexName);
    // return result;
    return { message: `Index ${indexName} deletion endpoint conceptual.` };
  }
}
```

## Security Considerations

*   **Strict Access Control**: Paramount. These endpoints can significantly impact search functionality and data. Use dedicated admin roles and strong authentication.
*   **Input Validation**: Validate all parameters, especially index names and any raw Elasticsearch queries if accepted (though direct query passthrough is discouraged).
*   **Auditing**: Log all administrative actions performed via these APIs for security and troubleshooting.
*   **Resource Protection**: Re-indexing can be resource-intensive. Ensure that triggering these operations doesn't overload the system. Consider queueing mechanisms for re-indexing tasks.
*   **Destructive Operations**: Endpoints like deleting an index should have extra safeguards, perhaps requiring a confirmation parameter or specific high-privilege roles.
