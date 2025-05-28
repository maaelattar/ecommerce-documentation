# Tutorial 12: Production Deployment

## 🎯 Objective
Deploy Product Service to AWS using ECS Fargate with proper configuration.

## Step 1: Dockerfile

**Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3001

CMD ["node", "dist/main"]
```

## Step 2: ECS Task Definition

**deploy/task-definition.json:**
```json
{
  "family": "product-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "product-service",
      "image": "your-account.dkr.ecr.region.amazonaws.com/product-service:latest",
      "portMappings": [
        {
          "containerPort": 3001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/product-service",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Step 3: Deployment Script

**scripts/deploy.sh:**
```bash
#!/bin/bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com

docker build -t product-service .
docker tag product-service:latest your-account.dkr.ecr.us-east-1.amazonaws.com/product-service:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/product-service:latest

aws ecs update-service --cluster ecommerce-cluster --service product-service --force-new-deployment
```

## 🎉 Congratulations!
You've completed the Product Service tutorial! Your service now includes:
- ✅ Complete product catalog management
- ✅ Authentication and authorization
- ✅ Event-driven communication
- ✅ Search integration
- ✅ Performance optimization
- ✅ Production monitoring
- ✅ AWS deployment

## ✅ Next Steps
Continue with **[Order Service Tutorial](../04-order-service/)** to build the order management system.