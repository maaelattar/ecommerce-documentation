# Technology Decision: Caching Implementation Details

*   **Status:** Accepted
*   **Date:** 2025-05-12
*   **Deciders:** Architecture Team, DevOps Team, Lead Developers
*   **Consulted:** Relevant Service Owners
*   **Informed:** All Engineering Teams

## 1. Context & Scope

This document provides detailed implementation, configuration, and operational guidance for the key components of the multi-layered caching strategy established in [ADR-009: Caching Strategy](./../adr/ADR-009-caching-strategy.md).

The primary focus is on the operationalization of the distributed cache (Redis) and the Content Delivery Network (CDN), as well as providing guidance for API Gateway and service-level caching within the e-commerce platform.

## 2. Recap of Multi-Layered Caching Strategy (from ADR-009)

ADR-009 established a multi-layered caching approach to optimize performance, scalability, and resilience. The layers include:

1.  **Client-Side (Browser) Caching:** For static assets and user-specific, non-sensitive data.
2.  **Content Delivery Network (CDN):** For static assets (JS, CSS, images) and publicly cacheable API responses. **Chosen Provider: AWS CloudFront**
3.  **API Gateway Caching:** For caching responses from backend services at the API gateway level.
4.  **Distributed Cache (Redis):** For shared session data, frequently accessed query results, pre-computed data, rate limiting.
5.  **In-Memory Cache (Service-Level):** For very hot, small datasets specific to a service instance.
6.  **Database Caching:** Leveraging built-in database caching capabilities.

Redis was selected as the primary technology for the distributed cache.

## 3. Distributed Cache: Redis Implementation Details

### 3.1. Selected Redis Deployment Model/Provider

*   **Provider/Model:** AWS ElastiCache for Redis
*   **Rationale for Choice:**
    *   **Managed Service:** ElastiCache is a fully managed Redis service by AWS, significantly reducing operational overhead related to provisioning, patching, monitoring, backups, and failure recovery compared to a self-managed deployment.
    *   **AWS Ecosystem Integration:** Seamless integration with other AWS services, including Amazon VPC for network isolation, IAM for access control, CloudWatch for monitoring, and potentially AWS Lambda for event-driven interactions if needed.
    *   **Scalability and High Availability:** ElastiCache provides straightforward mechanisms for scaling (both vertically and horizontally via sharding in cluster mode) and configuring multi-AZ replication for high availability.
    *   **Performance:** Optimized for performance within the AWS environment.
    *   **Security:** Offers encryption in transit and at rest, and network security through security groups and subnet groups.
    *   **Ease of Use:** Simplifies deployment and management, allowing the team to focus on application development rather than Redis administration.

### 3.2. Cluster Configuration (Example - adjust based on chosen model)

*   **Cluster Mode:** Enabled (Recommended for scalability and HA using Redis Cluster).
*   **Node Types/Instance Sizes:** Start with a suitable `cache.m6g.large` or `cache.r6g.large` (Graviton2 instances for better price-performance) and adjust based on performance testing and monitoring of memory usage, CPU, and network.
*   **Sharding Strategy:** ElastiCache for Redis (Cluster Mode Enabled) handles sharding automatically. The number of shards will be determined by the overall data size and throughput requirements (e.g., start with 2-3 shards).
*   **Replication:** Minimum of 1 replica per primary shard (e.g., `Replicas per Node Group: 1`) for Multi-AZ high availability.

### 3.3. Persistence Strategy

*   **RDB Snapshots:** Enabled, Daily automatic snapshots for backup and recovery purposes. Manual snapshots before significant changes.
*   **AOF (Append Only File):** Disabled by default for cache use cases. (Enabling AOF provides higher durability but can impact performance. For most caching scenarios where data can be rebuilt from a source of truth, RDB snapshots for disaster recovery are sufficient. If Redis is used for more durable data storage, AOF might be considered.)
*   **Decision:** For primary caching use cases, RDB snapshots for DR are sufficient. If specific use cases require higher durability from Redis itself, AOF could be enabled on a per-cluster basis, accepting the performance trade-off.

### 3.4. Eviction Policy

*   **Recommended Policy:** `volatile-lru` (Least Recently Used for keys with an expiry set) or `allkeys-lru` (Least Recently Used for all keys) are common starting points for caches.
    *   `volatile-lru`: Removes the least recently used keys out of all keys with an expire set.
    *   `allkeys-lru`: Evicts any key according to the LRU algorithm when memory is full.
*   **Consideration:** The best policy depends on the access patterns. If all keys are equally likely to be accessed again, `allkeys-lru` might be better. If some keys are set without an explicit TTL but should still be evictable, `allkeys-lru` is appropriate. `volatile-ttl` (evict keys with an expire set, prioritizing those with shorter TTL) can also be useful.
*   **Initial Choice:** `volatile-lru` - This assumes most cached items will have a TTL.

### 3.5. Security

*   **Encryption in Transit:** Enabled (TLS).
*   **Encryption at Rest:** Enabled.
*   **Authentication:** Redis AUTH token enabled.
*   **Network Security:** Deployed within a private VPC, accessible only from specific security groups associated with the application services. Utilize ElastiCache subnet groups.

### 3.6. Monitoring and Alerting

*   Leverage AWS CloudWatch metrics for ElastiCache (CPU, Memory, Network, Cache Hit/Miss Rate, Evictions, Latency, Replication Lag).
*   Set up CloudWatch Alarms for key metrics (e.g., high CPU/Memory, low cache hit rate, excessive evictions, increased latency).
*   Integrate with the central monitoring solution (Amazon Managed Grafana, as per [ADR-011](./../adr/ADR-011-monitoring-and-alerting-strategy.md) and the [Monitoring and Observability Stack](./08-monitoring-observability-stack.md) document).

### 3.7. Backup and Recovery

*   Utilize automated daily snapshots provided by ElastiCache.
*   Define retention period for snapshots (e.g., 7-30 days based on recovery needs).
*   Test recovery procedures periodically.

## 4. Content Delivery Network (CDN) Implementation Details

### 4.1. Selected CDN Provider

*   **Provider:** Amazon Web Services (AWS) CloudFront
*   **Rationale for Choice:**
    *   **AWS Ecosystem Integration:** As AWS is our primary cloud provider, CloudFront integrates seamlessly with other AWS services used by the platform, such as Amazon S3 (for static asset hosting), Elastic Load Balancing, API Gateway, and AWS WAF (for security).
    *   **Global Edge Network:** CloudFront has a vast global network of Points of Presence (PoPs), ensuring low-latency delivery of content to users worldwide.
    *   **Performance & Scalability:** It is designed for high performance and can handle large volumes of traffic and sudden spikes.
    *   **Security Features:** Integrates with AWS Shield for DDoS protection and AWS WAF for web application firewall capabilities. Supports HTTPS with custom SSL certificates via AWS Certificate Manager (ACM).
    *   **Cost-Effectiveness:** Offers various pricing options, including pay-as-you-go and Reserved Capacity, which can be cost-effective, especially when leveraging other AWS services (e.g., free data transfer between CloudFront and S3 within the same region for origin fetches).
    *   **Feature Set:** Provides comprehensive features like cache behaviors, origin groups (for failover), Lambda@Edge for request/response manipulation at the edge, real-time logs, and detailed reporting.
    *   **Ease of Management:** Configuration and management can be done via the AWS Management Console, AWS CLI, SDKs, or Infrastructure as Code (IaC) tools like CloudFormation or Terraform.

### 4.2. Configuration for Static Assets (JS, CSS, Images, Fonts)

*   **Origin:** (e.g., S3 bucket, specific service endpoint serving static content).
*   **Cache Behaviors:** Define specific caching rules based on path patterns (e.g., `/static/*`, `/images/*`).
*   **Cache Policies/TTLs:** Set appropriate `Cache-Control` headers (e.g., `max-age`, `s-maxage`, `public`) at the origin. Leverage ETags for validation. Long TTLs for versioned assets (e.g., `main.a1b2c3d4.js`).
*   **Compression:** Enable Gzip/Brotli compression.
*   **Query String Forwarding:** Typically disable for static assets unless query strings are used for versioning.

### 4.3. Configuration for Caching API Responses (Publicly Cacheable Endpoints)

*   **Origin:** API Gateway or specific public-facing services.
*   **Cache Behaviors:** Target specific API paths (e.g., `/api/products`, `/api/categories`).
*   **Cache Policies/TTLs:** Shorter TTLs than static assets. Respect `Cache-Control` headers from API responses (`s-maxage`, `Vary`).
*   **Query String Forwarding:** Forward and cache based on relevant query parameters (e.g., `page`, `pageSize`). Avoid caching based on sensitive or highly variable parameters.
*   **HTTP Methods:** Typically cache `GET` and `HEAD` requests.

### 4.4. Custom Domain & SSL/TLS Certificate Management

*   Configure custom domain(s) (e.g., `cdn.example.com`) for CDN distributions.
*   Manage SSL/TLS certificates (e.g., AWS Certificate Manager, Let's Encrypt, or provider-managed certificates).

### 4.5. Cache Invalidation Mechanisms

*   **API-based Invalidation:** Use CDN provider APIs for targeted or wildcard invalidations when content updates.
*   **Versioning:** Use versioned filenames for static assets (e.g., `styles.v1.2.css`) to ensure new versions are fetched without explicit invalidation.
*   **Strategy:** (Define when and how invalidations will be triggered, e.g., during CI/CD deployment, after content updates).

### 4.6. Key Metrics for Monitoring CDN Performance

*   **Hit Rate/Miss Rate:** (Percentage of requests served from cache vs. origin).
*   **Latency:** (Edge latency, origin latency).
*   **Traffic Volume:** (Data transferred, requests served).
*   **Error Rates:** (4xx, 5xx errors from edge and origin).
*   **Cost:** (Monitor CDN usage and associated costs).

## 5. API Gateway Caching Implementation Details

As per ADR-014 (API Gateway Strategy) and our AWS-centric approach, Amazon API Gateway is the likely candidate for our API Gateway layer. It offers built-in caching capabilities that can further reduce latency and load on backend services for specific types of requests.

### 5.1. Selected API Gateway Caching Solution

*   **Technology:** Amazon API Gateway built-in caching.
*   **Rationale for Use:**
    *   **Reduce Backend Load:** Serves frequently accessed, cacheable responses directly from the gateway, reducing the number of requests hitting backend services (e.g., product catalog APIs, configuration endpoints).
    *   **Improve Latency:** Responses served from the API Gateway cache have lower latency than those requiring a round trip to backend services.
    *   **Cost Savings:** Can potentially reduce costs associated with backend compute resources and data transfer out from services.
    *   **Ease of Configuration:** Integrated directly into API Gateway, making it relatively simple to enable and configure for specific API stages, routes, or methods.

### 5.2. Key Configuration and Usage Considerations

*   **Cache Provisioning:** Caching is enabled per stage in Amazon API Gateway. When enabled, a dedicated cache instance is provisioned.
*   **Cache Capacity:** Choose an appropriate cache instance size (e.g., 0.5 GB up to 237 GB) based on the expected volume of cacheable data and request rate. Start with a smaller size and monitor cache hit rate and evictions to adjust.
*   **Cache TTL (Time-To-Live):** Define a default TTL for cached responses at the stage or method level. This determines how long a response remains in the cache before being considered stale. The TTL should be appropriate for the data's rate of change (e.g., short TTLs for rapidly changing data, longer for relatively static data).
*   **Cache Key Configuration:**
    *   By default, the cache key includes the request path and query string parameters. Customize cache keys by including specific HTTP headers (e.g., `Accept-Language` for localized responses) or authorizer principal ID (for user-specific cached data, if appropriate and secure).
    *   Carefully select cache key parameters to ensure appropriate cache granularity and avoid overly broad or narrow caching.
*   **Suitable Use Cases:**
    *   Primarily for `GET` requests that return non-personalized or publicly cacheable data.
    *   Endpoints serving configuration data, lists of items (e.g., product categories), or read-only resource representations.
    *   Not suitable for `POST`, `PUT`, `DELETE`, or `PATCH` requests, or for responses containing highly sensitive or frequently changing personalized data.
*   **Encryption:** API Gateway cache data can be encrypted at rest.
*   **Cache Invalidation:**
    *   **TTL Expiration:** The primary mechanism for data freshness.
    *   **Explicit Invalidation:** API Gateway provides mechanisms to invalidate cache entries (e.g., for the entire stage, or by specific cache key paths). This can be triggered programmatically (via AWS SDK/CLI) after data updates in backend services. Requires careful coordination.
    *   Consider using a combination of TTL and targeted invalidation for optimal freshness and performance.
*   **Security Considerations:**
    *   **Do Not Cache Sensitive Data:** Avoid caching responses containing personally identifiable information (PII) or other sensitive data unless explicitly required and secured (e.g., caching per user with authorizer principal ID in cache key, and short TTLs).
    *   Ensure that caching behavior does not inadvertently leak data between users if cache keys are not configured correctly for personalized content.
*   **Monitoring:**
    *   Monitor API Gateway cache metrics in CloudWatch (e.g., `CacheHitCount`, `CacheMissCount`, `Latency`).
    *   Use these metrics to optimize cache size, TTL, and identify if caching is effective.

### 5.3. When to Prefer API Gateway Cache vs. Distributed Cache (Redis)

*   **API Gateway Cache:** Best for caching full HTTP responses for public or semi-public data at the edge of your API layer. Simpler for response caching directly tied to API endpoints.
*   **Distributed Cache (ElastiCache for Redis):** More versatile. Use for:
    *   Caching granular data objects or query results shared across multiple services or application instances.
    *   Session management.
    *   Rate limiting counters.
    *   Leaderboards, real-time data.
    *   Situations requiring more complex data structures or operations than simple key-value response caching.

Often, both can be used complementarily in a multi-layered caching strategy.

## 6. In-Memory Cache (Service-Level) Implementation Details

Service-level in-memory caching refers to caching data directly within the memory space of an individual service instance. This is the fastest caching layer available but is local to each instance and has limited capacity.

### 6.1. Purpose and Use Cases

*   **Ultra-Low Latency Access:** For extremely hot data that needs to be accessed with minimal overhead (e.g., frequently checked feature flags, routing information, pre-computed instance-specific data).
*   **Reducing External Calls for Highly Repetitive Data:** Caching results from frequent, identical calls to external services or databases for a very short period, where the data is specific to the context of the current instance's operations.
*   **Temporary Storage of Session-Local Data:** If a service instance handles multiple related requests from a single user sequentially, it might cache intermediate results in memory for that short interaction.

### 6.2. Key Considerations and Best Practices

*   **Cache Scope & Lifetime:** Data stored in an in-memory cache is local to a single service instance. It is lost if the instance restarts. This makes it unsuitable for shared state or durable data.
*   **Cache Size Management:**
    *   In-memory caches consume the service's heap memory. Keep cache sizes small and well-defined to prevent OutOfMemoryErrors.
    *   Implement strategies to limit cache size (e.g., maximum number of entries, maximum total size).
*   **Eviction Policies:** Implement appropriate eviction policies (e.g., LRU - Least Recently Used, LFU - Least Frequently Used, TTL/TTI - Time To Live/Idle) to ensure stale data is removed and the cache doesn't grow indefinitely.
*   **Data Consistency:**
    *   In-memory caches can lead to data inconsistencies across different instances of the same service if the underlying data changes. This layer is best for data that is immutable, instance-specific, or where eventual consistency is acceptable.
    *   If strong consistency is required for shared data, a distributed cache (Redis) is the appropriate choice.
*   **Concurrency:** If multiple threads within a service instance access the cache, ensure the cache implementation is thread-safe.
*   **Cache Invalidation:** Have a strategy for invalidating or refreshing cached data if the source data changes. This can be challenging for in-memory caches across distributed instances, reinforcing their use for instance-local or very short-lived data.

### 6.3. Technology Choices (Language/Framework Dependent)

Specific implementations of in-memory caches depend on the programming language and framework used by the service:

*   **Node.js (NestJS):**
    *   Simple JavaScript objects or Maps can be used for basic caching with manual TTL management.
    *   Libraries like `node-cache`, `memory-cache`, or NestJS's built-in `CacheModule` (which can use an in-memory provider) offer more features like automatic eviction and TTL.
*   **Java (Spring Boot):**
    *   Spring Framework's caching abstraction with `ConcurrentHashMap` as a provider.
    *   Libraries like Google Guava Cache, Ehcache, or Caffeine (a high-performance Java 8 caching library).
*   **Python (Django/Flask):**
    *   Built-in dictionary objects for simple cases.
    *   Libraries like `cachetools` or framework-specific caching mechanisms (e.g., Django's cache framework with a local memory backend).
*   **Go:**
    *   Standard library maps with mutexes for thread safety, or more advanced libraries like `go-cache` or `Ristretto`.

### 6.4. When Not to Use In-Memory Caching

*   For data that needs to be shared across multiple service instances or different services (use Redis).
*   For large datasets that would consume too much memory per instance.
*   When strong consistency of cached data across all instances is critical.
*   As a replacement for proper database optimization or a distributed cache.

In-memory caching is a tactical optimization for specific hot paths within a service instance and should be used judiciously as part of the broader multi-layered caching strategy.

## 7. Database Caching
{{ ... }}
