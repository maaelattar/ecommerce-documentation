# Content Events for Search Service

## Overview

To provide comprehensive search results that include not just products but also informational content (like blog posts, articles, help pages, FAQs), the Search Service needs to subscribe to events from Content Management Systems (CMS) or other services responsible for managing this type of content.

## Subscribed Content Events

The following events related to content are typically consumed by the Search Service.

### 1. `ContentPublished` (or `ContentCreated`, `ArticlePublished`)

*   **Source Service**: CMS / Content Service
*   **Topic**: `content.events` (or `cms.events`)
*   **Trigger**: A new piece of content (article, blog post, FAQ, etc.) is published and made live.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-content-published-1",
      "eventType": "ContentPublished",
      "timestamp": "2023-11-17T10:00:00Z",
      "version": "1.0",
      "source": "CmsService",
      "data": {
        "id": "article_xyz789",
        "title": "Top 10 Features of Our New Product Line",
        "slug": "top-10-features-new-product-line",
        "contentType": "blog-post", // e.g., blog-post, help-article, faq, landing-page
        "authorId": "author_jane_doe",
        "authorName": "Jane Doe", // Denormalized for convenience
        "body": "<p>Discover the amazing new features...</p>", // Or a path to the full content, or a summarized version
        "excerpt": "A quick look at the top 10 features of our exciting new product line, designed to enhance your experience.",
        "tags": ["new products", "features", "innovation"],
        "keywords": ["product update", "technology", "gadgets"],
        "publicationDate": "2023-11-17T09:55:00Z",
        "lastModifiedDate": "2023-11-17T09:55:00Z",
        "status": "published",
        "visibility": "public",
        "seoTitle": "Explore Top 10 Features: New Product Line | OurBrand",
        "seoDescription": "Learn about the innovative features in our latest product line. Read the full article now.",
        "customFields": {
          "relatedProductId": "prod_abc123"
        }
        // Any other fields relevant for searching and filtering
      }
    }
    ```
*   **Search Service Action**: Create a new document in the content search index (e.g., an Elasticsearch index dedicated to articles, blogs, FAQs).

### 2. `ContentUpdated`

*   **Source Service**: CMS / Content Service
*   **Topic**: `content.events`
*   **Trigger**: An existing piece of published content is updated.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-content-updated-2",
      "eventType": "ContentUpdated",
      "timestamp": "2023-11-17T11:30:00Z",
      "version": "1.1", // Version incremented
      "source": "CmsService",
      "data": {
        "id": "article_xyz789",
        // Full updated content or partial. Full is often simpler.
        "title": "Top 12 Features of Our New Product Line (Updated)", // Updated title
        "body": "<p>We\'ve added even more to discover...</p>",
        "excerpt": "An updated look at the top 12 features of our exciting new product line, designed to further enhance your experience.",
        "tags": ["new products", "features", "innovation", "update"], // Added a tag
        "lastModifiedDate": "2023-11-17T11:28:00Z",
        "customFields": {
          "relatedProductId": "prod_abc123",
          "editorNote": "Minor corrections applied."
        }
        // ... other fields
      }
    }
    ```
*   **Search Service Action**: Update the corresponding document in the content search index.

### 3. `ContentUnpublished` (or `ContentArchived`, `ContentStatusChanged`)

*   **Source Service**: CMS / Content Service
*   **Topic**: `content.events`
*   **Trigger**: A piece of content is unpublished, archived, or its status changes in a way that it should no longer be searchable by the general public.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-content-unpublished-3",
      "eventType": "ContentUnpublished",
      "timestamp": "2023-11-17T12:00:00Z",
      "version": "1.0",
      "source": "CmsService",
      "data": {
        "id": "article_xyz789",
        "newStatus": "archived", // Or unpublished, draft
        "oldStatus": "published",
        "unpublishedDate": "2023-11-17T11:59:00Z"
      }
    }
    ```
*   **Search Service Action**: Depending on the new status:
    *   If unpublished/archived and should not be searchable: Delete the document from the public content search index or update a status field to filter it out from public queries.
    *   If it's a status change (e.g., from `public` to `restricted`), update the document's access control fields.

### 4. `ContentDeleted`

*   **Source Service**: CMS / Content Service
*   **Topic**: `content.events`
*   **Trigger**: A piece of content is permanently deleted from the CMS.
*   **Payload Structure (Example JSON)**:
    ```json
    {
      "eventId": "uuid-content-deleted-4",
      "eventType": "ContentDeleted",
      "timestamp": "2023-11-17T12:30:00Z",
      "version": "1.0",
      "source": "CmsService",
      "data": {
        "id": "faq_old_001",
        "deletedAt": "2023-11-17T12:29:00Z"
      }
    }
    ```
*   **Search Service Action**: Delete the corresponding document from the content search index.

## General Considerations for Content Events

*   **Content Structure**: The `body` of the content might be large. Decide whether to index the full body or an extracted/summarized version. For full-text search, the full body is often needed. Consider how HTML or other markup is handled (stripped, indexed, etc.).
*   **Content Types**: Clearly define the various `contentType` values and how they might influence search behavior or filtering.
*   **Richness of Data**: Include fields like tags, keywords, SEO metadata, and custom fields as they can be valuable for relevance and filtering in search.
*   **Permissions**: If content has visibility restrictions (e.g., internal articles, member-only content), this information must be in the event so the Search Service can apply appropriate filters.

## Search Service Responsibilities

*   Subscribe to `content.events` (or equivalent) topic(s).
*   Deserialize, validate, and transform content event data.
*   Extract and prepare text for full-text indexing, potentially applying specific text analysis (e.g., HTML stripping, language-specific analyzers).
*   Perform CRUD operations on its content search index in Elasticsearch.
*   Handle errors and ensure idempotency of processing.
