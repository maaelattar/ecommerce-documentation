# Event Publishing - Order Service with Shared Libraries

## 🎯 Objective
Implement reliable event publishing using shared event utilities with transactional outbox pattern.

## 📡 Order Events Definition

```typescript
// src/events/order.events.ts
import { DomainEvent } from '@ecommerce/rabbitmq-event-utils';

export class OrderCreatedEvent extends DomainEvent {
  constructor(
    public readonly orderId: string,
    public readonly customerId: string,
    public readonly totalAmount: number,
    public readonly items: Array<{
      productId: string;
      quantity: number;
      price: number;
    }>,
  ) {
    super('order.created', '1.0.0');
  }
}

export class OrderStatusChangedEvent extends DomainEvent {
  constructor(
    public readonly orderId: string,
    public readonly customerId: string,
    public readonly previousStatus: string,
    public readonly newStatus: string,
    public readonly timestamp: Date,
  ) {
    super('order.status_changed', '1.0.0');
  }
}

export class OrderCancelledEvent extends DomainEvent {
  constructor(
    public readonly orderId: string,
    public readonly customerId: string,
    public readonly reason: string,
    public readonly refundAmount: number,
  ) {
    super('order.cancelled', '1.0.0');
  }
}
```

## 🔄 Event Publishing in Service

```typescript
// Updated order.service.ts with event publishing
async updateOrderStatus(orderId: string, newStatus: OrderStatus, customerId: string): Promise<Order> {
  return await this.dataSource.transaction(async (manager) => {
    const order = await manager.findOne(Order, { 
      where: { id: orderId, customerId },
      relations: ['items'],
    });

    if (!order) {
      throw new NotFoundException('Order not found');
    }

    const previousStatus = order.status;
    order.status = newStatus;
    order.version += 1;

    const updatedOrder = await manager.save(order);

    // Publish status change event
    const event = new OrderStatusChangedEvent(
      orderId,
      customerId,
      previousStatus,
      newStatus,
      new Date(),
    );

    await this.eventPublisher.publishWithTransaction(event, manager);

    this.logger.log('Order status updated', 'OrderService', {
      orderId,
      previousStatus,
      newStatus,
    });

    return updatedOrder;
  });
}
```