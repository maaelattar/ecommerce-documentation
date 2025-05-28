# Tutorial 18: End-to-End Integration Testing

## 🎯 Objective
Test that User Service, infrastructure, and shared libraries work together properly before building Product Service.

## 📚 Integration Test Checklist

### ✅ **Infrastructure Tests**
```bash
# 1. Verify LocalStack infrastructure is running
awslocal rds describe-db-instances
awslocal s3 ls
awslocal secretsmanager list-secrets

# 2. Test database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# 3. Test RabbitMQ connectivity
curl http://guest:guest@localhost:15672/api/overview
```

### ✅ **User Service Tests**
```bash
# 1. Start User Service
cd user-service
npm run start:dev

# 2. Test registration endpoint
curl -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","firstName":"Test","lastName":"User"}'

# 3. Test login endpoint
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# 4. Test JWT validation (save token from login)
curl -X GET http://localhost:3000/users/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### ✅ **Event Publishing Tests**
```bash
# 1. Check RabbitMQ management UI
open http://localhost:15672

# 2. Verify User Service publishes events
# Look for user.created events in RabbitMQ

# 3. Test event structure matches BaseEvent interface
```

## 🔧 Troubleshooting Common Issues

### Database Connection Issues
- Check LocalStack is running: `docker ps`
- Verify environment variables: `echo $DATABASE_URL`
- Test direct connection: `psql $DATABASE_URL`

### Authentication Issues  
- Verify JWT_SECRET is set
- Check token expiration
- Validate user roles and permissions

### Event Publishing Issues
- Check RabbitMQ connection string
- Verify queue creation
- Test message serialization

## ✅ Integration Success Criteria

Before moving to Product Service, verify:
- ✅ User registration and login working
- ✅ JWT authentication working  
- ✅ Database operations successful
- ✅ Event publishing functional
- ✅ Shared libraries built and ready
- ✅ Infrastructure stable and accessible

## 🚀 Ready for Product Service

If all tests pass, you're ready to start building the Product Service with confidence that the foundation is solid!

## ✅ Next Step

Integration complete? Move to **[Product Service Tutorial](../03-product-service/README.md)**