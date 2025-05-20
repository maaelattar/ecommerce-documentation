# Containerization Standards

## 1. Introduction

This document defines the containerization standards for the e-commerce platform. Standardizing our containerization approach ensures consistency, security, and operational efficiency across all microservices. These standards align with our AWS-centric architecture decisions and cloud-native deployment strategy.

## 2. Docker Image Standards

### 2.1. Base Images

| Service Type     | Base Image                 | Version              |
| ---------------- | -------------------------- | -------------------- |
| Node.js Services | node:20-alpine             | Latest patch version |
| Java Services    | amazoncorretto:17-alpine   | Latest patch version |
| Python Services  | python:3.11-slim           | Latest patch version |
| Go Services      | golang:1.21-alpine (build) | Latest patch version |
| Go Services      | alpine:3.18 (runtime)      | Latest patch version |

#### 2.1.1. Base Image Guidelines

- **Prefer Alpine-based** images for reduced size and attack surface
- **Pin exact versions** (e.g., `node:20.10.0-alpine3.18`) in production Dockerfiles
- **Use official images** from verified publishers
- **Scan all base images** for vulnerabilities before use
- **Update base images** regularly to incorporate security patches

### 2.2. Multi-Stage Builds

All service Dockerfiles must use multi-stage builds to minimize final image size:

```dockerfile
# Example for Node.js service
FROM node:20.10.0-alpine3.18 AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20.10.0-alpine3.18
WORKDIR /app
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/node_modules /app/node_modules
COPY package*.json ./

USER node
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### 2.3. Image Naming and Tagging

- **Repository Format**: `${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${SERVICE_NAME}`
- **Required Tags**:
  - Git SHA: `${REPO}:${COMMIT_HASH}`
  - Semantic Version: `${REPO}:${SEMVER}` (for releases)
  - Environment: `${REPO}:${ENV}-${COMMIT_HASH}`
  - Latest: `${REPO}:latest` (points to the most recent stable build)

### 2.4. Image Optimization

- **Target Size**: < 200MB for Node.js services, < 300MB for Java services
- **Layer Optimization**:
  - Order Dockerfile instructions from least to most frequently changing
  - Combine RUN commands with `&&` to reduce layers
  - Use `.dockerignore` to exclude unnecessary files
- **Caching**:
  - Dependencies installation separate from code copying
  - Development tools excluded from production images

## 3. Security Requirements

### 3.1. Non-Root User

All containers must run as non-root users:

```dockerfile
# Create a non-root user with specific UID/GID
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /bin/sh -D appuser

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser
```

### 3.2. Image Scanning

- **Pre-build Scanning**: Base images scanned before build
- **Post-build Scanning**: Complete images scanned in ECR
- **Blocking Issues**:
  - Critical vulnerabilities block promotion to production
  - High vulnerabilities require exception approval
  - Medium/low vulnerabilities tracked and remediated in scheduled updates

### 3.3. Secret Management

- **No Secrets in Images**:
  - No hardcoded secrets in Dockerfiles
  - No secrets in environment variables baked into images
- **Runtime Secret Injection**:
  - AWS Secrets Manager for sensitive data
  - External Secrets Operator for Kubernetes
  - Environment variables injected at runtime

### 3.4. Read-Only File System

Production containers should use read-only file systems where possible:

```yaml
# Kubernetes example
securityContext:
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

With volume mounts for required writeable directories:

```yaml
volumeMounts:
  - name: tmp-volume
    mountPath: /tmp
  - name: cache-volume
    mountPath: /app/cache
```

## 4. Resource Management

### 4.1. Resource Limits

All containers must specify both requests and limits:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 4.2. Resource Guidelines

| Service Type      | CPU Request | CPU Limit   | Memory Request | Memory Limit |
| ----------------- | ----------- | ----------- | -------------- | ------------ |
| API Services      | 100m-250m   | 500m-1000m  | 256Mi-512Mi    | 512Mi-1Gi    |
| Worker Services   | 100m-500m   | 500m-2000m  | 256Mi-1Gi      | 512Mi-2Gi    |
| Database Services | 500m-1000m  | 1000m-4000m | 1Gi-4Gi        | 2Gi-8Gi      |
| Cache Services    | 100m-250m   | 250m-500m   | 512Mi-2Gi      | 1Gi-4Gi      |

### 4.3. Graceful Shutdown

All services must implement graceful shutdown to handle SIGTERM signals:

```javascript
// Example for Node.js
process.on("SIGTERM", async () => {
  console.log("Received SIGTERM signal. Shutting down gracefully...");

  // Close server connections
  await new Promise((resolve) => server.close(resolve));

  // Close database connections
  await db.disconnect();

  console.log("Graceful shutdown completed.");
  process.exit(0);
});
```

## 5. Health Checks and Observability

### 5.1. Health Endpoints

All services must implement the following endpoints:

- **Liveness**: `/health/live` - Basic server health
- **Readiness**: `/health/ready` - Service ready to handle requests
- **Startup**: `/health/startup` - Initial service startup completed

Example health check configuration:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 3000
  initialDelaySeconds: 30
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /health/ready
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 2
startupProbe:
  httpGet:
    path: /health/startup
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 12 # Allow 60s for startup
```

### 5.2. Logging Standards

All containers must output logs to stdout/stderr in JSON format:

```json
{
  "timestamp": "2023-11-21T12:34:56.789Z",
  "level": "info",
  "service": "product-service",
  "environment": "production",
  "requestId": "abcd1234",
  "message": "Request processed successfully",
  "context": {
    "path": "/products/123",
    "method": "GET",
    "duration": 45,
    "userId": "user-789"
  }
}
```

### 5.3. Metrics Exposure

All services must expose Prometheus metrics on `/metrics` endpoint:

- **Standard Metrics**:
  - Request count, latency, error rates
  - CPU/memory usage
  - Connection pool stats
  - Queue depths
- **Custom Business Metrics**:
  - Transaction counts
  - Business operation success/failure
  - Domain-specific counters

## 6. Configuration Management

### 6.1. Environment Variables

- **Required Env Vars**:
  - `NODE_ENV` or equivalent for runtime environment
  - `LOG_LEVEL` for logging verbosity
  - `SERVICE_PORT` for application port
- **Configuration Structure**:
  - Group related configs (e.g., `DB_HOST`, `DB_PORT`, `DB_NAME`)
  - Use prefixes for service integration (`PAYMENT_API_URL`, `INVENTORY_API_URL`)

### 6.2. Configuration Loading

Services should load configuration in this priority order:

1. Environment variables (highest priority)
2. Config files in ConfigMaps
3. Default values in code (lowest priority)

Example configuration loading:

```javascript
// Node.js example
const config = {
  port: parseInt(process.env.SERVICE_PORT || "3000", 10),
  database: {
    host: process.env.DB_HOST || "localhost",
    port: parseInt(process.env.DB_PORT || "5432", 10),
    name: process.env.DB_NAME || "ecommerce",
    username: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
  },
  logging: {
    level: process.env.LOG_LEVEL || "info",
  },
};
```

### 6.3. Secrets Management

- **AWS Secrets Manager** for sensitive configuration
- **External Secrets Operator** for Kubernetes integration
- **Secret Mounting**:
  - Mount as environment variables or files
  - Rotate without container restart when possible

## 7. Container Lifecycle Management

### 7.1. Init Containers

Use init containers for setup tasks:

```yaml
initContainers:
  - name: wait-for-db
    image: busybox:1.36
    command:
      [
        "sh",
        "-c",
        "until nc -z -w5 postgres-svc 5432; do echo waiting for database; sleep 2; done;",
      ]
  - name: migrations
    image: ${ECR_REPO}/product-service:${TAG}
    command: ["npm", "run", "migrations"]
    env:
      - name: DB_HOST
        value: postgres-svc
```

### 7.2. Sidecar Containers

Use sidecars for auxiliary functionality:

- **Log Forwarding**: Fluent Bit sidecar
- **Metrics Collection**: Prometheus exporter sidecar
- **Service Mesh**: Envoy proxy sidecar for AWS App Mesh

### 7.3. Container Lifecycle Hooks

Implement `postStart` and `preStop` hooks:

```yaml
lifecycle:
  postStart:
    exec:
      command: ["/bin/sh", "-c", "echo Container started > /proc/1/fd/1"]
  preStop:
    exec:
      command:
        [
          "/bin/sh",
          "-c",
          "sleep 10 && echo Graceful shutdown initiated > /proc/1/fd/1",
        ]
```

## 8. Testing and Validation

### 8.1. Local Testing

- **Docker Compose** for local service integration testing
- **Tilt** for local Kubernetes development

Example Docker Compose configuration:

```yaml
version: "3.8"
services:
  product-service:
    build:
      context: ./product-service
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DB_HOST=postgres
    depends_on:
      - postgres
      - rabbitmq

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=ecommerce
    volumes:
      - postgres-data:/var/lib/postgresql/data

  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"

volumes:
  postgres-data:
```

### 8.2. Automated Testing

- **Container Structure Tests**: Validate image structure
- **Vulnerability Scanning**: Scan for security issues
- **Integration Testing**: Test container interactions

Example container structure test:

```yaml
schemaVersion: "2.0.0"
commandTests:
  - name: "Node.js Version"
    command: "node"
    args: ["--version"]
    expectedOutput: ["v20"]
  - name: "Non-Root User"
    command: "whoami"
    expectedOutput: ["appuser"]
fileExistenceTests:
  - name: "App Files"
    path: "/app/dist/main.js"
    shouldExist: true
  - name: "No Source Files"
    path: "/app/src"
    shouldExist: false
metadataTest:
  exposedPorts: ["3000"]
  user: "appuser"
```

## 9. Container Development Workflow

### 9.1. Local Development

1. **Code Changes**:

   - Make code changes in local environment
   - Run unit tests
   - Build local Docker image

2. **Local Testing**:

   ```bash
   # Build image
   docker build -t product-service:dev .

   # Run container
   docker run -p 3000:3000 --env-file .env.dev product-service:dev

   # Or with Docker Compose
   docker-compose up
   ```

3. **Kubernetes Development**:

   ```bash
   # Start local Kubernetes dev environment
   tilt up

   # View logs
   tilt logs product-service
   ```

### 9.2. CI Pipeline Integration

1. **PR Creation**:

   - Automated container build
   - Container structure tests
   - Security scanning

2. **Merge to Develop**:
   - Build production-ready image
   - Push to ECR with appropriate tags
   - Deploy to development environment

### 9.3. Telepresence Integration

For testing local code against remote containers:

```bash
# Connect to remote cluster
telepresence connect

# Intercept service traffic
telepresence intercept product-service --port 3000:80

# Run service locally
npm run start:dev

# When done
telepresence leave product-service
```

## 10. Documentation Requirements

### 10.1. Container Documentation

Each containerized service must include:

- **README.md**: General service description
- **CONTAINER.md**: Container-specific documentation
- **Dockerfile**: Well-commented Dockerfile
- **docker-compose.yml**: Local development setup

### 10.2. Required Documentation Sections

CONTAINER.md must include:

- **Build Instructions**: How to build the container
- **Run Instructions**: How to run locally
- **Configuration**: Available environment variables
- **Endpoints**: API endpoints and health checks
- **Resource Requirements**: CPU/memory recommendations
- **Dependencies**: External service dependencies
- **Maintenance**: Update procedures and considerations

## 11. References

- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [AWS Container Security Best Practices](https://docs.aws.amazon.com/AmazonECR/latest/userguide/security-best-practices.html)
- [OpenTelemetry Instrumentation](https://opentelemetry.io/docs/instrumentation/)
- [Prometheus Metrics Guidelines](https://prometheus.io/docs/practices/naming/)
- [Tilt Documentation](https://docs.tilt.dev/)
- [Telepresence Documentation](https://www.telepresence.io/docs/)
- [ADR-003-nodejs-nestjs-for-initial-services](../../architecture/adr/ADR-003-nodejs-nestjs-for-initial-services.md)
- [ADR-006-cloud-native-deployment-strategy](../../architecture/adr/ADR-006-cloud-native-deployment-strategy.md)
