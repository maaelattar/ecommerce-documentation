# How to Think About Event-Driven Architecture: Async Communication Mastery

> **Learning Goal**: Master the mental models for designing resilient, scalable event-driven systems

---

## 🤔 STEP 1: Understanding Events vs Commands

### What's the Fundamental Difference?

**Commands**: "Please do this"
- Imperative (telling someone what to do)
- Directed to specific service
- Can be rejected
- Synchronous mindset

**Events**: "This happened"  
- Declarative (announcing facts)
- Broadcast to anyone interested
- Cannot be rejected (it already happened)
- Asynchronous mindset

### 💭 Mental Model: News vs Instructions

**Command Example**:
```
ProcessPayment {
  orderId: "123",
  amount: 99.99,
  creditCard: "4111..."
}
```
*"Payment Service, please process this payment"*

**Event Example**:
```
PaymentProcessed {
  orderId: "123", 
  amount: 99.99,
  transactionId: "txn_456",
  processedAt: "2024-01-15T10:30:00Z"
}
```
*"Hey everyone, payment was processed successfully"*

**❓ Stop and Think**: Why would you choose events over commands?

**💡 Key Insight**: Events enable loose coupling - the publisher doesn't need to know who cares about the event.

---

## 🏗️ STEP 2: Event Design Thinking

### How Do You Design Good Events?

#### Rule 1: Events Are Immutable Facts
**Bad Event**:
```typescript
interface UserUpdated {
  userId: string;
  // What changed? We don't know!
}
```

**Good Event**:
```typescript
interface UserEmailChanged {
  userId: string;
  previousEmail: string;
  newEmail: string;
  changedAt: Date;
  changedBy: string;
}
```

#### Rule 2: Include Context, Not Just IDs
**Bad Event**:
```typescript
interface OrderPlaced {
  orderId: string;  // Recipients must call back to get details
}
```

**Good Event**:
```typescript
interface OrderPlaced {
  orderId: string;
  customerId: string;
  customerEmail: string;  // For notifications
  totalAmount: number;    // For analytics
  items: Array<{
    productId: string;
    productName: string;  // For order history
    quantity: number;
    price: number;
  }>;
  placedAt: Date;
}
```

**💡 Design Principle**: Include enough data so consumers don't need to call back immediately.

### 🛑 EVENT NAMING: Past Tense vs Present Tense

**Past Tense** (Facts):
- `UserRegistered` ✅
- `PaymentProcessed` ✅  
- `OrderShipped` ✅

**Present Tense** (Commands):
- `RegisterUser` ❌ (This is a command)
- `ProcessPayment` ❌ (This is a command)

**Mental Model**: Events are like newspaper headlines - they report what already happened.

---

## 🔄 STEP 3: Event Flow Patterns

### Pattern 1: Simple Pub/Sub
```
Service A publishes → Event Bus → Service B subscribes
                                → Service C subscribes  
                                → Service D subscribes
```

**When to Use**: Simple notifications, multiple consumers

**Example**: User registration
```
UserService publishes UserRegistered
├── EmailService → Send welcome email
├── AnalyticsService → Track signup metrics
└── RecommendationService → Initialize preferences
```

### Pattern 2: Event Sourcing
```
Commands → Events → Event Store → Current State
```

**Mental Model**: Instead of storing current state, store the history of what happened.

**Traditional Approach**:
```sql
-- Account table stores current balance
UPDATE accounts SET balance = 1000 WHERE id = 123;
```

**Event Sourcing Approach**:
```
Events: 
1. AccountOpened { accountId: 123, initialBalance: 0 }
2. MoneyDeposited { accountId: 123, amount: 500 }
3. MoneyDeposited { accountId: 123, amount: 750 }  
4. MoneyWithdrawn { accountId: 123, amount: 250 }

Current Balance = Sum of events = 1000
```

**Benefits**:
- ✅ Complete audit trail
- ✅ Can replay events to debug
- ✅ Can project different views of same data
- ✅ Time travel (what was state at any point?)

**Costs**:
- ❌ More complex querying
- ❌ Event schema evolution challenges
- ❌ Storage grows continuously

### Pattern 3: Saga (Event Choreography)
```
Service A → Event → Service B → Event → Service C → Event...
```

**Use Case**: Multi-step business processes

**Example**: Order fulfillment saga
```
1. OrderService: OrderPlaced event
2. PaymentService: Processes payment → PaymentProcessed event
3. InventoryService: Reserves items → ItemsReserved event  
4. ShippingService: Ships order → OrderShipped event
5. NotificationService: Sends confirmation
```

**❓ What if payment fails?**
```
1. OrderService: OrderPlaced event
2. PaymentService: Payment fails → PaymentFailed event
3. OrderService: Cancels order → OrderCancelled event
4. NotificationService: Sends failure notification
```

---

## 🚨 STEP 4: Error Handling and Resilience

### The Challenge: Eventual Consistency

**In synchronous systems**:
```
try {
  updateInventory();
  processPayment();
  createOrder();
} catch (error) {
  // Rollback everything
}
```

**In event-driven systems**:
- Events can be processed out of order
- Some events might fail to process
- Network partitions can delay events
- Services might be temporarily down

### Strategy 1: At-Least-Once Delivery + Idempotency

**At-Least-Once**: Message might be delivered multiple times
**Idempotency**: Processing the same message multiple times has same effect

```typescript
// Idempotent event handler
async handlePaymentProcessed(event: PaymentProcessed) {
  // Check if already processed
  const existingPayment = await this.paymentRepo.findByTransactionId(
    event.transactionId
  );
  
  if (existingPayment) {
    return; // Already processed, skip
  }
  
  // Process the event
  await this.processPayment(event);
}
```

**💡 Idempotency Pattern**: Use unique event IDs or business keys to detect duplicates.

### Strategy 2: Dead Letter Queues

**What happens when event processing keeps failing?**

```
Event Queue → Consumer → FAILS → Retry Queue
                                      ↓
               Dead Letter Queue ← FAILS AGAIN
```

**Mental Model**: Like undeliverable mail - it goes to a special place for manual handling.

### Strategy 3: Circuit Breaker for Event Publishing

```typescript
class EventPublisher {
  async publish(event: DomainEvent) {
    if (this.circuitBreaker.isOpen()) {
      // Store event locally, retry later
      await this.localEventStore.save(event);
      return;
    }
    
    try {
      await this.messageQueue.publish(event);
    } catch (error) {
      this.circuitBreaker.recordFailure();
      await this.localEventStore.save(event);
    }
  }
}
```

---

## 📊 STEP 5: Event Ordering and Consistency

### The Problem: Events Can Arrive Out of Order

**Scenario**: User updates their email twice quickly
```
Event 1: EmailChanged { newEmail: "user@gmail.com", timestamp: 10:00:01 }
Event 2: EmailChanged { newEmail: "user@yahoo.com", timestamp: 10:00:02 }
```

**But they arrive as**: Event 2, then Event 1
**Result**: Wrong final email address!

### Solution 1: Event Versioning
```typescript
interface EmailChanged {
  userId: string;
  newEmail: string;
  version: number;  // Monotonic sequence
  timestamp: Date;
}
```

**Handler Logic**:
```typescript
async handleEmailChanged(event: EmailChanged) {
  const currentVersion = await this.getUserVersion(event.userId);
  
  if (event.version <= currentVersion) {
    return; // Ignore old events
  }
  
  await this.updateEmail(event.userId, event.newEmail, event.version);
}
```

### Solution 2: Partition by Entity ID
```
Events for User 123 → Partition A → Single consumer
Events for User 456 → Partition B → Single consumer  
Events for User 789 → Partition C → Single consumer
```

**Guarantee**: Events for same user are processed in order.

### 🤔 Consistency Patterns

#### Eventually Consistent Reads
```
Write: UserService updates user → UserUpdated event
Read: ProfileService updates profile from event (with delay)
```

**Trade-off**: Reads might be slightly stale, but system is more available.

#### Read-Your-Own-Writes Consistency
```
User updates profile → Show updated profile immediately
Other users see update → After event propagation
```

**Implementation**: Return updated data directly from write service, don't wait for events.

---

## 🔍 STEP 6: Event Schema Evolution

### The Problem: Events Live Forever

Unlike REST APIs, events in your event store might be replayed years later.

**Bad**: Changing event structure breaks old consumers
```typescript
// Version 1
interface OrderPlaced {
  orderId: string;
  amount: number;
}

// Version 2 - BREAKING CHANGE!
interface OrderPlaced {
  orderId: string;
  totalAmount: number;  // Renamed field
  currency: string;     // New required field
}
```

### Strategy 1: Additive Changes Only
```typescript
// Version 1
interface OrderPlaced {
  orderId: string;
  amount: number;
}

// Version 2 - NON-BREAKING
interface OrderPlaced {
  orderId: string;
  amount: number;
  currency?: string;     // Optional field
  customerId?: string;   // Optional field
}
```

### Strategy 2: Event Versioning
```typescript
interface OrderPlacedV1 {
  version: 1;
  orderId: string;
  amount: number;
}

interface OrderPlacedV2 {
  version: 2;
  orderId: string; 
  totalAmount: number;
  currency: string;
}
```

**Handler supports both**:
```typescript
async handleOrderPlaced(event: OrderPlacedV1 | OrderPlacedV2) {
  if (event.version === 1) {
    return this.handleV1(event);
  } else {
    return this.handleV2(event);
  }
}
```

---

## 🎯 STEP 7: Event Sourcing Deep Dive

### Building a Complete Event-Sourced System

**Example**: E-commerce Order Aggregate

```typescript
// Events
interface OrderCreated {
  orderId: string;
  customerId: string;
  items: OrderItem[];
  createdAt: Date;
}

interface PaymentProcessed {
  orderId: string;
  paymentId: string;
  amount: number;
  processedAt: Date;
}

interface OrderShipped {
  orderId: string;
  trackingNumber: string;
  shippedAt: Date;
}

interface OrderCancelled {
  orderId: string;
  reason: string;
  cancelledAt: Date;
}
```

**Aggregate Root**:
```typescript
class Order {
  private events: DomainEvent[] = [];
  
  constructor(
    public id: string,
    public customerId: string,
    public status: OrderStatus,
    public items: OrderItem[],
    public totalAmount: number
  ) {}
  
  static fromEvents(events: DomainEvent[]): Order {
    const order = new Order('', '', 'created', [], 0);
    
    for (const event of events) {
      order.applyEvent(event);
    }
    
    return order;
  }
  
  private applyEvent(event: DomainEvent) {
    switch (event.type) {
      case 'OrderCreated':
        this.applyOrderCreated(event as OrderCreated);
        break;
      case 'PaymentProcessed':
        this.applyPaymentProcessed(event as PaymentProcessed);
        break;
      // ... other events
    }
  }
  
  processPayment(paymentId: string, amount: number) {
    if (this.status !== 'created') {
      throw new Error('Can only process payment for created orders');
    }
    
    const event = new PaymentProcessed({
      orderId: this.id,
      paymentId,
      amount,
      processedAt: new Date()
    });
    
    this.applyEvent(event);
    this.events.push(event);
  }
}
```

**💡 Mental Model**: The aggregate is a state machine that transitions based on events.

---

## 🧪 STEP 8: Testing Event-Driven Systems

### Testing Strategy 1: Test Event Handlers Independently

```typescript
describe('OrderEventHandler', () => {
  it('should create order projection when OrderCreated event received', async () => {
    // Arrange
    const event = new OrderCreated({
      orderId: '123',
      customerId: 'user-456',
      items: [{ productId: 'prod-1', quantity: 2 }]
    });
    
    // Act
    await orderHandler.handle(event);
    
    // Assert
    const projection = await orderRepo.findById('123');
    expect(projection.customerId).toBe('user-456');
    expect(projection.items).toHaveLength(1);
  });
});
```

### Testing Strategy 2: Integration Tests with Test Events

```typescript
describe('Order Fulfillment Flow', () => {
  it('should complete order when payment processed', async () => {
    // Arrange: Create order
    await eventBus.publish(new OrderCreated({ orderId: '123' }));
    
    // Act: Process payment  
    await eventBus.publish(new PaymentProcessed({ orderId: '123' }));
    
    // Assert: Order status updated
    await eventually(() => {
      const order = await orderService.findById('123');
      expect(order.status).toBe('paid');
    });
  });
});
```

### Testing Strategy 3: Event Store Testing

```typescript
describe('Order Aggregate', () => {
  it('should replay events to reconstruct state', () => {
    // Arrange
    const events = [
      new OrderCreated({ orderId: '123', customerId: 'user-1' }),
      new PaymentProcessed({ orderId: '123', amount: 100 }),
      new OrderShipped({ orderId: '123', trackingNumber: 'TRACK123' })
    ];
    
    // Act
    const order = Order.fromEvents(events);
    
    // Assert
    expect(order.status).toBe('shipped');
    expect(order.customerId).toBe('user-1');
  });
});
```

---

## 💡 Key Mental Models You've Learned

### 1. **Events vs Commands**
- **Commands**: "Please do this" (can be rejected)
- **Events**: "This happened" (facts, cannot be rejected)

### 2. **Eventually Consistent by Design**
- Accept temporary inconsistency for better availability
- Plan for out-of-order events and failures
- Use idempotency to handle duplicates

### 3. **Event Store as Source of Truth**
- Current state is derived from events
- Events are immutable facts
- Can replay events to rebuild state

### 4. **Choreography vs Orchestration**
- **Choreography**: Services react to events (decentralized)
- **Orchestration**: Central coordinator manages flow (centralized)

---

## 🚀 What You Can Do Now

You've mastered event-driven thinking:

1. **Design** events that enable loose coupling
2. **Handle** failures and eventual consistency gracefully  
3. **Implement** event sourcing for audit trails and debuggability
4. **Test** event-driven systems effectively
5. **Evolve** event schemas without breaking consumers

**❓ Final Challenge**:
Design an event-driven system for a ride-sharing platform (like Uber).

**Consider**:
- What events would you publish?
- How would you handle driver matching?
- What happens if payment fails after ride completion?
- How would you ensure events arrive in order?
- What projections would you build for different read models?

If you can design this system with proper event flows, you're thinking like an event-driven architect! 🔄✨