# 10. Deployment & Production Operations

## Overview

Deploy the Payment Service to production with security best practices, PCI compliance considerations, and operational excellence patterns for financial services.

## 🎯 Learning Objectives

- Containerize with security best practices
- Deploy to AWS with PCI considerations
- Configure production monitoring
- Set up backup and disaster recovery
- Implement blue-green deployment

---

## Step 1: Docker Configuration

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

FROM node:18-alpine AS runtime

# Security: Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nestjs -u 1001

# Security: Install security updates
RUN apk update && apk upgrade && apk add --no-cache dumb-init

WORKDIR /app

# Copy application files
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=nestjs:nodejs . .

# Security: Remove unnecessary packages
RUN apk del apk-tools

# Security: Set proper permissions
RUN chmod -R 755 /app

USER nestjs

EXPOSE 3005

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main"]
```

### 1.2 Docker Compose for Local Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  payment-service:
    build: .
    ports:
      - "3005:3005"
    environment:
      - NODE_ENV=development
      - DATABASE_HOST=postgres
      - REDIS_HOST=redis
      - RABBITMQ_URL=amqp://rabbitmq:5672
    depends_on:
      - postgres
      - redis
      - rabbitmq
    volumes:
      - ./src:/app/src
    networks:
      - payment-network

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: payment_service
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - payment-network

  redis:
    image: redis:7-alpine
    networks:
      - payment-network

  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: password
    ports:
      - "15672:15672"
    networks:
      - payment-network

volumes:
  postgres_data:

networks:
  payment-network:
    driver: bridge
```