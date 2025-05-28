# Tutorial 15: Production Deployment & Security Hardening

## Overview
This final tutorial covers deploying our AWS-native User Service to production with enterprise-grade security, monitoring, and operational practices.

## Learning Objectives
- Deploy User Service to AWS production environment
- Implement comprehensive security configurations
- Set up production monitoring and alerting
- Configure auto-scaling and load balancing
- Implement disaster recovery and backup strategies

## Prerequisites
- Completed all previous User Service tutorials (01-14)
- AWS account with appropriate IAM permissions
- CDK v2 installed and configured
- Docker and AWS CLI configured

## Step 1: Production CDK Infrastructure

### 1.1 Create Production CDK Stack
```typescript
// infrastructure/lib/user-service-production-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export class UserServiceProductionStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
```    // VPC for production environment
    const vpc = new ec2.Vpc(this, 'UserServiceVPC', {
      maxAzs: 3,
      natGateways: 2,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          cidrMask: 28,
          name: 'Database',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
    });

    // RDS Database with Multi-AZ
    const dbSecurityGroup = new ec2.SecurityGroup(this, 'DatabaseSG', {
      vpc,
      description: 'Security group for User Service database',
      allowAllOutbound: false,
    });

    const database = new rds.DatabaseInstance(this, 'UserServiceDB', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_15_3,
      }),
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T3,
        ec2.InstanceSize.MEDIUM
      ),
      vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },
      multiAz: true,
      securityGroups: [dbSecurityGroup],
      backupRetention: cdk.Duration.days(7),
      deletionProtection: true,
      storageEncrypted: true,
      monitoringInterval: cdk.Duration.seconds(60),
    });
```### 1.2 ECS Service Configuration
```typescript
    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'UserServiceCluster', {
      vpc,
      containerInsights: true,
    });

    // CloudWatch Log Group
    const logGroup = new logs.LogGroup(this, 'UserServiceLogs', {
      retention: logs.RetentionDays.ONE_MONTH,
    });

    // Fargate Service with Load Balancer
    const fargateService = new ecsPatterns.ApplicationLoadBalancedFargateService(
      this,
      'UserService',
      {
        cluster,
        cpu: 512,
        memoryLimitMiB: 1024,
        desiredCount: 2,
        taskImageOptions: {
          image: ecs.ContainerImage.fromRegistry('your-ecr-repo/user-service:latest'),
          containerPort: 3000,
          environment: {
            NODE_ENV: 'production',
            AWS_REGION: this.region,
          },
          secrets: {
            DATABASE_URL: ecs.Secret.fromSecretsManager(
              secretsmanager.Secret.fromSecretNameV2(
                this,
                'DatabaseSecret',
                'user-service/database'
              )
            ),
          },
          logDriver: ecs.LogDriver.awsLogs({
            streamPrefix: 'user-service',
            logGroup,
          }),
        },
        publicLoadBalancer: true,
        listenerPort: 443,
        protocol: ecsPatterns.ApplicationProtocol.HTTPS,
        domainName: 'api.yourdomain.com',
        domainZone: route53.HostedZone.fromLookup(this, 'Zone', {
          domainName: 'yourdomain.com',
        }),
      }
    );
```    // Auto Scaling
    const scaling = fargateService.service.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 10,
    });

    scaling.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 70,
    });

    scaling.scaleOnMemoryUtilization('MemoryScaling', {
      targetUtilizationPercent: 80,
    });
  }
}
```

## Step 2: Security Configuration

### 2.1 IAM Roles and Policies
```typescript
// Create IAM role for ECS tasks
const taskRole = new iam.Role(this, 'UserServiceTaskRole', {
  assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
  managedPolicies: [
    iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
  ],
  inlinePolicies: {
    UserServicePolicy: new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            'cognito-idp:AdminGetUser',
            'cognito-idp:AdminCreateUser',
            'cognito-idp:AdminSetUserPassword',
            'cognito-idp:AdminDisableUser',
            'ses:SendEmail',
            'ses:SendRawEmail',
            'secretsmanager:GetSecretValue',
            'logs:CreateLogGroup',
            'logs:CreateLogStream',
            'logs:PutLogEvents',
          ],
          resources: ['*'],
        }),
      ],
    }),
  },
});
```### 2.2 Production Dockerfile
```dockerfile
# Dockerfile.production
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nestjs -u 1001

# Copy built application
COPY --from=builder --chown=nestjs:nodejs /app/node_modules ./node_modules
COPY --chown=nestjs:nodejs dist ./dist
COPY --chown=nestjs:nodejs package*.json ./

USER nestjs

EXPOSE 3000

CMD ["node", "dist/main"]
```

## Step 3: CI/CD Pipeline

### 3.1 GitHub Actions for ECR
```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: user-service

jobs:
  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
```    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    - name: Build, tag, and push image to Amazon ECR
      id: build-image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -f Dockerfile.production -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

    - name: Deploy to ECS
      run: |
        aws ecs update-service --cluster user-service-cluster --service user-service --force-new-deployment
```

## Step 4: Environment Variables & Secrets

### 4.1 Production Environment Configuration
```typescript
// src/config/production.config.ts
export const productionConfig = {
  database: {
    host: process.env.DB_HOST,
    port: parseInt(process.env.DB_PORT || '5432'),
    username: process.env.DB_USERNAME,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    ssl: {
      require: true,
      rejectUnauthorized: false,
    },
    logging: false,
    synchronize: false,
    migrationsRun: true,
  },
  cognito: {
    userPoolId: process.env.COGNITO_USER_POOL_ID,
    clientId: process.env.COGNITO_CLIENT_ID,
    region: process.env.AWS_REGION,
  },
  aws: {
    region: process.env.AWS_REGION,
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  },
  logging: {
    level: 'info',
    format: 'json',
  },
};
```## Step 5: Production Monitoring & Alerting

### 5.1 CloudWatch Dashboards
```typescript
// infrastructure/lib/monitoring-stack.ts
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';

const dashboard = new cloudwatch.Dashboard(this, 'UserServiceDashboard', {
  dashboardName: 'UserService-Production',
  widgets: [
    [
      new cloudwatch.GraphWidget({
        title: 'API Response Times',
        left: [
          new cloudwatch.Metric({
            namespace: 'AWS/ApplicationELB',
            metricName: 'TargetResponseTime',
            dimensionsMap: {
              LoadBalancer: fargateService.loadBalancer.loadBalancerFullName,
            },
            statistic: 'Average',
          }),
        ],
      }),
    ],
    [
      new cloudwatch.GraphWidget({
        title: 'ECS Service CPU/Memory',
        left: [
          new cloudwatch.Metric({
            namespace: 'AWS/ECS',
            metricName: 'CPUUtilization',
            dimensionsMap: {
              ServiceName: fargateService.service.serviceName,
              ClusterName: cluster.clusterName,
            },
            statistic: 'Average',
          }),
        ],
        right: [
          new cloudwatch.Metric({
            namespace: 'AWS/ECS',
            metricName: 'MemoryUtilization',
            dimensionsMap: {
              ServiceName: fargateService.service.serviceName,
              ClusterName: cluster.clusterName,
            },
            statistic: 'Average',
          }),
        ],
      }),
    ],
  ],
});
```### 5.2 CloudWatch Alarms
```typescript
// High CPU Utilization Alarm
const cpuAlarm = new cloudwatch.Alarm(this, 'HighCPUAlarm', {
  metric: new cloudwatch.Metric({
    namespace: 'AWS/ECS',
    metricName: 'CPUUtilization',
    dimensionsMap: {
      ServiceName: fargateService.service.serviceName,
      ClusterName: cluster.clusterName,
    },
    statistic: 'Average',
  }),
  threshold: 80,
  evaluationPeriods: 2,
  alarmDescription: 'User Service CPU utilization is high',
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
});

// High Response Time Alarm
const responseTimeAlarm = new cloudwatch.Alarm(this, 'HighResponseTimeAlarm', {
  metric: new cloudwatch.Metric({
    namespace: 'AWS/ApplicationELB',
    metricName: 'TargetResponseTime',
    dimensionsMap: {
      LoadBalancer: fargateService.loadBalancer.loadBalancerFullName,
    },
    statistic: 'Average',
  }),
  threshold: 1.0,
  evaluationPeriods: 3,
  alarmDescription: 'User Service response time is high',
});

// SNS Topic for Alerts
const alertTopic = new sns.Topic(this, 'UserServiceAlerts', {
  displayName: 'User Service Production Alerts',
});

cpuAlarm.addAlarmAction(new cloudwatchActions.SnsAction(alertTopic));
responseTimeAlarm.addAlarmAction(new cloudwatchActions.SnsAction(alertTopic));
```## Step 6: Disaster Recovery & Backup

### 6.1 Database Backup Strategy
```typescript
// Automated database backups
const dbBackup = new rds.DatabaseInstance(this, 'UserServiceDB', {
  // ... existing configuration
  backupRetention: cdk.Duration.days(30),
  deleteAutomatedBackups: false,
  deletionProtection: true,
  
  // Point-in-time recovery
  monitoringInterval: cdk.Duration.seconds(60),
  performanceInsightRetention: rds.PerformanceInsightRetention.MONTHS_1,
});

// Cross-region read replica for disaster recovery
const readReplica = new rds.DatabaseInstanceReadReplica(this, 'UserServiceReadReplica', {
  sourceDatabaseInstance: database,
  instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
  vpc: replicaVpc, // VPC in different region
});
```

### 6.2 Application Health Checks
```typescript
// src/health/health.controller.ts
import { Controller, Get } from '@nestjs/common';
import { HealthCheck, HealthCheckService, TypeOrmHealthIndicator } from '@nestjs/terminus';

@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private db: TypeOrmHealthIndicator,
  ) {}

  @Get()
  @HealthCheck()
  check() {
    return this.health.check([
      () => this.db.pingCheck('database'),
    ]);
  }

  @Get('ready')
  @HealthCheck()
  ready() {
    return this.health.check([
      () => this.db.pingCheck('database'),
      // Add more readiness checks here
    ]);
  }
}
```## Step 7: Deployment Process

### 7.1 Deploy to Production
```bash
# 1. Build and push infrastructure
cd infrastructure
npm run build
cdk deploy UserServiceProductionStack --require-approval never

# 2. Build and push application
docker build -f Dockerfile.production -t user-service:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker tag user-service:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/user-service:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/user-service:latest

# 3. Update ECS service
aws ecs update-service --cluster user-service-cluster --service user-service --force-new-deployment
```

### 7.2 Post-Deployment Verification
```bash
# Check service health
curl https://api.yourdomain.com/health

# Verify database migrations
aws ecs run-task --cluster user-service-cluster --task-definition user-service-migrations

# Check logs
aws logs tail /aws/ecs/user-service --follow
```

## Step 8: Production Checklist

### 8.1 Security Verification
- [ ] All secrets stored in AWS Secrets Manager
- [ ] IAM roles follow least privilege principle
- [ ] Database in private subnets with encryption
- [ ] HTTPS enforced on all endpoints
- [ ] WAF configured for API protection
- [ ] VPC Flow Logs enabled

### 8.2 Monitoring Setup
- [ ] CloudWatch dashboards configured
- [ ] Alarms set for critical metrics
- [ ] SNS notifications configured
- [ ] Log aggregation working
- [ ] Performance metrics collecting

### 8.3 Backup & Recovery
- [ ] Database backups automated
- [ ] Cross-region read replica deployed
- [ ] Disaster recovery plan documented
- [ ] Recovery procedures tested

## Conclusion

You have successfully deployed a production-ready AWS-native User Service with:
- Enterprise-grade security and compliance
- Auto-scaling and high availability
- Comprehensive monitoring and alerting
- Disaster recovery capabilities
- CI/CD pipeline for continuous deployment

This completes the AWS-native enhancement of the User Service tutorial series!