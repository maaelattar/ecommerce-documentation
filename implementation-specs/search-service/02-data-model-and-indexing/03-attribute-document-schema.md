# Attribute Document Schema

## Overview

The attribute document schema defines the structure for product attributes in Elasticsearch. Attributes represent product characteristics used for filtering, faceting, and search refinement. This schema enables dynamic attribute management and efficient faceted navigation.

## Schema Structure

```json
{
  "id": "string",                     // Unique attribute identifier
  "code": "string",                   // Attribute code (machine name)
  "label": "string",                  // Display label
  "created_at": "date",               // Creation timestamp
  "updated_at": "date",               // Last update timestamp
  "status": "string",                 // Status (active, inactive)
  
  "type": "string",                   // Data type (string, numeric, boolean, date, etc.)
  "input_type": "string",             // Input type (text, select, multiselect, date, etc.)
  "is_system": "boolean",             // Whether it's a system attribute
  "is_required": "boolean",           // Whether required for products
  "is_unique": "boolean",             // Whether values must be unique
  
  "search_config": {                  // Search configuration
    "searchable": "boolean",          // Whether used in full-text search
    "filterable": "boolean",          // Whether used for filtering
    "comparable": "boolean",          // Whether used for product comparison
    "use_in_sorting": "boolean",      // Whether used for sorting
    "visible_in_search": "boolean",   // Whether visible in search results
    "position": "integer",            // Display position in filters
    "facet_min_count": "integer",     // Minimum count for facet display
    "index_analyzer": "string",       // Analyzer used for indexing
    "search_analyzer": "string"       // Analyzer used for searching
  },
  
  "display_config": {                 // Display configuration
    "visible_in_product_page": "boolean", // Whether visible on product page
    "visible_in_catalog": "boolean",  // Whether visible in catalog
    "display_mode": "string",         // How to display (text, swatch, etc.)
    "group": "string",                // Attribute group name
    "position_in_group": "integer"    // Position within attribute group
  },
  
  "validation_rules": {               // Validation rules
    "min_length": "integer",          // Minimum text length
    "max_length": "integer",          // Maximum text length
    "min_value": "number",            // Minimum numeric value
    "max_value": "number",            // Maximum numeric value
    "regex_pattern": "string",        // Validation regex pattern
    "allowed_file_extensions": ["string"] // For file attributes
  },
  
  "options": [                        // Predefined options for select attributes
    {
      "id": "string",                 // Option ID
      "value": "string",              // Option value
      "label": "string",              // Option display label
      "position": "integer",          // Sort order
      "is_default": "boolean",        // Whether it's the default option
      "swatch_value": "string",       // Swatch value for display (color code, image URL)
      "swatch_type": "string"         // Swatch type (color, image, text)
    }
  ],
  
  "localized_labels": {               // Internationalized labels
    "en_US": "string",                // English (US) label
    "es_ES": "string",                // Spanish label
    "fr_FR": "string"                 // French label
  },
  
  "eav_entity_type": "string",        // Entity type (product, category, etc.)
  "source_model": "string",           // Source model for option values
  "backend_model": "string",          // Backend model for processing
  
  "usage_stats": {                    // Usage statistics
    "product_count": "integer",       // Number of products using this attribute
    "filter_count": "integer",        // Number of times used in filters
    "search_count": "integer"         // Number of times used in searches
  },
  
  "metadata": {                       // Miscellaneous metadata
    "created_by": "string",           // User who created the attribute
    "updated_by": "string",           // User who last updated the attribute
    "version": "integer",             // Document version
    "tenant_id": "string"             // Multi-tenant identifier
  }
}
```

## Field Descriptions

### Core Fields

- **id**: Unique identifier for the attribute, typically a UUID
- **code**: Machine-readable attribute code, used in queries and code
- **label**: Human-readable display name
- **status**: Current attribute status (active, inactive)
- **type**: Data type (string, numeric, boolean, date, etc.)
- **input_type**: UI input type (text, select, multiselect, date, etc.)
- **is_system**: Whether it's a system attribute that cannot be deleted
- **is_required**: Whether the attribute is required for products
- **is_unique**: Whether attribute values must be unique across products

### Search Configuration

- **search_config**: Settings for search behavior
  - **searchable**: Whether attribute is included in full-text search
  - **filterable**: Whether attribute can be used for filtering
  - **comparable**: Whether attribute is used in product comparison
  - **use_in_sorting**: Whether attribute can be used for sorting results
  - **visible_in_search**: Whether attribute is visible in search results
  - **position**: Display order in filter lists
  - **facet_min_count**: Minimum number of products needed to display a facet value
  - **index_analyzer**: Elasticsearch analyzer used for indexing
  - **search_analyzer**: Elasticsearch analyzer used for searching

### Display Configuration

- **display_config**: Settings for UI presentation
  - **visible_in_product_page**: Whether shown on product detail pages
  - **visible_in_catalog**: Whether shown in product listings
  - **display_mode**: How to display the attribute (text, swatch, etc.)
  - **group**: Attribute group for organization
  - **position_in_group**: Sort order within the group

### Options

- **options**: For attributes with predefined values (select, multiselect)
  - **id**: Option identifier
  - **value**: Internal option value
  - **label**: Display label for the option
  - **position**: Sort order
  - **is_default**: Whether the option is selected by default
  - **swatch_value**: For swatch attributes, color code or image URL
  - **swatch_type**: Type of swatch (color, image, text)

### Localization

- **localized_labels**: Translations of the attribute label
  - Keys are locale codes, values are translated labels

### Statistics

- **usage_stats**: Information about attribute usage
  - **product_count**: Number of products using this attribute
  - **filter_count**: How often the attribute is used in filters
  - **search_count**: How often the attribute is used in searches

## Sample Attribute Documents

### Text Attribute Example

```json
{
  "id": "attr-101",
  "code": "material",
  "label": "Material",
  "created_at": "2023-01-10T08:45:00Z",
  "updated_at": "2023-08-15T11:20:00Z",
  "status": "active",
  
  "type": "string",
  "input_type": "text",
  "is_system": false,
  "is_required": false,
  "is_unique": false,
  
  "search_config": {
    "searchable": true,
    "filterable": true,
    "comparable": true,
    "use_in_sorting": false,
    "visible_in_search": true,
    "position": 5,
    "facet_min_count": 1,
    "index_analyzer": "english",
    "search_analyzer": "english"
  },
  
  "display_config": {
    "visible_in_product_page": true,
    "visible_in_catalog": false,
    "display_mode": "text",
    "group": "product_details",
    "position_in_group": 3
  },
  
  "validation_rules": {
    "min_length": 2,
    "max_length": 50
  },
  
  "localized_labels": {
    "en_US": "Material",
    "es_ES": "Material",
    "fr_FR": "Matériel"
  },
  
  "eav_entity_type": "product",
  
  "usage_stats": {
    "product_count": 1245,
    "filter_count": 3567,
    "search_count": 982
  },
  
  "metadata": {
    "created_by": "system.admin",
    "updated_by": "catalog.manager",
    "version": 3,
    "tenant_id": "default"
  }
}
```

### Select Attribute Example

```json
{
  "id": "attr-102",
  "code": "size",
  "label": "Size",
  "created_at": "2023-01-05T09:30:00Z",
  "updated_at": "2023-09-12T14:25:00Z",
  "status": "active",
  
  "type": "string",
  "input_type": "select",
  "is_system": false,
  "is_required": true,
  "is_unique": false,
  
  "search_config": {
    "searchable": true,
    "filterable": true,
    "comparable": true,
    "use_in_sorting": false,
    "visible_in_search": true,
    "position": 2,
    "facet_min_count": 1
  },
  
  "display_config": {
    "visible_in_product_page": true,
    "visible_in_catalog": true,
    "display_mode": "dropdown",
    "group": "product_details",
    "position_in_group": 1
  },
  
  "options": [
    {
      "id": "size-xs",
      "value": "XS",
      "label": "Extra Small",
      "position": 1,
      "is_default": false
    },
    {
      "id": "size-s",
      "value": "S",
      "label": "Small",
      "position": 2,
      "is_default": false
    },
    {
      "id": "size-m",
      "value": "M",
      "label": "Medium",
      "position": 3,
      "is_default": true
    },
    {
      "id": "size-l",
      "value": "L",
      "label": "Large",
      "position": 4,
      "is_default": false
    },
    {
      "id": "size-xl",
      "value": "XL",
      "label": "Extra Large",
      "position": 5,
      "is_default": false
    }
  ],
  
  "localized_labels": {
    "en_US": "Size",
    "es_ES": "Talla",
    "fr_FR": "Taille"
  },
  
  "eav_entity_type": "product",
  
  "usage_stats": {
    "product_count": 3621,
    "filter_count": 12458,
    "search_count": 5789
  },
  
  "metadata": {
    "created_by": "system.admin",
    "updated_by": "catalog.manager",
    "version": 5,
    "tenant_id": "default"
  }
}
```

## Indexing Considerations

1. **Nested Options**: Store options as nested objects for proper query matching
2. **Keyword vs. Text**: Store code as keyword for exact matching, label as text for searching
3. **Multi-fields**: Use multi-fields for labels to enable both exact matching and text search
4. **Completion Suggester**: Consider a completion suggester field for attribute autocomplete
5. **Dynamic Mapping**: For exceptional cases, dynamic mapping can be used for custom fields