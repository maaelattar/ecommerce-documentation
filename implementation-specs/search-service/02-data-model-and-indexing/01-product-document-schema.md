# Product Document Schema

## Overview

The product document schema defines the structure and fields for product documents in the Elasticsearch index. This schema is designed to support comprehensive product search, faceted navigation, and relevance tuning while optimizing for search performance.

## Schema Structure

```json
{
  "id": "string",                     // Unique product identifier
  "sku": "string",                    // Stock keeping unit
  "name": "string",                   // Product name
  "description": "text",              // Full product description
  "short_description": "text",        // Abbreviated description for listings
  "slug": "string",                   // URL-friendly identifier
  "status": "string",                 // Product status (active, inactive, discontinued)
  "visibility": "string",             // Product visibility (visible, hidden, search_only)
  "created_at": "date",               // Creation timestamp
  "updated_at": "date",               // Last update timestamp
  "published_at": "date",             // When product was made public
  "type": "string",                   // Product type (simple, configurable, bundle, etc.)
  
  "categories": [                     // Categories the product belongs to
    {
      "id": "string",                 // Category ID
      "name": "string",               // Category name
      "path": "string",               // Full category path
      "level": "integer",             // Depth in category hierarchy
      "position": "integer"           // Position within category
    }
  ],
  
  "brand": {                          // Brand information
    "id": "string",                   // Brand ID
    "name": "string",                 // Brand name
    "logo_url": "string"              // Brand logo URL
  },
  
  "pricing": {                        // Pricing information
    "currency": "string",             // Currency code
    "list_price": "float",            // Regular price
    "sale_price": "float",            // Discounted price if on sale
    "sale_price_effective_date": {    // Date range for sale price
      "from": "date",
      "to": "date"
    },
    "price_range": {                  // For configurable products
      "min_price": "float",
      "max_price": "float"
    },
    "tax_class": "string",            // Tax classification
    "tax_rate": "float"               // Applicable tax rate
  },
  
  "inventory": {                      // Inventory information
    "in_stock": "boolean",            // Whether product is in stock
    "quantity": "integer",            // Available quantity
    "availability": "string",         // Availability status
    "threshold": "integer"            // Low stock threshold
  },
  
  "attributes": {                     // Product attributes
    "color": "string",                // Example: color attribute
    "size": "string",                 // Example: size attribute
    "material": "string",             // Example: material attribute
    "weight": "float",                // Example: weight attribute
    "dimensions": {                   // Example: dimensions attribute
      "length": "float",
      "width": "float",
      "height": "float",
      "unit": "string"
    },
    "custom_attributes": [            // Dynamic custom attributes
      {
        "code": "string",             // Attribute code
        "label": "string",            // Display label
        "value": "any",               // Attribute value
        "value_text": "string",       // Searchable text representation
        "filterable": "boolean",      // Whether used in faceted navigation
        "searchable": "boolean"       // Whether searchable
      }
    ]
  },
  
  "variants": [                       // For configurable products
    {
      "id": "string",                 // Variant ID
      "sku": "string",                // Variant SKU
      "attributes": {                 // Variant-specific attributes
        "color": "string",
        "size": "string"
      },
      "pricing": {                    // Variant-specific pricing
        "list_price": "float",
        "sale_price": "float"
      },
      "inventory": {                  // Variant-specific inventory
        "in_stock": "boolean",
        "quantity": "integer"
      }
    }
  ],
  
  "media": {                          // Product media
    "thumbnail": "string",            // Thumbnail image URL
    "images": [                       // Product images
      {
        "url": "string",              // Image URL
        "alt": "string",              // Alt text
        "position": "integer",        // Display order
        "type": "string"              // Image type (main, alternate, swatch)
      }
    ],
    "videos": [                       // Product videos
      {
        "url": "string",              // Video URL
        "thumbnail": "string",        // Video thumbnail
        "title": "string",            // Video title
        "description": "string"       // Video description
      }
    ]
  },
  
  "seo": {                            // SEO metadata
    "title": "string",                // SEO title
    "description": "string",          // Meta description
    "keywords": [                     // Meta keywords
      "string"
    ],
    "canonical_url": "string",        // Canonical URL
    "structured_data": "object"       // JSON-LD structured data
  },
  
  "ratings": {                        // Product ratings
    "average": "float",               // Average rating (1-5)
    "count": "integer",               // Number of ratings
    "distribution": {                 // Distribution of ratings
      "1": "integer",
      "2": "integer",
      "3": "integer",
      "4": "integer",
      "5": "integer"
    }
  },
  
  "shipping": {                       // Shipping information
    "weight": "float",                // Shipping weight
    "weight_unit": "string",          // Weight unit
    "dimensions": {                   // Shipping dimensions
      "length": "float",
      "width": "float",
      "height": "float",
      "unit": "string"
    },
    "free_shipping": "boolean",       // Whether eligible for free shipping
    "shipping_class": "string"        // Shipping class
  },
  
  "tags": [                           // Product tags
    "string"
  ],
  
  "related_products": [               // Related product IDs
    "string"
  ],
  
  "cross_sell_products": [            // Cross-sell product IDs
    "string"
  ],
  
  "upsell_products": [                // Upsell product IDs
    "string"
  ],
  
  "search_data": {                    // Additional search-specific fields
    "search_keywords": [              // Additional search keywords
      "string"
    ],
    "search_boost": "float",          // Manual relevance boost
    "popularity_score": "float",      // Calculated popularity score
    "conversion_rate": "float",       // Historical conversion rate
    "view_count": "integer",          // Number of product views
    "sale_count": "integer"           // Number of sales
  },
  
  "metadata": {                       // Miscellaneous metadata
    "created_by": "string",           // User who created the product
    "updated_by": "string",           // User who last updated the product
    "version": "integer",             // Document version
    "tenant_id": "string"             // Multi-tenant identifier
  }
}
```

## Field Descriptions

### Core Fields

- **id**: Unique identifier for the product, typically a UUID
- **sku**: Stock keeping unit, a unique identifier used for inventory tracking
- **name**: The product's display name
- **description**: Complete product description with HTML markup
- **short_description**: A condensed version of the description for listing pages
- **slug**: URL-friendly version of the product name
- **status**: Current product status (active, inactive, discontinued)
- **visibility**: Controls where the product appears (visible, hidden, search_only)
- **type**: Product type (simple, configurable, bundle, virtual, downloadable)

### Category Fields

- **categories**: Array of categories the product belongs to
  - **id**: Category identifier
  - **name**: Category name
  - **path**: Full hierarchical path (e.g., "Electronics/Computers/Laptops")
  - **level**: Depth in category tree (root = 0)
  - **position**: Sort order within the category

### Brand Fields

- **brand**: Brand information
  - **id**: Brand identifier
  - **name**: Brand name
  - **logo_url**: URL to brand logo image

### Pricing Fields

- **pricing**: Contains all price-related information
  - **currency**: ISO currency code (e.g., "USD")
  - **list_price**: Regular product price
  - **sale_price**: Discounted price if applicable
  - **sale_price_effective_date**: Date range for when sale price is valid
  - **price_range**: For products with multiple variants or options
  - **tax_class**: Tax classification
  - **tax_rate**: Applicable tax rate percentage

### Inventory Fields

- **inventory**: Stock and availability information
  - **in_stock**: Boolean indicating whether the product is in stock
  - **quantity**: Available quantity
  - **availability**: More specific availability status (in_stock, out_of_stock, backorder, preorder)
  - **threshold**: Quantity at which low stock notification is triggered

### Attribute Fields

- **attributes**: Product characteristics
  - Common attributes like color, size, material
  - **custom_attributes**: Array of dynamic attributes
    - **code**: Attribute identifier
    - **label**: Human-readable name
    - **value**: The attribute value
    - **value_text**: Searchable text representation of the value
    - **filterable**: Whether the attribute can be used in faceted navigation
    - **searchable**: Whether the attribute is included in search

### Media Fields

- **media**: Product images and videos
  - **thumbnail**: Main thumbnail image URL
  - **images**: Array of product images with metadata
  - **videos**: Array of product videos with metadata

### SEO Fields

- **seo**: Search engine optimization data
  - **title**: Custom title tag
  - **description**: Meta description
  - **keywords**: Meta keywords
  - **canonical_url**: Canonical URL to prevent duplicate content issues
  - **structured_data**: JSON-LD structured data for rich snippets

### Search-specific Fields

- **search_data**: Fields that enhance search capability
  - **search_keywords**: Additional terms to match in searches
  - **search_boost**: Manual adjustment to search relevance
  - **popularity_score**: Calculated score based on views, sales, etc.
  - **conversion_rate**: Historical conversion rate for the product
  - **view_count**: Number of product page views
  - **sale_count**: Number of units sold

## Sample Product Document

```json
{
  "id": "prod-12345",
  "sku": "LP-2023-BLU-M",
  "name": "Premium Denim Slim Fit Jeans",
  "description": "<p>Our premium denim jeans feature a slim fit design with...</p>",
  "short_description": "Premium slim fit jeans in stonewashed denim",
  "slug": "premium-denim-slim-fit-jeans",
  "status": "active",
  "visibility": "visible",
  "created_at": "2023-05-15T10:30:00Z",
  "updated_at": "2023-10-01T14:22:00Z",
  "published_at": "2023-05-20T08:00:00Z",
  "type": "configurable",
  
  "categories": [
    {
      "id": "cat-101",
      "name": "Men's Jeans",
      "path": "Clothing/Men's/Jeans",
      "level": 2,
      "position": 3
    },
    {
      "id": "cat-158",
      "name": "New Arrivals",
      "path": "New Arrivals",
      "level": 0,
      "position": 1
    }
  ],
  
  "brand": {
    "id": "brand-42",
    "name": "LuxuryDenim",
    "logo_url": "https://assets.example.com/brands/luxurydenim.png"
  },
  
  "pricing": {
    "currency": "USD",
    "list_price": 89.99,
    "sale_price": 69.99,
    "sale_price_effective_date": {
      "from": "2023-10-01T00:00:00Z",
      "to": "2023-10-31T23:59:59Z"
    },
    "price_range": {
      "min_price": 69.99,
      "max_price": 69.99
    },
    "tax_class": "clothing",
    "tax_rate": 8.25
  },
  
  "inventory": {
    "in_stock": true,
    "quantity": 250,
    "availability": "in_stock",
    "threshold": 25
  },
  
  "attributes": {
    "color": "blue",
    "material": "98% cotton, 2% elastane",
    "weight": 0.8,
    "custom_attributes": [
      {
        "code": "fit",
        "label": "Fit",
        "value": "slim",
        "value_text": "Slim Fit",
        "filterable": true,
        "searchable": true
      },
      {
        "code": "rise",
        "label": "Rise",
        "value": "mid",
        "value_text": "Mid Rise",
        "filterable": true,
        "searchable": true
      }
    ]
  },
  
  "variants": [
    {
      "id": "var-12345-s",
      "sku": "LP-2023-BLU-S",
      "attributes": {
        "size": "S"
      },
      "pricing": {
        "list_price": 89.99,
        "sale_price": 69.99
      },
      "inventory": {
        "in_stock": true,
        "quantity": 45
      }
    },
    {
      "id": "var-12345-m",
      "sku": "LP-2023-BLU-M",
      "attributes": {
        "size": "M"
      },
      "pricing": {
        "list_price": 89.99,
        "sale_price": 69.99
      },
      "inventory": {
        "in_stock": true,
        "quantity": 78
      }
    }
  ],
  
  "media": {
    "thumbnail": "https://assets.example.com/products/LP-2023-BLU/thumbnail.jpg",
    "images": [
      {
        "url": "https://assets.example.com/products/LP-2023-BLU/main.jpg",
        "alt": "Premium Denim Slim Fit Jeans - Front View",
        "position": 1,
        "type": "main"
      },
      {
        "url": "https://assets.example.com/products/LP-2023-BLU/back.jpg",
        "alt": "Premium Denim Slim Fit Jeans - Back View",
        "position": 2,
        "type": "alternate"
      }
    ]
  },
  
  "seo": {
    "title": "Premium Denim Slim Fit Jeans | LuxuryDenim | Example Store",
    "description": "Shop our premium slim fit jeans in stonewashed denim. Comfortable, stylish, and durable for everyday wear.",
    "keywords": ["slim fit jeans", "premium denim", "men's jeans", "LuxuryDenim"],
    "canonical_url": "https://www.example.com/products/premium-denim-slim-fit-jeans"
  },
  
  "ratings": {
    "average": 4.7,
    "count": 142,
    "distribution": {
      "1": 2,
      "2": 3,
      "3": 9,
      "4": 30,
      "5": 98
    }
  },
  
  "tags": [
    "bestseller",
    "featured",
    "premium"
  ],
  
  "search_data": {
    "search_keywords": [
      "denim pants",
      "blue jeans",
      "men's pants"
    ],
    "search_boost": 1.2,
    "popularity_score": 0.85,
    "conversion_rate": 0.063,
    "view_count": 12540,
    "sale_count": 789
  },
  
  "metadata": {
    "created_by": "john.smith",
    "updated_by": "product.manager",
    "version": 12,
    "tenant_id": "default"
  }
}
```

## Indexing Considerations

1. **Field Mapping Types**: Use appropriate Elasticsearch field types:
   - Exact match fields (id, sku): keyword
   - Full-text fields (name, description): text with appropriate analyzers
   - Numeric fields (price, ratings): float or integer
   - Boolean fields (in_stock): boolean
   - Date fields (created_at): date
   - Nested fields (variants, attributes): nested

2. **Multi-fields**: Configure multi-fields for search and aggregation:
   - Text fields with keyword sub-fields for aggregations
   - Text fields with different analyzers for language support

3. **Nested vs. Object**: Use nested for arrays of objects where individual object matching is needed

4. **Index-time Field Boost**: Applied to increase relevance of specific fields