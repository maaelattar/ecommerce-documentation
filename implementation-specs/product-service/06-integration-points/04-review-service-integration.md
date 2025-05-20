# Product Service Integration with Review Service (Potential)

## 1. Overview

This document outlines potential integration points between the **Product Service** and a dedicated **Review Service**. The primary approach for such integrations should be **asynchronous and event-driven** where possible, with synchronous API calls reserved for specific, justified scenarios like real-time validation.

Interactions typically fall into two categories:

1.  **Product Service needing review data**: To display review summaries (average rating, count) or lists of reviews on product pages.
2.  **Review Service needing product data**: To validate product existence when a review is submitted, or to display basic product information alongside reviews.

## 2. Asynchronous Integration Patterns (Preferred)

### 2.1. Review Data for Product Service (Displaying Review Summaries)

- **Scenario**: Product Service needs to display `averageRating` and `reviewCount` for products (e.g., on product listings, product detail pages, for search result enrichment).
  - **Event-Driven Approach**: The Review Service, after calculating new statistics for a product (e.g., after a new review is approved, or a review is deleted), publishes an event like `ProductReviewStatsUpdated { productId, averageRating, reviewCount, lastReviewDate }`.
  - Product Service subscribes to these events and updates its local, denormalized product information. This updated product information (including review stats) is then available for its own API responses and for indexing into the Search Service.

### 2.2. Product Data for Review Service (Enriching Review Displays)

- **Scenario**: Review Service needs to display product name and image alongside reviews.
  - **Event-Driven Approach**: Review Service subscribes to `ProductCreated`, `ProductUpdated` (specifically for changes to name, image URL, status), and `ProductDeleted` events from Product Service.
  - It maintains a local, eventually consistent cache of these basic details for products that have reviews associated with them. This cache is used when displaying review lists or individual reviews, avoiding synchronous calls to Product Service for data that changes relatively infrequently.

## 3. Exceptional Synchronous API Calls

Synchronous calls should be justified and adhere to the [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md) (for the calling service) and [Exposing Product Service APIs](./08-exposing-product-service-apis.md) (for the called service).

### 3.1. Product Service Calls Review Service (Displaying Full Review Lists)

- **Purpose**: To fetch a list of actual review texts, ratings, and reviewer details for a specific product, typically for display on a product detail page when a user explicitly requests to see reviews.
- **Justification**: While summary stats are event-driven, fetching a potentially long and dynamic list of full reviews on-demand might be better suited for a synchronous, paginated API call if the data isn't easily denormalized into Product Service or if real-time updates (e.g. new reviews appearing instantly) are desired for this specific view.
- **Review Service Endpoint(s)**: e.g., `GET /reviews?productId={id}&page={page}&limit={limit}&sortBy=recent`
- **Response Payload(s) Example**:
  ```json
  {
    "productId": "uuid",
    "averageRating": 4.5, // Can still be part of this response
    "reviewCount": 120,
    "reviews": [
      {
        "reviewId": "review_uuid_1",
        "rating": 5,
        "title": "Great product!",
        "comment": "...",
        "reviewerName": "UserX",
        "createdAt": "ISO8601"
      }
      // ... more reviews ...
    ],
    "pagination": { "currentPage": 1, "totalPages": 12, "pageSize": 10 }
  }
  ```

### 3.2. Review Service Calls Product Service (Validating Product on Review Submission)

- **Purpose**: When a user submits a new review, Review Service needs to validate that the `productId` (or `variantId`) provided is valid, and the product is in an active/reviewable state.
- **Justification**: This is a critical validation step to ensure data integrity for new reviews. An event-driven check might lead to orphan reviews if the product doesn't exist or becomes inactive before the event is processed.
- **Product Service Endpoint(s) Consumed**: e.g., `GET /products/{productId}/validation-status` or a lightweight `HEAD /products/{productId}`. The endpoint should ideally return minimal data (e.g., just status or HTTP 200 OK if valid, 404 if not).
- **Key Information Used by Review Service**: Confirmation of existence and active status.

## 4. Considerations

- **Dedicated Review Service**: These patterns assume a dedicated Review Service. If reviews are a very simple feature embedded directly within Product Service (not generally recommended for scalability or feature richness like moderation), these integrations are internal module interactions, not inter-service.
- **Data Ownership**: Review Service owns review data. Product Service owns product data. Events and minimal synchronous calls help maintain this boundary while enabling features.

## 5. References

- [Product Service OpenAPI Specification](../../openapi/product-service.yaml)
- [Review Service OpenAPI Specification](../../../review-service/openapi/review-service.yaml) _(Assumed path)_
- [Product Service - Phase 5 Event Publishing](../../05-event-publishing/)
- [General API Consumption Guidelines](./07-general-api-consumption-guidelines.md)
- [Exposing Product Service APIs](./08-exposing-product-service-apis.md)
