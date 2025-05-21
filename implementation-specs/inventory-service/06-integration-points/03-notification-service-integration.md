# Notification Service Integration

## Overview

The integration between Inventory Service and Notification Service enables automated notifications for critical inventory events. This integration allows stakeholders to be alerted about inventory issues, stock levels, and exceptional conditions that require attention.

## Integration Patterns

The integration primarily uses event-driven communication patterns:

```
┌───────────────────┐                   ┌───────────────────┐
│                   │                   │                   │
│    Inventory      │─── Events ───────▶│   Notification    │
│    Service        │                   │   Service         │
│                   │                   │                   │
└───────────────────┘                   └────────┬──────────┘
                                                 │
                                                 │
                                                 ▼
                                        ┌───────────────────┐
                                        │                   │
                                        │ Email, SMS, Push  │
                                        │ Notifications     │
                                        │                   │
                                        └───────────────────┘
```

## Event-Driven Integration

### Events Published by Inventory Service

These events trigger notifications to appropriate stakeholders.

1. **LowStockThresholdReachedEvent**
   - **Purpose**: Alerts inventory managers when an item falls below its reorder threshold
   - **Consumer Action**: Notification Service sends alerts to purchasing department
   - **Exchange**: `inventory.notifications`
   - **Routing Key**: `inventory.lowstockthresholdreached.inventoryitem`

   ```typescript
   // Example payload
   {
     "eventId": "e1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
     "eventType": "LowStockThresholdReached",
     "eventVersion": "1.0.0",
     "aggregateId": "inv_01GXYZ234DEF",
     "aggregateType": "InventoryItem",
     "timestamp": "2023-05-15T09:30:00Z",
     "metadata": {
       "source": "inventory-service",
       "severity": "WARNING"
     },
     "payload": {
       "inventoryItemId": "inv_01GXYZ234DEF",
       "sku": "WIDGET-2",
       "productId": "prod_01FXYZ789ABC",
       "name": "Widget Deluxe Plus",
       "warehouseId": "wh_01HXYZ789GHI",
       "currentQuantity": 5,
       "reorderThreshold": 10,
       "targetStockLevel": 75,
       "suggestedOrderQuantity": 70,
       "thresholdPercentage": 50,
       "estimatedDaysUntilStockout": 3
     }
   }
   ```

2. **OutOfStockEvent**
   - **Purpose**: Alerts inventory and product managers when an item is out of stock
   - **Consumer Action**: Notification Service sends high-priority alerts to inventory managers and product managers
   - **Exchange**: `inventory.notifications`
   - **Routing Key**: `inventory.outofstock.inventoryitem`

3. **StockReplenishedEvent**
   - **Purpose**: Notifies when stock has been replenished for previously low/out-of-stock items
   - **Consumer Action**: Notification Service sends informational alerts to inventory managers
   - **Exchange**: `inventory.notifications`
   - **Routing Key**: `inventory.stockreplenished.inventoryitem`

4. **AllocationFailedEvent**
   - **Purpose**: Alerts when an order cannot be allocated due to inventory issues
   - **Consumer Action**: Notification Service sends alerts to order fulfillment team
   - **Exchange**: `inventory.notifications`
   - **Routing Key**: `inventory.allocationfailed.allocation`

5. **InventoryDiscrepancyEvent**
   - **Purpose**: Alerts when a significant discrepancy is found during cycle counts
   - **Consumer Action**: Notification Service sends alerts to inventory managers and loss prevention
   - **Exchange**: `inventory.notifications`
   - **Routing Key**: `inventory.inventorydiscrepancy.inventoryitem`

## Notification Types and Recipients

The Notification Service creates different types of notifications based on inventory events:

1. **Low Stock Notification**
   - **Recipients**: Purchasing team, inventory managers
   - **Channels**: Email, dashboard alert
   - **Severity**: Warning
   - **Content**: Item details, current quantity, reorder threshold, suggested order quantity
   - **Actions**: "Create Purchase Order" link

2. **Out of Stock Notification**
   - **Recipients**: Purchasing team, inventory managers, product managers
   - **Channels**: Email, SMS (for critical items), dashboard alert
   - **Severity**: Critical
   - **Content**: Item details, last transaction details, pending orders affected
   - **Actions**: "Create Emergency PO" link, "View Affected Orders" link

3. **Stock Replenished Notification**
   - **Recipients**: Inventory managers
   - **Channels**: Dashboard alert
   - **Severity**: Info
   - **Content**: Item details, new stock level, days out of stock
   - **Actions**: "View Inventory Details" link

4. **Allocation Failed Notification**
   - **Recipients**: Order fulfillment team, inventory managers
   - **Channels**: Email, dashboard alert
   - **Severity**: High
   - **Content**: Order details, affected item details, reason for failure
   - **Actions**: "View Order" link, "Check Inventory" link

5. **Inventory Discrepancy Notification**
   - **Recipients**: Inventory managers, loss prevention team
   - **Channels**: Email, dashboard alert
   - **Severity**: High
   - **Content**: Item details, expected quantity, actual quantity, variance amount and percentage
   - **Actions**: "View Inventory Transactions" link, "Create Investigation" link

## Implementation Details

### Event Handler in Notification Service

```typescript
@Injectable()
export class InventoryNotificationHandler {
  constructor(
    private readonly notificationService: NotificationService,
    private readonly userService: UserService,
    private readonly configService: ConfigService,
    private readonly logger: Logger
  ) {}

  @EventPattern('inventory.lowstockthresholdreached.inventoryitem')
  async handleLowStockThresholdReached(data: LowStockThresholdReachedEvent): Promise<void> {
    this.logger.log(`Processing low stock notification for ${data.payload.sku}`);
    
    try {
      // Get recipients from configuration
      const recipientRoles = this.configService.get<string[]>('notifications.lowStock.recipientRoles', ['purchasing', 'inventory-manager']);
      const recipients = await this.userService.getUsersByRoles(recipientRoles);
      
      // Create notification content
      const notification: NotificationDto = {
        type: 'LOW_STOCK',
        severity: 'WARNING',
        title: `Low Stock Alert: ${data.payload.name} (${data.payload.sku})`,
        content: `
          Item ${data.payload.name} (SKU: ${data.payload.sku}) is running low on stock.
          Current quantity: ${data.payload.currentQuantity}
          Reorder threshold: ${data.payload.reorderThreshold}
          Suggested order quantity: ${data.payload.suggestedOrderQuantity}
          Estimated days until stockout: ${data.payload.estimatedDaysUntilStockout}
        `,
        metadata: {
          inventoryItemId: data.payload.inventoryItemId,
          productId: data.payload.productId,
          sku: data.payload.sku,
          warehouseId: data.payload.warehouseId
        },
        actions: [
          {
            label: 'Create Purchase Order',
            url: `/purchasing/create-po?productId=${data.payload.productId}&suggestedQuantity=${data.payload.suggestedOrderQuantity}`,
            primary: true
          },
          {
            label: 'View Inventory Details',
            url: `/inventory/items/${data.payload.inventoryItemId}`
          }
        ]
      };
      
      // Send notification to all recipients
      for (const recipient of recipients) {
        await this.notificationService.sendNotification(recipient.id, notification, ['email', 'dashboard']);
      }
      
      this.logger.log(`Low stock notification sent to ${recipients.length} recipients for ${data.payload.sku}`);
    } catch (error) {
      this.logger.error(`Failed to process low stock notification for ${data.payload.sku}`, error);
    }
  }

  @EventPattern('inventory.outofstock.inventoryitem')
  async handleOutOfStock(data: OutOfStockEvent): Promise<void> {
    // Similar implementation for out of stock notifications
    // With higher severity and additional channels like SMS
  }

  // Additional handlers for other inventory events...
}
```

### Notification Configuration

The Notification Service maintains configuration for different inventory notification types:

```typescript
// notification-config.service.ts
@Injectable()
export class NotificationConfigService {
  constructor(
    @InjectRepository(NotificationConfig)
    private readonly notificationConfigRepository: Repository<NotificationConfig>,
    private readonly logger: Logger
  ) {}
  
  async getNotificationConfig(type: string): Promise<NotificationConfig> {
    const config = await this.notificationConfigRepository.findOne({ where: { type } });
    
    if (!config) {
      this.logger.warn(`No configuration found for notification type: ${type}`);
      return this.getDefaultConfig(type);
    }
    
    return config;
  }
  
  private getDefaultConfig(type: string): NotificationConfig {
    // Default configurations for inventory notifications
    switch (type) {
      case 'LOW_STOCK':
        return {
          type: 'LOW_STOCK',
          enabled: true,
          recipientRoles: ['purchasing', 'inventory-manager'],
          channels: ['email', 'dashboard'],
          throttleSeconds: 86400, // Once per day for the same item
          templates: {
            email: 'low-stock-email',
            sms: 'low-stock-sms',
            push: 'low-stock-push',
            dashboard: 'low-stock-dashboard'
          }
        };
      
      case 'OUT_OF_STOCK':
        return {
          type: 'OUT_OF_STOCK',
          enabled: true,
          recipientRoles: ['purchasing', 'inventory-manager', 'product-manager'],
          channels: ['email', 'sms', 'dashboard'],
          throttleSeconds: 0, // No throttling for out of stock
          templates: {
            email: 'out-of-stock-email',
            sms: 'out-of-stock-sms',
            push: 'out-of-stock-push',
            dashboard: 'out-of-stock-dashboard'
          }
        };
      
      // Additional default configs...
      
      default:
        return {
          type,
          enabled: true,
          recipientRoles: ['inventory-manager'],
          channels: ['dashboard'],
          throttleSeconds: 3600,
          templates: {
            email: 'default-email',
            dashboard: 'default-dashboard'
          }
        };
    }
  }
}
```

## Notification Templates

The Notification Service uses customizable templates for different channels:

### Email Template Example (Low Stock)

```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background-color: #f8cb4a; color: #333; padding: 20px; text-align: center;">
    <h1>Low Stock Alert</h1>
  </div>
  <div style="padding: 20px;">
    <p>Hello {{recipientName}},</p>
    
    <p>This is to inform you that the following item is running low on stock:</p>
    
    <div style="background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-left: 4px solid #f8cb4a;">
      <p><strong>Item:</strong> {{itemName}} (SKU: {{sku}})</p>
      <p><strong>Current Quantity:</strong> {{currentQuantity}}</p>
      <p><strong>Reorder Threshold:</strong> {{reorderThreshold}}</p>
      <p><strong>Warehouse:</strong> {{warehouseName}}</p>
      <p><strong>Suggested Order Quantity:</strong> {{suggestedOrderQuantity}}</p>
      <p><strong>Estimated Days Until Stockout:</strong> {{estimatedDaysUntilStockout}}</p>
    </div>
    
    <p>Please take appropriate action to replenish this item.</p>
    
    <div style="text-align: center; margin-top: 20px;">
      <a href="{{createPurchaseOrderUrl}}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-right: 10px;">Create Purchase Order</a>
      <a href="{{viewInventoryUrl}}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Inventory Details</a>
    </div>
    
    <p style="margin-top: 30px; font-size: 12px; color: #777;">
      This is an automated notification from the {{companyName}} Inventory Management System.
      If you no longer wish to receive these alerts, please update your notification preferences in your account settings.
    </p>
  </div>
</div>
```

### SMS Template Example (Out of Stock)

```
URGENT: {{itemName}} ({{sku}}) is OUT OF STOCK at {{warehouseName}}. {{pendingAllocations}} pending orders affected. Visit {{shortUrl}} for details.
```

## Notification Throttling and Aggregation

To prevent notification fatigue, the system implements:

1. **Throttling**
   - Configurable time-based throttling per item and notification type
   - Prevents repeated notifications for the same condition

2. **Aggregation**
   - Combines multiple low-stock notifications into a single digest
   - Daily summary emails with all items requiring attention

```typescript
@Injectable()
export class NotificationThrottlingService {
  constructor(
    @InjectRepository(NotificationHistory)
    private readonly notificationHistoryRepository: Repository<NotificationHistory>,
    private readonly configService: ConfigService,
    private readonly logger: Logger
  ) {}
  
  async shouldThrottleNotification(
    type: string,
    entityId: string,
    recipientId: string
  ): Promise<boolean> {
    // Get throttle time from config
    const config = await this.notificationConfigService.getNotificationConfig(type);
    const throttleSeconds = config.throttleSeconds;
    
    // If throttling is disabled, always allow
    if (throttleSeconds <= 0) {
      return false;
    }
    
    // Check for recent notifications of the same type for the same entity and recipient
    const cutoffTime = new Date();
    cutoffTime.setSeconds(cutoffTime.getSeconds() - throttleSeconds);
    
    const recentNotification = await this.notificationHistoryRepository.findOne({
      where: {
        notificationType: type,
        entityId: entityId,
        recipientId: recipientId,
        createdAt: MoreThan(cutoffTime)
      }
    });
    
    return !!recentNotification;
  }
  
  async recordNotification(
    type: string,
    entityId: string,
    recipientId: string
  ): Promise<void> {
    await this.notificationHistoryRepository.save({
      notificationType: type,
      entityId: entityId,
      recipientId: recipientId,
      createdAt: new Date()
    });
  }
}
```

## Notification Delivery Tracking

The Notification Service tracks delivery and engagement metrics:

1. **Delivery Status**
   - Tracks if notifications were successfully delivered on each channel
   - Records delivery timestamps and error information

2. **Engagement Tracking**
   - Tracks if notifications were viewed, clicked, or acted upon
   - Used to improve notification effectiveness

```typescript
@Entity('notification_delivery')
export class NotificationDelivery {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  notificationId: string;

  @Column()
  recipientId: string;

  @Column()
  channel: string; // email, sms, push, dashboard

  @Column({
    type: 'enum',
    enum: DeliveryStatus,
    default: DeliveryStatus.PENDING
  })
  status: DeliveryStatus;

  @Column({ nullable: true })
  deliveredAt: Date;

  @Column({ nullable: true })
  errorMessage: string;

  @Column({ default: false })
  viewed: boolean;

  @Column({ nullable: true })
  viewedAt: Date;

  @Column({ default: false })
  clicked: boolean;

  @Column({ nullable: true })
  clickedAt: Date;

  @Column({ nullable: true })
  clickedAction: string;
}

enum DeliveryStatus {
  PENDING = 'PENDING',
  DELIVERED = 'DELIVERED',
  FAILED = 'FAILED'
}
```

## Notification Preferences

Users can configure their notification preferences for inventory events:

1. **Channel Preferences**
   - Which channels to use for different notification types
   - Time-of-day restrictions for certain channels

2. **Severity Thresholds**
   - Minimum severity level for notifications
   - Option to only receive critical notifications

```typescript
@Entity('notification_preferences')
export class NotificationPreferences {
  @PrimaryColumn()
  userId: string;

  @Column('json')
  channelPreferences: {
    [notificationType: string]: string[] // Array of enabled channels
  };

  @Column('json')
  severityThresholds: {
    email: NotificationSeverity;
    sms: NotificationSeverity;
    push: NotificationSeverity;
    dashboard: NotificationSeverity;
  };

  @Column('json')
  timeRestrictions: {
    email?: { start: string; end: string; timezone: string };
    sms?: { start: string; end: string; timezone: string };
    push?: { start: string; end: string; timezone: string };
  };

  @Column('json')
  disabledNotifications: string[]; // Array of disabled notification types
}

enum NotificationSeverity {
  INFO = 'INFO',
  WARNING = 'WARNING',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}
```

## Error Handling

1. **Failed Delivery Handling**
   - Retry logic for failed notification delivery
   - Fallback channels when primary channel fails

2. **Event Processing Errors**
   - Dead letter queues for failed event processing
   - Administrative interface to review and reprocess

## Monitoring and Observability

1. **Notification Metrics**
   - Delivery success rates by channel
   - Notification volumes by type
   - User engagement metrics

2. **SLA Monitoring**
   - Time from event to notification delivery
   - Error rates and retry statistics