# Content Document Schema

## Overview

The content document schema defines the structure for storing marketing and informational content in Elasticsearch. This includes blog posts, articles, buying guides, FAQs, and other content types that enhance the e-commerce experience and can be included in search results alongside products.

## Schema Structure

```json
{
  "id": "string",                     // Unique content identifier
  "title": "string",                  // Content title
  "slug": "string",                   // URL-friendly identifier
  "content_type": "string",           // Type of content (blog, article, guide, etc.)
  "body": "text",                     // Main content body (HTML)
  "summary": "text",                  // Short summary or excerpt
  "status": "string",                 // Status (published, draft, archived)
  "visibility": "string",             // Visibility (public, private, restricted)
  "created_at": "date",               // Creation timestamp
  "updated_at": "date",               // Last update timestamp
  "published_at": "date",             // Publication timestamp
  
  "author": {                         // Content author
    "id": "string",                   // Author ID
    "name": "string",                 // Author name
    "email": "string",                // Author email
    "avatar_url": "string",           // Author avatar URL
    "bio": "string"                   // Author biography
  },
  
  "categories": [                     // Content categories
    {
      "id": "string",                 // Category ID
      "name": "string",               // Category name
      "slug": "string",               // Category slug
      "path": "string"                // Category path
    }
  ],
  
  "tags": ["string"],                 // Content tags
  
  "related_products": [               // Related product IDs
    "string"
  ],
  
  "related_content": [                // Related content IDs
    "string"
  ],
  
  "media": {                          // Content media
    "featured_image": {               // Featured image
      "url": "string",                // Image URL
      "alt": "string",                // Alt text
      "width": "integer",             // Image width in pixels
      "height": "integer"             // Image height in pixels
    },
    "gallery": [                      // Additional images
      {
        "url": "string",              // Image URL
        "alt": "string",              // Alt text
        "width": "integer",           // Image width
        "height": "integer",          // Image height
        "caption": "string"           // Image caption
      }
    ],
    "videos": [                       // Videos
      {
        "url": "string",              // Video URL
        "thumbnail": "string",        // Video thumbnail
        "title": "string",            // Video title
        "duration": "integer"         // Video duration in seconds
      }
    ],
    "attachments": [                  // Downloadable attachments
      {
        "url": "string",              // File URL
        "name": "string",             // File name
        "type": "string",             // File type
        "size": "integer"             // File size in bytes
      }
    ]
  },
  
  "attributes": {                     // Content attributes
    "reading_time": "integer",        // Estimated reading time in minutes
    "complexity_level": "string",     // Content complexity (beginner, intermediate, expert)
    "format": "string",               // Content format (article, video, infographic)
    "custom_attributes": [            // Dynamic custom attributes
      {
        "key": "string",              // Attribute key
        "value": "any",               // Attribute value
        "searchable": "boolean"       // Whether attribute is searchable
      }
    ]
  },
  
  "sections": [                       // Content sections for structured content
    {
      "id": "string",                 // Section ID
      "title": "string",              // Section title
      "content": "text",              // Section content
      "order": "integer"              // Section order
    }
  ],
  
  "seo": {                            // SEO metadata
    "title": "string",                // SEO title
    "description": "string",          // Meta description
    "keywords": ["string"],           // Meta keywords
    "canonical_url": "string",        // Canonical URL
    "robots": "string",               // Robots meta tag
    "open_graph": {                   // Open Graph metadata
      "title": "string",
      "description": "string",
      "image": "string",
      "type": "string"
    },
    "twitter_card": {                 // Twitter Card metadata
      "card": "string",
      "title": "string",
      "description": "string",
      "image": "string"
    }
  },
  
  "engagement": {                     // Engagement metrics
    "view_count": "integer",          // Number of views
    "like_count": "integer",          // Number of likes
    "comment_count": "integer",       // Number of comments
    "share_count": "integer",         // Number of shares
    "avg_time_on_page": "float"       // Average time spent on page (seconds)
  },
  
  "metadata": {                       // Miscellaneous metadata
    "created_by": "string",           // User who created the content
    "updated_by": "string",           // User who last updated the content
    "version": "integer",             // Document version
    "tenant_id": "string",            // Multi-tenant identifier
    "locale": "string",               // Content locale
    "translations": ["string"]        // IDs of translated versions
  }
}
```

## Field Descriptions

### Core Fields

- **id**: Unique identifier for the content, typically a UUID
- **title**: The content's main title
- **slug**: URL-friendly version of the title
- **content_type**: Type of content (blog, article, guide, FAQ, etc.)
- **body**: Main content body, typically HTML
- **summary**: Short excerpt or summary of the content
- **status**: Publication status (published, draft, archived)
- **visibility**: Content visibility (public, private, restricted)

### Author Information

- **author**: Information about the content author
  - **id**: Author identifier
  - **name**: Author name
  - **email**: Author email
  - **avatar_url**: URL to author's avatar image
  - **bio**: Short author biography

### Categorization

- **categories**: Categories the content belongs to
  - Array of category objects with id, name, slug, and path
- **tags**: Array of tag strings for additional categorization

### Related Items

- **related_products**: Array of product IDs related to the content
- **related_content**: Array of content IDs that are related

### Media

- **media**: Media assets associated with the content
  - **featured_image**: Primary image used for thumbnails and social sharing
  - **gallery**: Additional images included in the content
  - **videos**: Video content embedded in or related to the content
  - **attachments**: Downloadable files associated with the content

### Attributes

- **attributes**: Content characteristics
  - **reading_time**: Estimated time to read the content in minutes
  - **complexity_level**: Indicates the content's complexity (beginner, intermediate, expert)
  - **format**: Content format (article, video, infographic, etc.)
  - **custom_attributes**: Dynamic custom attributes for extensibility

### Content Structure

- **sections**: For structured content with distinct sections
  - **id**: Section identifier
  - **title**: Section heading
  - **content**: Section content
  - **order**: Numeric ordering of sections

### SEO

- **seo**: Search engine optimization data
  - **title**: Custom title tag
  - **description**: Meta description
  - **keywords**: Meta keywords
  - **canonical_url**: Canonical URL
  - **robots**: Robots meta directives
  - **open_graph**: Open Graph metadata for social sharing
  - **twitter_card**: Twitter Card metadata for Twitter sharing

### Engagement

- **engagement**: Metrics tracking user engagement
  - **view_count**: Number of page views
  - **like_count**: Number of likes or reactions
  - **comment_count**: Number of comments
  - **share_count**: Number of social shares
  - **avg_time_on_page**: Average time users spend on the content

## Sample Content Document

```json
{
  "id": "content-12345",
  "title": "How to Choose the Perfect Jeans for Your Body Type",
  "slug": "how-to-choose-perfect-jeans-body-type",
  "content_type": "guide",
  "body": "<p>Finding the perfect pair of jeans can be challenging. This comprehensive guide will help you understand different jean styles and which ones work best for your body type.</p><h2>Understanding Jean Fits</h2><p>Before diving into body types, let's review the main jean fits available:</p><ul><li><strong>Skinny:</strong> Tight throughout hip, thigh, and leg</li><li><strong>Slim:</strong> Fitted but not tight</li><li><strong>Straight:</strong> Same width from hip to ankle</li><li><strong>Bootcut:</strong> Slight flare at ankle</li><li><strong>Wide-leg:</strong> Loose throughout leg</li></ul>...",
  "summary": "Discover which jean styles best flatter your body type with our comprehensive guide to denim fits, rises, and washes.",
  "status": "published",
  "visibility": "public",
  "created_at": "2023-06-10T14:30:00Z",
  "updated_at": "2023-09-22T10:15:00Z",
  "published_at": "2023-06-12T08:00:00Z",
  
  "author": {
    "id": "author-42",
    "name": "Sarah Johnson",
    "email": "sarah.johnson@example.com",
    "avatar_url": "https://assets.example.com/authors/sarah-johnson.jpg",
    "bio": "Sarah is a fashion stylist with over 10 years of experience in the denim industry."
  },
  
  "categories": [
    {
      "id": "cat-fashion",
      "name": "Fashion Advice",
      "slug": "fashion-advice",
      "path": "Blog/Fashion Advice"
    },
    {
      "id": "cat-denim",
      "name": "Denim Guide",
      "slug": "denim-guide",
      "path": "Blog/Fashion Advice/Denim Guide"
    }
  ],
  
  "tags": [
    "jeans",
    "denim",
    "fashion",
    "style guide",
    "body positivity"
  ],
  
  "related_products": [
    "prod-12345",
    "prod-12346",
    "prod-12347"
  ],
  
  "related_content": [
    "content-12300",
    "content-12346"
  ],
  
  "media": {
    "featured_image": {
      "url": "https://assets.example.com/content/jeans-guide-main.jpg",
      "alt": "Different jean styles on diverse body types",
      "width": 1200,
      "height": 800
    },
    "gallery": [
      {
        "url": "https://assets.example.com/content/skinny-jeans.jpg",
        "alt": "Skinny jeans style",
        "width": 800,
        "height": 600,
        "caption": "Skinny jeans hug the legs from hip to ankle"
      },
      {
        "url": "https://assets.example.com/content/bootcut-jeans.jpg",
        "alt": "Bootcut jeans style",
        "width": 800,
        "height": 600,
        "caption": "Bootcut jeans flare slightly from the knee down"
      }
    ],
    "videos": [
      {
        "url": "https://assets.example.com/content/jean-fitting-guide.mp4",
        "thumbnail": "https://assets.example.com/content/jean-fitting-guide-thumb.jpg",
        "title": "How to Measure for the Perfect Jean Fit",
        "duration": 325
      }
    ],
    "attachments": [
      {
        "url": "https://assets.example.com/content/jean-size-chart.pdf",
        "name": "Comprehensive Jean Size Chart",
        "type": "application/pdf",
        "size": 1253467
      }
    ]
  },
  
  "attributes": {
    "reading_time": 8,
    "complexity_level": "beginner",
    "format": "article",
    "custom_attributes": [
      {
        "key": "season",
        "value": "all-season",
        "searchable": true
      },
      {
        "key": "editor_pick",
        "value": true,
        "searchable": false
      }
    ]
  },
  
  "sections": [
    {
      "id": "section-1",
      "title": "Understanding Jean Fits",
      "content": "<p>Before diving into body types, let's review the main jean fits available:</p><ul><li><strong>Skinny</strong>: Tight throughout hip, thigh, and leg</li><li><strong>Slim</strong>: Fitted but not tight</li><li><strong>Straight</strong>: Same width from hip to ankle</li><li><strong>Bootcut</strong>: Slight flare at ankle</li><li><strong>Wide-leg</strong>: Loose throughout leg</li></ul>",
      "order": 1
    },
    {
      "id": "section-2",
      "title": "Jean Rises Explained",
      "content": "<p>The 'rise' refers to the distance from the crotch seam to the top of the waistband:</p><ul><li><strong>Low-rise</strong>: Sits below the naval</li><li><strong>Mid-rise</strong>: Sits at the naval</li><li><strong>High-rise</strong>: Sits above the naval</li></ul>",
      "order": 2
    }
  ],
  
  "seo": {
    "title": "Jeans Buying Guide: Find the Perfect Fit for Your Body Type | Example Store",
    "description": "Learn how to choose the perfect jeans for your body shape with our comprehensive denim guide covering fits, rises, washes, and styling tips.",
    "keywords": ["jeans guide", "denim fits", "body type", "jean shopping"],
    "canonical_url": "https://www.example.com/blog/how-to-choose-perfect-jeans-body-type",
    "robots": "index, follow",
    "open_graph": {
      "title": "Find Your Perfect Jeans with Our Body Type Guide",
      "description": "Our comprehensive guide will help you find jeans that flatter your unique body shape.",
      "image": "https://assets.example.com/content/jeans-guide-social.jpg",
      "type": "article"
    },
    "twitter_card": {
      "card": "summary_large_image",
      "title": "Find Your Perfect Jeans with Our Body Type Guide",
      "description": "Our comprehensive guide will help you find jeans that flatter your unique body shape.",
      "image": "https://assets.example.com/content/jeans-guide-social.jpg"
    }
  },
  
  "engagement": {
    "view_count": 12845,
    "like_count": 348,
    "comment_count": 42,
    "share_count": 156,
    "avg_time_on_page": 245.5
  },
  
  "metadata": {
    "created_by": "sarah.johnson",
    "updated_by": "content.editor",
    "version": 3,
    "tenant_id": "default",
    "locale": "en_US",
    "translations": ["content-12345-fr", "content-12345-es"]
  }
}
```

## Indexing Considerations

1. **Text Analysis**: Use appropriate analyzers for title and body fields to improve text search
2. **Nested Fields**: Use nested type for structured arrays like sections and custom attributes
3. **Multi-fields**: Configure text fields with keyword sub-fields for sorting and aggregations
4. **Content Relationships**: Consider using a graph approach for related content recommendations
5. **Highlighting**: Ensure body field configuration supports text highlighting in search results