# Tutorial 9: Service Integration

## 🎯 Objective
Connect Product Service with other microservices in the ecommerce platform.

## Step 1: Event Listeners

**src/modules/inventory/listeners/product.listener.ts:**
```typescript
import { Injectable } from '@nestjs/common';
import { EventPattern } from '@nestjs/microservices';

@Injectable()
export class ProductEventListener {
  @EventPattern('ProductCreated')
  async handleProductCreated(data: any) {
    console.log('Product created, initializing inventory:', data);
    // Initialize inventory record for new product
  }

  @EventPattern('ProductUpdated')
  async handleProductUpdated(data: any) {
    console.log('Product updated, syncing data:', data);
    // Update related inventory information
  }
}
```

## Step 2: External Service Calls

**src/modules/products/services/inventory.service.ts:**
```typescript
import { Injectable, HttpService } from '@nestjs/common';

@Injectable()
export class InventoryService {
  constructor(private readonly httpService: HttpService) {}

  async checkStock(productId: string): Promise<number> {
    const response = await this.httpService
      .get(`${process.env.INVENTORY_SERVICE_URL}/products/${productId}/stock`)
      .toPromise();
    
    return response.data.quantity;
  }

  async reserveStock(productId: string, quantity: number): Promise<boolean> {
    const response = await this.httpService
      .post(`${process.env.INVENTORY_SERVICE_URL}/products/${productId}/reserve`, {
        quantity,
      })
      .toPromise();
    
    return response.data.success;
  }
}
```

## ✅ Next Steps
Continue with **[10-performance.md](./10-performance.md)** for optimization techniques.