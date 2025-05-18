# Identity Provider (IdP) Selection Decision

Date: 2025-05-12  
Status: Accepted

## Context

Based on our previously accepted ADR-005 (JWT-based Authentication and Authorization), we established that our authentication strategy will use JSON Web Tokens (JWTs) within an OAuth 2.0/OpenID Connect (OIDC) compliant framework. This document finalizes the specific Identity Provider (IdP) selection to implement this authentication and authorization strategy, aligning with our current project goal of leveraging AWS managed services.

## Decision

After re-evaluating options with a focus on AWS managed services, we have selected **Amazon Cognito** as our Identity Provider solution.

## Rationale

Amazon Cognito is selected for the following reasons, prioritizing ease of use, deep AWS integration, and reduced operational overhead for the current project phase:

1.  **Fully Managed Service:** AWS manages the infrastructure, scalability, availability, and maintenance of Cognito, significantly reducing the operational burden on our team compared to self-hosting an IdP like Keycloak.
2.  **Seamless AWS Ecosystem Integration:**
    *   Natively integrates with Amazon API Gateway (for authorizing API requests), Application Load Balancers (ALB), AWS AppSync, and other AWS services.
    *   Works well with IAM for defining permissions for authenticated users.
3.  **Standards-Compliant OIDC/OAuth 2.0:**
    *   Provides robust support for OpenID Connect and OAuth 2.0 identity and access tokens.
    *   Supports standard flows (Authorization Code, Implicit, Client Credentials).
4.  **Security Features:**
    *   Offers features like multi-factor authentication (MFA), adaptive authentication (risk-based), compromised credential checking, and encryption of data at rest and in transit.
    *   Helps meet compliance requirements (e.g., HIPAA eligibility, PCI DSS, SOC).
5.  **User Management & Directory Services:**
    *   Provides User Pools for creating and managing user directories.
    *   Supports user sign-up, sign-in, password recovery, and profile management.
6.  **Federation Capabilities:**
    *   Supports identity federation with social identity providers (like Google, Facebook, Apple) and SAML 2.0 or OIDC identity providers (which could include Keycloak if used for a specific, separate purpose in the future).
7.  **Customizable UI:** Allows customization of the hosted UI for login, sign-up, and other user flows to match application branding.
8.  **Scalability & Cost-Effectiveness:** Scales automatically to millions of users. The pricing model is typically based on Monthly Active Users (MAUs), which can be cost-effective, especially considering the avoided operational costs of a self-managed solution.

While Keycloak (previously considered) offers excellent features and control as an open-source, self-hosted solution, the strategic decision for this project phase is to leverage AWS managed services like Cognito to accelerate development and simplify operations.

## Implementation Details (Amazon Cognito)

### 1. Cognito User Pools

*   **Primary User Directory:** A User Pool will be configured to store and manage customer identities.
*   **Attributes:** Standard attributes (email, phone number, preferred_username) and custom attributes (e.g., `user_id`, `customer_tier`) will be defined as needed.
*   **Password Policies:** Strong password policies will be enforced.
*   **MFA:** Multi-Factor Authentication (e.g., TOTP, SMS) will be enabled and encouraged for users.
*   **Sign-up/Sign-in:** Configure self-service sign-up and sign-in flows. Consider email or phone number verification.

### 2. Cognito Identity Pools (Federated Identities) - If Applicable

*   If direct access to AWS resources (e.g., S3, DynamoDB) from the client-side is required (less common for backend-centric e-commerce architectures), Identity Pools can be used to grant temporary AWS credentials to users.
*   Typically, authentication will be handled by User Pools, and backend services will interact with other AWS resources using IAM roles.

### 3. App Clients

*   Separate App Clients will be configured for different applications (e.g., web frontend, mobile app, backend services needing client credentials).
*   Configure OAuth 2.0 flows (Authorization Code with PKCE for public clients, Client Credentials for confidential clients).
*   Define OAuth scopes (e.g., `openid`, `profile`, `email`, custom scopes like `order:read`, `order:write`).

### 4. Domain and UI Customization

*   **Cognito Domain:** A custom domain or a Cognito-provided domain prefix will be configured for the hosted UI.
*   **UI Customization:** The hosted UI for login, sign-up, MFA setup, and password recovery will be customized to match the application's branding.
*   **Lambda Triggers:** Utilize Lambda triggers for custom workflows during user lifecycle events (e.g., pre sign-up, post-confirmation, pre token generation).

### 5. Token Management

*   **ID Tokens:** Used by client applications to get user profile information.
*   **Access Tokens:** Used by client applications to authorize API calls to backend services (validated by API Gateway or backend services).
*   **Refresh Tokens:** Securely stored by client applications to obtain new ID and access tokens without requiring the user to re-authenticate.
*   Token lifetimes will be configured according to security best practices (short-lived access tokens, longer-lived refresh tokens).

### 6. Security Configurations

*   **Advanced Security Features:** Enable features like adaptive authentication and compromised credential protection.
*   **Token Revocation:** Implement mechanisms for token revocation if necessary.
*   **Audit Logging:** Leverage CloudTrail for auditing Cognito API calls.

### 7. Integration with API Gateway

*   Amazon API Gateway will be configured with a Cognito User Pool Authorizer to protect API endpoints.

## Alternatives Considered

*   **Keycloak (Self-Hosted on EKS):** A powerful open-source IdP offering extensive features, customization, and full control. Previously selected but now superseded by Cognito to align with the strategy of using AWS managed services for this project iteration due to lower operational overhead.
*   **Auth0, Okta, FusionAuth:** Commercial IdP solutions offering rich feature sets and enterprise support. Considered more expensive and potentially more complex than needed for the current project phase focused on AWS native services.

## Dependencies

*   **Infrastructure Team:** Configuration of Cognito resources via IaC (CDK/CloudFormation).
*   **Development Teams:** Integrating applications with Cognito for authentication and authorization, handling tokens.
*   **Security Team:** Reviewing Cognito configurations and security best practices.

## Action Items

1.  Configure Amazon Cognito User Pool(s) and App Client(s) for the development environment.
2.  Develop CI/CD pipelines for Cognito configuration updates via IaC.
3.  Integrate frontend and backend services with Cognito for authentication.
4.  Document best practices for token handling and secure local storage for development teams.
5.  Establish monitoring for Cognito user activity and potential security events (e.g., via CloudWatch Logs and Metrics).

## References

*   [ADR-005: JWT-based Authentication and Authorization](./../adr/ADR-005-jwt-based-authentication-and-authorization.md)
*   [Amazon Cognito Developer Guide](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)
