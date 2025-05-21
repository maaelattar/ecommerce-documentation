# Event Sourcing Operational Considerations

## Overview

This document outlines the operational aspects of managing an event-sourced system in production, with specific focus on the Inventory Service implementation. It covers monitoring, performance optimization, backup strategies, and troubleshooting techniques.

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Event Store Metrics**
   - Event write latency (p50, p95, p99)
   - Event read latency (p50, p95, p99)
   - Event write throughput (events/second)
   - Event store size (total events count and storage size)
   - Failed event persistence count
   - DynamoDB throttling events
   - DynamoDB consumed read/write capacity units

2. **Snapshot Store Metrics**
   - Snapshot creation latency
   - Snapshot retrieval latency
   - Snapshot store size
   - Snapshot creation frequency

3. **Event Processing Metrics**
   - Event processing latency
   - Event processing throughput
   - Failed event processing count
   - Event replay execution time
   - Projection rebuild time

### CloudWatch Dashboards

The primary monitoring dashboard includes:

```
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│                         │ │                         │ │                         │
│   Event Store Writes    │ │   Event Store Reads     │ │   DynamoDB Throttling   │
│                         │ │                         │ │                         │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│                         │ │                         │ │                         │
│   Event Processing      │ │   Snapshot Operations   │ │   Error Rates           │
│                         │ │                         │ │                         │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│                         │ │                         │ │                         │
│   Projection Status     │ │   System Resources      │ │   API Latency           │
│                         │ │                         │ │                         │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

### Alerting Thresholds

| Metric | Warning Threshold | Critical Threshold | Action |
|--------|-------------------|-------------------|--------|
| Event write latency (p95) | > 500ms | > 1s | Investigate capacity, optimize queries |
| Event read latency (p95) | > 200ms | > 500ms | Check indexing, scale read capacity |
| Failed event persistence | > 0 in 5 min | > 10 in 5 min | Check error logs, restore connectivity |
| DynamoDB throttling | > 10 in 5 min | > 50 in 5 min | Increase provisioned capacity |
| Event processing errors | > 5 in 15 min | > 20 in 15 min | Check error logs, restore service |
| Projection rebuild failures | Any | > 3 in 1 hour | Investigate immediately |

## Performance Optimization

### DynamoDB Optimization

1. **Capacity Planning**
   - Use on-demand capacity for unpredictable workloads
   - Use provisioned capacity with auto-scaling for predictable workloads
   - Set appropriate alerts for throttling
   - Consider reserved capacity for cost optimization

2. **Access Patterns**
   - Design partition keys to distribute load evenly
   - Avoid hot partitions by adding random suffixes if needed
   - Use sparse indexes when appropriate
   - Implement batch operations for bulk reads/writes

3. **Query Optimization**
   - Use strongly consistent reads only when necessary
   - Implement pagination for large result sets
   - Use sparse indexes to reduce index size
   - Cache frequently accessed projections

### ElasticSearch Optimization

1. **Index Design**
   - Use time-based index patterns (e.g., `inventory-events-YYYY-MM`)
   - Implement index lifecycle management
   - Use appropriate mappings and analyzers
   - Shard appropriately based on volume

2. **Query Performance**
   - Use filter context instead of query context when possible
   - Implement appropriate caching strategies
   - Consider using scroll API for large result sets
   - Leverage aggregations for analytics

## Backup and Recovery Strategies

### Event Store Backup

1. **DynamoDB Backup**
   - Enable point-in-time recovery (PITR) on the event store table
   - Set up AWS Backup to create daily backups with 90-day retention
   - Store monthly backups in S3 for longer retention (1 year)
   - Schedule regular backup testing exercises

2. **Event Replication**
   - Implement DynamoDB Streams to capture all changes
   - Replicate events to S3 using Lambda
   - Consider cross-region replication for disaster recovery

### Snapshot Store Backup

1. **Regular Snapshots**
   - Back up the snapshot table daily
   - Retain snapshots for 30 days
   - Verify snapshot integrity monthly

2. **Recovery Strategy**
   - Restore snapshot table first during recovery
   - Then restore event store
   - Verify consistency between snapshots and events

### Recovery Procedures

#### Full System Recovery

1. Restore DynamoDB tables from backup
2. Verify snapshot integrity
3. Replay events post last snapshot if needed
4. Rebuild projections
5. Validate system integrity via health checks

#### Partial Recovery (Projection Only)

1. Use the replay functionality to rebuild specific projections
2. Validate projection consistency
3. Switch traffic to new projection when validated

## Handling Schema Evolution

### Event Schema Versioning

The Inventory Service implements a formal versioning strategy for events:

```typescript
interface EventSchema {
  version: number;     // Incremental version number
  deprecated: boolean; // Whether this schema version is deprecated
  schema: any;         // JSON Schema definition of the event
}

// Example usage
const INVENTORY_ITEM_CREATED_SCHEMAS = {
  1: {
    version: 1,
    deprecated: true,
    schema: { /* original schema */ }
  },
  2: {
    version: 2,
    deprecated: false,
    schema: { /* current schema with additional fields */ }
  }
};
```

### Schema Migration Strategy

1. **Backward Compatibility**
   - Always maintain backward compatibility for at least one version
   - Include version number in each event
   - Never remove fields, only add new optional fields

2. **Event Upcasting**
   - Implement event upcasters to convert from old to new schema versions
   - Use a chain of responsibility pattern for multiple version transitions

```typescript
@Injectable()
export class EventUpcaster {
  upcasters: Map<string, EventTypeUpcaster> = new Map();

  constructor() {
    // Register upcasters for each event type
    this.upcasters.set('INVENTORY_ITEM_CREATED', new InventoryItemCreatedUpcaster());
    this.upcasters.set('STOCK_LEVEL_CHANGED', new StockLevelChangedUpcaster());
    // Add more as needed
  }

  upcast(event: RawEvent): DomainEvent {
    const upcaster = this.upcasters.get(event.eventType);
    
    if (!upcaster) {
      return this.convertToCurrentVersion(event);
    }
    
    return upcaster.upcast(event);
  }

  private convertToCurrentVersion(rawEvent: RawEvent): DomainEvent {
    // Default conversion logic
  }
}
```

## Troubleshooting Guide

### Common Issues and Resolutions

| Issue | Symptoms | Troubleshooting Steps | Resolution |
|-------|----------|----------------------|------------|
| DynamoDB Throttling | High latency, failed operations | Check CloudWatch for throttling metrics | Increase provisioned capacity or switch to on-demand |
| Inconsistent Projections | Query results don't match expected state | Check event processing logs, verify last processed event | Rebuild projection from events |
| Missing Events | Aggregate state is incomplete | Verify event store integrity, check for failed persistence | Recover events from backup if needed |
| Snapshot Corruption | Failed to load aggregate from snapshot | Check snapshot integrity, verify serialization | Fall back to full event replay |
| Concurrency Conflicts | Frequent optimistic locking exceptions | Check for high contention on specific aggregates | Implement conflict resolution strategy |

### Debugging Tools

1. **Event Store Explorer**
   - Web-based tool to browse and search events
   - Ability to examine event details and metadata
   - Export events for analysis

2. **Projection Debugger**
   - View current state of projections
   - Compare projection state with expected state
   - Trace projection updates from specific events

3. **Replay Debugger**
   - Step through event replay one event at a time
   - Observe state changes after each event
   - Identify problematic events

## Disaster Recovery Testing

Regular disaster recovery testing is essential:

1. **Quarterly Table Recovery Test**
   - Restore event store and snapshot tables to test environment
   - Verify data integrity
   - Measure recovery time

2. **Bi-annual Full System Recovery Test**
   - Simulate complete service failure
   - Perform full recovery procedure
   - Document recovery time and any issues

3. **Monthly Projection Rebuild Test**
   - Rebuild one projection from events
   - Verify results match production
   - Optimize if performance issues are found

## Security Considerations

1. **Event Data Encryption**
   - Encrypt events at rest using AWS KMS
   - Implement field-level encryption for sensitive data
   - Rotate encryption keys according to security policy

2. **Access Control**
   - Implement fine-grained IAM policies for event store access
   - Audit all administrative operations
   - Use secure authentication for replay and admin APIs

3. **Event Data Compliance**
   - Implement GDPR compliance features
   - Support data anonymization for user-related events
   - Maintain audit trail of data access and modifications