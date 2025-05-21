# 07 - External System Integrations

This document describes integrations between the User Service and external, third-party systems. These integrations enhance functionality, security, or user experience by leveraging specialized external services.

## 1. Third-Party Identity Providers (Social Logins)

*   **Purpose**: To allow users to register and log in using their existing accounts from popular identity providers (IdPs) like Google, Facebook, Apple, GitHub, etc. (OAuth 2.0 / OpenID Connect - OIDC).
*   **Integration Mechanism (Conceptual - using Passport.js with NestJS)**:
    *   The User Service would use libraries like `passport` and specific Passport strategies (e.g., `passport-google-oauth20`, `passport-facebook`, `passport-apple`).
    *   **Flow**:
        1.  Client (frontend) initiates social login, redirecting the user to the IdP's authorization server.
        2.  User authenticates with the IdP and grants permission.
        3.  IdP redirects back to a pre-configured callback URL on the User Service (e.g., `/auth/google/callback`) with an authorization code or tokens.
        4.  The User Service's callback handler exchanges the code for tokens (access, ID token) from the IdP.
        5.  User Service retrieves user profile information from the IdP using the ID token or by calling the IdP's user info endpoint.
        6.  User Service either:
            *   Finds an existing local user account linked to this social identity (e.g., by social ID or verified email).
            *   Creates a new local user account, linking it to the social identity and populating it with data from the IdP (e.g., email, name, profile picture).
        7.  User Service issues its own JWT access and refresh tokens to the client, just like with a regular password-based login.
*   **Configuration**: For each IdP, the User Service needs:
    *   `Client ID` and `Client Secret` (obtained from the IdP developer console).
    *   Registered `Redirect URI(s)`.
    *   Scopes to request (e.g., `openid`, `email`, `profile`).
*   **Security Considerations**:
    *   Securely store IdP client secrets.
    *   Validate the `state` parameter in OAuth flows to prevent CSRF.
    *   Verify ID token signatures and claims from the IdP.
    *   Handle account linking securely (e.g., if a user tries to link a social account whose email is already in use by another local account).
*   **User Experience**: Provide options for users to link/unlink social accounts from their existing local accounts.

## 2. Breached Password Check (Have I Been Pwned - HIBP)

*   **Purpose**: To prevent users from choosing passwords that are known to have been compromised in data breaches, enhancing account security.
*   **Integration Mechanism**:
    *   The `PasswordPolicyService` (within User Service) integrates with the HIBP Pwned Passwords API.
    *   During registration or password change, the chosen password (after basic policy checks) is hashed (SHA-1 for HIBP).
    *   The first 5 characters of the SHA-1 hash are sent to the HIBP API (k-anonymity model).
    *   HIBP API returns a list of hash suffixes that match the prefix, along with their breach counts.
    *   `PasswordPolicyService` checks if the user's password hash suffix is in the list.
    *   If found, the password is rejected.
*   **API Endpoint**: `https://api.pwnedpasswords.com/range/{hashPrefix}` (as detailed in `08-password-policy-service.md`).
*   **Security Considerations**:
    *   The k-anonymity model ensures the full password hash is not sent to HIBP.
    *   Consider fallback behavior if the HIBP API is unavailable (e.g., allow with warning, or temporarily deny if strict policy).

## 3. CAPTCHA Service (e.g., Google reCAPTCHA, hCAPTCHA)

*   **Purpose**: To protect public-facing endpoints like registration, login, and password reset requests from automated bot abuse.
*   **Integration Mechanism**:
    1.  Client (frontend) integrates the CAPTCHA widget (e.g., reCAPTCHA checkbox or invisible CAPTCHA).
    2.  User interacts with the CAPTCHA.
    3.  Upon successful CAPTCHA challenge, the client receives a CAPTCHA token.
    4.  Client submits this token along with the main request (e.g., registration form) to the User Service.
    5.  User Service (`AuthService` or a dedicated guard) takes the CAPTCHA token and makes a server-to-server API call to the CAPTCHA provider's verification endpoint, sending its secret key and the token.
    6.  CAPTCHA provider responds with success/failure and potentially a score.
    7.  If verification fails, the User Service rejects the original request (e.g., 400 Bad Request or 403 Forbidden).
*   **Configuration**: User Service needs its site key and secret key from the CAPTCHA provider.
*   **Security Considerations**: Securely store the CAPTCHA secret key.

## 4. External Communication Services (Email/SMS)

*   **Purpose**: To send emails (welcome, verification, password reset, security alerts) and potentially SMS messages (for MFA, notifications).
*   **Integration Mechanism - Preferred**: Via an internal **Notification Service**.
    *   The User Service publishes events like `PasswordResetRequestedEventV1` or `UserRegisteredEventV1`.
    *   A dedicated Notification Service consumes these events and handles the actual integration with third-party email providers (e.g., SendGrid, AWS SES, Mailgun) or SMS gateways (e.g., Twilio, Vonage).
    *   This decouples User Service from specific communication provider details and centralizes template management, retry logic, and provider switching.
*   **Integration Mechanism - Direct (Less Preferred)**:
    *   User Service could directly use SDKs or APIs of email/SMS providers.
    *   This creates tighter coupling and distributes provider-specific logic.
*   **Configuration**: If direct, User Service would need API keys and settings for the chosen providers.
*   **Security**: Securely store provider API keys. Be mindful of rate limits and PII in email/SMS content.

These external integrations enhance the User Service's capabilities but also introduce dependencies that need careful management regarding security, availability, and error handling.
