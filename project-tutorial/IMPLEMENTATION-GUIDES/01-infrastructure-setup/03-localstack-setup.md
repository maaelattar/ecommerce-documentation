# LocalStack Setup

## 🎯 Objective

Set up LocalStack to simulate AWS services locally.

## 📚 What is LocalStack?

LocalStack simulates AWS services on your machine:
- **RDS** for PostgreSQL databases
- **S3** for file storage  
- **SQS/SNS** for messaging
- **ElastiCache** for Redis

## 🔧 Start LocalStack

### 1. Navigate & Start
```bash
cd ecommerce-repos-polyrepo/ecommerce-infrastructure/local
docker-compose up -d
```

### 2. Configure AWS CLI
```bash
aws configure set aws_access_key_id test
aws configure set aws_secret_access_key test
aws configure set region us-east-1

# Create LocalStack alias
echo 'alias awslocal="aws --endpoint-url=http://localhost:4566"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Test Connection
```bash
# Test S3 service
awslocal s3 mb s3://test-bucket
awslocal s3 ls
```

### 4. Check Status
```bash
# View running services
docker-compose ps
curl http://localhost:4566/health
```

## ✅ Next Step

LocalStack running? Continue to **[03-cdk-infrastructure.md](./03-cdk-infrastructure.md)**