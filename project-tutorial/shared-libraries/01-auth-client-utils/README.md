# Auth Client Utils - @ecommerce/auth-client-utils

## Overview

This tutorial builds the authentication utilities shared library that provides standardized JWT validation, user context management, and RBAC utilities for all microservices in the platform.

## 🎯 Learning Objectives

- Build JWT validation modules and guards
- Create user context decorators and utilities
- Implement role-based access control (RBAC)
- Package and version a shared TypeScript library
- Integrate authentication across multiple services

---

## Step 1: Initialize the Package

### 1.1 Create Package Structure

```bash
# Create the package directory
mkdir -p shared-libraries/auth-client-utils
cd shared-libraries/auth-client-utils

# Initialize npm package
npm init -y

# Install dependencies
npm install @nestjs/common @nestjs/passport @nestjs/jwt
npm install passport passport-jwt jwks-rsa
npm install reflect-metadata class-validator class-transformer

# Install dev dependencies
npm install -D typescript @types/node @types/passport-jwt
npm install -D jest @types/jest ts-jest
npm install -D @nestjs/testing
```

### 1.2 Package Configuration

```json
{
  "name": "@ecommerce/auth-client-utils",
  "version": "1.0.0",
  "description": "Authentication utilities for ecommerce microservices",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "test:watch": "jest --watch",
    "prepublishOnly": "npm run build"
  },
  "keywords": ["nestjs", "authentication", "jwt", "rbac"],
  "author": "Ecommerce Platform Team",
  "license": "UNLICENSED",
  "peerDependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/passport": "^10.0.0",
    "passport": "^0.6.0",
    "passport-jwt": "^4.0.0"
  }
}
```