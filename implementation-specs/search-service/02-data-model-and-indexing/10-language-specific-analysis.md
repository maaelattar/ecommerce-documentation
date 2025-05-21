# Language-Specific Analysis Configuration

## Overview

This document defines the language-specific text analysis configurations for the Search Service. Proper language analysis is essential for delivering relevant search results across different languages, as each language has unique characteristics that require specialized processing.

## Supported Languages

The search service provides specialized analysis configurations for the following languages:

1. English (Default)
2. Spanish
3. French
4. German
5. Italian
6. Portuguese
7. Dutch
8. Russian
9. Arabic
10. Chinese (Simplified)
11. Japanese
12. Korean

## Analysis Configuration

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "english": {
          "tokenizer": "standard",
          "filter": [
            "english_possessive_stemmer",
            "lowercase",
            "english_stop",
            "english_stemmer"
          ]
        },
        "spanish": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "spanish_stop",
            "spanish_stemmer"
          ]
        },
        "french": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "french_elision",
            "french_stop",
            "french_stemmer"
          ]
        },
        "german": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "german_normalization",
            "german_stop",
            "german_stemmer"
          ]
        },
        "italian": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "italian_elision",
            "italian_stop",
            "italian_stemmer"
          ]
        },
        "portuguese": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "portuguese_stop",
            "portuguese_stemmer"
          ]
        },
        "dutch": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "dutch_stop",
            "dutch_stemmer"
          ]
        },
        "russian": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "russian_stop",
            "russian_stemmer"
          ]
        },
        "arabic": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "arabic_normalization",
            "arabic_stop",
            "arabic_stemmer"
          ]
        },
        "cjk": {
          "tokenizer": "standard",
          "filter": [
            "cjk_width",
            "lowercase",
            "cjk_bigram",
            "cjk_stop"
          ]
        },
        "chinese": {
          "tokenizer": "smartcn_tokenizer",
          "filter": [
            "lowercase",
            "smartcn_stop"
          ]
        },
        "japanese": {
          "tokenizer": "kuromoji_tokenizer",
          "filter": [
            "kuromoji_baseform",
            "kuromoji_part_of_speech",
            "cjk_width",
            "lowercase",
            "kuromoji_stemmer",
            "ja_stop"
          ]
        },
        "korean": {
          "tokenizer": "nori_tokenizer",
          "filter": [
            "nori_part_of_speech",
            "lowercase",
            "nori_readingform",
            "ko_stop"
          ]
        }
      },
      "filter": {
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
        },
        "spanish_stop": {
          "type": "stop",
          "stopwords": "_spanish_"
        },
        "spanish_stemmer": {
          "type": "stemmer",
          "language": "spanish"
        },
        "french_elision": {
          "type": "elision",
          "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"]
        },
        "french_stop": {
          "type": "stop",
          "stopwords": "_french_"
        },
        "french_stemmer": {
          "type": "stemmer",
          "language": "french"
        },
        "german_normalization": {
          "type": "german_normalization"
        },
        "german_stop": {
          "type": "stop",
          "stopwords": "_german_"
        },
        "german_stemmer": {
          "type": "stemmer",
          "language": "german"
        },
        "italian_elision": {
          "type": "elision",
          "articles": ["c", "l", "all", "dall", "dell", "nell", "sull", "coll", "pell", "gl", "agl", "dagl", "degl", "negl", "sugl", "un", "m", "t", "s", "v", "d"]
        },
        "italian_stop": {
          "type": "stop",
          "stopwords": "_italian_"
        },
        "italian_stemmer": {
          "type": "stemmer",
          "language": "italian"
        },
        "portuguese_stop": {
          "type": "stop",
          "stopwords": "_portuguese_"
        },
        "portuguese_stemmer": {
          "type": "stemmer",
          "language": "portuguese"
        },
        "dutch_stop": {
          "type": "stop",
          "stopwords": "_dutch_"
        },
        "dutch_stemmer": {
          "type": "stemmer",
          "language": "dutch"
        },
        "russian_stop": {
          "type": "stop",
          "stopwords": "_russian_"
        },
        "russian_stemmer": {
          "type": "stemmer",
          "language": "russian"
        },
        "arabic_normalization": {
          "type": "arabic_normalization"
        },
        "arabic_stop": {
          "type": "stop",
          "stopwords": "_arabic_"
        },
        "arabic_stemmer": {
          "type": "stemmer",
          "language": "arabic"
        },
        "cjk_width": {
          "type": "cjk_width"
        },
        "cjk_bigram": {
          "type": "cjk_bigram",
          "ignored_scripts": ["hangul", "hiragana", "katakana"]
        },
        "cjk_stop": {
          "type": "stop",
          "stopwords_path": "analysis/cjk_stop.txt"
        },
        "smartcn_stop": {
          "type": "stop",
          "stopwords_path": "analysis/smartcn_stop.txt"
        },
        "ja_stop": {
          "type": "stop",
          "stopwords_path": "analysis/ja_stop.txt"
        },
        "ko_stop": {
          "type": "stop",
          "stopwords_path": "analysis/ko_stop.txt"
        }
      }
    }
  }
}
```

## Language-Specific Analyzer Descriptions

### English Analyzer

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `english_possessive_stemmer` - Removes possessive endings ('s)
  - `lowercase` - Normalizes case
  - `english_stop` - Removes English stop words
  - `english_stemmer` - Applies English stemming algorithm

Example:
- Input: "The car's engine was running smoothly"
- Output tokens: "car", "engin", "run", "smooth"

### Spanish Analyzer

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase` - Normalizes case
  - `spanish_stop` - Removes Spanish stop words
  - `spanish_stemmer` - Applies Spanish stemming algorithm

Example:
- Input: "Los zapatos rojos son nuevos"
- Output tokens: "zapat", "roj", "nuev"

### French Analyzer

Components:
- **Tokenizer**: `standard`
- **Filters**:
  - `lowercase` - Normalizes case
  - `french_elision` - Removes elisions (l', d', etc.)
  - `french_stop` - Removes French stop words
  - `french_stemmer` - Applies French stemming algorithm

Example:
- Input: "L'histoire des chaussures rouges"
- Output tokens: "histoir", "chaussur", "roug"

### CJK (Chinese, Japanese, Korean) Analyzers

#### Chinese Analyzer
- Uses the Smart Chinese Analysis plugin with specialized tokenization

#### Japanese Analyzer
- Uses the Kuromoji Analysis plugin for Japanese text analysis
- Handles decompounding, part-of-speech filtering, and stemming

#### Korean Analyzer
- Uses the Nori Analysis plugin for Korean text analysis
- Handles word extraction, part-of-speech filtering, and reading form normalization

## Multi-language Field Configuration

Example mapping for a multi-language product name field:

```json
"name": {
  "type": "text",
  "analyzer": "standard",
  "fields": {
    "english": {
      "type": "text",
      "analyzer": "english"
    },
    "spanish": {
      "type": "text",
      "analyzer": "spanish"
    },
    "french": {
      "type": "text",
      "analyzer": "french"
    }
  }
}
```

## Language Detection and Routing

For content where the language is unknown at index time:

1. **Detection Strategy**:
   - Use language detection libraries during indexing
   - Store detected language in a separate field
   - Apply language-specific analysis to appropriate fields

2. **Implementation Example**:
   ```json
   PUT products/_doc/123
   {
     "name": "Blue Cotton T-Shirt",
     "description": "Comfortable blue t-shirt made from premium cotton.",
     "detected_language": "en",
     "name_localized": {
       "en": "Blue Cotton T-Shirt",
       "es": "Camiseta de Algodón Azul",
       "fr": "T-shirt Bleu en Coton"
     }
   }
   ```

3. **Language-Specific Search**:
   ```json
   GET products/_search
   {
     "query": {
       "bool": {
         "should": [
           {
             "match": {
               "name.english": {
                 "query": "cotton shirts",
                 "boost": 1.5
               }
             }
           },
           {
             "match": {
               "name_localized.en": "cotton shirts"
             }
           }
         ]
       }
     }
   }
   ```

## Custom Dictionary Files

### Stop Words

- **Path Format**: `analysis/{language}_stop.txt`
- **Content Format**: One stop word per line

Example for custom Japanese stop words (`analysis/ja_stop.txt`):
```
これ
それ
あれ
この
その
あの
```

## Implementation Guidelines

1. **Plugin Requirements**:
   - For CJK languages, install the required analysis plugins:
     - Chinese: Smart Chinese Analysis plugin
     - Japanese: Kuromoji Analysis plugin
     - Korean: Nori Analysis plugin

2. **Field Configuration Strategy**:
   - For known single-language content: Use language-specific analyzer directly
   - For fields with mixed languages: Use multi-fields with language-specific sub-fields
   - For user queries: Detect query language or use language-agnostic analyzers

3. **Testing Language Analysis**:
   Use the Analyze API to test analyzer behavior:
   ```bash
   GET /_analyze
   {
     "analyzer": "french",
     "text": "Les chaussures rouges sont très belles"
   }
   ```

4. **Search-Time Language Selection**:
   - For multi-language applications, send queries to language-specific fields
   - Consider boosting native language fields higher than others

5. **Handling Special Cases**:
   - For product names that should not be stemmed: Use keyword fields
   - For brand names and proper nouns: Consider custom token filters

## Maintenance and Optimization

1. **Stopwords Updates**:
   - Regularly review and update language-specific stopword lists
   - Monitor impact on recall and precision metrics

2. **Dictionary Customization**:
   - Maintain domain-specific dictionaries for specialized terminology
   - For CJK languages, consider custom dictionaries for domain-specific terms

3. **User Language Preferences**:
   - Store user language preferences
   - Boost results in the user's preferred language