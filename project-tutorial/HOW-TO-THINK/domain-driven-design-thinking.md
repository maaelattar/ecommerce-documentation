# Domain-Driven Design Thinking: Modeling Complex Business Domains

> **Learning Goal**: Master the systematic approach to understanding business domains and translating them into robust software architectures

---

## 🎯 STEP 1: What is Domain-Driven Design?

### Beyond Technical Implementation

**Traditional Approach**: "Let's build an e-commerce system with users, products, and orders"
**DDD Approach**: "Let's understand the e-commerce business domain, identify the core business capabilities, and model software that reflects how the business actually works"

### 💭 The DDD Mindset Shift

**Before DDD**:
```
Developer Thinking:
"I need a User table, Product table, Order table..."
"How do I implement shopping cart functionality?"
"What's the database schema for this?"

Result: Technical model that doesn't match business reality
```

**With DDD**:
```
Domain Expert Collaboration:
"How does your business handle customer relationships?"
"What happens when inventory runs low?"
"How do you handle returns and refunds?"
"What are the business rules for pricing?"

Result: Software that speaks the business language
```

**❓ Stop and Think**: Why does it matter if software matches business thinking?

### The Core Problem DDD Solves

**The Translation Problem**:
```
Business Language → Technical Language → Business Language
"Customer places order" → "POST /api/orders" → "Order created"

Lost in Translation:
├── Business rules become scattered across code
├── Domain experts can't validate software behavior
├── Changes require retranslating business requirements
└── Technical debt accumulates as business evolves
```

**DDD Solution**:
```
Shared Language (Ubiquitous Language)
Business Expert: "Customer places order for products"
Developer: "Customer aggregate places order for product aggregates"
Code: customer.placeOrder(products)

Benefits:
├── Business rules are explicit in code
├── Domain experts can read and validate code
├── Changes are expressed in business terms
└── Software evolves with business understanding
```

**💡 Core Insight**: DDD is about creating software that business people can understand and validate.

---

## 🏗️ STEP 2: Strategic DDD - Understanding the Business Domain

### Domain Discovery Process

**Step 1: Event Storming - Understanding Business Flows**

**E-commerce Event Storming Example**:
```
Timeline of Business Events:

Customer Journey:
Customer Registers → Email Verified → Profile Created → 
Browses Catalog → Adds to Cart → Applies Discount → 
Places Order → Payment Processed → Order Confirmed →
Inventory Reserved → Order Shipped → Customer Notified →
Order Delivered → Review Requested

Vendor Journey:
Vendor Registers → Vendor Verified → Products Listed →
Inventory Updated → Order Received → Order Fulfilled →
Payment Received → Performance Reviewed

Administrative Journey:
Fraud Detected → Account Suspended → Dispute Raised →
Investigation Started → Resolution Applied → Account Restored
```

**Key Questions During Event Storming**:
- 🎯 **What triggers this event?** (understanding causality)
- 📊 **Who cares about this event?** (identifying stakeholders)
- 🔧 **What business rules apply?** (understanding constraints)
- 📈 **What happens next?** (understanding workflows)

### Identifying Bounded Contexts

**Bounded Context**: A boundary within which a particular domain model applies

**E-commerce Bounded Contexts Analysis**:
```
Context Discovery Questions:

1. "What does 'Customer' mean in different parts of the business?"

Marketing Context:
├── Customer = Lead with demographic data
├── Focus: Conversion, segmentation, campaigns
└── Language: "prospects", "conversion funnel", "lifetime value"

Sales Context:
├── Customer = Active buyer with purchase history
├── Focus: Order management, pricing, relationships
└── Language: "orders", "shopping cart", "checkout"

Support Context:
├── Customer = Service case with issue history
├── Focus: Problem resolution, satisfaction
└── Language: "tickets", "escalation", "resolution"

Different contexts, different models of "Customer"!
```

**Bounded Context Identification Framework**:
```
For each business capability, ask:

Language Boundaries:
├── Do terms mean different things in different areas?
├── Do teams use different vocabulary for same concepts?
└── Are there translation needs between teams?

Organizational Boundaries:
├── Which teams own which business processes?
├── How do teams collaborate and communicate?
└── Where are the handoff points between teams?

Data Boundaries:
├── What data does each team own and modify?
├── What data is shared vs. private to teams?
└── Where are the authoritative sources of truth?

Process Boundaries:
├── What business processes are independent?
├── Where do processes hand off to other processes?
└── What business rules apply within each process?
```

### E-commerce Bounded Contexts Map

**Our E-commerce Domain Structure**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    E-commerce Business Domain                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │   Identity &    │    │    Catalog      │                   │
│  │  Access Mgmt    │    │   Management    │                   │
│  │                 │    │                 │                   │
│  │ - Authentication│    │ - Products      │                   │
│  │ - Authorization │    │ - Categories    │                   │
│  │ - User Profiles │    │ - Search        │                   │
│  │ - Permissions   │    │ - Recommendations│                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │   Inventory     │    │     Orders      │                   │
│  │   Management    │    │   Management    │                   │
│  │                 │    │                 │                   │
│  │ - Stock Levels  │    │ - Shopping Cart │                   │
│  │ - Reservations  │    │ - Order Process │                   │
│  │ - Warehouses    │    │ - Order History │                   │
│  │ - Suppliers     │    │ - Returns       │                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │    Payments     │    │  Communication  │                   │
│  │   & Billing     │    │   & Messaging   │                   │
│  │                 │    │                 │                   │
│  │ - Payment Proc  │    │ - Notifications │                   │
│  │ - Fraud Detect  │    │ - Email/SMS     │                   │
│  │ - Subscriptions │    │ - Support       │                   │
│  │ - Refunds       │    │ - Marketing     │                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Context Relationships**:
```
Upstream/Downstream Relationships:

Identity Context (Upstream) → All Other Contexts
├── Provides: User authentication and authorization
├── Consumes: Nothing (foundational)
└── Relationship: Core shared kernel

Catalog Context → Orders Context  
├── Provides: Product information for orders
├── Consumes: Order data for analytics
└── Relationship: Customer/Supplier

Orders Context → Inventory Context
├── Provides: Reservation requests
├── Consumes: Stock availability
└── Relationship: Partnership (mutual dependency)

Orders Context → Payments Context
├── Provides: Payment requests
├── Consumes: Payment confirmations
└── Relationship: Customer/Supplier

All Contexts → Communication Context
├── Provides: Event notifications
├── Consumes: Communication services
└── Relationship: Published Language (events)
```

---

## 🎯 STEP 3: Tactical DDD - Implementing Domain Models

### Building Blocks of DDD

**1. Entities - Objects with Identity**
```typescript
// Bad: Anemic Domain Model
interface Order {
  id: string;
  customerId: string;
  items: OrderItem[];
  status: string;
  total: number;
}

// Good: Rich Domain Model
class Order {
  private constructor(
    private readonly id: OrderId,
    private readonly customerId: CustomerId,
    private items: OrderItem[],
    private status: OrderStatus,
    private readonly createdAt: Date
  ) {}

  static create(customerId: CustomerId, items: OrderItem[]): Order {
    if (items.length === 0) {
      throw new Error("Order must have at least one item");
    }
    
    return new Order(
      OrderId.generate(),
      customerId,
      items,
      OrderStatus.PENDING,
      new Date()
    );
  }

  addItem(item: OrderItem): void {
    if (this.status !== OrderStatus.PENDING) {
      throw new Error("Cannot modify confirmed order");
    }
    
    this.items.push(item);
  }

  confirm(): void {
    if (this.items.length === 0) {
      throw new Error("Cannot confirm empty order");
    }
    
    this.status = OrderStatus.CONFIRMED;
  }

  calculateTotal(): Money {
    return this.items.reduce(
      (total, item) => total.add(item.getSubtotal()),
      Money.zero()
    );
  }

  // Business logic lives in the domain model
  canBeCancelled(): boolean {
    return this.status === OrderStatus.PENDING || 
           this.status === OrderStatus.CONFIRMED;
  }
}
```

**2. Value Objects - Objects Without Identity**
```typescript
// Email Value Object
class Email {
  private constructor(private readonly value: string) {}

  static create(email: string): Email {
    if (!this.isValid(email)) {
      throw new Error("Invalid email format");
    }
    return new Email(email.toLowerCase());
  }

  private static isValid(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  toString(): string {
    return this.value;
  }

  equals(other: Email): boolean {
    return this.value === other.value;
  }
}

// Money Value Object
class Money {
  private constructor(
    private readonly amount: number,
    private readonly currency: Currency
  ) {}

  static create(amount: number, currency: Currency): Money {
    if (amount < 0) {
      throw new Error("Money amount cannot be negative");
    }
    return new Money(amount, currency);
  }

  add(other: Money): Money {
    if (!this.currency.equals(other.currency)) {
      throw new Error("Cannot add money with different currencies");
    }
    return new Money(this.amount + other.amount, this.currency);
  }

  multiply(factor: number): Money {
    return new Money(this.amount * factor, this.currency);
  }

  static zero(currency: Currency = Currency.USD): Money {
    return new Money(0, currency);
  }
}
```

**3. Aggregates - Consistency Boundaries**
```typescript
// Order Aggregate Root
class Order {
  private items: Map<ProductId, OrderItem> = new Map();
  private status: OrderStatus = OrderStatus.DRAFT;

  // Aggregate ensures business invariants
  addItem(productId: ProductId, quantity: number, price: Money): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error("Cannot modify non-draft order");
    }

    const existingItem = this.items.get(productId);
    if (existingItem) {
      // Business rule: combine quantities for same product
      existingItem.increaseQuantity(quantity);
    } else {
      const newItem = OrderItem.create(productId, quantity, price);
      this.items.set(productId, newItem);
    }

    // Ensure total doesn't exceed limit
    if (this.calculateTotal().amount > 10000) {
      throw new Error("Order total cannot exceed $10,000");
    }
  }

  // Aggregate coordinates changes to ensure consistency
  confirm(): void {
    if (this.items.size === 0) {
      throw new Error("Cannot confirm empty order");
    }

    // All validation passes, change state atomically
    this.status = OrderStatus.CONFIRMED;
    
    // Emit domain events for other bounded contexts
    this.addDomainEvent(new OrderConfirmedEvent(this.id, this.customerId));
  }

  // Only aggregate root is accessible from outside
  getItems(): ReadonlyArray<OrderItem> {
    return Array.from(this.items.values());
  }
}

// OrderItem is part of Order aggregate, not standalone
class OrderItem {
  private constructor(
    private readonly productId: ProductId,
    private quantity: number,
    private readonly unitPrice: Money
  ) {}

  static create(productId: ProductId, quantity: number, price: Money): OrderItem {
    if (quantity <= 0) {
      throw new Error("Quantity must be positive");
    }
    return new OrderItem(productId, quantity, price);
  }

  increaseQuantity(amount: number): void {
    if (amount <= 0) {
      throw new Error("Quantity increase must be positive");
    }
    this.quantity += amount;
  }

  getSubtotal(): Money {
    return this.unitPrice.multiply(this.quantity);
  }
}
```

**4. Domain Services - Business Logic That Doesn't Belong to Entities**
```typescript
// Domain Service for complex business logic
class OrderPricingService {
  constructor(
    private readonly discountPolicy: DiscountPolicy,
    private readonly taxCalculator: TaxCalculator
  ) {}

  calculateFinalPrice(order: Order, customer: Customer): Money {
    const subtotal = order.calculateSubtotal();
    
    // Apply customer-specific discounts
    const discount = this.discountPolicy.calculateDiscount(customer, order);
    const discountedAmount = subtotal.subtract(discount);
    
    // Calculate taxes based on customer location
    const tax = this.taxCalculator.calculateTax(discountedAmount, customer.getAddress());
    
    return discountedAmount.add(tax);
  }
}

// Domain service interface (in domain layer)
interface InventoryService {
  checkAvailability(productId: ProductId, quantity: number): boolean;
  reserveItems(orderId: OrderId, items: OrderItem[]): ReservationResult;
}

// Implementation in infrastructure layer
class InventoryServiceImpl implements InventoryService {
  constructor(private inventoryRepository: InventoryRepository) {}

  checkAvailability(productId: ProductId, quantity: number): boolean {
    const inventory = this.inventoryRepository.findByProductId(productId);
    return inventory ? inventory.getAvailableQuantity() >= quantity : false;
  }

  reserveItems(orderId: OrderId, items: OrderItem[]): ReservationResult {
    // Implementation details...
  }
}
```

### Repository Pattern - Data Access

```typescript
// Domain Repository Interface (in domain layer)
interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: OrderId): Promise<Order | null>;
  findByCustomerId(customerId: CustomerId): Promise<Order[]>;
  nextIdentity(): OrderId;
}

// Infrastructure Implementation
class PostgreSQLOrderRepository implements OrderRepository {
  constructor(private db: Database) {}

  async save(order: Order): Promise<void> {
    const orderData = this.toDatabase(order);
    
    await this.db.transaction(async (tx) => {
      // Save order
      await tx.query(
        'INSERT INTO orders (id, customer_id, status, created_at) VALUES ($1, $2, $3, $4) ON CONFLICT (id) DO UPDATE SET status = $3',
        [orderData.id, orderData.customerId, orderData.status, orderData.createdAt]
      );
      
      // Save order items
      await tx.query('DELETE FROM order_items WHERE order_id = $1', [orderData.id]);
      for (const item of orderData.items) {
        await tx.query(
          'INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES ($1, $2, $3, $4)',
          [orderData.id, item.productId, item.quantity, item.unitPrice]
        );
      }
    });
  }

  async findById(id: OrderId): Promise<Order | null> {
    const result = await this.db.query(
      'SELECT * FROM orders WHERE id = $1',
      [id.toString()]
    );
    
    if (result.rows.length === 0) {
      return null;
    }
    
    const orderData = result.rows[0];
    const itemsResult = await this.db.query(
      'SELECT * FROM order_items WHERE order_id = $1',
      [id.toString()]
    );
    
    return this.toDomain(orderData, itemsResult.rows);
  }

  private toDomain(orderData: any, itemsData: any[]): Order {
    // Convert database representation to domain model
    const items = itemsData.map(item => 
      OrderItem.create(
        ProductId.create(item.product_id),
        item.quantity,
        Money.create(item.unit_price, Currency.USD)
      )
    );

    return Order.reconstitute(
      OrderId.create(orderData.id),
      CustomerId.create(orderData.customer_id),
      items,
      OrderStatus.fromString(orderData.status),
      orderData.created_at
    );
  }
}
```

---

## 🎨 STEP 4: Domain Events and Integration

### Domain Events Pattern

**Why Domain Events?**
```
Problem: Cross-Context Communication

When Order is confirmed:
├── Inventory needs to reserve items
├── Payment needs to process payment
├── Notification needs to send confirmation
├── Analytics needs to track conversion
└── Shipping needs to prepare fulfillment

Traditional Approach (Tight Coupling):
class OrderService {
  confirmOrder(orderId: OrderId): void {
    const order = this.orderRepository.findById(orderId);
    order.confirm();
    this.orderRepository.save(order);
    
    // Tightly coupled to other services
    this.inventoryService.reserveItems(order);
    this.paymentService.processPayment(order);
    this.notificationService.sendConfirmation(order);
    this.analyticsService.trackOrder(order);
    this.shippingService.prepareShipment(order);
  }
}

Problems:
├── Order service knows about all other services
├── Failure in any service affects order confirmation
├── Hard to add new integrations
└── Violates single responsibility principle
```

**Domain Events Solution**:
```typescript
// Domain Event
class OrderConfirmedEvent {
  constructor(
    public readonly orderId: OrderId,
    public readonly customerId: CustomerId,
    public readonly items: ReadonlyArray<OrderItem>,
    public readonly total: Money,
    public readonly occurredAt: Date = new Date()
  ) {}
}

// Aggregate publishes events
class Order {
  private domainEvents: DomainEvent[] = [];

  confirm(): void {
    if (this.items.size === 0) {
      throw new Error("Cannot confirm empty order");
    }

    this.status = OrderStatus.CONFIRMED;
    
    // Publish domain event
    this.addDomainEvent(new OrderConfirmedEvent(
      this.id,
      this.customerId,
      this.getItems(),
      this.calculateTotal()
    ));
  }

  private addDomainEvent(event: DomainEvent): void {
    this.domainEvents.push(event);
  }

  getUncommittedEvents(): DomainEvent[] {
    return [...this.domainEvents];
  }

  markEventsAsCommitted(): void {
    this.domainEvents = [];
  }
}

// Application Service coordinates
class OrderApplicationService {
  constructor(
    private orderRepository: OrderRepository,
    private eventPublisher: DomainEventPublisher
  ) {}

  async confirmOrder(orderId: OrderId): Promise<void> {
    const order = await this.orderRepository.findById(orderId);
    if (!order) {
      throw new Error("Order not found");
    }

    // Domain logic
    order.confirm();

    // Persist changes and publish events atomically
    await this.orderRepository.save(order);
    
    // Publish events for other bounded contexts
    const events = order.getUncommittedEvents();
    await this.eventPublisher.publishAll(events);
    
    order.markEventsAsCommitted();
  }
}

// Event Handlers in other bounded contexts
class InventoryEventHandler {
  constructor(private inventoryService: InventoryService) {}

  @EventHandler(OrderConfirmedEvent)
  async handle(event: OrderConfirmedEvent): Promise<void> {
    await this.inventoryService.reserveItems(
      event.orderId,
      event.items
    );
  }
}

class NotificationEventHandler {
  constructor(private notificationService: NotificationService) {}

  @EventHandler(OrderConfirmedEvent)
  async handle(event: OrderConfirmedEvent): Promise<void> {
    await this.notificationService.sendOrderConfirmation(
      event.customerId,
      event.orderId
    );
  }
}
```

### Event Sourcing Integration

**Traditional State Storage vs Event Sourcing**:
```typescript
// Traditional: Store Current State
class Order {
  id: OrderId;
  status: OrderStatus;
  items: OrderItem[];
  total: Money;
  // Lost: How did we get to this state?
}

// Event Sourcing: Store Events That Led to State
class OrderEventStore {
  async save(orderId: OrderId, events: DomainEvent[]): Promise<void> {
    for (const event of events) {
      await this.eventStore.append(orderId.toString(), event);
    }
  }

  async getEvents(orderId: OrderId): Promise<DomainEvent[]> {
    return await this.eventStore.getEvents(orderId.toString());
  }
}

// Reconstruct aggregate from events
class Order {
  static fromHistory(events: DomainEvent[]): Order {
    const order = new Order();
    
    for (const event of events) {
      order.apply(event);
    }
    
    return order;
  }

  private apply(event: DomainEvent): void {
    switch (event.constructor) {
      case OrderCreatedEvent:
        this.applyOrderCreated(event as OrderCreatedEvent);
        break;
      case ItemAddedEvent:
        this.applyItemAdded(event as ItemAddedEvent);
        break;
      case OrderConfirmedEvent:
        this.applyOrderConfirmed(event as OrderConfirmedEvent);
        break;
    }
  }

  private applyOrderCreated(event: OrderCreatedEvent): void {
    this.id = event.orderId;
    this.customerId = event.customerId;
    this.status = OrderStatus.DRAFT;
    this.items = new Map();
  }

  private applyItemAdded(event: ItemAddedEvent): void {
    const item = OrderItem.create(
      event.productId,
      event.quantity,
      event.unitPrice
    );
    this.items.set(event.productId, item);
  }

  private applyOrderConfirmed(event: OrderConfirmedEvent): void {
    this.status = OrderStatus.CONFIRMED;
  }
}
```

---

## 🚀 STEP 5: DDD in Our E-commerce System

### Service Boundaries from DDD Analysis

**How We Applied DDD to Define Services**:
```
DDD Analysis → Service Architecture

Bounded Context: Identity & Access Management
├── Domain Concepts: User, Role, Permission, Session
├── Business Rules: Authentication, authorization, user lifecycle
├── Service: User Service
└── Responsibilities: Login, registration, permissions, profiles

Bounded Context: Catalog Management  
├── Domain Concepts: Product, Category, Brand, Specification
├── Business Rules: Product lifecycle, categorization, search
├── Service: Product Service
└── Responsibilities: Product CRUD, catalog browsing, search

Bounded Context: Inventory Management
├── Domain Concepts: Stock, Warehouse, Reservation, Supplier
├── Business Rules: Stock tracking, reservation, reordering
├── Service: Inventory Service  
└── Responsibilities: Stock management, reservations, warehouse ops

Bounded Context: Order Management
├── Domain Concepts: Order, Cart, OrderItem, Pricing
├── Business Rules: Order lifecycle, pricing, validation
├── Service: Order Service
└── Responsibilities: Cart management, order processing, order history

Bounded Context: Payment & Billing
├── Domain Concepts: Payment, Transaction, Refund, Billing
├── Business Rules: Payment processing, fraud detection, refunds
├── Service: Payment Service
└── Responsibilities: Payment processing, transaction management

Bounded Context: Communication & Messaging
├── Domain Concepts: Notification, Message, Template, Channel
├── Business Rules: Notification preferences, delivery rules
├── Service: Notification Service
└── Responsibilities: Email, SMS, push notifications
```

### Domain Models in Each Service

**User Service Domain Model**:
```typescript
// User Aggregate
class User {
  private constructor(
    private readonly id: UserId,
    private email: Email,
    private profile: UserProfile,
    private roles: Set<Role>,
    private status: UserStatus
  ) {}

  static register(email: Email, password: Password): User {
    const user = new User(
      UserId.generate(),
      email,
      UserProfile.empty(),
      new Set([Role.CUSTOMER]),
      UserStatus.PENDING_VERIFICATION
    );

    user.addDomainEvent(new UserRegisteredEvent(user.id, user.email));
    return user;
  }

  verifyEmail(verificationCode: VerificationCode): void {
    if (this.status !== UserStatus.PENDING_VERIFICATION) {
      throw new Error("User is not pending verification");
    }

    this.status = UserStatus.ACTIVE;
    this.addDomainEvent(new EmailVerifiedEvent(this.id));
  }

  assignRole(role: Role): void {
    if (this.roles.has(role)) {
      return; // Already has role
    }

    this.roles.add(role);
    this.addDomainEvent(new RoleAssignedEvent(this.id, role));
  }

  hasPermission(permission: Permission): boolean {
    return Array.from(this.roles).some(role => 
      role.hasPermission(permission)
    );
  }
}

// Value Objects
class Email {
  private constructor(private readonly value: string) {}

  static create(email: string): Email {
    if (!this.isValid(email)) {
      throw new Error("Invalid email format");
    }
    return new Email(email.toLowerCase());
  }

  private static isValid(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  toString(): string {
    return this.value;
  }
}

class Role {
  private constructor(
    private readonly name: string,
    private readonly permissions: Set<Permission>
  ) {}

  static customer(): Role {
    return new Role("CUSTOMER", new Set([
      Permission.BROWSE_PRODUCTS,
      Permission.PLACE_ORDERS,
      Permission.VIEW_ORDER_HISTORY
    ]));
  }

  static vendor(): Role {
    return new Role("VENDOR", new Set([
      Permission.MANAGE_PRODUCTS,
      Permission.VIEW_SALES_REPORTS,
      Permission.MANAGE_INVENTORY
    ]));
  }

  hasPermission(permission: Permission): boolean {
    return this.permissions.has(permission);
  }
}
```

**Order Service Domain Model**:
```typescript
// Order Aggregate
class Order {
  private constructor(
    private readonly id: OrderId,
    private readonly customerId: CustomerId,
    private items: Map<ProductId, OrderItem>,
    private status: OrderStatus,
    private readonly createdAt: Date
  ) {}

  static createForCustomer(customerId: CustomerId): Order {
    const order = new Order(
      OrderId.generate(),
      customerId,
      new Map(),
      OrderStatus.DRAFT,
      new Date()
    );

    order.addDomainEvent(new OrderCreatedEvent(order.id, customerId));
    return order;
  }

  addItem(productInfo: ProductInfo, quantity: number): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error("Cannot modify non-draft order");
    }

    const existingItem = this.items.get(productInfo.id);
    if (existingItem) {
      existingItem.increaseQuantity(quantity);
    } else {
      const item = OrderItem.create(productInfo, quantity);
      this.items.set(productInfo.id, item);
    }

    this.addDomainEvent(new ItemAddedToOrderEvent(
      this.id,
      productInfo.id,
      quantity
    ));
  }

  confirm(pricingService: OrderPricingService): void {
    if (this.items.size === 0) {
      throw new Error("Cannot confirm empty order");
    }

    // Calculate final pricing
    const finalPrice = pricingService.calculateFinalPrice(this);
    
    this.status = OrderStatus.CONFIRMED;
    
    this.addDomainEvent(new OrderConfirmedEvent(
      this.id,
      this.customerId,
      Array.from(this.items.values()),
      finalPrice
    ));
  }

  // Business invariants
  private ensureOrderLimits(): void {
    const total = this.calculateSubtotal();
    if (total.amount > 50000) {
      throw new Error("Order total cannot exceed $50,000");
    }

    if (this.items.size > 100) {
      throw new Error("Order cannot have more than 100 different items");
    }
  }
}

// Domain Service
class OrderPricingService {
  constructor(
    private readonly discountCalculator: DiscountCalculator,
    private readonly taxCalculator: TaxCalculator
  ) {}

  calculateFinalPrice(order: Order): Money {
    const subtotal = order.calculateSubtotal();
    const discount = this.discountCalculator.calculate(order);
    const tax = this.taxCalculator.calculate(subtotal.subtract(discount));
    
    return subtotal.subtract(discount).add(tax);
  }
}
```

### Cross-Context Integration Through Events

**Event-Driven Integration Example**:
```typescript
// Order Service publishes events
class OrderConfirmedEvent {
  constructor(
    public readonly orderId: OrderId,
    public readonly customerId: CustomerId,
    public readonly items: OrderItem[],
    public readonly total: Money,
    public readonly confirmedAt: Date = new Date()
  ) {}
}

// Inventory Service reacts to order events
class InventoryEventHandler {
  constructor(private inventoryService: InventoryDomainService) {}

  @EventHandler(OrderConfirmedEvent)
  async handle(event: OrderConfirmedEvent): Promise<void> {
    try {
      await this.inventoryService.reserveItemsForOrder(
        event.orderId,
        event.items
      );
    } catch (error) {
      // Publish compensation event
      await this.eventPublisher.publish(new InventoryReservationFailedEvent(
        event.orderId,
        error.message
      ));
    }
  }
}

// Payment Service reacts to inventory events
class PaymentEventHandler {
  constructor(private paymentService: PaymentDomainService) {}

  @EventHandler(InventoryReservedEvent)
  async handle(event: InventoryReservedEvent): Promise<void> {
    await this.paymentService.processPaymentForOrder(
      event.orderId,
      event.totalAmount
    );
  }

  @EventHandler(InventoryReservationFailedEvent)
  async handle(event: InventoryReservationFailedEvent): Promise<void> {
    // Cancel the order due to inventory failure
    await this.eventPublisher.publish(new OrderCancellationRequestedEvent(
      event.orderId,
      "Insufficient inventory"
    ));
  }
}
```

---

## 💡 Key DDD Principles Applied in Our System

### 1. **Ubiquitous Language**
- Code uses business terminology: `Order.confirm()`, `Customer.placeOrder()`
- Domain experts can read and validate business logic
- Business rules are explicit and testable

### 2. **Bounded Contexts as Service Boundaries**  
- Each service owns a specific business capability
- Clear contracts between services through events
- Independent evolution of each context

### 3. **Rich Domain Models**
- Business logic lives in domain objects, not services
- Entities enforce business invariants
- Value objects ensure data integrity

### 4. **Domain Events for Integration**
- Loose coupling between bounded contexts
- Eventual consistency through event-driven architecture
- Clear audit trail of business events

### 5. **Separation of Concerns**
- Domain layer pure business logic
- Application layer coordinates use cases
- Infrastructure layer handles technical concerns

---

## 🎯 What You Can Do Now

You've mastered Domain-Driven Design thinking:

1. **Analyze business domains** to identify bounded contexts and service boundaries
2. **Model rich domain objects** that encode business rules and invariants
3. **Design loosely coupled systems** using domain events and eventual consistency
4. **Speak the business language** in code and technical discussions
5. **Apply DDD strategically** to complex business domains

**🏆 Practice Exercise**:
Apply DDD analysis to a different business domain:

1. **Event Storm** a business process (e.g., library management, hotel booking)
2. **Identify bounded contexts** based on language and organizational boundaries
3. **Model core aggregates** with business rules and invariants
4. **Design domain events** for cross-context communication
5. **Map to microservices architecture** based on bounded contexts

**Success Metric**: Can you explain business logic in terms that domain experts understand and validate?

Domain-Driven Design is the bridge between business needs and technical implementation - it's how you build software that truly serves the business! 🌉✨

---

## 🔗 **Next Steps in Your Learning Journey**

- **Apply DDD to**: Our system design tutorials (see how DDD guided our architecture)
- **Connect with**: Trade-off analysis (understand when to apply DDD patterns)
- **Practice with**: Implementation guides (see DDD principles in code)

**Remember**: DDD is about collaboration with domain experts and building software that speaks the business language!