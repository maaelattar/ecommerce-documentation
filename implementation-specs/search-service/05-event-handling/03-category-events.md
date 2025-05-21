# Category Events for Search Service

## Overview

The Search Service subscribes to events from the Category Service (or any service managing category data) to keep its category information and product-to-category associations in the search indexes accurate. Changes to categories can affect product listings, faceting, and category-specific searches.

## Subscribed Category Events

The following events related to categories are typically consumed by the Search Service.

### 1. `CategoryCreated`

*   **Source Service**: Category Service
*   **Topic**: `category.events` (or a more general `taxonomy.events`)
*   **Trigger**: A new category is successfully created.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-category-created-1",
      "eventType": "CategoryCreated",
      "timestamp": "2023-11-16T09:00:00Z",
      "version": "1.0",
      "source": "CategoryService",
      "data": {
        "id": "cat_elec_001",
        "name": "Consumer Electronics",
        "description": "Gadgets and devices for everyday use.",
        "slug": "consumer-electronics",
        "parentCategoryId": null, // null for top-level categories
        "ancestorCategoryIds": [], // Path from root
        "imageUrl": "https://example.com/images/cat_elec_001.jpg",
        "isActive": true,
        "sortOrder": 10,
        "metaTitle": "Shop Consumer Electronics Online",
        "metaDescription": "Find the best deals on consumer electronics.",
        "createdAt": "2023-11-16T08:59:00Z",
        "updatedAt": "2023-11-16T08:59:00Z"
        // Include all fields relevant for search faceting, display, or filtering
      }
    }
    ```
*   **Search Service Action**:
    *   If categories are indexed as separate documents (for category search/browsing), create a new category document in the category index.
    *   Potentially update product documents if this category creation affects their denormalized category information (though usually `ProductUpdated` events would handle product-category linkage changes).

### 2. `CategoryUpdated`

*   **Source Service**: Category Service
*   **Topic**: `category.events`
*   **Trigger**: An existing category's details are updated (e.g., name, description, parent, status).
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-category-updated-2",
      "eventType": "CategoryUpdated",
      "timestamp": "2023-11-16T09:30:00Z",
      "version": "1.0",
      "source": "CategoryService",
      "data": {
        "id": "cat_elec_001",
        // Full updated category data or partial. Full is often simpler for search.
        "name": "Consumer Electronics & Gadgets", // Updated name
        "description": "A wide range of the latest gadgets and electronic devices for home and personal use.",
        "isActive": true,
        "metaTitle": "Buy Consumer Electronics & Gadgets Online", // Updated meta title
        "updatedAt": "2023-11-16T09:29:00Z"
        // ... other fields
      }
    }
    ```
*   **Search Service Action**:
    *   Update the corresponding category document in the category index.
    *   If category details (like name or hierarchy) are denormalized into product documents, this event might trigger updates to affected product documents in the product index. This can be a cascading update; careful consideration is needed for performance.

### 3. `CategoryDeleted`

*   **Source Service**: Category Service
*   **Topic**: `category.events`
*   **Trigger**: A category is permanently deleted.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-category-deleted-3",
      "eventType": "CategoryDeleted",
      "timestamp": "2023-11-16T10:00:00Z",
      "version": "1.0",
      "source": "CategoryService",
      "data": {
        "id": "cat_fashion_old_002",
        "deletedAt": "2023-11-16T09:59:00Z"
        // Optionally, information about how to handle products previously in this category
        // e.g., re-assign to a parent or a default category, or if products are also deleted.
      }
    }
    ```
*   **Search Service Action**:
    *   Delete the corresponding category document from the category index.
    *   Handle products associated with this category: remove the category from their denormalized data or potentially mark them for review if they become uncategorized. This requires careful coordination with the Product Service logic.

### 4. `CategoryMoved` (or `CategoryParentChanged`)

*   **Source Service**: Category Service
*   **Topic**: `category.events`
*   **Trigger**: A category is moved under a different parent category, changing its position in the hierarchy.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-category-moved-4",
      "eventType": "CategoryMoved",
      "timestamp": "2023-11-16T10:30:00Z",
      "version": "1.0",
      "source": "CategoryService",
      "data": {
        "id": "cat_sub_accessories_005",
        "newParentCategoryId": "cat_main_electronics_001",
        "oldParentCategoryId": "cat_main_lifestyle_002",
        "newAncestorCategoryIds": ["cat_main_electronics_001"],
        "oldAncestorCategoryIds": ["cat_main_lifestyle_002"],
        "updatedAt": "2023-11-16T10:29:00Z"
      }
    }
    ```
*   **Search Service Action**:
    *   Update the category document in the category index with the new parent and ancestor information.
    *   This is a significant change that will likely require updating the denormalized category hierarchy information (e.g., breadcrumbs, facet paths) in all associated product documents. This can be a heavy operation.

## General Considerations for Category Events

*   **Impact on Products**: Changes in categories (especially hierarchy or deletion) can have a widespread impact on product data within the search index. The event processing logic must account for these cascading effects efficiently.
*   **Denormalization Strategy**: The Search Service often denormalizes category information (names, paths) into product documents for efficient filtering and faceting. Category events must trigger updates to this denormalized data.
*   **Hierarchy Management**: Accurately reflecting the category hierarchy is crucial for navigation and faceting. Events should provide clear information about parent-child relationships and paths (e.g., `ancestorCategoryIds`).
*   **Consistency**: Ensuring consistency between the Category Service's view of the hierarchy and the Search Service's indexed representation is vital.

## Search Service Responsibilities

*   Subscribe to `category.events` topic(s).
*   Deserialize, validate, and transform category event data.
*   Update its category index (if maintained separately).
*   Propagate relevant changes to the product index, updating denormalized category information in product documents.
*   Manage potential cascading updates efficiently.
*   Handle errors and ensure idempotency.
