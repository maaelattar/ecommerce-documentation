# Authentication & Authorization API Specification

## Overview
This document describes the authentication and authorization mechanisms for the Product Service APIs, including login, token management, RBAC enforcement, and security best practices.

## Authentication
- **Mechanism:** JWT (JSON Web Token) or OAuth2
- **Token Types:** Access token (short-lived), Refresh token (long-lived)
- **Token Transport:** HTTP Authorization header (Bearer)

### 1. `POST /auth/login`
- **Description:** Authenticate user and issue JWT tokens
- **Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```
- **Response:**
```json
{
  "accessToken": "jwt-string",
  "refreshToken": "jwt-string",
  "expiresIn": 3600
}
```
- **Error Responses:** 401 Unauthorized (invalid credentials)

### 2. `POST /auth/refresh`
- **Description:** Refresh access token using a valid refresh token
- **Request Body:**
```json
{
  "refreshToken": "jwt-string"
}
```
- **Response:**
```json
{
  "accessToken": "jwt-string",
  "expiresIn": 3600
}
```
- **Error Responses:** 401 Unauthorized (invalid/expired refresh token)

### 3. `POST /auth/logout`
- **Description:** Invalidate refresh token (optional, for stateful implementations)
- **Request Body:**
```json
{
  "refreshToken": "jwt-string"
}
```
- **Response:** 204 No Content

## JWT Structure
- **Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```
- **Payload Example:**
```json
{
  "sub": "user-id",
  "username": "string",
  "roles": ["admin", "manager"],
  "exp": 1712345678
}
```
- **Signature:** HMAC or RSA

## Authorization (RBAC)
- **Roles:** admin, manager, editor, warehouse, marketing, user
- **Enforcement:**
  - Each endpoint specifies required roles
  - Middleware/guards check JWT claims
- **Example:**
  - `POST /products` requires `admin|manager|editor`
  - `PATCH /inventory/{variantId}` requires `admin|manager|warehouse`

## Protected Endpoints
- All write operations require a valid JWT and appropriate role
- Read operations may be public or require authentication based on resource

## Example Auth Flow
1. User logs in via `/auth/login` and receives tokens
2. User includes `Authorization: Bearer <accessToken>` in API requests
3. On token expiry, user calls `/auth/refresh` to obtain a new access token
4. User logs out via `/auth/logout` (optional)

## Security Best Practices
- Use HTTPS for all endpoints
- Store secrets securely (env vars, vault)
- Set short expiry for access tokens, longer for refresh tokens
- Rotate signing keys regularly
- Log and monitor authentication events
- Implement rate limiting on auth endpoints
- Invalidate tokens on password change or suspicious activity

## Error Handling
- Standard error response:
```json
{
  "error": "Unauthorized",
  "message": "Invalid credentials",
  "statusCode": 401
}
```

## References
- [JWT RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [OWASP API Security](https://owasp.org/www-project-api-security/) 