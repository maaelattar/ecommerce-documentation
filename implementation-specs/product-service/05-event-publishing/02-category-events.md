# Category Events Specification

## 1. Overview

This document details the domain events published by the Product Service related to the lifecycle and state changes of product Categories.

All events follow the [General Event Structure defined in the Event Publishing Overview](../05-event-publishing/00-overview.md#5-general-event-structure).

## 2. Category Events

### 2.1. `CategoryCreated`

- **`eventType`**: `CategoryCreated`
- **`eventVersion`**: `1.0`
- **Description**: Published when a new category is successfully created.
- **Trigger**: Successful completion of the `createCategory` method in `CategoryService` (within Product Service).
- **`entityId`**: The `categoryId` of the newly created category.
- **Payload Schema**:
  ```json
  {
    "categoryId": "uuid",
    "name": "string",
    "description": "string",
    "parentId": "uuid", // null if it's a top-level category
    "path": "string", // e.g., "uuid-parent/uuid-child"
    "level": "integer", // Hierarchy level
    "metadata": {"key": "value"},
    "createdAt": "ISO8601",
    "createdBy": "string"
  }
  ```
- **Potential Consumers**: Search Service (for faceted search), Navigation builders, Analytics Service.

### 2.2. `CategoryUpdated`

- **`eventType`**: `CategoryUpdated`
- **`eventVersion`**: `1.0`
- **Description**: Published when attributes of an existing category are updated (e.g., name, description, metadata).
- **Trigger**: Successful completion of the `updateCategory` method.
- **`entityId`**: The `categoryId` of the updated category.
- **Payload Schema**:
  ```json
  {
    "categoryId": "uuid",
    "updatedFields": ["string"], // e.g., ["name", "description", "metadata.isActive"]
    "name": "string", // Current value
    "description": "string", // Current value
    "metadata": {"key": "value"}, // Current value
    "updatedAt": "ISO8601",
    "updatedBy": "string"
  }
  ```
- **Potential Consumers**: Search Service, Navigation builders, Cache invalidation services.

### 2.3. `CategoryDeleted`

- **`eventType`**: `CategoryDeleted`
- **`eventVersion`**: `1.0`
- **Description**: Published when a category is successfully deleted.
- **Trigger**: Successful completion of the `deleteCategory` method.
- **`entityId`**: The `categoryId` of the deleted category.
- **Payload Schema**:
  ```json
  {
    "categoryId": "uuid",
    "deletedAt": "ISO8601",
    "deletedBy": "string"
  }
  ```
- **Potential Consumers**: Search Service, Navigation builders (to remove the category), Product Service itself (potentially to disassociate products or re-assign to a default category if business rules dictate).

### 2.4. `CategoryMoved`

- **`eventType`**: `CategoryMoved`
- **`eventVersion`**: `1.0`
- **Description**: Published when a category is moved to a new parent, affecting its position in the hierarchy.
- **Trigger**: Successful completion of the `moveCategory` method.
- **`entityId`**: The `categoryId` of the moved category.
- **Payload Schema**:
  ```json
  {
    "categoryId": "uuid",
    "oldParentId": "uuid", // null if was top-level
    "newParentId": "uuid", // null if moved to top-level
    "oldPath": "string",
    "newPath": "string",
    "newLevel": "integer",
    "movedAt": "ISO8601",
    "movedBy": "string"
  }
  ```
- **Potential Consumers**: Search Service, Navigation builders, Product data synchronization services.

## 3. References

- [Event Publishing Overview](./00-overview.md)
- [Category Entity Model](../../02-data-model-setup/02b-category-entity.md) 