# DDD in Practice: E-commerce Architecture Case Study

> **Learning Goal**: See how Domain-Driven Design principles are applied in real-world microservices architecture using our e-commerce platform

---

## 🎯 STEP 1: From Domain Analysis to Service Architecture

### Strategic DDD Applied: Service Boundary Discovery

**Our Domain Analysis Process**:
```
Business Capability Mapping:

E-commerce Business Functions:
├── Customer Management (Identity, profiles, preferences)
├── Product Catalog (Products, categories, search, recommendations)
├── Inventory Management (Stock, reservations, warehouses)
├── Order Processing (Cart, checkout, order lifecycle)
├── Payment Processing (Payments, billing, refunds)
├── Communication (Notifications, marketing, support)
└── Analytics & Reporting (Business intelligence, insights)

Language Analysis:
"Customer" means different things:
├── In Identity context: Authentication credentials and profile
├── In Order context: Buyer with shipping address and preferences  
├── In Marketing context: Segment with behavior patterns
├── In Support context: User with service history

"Product" varies by context:
├── In Catalog context: Rich content with descriptions and media
├── In Inventory context: SKU with stock levels and locations
├── In Order context: Purchasable item with price and variants
├── In Search context: Indexed content with relevance scoring
```

**Resulting Microservices Architecture**:
```
┌─────────────────────────────────────────────────────────────────┐
│                E-commerce Domain Services                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │  User Service   │    │ Product Service │                   │
│  │                 │    │                 │                   │
│  │ Identity Context│    │ Catalog Context │                   │
│  │ - Authentication│    │ - Product Info  │                   │
│  │ - User Profiles │    │ - Categories    │                   │
│  │ - Permissions   │    │ - Specifications│                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │Inventory Service│    │  Order Service  │                   │
│  │                 │    │                 │                   │
│  │Inventory Context│    │ Order Context   │                   │
│  │ - Stock Levels  │    │ - Shopping Cart │                   │
│  │ - Reservations  │    │ - Order Process │                   │
│  │ - Warehouses    │    │ - Order History │                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │ Payment Service │    │ Search Service  │                   │
│  │                 │    │                 │                   │
│  │ Payment Context │    │ Search Context  │                   │
│  │ - Transactions  │    │ - Product Index │                   │
│  │ - Fraud Detect  │    │ - Search Queries│                   │
│  │ - Billing       │    │ - Recommendations│                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
│          ┌─────────────────┐                                   │
│          │Notification Svc │                                   │
│          │                 │                                   │
│          │Communication    │                                   │
│          │Context          │                                   │
│          │ - Email/SMS     │                                   │
│          │ - Push Notifs   │                                   │
│          │ - Templates     │                                   │
│          └─────────────────┘                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Context Mapping and Integration Patterns

**Anti-Corruption Layer Pattern**:
```
Problem: External Payment Gateway has different domain model

External API Model:
{
  "transaction_id": "tx_12345",
  "payment_method": "credit_card",
  "amount_cents": 1999,
  "currency_code": "USD",
  "status_code": "SUCCESS",
  "customer_reference": "cust_67890"
}

Our Domain Model:
class Payment {
  constructor(
    private id: PaymentId,
    private orderId: OrderId,
    private amount: Money,
    private method: PaymentMethod,
    private status: PaymentStatus
  ) {}
}

Anti-Corruption Layer:
class PaymentGatewayAdapter {
  constructor(private gateway: ExternalPaymentGateway) {}

  async processPayment(payment: Payment): Promise<PaymentResult> {
    // Translate our domain model to external API
    const externalRequest = {
      transaction_id: payment.getId().toString(),
      payment_method: this.translatePaymentMethod(payment.getMethod()),
      amount_cents: payment.getAmount().toCents(),
      currency_code: payment.getAmount().getCurrency().getCode(),
      customer_reference: payment.getCustomerId().toString()
    };

    // Call external service
    const externalResponse = await this.gateway.processPayment(externalRequest);

    // Translate response back to our domain model
    return PaymentResult.create(
      PaymentId.create(externalResponse.transaction_id),
      this.translateStatus(externalResponse.status_code),
      Money.fromCents(externalResponse.amount_cents, Currency.USD)
    );
  }

  private translatePaymentMethod(method: PaymentMethod): string {
    switch (method) {
      case PaymentMethod.CREDIT_CARD: return "credit_card";
      case PaymentMethod.DEBIT_CARD: return "debit_card";
      case PaymentMethod.PAYPAL: return "paypal";
      default: throw new Error(`Unsupported payment method: ${method}`);
    }
  }

  private translateStatus(statusCode: string): PaymentStatus {
    switch (statusCode) {
      case "SUCCESS": return PaymentStatus.COMPLETED;
      case "PENDING": return PaymentStatus.PENDING;
      case "FAILED": return PaymentStatus.FAILED;
      default: return PaymentStatus.UNKNOWN;
    }
  }
}
```

---

## 🏗️ STEP 2: Tactical DDD Implementation Examples

### Order Service: Rich Domain Model

**Order Aggregate Implementation**:
```typescript
// Domain/Entities/Order.ts
export class Order {
  private domainEvents: DomainEvent[] = [];

  private constructor(
    private readonly id: OrderId,
    private readonly customerId: CustomerId,
    private items: Map<ProductId, OrderItem>,
    private status: OrderStatus,
    private readonly createdAt: Date,
    private shippingAddress?: Address,
    private billingAddress?: Address
  ) {}

  // Factory method - encapsulates creation logic
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

  // Business operations
  addItem(productInfo: ProductInfo, quantity: number): void {
    this.ensureOrderIsModifiable();
    
    const existingItem = this.items.get(productInfo.getId());
    if (existingItem) {
      existingItem.increaseQuantity(quantity);
    } else {
      const newItem = OrderItem.create(productInfo, quantity);
      this.items.set(productInfo.getId(), newItem);
    }

    this.ensureBusinessInvariants();
    
    this.addDomainEvent(new ItemAddedToOrderEvent(
      this.id,
      productInfo.getId(),
      quantity
    ));
  }

  removeItem(productId: ProductId): void {
    this.ensureOrderIsModifiable();
    
    if (this.items.has(productId)) {
      this.items.delete(productId);
      this.addDomainEvent(new ItemRemovedFromOrderEvent(this.id, productId));
    }
  }

  setShippingAddress(address: Address): void {
    this.ensureOrderIsModifiable();
    this.shippingAddress = address;
    this.addDomainEvent(new ShippingAddressUpdatedEvent(this.id, address));
  }

  // Complex business operation with multiple invariants
  confirm(inventoryService: InventoryService, pricingService: OrderPricingService): void {
    this.ensureOrderCanBeConfirmed();
    
    // Business rule: Must have items
    if (this.items.size === 0) {
      throw new OrderValidationError("Cannot confirm empty order");
    }

    // Business rule: Must have shipping address
    if (!this.shippingAddress) {
      throw new OrderValidationError("Shipping address required");
    }

    // Business rule: All items must be available
    for (const item of this.items.values()) {
      if (!inventoryService.isAvailable(item.getProductId(), item.getQuantity())) {
        throw new OrderValidationError(`Insufficient inventory for product ${item.getProductId()}`);
      }
    }

    // Calculate final pricing
    const finalPrice = pricingService.calculateFinalPrice(this);
    
    // State transition
    this.status = OrderStatus.CONFIRMED;
    
    // Emit domain event for other bounded contexts
    this.addDomainEvent(new OrderConfirmedEvent(
      this.id,
      this.customerId,
      Array.from(this.items.values()),
      finalPrice,
      this.shippingAddress
    ));
  }

  // Business invariants
  private ensureOrderIsModifiable(): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new OrderStateError("Cannot modify order in current state");
    }
  }

  private ensureOrderCanBeConfirmed(): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new OrderStateError("Order is not in draft state");
    }
  }

  private ensureBusinessInvariants(): void {
    const total = this.calculateSubtotal();
    
    // Business rule: Maximum order value
    if (total.getAmount() > 50000) {
      throw new OrderValidationError("Order total cannot exceed $50,000");
    }

    // Business rule: Maximum number of items
    if (this.items.size > 100) {
      throw new OrderValidationError("Order cannot contain more than 100 different products");
    }

    // Business rule: Minimum order value for certain regions
    if (this.requiresMinimumOrderValue() && total.getAmount() < 25) {
      throw new OrderValidationError("Minimum order value of $25 required");
    }
  }

  private requiresMinimumOrderValue(): boolean {
    return this.shippingAddress?.getCountry() === Country.INTERNATIONAL;
  }

  // Domain events management
  getUncommittedEvents(): DomainEvent[] {
    return [...this.domainEvents];
  }

  markEventsAsCommitted(): void {
    this.domainEvents = [];
  }

  private addDomainEvent(event: DomainEvent): void {
    this.domainEvents.push(event);
  }

  // Read-only access to internal state
  getId(): OrderId { return this.id; }
  getCustomerId(): CustomerId { return this.customerId; }
  getStatus(): OrderStatus { return this.status; }
  getItems(): ReadonlyArray<OrderItem> { return Array.from(this.items.values()); }
  getShippingAddress(): Address | undefined { return this.shippingAddress; }

  calculateSubtotal(): Money {
    return Array.from(this.items.values())
      .reduce((total, item) => total.add(item.getSubtotal()), Money.zero());
  }
}

// Value Objects
export class OrderItem {
  private constructor(
    private readonly productId: ProductId,
    private readonly productName: string,
    private readonly unitPrice: Money,
    private quantity: number
  ) {}

  static create(productInfo: ProductInfo, quantity: number): OrderItem {
    if (quantity <= 0) {
      throw new Error("Quantity must be positive");
    }
    
    return new OrderItem(
      productInfo.getId(),
      productInfo.getName(),
      productInfo.getPrice(),
      quantity
    );
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

  getProductId(): ProductId { return this.productId; }
  getQuantity(): number { return this.quantity; }
  getUnitPrice(): Money { return this.unitPrice; }
}

// Domain Services
export class OrderPricingService {
  constructor(
    private readonly discountService: DiscountService,
    private readonly taxService: TaxService,
    private readonly shippingService: ShippingService
  ) {}

  calculateFinalPrice(order: Order): Money {
    const subtotal = order.calculateSubtotal();
    
    // Apply discounts
    const discount = this.discountService.calculateOrderDiscount(order);
    const discountedAmount = subtotal.subtract(discount);
    
    // Calculate shipping
    const shippingCost = this.shippingService.calculateShippingCost(
      order.getItems(),
      order.getShippingAddress()!
    );
    
    // Calculate tax
    const taxableAmount = discountedAmount.add(shippingCost);
    const tax = this.taxService.calculateTax(taxableAmount, order.getShippingAddress()!);
    
    return taxableAmount.add(tax);
  }
}
```

### Product Service: Aggregate with Complex Business Logic

**Product Aggregate with Variant Management**:
```typescript
// Domain/Entities/Product.ts
export class Product {
  private domainEvents: DomainEvent[] = [];

  private constructor(
    private readonly id: ProductId,
    private readonly vendorId: VendorId,
    private name: string,
    private description: string,
    private category: Category,
    private basePrice: Money,
    private variants: Map<VariantId, ProductVariant>,
    private status: ProductStatus,
    private readonly createdAt: Date
  ) {}

  static create(
    vendorId: VendorId,
    name: string,
    description: string,
    category: Category,
    basePrice: Money
  ): Product {
    // Business rule: Validate product name
    if (name.length < 3 || name.length > 100) {
      throw new ProductValidationError("Product name must be between 3 and 100 characters");
    }

    // Business rule: Validate base price
    if (basePrice.getAmount() <= 0) {
      throw new ProductValidationError("Product price must be positive");
    }

    const product = new Product(
      ProductId.generate(),
      vendorId,
      name,
      description,
      category,
      basePrice,
      new Map(),
      ProductStatus.DRAFT,
      new Date()
    );

    product.addDomainEvent(new ProductCreatedEvent(
      product.id,
      vendorId,
      name,
      category
    ));

    return product;
  }

  // Complex business operation
  addVariant(
    name: string,
    attributes: Map<string, string>,
    priceModifier: Money,
    sku: SKU
  ): VariantId {
    this.ensureProductIsModifiable();

    // Business rule: SKU must be unique across all variants
    if (this.hasVariantWithSku(sku)) {
      throw new ProductValidationError(`SKU ${sku.getValue()} already exists`);
    }

    // Business rule: Variant name must be unique within product
    if (this.hasVariantWithName(name)) {
      throw new ProductValidationError(`Variant name '${name}' already exists`);
    }

    // Business rule: Price modifier cannot make final price negative
    const finalPrice = this.basePrice.add(priceModifier);
    if (finalPrice.getAmount() <= 0) {
      throw new ProductValidationError("Variant price modifier results in negative price");
    }

    const variant = ProductVariant.create(
      name,
      attributes,
      priceModifier,
      sku
    );

    this.variants.set(variant.getId(), variant);

    this.addDomainEvent(new ProductVariantAddedEvent(
      this.id,
      variant.getId(),
      name,
      sku
    ));

    return variant.getId();
  }

  publish(): void {
    this.ensureProductCanBePublished();

    // Business rule: Must have at least one variant or be a simple product
    if (this.variants.size === 0 && !this.isSimpleProduct()) {
      throw new ProductValidationError("Product must have at least one variant before publishing");
    }

    // Business rule: All variants must be ready for sale
    for (const variant of this.variants.values()) {
      if (!variant.isReadyForSale()) {
        throw new ProductValidationError(`Variant ${variant.getName()} is not ready for sale`);
      }
    }

    this.status = ProductStatus.PUBLISHED;

    this.addDomainEvent(new ProductPublishedEvent(
      this.id,
      this.vendorId,
      this.name,
      this.category
    ));
  }

  updatePrice(newBasePrice: Money): void {
    this.ensureProductIsModifiable();

    // Business rule: Price cannot be reduced by more than 50% at once
    const reductionPercentage = this.basePrice.subtract(newBasePrice)
      .divide(this.basePrice.getAmount())
      .multiply(100);

    if (reductionPercentage.getAmount() > 50) {
      throw new ProductValidationError("Price cannot be reduced by more than 50% at once");
    }

    const oldPrice = this.basePrice;
    this.basePrice = newBasePrice;

    this.addDomainEvent(new ProductPriceUpdatedEvent(
      this.id,
      oldPrice,
      newBasePrice
    ));
  }

  // Business logic queries
  getEffectivePrice(variantId?: VariantId): Money {
    if (variantId) {
      const variant = this.variants.get(variantId);
      if (!variant) {
        throw new Error("Variant not found");
      }
      return this.basePrice.add(variant.getPriceModifier());
    }
    return this.basePrice;
  }

  isAvailableForPurchase(): boolean {
    return this.status === ProductStatus.PUBLISHED &&
           (this.isSimpleProduct() || this.hasAvailableVariants());
  }

  private hasAvailableVariants(): boolean {
    return Array.from(this.variants.values())
      .some(variant => variant.isAvailable());
  }

  private isSimpleProduct(): boolean {
    return this.variants.size === 0;
  }

  // Business invariants
  private ensureProductIsModifiable(): void {
    if (this.status === ProductStatus.DISCONTINUED) {
      throw new ProductStateError("Cannot modify discontinued product");
    }
  }

  private ensureProductCanBePublished(): void {
    if (this.status === ProductStatus.PUBLISHED) {
      throw new ProductStateError("Product is already published");
    }
    if (this.status === ProductStatus.DISCONTINUED) {
      throw new ProductStateError("Cannot publish discontinued product");
    }
  }

  private hasVariantWithSku(sku: SKU): boolean {
    return Array.from(this.variants.values())
      .some(variant => variant.getSku().equals(sku));
  }

  private hasVariantWithName(name: string): boolean {
    return Array.from(this.variants.values())
      .some(variant => variant.getName().toLowerCase() === name.toLowerCase());
  }
}

// Complex Value Object
export class ProductVariant {
  private constructor(
    private readonly id: VariantId,
    private readonly name: string,
    private readonly attributes: Map<string, string>,
    private readonly priceModifier: Money,
    private readonly sku: SKU,
    private status: VariantStatus
  ) {}

  static create(
    name: string,
    attributes: Map<string, string>,
    priceModifier: Money,
    sku: SKU
  ): ProductVariant {
    // Validate variant attributes
    if (attributes.size === 0) {
      throw new Error("Variant must have at least one attribute");
    }

    return new ProductVariant(
      VariantId.generate(),
      name,
      new Map(attributes), // Create defensive copy
      priceModifier,
      sku,
      VariantStatus.ACTIVE
    );
  }

  isReadyForSale(): boolean {
    return this.status === VariantStatus.ACTIVE && 
           this.hasRequiredAttributes();
  }

  isAvailable(): boolean {
    return this.status === VariantStatus.ACTIVE;
  }

  private hasRequiredAttributes(): boolean {
    // Business rule: Certain categories require specific attributes
    const requiredAttributes = ['size', 'color']; // This would come from category rules
    return requiredAttributes.every(attr => this.attributes.has(attr));
  }

  getId(): VariantId { return this.id; }
  getName(): string { return this.name; }
  getPriceModifier(): Money { return this.priceModifier; }
  getSku(): SKU { return this.sku; }
  getAttributes(): ReadonlyMap<string, string> { return this.attributes; }
}
```

---

## 🎯 STEP 3: Event-Driven Integration Patterns

### Saga Pattern Implementation

**Order Processing Saga with Compensation**:
```typescript
// Application/Sagas/OrderProcessingSaga.ts
export class OrderProcessingSaga {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly inventoryService: InventoryService,
    private readonly paymentService: PaymentService,
    private readonly eventPublisher: DomainEventPublisher
  ) {}

  @SagaStart
  @EventHandler(OrderConfirmedEvent)
  async handleOrderConfirmed(event: OrderConfirmedEvent): Promise<void> {
    const sagaId = SagaId.fromOrderId(event.orderId);
    
    try {
      // Step 1: Reserve inventory
      const reservationResult = await this.inventoryService.reserveItems(
        event.orderId,
        event.items
      );

      if (!reservationResult.isSuccessful()) {
        await this.compensateOrder(event.orderId, "Insufficient inventory");
        return;
      }

      // Step 2: Process payment
      const paymentResult = await this.paymentService.processPayment(
        event.orderId,
        event.total,
        event.customerId
      );

      if (!paymentResult.isSuccessful()) {
        // Compensate: Release inventory
        await this.inventoryService.releaseReservation(event.orderId);
        await this.compensateOrder(event.orderId, "Payment failed");
        return;
      }

      // Step 3: Confirm order
      await this.finalizeOrder(event.orderId);

    } catch (error) {
      await this.handleSagaError(sagaId, error);
    }
  }

  @EventHandler(PaymentFailedEvent)
  async handlePaymentFailed(event: PaymentFailedEvent): Promise<void> {
    // Compensate: Release inventory reservation
    await this.inventoryService.releaseReservation(event.orderId);
    await this.compensateOrder(event.orderId, "Payment processing failed");
  }

  @EventHandler(InventoryReservationFailedEvent)
  async handleInventoryReservationFailed(event: InventoryReservationFailedEvent): Promise<void> {
    await this.compensateOrder(event.orderId, "Inventory reservation failed");
  }

  private async compensateOrder(orderId: OrderId, reason: string): Promise<void> {
    const order = await this.orderRepository.findById(orderId);
    if (order) {
      order.cancel(reason);
      await this.orderRepository.save(order);

      await this.eventPublisher.publish(new OrderCancelledEvent(
        orderId,
        reason,
        new Date()
      ));
    }
  }

  private async finalizeOrder(orderId: OrderId): Promise<void> {
    const order = await this.orderRepository.findById(orderId);
    if (order) {
      order.markAsProcessing();
      await this.orderRepository.save(order);

      await this.eventPublisher.publish(new OrderProcessingStartedEvent(
        orderId,
        new Date()
      ));
    }
  }
}
```

### Event Sourcing with Projections

**Order Event Store and Projections**:
```typescript
// Infrastructure/EventSourcing/OrderEventStore.ts
export class OrderEventStore {
  constructor(private readonly eventStore: EventStore) {}

  async save(orderId: OrderId, events: DomainEvent[], expectedVersion: number): Promise<void> {
    const streamId = `order-${orderId.toString()}`;
    
    await this.eventStore.appendToStream(
      streamId,
      events.map(event => ({
        eventType: event.constructor.name,
        eventData: event,
        eventId: EventId.generate(),
        timestamp: new Date()
      })),
      expectedVersion
    );
  }

  async getEvents(orderId: OrderId): Promise<DomainEvent[]> {
    const streamId = `order-${orderId.toString()}`;
    const eventRecords = await this.eventStore.readStream(streamId);
    
    return eventRecords.map(record => this.deserializeEvent(record));
  }

  private deserializeEvent(record: EventRecord): DomainEvent {
    switch (record.eventType) {
      case 'OrderCreatedEvent':
        return new OrderCreatedEvent(
          OrderId.create(record.eventData.orderId),
          CustomerId.create(record.eventData.customerId)
        );
      case 'ItemAddedToOrderEvent':
        return new ItemAddedToOrderEvent(
          OrderId.create(record.eventData.orderId),
          ProductId.create(record.eventData.productId),
          record.eventData.quantity
        );
      case 'OrderConfirmedEvent':
        return new OrderConfirmedEvent(
          OrderId.create(record.eventData.orderId),
          CustomerId.create(record.eventData.customerId),
          record.eventData.items,
          Money.create(record.eventData.total.amount, record.eventData.total.currency)
        );
      default:
        throw new Error(`Unknown event type: ${record.eventType}`);
    }
  }
}

// Read Models / Projections
export class OrderSummaryProjection {
  constructor(private readonly readModelStore: ReadModelStore) {}

  @EventHandler(OrderCreatedEvent)
  async handleOrderCreated(event: OrderCreatedEvent): Promise<void> {
    const orderSummary = {
      orderId: event.orderId.toString(),
      customerId: event.customerId.toString(),
      status: 'DRAFT',
      itemCount: 0,
      totalAmount: 0,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await this.readModelStore.save('order_summaries', orderSummary);
  }

  @EventHandler(ItemAddedToOrderEvent)
  async handleItemAdded(event: ItemAddedToOrderEvent): Promise<void> {
    const orderSummary = await this.readModelStore.findById(
      'order_summaries', 
      event.orderId.toString()
    );

    if (orderSummary) {
      orderSummary.itemCount += event.quantity;
      orderSummary.updatedAt = new Date();
      
      await this.readModelStore.update('order_summaries', orderSummary);
    }
  }

  @EventHandler(OrderConfirmedEvent)
  async handleOrderConfirmed(event: OrderConfirmedEvent): Promise<void> {
    const orderSummary = await this.readModelStore.findById(
      'order_summaries',
      event.orderId.toString()
    );

    if (orderSummary) {
      orderSummary.status = 'CONFIRMED';
      orderSummary.totalAmount = event.total.getAmount();
      orderSummary.updatedAt = new Date();
      
      await this.readModelStore.update('order_summaries', orderSummary);
    }
  }
}
```

---

## 💡 Key DDD Implementation Patterns Used

### 1. **Aggregate Design Patterns**
- **Single Aggregate Root**: Only Order class is accessible from outside
- **Business Invariants**: All business rules enforced within aggregates
- **Domain Events**: Aggregates publish events for cross-context communication

### 2. **Value Object Patterns**
- **Immutability**: Value objects cannot be changed after creation
- **Validation**: Business rules enforced during creation
- **Equality**: Value objects compared by value, not identity

### 3. **Domain Service Patterns**
- **Complex Business Logic**: Operations that don't belong to a single aggregate
- **External Dependencies**: Services that need infrastructure concerns
- **Policy Enforcement**: Business rules that span multiple aggregates

### 4. **Repository Patterns**
- **Domain Interface**: Repository defined in domain layer
- **Infrastructure Implementation**: Actual data access in infrastructure layer
- **Aggregate Reconstruction**: Convert database records to domain objects

### 5. **Event-Driven Integration**
- **Domain Events**: Business events published by aggregates
- **Event Handlers**: Cross-context integration through events
- **Saga Pattern**: Long-running business processes with compensation

---

## 🎯 What You've Learned

You've seen how DDD principles are applied in practice:

1. **Strategic DDD** guides service boundary decisions based on business domains
2. **Rich domain models** encode business rules and enforce invariants
3. **Domain events** enable loose coupling between bounded contexts
4. **Aggregates** provide consistency boundaries and transaction scope
5. **Anti-corruption layers** protect domain models from external system concerns

**🏆 Practical Exercise**:
Analyze how DDD patterns are used in our implementation guides:

1. **Review User Service** implementation and identify aggregates, value objects, and domain events
2. **Examine Product Service** to see complex business logic in domain models
3. **Study Order Service** to understand how sagas handle distributed transactions
4. **Look at event handlers** to see cross-context integration patterns

**Success Metric**: Can you identify and explain the DDD patterns used in each service and why they were chosen?

Understanding DDD in practice helps you build systems that truly reflect the business domain and evolve with business needs! 🏗️✨

---

## 🔗 **Next Steps in Your Learning Journey**

- **Apply to**: Implementation guides (see DDD patterns in real code)
- **Connect with**: System design tutorials (understand architectural decisions)
- **Practice with**: Your own domain modeling exercises

**Remember**: DDD is about collaboration with business experts and building software that speaks their language!