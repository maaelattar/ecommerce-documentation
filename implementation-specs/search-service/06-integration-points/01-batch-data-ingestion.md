# Batch Data Ingestion for Search Service

## Overview

While the primary mechanism for keeping the Search Service's indexes up-to-date is through real-time event consumption, batch data ingestion plays a crucial role in several scenarios:

1.  **Initial Data Seeding**: When the Search Service is first deployed, or a new index is created (e.g., for a new locale or a completely new type of searchable content), a batch process is needed to populate the search indexes with existing data from the source-of-truth systems.
2.  **Full Re-synchronization/Reconciliation**: As detailed in `../05-event-handling/10-data-consistency-strategies.md`, periodic full re-syncs or reconciliation jobs can correct any discrepancies that might have accumulated over time due to missed events, bugs, or other issues.
3.  **Recovery from Failures**: In case of major issues with the eventing pipeline or catastrophic data corruption in a search index, a batch job might be the most reliable way to restore a healthy state.
4.  **Data Backfills**: When the search schema changes or new fields are introduced that require data not available in historical events, a batch job can backfill this information from source systems.

This document outlines the strategies and considerations for implementing batch data ingestion for the Search Service.

## Data Sources

Batch ingestion will typically pull data directly from the source-of-truth microservices' databases or dedicated data stores. This requires appropriate permissions and often a read-replica or an export mechanism to avoid impacting the transactional load on the primary databases.

*   **Product Data**: From Product Service database.
*   **Category Data**: From Category Service database.
*   **Content Data**: From CMS/Content Service database or exports.
*   **User Data (if applicable for personalization/entitlements)**: From User Service database.

## Ingestion Mechanisms and Technologies

Several approaches can be used for batch ingestion:

1.  **Scheduled Batch Jobs (e.g., Cron Jobs, Kubernetes CronJobs)**:
    *   A dedicated script or application (potentially part of the Search Service deployment or a separate utility) runs on a schedule.
    *   This job queries the source databases, transforms the data, and uses the Elasticsearch bulk API to index it.
    *   **Technology**: Can be written in any language (Python, Node.js/TypeScript, Java) with appropriate database connectors and Elasticsearch client libraries.

2.  **Data Pipeline Tools (e.g., Apache NiFi, Apache Airflow, AWS Glue, Logstash JDBC Input)**:
    *   These tools provide robust frameworks for building ETL (Extract, Transform, Load) pipelines.
    *   **Logstash**: Can use the JDBC input plugin to read from databases and the Elasticsearch output plugin to write to Elasticsearch. Suitable for simpler, continuous batch syncs.
    *   **Airflow/NiFi/Glue**: Offer more complex workflow management, scheduling, monitoring, and error handling for large-scale batch operations.

3.  **Elasticsearch Ingest Pipelines (for transformation)**:
    *   Data can be extracted and sent to Elasticsearch, which then uses its own Ingest Node pipelines to perform transformations (e.g., field manipulation, enrichment lookups via enrich processor) before final indexing.
    *   This reduces the transformation load on the client-side batch job.

## Process Flow

A typical batch ingestion process involves:

1.  **Extraction**: Fetch data from the source system(s).
    *   Handle pagination for large datasets.
    *   Filter for active/relevant records if doing a full sync (e.g., only active products).
    *   Consider using snapshotting or consistent reads from the database if possible.
2.  **Transformation**: Convert the source data into the Elasticsearch document schema.
    *   This transformation logic should ideally be consistent with the logic used for event-based updates to ensure data uniformity.
    *   May involve joining data from multiple tables or services (though this increases complexity; denormalized sources are preferred).
3.  **Loading**: Index the transformed data into Elasticsearch.
    *   **Bulk API**: Always use the Elasticsearch Bulk API for efficient batch indexing.
    *   **Index Aliases for Zero-Downtime Re-indexing**: For full re-syncs, a common pattern is:
        1.  Create a new index (e.g., `products_v2`).
        2.  Run the batch job to populate this new index.
        3.  Once populated and verified, atomically switch a common read alias (e.g., `products_live`) from the old index (`products_v1`) to the new index (`products_v2`).
        4.  Delete the old index (`products_v1`) after a safe period.
    *   **Error Handling**: The bulk API provides per-item error details. Log errors and decide on a strategy (e.g., retry failed items, send to a separate "batch DLQ" or error log).
    *   **Throttling**: For very large datasets, implement throttling or control the concurrency of bulk requests to avoid overwhelming Elasticsearch or the source databases.

## Key Considerations

*   **Resource Impact**: Batch jobs can be resource-intensive on both source databases and the Elasticsearch cluster. Schedule them during off-peak hours if possible.
*   **Job Monitoring and Alerting**: Implement robust monitoring for batch job status (success, failure, duration), data processed, and error rates. Alerts for job failures are crucial.
*   **Idempotency**: If a batch job is re-runnable, ensure it doesn't create duplicate documents or have other side effects. Using the entity ID as the Elasticsearch document ID handles this for creations/updates.
*   **Data Consistency during Batch Run**: For long-running batch jobs, the data in the source system might change during the extraction. This means the batch-indexed data might be slightly stale by the time the job finishes. Eventual consistency through ongoing event processing will catch up on these changes.
*   **Concurrency with Event Processing**: Ensure batch updates and real-time event processing don't conflict. Using versioning (as discussed in consistency strategies) can help, where the operation with the higher version (or later timestamp) wins.
*   **Configuration**: Parameterize batch jobs for target indexes, source connection details, etc.
*   **Security**: Secure access to source databases and the Elasticsearch cluster.

## Triggering Batch Jobs

*   **Scheduled**: Regular full syncs or reconciliation (e.g., nightly, weekly).
*   **Manual**: For initial seeding, recovery, or specific backfill operations triggered by administrators.
*   **Event-Triggered (Less Common for Full Batch)**: A specific system event could trigger a targeted mini-batch process, though this blurs the line with regular event handling.

## Example Scenario: Initial Product Seeding

1.  A Kubernetes CronJob is scheduled to run (or triggered manually).
2.  The job (a Node.js script) connects to a read-replica of the Product Service database.
3.  It fetches all active products in batches (e.g., 1000 at a time).
4.  For each batch, it transforms the product data into the `ProductDocument` schema.
5.  It constructs an Elasticsearch bulk request and sends it to the `products_initial_seed` index.
6.  Logs success/failure for each bulk request.
7.  Once complete, an administrator verifies the index and then manually updates the `products_live` alias to point to `products_initial_seed`.

This document provides a foundation for how batch data ingestion can complement event-driven updates for the Search Service, ensuring data completeness and aiding in recovery and reconciliation.
