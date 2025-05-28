# Development Workflow

## 🎯 Objective

Learn daily development workflow.

## 🔄 Start Environment

```bash
# Start infrastructure
./dev start

# Start services  
cd services/user-service && pnpm run dev
```

## 🔧 Common Tasks

### Health Checks
```bash
curl http://localhost:4566/health      # LocalStack
curl http://localhost:3001/health      # Services
```

### Database
```bash
psql postgresql://user:pass@localhost:5432/user_service
pnpm run db:migrate
```

### Monitoring
```bash
docker-compose logs -f localstack
open http://localhost:15672  # RabbitMQ
```

### Stop
```bash
./dev stop && ./dev clean
```

## 📋 Quality Standards

Following **[API Standards](../../architecture/quality-standards/api-design-standards.md)**:
- ✅ Health endpoints
- ✅ Consistent logging

## ✅ Next Step

See **[06-troubleshooting.md](./06-troubleshooting.md)**