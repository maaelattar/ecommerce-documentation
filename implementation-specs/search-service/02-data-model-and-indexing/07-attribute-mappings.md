# Attribute Mappings

## Overview

This document defines the Elasticsearch mapping configuration for attribute documents. These mappings optimize the storage and retrieval of product attributes used for filtering, faceting, and search refinement.

## Mapping Configuration

```json
{
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "code": {
        "type": "keyword"
      },
      "label": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "normalizer": "lowercase_normalizer"
          },
          "completion": {
            "type": "completion",
            "analyzer": "simple"
          }
        }
      },
      "created_at": {
        "type": "date"
      },
      "updated_at": {
        "type": "date"
      },
      "status": {
        "type": "keyword"
      },
      
      "type": {
        "type": "keyword"
      },
      "input_type": {
        "type": "keyword"
      },
      "is_system": {
        "type": "boolean"
      },
      "is_required": {
        "type": "boolean"
      },
      "is_unique": {
        "type": "boolean"
      },
      
      "search_config": {
        "properties": {
          "searchable": {
            "type": "boolean"
          },
          "filterable": {
            "type": "boolean"
          },
          "comparable": {
            "type": "boolean"
          },
          "use_in_sorting": {
            "type": "boolean"
          },
          "visible_in_search": {
            "type": "boolean"
          },
          "position": {
            "type": "integer"
          },
          "facet_min_count": {
            "type": "integer"
          },
          "index_analyzer": {
            "type": "keyword"
          },
          "search_analyzer": {
            "type": "keyword"
          }
        }
      },
      
      "display_config": {
        "properties": {
          "visible_in_product_page": {
            "type": "boolean"
          },
          "visible_in_catalog": {
            "type": "boolean"
          },
          "display_mode": {
            "type": "keyword"
          },
          "group": {
            "type": "keyword"
          },
          "position_in_group": {
            "type": "integer"
          }
        }
      },
      
      "validation_rules": {
        "properties": {
          "min_length": {
            "type": "integer"
          },
          "max_length": {
            "type": "integer"
          },
          "min_value": {
            "type": "float"
          },
          "max_value": {
            "type": "float"
          },
          "regex_pattern": {
            "type": "keyword",
            "index": false
          },
          "allowed_file_extensions": {
            "type": "keyword"
          }
        }
      },
      
      "options": {
        "type": "nested",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "value": {
            "type": "keyword"
          },
          "label": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword",
                "normalizer": "lowercase_normalizer"
              }
            }
          },
          "position": {
            "type": "integer"
          },
          "is_default": {
            "type": "boolean"
          },
          "swatch_value": {
            "type": "keyword",
            "index": false
          },
          "swatch_type": {
            "type": "keyword"
          }
        }
      },
      
      "localized_labels": {
        "type": "object",
        "dynamic": true,
        "properties": {
          "en_US": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          }
        }
      },
      
      "eav_entity_type": {
        "type": "keyword"
      },
      "source_model": {
        "type": "keyword"
      },
      "backend_model": {
        "type": "keyword"
      },
      
      "usage_stats": {
        "properties": {
          "product_count": {
            "type": "integer"
          },
          "filter_count": {
            "type": "integer"
          },
          "search_count": {
            "type": "integer"
          }
        }
      },
      
      "metadata": {
        "properties": {
          "created_by": {
            "type": "keyword"
          },
          "updated_by": {
            "type": "keyword"
          },
          "version": {
            "type": "integer"
          },
          "tenant_id": {
            "type": "keyword"
          }
        }
      }
    }
  }
}
```

## Settings Configuration

```json
{
  "settings": {
    "index": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "refresh_interval": "10s",
      "analysis": {
        "normalizer": {
          "lowercase_normalizer": {
            "type": "custom",
            "filter": [
              "lowercase",
              "asciifolding"
            ]
          }
        }
      }
    }
  }
}
```

## Field Type Explanations

### Core Fields

- **id**, **code**: Keyword type for exact matching
- **label**: Text type with multiple sub-fields:
  - Standard text analysis for full-text search
  - Keyword sub-field for sorting and aggregations
  - Completion sub-field for autocomplete suggestions
- **status**: Keyword type for exact matching and filtering
- **created_at**, **updated_at**: Date type for time-based queries

### Type and Configuration Fields

- **type**: Keyword for data type (string, numeric, boolean, etc.)
- **input_type**: Keyword for UI input type (text, select, multiselect, etc.)
- **is_system**, **is_required**, **is_unique**: Boolean fields for attribute properties

### Search Configuration Fields

- **search_config.searchable**, **search_config.filterable**: Boolean fields for search behavior
- **search_config.position**: Integer for display order in filters
- **search_config.facet_min_count**: Integer for minimum product count to display a facet value
- **search_config.index_analyzer**, **search_config.search_analyzer**: Keywords for analyzer references

### Display Configuration Fields

- **display_config.visible_in_product_page**, **display_config.visible_in_catalog**: Boolean fields for UI visibility
- **display_config.display_mode**: Keyword for display type (text, dropdown, swatch, etc.)
- **display_config.group**: Keyword for attribute group assignment
- **display_config.position_in_group**: Integer for position within group

### Validation Rule Fields

- **validation_rules.min_length**, **validation_rules.max_length**: Integer fields for text length constraints
- **validation_rules.min_value**, **validation_rules.max_value**: Float fields for numeric constraints
- **validation_rules.regex_pattern**: Keyword field (not indexed) for validation patterns
- **validation_rules.allowed_file_extensions**: Keyword array for file type validation

### Option Fields

- **options**: Nested type for predefined attribute values
  - **options.id**, **options.value**: Keyword fields for exact matching
  - **options.label**: Text field with keyword sub-field
  - **options.position**: Integer for sort order
  - **options.is_default**: Boolean for default selection
  - **options.swatch_value**: Keyword field (not indexed) for color codes or image URLs
  - **options.swatch_type**: Keyword field for swatch display type

### Localization Fields

- **localized_labels**: Object field with dynamic mapping for translations
  - Each locale code mapped to a text field with keyword sub-field

### Usage Statistics Fields

- **usage_stats.product_count**: Integer for number of products using this attribute
- **usage_stats.filter_count**: Integer for filter usage count
- **usage_stats.search_count**: Integer for search usage count

## Analyzer Configurations

### Lowercase Normalizer

The `lowercase_normalizer` standardizes text for exact matching:
- **filters**: lowercase, asciifolding - ensures case-insensitive matching and removes diacritics

## Implementation Guidelines

1. **Create Index Template**:
   ```bash
   PUT _index_template/attributes_template
   {
     "index_patterns": ["*-attributes-*"],
     "template": {
       "settings": { ... },
       "mappings": { ... }
     }
   }
   ```

2. **Dynamic Mapping for Localized Labels**:
   The `localized_labels` field uses dynamic mapping to support new languages:
   ```json
   "localized_labels": {
     "type": "object",
     "dynamic": true
   }
   ```
   
   When a new language is added, it will automatically create the appropriate field:
   ```json
   {
     "localized_labels": {
       "de_DE": "Größe"
     }
   }
   ```

3. **Attribute Option Indexing**:
   For attributes with options (like dropdown fields):
   
   ```json
   {
     "id": "attr-size",
     "code": "size",
     "label": "Size",
     "type": "string",
     "input_type": "select",
     "options": [
       {
         "id": "size-s",
         "value": "S",
         "label": "Small",
         "position": 1,
         "is_default": false
       },
       {
         "id": "size-m",
         "value": "M",
         "label": "Medium",
         "position": 2,
         "is_default": true
       }
     ]
   }
   ```

4. **Search Examples**:
   
   To find all filterable attributes:
   ```json
   GET attributes/_search
   {
     "query": {
       "term": {
         "search_config.filterable": true
       }
     }
   }
   ```
   
   To find attributes in a specific group:
   ```json
   GET attributes/_search
   {
     "query": {
       "term": {
         "display_config.group": "product_details"
       }
     },
     "sort": [
       { "display_config.position_in_group": "asc" }
     ]
   }
   ```
   
   To search for attributes with specific options:
   ```json
   GET attributes/_search
   {
     "query": {
       "nested": {
         "path": "options",
         "query": {
           "match": {
             "options.label": "Small"
           }
         }
       }
     }
   }
   ```

5. **Updating Usage Statistics**:
   Implement a scheduled job to update usage statistics:
   
   ```json
   POST attributes/_update/attr-size
   {
     "doc": {
       "usage_stats": {
         "product_count": 1250,
         "filter_count": 3580,
         "search_count": 987
       }
     }
   }
   ```

6. **Attribute Completion Suggestions**:
   Use the completion suggester for attribute autocomplete:
   
   ```json
   GET attributes/_search
   {
     "suggest": {
       "attribute_suggest": {
         "prefix": "si",
         "completion": {
           "field": "label.completion",
           "size": 5
         }
       }
     }
   }
   ```