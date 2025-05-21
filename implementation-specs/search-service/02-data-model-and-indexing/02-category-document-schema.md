# Category Document Schema

## Overview

The category document schema defines the structure for storing product category information in Elasticsearch. Categories represent the hierarchical organization of products and are essential for faceted navigation, browsing, and search refinement.

## Schema Structure

```json
{
  "id": "string",                     // Unique category identifier
  "name": "string",                   // Category name
  "slug": "string",                   // URL-friendly identifier
  "description": "text",              // Category description
  "status": "string",                 // Status (active, inactive)
  "visibility": "string",             // Visibility (visible, hidden)
  "created_at": "date",               // Creation timestamp
  "updated_at": "date",               // Last update timestamp
  "path": "string",                   // Full path (e.g., "Electronics/Computers/Laptops")
  "path_ids": ["string"],             // Array of IDs in the path
  "level": "integer",                 // Depth in category tree (root = 0)
  "position": "integer",              // Sort order position
  "parent_id": "string",              // ID of parent category (null for root)
  
  "attributes": {                     // Category-specific attributes
    "display_mode": "string",         // How to display products (grid, list)
    "default_sort": "string",         // Default product sort order
    "page_layout": "string",          // Page layout template
    "custom_attributes": [            // Dynamic custom attributes
      {
        "code": "string",             // Attribute code
        "label": "string",            // Display label
        "value": "any",               // Attribute value
        "filterable": "boolean"       // Whether used in filtering
      }
    ]
  },
  
  "media": {                          // Category media
    "thumbnail": "string",            // Thumbnail image URL
    "banner": "string",               // Banner image URL
    "icon": "string"                  // Category icon URL
  },
  
  "seo": {                            // SEO metadata
    "title": "string",                // SEO title
    "description": "string",          // Meta description
    "keywords": ["string"],           // Meta keywords
    "canonical_url": "string",        // Canonical URL
    "robots": "string"                // Robots meta tag
  },
  
  "product_counts": {                 // Product count information
    "total": "integer",               // Total products in category
    "active": "integer",              // Active products in category
    "in_stock": "integer"             // In-stock products in category
  },
  
  "filters": [                        // Available filters for this category
    {
      "attribute_code": "string",     // Filter attribute code
      "label": "string",              // Display label
      "type": "string",               // Filter type (checkbox, range, etc.)
      "position": "integer",          // Display order
      "visible": "boolean"            // Whether filter is visible
    }
  ],
  
  "featured_products": ["string"],    // IDs of featured products
  
  "children": [                       // Direct child categories
    {
      "id": "string",                 // Child category ID
      "name": "string",               // Child category name
      "slug": "string",               // Child category slug
      "position": "integer"           // Sort order position
    }
  ],
  
  "metadata": {                       // Miscellaneous metadata
    "created_by": "string",           // User who created the category
    "updated_by": "string",           // User who last updated the category
    "version": "integer",             // Document version
    "tenant_id": "string"             // Multi-tenant identifier
  }
}
```

## Field Descriptions

### Core Fields

- **id**: Unique identifier for the category, typically a UUID
- **name**: The category's display name
- **slug**: URL-friendly version of the category name
- **description**: HTML description of the category
- **status**: Current category status (active, inactive)
- **visibility**: Controls category visibility (visible, hidden)
- **path**: Full hierarchical path, typically separated by slashes
- **path_ids**: Array of category IDs representing the hierarchical path
- **level**: Depth in category hierarchy, with root categories at level 0
- **position**: Numeric value determining sort order within the parent category
- **parent_id**: ID of the parent category, null for root categories

### Attribute Fields

- **attributes**: Category-specific attributes
  - **display_mode**: How products should be displayed (grid, list)
  - **default_sort**: Default product sort order (position, name, price, etc.)
  - **page_layout**: Page layout template to use
  - **custom_attributes**: Array of dynamic attributes specific to the category

### Media Fields

- **media**: Category images
  - **thumbnail**: Small image displayed in category listings
  - **banner**: Large banner image displayed on category pages
  - **icon**: Icon used in navigation menus

### SEO Fields

- **seo**: Search engine optimization data
  - **title**: Custom title tag for the category page
  - **description**: Meta description
  - **keywords**: Meta keywords
  - **canonical_url**: Canonical URL to prevent duplicate content
  - **robots**: Robots meta tag directives

### Navigation Fields

- **filters**: Available filters for products in this category
  - **attribute_code**: Filter attribute code
  - **label**: Display label for the filter
  - **type**: Filter display type (checkbox, range, etc.)
  - **position**: Display order
  - **visible**: Whether the filter is visible
- **children**: Direct child categories with minimal information for navigation
- **featured_products**: Array of product IDs featured in this category

### Statistics Fields

- **product_counts**: Count of products in the category
  - **total**: Total number of products in the category
  - **active**: Number of active products
  - **in_stock**: Number of in-stock products

## Sample Category Document

```json
{
  "id": "cat-101",
  "name": "Men's Jeans",
  "slug": "mens-jeans",
  "description": "<p>Shop our collection of men's jeans in various styles and fits.</p>",
  "status": "active",
  "visibility": "visible",
  "created_at": "2023-04-12T09:15:00Z",
  "updated_at": "2023-09-05T16:30:00Z",
  "path": "Clothing/Men's/Jeans",
  "path_ids": ["cat-50", "cat-75", "cat-101"],
  "level": 2,
  "position": 3,
  "parent_id": "cat-75",
  
  "attributes": {
    "display_mode": "grid",
    "default_sort": "position",
    "page_layout": "two-column",
    "custom_attributes": [
      {
        "code": "featured_category",
        "label": "Featured Category",
        "value": true,
        "filterable": false
      },
      {
        "code": "season",
        "label": "Season",
        "value": "all-season",
        "filterable": true
      }
    ]
  },
  
  "media": {
    "thumbnail": "https://assets.example.com/categories/mens-jeans-thumb.jpg",
    "banner": "https://assets.example.com/categories/mens-jeans-banner.jpg",
    "icon": "https://assets.example.com/categories/mens-jeans-icon.svg"
  },
  
  "seo": {
    "title": "Men's Jeans | Premium Denim & Designer Styles | Example Store",
    "description": "Shop our collection of men's jeans including slim fit, straight leg, bootcut and more. Find premium denim and designer styles for every occasion.",
    "keywords": ["men's jeans", "denim jeans", "designer jeans", "slim fit jeans"],
    "canonical_url": "https://www.example.com/clothing/mens/jeans",
    "robots": "index, follow"
  },
  
  "product_counts": {
    "total": 85,
    "active": 78,
    "in_stock": 72
  },
  
  "filters": [
    {
      "attribute_code": "fit",
      "label": "Fit",
      "type": "checkbox",
      "position": 1,
      "visible": true
    },
    {
      "attribute_code": "color",
      "label": "Color",
      "type": "swatch",
      "position": 2,
      "visible": true
    },
    {
      "attribute_code": "price",
      "label": "Price",
      "type": "range",
      "position": 3,
      "visible": true
    }
  ],
  
  "featured_products": [
    "prod-12345",
    "prod-12346",
    "prod-12347"
  ],
  
  "children": [
    {
      "id": "cat-102",
      "name": "Slim Fit Jeans",
      "slug": "slim-fit-jeans",
      "position": 1
    },
    {
      "id": "cat-103",
      "name": "Straight Leg Jeans",
      "slug": "straight-leg-jeans",
      "position": 2
    },
    {
      "id": "cat-104",
      "name": "Bootcut Jeans",
      "slug": "bootcut-jeans",
      "position": 3
    }
  ],
  
  "metadata": {
    "created_by": "jane.doe",
    "updated_by": "catalog.manager",
    "version": 8,
    "tenant_id": "default"
  }
}
```

## Indexing Considerations

1. **Hierarchical Data**: Category hierarchies can be queried using the path field or path_ids array
2. **Nested vs. Object**: Use nested type for arrays like filters and custom_attributes where individual object matching is needed
3. **Parent-Child Relationship**: Use join field if parent-child relationships need to be maintained in a single index
4. **Multi-fields**: Configure name and description with keyword sub-fields for sorting and aggregations
5. **Completion Suggester**: Consider using a completion suggester field for category autocomplete functionality