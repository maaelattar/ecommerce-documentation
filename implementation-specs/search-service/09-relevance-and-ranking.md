# Search Service - Relevance and Ranking Strategy

## 1. Overview

Search relevance is paramount for a positive user experience and successful e-commerce outcomes. This document outlines the strategy for achieving and continuously improving the relevance of search results provided by the Search Service. It involves a combination of text relevance, business rules, and potentially personalization.

## 2. Core Relevance Factors (Search Engine Based)

The underlying search engine (e.g., OpenSearch/Elasticsearch) provides a sophisticated relevance scoring mechanism, typically based on algorithms like BM25 (Okapi BM25) which considers:

*   **Term Frequency (TF)**: How often a search term appears in a document field.
*   **Inverse Document Frequency (IDF)**: How rare a term is across all documents in the index. Rarer terms get higher weight.
*   **Field Length Normalization**: Shorter fields matching the term are often considered more relevant.

These factors are the foundation, but we will build upon them.

## 3. Techniques for Tuning Relevance

### 3.1. Field Weighting (Boosting at Query Time)
*   As described in `08-query-dsl-and-features.md`, the `multi_match` query will assign different boosts (weights) to different fields.
    *   Example: `name^5`, `sku^4`, `brand_name^3`, `category_names^2`, `description_short^1.5`.
*   These weights are configurable and can be adjusted based on performance analysis and business priorities.

### 3.2. Query Structure and Clauses
*   **`must` vs. `should` clauses**: Using `should` clauses in a boolean query allows us to boost documents matching certain criteria without strictly requiring them, influencing the score positively.
*   **Function Score Query**: For more advanced control, the `function_score` query can be used to modify scores based on:
    *   **Field Value Factor**: Boost based on the value of a numeric field (e.g., `popularity_score`, `average_rating`).
    *   **Decay Functions**: Boost or penalize based on proximity to a date (e.g., boost newer products) or a numeric value.
    *   **Script Score**: Use custom scripts for complex scoring logic (use with caution due to performance implications).
    *   **Weight**: Assign a weight to documents matching a filter, then combine with the original query score.

### 3.3. Index-Time Strategies
*   **Proper Analysis**: Ensuring text fields are analyzed correctly (tokenization, stemming, lowercase, synonyms) is crucial for matching.
    *   Language-specific analyzers for different languages.
*   **Denormalization**: Having rich, relevant data in the search document allows the scoring algorithm to work effectively.
*   **Shingles/N-grams**: Indexing shingles (adjacent word pairs/triplets) can improve phrase matching relevance.

### 3.4. Business Rule Boosting/Burying
*   **Boosting on Promotion/Flags**: Boost products that are on sale, new arrivals, featured, or best-sellers.
    *   Can be done using `should` clauses with boosts, or via `function_score` with filters.
    *   Example: `{"term": {"is_new_arrival": {"value": true, "boost": 1.2}}}` in a `should` clause.
*   **Inventory-Aware Ranking**: 
    *   Slightly demote (but not hide) products with very low stock to prioritize items that are readily available, if desired.
    *   Out-of-stock items should ideally be filtered out by default or heavily penalized in ranking unless the user explicitly requests to see them.
*   **Brand Boosting**: Business may want to boost certain brands, either globally or for specific queries.

## 4. Synonym Management
*   Crucial for bridging the vocabulary gap between users and the product catalog.
*   Synonym lists (e.g., "pants" = "trousers", "phone" = "smartphone") will be managed (potentially via an admin interface).
*   Applied using synonym graph token filters in the search engine's analyzers, ideally at query time for flexibility.

## 5. Personalization (Future Enhancement)

While not in the initial MVP, personalization is a key area for future relevance improvement.

*   **User-Specific Boosting**: Boost products/categories/brands that a user has previously interacted with (viewed, added to cart, purchased, wishlisted).
*   **Collaborative Filtering**: "Users who searched for X also viewed/bought Y."
*   **Search History**: Use a user's past search queries to infer intent and tailor current results.
*   **A/B Testing**: Personalization strategies would require rigorous A/B testing.
*   Requires integration with user activity tracking systems and potentially machine learning models.

## 6. Measuring and Iterating on Relevance

Relevance is not a one-time setup; it requires continuous monitoring and improvement.

### 6.1. Key Metrics
*   **Click-Through Rate (CTR)**: Percentage of displayed search results that get clicked.
*   **Conversion Rate from Search**: Percentage of searches that lead to a purchase.
*   **Average Click Position**: Lower is better (users find relevant items quickly).
*   **Zero-Result Queries**: Number of queries that return no results. Indicates content gaps or query understanding issues.
*   **Queries with High Abandonment**: Searches where users don't click any results or leave the site.
*   **User Feedback**: Direct feedback mechanisms (e.g., "Was this search helpful?").

### 6.2. Tools and Techniques
*   **Search Analytics Dashboards**: To track the metrics above.
*   **A/B Testing Framework**: To compare different relevance models, field weights, or algorithms.
    *   The Search Service API should support routing users to different test groups or applying different ranking profiles.
*   **Judgment Lists / Human Evaluation**: Create sets of benchmark queries and have human evaluators rate the quality of results from different ranking models.
*   **Offline Evaluation Metrics**: Using historical data and judgment lists to calculate metrics like nDCG (Normalized Discounted Cumulative Gain), MAP (Mean Average Precision).
*   **Regular Review Meetings**: Cross-functional teams (Search PM, engineers, data scientists, merchandisers) to review performance and plan improvements.

## 7. Handling "No Results"

*   **Broaden Search**: Automatically re-run query with fewer terms or more aggressive fuzziness.
*   **Spell Check / "Did You Mean?"**: Offer alternative spellings.
*   **Synonym Expansion**: Ensure comprehensive synonyms are in place.
*   **Fallbacks**: If no products match, suggest related categories, popular products, or helpful articles.
*   **Logging**: Log zero-result queries to identify content gaps or issues with query understanding.

## 8. Configuration Management

*   Relevance configurations (field weights, boosting rules, synonym lists) need to be managed, versioned, and deployable.
*   Changes should be auditable and easy to roll back if they negatively impact performance.
*   An admin interface or controlled configuration files will be used for this.
