# Hands-On: Infrastructure Code Walkthrough

## 🎯 Objective
Walk through the **actual repository files** to understand how everything connects.

## 📁 Key Files to Explore

### 1. **Entry Point**
```bash
cd ecommerce-infrastructure/aws
cat bin/ecommerce-app.ts
```
**Shows:** Environment selection (local vs production)

### 2. **Environment Config**
```bash
cat config/environments.ts
```
**Shows:** LocalStack vs AWS settings

### 3. **Main Stack**
```bash
cat lib/ecommerce-infrastructure.ts
```
**Shows:** How constructs are composed together

### 4. **Individual Constructs**
```bash
ls lib/constructs/
cat lib/constructs/data/database-construct.ts
```
**Shows:** How 7 microservice databases are created

## 🔧 What to Look For

- ✅ **Composition** - How main stack assembles constructs  
- ✅ **Strategy** - How providers handle environments
- ✅ **Dependencies** - VPC → Security → Databases order
- ✅ **Configuration** - Different settings per environment

## 📋 Exercise

1. Open `lib/ecommerce-infrastructure.ts`
2. Find where `VpcConstruct` is created
3. See how it's passed to `DatabaseConstruct`
4. Notice the dependency chain

## ✅ Next Step
Code explored? Continue to **[03-localstack-setup.md](./03-localstack-setup.md)**