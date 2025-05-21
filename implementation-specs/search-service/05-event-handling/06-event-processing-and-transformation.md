# Event Processing and Transformation

## Overview

Once an event is consumed from the message broker (e.g., Kafka), the Search Service must process and transform its payload into a format suitable for updating the relevant Elasticsearch index (products, categories, content, etc.). This involves several steps, from validation and data enrichment to mapping the event data to the target search schema.

## Stages of Event Processing

1.  **Deserialization**: The raw event message (typically JSON) is deserialized into a structured object (e.g., a TypeScript class or interface).
2.  **Validation**: The event payload is validated against a defined schema or set of rules.
    *   **Schema Validation**: Ensure the event structure matches expectations (e.g., using class-validator with DTOs in NestJS, or a formal schema like Avro/JSON Schema if a schema registry is used).
    *   **Business Rule Validation**: Check for required fields, valid data types, and consistency (e.g., a `ProductUpdated` event must contain a `productId`).
3.  **Event Type Identification**: Determine the specific type of event (e.g., `ProductCreated`, `CategoryUpdated`) often based on a dedicated field in the event (`eventType`) or a header.
4.  **Data Transformation/Mapping**: Convert the event data structure to the target Elasticsearch document schema.
    *   **Field Mapping**: Direct mapping of fields (e.g., `event.data.name` to `productDocument.name`).
    *   **Data Conversion**: Type conversions (e.g., string to number, date string to ISO date object).
    *   **Data Enrichment (Optional & Use with Caution)**: Sometimes, the event might not contain all necessary information for the search index. Light enrichment might occur by:
        *   Looking up related data from an internal cache within the Search Service (e.g., enriching a product with full category names if only IDs are in the event).
        *   **Avoid synchronous calls to other services during event processing if possible**, as this introduces latency and coupling, potentially impacting event throughput. If enrichment is essential and not in the event, the source service should ideally include it.
    *   **Computed Fields**: Generating fields for the search index that don't exist in the source event (e.g., a `hasStock: true/false` field based on `stockQuantity`, or a concatenated field for searching).
    *   **Localization Handling**: If the event contains localized data (e.g., product names in multiple languages), transform it into the structure expected by Elasticsearch for multilingual search (e.g., language-specific fields like `name_en`, `name_fr`).
5.  **Idempotency Check (Pre-emptive)**: Before extensive processing, check if this specific event (based on `eventId`) has already been successfully processed to avoid redundant work, especially if at-least-once delivery is guaranteed by the broker and retries are possible.

## Transformation Logic Implementation (NestJS)

Transformation logic is typically encapsulated within dedicated services or mappers.

**Example: Product Event Transformation**

Let's assume `ProductCreated` event and a target `ProductDocument` schema for Elasticsearch.

**Event DTO (Simplified):**
```typescript
// src/events/dto/product-created-event.dto.ts
import { Type } from 'class-transformer';
import { IsString, IsNotEmpty, IsNumber, ValidateNested, IsArray, IsUUID, IsDateString, IsBoolean } from 'class-validator';

class PriceDto {
  @IsNumber()
  amount: number;
  @IsString()
  currency: string;
}

class CategoryReferenceDto {
  @IsString()
  id: string;
  @IsString()
  name: string; // Denormalized for direct use or lookup
}

export class ProductCreatedEventDataDto {
  @IsUUID()
  id: string;

  @IsString()
  @IsNotEmpty()
  name: string;

  @IsString()
  description: string;

  @ValidateNested()
  @Type(() => PriceDto)
  price: PriceDto;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CategoryReferenceDto)
  categories: CategoryReferenceDto[];

  @IsString()
  brandName: string;

  @IsArray()
  @IsString({ each: true })
  tags: string[];

  @IsString()
  imageUrl: string;

  @IsBoolean()
  isActive: boolean;

  @IsDateString()
  createdAt: string;
}

export class ProductCreatedEventDto {
  @IsUUID()
  eventId: string;

  @IsString()
  eventType: 'ProductCreated';

  @IsDateString()
  timestamp: string;

  @ValidateNested()
  @Type(() => ProductCreatedEventDataDto)
  data: ProductCreatedEventDataDto;
}
```

**Elasticsearch Product Document Interface (Simplified):**
```typescript
// src/search/interfaces/product-document.interface.ts
export interface ProductDocument {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  category_ids: string[];
  category_names: string[]; // For faceting/display
  brand: string;
  tags: string[];
  image_url: string;
  is_active: boolean;
  created_at: Date;
  // ... other search-specific fields (e.g., suggestion fields, sortable fields)
}
```

**Transformer Service/Mapper:**
```typescript
// src/search/services/product-event.transformer.ts
import { Injectable } from '@nestjs/common';
import { ProductCreatedEventDataDto } from '../../events/dto/product-created-event.dto';
import { ProductDocument } from '../interfaces/product-document.interface';

@Injectable()
export class ProductEventTransformer {
  transformProductCreated(eventData: ProductCreatedEventDataDto): ProductDocument {
    return {
      id: eventData.id,
      name: eventData.name,
      description: eventData.description,
      price: eventData.price.amount,
      currency: eventData.price.currency,
      category_ids: eventData.categories.map(cat => cat.id),
      category_names: eventData.categories.map(cat => cat.name),
      brand: eventData.brandName,
      tags: eventData.tags,
      image_url: eventData.imageUrl,
      is_active: eventData.isActive,
      created_at: new Date(eventData.createdAt),
      // Add any other transformations or default values for search-specific fields
    };
  }

  // Similar methods for ProductUpdatedEvent, transforming partial or full updates
  // transformProductUpdated(eventData: ProductUpdatedEventDataDto): Partial<ProductDocument> { ... }
}
```

**Event Handler using the Transformer:**
```typescript
// src/events/event-handling.controller.ts (Conceptual)
import { Controller } from '@nestjs/common';
import { EventPattern, Payload } from '@nestjs/microservices';
import { plainToClass } from 'class-transformer';
import { validate } from 'class-validator';
import { ProductCreatedEventDto, ProductCreatedEventDataDto } from './dto/product-created-event.dto';
import { ProductEventTransformer } from '../../search/services/product-event.transformer';
import { IndexingService } from '../../search/services/indexing.service'; // Assumed service for ES operations

@Controller()
export class EventHandlingController {
  constructor(
    private readonly transformer: ProductEventTransformer,
    private readonly indexingService: IndexingService,
  ) {}

  @EventPattern('product.created') // Or @MessagePattern subscribing to a topic
  async handleProductCreated(@Payload() rawEvent: any) {
    const event = plainToClass(ProductCreatedEventDto, rawEvent);
    const errors = await validate(event);

    if (errors.length > 0) {
      console.error('Event validation failed:', errors);
      // Implement error handling: log, send to DLQ, etc.
      return;
    }

    // Idempotency check could happen here or in IndexingService
    // if (await this.indexingService.hasProcessed(event.eventId)) return;

    const productDocument = this.transformer.transformProductCreated(event.data);
    
    try {
      await this.indexingService.indexProduct(productDocument, event.eventId);
    } catch (error) {
      console.error(`Failed to index product ${productDocument.id} from event ${event.eventId}:`, error);
      // Handle indexing errors (retry, DLQ)
      throw error; // Propagate to let NestJS microservice know about failure for retry/DLQ based on config
    }
  }
}
```

## Key Considerations

*   **Statelessness**: Transformers should ideally be stateless, operating only on the input event data.
*   **Performance**: Transformation logic should be efficient, as it's in the critical path of event processing.
*   **Testability**: Mappers and transformers should be easily unit-testable with clear inputs and outputs.
*   **Schema Evolution**: Plan for how changes in event schemas or target search schemas will be managed. Versioning of events and having adaptable transformers are key.
*   **Error Handling during Transformation**: If transformation fails (e.g., due to unexpected data that bypasses initial validation), these events should be routed to a DLQ or logged with sufficient detail for investigation.

## Next Steps

*   `07-index-update-logic.md`: Details how the transformed document is used to update Elasticsearch.
*   `08-error-handling-and-resilience.md`: Expands on handling failures during processing and transformation.
