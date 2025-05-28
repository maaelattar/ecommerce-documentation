# Tutorial 5: REST API Implementation

## 🎯 Objective
Build complete REST API with validation, error handling, and Swagger documentation.

## Step 1: DTOs for Validation

**src/modules/products/dto/create-product.dto.ts:**
```typescript
import { IsString, IsNumber, IsOptional, IsArray, IsUUID, Min } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateProductDto {
  @ApiProperty()
  @IsString()
  name: string;

  @ApiProperty()
  @IsString()
  slug: string;

  @ApiProperty()
  @IsString()
  description: string;

  @ApiProperty()
  @IsNumber()
  @Min(0)
  basePrice: number;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsArray()
  images?: string[];

  @ApiProperty()
  @IsUUID()
  categoryId: string;
}
```

## Step 2: Complete Product Controller

**src/modules/products/controllers/product.controller.ts:**
```typescript
import { Controller, Get, Post, Body, Patch, Param, Delete, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { JwtAuthGuard, RolesGuard, Roles } from '@ecommerce/auth-client-utils';
import { ProductService } from '../services/product.service';

@ApiTags('products')
@Controller('products')
export class ProductController {
  constructor(private readonly productService: ProductService) {}

  @Get()
  @ApiOperation({ summary: 'Get all products' })
  findAll(@Query('page') page = 1, @Query('limit') limit = 10) {
    return this.productService.findAll(page, limit);
  }

  @Post()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create product (Admin only)' })
  create(@Body() createProductDto: CreateProductDto) {
    return this.productService.create(createProductDto);
  }
}
```

> 💡 **Learning Note**: Notice we're implementing basic CRUD operations here. As your product catalog grows, you'll want advanced features like:
> - Full-text search across product descriptions
> - Filter by multiple attributes (color=red AND size=M)  
> - Category-based navigation with faceted search
> - Price range queries with sorting
> 
> PostgreSQL can handle these with complex SQL and JSONB operators, but it gets messy. MongoDB's native query operators and text search would make these features much more elegant. Keep this in mind as we add search in Tutorial 7!

## ✅ Next Step
Continue with **[06-event-publishing.md](./06-event-publishing.md)** for events.