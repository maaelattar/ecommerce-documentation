# API Endpoints - Search Service with Shared Libraries

## 🎯 Objective
Build comprehensive search API endpoints using shared authentication and validation utilities.

## 🔍 SearchController Implementation

```typescript
// src/search/search.controller.ts
import { Controller, Get, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiBearerAuth } from '@nestjs/swagger';

// Import shared utilities
import { JwtAuthGuard } from '@ecommerce/auth-client-utils';
import { LoggerService } from '@ecommerce/nestjs-core-utils';

import { SearchService } from './search.service';
import { SearchProductsDto } from './dto/search-products.dto';

@ApiTags('search')
@Controller('search')
export class SearchController {
  constructor(
    private readonly searchService: SearchService,
    private readonly logger: LoggerService,
  ) {}

  @Get('products')
  @ApiOperation({ summary: 'Search products with filters and facets' })
  @ApiQuery({ name: 'q', required: false, description: 'Search query' })
  @ApiQuery({ name: 'category', required: false, description: 'Filter by category' })
  @ApiQuery({ name: 'brand', required: false, description: 'Filter by brand' })
  @ApiQuery({ name: 'minPrice', required: false, type: Number })
  @ApiQuery({ name: 'maxPrice', required: false, type: Number })
  @ApiQuery({ name: 'inStock', required: false, type: Boolean })
  @ApiQuery({ name: 'sortBy', required: false, enum: ['relevance', 'price', 'rating', 'name', 'newest'] })
  @ApiQuery({ name: 'sortOrder', required: false, enum: ['asc', 'desc'] })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  async searchProducts(@Query() searchDto: SearchProductsDto) {
    this.logger.log('Product search request', 'SearchController', {
      query: searchDto.q,
      filters: searchDto.filters,
      page: searchDto.page,
      limit: searchDto.limit,
    });

    return await this.searchService.searchProducts(searchDto);
  }

  @Get('suggestions')
  @ApiOperation({ summary: 'Get search suggestions/autocomplete' })
  @ApiQuery({ name: 'q', required: true, description: 'Partial query for suggestions' })
  @ApiQuery({ name: 'limit', required: false, type: Number, description: 'Max suggestions to return' })
  async getSearchSuggestions(
    @Query('q') query: string,
    @Query('limit') limit?: number,
  ) {
    this.logger.log('Search suggestions request', 'SearchController', {
      query,
      limit,
    });

    return {
      suggestions: await this.searchService.getSearchSuggestions(query, limit),
    };
  }

  @Get('facets')
  @ApiOperation({ summary: 'Get search facets for filtering' })
  async getSearchFacets(@Query() searchDto: SearchProductsDto) {
    this.logger.log('Search facets request', 'SearchController', {
      baseQuery: searchDto.q,
      baseFilters: searchDto.filters,
    });

    return await this.searchService.getFacets(searchDto);
  }

  @Get('analytics')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get search analytics (admin only)' })
  async getSearchAnalytics() {
    // TODO: Implement search analytics
    return {
      message: 'Search analytics endpoint - to be implemented',
    };
  }
}
```

## 📊 DTOs and Validation

```typescript
// src/search/dto/search-products.dto.ts
import { IsOptional, IsString, IsNumber, IsBoolean, IsEnum, Min, Max } from 'class-validator';
import { Transform, Type } from 'class-transformer';
import { ApiProperty } from '@nestjs/swagger';

export class SearchFiltersDto {
  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  category?: string;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  brand?: string;

  @ApiProperty({ required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  minPrice?: number;

  @ApiProperty({ required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  maxPrice?: number;

  @ApiProperty({ required: false })
  @IsOptional()
  @Transform(({ value }) => value === 'true')
  @IsBoolean()
  inStock?: boolean;
}

export class SearchProductsDto {
  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  q?: string;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsEnum(['relevance', 'price', 'rating', 'name', 'newest'])
  sortBy?: 'relevance' | 'price' | 'rating' | 'name' | 'newest';

  @ApiProperty({ required: false })
  @IsOptional()
  @IsEnum(['asc', 'desc'])
  sortOrder?: 'asc' | 'desc';

  @ApiProperty({ required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(1)
  page?: number = 1;

  @ApiProperty({ required: false })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(1)
  @Max(100)
  limit?: number = 20;

  @ApiProperty({ type: SearchFiltersDto, required: false })
  @IsOptional()
  filters?: SearchFiltersDto;
}
```

```typescript
// src/search/dto/search-result.dto.ts
import { ApiProperty } from '@nestjs/swagger';

export class ProductSearchResultDto {
  @ApiProperty()
  id: string;

  @ApiProperty()
  name: string;

  @ApiProperty()
  description: string;

  @ApiProperty()
  price: number;

  @ApiProperty()
  category: {
    id: string;
    name: string;
    path: string;
  };

  @ApiProperty()
  brand: string;

  @ApiProperty()
  tags: string[];

  @ApiProperty()
  availability: {
    inStock: boolean;
    quantity: number;
  };

  @ApiProperty()
  ratings: {
    average: number;
    count: number;
  };

  @ApiProperty()
  seller: {
    id: string;
    name: string;
  };

  @ApiProperty()
  score: number;

  @ApiProperty()
  createdAt: Date;

  @ApiProperty()
  updatedAt: Date;
}

export class SearchResultDto {
  @ApiProperty({ type: [ProductSearchResultDto] })
  products: ProductSearchResultDto[];

  @ApiProperty()
  total: number;

  @ApiProperty()
  page: number;

  @ApiProperty()
  totalPages: number;

  @ApiProperty()
  took: number;
}
```

## 🚀 Search Module

```typescript
// src/search/search.module.ts
import { Module } from '@nestjs/common';
import { ElasticsearchModule } from '../elasticsearch/elasticsearch.module';

import { SearchController } from './search.controller';
import { SearchService } from './search.service';
import { IndexManagementService } from '../elasticsearch/index-management.service';

@Module({
  imports: [ElasticsearchModule],
  controllers: [SearchController],
  providers: [SearchService, IndexManagementService],
  exports: [SearchService],
})
export class SearchModule {}
```