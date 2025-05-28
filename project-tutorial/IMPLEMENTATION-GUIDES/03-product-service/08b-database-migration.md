# Tutorial 8b: Database Migration Strategy
## PostgreSQL → MongoDB Evolution

## 🎯 Objective
Experience the **strategic decision-making process** of migrating from PostgreSQL to MongoDB when relational patterns become limiting.

## 🤔 Why This Tutorial Exists

You've built a product service with PostgreSQL and **felt the pain points**:
- ✅ **JSONB workarounds** for flexible product attributes
- ✅ **Complex joins** for category hierarchies  
- ✅ **Dual-database architecture** (PostgreSQL + OpenSearch)
- ✅ **Rigid schema changes** requiring migrations

**This is real-world evolution!** Production systems start simple and evolve based on actual constraints.

## 📊 Pain Point Analysis

Let's examine what we experienced in tutorials 2-7:

### Pain Point 1: Flexible Product Attributes
**PostgreSQL Reality:**
```sql
-- Adding new attribute types requires schema changes
ALTER TABLE product_variants ADD COLUMN material VARCHAR(50);
ALTER TABLE product_variants ADD COLUMN season VARCHAR(20);

-- Querying JSON is complex and slow
SELECT * FROM product_variants 
WHERE (attributes->>'color')::text = 'red' 
  AND (attributes->>'size')::text = 'M';
```

**MongoDB Solution:**
```javascript
// No schema changes needed - just add fields
db.products.insertOne({
  name: "Summer T-Shirt",
  variants: [
    { color: "red", size: "M", material: "cotton", season: "summer" }
  ]
});

// Natural, indexed queries
db.products.find({ 
  "variants.color": "red", 
  "variants.size": "M" 
});
```

### Pain Point 2: Category Hierarchies
**PostgreSQL Complexity:**
```sql
-- Nested set queries are complex
WITH RECURSIVE category_tree AS (
  SELECT id, name, parent_id, 0 as level
  FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, ct.level + 1
  FROM categories c
  INNER JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree;
```

**MongoDB Simplicity:**
```javascript
// Natural hierarchical structure
{
  _id: "electronics",
  name: "Electronics",
  path: ["electronics"],
  parent: null,
  children: ["smartphones", "laptops"]
}

// Simple path-based queries
db.categories.find({ path: /^electronics/ })
```### Pain Point 3: Dual Database Architecture
**Current Complexity:**
- PostgreSQL for transactional data
- OpenSearch for search functionality  
- Synchronization challenges
- Two systems to deploy and maintain

**MongoDB Solution:**
- Single database with full-text search
- Built-in text indexes: `db.products.createIndex({ name: "text", description: "text" })`
- Atomic operations across all data

## 🔄 Migration Strategy

### Phase 1: Preparation (Week 1)
```typescript
// 1. Add MongoDB alongside PostgreSQL
// 2. Create parallel data models
// 3. Implement dual-write pattern

@Injectable()
export class ProductService {
  constructor(
    private postgresRepo: Repository<Product>,
    private mongoService: MongoProductService
  ) {}

  async create(data: CreateProductDto) {
    // Write to both databases
    const pgResult = await this.postgresRepo.save(data);
    await this.mongoService.create(this.transformToMongo(pgResult));
    return pgResult;
  }
}
```

### Phase 2: Gradual Migration (Week 2)
```typescript
// Start reading from MongoDB for new features
async findProductsWithAdvancedFilters(filters: any) {
  // New complex queries use MongoDB
  return this.mongoService.findWithFilters(filters);
}

async findById(id: string) {
  // Fallback pattern
  const mongoResult = await this.mongoService.findById(id);
  if (!mongoResult) {
    return this.postgresRepo.findOne({ where: { id } });
  }
  return mongoResult;
}
```

### Phase 3: Complete Migration (Week 3)
```typescript
// Switch all reads to MongoDB
// Keep PostgreSQL as backup
// Validate data consistency
// Remove PostgreSQL after validation period
```## 📋 MongoDB Data Model

### New Product Schema
```typescript
// MongoDB product document
interface MongoProduct {
  _id: string;
  name: string;
  slug: string;
  description: string;
  basePrice: number;
  images: string[];
  category: {
    _id: string;
    name: string;
    path: string[];  // ['electronics', 'smartphones']
  };
  variants: ProductVariant[];  // Embedded, not separate table
  attributes: {                // Flexible schema
    brand?: string;
    color?: string[];
    size?: string[];
    material?: string;
    weight?: number;
    [key: string]: any;        // Future attributes
  };
  searchTerms: string[];       // Denormalized for search
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface ProductVariant {
  sku: string;
  price: number;
  attributes: Record<string, any>;
  stockQuantity: number;
  imageUrl?: string;
  isActive: boolean;
}
```

### Benefits Realized
```typescript
// 1. Natural queries
db.products.find({ 
  "attributes.brand": "Nike",
  "variants.attributes.color": "red",
  price: { $gte: 50, $lte: 200 }
});

// 2. Flexible schema evolution
db.products.updateMany(
  { category: "clothing" },
  { $set: { "attributes.season": "spring" } }
);

// 3. Aggregation pipelines for analytics
db.products.aggregate([
  { $match: { "category.path": "electronics" } },
  { $group: { _id: "$attributes.brand", avgPrice: { $avg: "$basePrice" } } }
]);
```## 🔄 Implementation Steps

### Step 1: Add MongoDB Dependencies
```bash
npm install @nestjs/mongoose mongoose
npm install --save-dev @types/mongoose
```

### Step 2: Create MongoDB Schema
**src/modules/products/mongo/mongo-product.schema.ts:**
```typescript
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

@Schema({ timestamps: true })
export class MongoProduct extends Document {
  @Prop({ required: true })
  name: string;

  @Prop({ required: true, unique: true })
  slug: string;

  @Prop({ required: true })
  description: string;

  @Prop({ required: true, type: Number })
  basePrice: number;

  @Prop({ type: [String], default: [] })
  images: string[];

  @Prop({
    type: {
      _id: String,
      name: String,
      path: [String]
    }
  })
  category: {
    _id: string;
    name: string;
    path: string[];
  };

  @Prop({
    type: [{
      sku: String,
      price: Number,
      attributes: Object,
      stockQuantity: Number,
      imageUrl: String,
      isActive: Boolean
    }]
  })
  variants: any[];

  @Prop({ type: Object, default: {} })
  attributes: Record<string, any>;

  @Prop({ type: [String], default: [] })
  searchTerms: string[];

  @Prop({ default: true })
  isActive: boolean;
}

export const MongoProductSchema = SchemaFactory.createForClass(MongoProduct);
MongoProductSchema.index({ name: 'text', description: 'text' });
```### Step 3: Implement Migration Service
**src/modules/products/services/migration.service.ts:**
```typescript
@Injectable()
export class MigrationService {
  constructor(
    @InjectRepository(Product)
    private postgresRepo: Repository<Product>,
    @InjectModel(MongoProduct.name)
    private mongoModel: Model<MongoProduct>
  ) {}

  async migrateProduct(productId: string) {
    const pgProduct = await this.postgresRepo.findOne({
      where: { id: productId },
      relations: ['category', 'variants']
    });

    if (!pgProduct) throw new Error('Product not found');

    const mongoProduct = new this.mongoModel({
      _id: pgProduct.id,
      name: pgProduct.name,
      slug: pgProduct.slug,
      description: pgProduct.description,
      basePrice: pgProduct.basePrice,
      images: pgProduct.images || [],
      category: {
        _id: pgProduct.category.id,
        name: pgProduct.category.name,
        path: this.buildCategoryPath(pgProduct.category)
      },
      variants: pgProduct.variants.map(v => ({
        sku: v.sku,
        price: v.price,
        attributes: v.attributes || {},
        stockQuantity: v.stockQuantity,
        imageUrl: v.imageUrl,
        isActive: v.isActive
      })),
      attributes: this.extractAttributes(pgProduct),
      searchTerms: this.buildSearchTerms(pgProduct),
      isActive: pgProduct.isActive
    });

    return mongoProduct.save();
  }

  async migrateAllProducts() {
    const products = await this.postgresRepo.find();
    const migrated = [];
    
    for (const product of products) {
      try {
        await this.migrateProduct(product.id);
        migrated.push(product.id);
      } catch (error) {
        console.error(`Failed to migrate ${product.id}:`, error);
      }
    }
    
    return { total: products.length, migrated: migrated.length };
  }
}
```## 🎯 Key Learning Outcomes

After implementing this migration, you'll understand:

1. **When to migrate databases** - Specific pain points that trigger evolution
2. **How to plan migrations** - Dual-write patterns and gradual transitions  
3. **Document vs Relational** - Practical differences in real applications
4. **Schema flexibility** - How MongoDB handles evolving requirements
5. **Search consolidation** - Eliminating dual-database complexity

## 🚀 Production Considerations

### Migration Checklist
- [ ] **Data validation** - Ensure 100% data consistency
- [ ] **Performance testing** - Compare query performance  
- [ ] **Rollback plan** - Keep PostgreSQL as backup
- [ ] **Team training** - MongoDB query patterns vs SQL
- [ ] **Monitoring updates** - New database metrics
- [ ] **Backup strategy** - MongoDB backup procedures

### Success Metrics
- ✅ **Reduced complexity** - Single database system
- ✅ **Improved performance** - Native document queries
- ✅ **Feature velocity** - Faster schema evolution
- ✅ **Better search** - Consolidated search solution
- ✅ **Developer productivity** - Natural data modeling

## 🎓 Real-World Insight

This migration pattern reflects how successful companies evolve:

**Early Stage**: Start simple (PostgreSQL everywhere)  
**Growth Stage**: Hit scaling/flexibility pain points  
**Optimization Stage**: Migrate to specialized databases

Examples:
- **Instagram**: PostgreSQL → Cassandra for timeline data
- **Uber**: PostgreSQL → MongoDB for location data  
- **Netflix**: MySQL → Cassandra for viewing data

The key is **experiencing pain points first**, then making informed decisions!

## ✅ Next Step
Continue with **[09-deployment.md](./09-deployment.md)** for production deployment with your new MongoDB-based architecture.