# Notification Service: Template Management

## 1. Introduction

*   **Purpose of Templates**: Notification templates are essential for ensuring that all outgoing communications (emails, SMS, push notifications) are consistent, maintainable, and can be dynamically personalized. They separate the content and presentation of notifications from the core application logic. This allows for easier updates to wording, branding, and structure without requiring code changes in the business logic that triggers the notification.

*   **`TemplateManager` Component**: As outlined in [03-core-service-components.md](./03-core-service-components.md), the `TemplateManager` service is the central component responsible for loading, parsing, rendering, and managing these templates.

This document details the structure, storage, management, and usage of notification templates within the Notification Service.

## 2. Template Structure and Syntax

### 2.1. Supported Formats

The Notification Service will support different template formats based on the communication channel:

*   **Email**:
    *   **HTML**: For rich content emails. Templates will be standard HTML.
    *   **Plain Text**: A plain text alternative for HTML emails is highly recommended for email clients that do not support HTML or for users who prefer text-only emails. This will be a separate template or an auto-generated version from HTML if feasible.
*   **SMS**:
    *   **Plain Text**: SMS messages are plain text only. Templates will produce a simple string.
*   **Push Notifications**:
    *   **Structured JSON**: Push notifications typically require a structured payload. Templates will generate a JSON object that conforms to the requirements of the push notification providers (e.g., FCM, APNs via AWS SNS). This usually includes fields like `title`, `body`, `icon`, `sound`, and `customData`.

### 2.2. Templating Engine

*   **Engine**: **Handlebars.js** will be used as the templating engine.
*   **Justification**:
    *   **Feature-Rich**: Handlebars provides support for variables, conditional logic (`#if`, `#unless`), loops (`#each`), partials (reusable template snippets), and helpers (custom functions), which are sufficient for most notification template needs.
    *   **Ease of Use**: Its syntax is relatively simple and widely understood.
    *   **Security**: Handlebars automatically escapes HTML content by default when using triple-stash `{{{variable}}}` for unescaped HTML is not used, which helps prevent XSS vulnerabilities in HTML emails if data is user-supplied. For other formats like plain text or JSON, escaping is less of a concern from an XSS perspective but care must still be taken.
    *   **Maturity & Community**: It's a mature library with good community support and is widely used in Node.js applications.
    *   **NestJS Integration**: Can be easily integrated into a NestJS service.

### 2.3. Placeholders/Variables

Dynamic data is inserted into templates using Handlebars' standard syntax:
*   `{{variableName}}` for escaped HTML output.
*   `{{{unescapedVariableName}}}` for raw HTML output (to be used with extreme caution, primarily for pre-sanitized HTML content).
*   For JSON or plain text templates, `{{variableName}}` is standard.

Example (Email subject): `Order {{orderId}} Confirmed!`
Example (Email body): `Hello {{userName}}, your order has been shipped.`

### 2.4. Basic Logic

Handlebars supports basic conditional logic and loops:
*   **Conditionals**:
    ```handlebars
    {{#if userHasDiscount}}
      <p>Your special discount has been applied!</p>
    {{else}}
      <p>Thank you for your order.</p>
    {{/if}}
    ```
*   **Loops**:
    ```handlebars
    <p>Items in your order:</p>
    <ul>
    {{#each items}}
      <li>{{this.productName}} - Quantity: {{this.quantity}}</li>
    {{/each}}
    </ul>
    ```

### 2.5. Layouts/Partials

Handlebars supports **partials**, which are reusable pieces of template code. This is highly recommended for:
*   **Email**: Common headers, footers, and branding elements.
*   **JSON Push Notifications**: Common structures or data fields.

Partials will be stored in a designated `partials` subdirectory within the template storage structure and registered with the Handlebars environment when the `TemplateManager` initializes.
Example: `{{> email-header}}`, `{{> email-footer}}`

## 3. Template Storage

### 3.1. Mechanism Options

*   **Database**:
    *   **Pros**: Templates can be updated dynamically without service redeployment, versioning can be built into the schema, and a potential admin UI could manage them.
    *   **Cons**: Adds complexity to the service (requires DB schema, management interface), potentially slower to access than filesystem, more complex backup/restore.
*   **Filesystem**:
    *   **Pros**: Simplicity (templates are just files), versioning is naturally handled by Git ("templates-as-code"), easy for developers to manage, fast loading.
    *   **Cons**: Template updates require a service deployment.
*   **Hybrid**: Load templates from the filesystem by default but allow overrides or new templates from a database. This adds complexity but offers flexibility.

### 3.2. Recommended Approach & Rationale

For the initial version of the Notification Service, **Filesystem storage is recommended**.

*   **Rationale**:
    *   **Simplicity**: It's the simplest approach to implement and manage initially.
    *   **Templates-as-Code**: Treating templates as code and versioning them in Git aligns well with infrastructure-as-code and DevOps practices. Changes go through the same review and deployment pipeline as code changes, ensuring traceability and easier rollbacks.
    *   **Performance**: Loading from the filesystem is generally fast. Templates can be loaded and compiled once at service startup.
    *   **Deployment for Updates**: While updates require deployment, this is often acceptable, especially in a CI/CD environment. It ensures that template changes are tested alongside any code that might use them.
    *   **Alignment with Deferred API Management**: As per `04-api-layer.md`, API-driven template management is deferred. Filesystem storage supports this decision well.

### 3.3. Filesystem Directory Structure

A structured directory layout will be used:
```
/templates
  ├── emails/
  │   ├── en-US/
  │   │   ├── order-confirmation.html.hbs
  │   │   ├── order-confirmation.txt.hbs  // Plain text alternative
  │   │   ├── password-reset.html.hbs
  │   │   └── password-reset.txt.hbs
  │   ├── es-ES/
  │   │   ├── order-confirmation.html.hbs
  │   │   └── order-confirmation.txt.hbs
  │   └── partials/ // Email specific partials
  │       ├── header.html.hbs
  │       └── footer.html.hbs
  ├── sms/
  │   ├── en-US/
  │   │   └── order-shipped.txt.hbs
  │   └── es-ES/
  │       └── order-shipped.txt.hbs
  ├── push/
  │   ├── en-US/
  │   │   └── new-message-alert.json.hbs
  │   └── es-ES/
  │       └── new-message-alert.json.hbs
  └── partials/ // Global partials usable across channel types if generic enough
      └── common-signature.txt.hbs
```
*   The `TemplateManager` will be configured with the base path to the `/templates` directory.
*   `.hbs` is the recommended extension for Handlebars templates.

## 4. Template Naming Convention

A clear and consistent naming convention is crucial:
*   **Structure**: `{purposeOrEvent}-{channelType}-{locale}.{formatExtension}.hbs`
    *   `purposeOrEvent`: Describes the notification's purpose (e.g., `welcome`, `order-confirmation`, `password-reset`, `product-back-in-stock`).
    *   `channelType`: `email`, `sms`, `push`.
    *   `locale`: Language and regional code (e.g., `en-US`, `es-ES`, `fr-FR`).
    *   `formatExtension`: `html` (for HTML emails), `txt` (for plain text emails/SMS), `json` (for push notifications).
*   **Examples**:
    *   `order-confirmation-email-en-US.html.hbs`
    *   `order-confirmation-email-en-US.txt.hbs`
    *   `password-reset-sms-es-ES.txt.hbs`
    *   `new-feature-push-en-US.json.hbs`

Partials could follow a simpler convention like `email-header.html.hbs` within their respective `partials` directory.

## 5. Personalization

Templates are personalized by passing a data object (context) to the Handlebars rendering engine. This data is constructed by the `NotificationDispatcher` based on the information received from the triggering event or API call.

Example: For an `OrderConfirmedEvent`, the data object might include:
```json
{
  "userName": "John Doe",
  "orderId": "ORD123456",
  "items": [
    {"name": "Product A", "quantity": 1, "price": "10.00"},
    {"name": "Product B", "quantity": 2, "price": "5.00"}
  ],
  "totalAmount": "20.00",
  "shippingAddress": "123 Main St, Anytown, USA",
  "orderLink": "https://example.com/orders/ORD123456"
}
```
The `TemplateManager` would then use this object to render the `order-confirmation-email-en-US.html.hbs` template.

## 6. Localization (i18n)

*   **Strategy**: Localization will be achieved by maintaining separate template files for each supported language and locale, as shown in the directory structure in section 3.3.
*   **Language Selection**:
    *   The desired `locale` for a notification should ideally be part of the incoming event payload (e.g., from the user's profile data associated with the event).
    *   If no `locale` is provided, the service will fall back to a default locale (e.g., `en-US`) defined in its configuration.
    *   The `TemplateManager` will attempt to load the template matching the specified `locale`. If a template for that specific `locale` is not found, it may fall back to a base language (e.g., `en`) or the default system locale. This fallback logic needs to be clearly defined.
*   **Content**: All translatable text, including subject lines (for emails) and body content, will reside within these localized template files.

## 7. Versioning

*   **Mechanism**: Since templates are stored in the filesystem, versioning is handled directly by **Git**. Each change to a template is a commit in the Git repository.
*   **Usage**: The Notification Service, when deployed, will use the version of the templates that are part of that specific deployment package/Docker image. This ensures that the service code and its corresponding templates are consistent.
*   **Rollbacks**: If a problematic template change is deployed, rolling back to a previous version of the service (and thus its templates) is the standard procedure.

## 8. Management and Update Process

*   **Responsibility**:
    *   **Initial Creation & Major Changes**: Primarily developers, as part of feature development or service setup.
    *   **Minor Wording/Content Updates**: Could potentially be managed by a marketing or content team if a suitable workflow is established (e.g., they provide updated content, developers commit and deploy). However, with filesystem storage, direct updates always involve a developer committing changes.
*   **Update Process**:
    1.  Modify the template file(s) in the local development environment.
    2.  Test the changes thoroughly (see below).
    3.  Commit the changes to Git.
    4.  Push the changes, triggering the CI/CD pipeline.
    5.  The updated service (with the new templates) is deployed to staging and then production.
    *   As noted in `04-api-layer.md`, there is **no API for live template management** in the initial version.
*   **Testing Templates**:
    *   **Local Testing**: Developers should be able to easily render and preview templates locally with sample data. This might involve a simple script or test utility.
    *   **Unit Tests**: For the `TemplateManager`, ensure it can load and attempt to render templates correctly (mocking the actual rendering if too complex for a unit test).
    *   **Integration/Component Tests**: Test the notification flow with sample events and verify that the correct template is chosen and rendered with expected (or at least structurally correct) output. Visual inspection of rendered emails might be part of staging tests.
    *   **Preview Tools**: Consider using tools like MailHog or Ethereal for testing email rendering during development.

## 9. Security Considerations

*   **HTML Escaping**: Handlebars automatically escapes variables in `{{variable}}` blocks, which mitigates XSS risks in HTML email templates. Avoid using triple-stash `{{{variable}}}` for unescaped HTML unless the content is from a trusted source or has been pre-sanitized.
*   **Data Sanitization**: While Handlebars provides some protection, it's good practice to sanitize any user-provided data that will be rendered in templates, especially if it's used in contexts where escaping might not be default (e.g., within JavaScript in an HTML template, or complex JSON structures).
*   **JSON Templates for Push**: Ensure that JSON generated for push notifications is well-formed and does not allow for injection of malicious structures if any part of it is derived from user input.
*   **Resource Limits**: If templates involve complex logic (loops over large datasets, though generally discouraged in templates), be mindful of potential performance implications during rendering. The `TemplateManager` should have timeouts or resource limits if rendering becomes too intensive.
*   **Access Control to Templates**: Since templates are part of the codebase (filesystem storage), access control is managed via Git repository permissions.

This template management strategy prioritizes simplicity, version control, and consistency with a "templates-as-code" approach for the initial version of the Notification Service.
