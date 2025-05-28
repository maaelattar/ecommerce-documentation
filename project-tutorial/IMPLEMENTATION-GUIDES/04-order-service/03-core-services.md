# Core Services - Order Service with Shared Libraries

## 🎯 Objective
Implement order management business logic using shared libraries for consistency and reliability.

## 🏗️ Order Service Implementation

```typescript
// src/order/order.service.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, DataSource } from 'typeorm';

// Import shared utilities
import { LoggerService } from '@ecommerce/nestjs-core-utils';
import { EventPublisher } from '@ecommerce/rabbitmq-event-utils';

import { Order, OrderStatus } from './entities/order.entity';
import { CreateOrderDto } from './dto/create-order.dto';
import { OrderCreatedEvent, OrderStatusChangedEvent } from '../events/order.events';

@Injectable()
export class OrderService {
  constructor(
    @InjectRepository(Order)
    private readonly orderRepository: Repository<Order>,
    private readonly dataSource: DataSource,
    private readonly logger: LoggerService,
    private readonly eventPublisher: EventPublisher,
  ) {}

  async createOrder(createOrderDto: CreateOrderDto, customerId: string): Promise<Order> {
    return await this.dataSource.transaction(async (manager) => {
      try {
        // Create order with items
        const order = manager.create(Order, {
          ...createOrderDto,
          customerId,
          status: OrderStatus.PENDING,
        });
        
        const savedOrder = await manager.save(order);

        // Publish event using shared library
        const event = new OrderCreatedEvent(
          savedOrder.id,
          customerId,
          savedOrder.totalAmount,
          savedOrder.items.map(item => ({
            productId: item.productId,
            quantity: item.quantity,
            price: item.price,
          })),
        );

        await this.eventPublisher.publishWithTransaction(event, manager);

        this.logger.log('Order created successfully', 'OrderService', {
          orderId: savedOrder.id,
          customerId,
          totalAmount: savedOrder.totalAmount,
        });

        return savedOrder;
      } catch (error) {
        this.logger.error('Failed to create order', error, 'OrderService', {
          customerId,
        });
        throw error;
      }
    });
  }
```