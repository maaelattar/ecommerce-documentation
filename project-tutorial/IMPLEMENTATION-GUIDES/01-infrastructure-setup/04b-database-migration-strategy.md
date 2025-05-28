# Database Migration Strategy: From Simple to Optimal

## 🎯 Objective

Understand how to evolve from our simple PostgreSQL-everywhere setup to a production-optimized polyglot persistence architecture.

## 📚 Current State vs Future State

### What We Have Now
```typescript
// All services use PostgreSQL
const databases = [
  'userservice',     // PostgreSQL ✅ (Already optimal)
  'productservice',  // PostgreSQL → MongoDB (Phase 2)
  'orderservice',    // PostgreSQL ✅ (Already optimal)
  'paymentservice',  // PostgreSQL ✅ (Already optimal)
  'notificationservice', // PostgreSQL → MongoDB (Phase 3)
  'inventoryservice', // PostgreSQL → DynamoDB (Phase 2)
  'searchservice'    // PostgreSQL → OpenSearch (Phase 2)
];
```

### What We're Building Towards
```typescript
// Optimized database selection
const optimizedDatabases = {
  userService: 'PostgreSQL',      // ACID, Security, Relationships
  productService: 'MongoDB',      // Flexible Schema, Complex Attributes  
  orderService: 'PostgreSQL',     // Transactions, Financial Integrity
  paymentService: 'PostgreSQL',   // Compliance, Audit, ACID
  inventoryService: 'DynamoDB',   // High Throughput, Simple K-V
  notificationService: 'MongoDB', // Flexible Templates, Event Logs
  searchService: 'OpenSearch'     // Full-text Search, Analytics
};
```

## 🎯 Migration Decision Framework

### Step 1: Identify Pain Points in Each Service

**Product Service Pain Points:**
```sql
-- Schema changes for each new product type
ALTER TABLE products ADD COLUMN battery_capacity VARCHAR(50);

-- Complex queries become unmanageable  
SELECT * FROM products 
WHERE JSON_EXTRACT(specifications, '$.camera.main') = '48MP';
```**Inventory Service Pain Points:**
```sql
-- Lock contention during concurrent updates
BEGIN;
SELECT quantity FROM inventory WHERE product_id = 'ABC' FOR UPDATE;
UPDATE inventory SET quantity = quantity - 1 WHERE product_id = 'ABC';
COMMIT;
-- Thousands of concurrent updates = database deadlock nightmare
```

**Notification Service Pain Points:**
```sql
-- Rigid schema for flexible content
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    type VARCHAR(50),
    recipient_data JSON,  -- Becomes unmaintainable
    template_data JSON,   -- No schema validation
    delivery_log JSON     -- Complex queries impossible
);
```

### Step 2: When to Migrate

#### Phase 2 Migrations (High Impact)
**🚀 Product Service → MongoDB**
- **Trigger**: Schema changes every sprint
- **Benefit**: Flexible product attributes, rapid feature development
- **Risk**: Low - read-heavy workload, eventual consistency OK

**⚡ Inventory Service → DynamoDB**  
- **Trigger**: Lock contention during traffic spikes
- **Benefit**: Atomic counters, high throughput
- **Risk**: Medium - need to handle eventual consistency

**🔍 Search Service → OpenSearch**
- **Trigger**: Need full-text search capabilities
- **Benefit**: Native search, analytics, recommendations
- **Risk**: Low - dedicated search infrastructure

#### Phase 3 Migrations (Developer Productivity)
**🎨 Notification Service → MongoDB**
- **Trigger**: Complex template management requirements
- **Benefit**: Flexible schemas, rapid template development
- **Risk**: Low - non-critical service timing

## 🔄 Migration Implementation Strategy

### 1. Dual Write Pattern
```typescript
// Write to both old and new databases during migration
async createProduct(productData: CreateProductDto) {
  // Write to PostgreSQL (existing)
  const pgProduct = await this.pgRepository.save(productData);
  
  // Write to MongoDB (new)
  try {
    await this.mongoRepository.create(productData);
  } catch (error) {
    // Log but don't fail - old system still works
    this.logger.error('MongoDB write failed', error);
  }
  
  return pgProduct;
}
```### 2. Gradual Read Migration
```typescript
// Start reading from new database when ready
async getProduct(id: string) {
  try {
    // Try new database first
    const product = await this.mongoRepository.findById(id);
    if (product) return product;
  } catch (error) {
    this.logger.warn('MongoDB read failed, falling back to PostgreSQL');
  }
  
  // Fallback to old database
  return await this.pgRepository.findById(id);
}
```

### 3. Complete Migration
Once confident in the new system:
```typescript
// Remove old database integration
async getProduct(id: string) {
  return await this.mongoRepository.findById(id);
}
```

## 📋 Migration Checklist

### Before Migration
- [ ] Identify clear pain points with current database
- [ ] Confirm new database solves those specific problems
- [ ] Plan data migration strategy
- [ ] Set up monitoring for both systems

### During Migration  
- [ ] Implement dual-write pattern
- [ ] Monitor data consistency between systems
- [ ] Gradually shift read traffic
- [ ] Validate performance improvements

### After Migration
- [ ] Remove old database dependencies
- [ ] Update documentation and team training
- [ ] Monitor new system performance
- [ ] Document lessons learned

## ✅ Next Step

Understanding the migration strategy? Continue to **[05-service-integration.md](./05-service-integration.md)** to see how services connect to infrastructure.