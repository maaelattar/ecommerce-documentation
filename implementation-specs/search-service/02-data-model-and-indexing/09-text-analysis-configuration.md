# Text Analysis Configuration

## Overview

This document defines the text analysis configuration used across all indices in the Search Service. Text analysis determines how text is processed during indexing and searching, directly impacting search quality, relevance, and performance.

## Analyzer Definitions

```json
{
  "settings": {
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
        },
        "content_title_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding",
            "word_delimiter_graph"
          ]
        },
        "search_as_you_type_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding",
            "edge_ngram_filter"
          ]
        },
        "keyword_analyzer": {
          "type": "custom",
          "tokenizer": "keyword",
          "filter": [
            "lowercase",
            "asciifolding"
          ]
        },
        "autocomplete_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding",
            "edge_ngram_filter"
          ]
        },
        "sku_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "word_delimiter_graph"
          ]
        }
      },
      "char_filter": {
        "html_strip": {
          "type": "html_strip"
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
        "edge_ngram_filter": {
          "type": "edge_ngram",
          "min_gram": 1,
          "max_gram": 20
        },
        "synonym": {
          "type": "synonym_graph",
          "synonyms_path": "analysis/synonyms.txt"
        },
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        },
        "english_possessive_stemmer": {
          "type": "stemmer",
          "language": "possessive_english"
        }
      }
    }
  }
}
```

## Analyzer Descriptions

### Product Name Analyzer

The `product_name_analyzer` is designed for product names and titles where precise tokenization and normalization are needed.

Components:
- **Tokenizer**: `standard` - Breaks text on whitespace and removes punctuation
- **Filters**:
  - `lowercase` - Converts all tokens to lowercase
  - `asciifolding` - Converts characters to ASCII equivalents (removes diacritics)
  - `synonym` - Expands tokens to include synonyms from synonyms.txt
  - `word_delimiter_graph` - Splits tokens on case transitions, punctuation, etc.

Example:
- Input: "Ultra-HD 65\" Smart TV (2023)"
- Output tokens: "ultra", "hd", "65", "smart", "tv", "2023"

### N-gram Analyzer

The `ngram_analyzer` generates n-grams for partial matching, useful for fuzzy search.

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase`, `asciifolding`
  - `ngram_filter` - Creates n-grams of size 2-20

Example:
- Input: "shirt"
- Output tokens: "sh", "shi", "shir", "shirt", "hi", "hir", "hirt", "ir", "irt", "rt"

### HTML Analyzer

The `html_analyzer` processes HTML content for searching.

Components:
- **Char Filter**: `html_strip` - Removes HTML tags
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase`, `asciifolding`
  - `stop` - Removes common stop words

Example:
- Input: "<p>The <strong>best</strong> deals</p>"
- Output tokens: "the", "best", "deals"

### Content Title Analyzer

The `content_title_analyzer` is optimized for content titles and headings.

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase`, `asciifolding`
  - `word_delimiter_graph`

Example:
- Input: "How-to: Choose the Perfect Jeans"
- Output tokens: "how", "to", "choose", "the", "perfect", "jeans"

### Search-as-You-Type Analyzer

The `search_as_you_type_analyzer` enables real-time search suggestions.

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase`, `asciifolding`
  - `edge_ngram_filter` - Creates n-grams from the beginning of tokens

Example:
- Input: "blue"
- Output tokens: "b", "bl", "blu", "blue"

### SKU Analyzer

The `sku_analyzer` handles product SKUs and codes with special formatting.

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase`
  - `word_delimiter_graph` - Splits on punctuation and case changes

Example:
- Input: "LP-2023-BLU-M"
- Output tokens: "lp", "2023", "blu", "m"

## Filter Descriptions

### N-gram Filter

The `ngram_filter` creates n-grams between specified min and max lengths.
- **min_gram**: 2 - Minimum n-gram size
- **max_gram**: 20 - Maximum n-gram size

### Edge N-gram Filter

The `edge_ngram_filter` creates n-grams that start from the beginning of tokens.
- **min_gram**: 1 - Minimum n-gram size
- **max_gram**: 20 - Maximum n-gram size

### Synonym Filter

The `synonym` filter expands tokens with synonyms defined in a file.
- **synonyms_path**: "analysis/synonyms.txt" - Path to synonyms file
- **Format**: One set of synonyms per line, comma-separated

### English Filters

- **english_stop**: Removes English stop words
- **english_stemmer**: Applies English stemming rules
- **english_possessive_stemmer**: Removes possessive suffixes

## Normalizer Description

### Lowercase Normalizer

The `lowercase_normalizer` standardizes text for exact matching fields without tokenization.
- **Filters**:
  - `lowercase` - Converts characters to lowercase
  - `asciifolding` - Normalizes accented characters

## Custom Dictionary Files

### Synonyms File

Location: `analysis/synonyms.txt`

Format:
```
smartphone, mobile phone, cell phone
television, tv
laptop, notebook
jeans, denim pants
```

## Implementation Guidelines

1. **Adding Analyzers to Existing Indices**:
   Use the close/open API to update analyzers on existing indices:
   ```bash
   POST products/_close
   PUT products/_settings
   {
     "analysis": { ... }
   }
   POST products/_open
   ```

2. **Testing Analyzers**:
   Use the Analyze API to test analyzer behavior:
   ```bash
   GET /_analyze
   {
     "analyzer": "product_name_analyzer",
     "text": "Ultra-HD 65\" Smart TV (2023)"
   }
   ```

3. **Field-Specific Analysis**:
   Apply different analyzers to different fields based on search requirements:
   ```json
   "mappings": {
     "properties": {
       "name": {
         "type": "text",
         "analyzer": "product_name_analyzer",
         "search_analyzer": "standard"
       }
     }
   }
   ```

4. **Multi-field Analysis**:
   Use multi-fields to apply different analyzers to the same content:
   ```json
   "name": {
     "type": "text",
     "analyzer": "standard",
     "fields": {
       "ngram": {
         "type": "text",
         "analyzer": "ngram_analyzer"
       },
       "keyword": {
         "type": "keyword",
         "normalizer": "lowercase_normalizer"
       }
     }
   }
   ```

## Maintenance and Optimization

1. **Synonym Expansion**:
   - Regularly review and update synonym lists based on search logs
   - Consider automated expansion from search clickthrough data

2. **Performance Considerations**:
   - N-gram fields consume more index space and memory
   - Edge N-grams are more efficient for prefix matching than regular N-grams
   - Limit synonym expansion in high-volume fields

3. **Tuning Guidelines**:
   - Monitor query latency when introducing new analyzers
   - Balance precision (exact matching) and recall (finding more results)
   - Consider search-time vs. index-time analysis tradeoffs

4. **Custom Dictionary Updates**:
   - Implement a process for regularly updating synonym dictionaries
   - Use a staging environment to test impacts of dictionary changes
   - Document domain-specific terms in the synonym dictionary