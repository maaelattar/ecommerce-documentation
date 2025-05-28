# Tutorial 8: Testing Strategy

## 🎯 Objective
Implement comprehensive testing for Product Service including unit and integration tests.

## Step 1: Unit Tests

**src/modules/products/services/product.service.spec.ts:**
```typescript
import { Test } from '@nestjs/testing';
import { ProductService } from './product.service';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Product } from '../entities/product.entity';

describe('ProductService', () => {
  let service: ProductService;
  let mockRepository: any;

  beforeEach(async () => {
    mockRepository = {
      create: jest.fn(),
      save: jest.fn(),
      find: jest.fn(),
      findOne: jest.fn(),
    };

    const module = await Test.createTestingModule({
      providers: [
        ProductService,
        { provide: getRepositoryToken(Product), useValue: mockRepository },
      ],
    }).compile();

    service = module.get<ProductService>(ProductService);
  });

  it('should create a product', async () => {
    const productDto = { name: 'Test Product', basePrice: 10.99 };
    mockRepository.create.mockReturnValue(productDto);
    mockRepository.save.mockResolvedValue({ id: '1', ...productDto });

    const result = await service.create(productDto);
    expect(result.name).toBe('Test Product');
  });
});
```

## Step 2: Integration Tests

**test/products.e2e-spec.ts:**
```typescript
import { Test } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';

describe('Products (e2e)', () => {
  let app: INestApplication;

  beforeEach(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  it('/products (GET)', () => {
    return request(app.getHttpServer())
      .get('/products')
      .expect(200);
  });
});
```

## ✅ Next Steps
Complete Product Service with **[09-service-integration.md](./09-service-integration.md)**