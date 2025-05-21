# 04: Input Validation and Output Encoding in Payment Service

Robust input validation and proper output encoding are fundamental security practices to protect the Payment Service from a wide range of attacks, particularly injection vulnerabilities and Cross-Site Scripting (XSS).

## 1. Input Validation

All data received by the Payment Service, regardless of its source (e.g., API requests from clients/API Gateway, messages from internal services via Kafka, webhook payloads from payment gateways), MUST be rigorously validated before being processed or stored.

### 1.1. Principles of Input Validation

*   **Validate on Arrival:** Perform validation as soon as the data enters the service boundary.
*   **Centralized Validation Logic:** Use a centralized validation library or framework (e.g., class-validator in NestJS, Joi, Zod) to ensure consistency and maintainability.
*   **Deny by Default (Whitelisting):** Prefer whitelisting known good patterns and data types over blacklisting known bad inputs. If data doesn't match the expected format, reject it.
*   **Validate for Type, Format, Length, Range, and Business Rules:**
    *   **Type:** Ensure data is of the expected type (e.g., string, number, boolean, date).
    *   **Format:** Validate against specific formats (e.g., UUID for IDs, ISO 8601 for dates, specific currency codes, email format).
    *   **Length:** Check for minimum and maximum lengths for strings and array sizes.
    *   **Range:** Ensure numerical values fall within acceptable ranges.
    *   **Business Rules:** Validate against business-specific logic (e.g., a refund amount cannot exceed the original payment amount).

### 1.2. Specific Validation Areas

*   **API Endpoints:**
    *   Validate all request parameters (path, query, body, headers).
    *   Use Data Transfer Objects (DTOs) with validation decorators (common in NestJS with `class-validator` and `class-transformer`).
*   **Event Consumers (e.g., Kafka messages):**
    *   Validate the structure and content of event payloads against a defined schema (e.g., JSON Schema).
    *   Be resilient to malformed or unexpected event data.
*   **Webhook Payloads:**
    *   Validate the structure and data types of incoming webhook data from payment gateways, in addition to signature verification.
*   **Configuration Data:**
    *   Validate configuration values at startup to prevent issues due to misconfiguration.

### 1.3. Preventing Injection Attacks

*   **SQL Injection (SQLi):**
    *   Primarily use an Object-Relational Mapper (ORM) like TypeORM, which inherently protects against most SQLi vulnerabilities by using parameterized queries or properly escaping input.
    *   Avoid constructing SQL queries by concatenating strings with unvalidated user input. If raw SQL is absolutely necessary, ensure all inputs are strictly parameterized or escaped.
*   **NoSQL Injection:** If interacting with NoSQL databases, be aware of their specific injection risks and use appropriate SDKs and techniques that prevent them.
*   **Command Injection:** The Payment Service should generally not execute OS commands. If it must, ensure inputs used in commands are rigorously validated and sanitized, or avoid user input in commands altogether.
*   **LDAP Injection, XML Injection (XXE):** If interacting with such systems, apply specific validation and parsing techniques to prevent these vulnerabilities (though less common for a typical payment service).

## 2. Output Encoding

Output encoding ensures that data sent from the Payment Service (e.g., in API responses, logs) is treated as data and not as executable code by the recipient or rendering system. This is crucial for preventing XSS attacks.

### 2.1. Principles of Output Encoding

*   **Encode for the Context:** The type of encoding depends on where the data will be placed (e.g., HTML body, HTML attribute, JavaScript, CSS, URL component).
*   **Use Standard Libraries:** Employ well-vetted libraries for encoding (e.g., those built into templating engines or dedicated security libraries).

### 2.2. Specific Encoding Areas

*   **API Responses (JSON):**
    *   When returning data in JSON responses, ensure that strings are correctly JSON encoded. Modern HTTP frameworks and JSON serialization libraries usually handle this automatically.
    *   Be cautious if constructing JSON strings manually.
*   **Logging:**
    *   While logs are typically not rendered in a browser, sanitize or encode data written to logs to prevent log injection or manipulation that could facilitate other attacks or obscure malicious activity. For example, escape newlines (`\n`) or other control characters if they could break log parsing or be used to forge log entries.
    *   Avoid logging highly sensitive raw data like full payment details (even tokens if contextually sensitive in logs).
*   **Administrative UIs (If Applicable):** If the Payment Service has an associated administrative UI (even if separate), any data from the service rendered in the UI must be contextually encoded (e.g., HTML entity encoding for data displayed in HTML).

### 2.3. Preventing XSS (Cross-Site Scripting)

*   **Primary Defense:** Contextual output encoding.
*   **Content Security Policy (CSP):** If the Payment Service serves any HTML content directly or influences content on a front-end, implement a strong CSP to restrict the sources of executable scripts and other resources, mitigating the impact of any XSS that might occur.
*   **HTTPOnly and Secure Flags for Cookies:** If the service sets cookies (less common for a backend API), use `HTTPOnly` to prevent JavaScript access and `Secure` to ensure transmission over HTTPS.

## 3. Secure Parsing

*   When parsing structured data formats like XML or JSON from external sources, use secure parsers that are configured to prevent vulnerabilities like XXE (XML External Entity) attacks for XML or prototype pollution for JSON (though the latter is more of a JavaScript concern, be mindful if using Node.js extensively with complex object manipulation from untrusted sources).

By consistently applying input validation and output encoding, the Payment Service can significantly reduce its attack surface and protect against common and often severe vulnerabilities.