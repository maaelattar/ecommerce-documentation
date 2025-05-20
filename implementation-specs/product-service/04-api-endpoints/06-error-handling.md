# Error Handling API Documentation

## Overview
This document describes the error handling conventions for the Product Service APIs, including error response structure, standard error codes, examples, troubleshooting, and best practices for observability and support.

## Error Response Structure
All API errors return a consistent JSON structure:
```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "statusCode": 400,
  "details": { /* optional, additional error info */ },
  "correlationId": "uuid-string"
}
```
- `error`: A short error type or code (e.g., `ValidationError`, `Unauthorized`, `NotFound`)
- `message`: A human-readable description of the error
- `statusCode`: HTTP status code
- `details`: (optional) Additional error details (e.g., validation errors, field names)
- `correlationId`: (optional) Unique request ID for tracing and support

## Standard Error Codes & HTTP Status Mapping
| Error Type         | HTTP Status | Description                                 |
|--------------------|-------------|---------------------------------------------|
| ValidationError    | 400         | Input validation failed                     |
| InvalidRequest     | 400         | Malformed or missing parameters             |
| Unauthorized      | 401         | Authentication required/failed              |
| Forbidden         | 403         | Insufficient permissions                    |
| NotFound          | 404         | Resource not found                          |
| Conflict          | 409         | Duplicate or conflicting resource           |
| TooManyRequests   | 429         | Rate limit exceeded                         |
| InternalError     | 500         | Unexpected server error                     |
| ServiceUnavailable| 503         | Downstream service unavailable              |

## Field-Level Validation Errors
For validation errors, the `details` field provides per-field error information:
```json
{
  "error": "ValidationError",
  "message": "Validation failed",
  "statusCode": 400,
  "details": {
    "name": "Name is required",
    "price": "Price must be positive"
  },
  "correlationId": "uuid-string"
}
```

## Troubleshooting & Support
- Every error response includes a `correlationId` (request ID) for tracing
- Clients should log the `correlationId` and provide it when reporting issues
- Server logs include correlation IDs for all errors

## Error Logging & Monitoring
- All errors are logged server-side with full context (user, endpoint, payload, stack trace)
- Integration with monitoring/alerting tools (e.g., Sentry, Datadog, ELK)
- Alerts are triggered for high-severity errors (5xx, repeated 4xx, rate limits)
- Error rates and types are tracked for SLO/SLA reporting

## Best Practices
- Always return a consistent error structure
- Use appropriate HTTP status codes and error types
- Avoid exposing sensitive internal details (e.g., stack traces, DB errors)
- Provide actionable error messages for clients
- Document all custom error codes in the API spec
- Use correlation IDs for all requests and errors
- Monitor error rates and set up alerts for anomalies
- Regularly review and update error handling logic

## Example Error Responses
### Validation Error
```json
{
  "error": "ValidationError",
  "message": "Validation failed",
  "statusCode": 400,
  "details": {
    "name": "Name is required",
    "price": "Price must be positive"
  },
  "correlationId": "123e4567-e89b-12d3-a456-426614174000"
}
```
### Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Missing or invalid token",
  "statusCode": 401,
  "correlationId": "123e4567-e89b-12d3-a456-426614174000"
}
```
### Not Found
```json
{
  "error": "NotFound",
  "message": "Product not found",
  "statusCode": 404,
  "correlationId": "123e4567-e89b-12d3-a456-426614174000"
}
```
### Conflict
```json
{
  "error": "Conflict",
  "message": "Product name already exists",
  "statusCode": 409,
  "correlationId": "123e4567-e89b-12d3-a456-426614174000"
}
```
### Internal Server Error
```json
{
  "error": "InternalError",
  "message": "An unexpected error occurred",
  "statusCode": 500,
  "correlationId": "123e4567-e89b-12d3-a456-426614174000"
}
```

## References
- [RFC 7807: Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc7807)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Sentry Error Monitoring](https://sentry.io/welcome/)
- [Google Cloud Error Reporting](https://cloud.google.com/error-reporting) 