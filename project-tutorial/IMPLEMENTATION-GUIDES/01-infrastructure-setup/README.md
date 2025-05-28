# Infrastructure Setup Tutorial

## 🎯 What You'll Build

In this tutorial, you'll set up the complete development infrastructure for our ecommerce platform:

- **LocalStack** - Local AWS cloud simulation
- **CDK Infrastructure** - Multi-database polyglot persistence setup
- **Development Environment** - Docker, AWS CLI, monitoring tools  
- **Quality Standards** - Following our infrastructure standards

## 📚 Before We Start: Review the Specs

Let's understand what we're building by reviewing our infrastructure specifications:

- **[Infrastructure Specs](../../implementation-specs/infrastructure/)** - Complete infrastructure requirements
- **[Polyglot Persistence Strategy](../../architecture/polyglot-persistence-strategy.md)** - **NEW!** Database selection strategy
- **[Local Development ADR](../../architecture/adr/ADR-046-local-development-environment-orchestration.md)** - Architecture decisions
- **[Existing CDK Code](../../../ecommerce-infrastructure/aws/)** - Current implementation

## 🔍 Critical Review: Infrastructure Evolution

### Phase 1: Learning-First Approach (Current)
Our current infrastructure uses:
✅ **LocalStack** for local AWS simulation  
✅ **CDK** for Infrastructure as Code  
✅ **PostgreSQL for ALL services** (simplicity for learning)  
✅ **RabbitMQ** for event messaging  
✅ **Redis** for caching  

### Phase 2: Production-Optimized Approach (What You'll Build Towards)
Based on our [Polyglot Persistence Strategy](../../architecture/polyglot-persistence-strategy.md):

| Service | Database Choice | Why | Migration Priority |
|---------|-----------------|-----|-------------------|
| **User Service** | PostgreSQL | ACID, Security, Relationships | ✅ Already optimal |
| **Product Service** | MongoDB | Flexible Schema, Complex Attributes | 🚀 High value |
| **Order Service** | PostgreSQL | Transactions, Financial Integrity | ✅ Already optimal |
| **Payment Service** | PostgreSQL | Compliance, Audit, ACID | ✅ Already optimal |
| **Inventory Service** | DynamoDB | High Throughput, Simple K-V | 🚀 High performance gain || **Notification Service** | MongoDB | Flexible Templates, Event Logs | 🛠️ Developer productivity |
| **Search Service** | OpenSearch | Full-text Search, Analytics | 🔄 Already planned |

**Why Start with PostgreSQL Everywhere?**
- ✅ **Single database to learn** - Focus on microservices patterns first
- ✅ **Familiar SQL** - Most developers know PostgreSQL
- ✅ **Consistent tooling** - Same backup, monitoring, deployment patterns
- ✅ **Working system first** - Build something that works, then optimize

**When to Migrate?**
- 📊 **Product Service**: When schema changes every sprint slow you down
- ⚡ **Inventory Service**: When concurrent updates cause lock contention  
- 🎨 **Notification Service**: When JSON queries become unmaintainable

## 🛠️ Prerequisites

Before starting, ensure you have:
- **Docker & Docker Compose** installed
- **Node.js 18+** with npm/pnpm
- **Git** for version control
- **Terminal/Command line** access

## 📖 Tutorial Structure

1. **[Environment Setup](./01-environment-setup.md)** - Install tools and dependencies
2. **[Infrastructure Architecture](./02-infrastructure-architecture.md)** - Deep dive into what was built
3. **[Hands-On Code Walkthrough](./02b-hands-on-code-walkthrough.md)** - **NEW!** Navigate actual files
4. **[LocalStack Configuration](./03-localstack-setup.md)** - Set up local AWS cloud  
5. **[CDK Infrastructure](./04-cdk-infrastructure.md)** - Deploy infrastructure with CDK
6. **[Database Strategy](./04b-database-migration-strategy.md)** - **NEW!** Polyglot persistence planning
7. **[Service Integration](./05-service-integration.md)** - Connect services to infrastructure
8. **[Development Workflow](./06-development-workflow.md)** - Daily development practices
9. **[Troubleshooting](./07-troubleshooting.md)** - Common issues and solutions

## 🚀 Getting Started

Ready to build production-grade infrastructure? Start with **[01-environment-setup.md](./01-environment-setup.md)**

## 🎓 Learning Outcomes

By completing this tutorial, you'll:
- Understand AWS-native development patterns
- Master Infrastructure as Code with CDK
- Set up production-grade local development environment
- Follow enterprise infrastructure standards
- **Learn when and how to evolve from simple to optimized architecture**
- **Understand the real-world consequences of database choices**