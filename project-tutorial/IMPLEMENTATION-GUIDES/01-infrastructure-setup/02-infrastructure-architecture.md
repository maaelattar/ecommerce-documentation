# Infrastructure Architecture Deep Dive

## 🎯 Objective

Understand what was actually built in the `ecommerce-infrastructure` repository and how the CDK architecture works.

## 🏗️ Repository Structure

```
ecommerce-infrastructure/aws/
├── lib/
│   ├── ecommerce-infrastructure.ts      # Main orchestrator stack
│   ├── constructs/                      # Reusable infrastructure components
│   │   ├── data/                       # Database & cache constructs
│   │   ├── messaging/                  # Message broker constructs
│   │   ├── networking/                 # VPC & security constructs
│   │   ├── storage/                    # S3 & storage constructs
│   │   └── search/                     # ElasticSearch constructs
│   └── providers/                      # Environment-specific providers
├── config/                             # Environment configurations
├── bin/                                # CDK app entry point
└── scripts/                            # Deployment scripts
```

## 🧩 Architecture Patterns Used

### 1. **Composition Pattern**

Instead of one massive CDK stack, we use **construct composition**:

````typescript
// Main orchestrator - composes smaller constructs
export class EcommerceInfrastructure extends Stack {
  public readonly vpc: VpcConstruct;
  public readonly database: DatabaseConstruct;
  public readonly cache: CacheConstruct;
  public readonly messaging: AmazonMQConstruct;

  constructor(scope: Construct, id: string, props: EcommerceInfrastructureProps) {
    super(scope, id, props);

    // Each construct handles its own domain
    this.vpc = new VpcConstruct(this, 'Network', { provider });
    this.database = new DatabaseConstruct(this, 'Database', { ... });
    this.cache = new CacheConstruct(this, 'Cache', { ... });
    this.messaging = new AmazonMQConstruct(this, 'Messaging', { ... });
  }
}
```**Why This Matters:**
- ✅ **Separation of Concerns** - Each construct handles one responsibility
- ✅ **Reusability** - Constructs can be reused across projects
- ✅ **Testability** - Each construct can be tested independently
- ✅ **Maintainability** - Easy to modify one piece without affecting others

### 2. **Strategy Pattern for Environments**
Different deployment targets (LocalStack vs AWS) handled cleanly:

```typescript
// Environment provider factory
export class EnvironmentProviderFactory {
  static create(config: EnvironmentConfig): EnvironmentProvider {
    switch (config.environment) {
      case 'local':
        return new LocalStackProvider(config);
      case 'production':
        return new AWSProvider(config);
      default:
        throw new Error(`Unsupported environment: ${config.environment}`);
    }
  }
}
````

**Benefits:**

- ✅ **Same code** deploys to different environments
- ✅ **Environment-specific optimizations** (LocalStack vs AWS)
- ✅ **Easy to add new environments** (staging, development, etc.)

## 🗄️ What Each Construct Does

### VpcConstruct (`constructs/networking/`)

Creates the network foundation:

````typescript
// Creates isolated network with proper subnets
export class VpcConstruct extends Construct {
  public readonly vpc: ec2.Vpc;
  public readonly securityGroups: Map<string, ec2.SecurityGroup>;

  constructor(scope: Construct, id: string, props: VpcConstructProps) {
    super(scope, id);

    // Creates VPC with multiple availability zones
    this.vpc = new ec2.Vpc(this, 'EcommerceVPC', {
      maxAzs: 3,
      subnetConfiguration: [
        { name: 'Public', subnetType: ec2.SubnetType.PUBLIC },
        { name: 'Private', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
        { name: 'Database', subnetType: ec2.SubnetType.PRIVATE_ISOLATED }
      ]
    });
  }
}
```### DatabaseConstruct (`constructs/data/`)
Creates PostgreSQL databases for each microservice:

```typescript
export class DatabaseConstruct extends Construct {
  constructor(scope: Construct, id: string, props: DatabaseConstructProps) {
    super(scope, id);

    // Creates 7 PostgreSQL databases (one per microservice)
    // NOTE: This is our Phase 1 approach - PostgreSQL everywhere for learning simplicity
    // Phase 2 will migrate specific services to optimal databases per our polyglot strategy
    const databases = [
      'userservice',        // Will stay PostgreSQL (ACID, security)
      'productservice',     // Will migrate to MongoDB (flexible schema)
      'orderservice',       // Will stay PostgreSQL (transactions)
      'paymentservice',     // Will stay PostgreSQL (compliance)
      'notificationservice', // Will migrate to MongoDB (flexible templates)
      'searchservice',      // Will migrate to OpenSearch (full-text search)
      'inventoryservice'    // Will migrate to DynamoDB (high throughput)
    ];

    databases.forEach(dbName => {
      this.createDatabase(dbName, props);
    });
  }

  private createDatabase(name: string, props: DatabaseConstructProps) {
    return new rds.DatabaseInstance(this, `${name}DB`, {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_15_3
      }),
      instanceType: props.provider.getDatabaseInstanceType(),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      databaseName: name,
      credentials: rds.Credentials.fromGeneratedSecret('postgres'),
      securityGroups: [props.securityGroup]
    });
  }
}
````

### CacheConstruct (`constructs/data/`)

Creates Redis cache for session storage and caching:

````typescript
export class CacheConstruct extends Construct {
  constructor(scope: Construct, id: string, props: CacheConstructProps) {
    super(scope, id);

    // ElastiCache Redis cluster
    new elasticache.CfnCacheCluster(this, 'RedisCache', {
      cacheNodeType: props.provider.getCacheNodeType(),
      engine: 'redis',
      numCacheNodes: 1,
      vpcSecurityGroupIds: [props.securityGroup.securityGroupId]
    });
  }
}
```### AmazonMQConstruct (`constructs/messaging/`)
Creates RabbitMQ message broker for service communication:

```typescript
export class AmazonMQConstruct extends Construct {
  constructor(scope: Construct, id: string, props: AmazonMQConstructProps) {
    super(scope, id);

    // Amazon MQ RabbitMQ broker
    new amazonmq.CfnBroker(this, 'RabbitMQBroker', {
      brokerName: 'ecommerce-rabbitmq',
      engineType: 'RABBITMQ',
      engineVersion: '3.9.16',
      hostInstanceType: props.provider.getMQInstanceType(),
      publiclyAccessible: false,
      securityGroups: [props.securityGroup.securityGroupId],
      subnetIds: props.vpc.privateSubnets.map(subnet => subnet.subnetId)
    });
  }
}
````

## 🔧 Environment Providers

### LocalStackProvider

Optimizes for local development:

```typescript
export class LocalStackProvider implements EnvironmentProvider {
  getDatabaseInstanceType(): ec2.InstanceType {
    return ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO);
  }

  getCacheNodeType(): string {
    return "cache.t3.micro";
  }

  getMQInstanceType(): string {
    return "mq.t3.micro";
  }
}
```

### AWSProvider

Optimizes for production AWS:

````typescript
export class AWSProvider implements EnvironmentProvider {
  getDatabaseInstanceType(): ec2.InstanceType {
    return ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM);
  }

  getCacheNodeType(): string {
    return 'cache.t3.medium';
  }

  getMQInstanceType(): string {
    return 'mq.t3.medium';
  }
}
```## 🎯 Key Benefits of This Architecture

### 1. **Environment Consistency**
- Same infrastructure code works for LocalStack AND AWS
- No environment-specific configuration drift
- Easy to test infrastructure changes locally

### 2. **Microservice Ready**
- Each service gets its own isolated database
- Shared infrastructure (VPC, messaging) connects services
- Proper security boundaries between services

### 3. **Production Ready**
- Multi-AZ deployment for high availability
- Private subnets for security
- Encrypted databases and secure secrets management

### 4. **Developer Friendly**
- Fast local development with LocalStack
- Infrastructure as Code - version controlled
- Easy to recreate environments

## 🔗 How Services Connect

````

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ User Service │ │ Product Service │ │ Order Service │
│ │ │ │ │ │
│ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │
│ │ PostgreSQL │ │ │ │ PostgreSQL │ │ │ │ PostgreSQL │ │
│ │ Database │ │ │ │ Database │ │ │ │ Database │ │
│ └─────────────┘ │ │ └─────────────┘ │ │ └─────────────┘ │
└─────────┬───────┘ └─────────┬───────┘ └─────────┬───────┘
│ │ │
└──────────────────────┼──────────────────────┘
│
┌─────────────────┐
│ RabbitMQ │
│ Message │
│ Broker │
└─────────────────┘
│
┌───────────────┐
│ Redis Cache │
│ (Sessions) │
└───────────────┘

```

## ✅ Next Step

Understanding the architecture? Let's deploy it! Continue to **[03-cdk-infrastructure.md](./03-cdk-infrastructure.md)**
```
