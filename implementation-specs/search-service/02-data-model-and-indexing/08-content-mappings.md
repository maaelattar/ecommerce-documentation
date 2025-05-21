# Content Mappings

## Overview

This document defines the Elasticsearch mapping configuration for content documents. These mappings optimize the storage and retrieval of marketing and informational content like blog posts, articles, buying guides, and FAQs that enhance the e-commerce experience and can be included in search results.

## Mapping Configuration

```json
{
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "content_title_analyzer",
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
        },
        "boost": 2.0
      },
      "slug": {
        "type": "keyword"
      },
      "content_type": {
        "type": "keyword"
      },
      "body": {
        "type": "text",
        "analyzer": "html_analyzer",
        "fields": {
          "english": {
            "type": "text",
            "analyzer": "english"
          }
        }
      },
      "summary": {
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
      
      "author": {
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
          "email": {
            "type": "keyword"
          },
          "avatar_url": {
            "type": "keyword",
            "index": false
          },
          "bio": {
            "type": "text"
          }
        }
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
          "slug": {
            "type": "keyword"
          },
          "path": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          }
        }
      },
      
      "tags": {
        "type": "keyword"
      },
      
      "related_products": {
        "type": "keyword"
      },
      
      "related_content": {
        "type": "keyword"
      },
      
      "media": {
        "properties": {
          "featured_image": {
            "properties": {
              "url": {
                "type": "keyword",
                "index": false
              },
              "alt": {
                "type": "text"
              },
              "width": {
                "type": "integer"
              },
              "height": {
                "type": "integer"
              }
            }
          },
          "gallery": {
            "type": "nested",
            "properties": {
              "url": {
                "type": "keyword",
                "index": false
              },
              "alt": {
                "type": "text"
              },
              "width": {
                "type": "integer"
              },
              "height": {
                "type": "integer"
              },
              "caption": {
                "type": "text"
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
              "duration": {
                "type": "integer"
              }
            }
          },
          "attachments": {
            "type": "nested",
            "properties": {
              "url": {
                "type": "keyword",
                "index": false
              },
              "name": {
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
              "size": {
                "type": "integer"
              }
            }
          }
        }
      },
      
      "attributes": {
        "properties": {
          "reading_time": {
            "type": "integer"
          },
          "complexity_level": {
            "type": "keyword"
          },
          "format": {
            "type": "keyword"
          },
          "custom_attributes": {
            "type": "nested",
            "properties": {
              "key": {
                "type": "keyword"
              },
              "value": {
                "type": "keyword"
              },
              "searchable": {
                "type": "boolean"
              }
            }
          }
        }
      },
      
      "sections": {
        "type": "nested",
        "properties": {
          "id": {
            "type": "keyword"
          },
          "title": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          },
          "content": {
            "type": "text",
            "analyzer": "html_analyzer"
          },
          "order": {
            "type": "integer"
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
          },
          "open_graph": {
            "properties": {
              "title": {
                "type": "text"
              },
              "description": {
                "type": "text"
              },
              "image": {
                "type": "keyword",
                "index": false
              },
              "type": {
                "type": "keyword"
              }
            }
          },
          "twitter_card": {
            "properties": {
              "card": {
                "type": "keyword"
              },
              "title": {
                "type": "text"
              },
              "description": {
                "type": "text"
              },
              "image": {
                "type": "keyword",
                "index": false
              }
            }
          }
        }
      },
      
      "engagement": {
        "properties": {
          "view_count": {
            "type": "integer"
          },
          "like_count": {
            "type": "integer"
          },
          "comment_count": {
            "type": "integer"
          },
          "share_count": {
            "type": "integer"
          },
          "avg_time_on_page": {
            "type": "float"
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
          },
          "locale": {
            "type": "keyword"
          },
          "translations": {
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
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "refresh_interval": "10s",
      "analysis": {
        "analyzer": {
          "content_title_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
              "lowercase",
              "asciifolding",
              "word_delimiter_graph"
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
        }
      }
    }
  }
}
```

## Field Type Explanations

### Core Fields

- **id**, **slug**: Keyword type for exact matching
- **title**: Text type with multiple sub-fields and boosting:
  - Custom text analysis for search
  - Keyword sub-field for sorting and aggregations
  - Completion sub-field for autocomplete suggestions
  - Boost factor of 2.0 to prioritize title matches
- **content_type**: Keyword type for filtering by type (blog, article, guide, etc.)
- **body**: Text type with HTML stripping and language-specific analysis
- **summary**: Text type with boosting for relevance
- **status**, **visibility**: Keyword type for filtering
- **created_at**, **updated_at**, **published_at**: Date type for time-based queries

### Author Fields

- **author.id**, **author.email**: Keyword type for exact matching
- **author.name**: Text type with keyword sub-field
- **author.avatar_url**: Keyword field marked as non-indexed (index: false)
- **author.bio**: Text type for searching within author biographies

### Categorization Fields

- **categories**: Nested type to maintain the integrity of category objects
- **tags**: Keyword array for tag filtering and aggregation
- **related_products**, **related_content**: Keyword arrays for relationships

### Media Fields

- **media.featured_image**: Object type with URL, alt text, dimensions
- **media.gallery**, **media.videos**, **media.attachments**: Nested types for media collections
- Media URLs: Not indexed (index: false) to save space as they're not searched

### Content Structure Fields

- **sections**: Nested type for structured content with title, content, and ordering
- **sections.content**: Text type with HTML analyzer for searching within sections

### SEO Fields

- **seo.title**, **seo.description**: Text type for search within meta fields
- **seo.keywords**: Keyword array for exact match filtering
- **seo.open_graph**, **seo.twitter_card**: Object types for social sharing metadata

### Engagement Fields

- **engagement.view_count**, **engagement.like_count**: Integer types for metrics
- **engagement.avg_time_on_page**: Float type for decimal precision

## Analyzer Configurations

### Content Title Analyzer

The `content_title_analyzer` is optimized for content titles:
- **tokenizer**: standard - splits on whitespace and punctuation
- **filters**:
  - lowercase - case-insensitive matching
  - asciifolding - removes diacritics
  - word_delimiter_graph - splits on case transitions, punctuation, etc.

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
   PUT _index_template/content_template
   {
     "index_patterns": ["*-content-*"],
     "template": {
       "settings": { ... },
       "mappings": { ... }
     }
   }
   ```

2. **Indexing with Multi-language Support**:
   For content with multiple language versions:
   
   ```json
   POST content/_doc/content-12345-en
   {
     "id": "content-12345-en",
     "title": "How to Choose the Perfect Jeans",
     "language": "en_US",
     "metadata": {
       "translations": ["content-12345-fr", "content-12345-es"]
     }
   }
   ```

3. **Highlighting Configuration**:
   When searching content, use highlighting for relevant snippets:
   
   ```json
   GET content/_search
   {
     "query": {
       "multi_match": {
         "query": "jeans fit guide",
         "fields": ["title^2", "summary^1.5", "body"]
       }
     },
     "highlight": {
       "fields": {
         "body": {
           "fragment_size": 150,
           "number_of_fragments": 3,
           "no_match_size": 150
         },
         "title": {
           "number_of_fragments": 0
         }
       }
     }
   }
   ```

4. **Section Search**:
   To search within specific content sections:
   
   ```json
   GET content/_search
   {
     "query": {
       "nested": {
         "path": "sections",
         "query": {
           "bool": {
             "must": [
               { "match": { "sections.title": "Jean Rises" } },
               { "match": { "sections.content": "high-rise" } }
             ]
           }
         },
         "inner_hits": {}
       }
     }
   }
   ```

5. **Scoring by Engagement**:
   Use function score queries to boost content by engagement metrics:
   
   ```json
   GET content/_search
   {
     "query": {
       "function_score": {
         "query": {
           "match": {
             "body": "jeans sizing guide"
           }
         },
         "functions": [
           {
             "field_value_factor": {
               "field": "engagement.view_count",
               "modifier": "log1p",
               "factor": 0.5
             }
           }
         ],
         "boost_mode": "multiply"
       }
     }
   }
   ```

6. **Related Content Suggestions**:
   Use the More Like This query for content recommendations:
   
   ```json
   GET content/_search
   {
     "query": {
       "more_like_this": {
         "fields": ["title", "body", "tags"],
         "like": [
           {
             "_id": "content-12345"
           }
         ],
         "min_term_freq": 1,
         "max_query_terms": 12
       }
     }
   }
   ```

7. **Updating Engagement Metrics**:
   Use partial updates to keep engagement metrics current:
   
   ```json
   POST content/_update/content-12345
   {
     "script": {
       "source": "ctx._source.engagement.view_count += 1"
     }
   }
   ```