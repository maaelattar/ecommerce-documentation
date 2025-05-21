# Indexing Operations and Management

## Overview

Effective management of Elasticsearch indexing operations is critical for ensuring the Search Service provides accurate, up-to-date, and performant search results. This document covers the operational aspects of managing Elasticsearch indexes, including templates, mappings, re-indexing strategies, and the operational considerations for batch ingestion jobs.

## 1. Index Lifecycle Management (ILM) - If Applicable

For time-series data or logs, Elasticsearch ILM policies are powerful. For product/content search indexes that are continuously updated rather than rolling over by time, full ILM might be less relevant, but some concepts apply.

*   **Primary Use Case for Search**: While full ILM (hot-warm-cold-delete phases) is less common for a primary search index that needs to be fully queryable, ILM can be used to automate actions like `rollover` for write aliases if index size becomes a concern, or to manage snapshot policies.
*   If not using full ILM, manual or scripted processes for index management (templates, aliases, re-indexing) are needed.

## 2. Index Templates

*   **Purpose**: Automatically apply predefined settings (number of shards, replicas, refresh interval) and mappings to new indexes that match a specific name pattern.
*   **Best Practice**: Define index templates for all primary data types (e.g., `products-template`, `categories-template`, `content-template`).
*   **Management**: 
    *   Store template definitions in version control (JSON format).
    *   Apply templates to Elasticsearch using its API, typically during initial setup or via CI/CD when template definitions change.
    *   Example template pattern: `products-*` would apply to `products_v1`, `products_v2`, etc.

    ```json
    // Example: products-template.json
    {
      "index_patterns": ["products-*"],
      "template": {
        "settings": {
          "number_of_shards": 5,
          "number_of_replicas": 1,
          "refresh_interval": "5s", // Adjust based on indexing frequency and consistency needs
          "analysis": {
            // ... custom analyzers as defined in data model documentation ...
          }
        },
        "mappings": {
          // ... explicit mappings for product fields (name, description, price, etc.) ...
          // Refer to ../02-data-model-and-indexing/
        }
      }
    }
    ```

## 3. Mappings Management

*   **Importance**: Explicit mappings define how data in each field is indexed and stored (data type, analyzer, whether it's searchable, sortable, aggregatable).
*   **Updates**: 
    *   Adding new fields to an existing mapping is generally safe (if dynamic mapping is not strictly disabled).
    *   Changing the type or core indexing options of an existing field in a live index requires re-indexing the data into a new index with the updated mapping.
*   **Process**: Store mappings as part of index templates. When a mapping change is needed that requires re-indexing, a new version of the template and a new index will be created.

## 4. Re-indexing Strategies

Re-indexing is necessary for mapping changes, major Elasticsearch version upgrades, or recovering from certain issues. The goal is to minimize or eliminate downtime.

*   **Using Aliases (Standard Approach for Zero-Downtime)**:
    1.  **Current State**: A read/write alias (e.g., `products_live`) points to the current active index (e.g., `products_v1`). The Search Service application reads from and writes to `products_live`.
    2.  **Create New Index**: Create a new index (e.g., `products_v2`) with the new mappings/settings, using the updated index template.
    3.  **Re-index Data**: Use the Elasticsearch `_reindex` API or a custom batch job (see section 5) to copy and transform data from `products_v1` to `products_v2`.
        *   The `_reindex` API can often run in the background.
        *   During this time, live updates (from Kafka events) are still going to `products_live` (i.e., `products_v1`). These updates need to be captured and applied to `products_v2` as well. This can be complex:
            *   **Option A (Delta Re-index)**: After the main `_reindex` from `v1` to `v2` is complete, run another `_reindex` operation for documents updated in `v1` since the re-indexing started (using a timestamp or version field).
            *   **Option B (Dual Writes - Complex)**: Temporarily configure the application to write to both `products_v1` and `products_v2` (or have a process that replicates writes). This is more complex to implement correctly.
            *   **Option C (Replay from Source)**: If re-indexing takes a long time, it might be simpler to re-process all events from Kafka (from a certain point in time) or re-run batch jobs against `products_v2` after the initial bulk copy from `products_v1`.
    4.  **Verify New Index**: Thoroughly test `products_v2` (query performance, data integrity).
    5.  **Switch Alias**: Atomically update the `products_live` alias to point from `products_v1` to `products_v2`.
        ```json
        POST /_aliases
        {
          "actions": [
            { "remove": { "index": "products_v1", "alias": "products_live" } },
            { "add":    { "index": "products_v2", "alias": "products_live" } }
          ]
        }
        ```
    6.  **Delete Old Index**: After a safe period (and confirming `products_v2` is stable), delete `products_v1`.

*   **Considerations for Re-indexing**: 
    *   **Resource Intensive**: Re-indexing can be demanding on the Elasticsearch cluster (CPU, I/O, disk space for the new index).
    *   **Time Consuming**: For large indexes, it can take hours or even days.
    *   **Monitoring**: Closely monitor Elasticsearch cluster health and re-indexing progress.
    *   **Throttling**: The `_reindex` API supports `requests_per_second` to throttle the operation.

## 5. Operational Management of Batch Ingestion Jobs

(Refer to `../06-integration-points/01-batch-data-ingestion.md` for batch job design)

*   **Scheduling**: Use a reliable scheduler (Kubernetes CronJobs, Airflow, etc.) for periodic batch jobs (e.g., nightly reconciliation, full re-syncs if needed).
*   **Job Monitoring**: 
    *   Track job status (success, failure, running time).
    *   Number of records processed, created, updated, failed.
    *   Log output for errors and progress.
*   **Alerting**: Set up alerts for batch job failures or jobs running significantly longer than expected.
*   **Resource Allocation**: Ensure batch jobs have adequate resources (CPU, memory, network bandwidth) and don't overwhelm source systems or Elasticsearch.
*   **Idempotency**: Design batch jobs to be idempotent (re-runnable without side effects).
*   **Configuration**: Manage configurations for batch jobs (source DB connections, target ES index, batch sizes) securely and flexibly.
*   **Manual Triggers**: Provide a way for administrators to manually trigger batch jobs for specific scenarios (e.g., initial data load, disaster recovery).

## 6. Capacity Planning for Index Growth

*   **Monitor Disk Usage**: Track disk space usage on Elasticsearch data nodes and project growth trends.
*   **Monitor Document Counts and Index Sizes**: Understand how data volume is growing.
*   **Shard Size Management**: Keep an eye on average shard sizes. If shards are consistently growing too large, plan to adjust the number of primary shards for new indexes (or re-index existing ones).
*   **Scaling Elasticsearch**: Be prepared to scale the Elasticsearch cluster (add more data nodes, increase resources per node) as data grows or query/indexing load increases.

## 7. Routine Index Maintenance

*   **`_forcemerge` API (Use with Caution)**:
    *   Can be used to reduce the number of segments per shard, potentially improving search performance and reducing disk space for read-heavy indexes where updates are infrequent.
    *   It is a resource-intensive operation. Should be run during off-peak hours.
    *   Modern Elasticsearch versions handle segment merging well automatically, so manual `_forcemerge` is less often needed but can be a tool for specific optimization scenarios.
*   **Clear Cache API (`_cache/clear`)**: Rarely needed and can negatively impact performance by clearing caches. Use only if specifically troubleshooting cache-related issues.

Effective indexing operations ensure that the Search Service can adapt to changing data, new requirements, and maintain optimal performance over time.
