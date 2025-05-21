# Search Service - Query DSL and Features

## 1. Overview

This document describes how user search queries and API parameters are translated into the underlying Search Engine's Domain Specific Language (DSL) queries (e.g., OpenSearch/Elasticsearch Query DSL). It also outlines key search features supported.

## 2. Core Query Construction

When a user searches via the `/v1/search/products` API with a query string (`q=...`), the Search Service constructs a sophisticated query to the search engine.

### 2.1. Full-Text Search (`q` parameter)

*   **`multi_match` Query**: The `q` parameter is typically used in a `multi_match` query targeting multiple text fields with different weightings.
    *   **Fields and Boosts (Example)**:
        *   `name^5` (Product name, highest boost)
        *   `sku^4` (SKU, high boost for direct matches)
        *   `brand_name^3`
        *   `category_names^2`
        *   `keywords^2` (Tags)
        *   `description_short^1.5`
        *   `attributes.value_string^1` (Searchable attribute values)
        *   `description_long^0.5` (Lowest boost)
    *   **Type**: `best_fields` or `most_fields` might be used depending on desired behavior. `cross_fields` could be useful for queries spanning multiple fields conceptually.
    *   **Fuzziness**: `AUTO` fuzziness can be applied to handle typos (e.g., `fuzziness: "AUTO:3,6"` allows 1 edit for terms 3-6 chars long, 2 edits for longer).
    *   **Operator**: Default to `OR` for broader matching, but potentially switch to `AND` if all terms must match, or allow user to specify via advanced syntax (less common for e-commerce).
    *   **Synonyms**: Synonym graph token filters applied at index time or query time will expand terms.

### 2.2. Filtering (Facets)

*   API filter parameters (e.g., `category=cat123`, `brand=BrandX`, `attributes.color=Red`, `price_min=10&price_max=50`) are translated into `filter` clauses within the search engine's boolean query.
*   **`term` / `terms` Queries**: Used for exact matches on `keyword` fields (e.g., category IDs, brand names, attribute values).
    *   Example: `{"term": {"category_ids": "cat123"}}`
    *   Example: `{"terms": {"attributes.color.keyword": ["Red", "Pink"]}}` (if color is a keyword field)
*   **`range` Queries**: Used for numeric or date ranges (e.g., price, rating, created_at).
    *   Example: `{"range": {"price_current": {"gte": 10, "lte": 50}}}`
*   Filters are non-scoring, meaning they refine the result set without affecting the relevance score of matched documents.

### 2.3. Boolean Query Structure

The overall search query is typically a `bool` query:

```json
{
  "query": {
    "bool": {
      "must": [
        // Contains the multi_match query for the 'q' parameter if provided
        // { "multi_match": { "query": "user query", "fields": [...], ... } }
      ],
      "filter": [
        // Contains all term/terms/range queries from filter parameters
        // { "term": { "brand_name.keyword": "BrandX" } },
        // { "range": { "price_current": { "gte": 10, "lte": 50 } } }
        { "term": { "is_available": true } } // Example: Always filter for available products by default
      ],
      "should": [
        // Optional: Clauses that are good to match but not required.
        // Can be used for boosting documents that match certain criteria without excluding others.
        // e.g., boost new arrivals or featured products if no specific sort order is chosen.
        // { "term": { "is_new_arrival": { "value": true, "boost": 1.5 } } }
      ],
      "must_not": [
        // Optional: Clauses to exclude specific documents.
        // e.g., { "term": { "status": "discontinued" } }
      ]
    }
  }
  // ... aggregations, sorting, pagination added here ...
}
```

## 3. Faceting (Aggregations)

*   If `include_facets=true`, the Search Service adds `aggregations` (aggs) to the search engine query to calculate facet counts.
*   **`terms` Aggregation**: Used for fields like `brand_name.keyword`, `category_names.keyword`, `attributes.color.keyword`, etc., to get counts for each unique value.
*   **`range` Aggregation**: Used for price ranges or rating ranges.
*   **`nested` Aggregation**: If attributes are stored in a `nested` field, nested aggregations are needed to correctly facet on them.
*   Facet counts are calculated based on the result set *after* all filters have been applied, except for the filter corresponding to the facet itself (post-filtering for self-selected facets).

## 4. Sorting

*   The `sort_by` API parameter determines the `sort` clause in the search engine query.
*   **Relevance (`_score`)**: Default sort. Uses the search engine's calculated relevance score.
*   **Field Sorting**: Sorting by fields like `price_current`, `created_at`, `average_rating`, `name.keyword`.
    *   Example: `"sort": [{ "price_current": { "order": "asc" } }]`
*   Multiple sort criteria can be applied (e.g., sort by rating descending, then by price ascending).

## 5. Suggestions (Typeahead)

The `/v1/search/suggest` API uses different query types optimized for speed and prefix matching:

*   **`completion` Suggester**: If using Elasticsearch/OpenSearch completion suggester. Requires specific mapping for suggestion fields.
    *   Fast prefix-based suggestions.
    *   Can have contexts (e.g., suggest categories only if user types in category context).
*   **`search_as_you_type` Field Type**: A newer field type that provides good support for typeahead on multiple fields.
*   **Prefix Queries on `keyword` or `text_analyzed` fields**: Can be used but might be slower than dedicated suggesters for high-volume typeahead.
    *   Example on an edge N-gram analyzed field for product names.
*   The query for suggestions will typically be simpler, focusing on matching prefixes in fields like `name_exact`, `category_names`, `brand_name`.
*   Results might be blended from multiple suggestion sources (products, categories, brands, popular queries).

## 6. Advanced Features

### 6.1. Spell Check / Typo Tolerance
*   Handled by `fuzziness` in `multi_match` queries.
*   Alternatively, a `phrase_suggester` (did-you-mean feature) can be implemented to suggest alternative spellings if a query yields few or no results.

### 6.2. Synonym Expansion
*   Managed by synonym graph token filters in the search engine's analyzers.
*   Applied at index time or query time (query time is often more flexible for updating synonyms without re-indexing).
*   Synonym lists can be managed via the Search Service admin API.

### 6.3. Highlighting
*   Search results can include highlighted snippets showing where the query terms matched in the document fields (e.g., `<strong>matched_term</strong>`).
*   Configured via the `highlight` clause in the search engine query.

### 6.4. Pagination
*   Handled by `from` and `size` parameters in the search engine query (derived from `page` and `limit` API parameters).
*   Deep pagination can be performance-intensive; consider alternatives like `search_after` for very deep scrolling if needed.

### 6.5. Language-Specific Analysis
*   If supporting multiple languages, use language-specific analyzers (e.g., `english` analyzer, `french` analyzer) for appropriate stemming and stop word removal for `text_analyzed` fields.
*   The language might be determined by user locale or by indexing content in multiple languages.

## 7. Query Logging and Analytics

*   The Search Service (or the search engine itself) should log executed queries (anonymized or with user context if privacy permits).
*   This data is invaluable for understanding user behavior, identifying popular search terms, finding queries with no results, and tuning relevance.
