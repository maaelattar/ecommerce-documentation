# AWS Cognito Integration

## 🎯 Objective

Integrate Amazon Cognito per TDAC specs.

## 🔧 Setup

```bash
pnpm add @aws-sdk/client-cognito-identity-provider
```

### Cognito Service
```typescript
// src/auth/cognito.service.ts
import { Injectable } from '@nestjs/common';
import { CognitoIdentityProviderClient, AdminCreateUserCommand } from '@aws-sdk/client-cognito-identity-provider';

@Injectable()
export class CognitoService {
  private cognitoClient: CognitoIdentityProviderClient;
  
  constructor() {
    this.cognitoClient = new CognitoIdentityProviderClient({
      region: process.env.AWS_REGION,
      endpoint: process.env.AWS_ENDPOINT_URL,
    });
  }

  async createUser(email: string, password: string) {
    const command = new AdminCreateUserCommand({
      UserPoolId: process.env.COGNITO_USER_POOL_ID,
      Username: email,
      TemporaryPassword: password,
      UserAttributes: [{ Name: 'email', Value: email }],
    });
    
    return this.cognitoClient.send(command);
  }
}
```## 📚 Benefits

- **Fully managed** - No infrastructure maintenance
- **AWS integration** - API Gateway, ALB seamless integration
- **Security** - MFA, adaptive authentication, compromised credential detection

## 📋 TDAC Compliance

✅ Following **[TDAC-02 Identity Provider Selection](../../architecture/technology-decisions-aws-centeric%20(tdac)/02-identity-provider-selection.md)** - Amazon Cognito as primary IdP

## 🔧 Integration Pattern

This replaces local JWT implementation with AWS-managed identity provider for:
- Centralized user management
- Standard OIDC/OAuth 2.0 flows
- Reduced operational overhead

## ✅ Next Step

Continue to **[10-complete-api-implementation.md](./10-complete-api-implementation.md)**