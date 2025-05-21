# Product Mappings

## Overview

This document defines the Elasticsearch mapping configuration for product documents. Mappings specify how document fields should be stored and indexed, including field types, analyzers, and index options. This configuration is optimized for search performance, relevance, and faceted navigation.

## Mapping Configuration

```json
{
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "sku": {
        "type": "keyword",
        "fields": {
          "text": {
            "type": "text",
            "analyzer": "standard"
          }
        }
      },
      "name": {
        "type": "text",
        "analyzer": "product_name_analyzer",
        "fields": {
          "keyword": {
            "type": "keyword",
            "normalizer": "lowercase_normalizer",
            "ignore_above": 256
          },
          "ngram": {
            "type": "text",
            "analyzer": "ngram_analyzer"
          },
          "completion": {
            "type": "completion",
            "analyzer": "simple",
            "preserve_separators": true,
            "preserve_position_increments": true,
            "max_input_length": 50
          }
        },
        "boost": 3.0
      },
      "description": {
        "type": "text",
        "analyzer": "html_analyzer",
        "fields": {
          "english": {
            "type": "text",
            "analyzer": "english"
          }
        }
      },
      "short_description": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "english": {
            "type": "text",
            "analyzer": "english"
          }
        },
        "boost": 1.5
      },
      "slug": {
        "type": "keyword"
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
      "published_at": {
        "type": "date"
      },
      "type": {
        "type": "keyword"
      },
      
      "categories": {
        "type": "nested",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "name": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword",
                "normalizer": "lowercase_normalizer"
              }
            }
          },
          "path": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          },
          "level": {
            "type": "integer"
          },
          "position": {
            "type": "integer"
          }
        }
      },
      
      "brand": {
        "properties": {
          "id": {
            "type": "keyword"
          },
          "name": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword",
                "normalizer": "lowercase_normalizer"
              }
            },
            "boost": 2.0
          },
          "logo_url": {
            "type": "keyword",
            "index": false
          }
        }
      },
      
      "pricing": {
        "properties": {
          "currency": {
            "type": "keyword"
          },
          "list_price": {
            "type": "double"
          },
          "sale_price": {
            "type": "double"
          },
          "sale_price_effective_date": {
            "properties": {
              "from": {
                "type": "date"
              },
              "to": {
                "type": "date"
              }
            }
          },
          "price_range": {
            "properties": {
              "min_price": {
                "type": "double"
              },
              "max_price": {
                "type": "double"
              }
            }
          },
          "tax_class": {
            "type": "keyword"
          },
          "tax_rate": {
            "type": "double"
          }
        }
      },
      
      "inventory": {
        "properties": {
          "in_stock": {
            "type": "boolean"
          },
          "quantity": {
            "type": "integer"
          },
          "availability": {
            "type": "keyword"
          },
          "threshold": {
            "type": "integer"
          }
        }
      },
      
      "attributes": {
        "properties": {
          "color": {
            "type": "keyword",
            "fields": {
              "text": {
                "type": "text",
                "analyzer": "standard"
              }
            }
          },
          "size": {
            "type": "keyword"
          },
          "material": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          },
          "weight": {
            "type": "double"
          },
          "dimensions": {
            "properties": {
              "length": {
                "type": "double"
              },
              "width": {
                "type": "double"
              },
              "height": {
                "type": "double"
              },
              "unit": {
                "type": "keyword"
              }
            }
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
              "value_text": {
                "type": "text"
              },
              "filterable": {
                "type": "boolean"
              },
              "searchable": {
                "type": "boolean"
              }
            }
          }
        }
      },
      
      "variants": {
        "type": "nested",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "sku": {
            "type": "keyword"
          },
          "attributes": {
            "properties": {
              "color": {
                "type": "keyword"
              },
              "size": {
                "type": "keyword"
              }
            }
          },
          "pricing": {
            "properties": {
              "list_price": {
                "type": "double"
              },
              "sale_price": {
                "type": "double"
              }
            }
          },
          "inventory": {
            "properties": {
              "in_stock": {
                "type": "boolean"
              },
              "quantity": {
                "type": "integer"
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
          "images": {
            "type": "nested",
            "properties": {
              "url": {
                "type": "keyword",
                "index": false
              },
              "alt": {
                "type": "text"
              },
              "position": {
                "type": "integer"
              },
              "type": {
                "type": "keyword"
              }
            }
          },
          "videos": {
            "type": "nested",
            "properties": {
              "url": {
                "type": "keyword",
                "index": false
              },
              "thumbnail": {
                "type": "keyword",
                "index": false
              },
              "title": {
                "type": "text"
              },
              "description": {
                "type": "text"
              }
            }
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
          "structured_data": {
            "type": "object",
            "enabled": false
          }
        }
      },
      
      "ratings": {
        "properties": {
          "average": {
            "type": "double"
          },
          "count": {
            "type": "integer"
          },
          "distribution": {
            "properties": {
              "1": {"type": "integer"},
              "2": {"type": "integer"},
              "3": {"type": "integer"},
              "4": {"type": "integer"},
              "5": {"type": "integer"}
            }
          }
        }
      },
      
      "shipping": {
        "properties": {
          "weight": {
            "type": "double"
          },
          "weight_unit": {
            "type": "keyword"
          },
          "dimensions": {
            "properties": {
              "length": {
                "type": "double"
              },
              "width": {
                "type": "double"
              },
              "height": {
                "type": "double"
              },
              "unit": {
                "type": "keyword"
              }
            }
          },
          "free_shipping": {
            "type": "boolean"
          },
          "shipping_class": {
            "type": "keyword"
          }
        }
      },
      
      "tags": {
        "type": "keyword"
      },
      
      "related_products": {
        "type": "keyword"
      },
      
      "cross_sell_products": {
        "type": "keyword"
      },
      
      "upsell_products": {
        "type": "keyword"
      },
      
      "search_data": {
        "properties": {
          "search_keywords": {
            "type": "text",
            "analyzer": "standard",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          },
          "search_boost": {
            "type": "double"
          },
          "popularity_score": {
            "type": "double"
          },
          "conversion_rate": {
            "type": "double"
          },
          "view_count": {
            "type": "integer"
          },
          "sale_count": {
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
      "number_of_shards": 5,
      "number_of_replicas": 1,
      "refresh_interval": "10s",
      "analysis": {
        "analyzer": {
          "product_name_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
              "lowercase",
              "asciifolding",
              "synonym",
              "word_delimiter_graph"
            ]
          },
          "ngram_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
              "lowercase",
              "asciifolding",
              "ngram_filter"
            ]
          },
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
        },
        "filter": {
          "ngram_filter": {
            "type": "ngram",
            "min_gram": 2,
            "max_gram": 20
          },
          "synonym": {
            "type": "synonym_graph",
            "synonyms_path": "analysis/product_synonyms.txt"
          }
        }
      }
    }
  }
}
```

## Field Type Explanations

### Core Fields

- **id**, **sku**: Keyword type for exact matching
- **name**: Text type with multiple sub-fields:
  - Standard text analysis for full-text search
  - Keyword sub-field for sorting and aggregations
  - N-gram sub-field for partial matching
  - Completion sub-field for autocomplete suggestions
- **description**: Text type with HTML stripping and language-specific analysis
- **slug**, **status**, **visibility**, **type**: Keyword type for exact matching
- **created_at**, **updated_at**, **published_at**: Date type for time-based queries

### Nested Fields

- **categories**: Nested type to maintain the integrity of each category object
- **variants**: Nested type to allow querying on specific variant combinations
- **custom_attributes**: Nested type for proper attribute value matching
- **images**, **videos**: Nested type for structured media objects

### Numeric Fields

- **price**: Double type for decimal precision
- **ratings.average**: Double type for decimal precision
- **quantity**: Integer type for whole numbers

### Boolean Fields

- **in_stock**, **free_shipping**: Boolean type for true/false filters

### Special Field Configurations

- **name.boost**: Field-level boosting to prioritize name matches
- **brand.name.boost**: Field-level boosting for brand name
- **media URLs**: Not indexed (index: false) to save space as they're not searched
- **structured_data**: Disabled (enabled: false) as it's stored but not indexed

## Analyzer Configurations

### Product Name Analyzer

The `product_name_analyzer` is optimized for product name searches:
- **tokenizer**: standard - splits on whitespace and punctuation
- **filters**:
  - lowercase - case-insensitive matching
  - asciifolding - removes diacritics
  - synonym - expands search terms with synonyms
  - word_delimiter_graph - splits on case transitions, punctuation, etc.

### N-gram Analyzer

The `ngram_analyzer` enables partial matching:
- **tokenizer**: standard
- **filters**:
  - lowercase, asciifolding
  - ngram_filter - creates n-grams from tokens (min: 2, max: 20)

### HTML Analyzer

The `html_analyzer` processes text containing HTML:
- **char_filter**: html_strip - removes HTML tags
- **tokenizer**: standard
- **filters**: lowercase, asciifolding, stop - removes common stop words

## Implementation Guidelines

1. **Create Index Template**:
   ```bash
   PUT _index_template/products_template
   {
     "index_patterns": ["*-products-*"],
     "template": {
       "settings": { ... },
       "mappings": { ... }
     }
   }
   ```

2. **Dynamic Templates**:
   Consider adding dynamic templates for custom attributes that aren't explicitly mapped:
   ```json
   "dynamic_templates": [
     {
       "strings_as_keywords": {
         "match_mapping_type": "string",
         "mapping": {
           "type": "keyword",
           "ignore_above": 256
         }
       }
     }
   ]
   ```

3. **Runtime Fields**:
   Use runtime fields for calculated values:
   ```json
   "runtime_fields": {
     "discounted_percentage": {
       "type": "double",
       "script": {
         "source": "if (doc['pricing.list_price'].size() > 0 && doc['pricing.sale_price'].size() > 0) { emit((1 - (doc['pricing.sale_price'].value / doc['pricing.list_price'].value)) * 100); } else { emit(0); }"
       }
     }
   }
   ```

4. **Reindex Considerations**:
   - Implement a reindex API that creates a new index with updated mappings
   - Use aliases to switch between indexes without downtime
   - Consider zero-downtime reindexing strategies