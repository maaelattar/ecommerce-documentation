# Service Discovery and Registration for Search Service

## Overview

In a microservices architecture, services need a way to find and communicate with each other without hardcoding IP addresses or hostnames. Service discovery and registration mechanisms allow services like the Search Service to announce their availability and to dynamically discover the network locations of other services they need to interact with (e.g., Kafka brokers, Elasticsearch cluster, Authentication Service).

## Key Concepts

*   **Service Registration**: When an instance of the Search Service starts up, it registers itself with a central service registry, providing its network location (IP address, port) and potentially metadata (e.g., service name, version, health check endpoint).
*   **Service Discovery**: When another service (a client) needs to communicate with the Search Service, it queries the service registry to get a list of healthy, available instances of the Search Service. The client then typically uses client-side load balancing to choose an instance.
*   **Health Checking**: The service registry or the service instances themselves often perform health checks. Unhealthy instances are removed from the pool of available instances to prevent traffic from being routed to them.

## Common Mechanisms in a Microservices Platform

The specific mechanism used will depend on the underlying infrastructure and platform choices (e.g., Kubernetes, Consul, Eureka).

### 1. Kubernetes (K8s) Environment

If the e-commerce platform is deployed on Kubernetes, service discovery is largely handled natively:

*   **Registration**: When a Search Service `Pod` is created and managed by a `Deployment` or `StatefulSet`, Kubernetes automatically assigns it an IP address and manages its lifecycle.
*   **Discovery (DNS-based)**: Kubernetes provides internal DNS resolution. A Search Service `Service` (a K8s `Service` object) is created, which provides a stable DNS name (e.g., `search-service.namespace.svc.cluster.local`) and IP address (ClusterIP). This K8s `Service` load balances requests across the healthy `Pods` of the Search Service (identified by labels).
    *   Clients (other microservices within the cluster) simply connect to this stable DNS name.
    *   For example, an API Gateway or another microservice needing to call the Search Service API would use `http://search-service/v1/search/products` (assuming `search-service` resolves in its namespace or is fully qualified).
*   **Health Checking**: Kubernetes uses readiness and liveness probes defined in the `Pod` specification to determine if an instance of the Search Service is healthy and ready to receive traffic. If probes fail, K8s will stop sending traffic to that pod and may restart it.
    *   The Search Service should expose HTTP endpoints for these probes (e.g., `/health/live`, `/health/ready`).

    **NestJS Health Check Example (using `@nestjs/terminus`):**
    ```typescript
    // src/health/health.controller.ts
    import { Controller, Get } from '@nestjs/common';
    import { HealthCheckService, HttpHealthIndicator, HealthCheck, MemoryHealthIndicator, DiskHealthIndicator } from '@nestjs/terminus';
    import { ElasticsearchService } from '@nestjs/elasticsearch'; // Assuming this is your ES client service
    import { ConfigService } from '@nestjs/config';

    @Controller('health')
    export class HealthController {
      constructor(
        private health: HealthCheckService,
        private http: HttpHealthIndicator, // Example: check external dependency
        private memory: MemoryHealthIndicator,
        private disk: DiskHealthIndicator,
        private esService: ElasticsearchService, // Inject your ES service
        private configService: ConfigService,
      ) {}

      @Get('live') // Liveness probe: basic check if service is running
      @HealthCheck()
      checkLiveness() {
        return this.health.check([
          () => this.memory.checkHeap('memory_heap', 256 * 1024 * 1024), // Heap shouldn't exceed 256MB
        ]);
      }

      @Get('ready') // Readiness probe: checks if service is ready to accept traffic (dependencies are up)
      @HealthCheck()
      async checkReadiness() {
        return this.health.check([
          // Check Elasticsearch connection
          async () => {
            try {
              await this.esService.ping(); // Elasticsearch client ping
              return { elasticsearch: { status: 'up' } };
            } catch (err) {
              return { elasticsearch: { status: 'down', error: err.message } };
            }
          },
          // Check disk space
          () => this.disk.checkStorage('storage', { 
            path: this.configService.get<string>('healthcheck.disk.path', '/'), 
            thresholdPercent: this.configService.get<number>('healthcheck.disk.thresholdPercent', 0.8) 
          }),
          // Check Kafka connection (conceptual - would need a Kafka health indicator)
          // async () => /* your Kafka connection check */,
        ]);
      }
    }
    ```

### 2. Client-Side Discovery with a Service Registry (e.g., Consul, Netflix Eureka)

If not using Kubernetes or if a separate service registry is preferred:

*   **Registration**: The Search Service instance, on startup, makes an API call to the Service Registry (e.g., Consul agent or Eureka server) to register itself. This typically includes its service name, IP, port, and a health check endpoint.
    *   Libraries (e.g., `consul` for Node.js, Spring Cloud Netflix for Spring Boot) simplify this.
*   **Discovery**: Client services query the registry to get a list of healthy instances for `search-service`. The client then uses a load balancing strategy (e.g., round-robin, least connections) to pick an instance.
    *   Libraries often provide client-side load balancers (e.g., Ribbon with Eureka).
*   **Health Checking**: The Search Service instance periodically sends heartbeats to the registry, or the registry polls the service's health check endpoint.

### Search Service Discovering Other Services

The Search Service itself is also a client to other services:

*   **Elasticsearch Cluster**: While often a small, relatively static cluster, its nodes still need to be discovered. Elasticsearch clients can often take multiple seed node addresses.
*   **Kafka Brokers**: Kafka clients require a list of bootstrap broker addresses. In dynamic environments, these might come from a configuration service that itself uses service discovery, or directly from a service registry if brokers are registered.
*   **Authentication Service (IdP)**: The JWKS URI or token introspection endpoint of the identity provider needs to be discoverable or configurable.
*   **Configuration Service (if used)**: If configuration is centralized, the Search Service needs to know how to reach the Configuration Service on startup.

**Configuration Approach for Dependencies:**
Often, the addresses of critical infrastructure like Kafka, Elasticsearch, or the primary IdP are provided via configuration (e.g., environment variables, config files managed by a deployment pipeline or a Config Service) rather than dynamic service discovery for every request. This configuration itself might be populated based on service discovery at a higher level (e.g., by an orchestrator injecting config maps).

## Implementation in Search Service (NestJS)

*   **Health Checks**: Implement liveness and readiness endpoints using `@nestjs/terminus` as shown above.
*   **Kubernetes**: Relies on K8s YAML definitions for `Service`, `Deployment`, and probes.
*   **Consul/Eureka (Conceptual)**:
    ```typescript
    // main.ts or AppModule onModuleInit
    // import Consul = require('consul'); // Example for Consul
    // const consul = new Consul({ host: 'consul-server-address' });
    // const serviceId = `search-service-${uuidv4()}`;
    // await consul.agent.service.register({
    //   name: 'search-service',
    //   id: serviceId,
    //   address: 'my-instance-ip', // Needs to be dynamically obtained
    //   port: 3000,
    //   check: {
    //     http: `http://my-instance-ip:3000/health/ready`,
    //     interval: '10s',
    //     ttl: '15s', // Alternative to HTTP check
    //     deregistercriticalserviceafter: '1m'
    //   }
    // });

    // onApplicationShutdown: await consul.agent.service.deregister({id: serviceId});
    ```
    Actual IP address discovery for registration in non-containerized environments can be tricky. In containers, the container IP is used.

## Conclusion

Service discovery and registration are fundamental for a resilient and scalable microservice architecture. In Kubernetes environments, much of this is handled transparently. For other setups, dedicated tools like Consul or Eureka are common. The Search Service must both be discoverable and able to discover its own dependencies, primarily through health checks and leveraging the platform's chosen service discovery mechanisms.
