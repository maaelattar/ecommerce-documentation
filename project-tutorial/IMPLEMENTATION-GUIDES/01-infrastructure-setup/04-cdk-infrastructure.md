# CDK Infrastructure Deployment

## 🎯 Objective

Deploy the complete ecommerce infrastructure using AWS CDK.

## 📚 What We're Deploying

### Phase 1: Simple & Consistent (Current)
Our CDK creates:
- **7 PostgreSQL databases** (one per microservice) - Learning simplicity
- **Redis cache** (ElastiCache) - Session storage
- **RabbitMQ** (Amazon MQ) - Event messaging
- **S3 buckets** - File storage
- **VPC & Security Groups** - Network isolation

### Phase 2: Production-Optimized (Future)
Following our [Polyglot Persistence Strategy](../../architecture/polyglot-persistence-strategy.md), we'll evolve to:
- **PostgreSQL** - User, Order, Payment services (financial integrity)
- **MongoDB** - Product, Notification services (flexible schemas) 
- **DynamoDB** - Inventory service (high throughput)
- **OpenSearch** - Search service (full-text search)
- **Redis, RabbitMQ, S3** - Unchanged (already optimal)

## 🔧 Deploy Infrastructure

### 1. Setup CDK
```bash
cd ecommerce-repos-polyrepo/ecommerce-infrastructure/aws
pnpm install
```

### 2. Bootstrap & Deploy
```bash
# Bootstrap CDK for LocalStack
cdklocal bootstrap

# Deploy all infrastructure stacks
cdklocal deploy --all --require-approval never
```

This deploys:
- **EcommerceNetworkStack** - VPC, subnets, security groups
- **EcommerceDatabaseStack** - PostgreSQL instances  
- **EcommerceCacheStack** - Redis cache
- **EcommerceMessagingStack** - RabbitMQ
- **EcommerceStorageStack** - S3 buckets

### 3. Verify Deployment
```bash
# Check deployed resources
awslocal rds describe-db-instances
awslocal s3 ls
awslocal secretsmanager list-secrets
```

## 🎓 Understanding Your Choices

You now have a working infrastructure with PostgreSQL for all services. This is **intentionally simple** for learning. As you build services, you'll discover when specialized databases provide real benefits.

Next, learn how we'll evolve this: **[04b-database-migration-strategy.md](./04b-database-migration-strategy.md)**

## ✅ Then Continue

Infrastructure ready? Continue to **[05-service-integration.md](./05-service-integration.md)**