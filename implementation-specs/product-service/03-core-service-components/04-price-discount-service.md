# Price & Discount Service Specification

## Overview

The Price & Discount Service manages pricing, discounts, and promotional logic for product variants in the e-commerce platform. It is responsible for calculating final prices, applying discounts, tracking price history, and ensuring business rules are enforced. The service integrates with Product, Inventory, and Order services, supports complex discount scenarios, and provides APIs for price and discount management.

## Responsibilities

- Manage base, sale, and MSRP prices for product variants
- Apply and manage discounts (percentage, fixed, promotional, etc.)
- Calculate final prices considering all applicable discounts
- Track price and discount history for auditing
- Enforce business rules for price and discount validity
- Integrate with Product, Inventory, and Order services
- Support price queries, reporting, and analytics
- Publish and consume domain events for price and discount changes
- Ensure data consistency and transactional integrity
- Provide APIs for internal and external consumers

## Main Methods & Workflows

### Service Methods

#### 1. `updatePrice(variantId: string, updatePriceDto: UpdatePriceDto): Promise<ProductPrice>`
- **Description:** Updates the price for a product variant, records price history, and logs the operation.
- **Error Scenarios:**
  - Price not found (404 Not Found)
  - Invalid price data (400 Bad Request)
  - Unauthorized update (403 Forbidden)

#### 2. `applyDiscountToProduct(discountId: string, variantId: string, priority: number): Promise<void>`
- **Description:** Applies a discount to a product variant, validates rules, and logs the operation.
- **Error Scenarios:**
  - Discount or product not found (404 Not Found)
  - Invalid discount rules (400 Bad Request)
  - Overlapping or conflicting discounts (409 Conflict)

#### 3. `calculateFinalPrice(variantId: string): Promise<number>`
- **Description:** Calculates the final price for a product variant, considering all active discounts.
- **Error Scenarios:**
  - Price or discount data not found (404 Not Found)
  - Invalid discount application (400 Bad Request)

#### 4. `getPriceHistory(variantId: string): Promise<PriceHistory[]>`
- **Description:** Retrieves the price history for a product variant.

#### 5. `getActiveDiscounts(variantId: string): Promise<Discount[]>`
- **Description:** Returns all active discounts for a product variant.

#### 6. `createDiscount(createDiscountDto: CreateDiscountDto): Promise<Discount>`
- **Description:** Creates a new discount, validates rules, and logs the operation.
- **Error Scenarios:**
  - Invalid discount data (400 Bad Request)
  - Overlapping or conflicting discounts (409 Conflict)

### Example Workflow: Price Update
1. Validate input data and business rules
2. Retrieve current price for the variant
3. Update price fields (base, sale, MSRP, etc.)
4. Record price history entry
5. Create audit log entry
6. Publish `PriceUpdated` event
7. Return updated price

### Sequence Diagram (Textual)
- Admin → PriceDiscountService: updatePrice()
- PriceDiscountService → PriceRepository: findByProductVariant()
- PriceDiscountService → PriceRepository: update()
- PriceDiscountService → PriceHistoryRepository: create()
- PriceDiscountService → AuditLogger: log('UPDATE')
- PriceDiscountService → EventBus: publish(PriceUpdated)
- PriceDiscountService → Admin: return ProductPrice

## Integration

- **Repositories:**
  - PriceRepository: CRUD and query operations for prices
  - PriceHistoryRepository: Record price changes
  - DiscountRepository: CRUD and query operations for discounts
  - ProductRepository: For variant validation
- **Other Services:**
  - ProductService: For variant validation and linking
  - InventoryService: For price-inventory consistency
  - OrderService: For price validation during checkout
  - AuditLogger: Audit trail for all operations
  - EventBus: Publish/subscribe to price and discount events
- **Events:**
  - Publishes: `PriceUpdated`, `DiscountApplied`, `DiscountExpired`, `PriceHistoryRecorded`
  - Subscribes: Product and inventory changes (if event-driven)
- **External Integrations:**
  - Analytics/Reporting Service: Price and discount analytics
  - Notification Service: Price drop or promotion alerts

## Error Handling & Validation

- **Input Validation:**
  - Use DTOs and class-validator for all input
  - Enforce valid price and discount ranges, types, and dates
- **Business Rule Enforcement:**
  - Base price must be <= MSRP
  - Sale price must be <= base price
  - Discounts must not overlap or conflict
  - Valid discount periods and types
- **Error Handling:**
  - Use custom exceptions for domain errors
  - Return appropriate HTTP status codes
  - Log all errors and failed operations
- **Transactional Integrity:**
  - Use database transactions for multi-step operations
  - Rollback on failure

## Security & Access Control

- **Authentication:**
  - Require JWT or OAuth2 tokens for all operations
- **Authorization:**
  - Enforce RBAC for price and discount management (admin, manager, marketing roles)
- **Audit Logging:**
  - Log all price and discount changes, applications, and expirations
  - Include user context and before/after state
- **Data Protection:**
  - Mask or encrypt sensitive price and discount metadata
  - Validate and sanitize all user input
- **API Security:**
  - Rate limiting on write operations
  - CORS and security headers

## Testing Strategy

- **Unit Tests:**
  - Test all service methods in isolation
  - Mock repositories and external services
  - Cover all business rules and error scenarios
- **Integration Tests:**
  - Test workflows involving multiple services (e.g., price update with product and inventory)
  - Validate event publishing and consumption
- **End-to-End (E2E) Tests:**
  - Test price and discount API endpoints (update, apply, calculate, history)
  - Simulate real user scenarios
- **Test Utilities:**
  - Test factories for price, discount, and product variant creation
  - Database cleanup and seeding scripts
- **Coverage:**
  - Aim for >90% coverage on service logic

## Performance & Scalability

- **Query Optimization:**
  - Use indexes on frequently queried fields (variant, price type, discount status)
  - Optimize discount queries for active periods and priorities
- **Caching:**
  - Cache calculated final prices and active discounts
  - Invalidate cache on updates
- **Bulk Operations:**
  - Support batch price and discount updates and imports
  - Use transactions for bulk changes
- **Horizontal Scaling:**
  - Stateless service design for scaling
  - Use message queues for event-driven workflows

## Example Code Snippet: Final Price Calculation
```typescript
@Injectable()
export class PriceDiscountService {
    constructor(
        private readonly priceRepository: PriceRepository,
        private readonly discountRepository: DiscountRepository,
        private readonly auditLogger: AuditLogger,
        private readonly eventBus: EventBus
    ) {}

    async calculateFinalPrice(variantId: string): Promise<number> {
        const price = await this.priceRepository.findByProductVariant(variantId);
        if (!price) throw new NotFoundException('Price not found');
        const discounts = await this.discountRepository.findProductDiscounts(variantId);
        let finalPrice = price.basePrice;
        for (const discount of discounts) {
            finalPrice = this.applyDiscount(finalPrice, discount);
        }
        return Math.max(finalPrice, 0);
    }

    private applyDiscount(price: number, discount: Discount): number {
        switch (discount.type) {
            case 'percentage':
                return price * (1 - discount.value / 100);
            case 'fixed_amount':
                return price - discount.value;
            default:
                return price;
        }
    }
}
```

## References

- [Price and Discount Models](../02-data-model-setup/02c-price-models.md)
- [Product Service Specification](01-product-service.md)
- [Inventory Integration Specification](03a-inventory-integration.md)
- [Order Service Documentation](../order-service/)
- [Audit Logging](../02-data-model-setup/06-security-considerations.md)
- [Testing Strategy](06-testing-strategy.md)
- [NestJS Service Best Practices](https://docs.nestjs.com/providers)
- [Domain-Driven Design Patterns](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Event-Driven Architecture](https://microservices.io/patterns/data/event-driven-architecture.html) 