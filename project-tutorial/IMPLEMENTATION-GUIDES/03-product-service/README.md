# Product Service Tutorial - Complete Learning Guide

## 🎯 What You'll Build

Build a **production-ready Product Service** that evolves from simple to optimized:

- **📦 Product Catalog Management** - Products, categories, variants, and pricing
- **🔍 Search Integration** - Amazon OpenSearch for fast product discovery
- **📡 Event-Driven Communication** - Publish events for other services
- **🔐 Authentication Integration** - Use shared auth library from User Service
- **📊 Inventory Coordination** - Integrate with inventory management
- **🛡️ Role-Based Access** - Admin operations with proper permissions
- **🔄 Database Evolution** - **NEW!** Learn when and how to migrate from PostgreSQL to MongoDB

## 🎓 Learning Philosophy

This tutorial follows our **[Polyglot Persistence Strategy](../../architecture/polyglot-persistence-strategy.md)**:

**📚 Phase 1 (Tutorials 1-7)**: Start with PostgreSQL for learning simplicity  
**🔄 Phase 2 (Tutorial 8b)**: Experience pain points and migrate to MongoDB  
**🚀 Phase 3 (Tutorials 9-12)**: Production optimization and deployment

**Why This Approach?**
- ✅ **Learn fundamentals first** - Master service patterns without database complexity
- ✅ **Experience real pain points** - Understand WHY database choices matter
- ✅ **Strategic evolution** - See how production systems actually evolve
- ✅ **Practical decisions** - Learn decision-making, not just technology

## 📚 Prerequisites

**Required Foundations:**
- ✅ **[Infrastructure Setup](../01-infrastructure-setup/)** - LocalStack and CDK deployed
- ✅ **[User Service](../02-user-service/)** - Authentication system working
- ✅ **Shared Libraries** - Auth and event libraries (tutorials 16-18)

## 🎓 Learning Path

### **Phase 1: Foundation Setup (Tutorials 01-04)**
1. **[Project Setup](./01-project-setup.md)** - Create NestJS product service
2. **[Database Models](./02-database-models.md)** - Product, Category, Price entities ⚠️ *Note rigid schemas*
3. **[Core Services](./03-core-services.md)** - Business logic implementation
4. **[Authentication Integration](./04-auth-integration.md)** - Use shared auth library

### **Phase 2: API & Features (Tutorials 05-08)**
5. **[REST API Implementation](./05-api-implementation.md)** - Complete CRUD operations ⚠️ *Experience query complexity*
6. **[Event Publishing](./06-event-publishing.md)** - ProductCreated, ProductUpdated events
7. **[Search Integration](./07-search-integration.md)** - Amazon OpenSearch setup ⚠️ *Feel dual-database pain*
8. **[Testing Strategy](./08-testing.md)** - Unit and integration tests
8b. **[Database Migration Strategy](./08b-database-migration.md)** - **NEW!** PostgreSQL → MongoDB evolution 🔄

### **Phase 3: Production Ready (Tutorials 09-12)**
9. **[Service Integration](./09-service-integration.md)** - Connect with other services
10. **[Performance Optimization](./10-performance.md)** - Caching and optimization
11. **[Monitoring & Logging](./11-monitoring.md)** - CloudWatch integration
12. **[Production Deployment](./12-deployment.md)** - AWS production setup

## 🛠️ Technology Stack

### Phase 1 (Learning)
- **NestJS + TypeScript** - Core framework
- **PostgreSQL + TypeORM** - Database layer (start simple)
- **Amazon OpenSearch** - Product search (dual-database complexity)
- **RabbitMQ** - Event messaging
- **Shared Auth Library** - JWT validation

### Phase 2 (Evolution)
- **MongoDB + Mongoose** - Document database (after migration)
- **Consolidated Search** - MongoDB text indexes (simplified architecture)
- **Same NestJS/TypeScript** - Framework consistency maintained

## 📖 Getting Started

**Begin with [01-project-setup.md](./01-project-setup.md)** and follow the tutorials in sequence!