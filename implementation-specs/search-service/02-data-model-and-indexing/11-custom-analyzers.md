# Custom Analyzers

## Overview

This document defines custom analyzers designed specifically for the e-commerce search service. These analyzers address domain-specific search requirements that aren't fully satisfied by the standard or language-specific analyzers.

## Custom Analyzer Definitions

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "sku_code_analyzer": {
          "type": "custom",
          "tokenizer": "whitespace",
          "filter": [
            "lowercase",
            "sku_word_delimiter"
          ]
        },
        "color_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "color_synonym"
          ]
        },
        "product_taxonomy_analyzer": {
          "type": "custom",
          "tokenizer": "path_hierarchy",
          "filter": [
            "lowercase"
          ]
        },
        "size_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "size_synonym",
            "size_equivalent"
          ],
          "char_filter": [
            "size_char_filter"
          ]
        },
        "price_range_analyzer": {
          "type": "custom",
          "tokenizer": "keyword",
          "filter": [
            "price_range_filter"
          ]
        },
        "phonetic_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "phonetic_filter"
          ]
        },
        "brand_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "brand_synonym",
            "asciifolding"
          ],
          "char_filter": [
            "brand_char_filter"
          ]
        },
        "fashion_attribute_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "fashion_synonym",
            "asciifolding"
          ]
        },
        "tech_spec_analyzer": {
          "type": "custom",
          "tokenizer": "whitespace",
          "filter": [
            "lowercase",
            "tech_unit_normalization"
          ],
          "char_filter": [
            "tech_char_filter"
          ]
        }
      },
      "char_filter": {
        "size_char_filter": {
          "type": "pattern_replace",
          "pattern": "([0-9]+)\\s*([xX])\\s*([0-9]+)",
          "replacement": "$1x$3"
        },
        "brand_char_filter": {
          "type": "mapping",
          "mappings": [
            "& => and",
            "\\+ => plus",
            "@ => at"
          ]
        },
        "tech_char_filter": {
          "type": "pattern_replace",
          "pattern": "([0-9]+)\\s*([kKmMgGtTpP][bB])",
          "replacement": "$1$2"
        }
      },
      "filter": {
        "sku_word_delimiter": {
          "type": "word_delimiter_graph",
          "generate_word_parts": true,
          "generate_number_parts": true,
          "catenate_words": false,
          "catenate_numbers": false,
          "catenate_all": false,
          "split_on_case_change": true,
          "preserve_original": true,
          "split_on_numerics": true,
          "stem_english_possessive": false
        },
        "color_synonym": {
          "type": "synonym_graph",
          "synonyms_path": "analysis/color_synonyms.txt"
        },
        "size_synonym": {
          "type": "synonym_graph",
          "synonyms_path": "analysis/size_synonyms.txt"
        },
        "size_equivalent": {
          "type": "synonym_graph",
          "synonyms_path": "analysis/size_equivalents.txt"
        },
        "price_range_filter": {
          "type": "pattern_capture",
          "patterns": [
            "\\$([0-9]+)-\\$?([0-9]+)",
            "under\\s+\\$([0-9]+)",
            "over\\s+\\$([0-9]+)"
          ],
          "preserve_original": true
        },
        "phonetic_filter": {
          "type": "phonetic",
          "encoder": "double_metaphone",
          "replace": false
        },
        "brand_synonym": {
          "type": "synonym_graph",
          "synonyms_path": "analysis/brand_synonyms.txt"
        },
        "fashion_synonym": {
          "type": "synonym_graph",
          "synonyms_path": "analysis/fashion_synonyms.txt"
        },
        "tech_unit_normalization": {
          "type": "synonym_graph",
          "synonyms": [
            "gb, gigabyte, gigabytes",
            "mb, megabyte, megabytes",
            "tb, terabyte, terabytes",
            "ghz, gigahertz",
            "mhz, megahertz"
          ]
        }
      }
    }
  }
}
```

## Custom Analyzer Descriptions

### SKU Code Analyzer

The `sku_code_analyzer` handles product SKUs and internal codes with special formatting patterns.

Components:
- **Tokenizer**: `whitespace` - Treats spaces as token boundaries
- **Filters**:
  - `lowercase` - Normalizes case
  - `sku_word_delimiter` - Custom word delimiter configuration

Purpose:
- Process model numbers and SKUs that may include alphanumerics, hyphens, and dots
- Enable searching for parts of SKUs

Example:
- Input: "LP-2023-BLU-M"
- Output tokens: "lp", "lp-2023-blu-m", "2023", "blu", "m"

### Color Analyzer

The `color_analyzer` handles color terms with synonyms for improved search accuracy.

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase` - Normalizes case
  - `color_synonym` - Expands color terms with synonyms

Purpose:
- Match color variations and synonyms (navy, navy blue, dark blue)
- Normalize color descriptions

Example:
- Input: "navy"
- Output tokens: "navy", "navy blue", "dark blue"

### Product Taxonomy Analyzer

The `product_taxonomy_analyzer` processes hierarchical category paths.

Components:
- **Tokenizer**: `path_hierarchy` - Treats delimiters as path components
- **Filters**:
  - `lowercase` - Normalizes case

Purpose:
- Enable search at any level of the category hierarchy
- Support partial category path matching

Example:
- Input: "Clothing/Men's/Jeans"
- Output tokens: "clothing", "clothing/men's", "clothing/men's/jeans"

### Size Analyzer

The `size_analyzer` handles size information across different sizing systems.

Components:
- **Char Filter**: `size_char_filter` - Normalizes size formats (e.g., "38 x 32" to "38x32")
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase` - Normalizes case
  - `size_synonym` - Expands size terms (e.g., "large" to "l")
  - `size_equivalent` - Maps between different sizing systems

Purpose:
- Normalize size formats
- Map between different sizing systems (US, EU, International)
- Handle apparel sizes, dimensions, etc.

Example:
- Input: "XL 42 Tall"
- Output tokens: "xl", "extra large", "42", "16.5", "tall"

### Price Range Analyzer

The `price_range_analyzer` processes price range expressions.

Components:
- **Tokenizer**: `keyword` - Treats the entire input as a single token
- **Filters**:
  - `price_range_filter` - Captures price range patterns

Purpose:
- Extract price bounds from range expressions
- Support price range queries

Example:
- Input: "$50-$100"
- Output tokens: "$50-$100", "50", "100"
- Input: "under $50"
- Output tokens: "under $50", "50"

### Phonetic Analyzer

The `phonetic_analyzer` enables sound-alike matching for misspelled terms.

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase` - Normalizes case
  - `phonetic_filter` - Adds phonetic encodings using Double Metaphone algorithm

Purpose:
- Support error-tolerant search for names and terms
- Improve recall for misspelled queries

Example:
- Input: "Smith"
- Output tokens: "smith", "SM0", "XMT"

### Brand Analyzer

The `brand_analyzer` handles brand names with special characters and common variations.

Components:
- **Char Filter**: `brand_char_filter` - Maps special characters in brand names
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase` - Normalizes case
  - `brand_synonym` - Expands brand names with common variations
  - `asciifolding` - Removes diacritics

Purpose:
- Normalize brand name variations
- Handle special characters in brand names
- Support common abbreviations and misspellings

Example:
- Input: "H&M"
- Output tokens: "h", "and", "m", "hm"

### Fashion Attribute Analyzer

The `fashion_attribute_analyzer` handles fashion-specific terminology.

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase` - Normalizes case
  - `fashion_synonym` - Expands fashion terms with synonyms
  - `asciifolding` - Removes diacritics

Purpose:
- Normalize fashion terminology
- Map between different terms for the same concept

Example:
- Input: "v-neck"
- Output tokens: "v-neck", "v neck", "vneck"

### Tech Spec Analyzer

The `tech_spec_analyzer` handles technical specifications with units.

Components:
- **Char Filter**: `tech_char_filter` - Normalizes format of measurements with units
- **Tokenizer**: `whitespace`
- **Filters**:
  - `lowercase` - Normalizes case
  - `tech_unit_normalization` - Normalizes unit terms

Purpose:
- Normalize technical specifications
- Handle different unit expressions

Example:
- Input: "8 GB RAM"
- Output tokens: "8gb", "ram", "8", "gigabyte", "gigabytes"

## Custom Dictionary Files

### Color Synonyms

Location: `analysis/color_synonyms.txt`

Example Content:
```
navy, navy blue, dark blue
burgundy, maroon, wine, wine red
beige, tan, cream, off-white
teal, turquoise, aqua
gray, grey
```

### Size Synonyms

Location: `analysis/size_synonyms.txt`

Example Content:
```
xl, extra large, xtra large
l, large
m, medium
s, small
xs, extra small, xtra small
```

### Size Equivalents

Location: `analysis/size_equivalents.txt`

Example Content:
```
us 6, eu 36, uk 4
us 8, eu 38, uk 6
us 10, eu 40, uk 8
us 12, eu 42, uk 10
42 => 16.5, 16 1/2
```

### Brand Synonyms

Location: `analysis/brand_synonyms.txt`

Example Content:
```
j crew, j. crew, jcrew
calvin klein, ck
louis vuitton, lv
h&m, h & m, hm
```

### Fashion Synonyms

Location: `analysis/fashion_synonyms.txt`

Example Content:
```
jeans, denim pants, denims
t-shirt, tshirt, t shirt, tee
sneakers, athletic shoes, trainers
hoodie, hooded sweatshirt
```

## Implementation Guidelines

1. **Field Configuration**:
   Apply custom analyzers to specific fields in the mapping:
   
   ```json
   "mappings": {
     "properties": {
       "sku": {
         "type": "text",
         "analyzer": "sku_code_analyzer"
       },
       "color": {
         "type": "text",
         "analyzer": "color_analyzer",
         "fields": {
           "keyword": {
             "type": "keyword",
             "normalizer": "lowercase_normalizer"
           }
         }
       },
       "category_path": {
         "type": "text",
         "analyzer": "product_taxonomy_analyzer"
       }
     }
   }
   ```

2. **Testing Custom Analyzers**:
   Use the Analyze API to test behavior:
   
   ```json
   GET /_analyze
   {
     "analyzer": "color_analyzer",
     "text": "navy"
   }
   ```

3. **Dictionary Maintenance**:
   - Store synonym files in a version-controlled repository
   - Implement a process for reviewing and updating synonyms
   - Consider automating synonym discovery from search logs

4. **Mixed Analyzer Strategy**:
   Use multi-fields for different analysis needs:
   
   ```json
   "brand": {
     "type": "text",
     "analyzer": "brand_analyzer",
     "fields": {
       "keyword": {
         "type": "keyword",
         "normalizer": "lowercase_normalizer"
       },
       "phonetic": {
         "type": "text",
         "analyzer": "phonetic_analyzer"
       }
     }
   }
   ```

## Maintenance and Optimization

1. **Synonym Expansion**:
   - Regularly review search logs to identify missed synonym opportunities
   - Analyze zero-result searches for potential synonym additions
   - Consider domain-specific synonyms based on product categories

2. **Performance Considerations**:
   - Synonym expansion increases index size and query complexity
   - Use multi-fields approach to limit synonym usage to specific needs
   - Monitor query performance when adding new synonyms

3. **A/B Testing**:
   - Test new analyzers and synonym sets with A/B testing
   - Measure impact on key metrics: conversion rate, zero-result searches, click-through rate