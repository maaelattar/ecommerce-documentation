# Security Standards

## 1. Overview

This document defines security standards and best practices for the e-commerce platform. These standards ensure a consistent approach to securing our services, protecting customer data, and maintaining regulatory compliance across the entire platform.

## 2. Core Principles

### 2.1. Defense in Depth

- Implement multiple layers of security controls throughout the architecture
- Assume any single security control may fail
- Combine preventive, detective, and corrective controls
- Regularly audit and test all security layers

### 2.2. Least Privilege

- Grant minimum access required for functionality
- Regularly review and audit all access privileges
- Implement strong separation of duties
- Use time-limited credentials when possible

### 2.3. Secure by Default

- All systems must be secure in their default configuration
- Disable unnecessary features, ports, and services
- Apply security hardening to all components
- Enable security-enhancing features by default

### 2.4. Privacy by Design

- Treat privacy as a core requirement, not an add-on
- Collect only necessary personal data
- Implement data minimization and purpose limitation
- Provide users control over their personal data

## 3. Authentication Standards

### 3.1. User Authentication

- Implement multi-factor authentication (MFA) for all user accounts
- Enforce strong password policies:
  - Minimum 12 characters
  - Combination of uppercase, lowercase, numbers, and special characters
  - Check against common/breached password databases
  - Prevent password reuse (last 24 passwords)
- Implement account lockout after 5 failed attempts
- Use secure credential storage with modern hashing algorithms (Argon2id)

### 3.2. Service-to-Service Authentication

- Implement mutual TLS (mTLS) for service-to-service authentication
- Use short-lived service account credentials
- Implement credential rotation with zero downtime
- Audit all service account usage

### 3.3. API Authentication

- Use OAuth 2.0 with OpenID Connect for user-facing APIs
- Implement API keys with strict rate limiting for external partners
- Use JWT with appropriate algorithm (RS256) and validation
- Include standard security claims in all tokens

### 3.4. Token Management

- Short expiration times for access tokens (15-60 minutes)
- Implement secure token refresh mechanisms
- Include essential claims: `iss`, `sub`, `exp`, `iat`, `jti`, `aud`
- Validate all token claims server-side

## 4. Authorization Standards

### 4.1. Role-Based Access Control (RBAC)

- Define standardized roles across the platform
- Implement principle of least privilege in role definitions
- Document and regularly review all roles and permissions
- Implement segregation of duties for sensitive operations

### 4.2. Attribute-Based Access Control (ABAC)

- Supplement RBAC with attribute-based policies for fine-grained control
- Include contextual attributes in access decisions:
  - Time of day
  - User location
  - Device characteristics
  - Resource sensitivity
- Centralize policy definitions and enforcement

### 4.3. API Authorization

- Validate authorization for every API request
- Implement proper scope validation for OAuth tokens
- Return appropriate status codes (401 vs 403)
- Log all authorization failures

### 4.4. Implementation Example

```typescript
// Example of integrating RBAC and ABAC
@Injectable()
export class AuthorizationService {
  constructor(
    private readonly roleRepository: RoleRepository,
    private readonly policyEvaluator: PolicyEvaluator,
    private readonly logger: Logger
  ) {}

  async isAuthorized(
    user: User,
    resource: string,
    action: string,
    context: RequestContext
  ): Promise<boolean> {
    // Get user roles
    const roles = await this.roleRepository.getRolesForUser(user.id);

    // Check role-based permissions first (faster check)
    const hasRolePermission = roles.some((role) =>
      role.permissions.some(
        (p) => p.resource === resource && p.actions.includes(action)
      )
    );

    if (hasRolePermission) {
      // Log successful access via role
      this.logger.debug(
        `User ${user.id} authorized for ${action} on ${resource} via role`
      );
      return true;
    }

    // If no role-based permission, check attribute-based policies
    const policyResult = await this.policyEvaluator.evaluate({
      subject: user,
      resource,
      action,
      context,
    });

    if (policyResult.allowed) {
      // Log successful access via policy
      this.logger.debug(
        `User ${user.id} authorized for ${action} on ${resource} via policy`
      );
    } else {
      // Log denied access
      this.logger.warn(
        `User ${user.id} denied ${action} on ${resource}: ${policyResult.reason}`
      );
    }

    return policyResult.allowed;
  }
}
```

## 5. Data Protection

### 5.1. Data Classification

- Define data classification levels:
  - Public
  - Internal
  - Confidential
  - Restricted
- Document classification for all data entities
- Apply appropriate controls based on classification
- Regularly review and update classifications

### 5.2. Encryption at Rest

- Encrypt all sensitive data at rest
- Use industry-standard encryption algorithms (AES-256)
- Implement proper key management with rotation
- Use envelope encryption for large datasets
- Store encryption keys separately from encrypted data

### 5.3. Encryption in Transit

- Use TLS 1.3 for all public-facing endpoints
- Use TLS 1.2+ for all internal communications
- Implement certificate rotation procedures
- Configure secure cipher suites
- Disable compression to prevent CRIME attacks

### 5.4. Key Management

- Use a centralized key management service
- Implement automated key rotation
- Secure key backups and disaster recovery
- Monitor key usage and access
- Support key revocation procedures

### 5.5. Sensitive Data Handling

- Implement tokenization for payment card data
- Hash or encrypt personally identifiable information (PII)
- Implement data masking in logs and non-production environments
- Define secure data deletion procedures
- Log all access to sensitive data

## 6. Network Security

### 6.1. Network Segmentation

- Implement clear network boundaries between environments
- Use security groups to restrict network traffic
- Follow the principle of least connectivity
- Document all network paths and justify each connection

### 6.2. API Gateway Security

- Implement API gateway as central entry point
- Configure rate limiting and throttling
- Validate all input at the edge
- Block common attack patterns with WAF integration

### 6.3. DDoS Protection

- Implement multi-layer DDoS protection
- Configure automatic scaling for traffic spikes
- Use CDN for static content delivery
- Monitor for anomalous traffic patterns

### 6.4. Service Mesh Security

- Implement mTLS between all services
- Centralize traffic policy management
- Monitor all service-to-service communication
- Enforce authorization at the mesh level

## 7. Application Security

### 7.1. Secure Coding Standards

- Follow OWASP secure coding guidelines
- Implement static code analysis in CI/CD pipeline
- Conduct regular security training for developers
- Define language-specific secure coding standards

### 7.2. Dependency Management

- Regularly scan dependencies for vulnerabilities
- Define process for dependency updates
- Maintain inventory of all third-party components
- Implement policy for acceptable licenses

### 7.3. Input Validation

- Validate all input at service boundaries
- Implement schema validation for structured data
- Sanitize data before storage or display
- Use parameterized queries for all database operations

### 7.4. Output Encoding

- Encode all output appropriate to context
- Implement Content Security Policy (CSP)
- Use secure response headers
- Prevent content type sniffing

### 7.5. OWASP Top 10 Mitigations

| Vulnerability                   | Required Mitigations                                           |
| ------------------------------- | -------------------------------------------------------------- |
| Broken Access Control           | Centralized access control, least privilege, access auditing   |
| Cryptographic Failures          | Strong algorithms, proper key management, TLS enforcement      |
| Injection                       | Parameterized queries, ORM use, input validation               |
| Insecure Design                 | Threat modeling, secure defaults, principle of least privilege |
| Security Misconfiguration       | Hardened configurations, removal of defaults, regular scanning |
| Vulnerable Components           | Dependency scanning, regular updates, component inventory      |
| Identification/Authentication   | MFA, secure credential storage, account lockout                |
| Software and Data Integrity     | CI/CD security, SBOMs, integrity verification                  |
| Security Logging and Monitoring | Centralized logging, alerting, audit trails                    |
| Server-Side Request Forgery     | URL validation, network segmentation, firewall rules           |

## 8. Security Testing Standards

### 8.1. Required Testing Types

- Static Application Security Testing (SAST)
- Dynamic Application Security Testing (DAST)
- Software Composition Analysis (SCA)
- Infrastructure as Code (IaC) scanning
- Penetration testing
- Chaos engineering for security

### 8.2. Testing Frequency

| Test Type                  | Frequency                   | Trigger                           |
| -------------------------- | --------------------------- | --------------------------------- |
| SAST                       | Every commit                | Pull request                      |
| SCA                        | Every commit                | Pull request                      |
| IaC Scanning               | Every infrastructure change | Pull request                      |
| DAST                       | Weekly                      | Scheduled                         |
| Container scanning         | Every build                 | CI pipeline                       |
| Penetration testing        | Bi-annually                 | Major release, significant change |
| Security chaos engineering | Monthly                     | Scheduled                         |

### 8.3. Security Testing Implementation

```yaml
# Example GitLab CI/CD configuration for security testing
stages:
  - build
  - test
  - security
  - deploy

sast:
  stage: security
  script:
    - sast-scanner --output-format=json --output=gl-sast-report.json
  artifacts:
    paths:
      - gl-sast-report.json

dependency_scanning:
  stage: security
  script:
    - dependency-scan --output-format=json --output=gl-dependency-report.json
  artifacts:
    paths:
      - gl-dependency-report.json

container_scanning:
  stage: security
  script:
    - container-scan $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA --output=gl-container-report.json
  artifacts:
    paths:
      - gl-container-report.json

dast:
  stage: security
  variables:
    TARGET_URL: https://staging-$CI_PROJECT_PATH_SLUG.example.com
  script:
    - dast-scanner --target=$TARGET_URL --output=gl-dast-report.json
  artifacts:
    paths:
      - gl-dast-report.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

## 9. Vulnerability Management

### 9.1. Vulnerability Scanning

- Implement automated vulnerability scanning
- Scan all environments at defined intervals
- Include all infrastructure components and applications
- Generate risk-prioritized findings

### 9.2. Vulnerability Response

- Define SLAs for vulnerability remediation:
  - Critical: 24 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days
- Implement vulnerability tracking system
- Document exceptions with compensating controls
- Regular reporting on vulnerability status

### 9.3. Security Patching

- Define patching cadence for each environment
- Implement automated patch testing
- Document patch deployment procedures
- Maintain emergency patching procedures

## 10. Identity and Access Management

### 10.1. Identity Lifecycle Management

- Implement automated provisioning and deprovisioning
- Regular access reviews (quarterly at minimum)
- Just-in-time access for privileged operations
- Clear procedures for role changes and terminations

### 10.2. Secrets Management

- Use a central secrets management solution
- Generate strong secrets automatically
- Rotate secrets regularly
- Audit secret access and usage

### 10.3. Privileged Access Management

- Implement just-in-time privileged access
- Record all privileged sessions
- Require approval for critical access
- Use break-glass procedures for emergency access

### 10.4. Implementation Example

```typescript
// Example of just-in-time privileged access
@Controller("admin/temporary-access")
export class TemporaryAccessController {
  constructor(
    private readonly accessService: TemporaryAccessService,
    private readonly notificationService: NotificationService,
    private readonly auditService: AuditService
  ) {}

  @Post("request")
  @Roles("Admin")
  async requestTemporaryAccess(
    @Body() request: AccessRequestDto,
    @User() requester: UserInfo
  ): Promise<AccessRequestResponse> {
    // Validate the request
    if (request.duration > 4) {
      throw new BadRequestException("Maximum duration is 4 hours");
    }

    // Create the access request
    const accessRequest = await this.accessService.createRequest({
      userId: requester.id,
      role: request.role,
      resource: request.resource,
      justification: request.justification,
      duration: request.duration,
      status: "PENDING",
    });

    // Notify approvers
    await this.notificationService.notifyApprovers(accessRequest);

    // Audit the request
    await this.auditService.logEvent({
      action: "TEMPORARY_ACCESS_REQUESTED",
      actor: requester.id,
      target: request.resource,
      details: {
        requestId: accessRequest.id,
        role: request.role,
        justification: request.justification,
        duration: request.duration,
      },
    });

    return {
      requestId: accessRequest.id,
      status: "PENDING",
      expiresAt: null,
    };
  }

  @Post("approve/:requestId")
  @Roles("SecurityAdmin")
  async approveAccess(
    @Param("requestId") requestId: string,
    @User() approver: UserInfo
  ): Promise<AccessRequestResponse> {
    // Get the request
    const request = await this.accessService.getRequest(requestId);

    // Check if already processed
    if (request.status !== "PENDING") {
      throw new BadRequestException(
        `Request already ${request.status.toLowerCase()}`
      );
    }

    // Grant the access
    const expiresAt = new Date();
    expiresAt.setHours(expiresAt.getHours() + request.duration);

    const updatedRequest = await this.accessService.updateRequest(requestId, {
      status: "APPROVED",
      approvedBy: approver.id,
      approvedAt: new Date(),
      expiresAt,
    });

    // Grant the role
    await this.accessService.grantTemporaryRole(
      request.userId,
      request.role,
      request.resource,
      expiresAt
    );

    // Notify the requester
    await this.notificationService.notifyRequestApproved(updatedRequest);

    // Audit the approval
    await this.auditService.logEvent({
      action: "TEMPORARY_ACCESS_APPROVED",
      actor: approver.id,
      target: request.resource,
      details: {
        requestId,
        userId: request.userId,
        role: request.role,
        expiresAt,
      },
    });

    return {
      requestId,
      status: "APPROVED",
      expiresAt,
    };
  }
}
```

## 11. Monitoring and Incident Response

### 11.1. Security Monitoring

- Implement centralized security logging
- Configure alerting for security events
- Monitor for anomalous behaviors
- Implement user activity monitoring

### 11.2. Incident Response Plan

- Define security incident classification
- Document incident response procedures
- Establish response team and roles
- Conduct regular incident response exercises

### 11.3. Security Metrics

- Track mean time to detect (MTTD)
- Track mean time to respond (MTTR)
- Monitor and report on security KPIs
- Regular security posture assessments

### 11.4. Logging Requirements

All services must log the following security events:

- Authentication attempts (success and failure)
- Authorization decisions
- Data access and modification
- Configuration changes
- Privileged operations
- Security events from dependent services

Example log format:

```json
{
  "timestamp": "2023-08-12T13:45:30.123Z",
  "level": "WARN",
  "service": "user-service",
  "traceId": "abc123",
  "securityEvent": true,
  "eventType": "AUTHENTICATION_FAILURE",
  "userId": "user123",
  "sourceIp": "203.0.113.1",
  "userAgent": "Mozilla/5.0...",
  "details": {
    "reason": "INVALID_CREDENTIALS",
    "attemptCount": 3
  }
}
```

## 12. Compliance Requirements

### 12.1. Regulatory Compliance

- PCI DSS for payment card processing
- GDPR for EU personal data
- CCPA for California residents
- Regional regulations as applicable

### 12.2. PCI DSS Requirements

- Store no card data if possible, use third-party processors
- If necessary, implement tokenization for card data
- Maintain strict network segmentation for cardholder data
- Implement specific logging for PCI-related systems

### 12.3. GDPR Requirements

- Enable data subject rights (access, deletion, portability)
- Maintain data processing records
- Implement right to be forgotten functionality
- Record consent for all data processing

### 12.4. Compliance Monitoring

- Regular compliance control testing
- Automated evidence collection
- Compliance dashboard with control status
- Regular internal audits

## 13. Implementation Examples

### 13.1. Security Headers Configuration

```typescript
// Example of security headers middleware
@Injectable()
export class SecurityHeadersMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: Function) {
    // Content Security Policy
    res.setHeader(
      "Content-Security-Policy",
      "default-src 'self'; script-src 'self' https://trusted-cdn.example.com; " +
        "style-src 'self' https://trusted-cdn.example.com; " +
        "img-src 'self' data: https://trusted-cdn.example.com; " +
        "connect-src 'self' https://api.example.com; " +
        "font-src 'self' https://trusted-cdn.example.com; " +
        "object-src 'none'; " +
        "media-src 'self'; " +
        "frame-src 'self'; " +
        "frame-ancestors 'self'; " +
        "form-action 'self';"
    );

    // Prevent browsers from interpreting files as a different MIME type
    res.setHeader("X-Content-Type-Options", "nosniff");

    // Prevent clickjacking
    res.setHeader("X-Frame-Options", "DENY");

    // Enables the Cross-site scripting (XSS) filter in browsers
    res.setHeader("X-XSS-Protection", "1; mode=block");

    // HTTPS strict transport security
    res.setHeader(
      "Strict-Transport-Security",
      "max-age=31536000; includeSubDomains; preload"
    );

    // Referrer policy
    res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");

    // Remove X-Powered-By
    res.removeHeader("X-Powered-By");

    next();
  }
}
```

### 13.2. Multi-Factor Authentication Implementation

```typescript
@Injectable()
export class MfaService {
  constructor(
    private readonly otpRepository: OtpRepository,
    private readonly userRepository: UserRepository,
    private readonly notificationService: NotificationService,
    private readonly cryptoService: CryptoService
  ) {}

  async generateTotp(userId: string): Promise<TotpSetupResponse> {
    const user = await this.userRepository.findById(userId);
    const secret = this.cryptoService.generateTotpSecret();

    // Store secret for user
    await this.otpRepository.saveUserSecret(userId, {
      type: "TOTP",
      secret: this.cryptoService.encryptSensitive(secret),
      createdAt: new Date(),
    });

    // Generate QR code
    const otpauth = this.generateOtpAuthUrl(user.email, secret);
    const qrCodeUrl = await this.generateQrCode(otpauth);

    return {
      secret,
      qrCodeUrl,
      otpauthUrl: otpauth,
    };
  }

  async verifyTotp(userId: string, token: string): Promise<boolean> {
    // Get user's TOTP secret
    const userSecret = await this.otpRepository.getUserSecret(userId, "TOTP");
    if (!userSecret) {
      return false;
    }

    // Decrypt the secret
    const secret = this.cryptoService.decryptSensitive(userSecret.secret);

    // Verify the token
    return this.cryptoService.verifyTotp(token, secret);
  }

  async sendSmsOtp(userId: string): Promise<void> {
    const user = await this.userRepository.findById(userId);

    // Generate OTP code
    const otp = this.cryptoService.generateNumericOtp(6);
    const expiresAt = new Date();
    expiresAt.setMinutes(expiresAt.getMinutes() + 10); // 10 minute expiry

    // Store OTP for verification
    await this.otpRepository.saveOtp(userId, {
      type: "SMS",
      hashedCode: await this.cryptoService.hashOtp(otp),
      expiresAt,
      attempts: 0,
    });

    // Send SMS
    await this.notificationService.sendSms(
      user.phoneNumber,
      `Your verification code is: ${otp}. It expires in 10 minutes.`
    );
  }

  async verifySmsOtp(userId: string, code: string): Promise<boolean> {
    // Get stored OTP
    const storedOtp = await this.otpRepository.getLatestOtp(userId, "SMS");

    if (!storedOtp || storedOtp.expiresAt < new Date()) {
      return false;
    }

    // Increment attempt counter
    await this.otpRepository.incrementAttempts(storedOtp.id);

    // Check if max attempts reached
    if (storedOtp.attempts >= 5) {
      await this.otpRepository.invalidateOtp(storedOtp.id);
      throw new TooManyAttemptsException();
    }

    // Verify code
    const isValid = await this.cryptoService.verifyOtpHash(
      code,
      storedOtp.hashedCode
    );

    if (isValid) {
      // Invalidate OTP after successful use
      await this.otpRepository.invalidateOtp(storedOtp.id);
    }

    return isValid;
  }
}
```

### 13.3. Secure Password Storage

```typescript
@Injectable()
export class PasswordService {
  constructor(
    private readonly configService: ConfigService,
    private readonly logger: Logger
  ) {}

  /**
   * Hash a password using Argon2id
   */
  async hashPassword(password: string): Promise<string> {
    try {
      return await argon2.hash(password, {
        type: argon2.argon2id,
        memoryCost: 2 ** 16, // 64 MiB
        timeCost: 3, // 3 iterations
        parallelism: 1, // 1 thread
        saltLength: 16, // 16 bytes
        hashLength: 32, // 32 bytes
      });
    } catch (error) {
      this.logger.error(`Error hashing password: ${error.message}`);
      throw new InternalServerErrorException("Error securing password");
    }
  }

  /**
   * Verify a password against a hash
   */
  async verifyPassword(password: string, hash: string): Promise<boolean> {
    try {
      return await argon2.verify(hash, password);
    } catch (error) {
      this.logger.error(`Error verifying password: ${error.message}`);
      throw new InternalServerErrorException(
        "Error during password verification"
      );
    }
  }

  /**
   * Check if password meets security requirements
   */
  validatePasswordStrength(password: string): ValidationResult {
    const errors = [];

    // Minimum length
    if (password.length < 12) {
      errors.push("Password must be at least 12 characters long");
    }

    // Character types
    if (!/[A-Z]/.test(password)) {
      errors.push("Password must contain at least one uppercase letter");
    }

    if (!/[a-z]/.test(password)) {
      errors.push("Password must contain at least one lowercase letter");
    }

    if (!/[0-9]/.test(password)) {
      errors.push("Password must contain at least one number");
    }

    if (!/[^A-Za-z0-9]/.test(password)) {
      errors.push("Password must contain at least one special character");
    }

    // Check against common password list (simplified for example)
    const commonPasswords = this.configService.get("security.commonPasswords");
    if (commonPasswords.includes(password.toLowerCase())) {
      errors.push("Password is too common and easily guessable");
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}
```

## 14. References

- [OWASP Security Standards](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Cloud Security Alliance](https://cloudsecurityalliance.org/)
- [PCI DSS Requirements](https://www.pcisecuritystandards.org/)
- [Infrastructure as Code Standards](./infrastructure-as-code-standards.md)
- [Internal Security Policies](../../security/policies/)
- [Incident Response Playbooks](../../security/incident-response/)
