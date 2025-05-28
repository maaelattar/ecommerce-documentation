# Service Integration

## 🎯 Objective

Connect services to deployed infrastructure.

## 🔧 Get Infrastructure Details

```bash
# Database connections
awslocal rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,Endpoint.Address]'

# Service endpoints
awslocal elasticache describe-cache-clusters
awslocal s3 ls

# Secrets
awslocal secretsmanager get-secret-value --secret-id ecommerce/database/password
```

## 🔧 Configure Services

Create `.env.local` for each service:
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/service_db
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://localhost:5672
AWS_S3_BUCKET=ecommerce-files-local
AWS_ENDPOINT_URL=http://localhost:4566
```

## ✅ Test Connections

```bash
# Test database & Redis
psql $DATABASE_URL -c "SELECT 1;"
redis-cli ping
```

## 📋 Quality Standards Note

This setup follows our **[Infrastructure Standards](../../architecture/quality-standards/microservice-architecture-standards.md)**:
- ✅ Service isolation with dedicated databases
- ✅ Configuration through environment variables
- ✅ Local development parity with production

## 🎯 Database Evolution Strategy

Currently, all services use PostgreSQL for simplicity. As you build services, you'll identify specific pain points that specialized databases solve better. Our **[Polyglot Persistence Strategy](../../architecture/polyglot-persistence-strategy.md)** shows you exactly when and how to migrate to optimal database choices.

**Key Principle**: Start simple, evolve based on real pain points, not theoretical optimization.

## ✅ Next Step

Continue to **[05-development-workflow.md](./05-development-workflow.md)**