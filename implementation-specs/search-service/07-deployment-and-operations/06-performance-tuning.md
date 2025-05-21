# Performance Tuning and Optimization

## Overview

Performance is a critical aspect of any search service. Slow search queries or indexing delays can lead to poor user experience and outdated search results. This document outlines strategies and considerations for tuning and optimizing the performance of both the Search Service application (NestJS) and the underlying Elasticsearch cluster.

## I. Search Service Application Performance

### 1. Code Optimization (NestJS / Node.js)

*   **Asynchronous Operations**: Ensure all I/O-bound operations (calls to Elasticsearch, Kafka, external services if any) are asynchronous (`async/await`) to prevent blocking the Node.js event loop.
*   **Efficient Data Handling**: Minimize data manipulation and transformations. Use efficient algorithms and data structures.
*   **Payload Sizes**: Be mindful of the size of data retrieved from Elasticsearch and sent to clients. Only fetch and return necessary fields.
*   **Stream Processing (for large datasets)**: If dealing with extremely large request/response bodies or batch operations, consider using streams, though this is less common for typical search API responses.
*   **Dependency Management**: Keep dependencies up-to-date, as newer versions often include performance improvements and bug fixes.
*   **Profiling**: Use Node.js profiling tools (e.g., `node --prof`, Chrome DevTools profiler, Clinic.js) to identify CPU bottlenecks and memory leaks within the NestJS application.

### 2. Caching Strategies

(Also refer to `../03-core-components/08-cache-management.md`)
*   **API Response Caching**: Cache responses for frequently requested, non-personalized, or slowly changing search queries.
    *   **Cache Store**: In-memory cache (e.g., `@nestjs/cache-manager` with default store for single instances, not suitable for scaled deployments) or a distributed cache like Redis or Memcached for multiple service instances.
    *   **Cache Keys**: Use query parameters (keywords, filters, pagination) to generate unique cache keys.
    *   **Cache Invalidation**: Implement strategies to invalidate cache when underlying data changes (e.g., time-based TTL, event-driven invalidation based on Kafka events, explicit API calls).
*   **Elasticsearch Query Cache**: Elasticsearch has its own query cache. Ensure it's enabled and sized appropriately. Application-level caching is for full API responses.
*   **Caching External Data**: If the Search Service relies on any external data (e.g., for enrichment, though discouraged for real-time paths), cache this data aggressively.

### 3. Connection Pooling

*   **Elasticsearch Client**: Ensure the Elasticsearch client library uses connection pooling effectively to reuse connections to the ES cluster.
*   **Kafka Client**: Kafka clients also manage connections to brokers.
*   Ensure pool sizes are appropriately configured based on expected load and concurrent requests.

### 4. Load Balancing

*   Effective load balancing (e.g., via Kubernetes Service) across multiple instances of the Search Service is crucial for distributing traffic and preventing overload on individual instances.

### 5. Optimizing Event Consumption (Kafka)

*   **Batching**: Configure the Kafka consumer to fetch messages in batches.
*   **Concurrent Processing (with care)**: If event processing is I/O bound (e.g., waiting for Elasticsearch), you might explore processing multiple messages from a batch concurrently (e.g., using `Promise.all` with a concurrency limit). However, this can complicate error handling and ordering if not done carefully, especially if events within a batch are dependent.
*   **Efficient Transformation Logic**: Ensure event transformation logic (mapping to ES documents) is highly performant.

## II. Elasticsearch Performance Tuning

### 1. Query Optimization

*   **Understand Your Queries**: Use the Profile API (`_profile`) in Elasticsearch to analyze how search queries are executed and identify slow parts.
*   **Use `filter` Context over `query` Context**: For binary yes/no criteria (e.g., `status: "active"`, `brand: "BrandX"`), use the `filter` context in a `bool` query. Filters are cached and generally faster than queries because they don't affect scores.
*   **Avoid Leading Wildcards**: Queries like `*term` or `?term` are very slow as they require scanning all terms in the index.
*   **Minimize Scripting**: Scripts (Painless, Lucene expressions) in queries can be powerful but are slower than native query clauses. Use them sparingly and optimize them carefully.
*   **Pagination Depth (`from` + `size`)**: Deep pagination can be resource-intensive. Elasticsearch has a default limit (`index.max_result_window`). For very deep pagination, consider using `search_after` or Scroll API (for bulk data export, not interactive search).
*   **Field Selection (`_source` filtering)**: Only retrieve fields that are needed by the application using `_source` includes/excludes. This reduces network traffic and deserialization overhead.
*   **Appropriate Query Types**: Use the right query type for the job (e.g., `match` for full-text, `term` for exact keyword matches on `keyword` fields, `range` for numerical/date ranges).
*   **Optimize `bool` Queries**: Structure `bool` queries effectively. Use `minimum_should_match` carefully.

### 2. Index Design and Mappings

*   **Correct Data Types**: Use appropriate data types (e.g., `keyword` for exact matches/faceting/sorting, `text` for full-text search with analysis, `integer`, `date`).
*   **Disable Unnecessary Indexing**: If a field is only for display and not for searching, sorting, or aggregation, set `"index": false` in its mapping.
*   **Disable `_source` (Rarely Recommended)**: If disk space is extremely critical and you only retrieve data via `docvalue_fields` or `stored_fields`, you could disable `_source`, but this has significant limitations.
*   **`doc_values`**: Enabled by default for most fields. Essential for sorting and aggregations. If a field is never used for sorting/aggregations, you could disable `doc_values` to save a small amount of disk space, but this is usually not worth the trade-off.
*   **`norms`**: Store normalization factors for scoring. If scoring is not important for a specific `text` field, you can disable `norms` to save disk space (`"norms": false`).
*   **Analyzers**: Choose and configure analyzers appropriately for `text` fields. Over-analysis or incorrect analysis can lead to poor relevance or performance.
*   **Sharding Strategy**: As discussed in `02-elasticsearch-cluster-management.md`, an appropriate number of primary shards and shard size is crucial. Too many small shards or too few large shards can hurt performance.

### 3. Hardware and Cluster Configuration

*   **RAM**: Sufficient RAM for Elasticsearch heap and OS file system cache.
*   **Disk**: Fast SSDs (NVMe preferred).
*   **CPU**: Adequate CPU cores.
*   **Network**: Low-latency, high-bandwidth network between application nodes and Elasticsearch nodes, and between Elasticsearch nodes themselves.
*   **JVM Tuning**: Ensure JVM heap size is set correctly (max ~30-31GB, not more than 50% of node RAM). Monitor GC activity.
*   **Elasticsearch Caches**: Configure sizes for query cache, field data cache, etc., based on workload. Be cautious with manual adjustments; defaults are often reasonable.

### 4. Indexing Performance

*   **Use Bulk API**: Always use the Bulk API for indexing multiple documents.
*   **Optimize Bulk Request Size**: Experiment with optimal bulk request sizes (e.g., 1-10MB). Too small increases overhead; too large can cause memory pressure.
*   **Parallel Indexing Clients**: Multiple clients or threads writing in parallel can improve throughput, but don't overwhelm the cluster.
*   **Refresh Interval (`index.refresh_interval`)**: Increase the refresh interval (e.g., `30s` or `-1` to disable and refresh manually/periodically) during heavy initial loads or batch indexing to reduce the overhead of creating new segments. This means data takes longer to become searchable.
*   **Replicas During Initial Load**: For very large initial data loads, you can temporarily set `number_of_replicas` to 0, perform the load, and then increase it back to the desired value. This speeds up indexing as data doesn't need to be replicated simultaneously.
*   **Translog Settings**: Ensure `index.translog.durability` is appropriate (`request` for durability, `async` for higher performance but slight risk of data loss on crash if not fsynced).

### 5. Monitoring and Profiling (Elasticsearch)

*   Use Kibana monitoring, Elasticsearch APIs (`_nodes/stats`, `_indices/stats`, `_cat` APIs), or third-party monitoring tools to identify bottlenecks.
*   **Hot Threads API (`_nodes/hot_threads`)**: Helps identify what Elasticsearch threads are busy with.
*   **Slow Log**: Configure slow logs for search and indexing to capture operations exceeding certain time thresholds.

## Continuous Process

Performance tuning is not a one-time task. It requires continuous monitoring, analysis, and adjustments as data volumes, query patterns, and application features evolve. Regularly review slow queries, indexing performance, and cluster health.
