# Category Mappings

## Overview

This document defines the Elasticsearch mapping configuration for category documents. The mappings optimize category data for hierarchical navigation, faceted search, and category-based filtering while ensuring efficient storage and retrieval.

## Mapping Configuration

```json
{
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "name": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {
            "type": "keyword",
            "normalizer": "lowercase_normalizer",
            "ignore_above": 256
          },
          "completion": {
            "type": "completion",
            "analyzer": "simple"
          }
        }
      },
      "slug": {
        "type": "keyword"
      },
      "description": {
        "type": "text",
        "analyzer": "html_analyzer"
      },
      "status": {
        "type": "keyword"
      },
      "visibility": {
        "type": "keyword"
      },
      "created_at": {
        "type": "date"
      },
      "updated_at": {
        "type": "date"
      },
      "path": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "path_ids": {
        "type": "keyword"
      },
      "level": {
        "type": "integer"
      },
      "position": {
        "type": "integer"
      },
      "parent_id": {
        "type": "keyword"
      },
      
      "attributes": {
        "properties": {
          "display_mode": {
            "type": "keyword"
          },
          "default_sort": {
            "type": "keyword"
          },
          "page_layout": {
            "type": "keyword"
          },
          "custom_attributes": {
            "type": "nested",
            "properties": {
              "code": {
                "type": "keyword"
              },
              "label": {
                "type": "text",
                "fields": {
                  "keyword": {
                    "type": "keyword"
                  }
                }
              },
              "value": {
                "type": "keyword"
              },
              "filterable": {
                "type": "boolean"
              }
            }
          }
        }
      },
      
      "media": {
        "properties": {
          "thumbnail": {
            "type": "keyword",
            "index": false
          },
          "banner": {
            "type": "keyword",
            "index": false
          },
          "icon": {
            "type": "keyword",
            "index": false
          }
        }
      },
      
      "seo": {
        "properties": {
          "title": {
            "type": "text"
          },
          "description": {
            "type": "text"
          },
          "keywords": {
            "type": "keyword"
          },
          "canonical_url": {
            "type": "keyword",
            "index": false
          },
          "robots": {
            "type": "keyword"
          }
        }
      },
      
      "product_counts": {
        "properties": {
          "total": {
            "type": "integer"
          },
          "active": {
            "type": "integer"
          },
          "in_stock": {
            "type": "integer"
          }
        }
      },
      
      "filters": {
        "type": "nested",
        "properties": {
          "attribute_code": {
            "type": "keyword"
          },
          "label": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          },
          "type": {
            "type": "keyword"
          },
          "position": {
            "type": "integer"
          },
          "visible": {
            "type": "boolean"
          }
        }
      },
      
      "featured_products": {
        "type": "keyword"
      },
      
      "children": {
        "type": "nested",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "name": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          },
          "slug": {
            "type": "keyword"
          },
          "position": {
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
      },
      
      "join_field": {
        "type": "join",
        "relations": {
          "parent": "child"
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
        "analyzer": {
          "html_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "char_filter": [
              "html_strip"
            ],
            "filter": [
              "lowercase",
              "asciifolding",
              "stop"
            ]
          }
        },
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

- **id**, **slug**: Keyword type for exact matching
- **name**: Text type with multiple sub-fields:
  - Standard text analysis for full-text search
  - Keyword sub-field for sorting and aggregations
  - Completion sub-field for autocomplete suggestions
- **description**: Text type with HTML stripping for content search
- **status**, **visibility**: Keyword type for exact matching and filtering
- **created_at**, **updated_at**: Date type for time-based queries

### Hierarchical Fields

- **path**: Text field with keyword sub-field for hierarchical navigation
- **path_ids**: Keyword array for ancestor-descendant relationships
- **level**: Integer for category depth in the tree
- **position**: Integer for sorting within the same level
- **parent_id**: Keyword for direct parent relationship

### Join Field

- **join_field**: Special field type for parent-child relationships within the index
  - Facilitates queries like "get all child categories for a given parent"
  - Enables operations that respect the hierarchical nature of categories

### Nested Fields

- **custom_attributes**: Nested type for proper attribute value matching
- **filters**: Nested type for available product filters in this category
- **children**: Nested type for direct child category information

### Media Fields

- **media.thumbnail**, **media.banner**, **media.icon**: Keyword fields marked as non-indexed (index: false) as they are only for storage, not searching

### Product Counts

- **product_counts.total**, **product_counts.active**, **product_counts.in_stock**: Integer fields for category statistics

## Analyzer Configurations

### HTML Analyzer

The `html_analyzer` processes text containing HTML:
- **char_filter**: html_strip - removes HTML tags
- **tokenizer**: standard
- **filters**: lowercase, asciifolding, stop - removes common stop words

### Lowercase Normalizer

The `lowercase_normalizer` standardizes text for exact matching:
- **filters**: lowercase, asciifolding - ensures case-insensitive matching and removes diacritics

## Implementation Guidelines

1. **Create Index Template**:
   ```bash
   PUT _index_template/categories_template
   {
     "index_patterns": ["*-categories-*"],
     "template": {
       "settings": { ... },
       "mappings": { ... }
     }
   }
   ```

2. **Parent-Child Indexing**:
   When using the join field for parent-child relationships, index documents as follows:
   
   For a parent category:
   ```json
   {
     "id": "cat-parent-1",
     "name": "Parent Category",
     "join_field": "parent"
   }
   ```
   
   For a child category:
   ```json
   {
     "id": "cat-child-1",
     "name": "Child Category",
     "parent_id": "cat-parent-1",
     "join_field": {
       "name": "child",
       "parent": "cat-parent-1"
     }
   }
   ```

3. **Path Query Examples**:
   
   To find all categories in a specific path:
   ```json
   GET categories/_search
   {
     "query": {
       "match_phrase_prefix": {
         "path": "Clothing/Men's"
       }
     }
   }
   ```
   
   To find all direct children of a category:
   ```json
   GET categories/_search
   {
     "query": {
       "term": {
         "parent_id": "cat-parent-1"
       }
     }
   }
   ```
   
   To find all descendants of a category (requires parent-child relationship):
   ```json
   GET categories/_search
   {
     "query": {
       "has_parent": {
         "parent_type": "parent",
         "query": {
           "term": {
             "id": "cat-parent-1"
           }
         }
       }
     }
   }
   ```

4. **Updating Category Trees**:
   When moving categories in the hierarchy:
   - Update the `parent_id` of the moved category
   - Update the `path` and `path_ids` of the moved category and all its descendants
   - Update the `children` array of both the old and new parent categories

5. **Reindexing Strategy**:
   Since the category hierarchy is relatively stable and the dataset is usually small:
   - Consider reindexing the entire category tree when significant changes occur
   - Use bulk operations for efficiency
   - Update the alias after reindexing is complete