# Troubleshooting Guide

## 🎯 Common Issues & Solutions

### LocalStack
```bash
# Won't start
docker-compose restart

# Not accessible  
curl http://localhost:4566/health
```

### CDK
```bash
# Bootstrap fails
rm -rf cdk.out/ && cdklocal bootstrap --force

# Deployment fails
cdklocal deploy EcommerceNetworkStack
```

### Database
```bash
# Connection fails
awslocal rds describe-db-instances
psql postgresql://test:test@localhost:5432/postgres
```

### Services
```bash
# Won't start
cat .env.local && pnpm install
```

## 🔧 Reset Everything
```bash
./dev clean && docker system prune -f && ./dev start
```

## 🆘 Getting Help
- **[Implementation Specs](../../implementation-specs/)**
- **[Quality Standards](../../architecture/quality-standards/)**

## ✅ Infrastructure Complete!

Continue to **[User Service Tutorial](../02-user-service/README.md)**