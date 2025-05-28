# How to Think About Security: Defense in Depth Strategy

> **Learning Goal**: Develop a security mindset that anticipates threats and builds resilient defenses

---

## 🤔 STEP 1: Security as a Mindset, Not a Checklist

### What Problem Are We Really Solving?

**Surface Problem**: "We need to make our app secure"
**Real Problem**: "How do we protect valuable assets while enabling business functionality in the face of evolving threats?"

### 💭 The Adversarial Mindset

Most developers think:
```
Build feature → Add authentication → Check security box → Ship
```

Security engineers think:
```
Identify Assets → Threat Modeling → Attack Vectors → 
Defense Layers → Monitoring → Incident Response → Continuous Improvement
```

**❓ Stop and Think**: What would you do if you were trying to attack your own system?

**Common Attack Scenarios**:
1. **Data breaches** (steal customer data)
2. **Financial fraud** (manipulate transactions)
3. **Service disruption** (DDoS, system overload)
4. **Privilege escalation** (gain admin access)
5. **Supply chain attacks** (compromise dependencies)
6. **Social engineering** (trick users or employees)

**Security Mindset Shift**:
- 🔍 **Assume breach** (when, not if)
- 🎯 **Think like an attacker** (find weakest links)
- 🛡️ **Defense in depth** (multiple layers)
- 📊 **Continuous monitoring** (detect and respond)
- 🔄 **Regular updates** (evolve with threats)

**💡 Key Insight**: Security is not a destination, it's a continuous process of risk management.

---

## 🏗️ STEP 2: Threat Modeling Framework

### The STRIDE Method

**STRIDE** = **S**poofing, **T**ampering, **R**epudiation, **I**nformation Disclosure, **D**enial of Service, **E**levation of Privilege

#### Example: E-commerce Order System

```typescript
// System components to analyze
interface OrderSystem {
  components: {
    webApp: 'React frontend',
    apiGateway: 'Authentication and routing',
    orderService: 'Business logic',
    paymentService: 'Payment processing',
    database: 'Order and user data',
    messageQueue: 'Event processing'
  }
}
```

**Threat Analysis**:

| Component | Threat Type | Attack Scenario | Mitigation |
|-----------|-------------|-----------------|------------|
| Web App | **Spoofing** | Fake login page | HTTPS, CSP headers |
| API Gateway | **Tampering** | Modified requests | Input validation, signatures |
| Order Service | **Repudiation** | Deny placing order | Audit logs, digital signatures |
| Payment Service | **Information Disclosure** | Credit card theft | Encryption, tokenization |
| Database | **Denial of Service** | SQL injection overload | Rate limiting, parameterized queries |
| Message Queue | **Elevation of Privilege** | Admin access via queue | Authentication, authorization |

### Data Flow Diagram Analysis

```
User → [Web App] → [API Gateway] → [Order Service] → [Database]
                     ↓                    ↓
                 [Auth Service]     [Payment Service]
```

**Security Boundaries**:
- 🌐 **Internet/Intranet boundary** (external users)
- 🔐 **Authentication boundary** (authenticated users)
- 🏛️ **Service boundaries** (internal services)
- 💾 **Data storage boundary** (persistent data)

**❓ For each boundary, ask**: "What happens if this boundary is compromised?"

---

## 🛡️ STEP 3: Authentication and Authorization Architecture

### Beyond Basic Auth: Modern Identity Architecture

#### Zero Trust Authentication
**Mental Model**: "Never trust, always verify"

```typescript
// Traditional perimeter security (outdated)
if (request.isFromInternalNetwork()) {
  return allowAccess(); // Dangerous assumption
}

// Zero trust approach
async function authenticateRequest(request: Request): Promise<AuthContext> {
  // 1. Verify identity
  const token = await validateJWT(request.headers.authorization);
  
  // 2. Check session validity
  const session = await sessionStore.get(token.sessionId);
  if (session.isExpired() || session.isRevoked()) {
    throw new UnauthorizedException();
  }
  
  // 3. Verify device/location if suspicious
  if (await isSuspiciousActivity(token.userId, request)) {
    await requireAdditionalVerification(token.userId);
  }
  
  // 4. Build context for authorization
  return {
    userId: token.userId,
    roles: token.roles,
    permissions: await getPermissions(token.userId),
    deviceTrust: await getDeviceTrustScore(request),
    riskScore: await calculateRiskScore(request)
  };
}
```

#### Multi-Factor Authentication Strategy

```typescript
interface MFAChallenge {
  type: 'sms' | 'totp' | 'webauthn' | 'backup-codes';
  required: boolean;
  riskScore: number;
}

class AdaptiveMFA {
  async determineRequiredFactors(authContext: AuthContext): Promise<MFAChallenge[]> {
    const challenges: MFAChallenge[] = [];
    
    // Always require password (something you know)
    challenges.push({ type: 'password', required: true, riskScore: 0 });
    
    // Risk-based additional factors
    if (authContext.newDevice || authContext.newLocation) {
      challenges.push({ type: 'sms', required: true, riskScore: 5 });
    }
    
    if (authContext.highValueOperation) {
      challenges.push({ type: 'webauthn', required: true, riskScore: 3 });
    }
    
    if (authContext.adminAccess) {
      challenges.push({ type: 'totp', required: true, riskScore: 7 });
    }
    
    return challenges;
  }
}
```

### Authorization Patterns

#### Role-Based Access Control (RBAC)
```typescript
// Simple but limited
interface User {
  id: string;
  roles: string[]; // ['admin', 'manager', 'user']
}

function canAccess(user: User, resource: string, action: string): boolean {
  if (user.roles.includes('admin')) return true;
  if (resource === 'orders' && action === 'read' && user.roles.includes('manager')) return true;
  return false;
}
```

#### Attribute-Based Access Control (ABAC)
```typescript
// More flexible and granular
interface AuthorizationContext {
  subject: {
    userId: string;
    department: string;
    clearanceLevel: number;
    roles: string[];
  };
  resource: {
    type: string;
    owner: string;
    classification: string;
    department: string;
  };
  action: string;
  environment: {
    time: Date;
    location: string;
    networkType: 'internal' | 'external';
  };
}

class ABACEngine {
  async authorize(context: AuthorizationContext): Promise<boolean> {
    const policies = await this.getPoliciesForResource(context.resource.type);
    
    for (const policy of policies) {
      if (await this.evaluatePolicy(policy, context)) {
        return policy.effect === 'allow';
      }
    }
    
    return false; // Deny by default
  }
  
  async evaluatePolicy(policy: Policy, context: AuthorizationContext): Promise<boolean> {
    // Example policy: "Managers can read orders from their department during business hours"
    return (
      context.subject.roles.includes('manager') &&
      context.action === 'read' &&
      context.resource.type === 'order' &&
      context.subject.department === context.resource.department &&
      this.isBusinessHours(context.environment.time)
    );
  }
}
```

---

## 🔐 STEP 4: Data Protection Strategy

### Encryption Strategy

#### Data at Rest
```typescript
// Database level encryption
class EncryptedUserRepository {
  async saveUser(user: User): Promise<void> {
    const encryptedUser = {
      ...user,
      email: await this.encryption.encrypt(user.email),
      socialSecurityNumber: await this.encryption.encrypt(user.ssn),
      creditCardToken: await this.tokenization.tokenize(user.creditCard)
    };
    
    await this.database.save(encryptedUser);
  }
  
  async getUser(id: string): Promise<User> {
    const encryptedUser = await this.database.findById(id);
    
    return {
      ...encryptedUser,
      email: await this.encryption.decrypt(encryptedUser.email),
      socialSecurityNumber: await this.encryption.decrypt(encryptedUser.socialSecurityNumber),
      creditCard: await this.tokenization.detokenize(encryptedUser.creditCardToken)
    };
  }
}
```

#### Data in Transit
```typescript
// API security headers
app.use((req, res, next) => {
  // Force HTTPS
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  
  // Prevent content type sniffing
  res.setHeader('X-Content-Type-Options', 'nosniff');
  
  // XSS protection
  res.setHeader('X-XSS-Protection', '1; mode=block');
  
  // Content Security Policy
  res.setHeader('Content-Security-Policy', 
    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
  );
  
  next();
});
```

### Data Classification and Handling

```typescript
enum DataClassification {
  PUBLIC = 'public',           // Can be shared publicly
  INTERNAL = 'internal',       // Internal use only
  CONFIDENTIAL = 'confidential', // Restricted access
  RESTRICTED = 'restricted'    // Highest security
}

interface DataField {
  name: string;
  classification: DataClassification;
  retention: {
    period: string; // '7 years', '30 days'
    action: 'delete' | 'archive';
  };
  encryption: {
    required: boolean;
    algorithm: string;
  };
  access: {
    roles: string[];
    audit: boolean;
  };
}

// User data classification
const userDataFields: DataField[] = [
  {
    name: 'email',
    classification: DataClassification.CONFIDENTIAL,
    retention: { period: '7 years', action: 'archive' },
    encryption: { required: true, algorithm: 'AES-256' },
    access: { roles: ['user', 'admin'], audit: true }
  },
  {
    name: 'purchaseHistory',
    classification: DataClassification.INTERNAL,
    retention: { period: '2 years', action: 'delete' },
    encryption: { required: false, algorithm: '' },
    access: { roles: ['user', 'sales', 'admin'], audit: false }
  }
];
```

---

## 🚨 STEP 5: Input Validation and Injection Prevention

### Comprehensive Input Validation

```typescript
// Layered validation approach
class SecurityValidation {
  async validateUserInput(input: any, schema: ValidationSchema): Promise<ValidatedInput> {
    // 1. Schema validation (structure and types)
    const schemaResult = await this.schemaValidator.validate(input, schema);
    if (!schemaResult.isValid) {
      throw new ValidationError('Invalid input structure', schemaResult.errors);
    }
    
    // 2. Security validation (injection attempts, malicious patterns)
    const securityResult = await this.securityValidator.validate(input);
    if (!securityResult.isValid) {
      await this.securityLog.logSuspiciousActivity(input, securityResult.threats);
      throw new SecurityError('Suspicious input detected');
    }
    
    // 3. Business logic validation (business rules)
    const businessResult = await this.businessValidator.validate(input);
    if (!businessResult.isValid) {
      throw new BusinessError('Business rule violation', businessResult.errors);
    }
    
    return schemaResult.sanitizedInput;
  }
}

// SQL injection prevention
class DatabaseService {
  async getUserOrders(userId: string): Promise<Order[]> {
    // ❌ Vulnerable to SQL injection
    // const query = `SELECT * FROM orders WHERE user_id = '${userId}'`;
    
    // ✅ Use parameterized queries
    const query = 'SELECT * FROM orders WHERE user_id = $1';
    return this.database.query(query, [userId]);
  }
  
  async searchProducts(searchTerm: string): Promise<Product[]> {
    // ✅ Validate and sanitize input
    const sanitizedTerm = this.sanitizer.sanitizeSearchTerm(searchTerm);
    const query = 'SELECT * FROM products WHERE name ILIKE $1 LIMIT 100';
    return this.database.query(query, [`%${sanitizedTerm}%`]);
  }
}
```

### Cross-Site Scripting (XSS) Prevention

```typescript
// Content Security Policy implementation
class CSPPolicy {
  generateCSP(context: RequestContext): string {
    const nonce = this.generateNonce();
    
    const policy = [
      `default-src 'self'`,
      `script-src 'self' 'nonce-${nonce}' https://trusted-analytics.com`,
      `style-src 'self' 'unsafe-inline'`, // Consider inline styles carefully
      `img-src 'self' data: https://trusted-cdn.com`,
      `connect-src 'self' https://api.example.com`,
      `font-src 'self' https://fonts.googleapis.com`,
      `object-src 'none'`,
      `base-uri 'self'`,
      `form-action 'self'`,
      `frame-ancestors 'none'`
    ];
    
    return policy.join('; ');
  }
}

// Output encoding
class OutputEncoder {
  encodeForHTML(input: string): string {
    return input
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  }
  
  encodeForHTMLAttribute(input: string): string {
    return input.replace(/[^a-zA-Z0-9]/g, (char) => {
      return `&#x${char.charCodeAt(0).toString(16)};`;
    });
  }
  
  encodeForJavaScript(input: string): string {
    return JSON.stringify(input); // Use JSON.stringify for safety
  }
}
```

---

## 📊 STEP 6: Security Monitoring and Incident Response

### Security Event Detection

```typescript
// Security event monitoring
class SecurityMonitor {
  async monitorLoginAttempts(userId: string, clientIP: string): Promise<void> {
    const recentAttempts = await this.getRecentLoginAttempts(userId, clientIP);
    
    // Detect brute force attacks
    if (recentAttempts.failed > 5 && recentAttempts.timespan < 300) { // 5 failures in 5 minutes
      await this.handleBruteForceAttack(userId, clientIP);
    }
    
    // Detect credential stuffing
    if (recentAttempts.uniqueUserIds > 50 && recentAttempts.sameIP) { // 50+ users from same IP
      await this.handleCredentialStuffing(clientIP);
    }
    
    // Detect impossible travel
    const lastLocation = await this.getLastLoginLocation(userId);
    if (await this.isImpossibleTravel(lastLocation, clientIP)) {
      await this.handleImpossibleTravel(userId, clientIP);
    }
  }
  
  async detectDataExfiltration(userId: string, dataAccess: DataAccessEvent): Promise<void> {
    const baseline = await this.getUserBaseline(userId);
    
    // Unusual data access patterns
    if (dataAccess.recordsAccessed > baseline.averageRecords * 10) {
      await this.alertSecurityTeam('UNUSUAL_DATA_ACCESS', {
        userId,
        recordsAccessed: dataAccess.recordsAccessed,
        baseline: baseline.averageRecords
      });
    }
    
    // Access to sensitive data outside normal hours
    if (dataAccess.classification === 'RESTRICTED' && !this.isBusinessHours()) {
      await this.alertSecurityTeam('OFF_HOURS_SENSITIVE_ACCESS', {
        userId,
        dataAccessed: dataAccess.type,
        time: new Date()
      });
    }
  }
}
```

### Incident Response Automation

```typescript
// Automated incident response
class IncidentResponse {
  async handleSecurityIncident(incident: SecurityIncident): Promise<void> {
    // 1. Immediate containment
    await this.containThreat(incident);
    
    // 2. Evidence preservation
    await this.preserveEvidence(incident);
    
    // 3. Stakeholder notification
    await this.notifyStakeholders(incident);
    
    // 4. Investigation initiation
    await this.initiateInvestigation(incident);
  }
  
  async containThreat(incident: SecurityIncident): Promise<void> {
    switch (incident.type) {
      case 'BRUTE_FORCE_ATTACK':
        await this.blockIP(incident.sourceIP);
        await this.lockAccount(incident.targetUserId);
        break;
        
      case 'DATA_BREACH_SUSPECTED':
        await this.revokeUserSessions(incident.affectedUsers);
        await this.enableEnhancedLogging();
        break;
        
      case 'MALWARE_DETECTED':
        await this.isolateAffectedSystems(incident.affectedSystems);
        await this.runMalwareScan();
        break;
    }
  }
  
  async preserveEvidence(incident: SecurityIncident): Promise<void> {
    const evidence = {
      logs: await this.captureLogs(incident.timeRange),
      networkTraffic: await this.captureNetworkData(incident.sourceIP),
      systemSnapshots: await this.captureSystemState(incident.affectedSystems),
      userActions: await this.captureUserActivity(incident.affectedUsers)
    };
    
    await this.storeEvidence(incident.id, evidence);
  }
}
```

---

## 🔄 STEP 7: Secure Development Lifecycle

### Security by Design

```typescript
// Security requirements gathering
interface SecurityRequirement {
  category: 'authentication' | 'authorization' | 'encryption' | 'audit' | 'privacy';
  requirement: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  compliance: string[]; // ['GDPR', 'PCI-DSS', 'HIPAA']
  implementationGuidance: string;
}

const ecommerceSecurityRequirements: SecurityRequirement[] = [
  {
    category: 'authentication',
    requirement: 'Multi-factor authentication for admin accounts',
    riskLevel: 'critical',
    compliance: ['PCI-DSS'],
    implementationGuidance: 'Implement TOTP or WebAuthn for admin users'
  },
  {
    category: 'encryption',
    requirement: 'PII must be encrypted at rest and in transit',
    riskLevel: 'high',
    compliance: ['GDPR', 'PCI-DSS'],
    implementationGuidance: 'Use AES-256 for data at rest, TLS 1.3 for data in transit'
  }
];
```

### Security Testing Strategy

```typescript
// Security testing pyramid
class SecurityTestSuite {
  // Unit level - test individual security functions
  async testPasswordValidation(): Promise<void> {
    const weakPasswords = ['123456', 'password', 'qwerty'];
    for (const password of weakPasswords) {
      expect(validatePassword(password)).toBe(false);
    }
    
    const strongPassword = 'MyStr0ng!P@ssw0rd';
    expect(validatePassword(strongPassword)).toBe(true);
  }
  
  // Integration level - test security between components
  async testAuthenticationFlow(): Promise<void> {
    const user = await this.createTestUser();
    
    // Test successful authentication
    const loginResponse = await this.loginUser(user.email, user.password);
    expect(loginResponse.token).toBeDefined();
    
    // Test token validation
    const protectedResource = await this.accessProtectedResource(loginResponse.token);
    expect(protectedResource.status).toBe(200);
    
    // Test token expiration
    await this.advanceTime('1 hour');
    const expiredAccess = await this.accessProtectedResource(loginResponse.token);
    expect(expiredAccess.status).toBe(401);
  }
  
  // System level - test complete security scenarios
  async testSecurityScenarios(): Promise<void> {
    await this.testSQLInjectionPrevention();
    await this.testXSSPrevention();
    await this.testCSRFProtection();
    await this.testRateLimiting();
    await this.testDataEncryption();
  }
}
```

### Vulnerability Management

```typescript
// Continuous vulnerability scanning
class VulnerabilityManager {
  async scanDependencies(): Promise<VulnerabilityReport> {
    // Scan package dependencies
    const npmAudit = await this.runNpmAudit();
    const synkScan = await this.runSynkScan();
    
    // Scan container images
    const containerScan = await this.scanContainerImages();
    
    // Scan infrastructure
    const infraScan = await this.scanInfrastructure();
    
    return this.aggregateResults([npmAudit, synkScan, containerScan, infraScan]);
  }
  
  async prioritizeVulnerabilities(vulnerabilities: Vulnerability[]): Promise<Vulnerability[]> {
    return vulnerabilities.sort((a, b) => {
      // Prioritize by CVSS score, exploitability, and business impact
      const scoreA = this.calculatePriorityScore(a);
      const scoreB = this.calculatePriorityScore(b);
      return scoreB - scoreA;
    });
  }
  
  private calculatePriorityScore(vuln: Vulnerability): number {
    let score = vuln.cvssScore * 10; // Base CVSS score
    
    // Adjust for exploitability
    if (vuln.exploitAvailable) score *= 1.5;
    if (vuln.remoteExploitable) score *= 1.3;
    
    // Adjust for business impact
    if (vuln.affectsProduction) score *= 2;
    if (vuln.affectsCustomerData) score *= 1.8;
    
    return score;
  }
}
```

---

## 💡 Key Mental Models You've Learned

### 1. **Adversarial Thinking**
- Think like an attacker to find weaknesses
- Assume breach will happen, prepare response
- Question every assumption about trust

### 2. **Defense in Depth**
- Multiple layers of security controls
- Fail securely when one layer is compromised
- Security as a system property, not a feature

### 3. **Zero Trust Architecture**
- Never trust, always verify
- Verify identity, device, and context
- Continuous authentication and authorization

### 4. **Risk-Based Decision Making**
- Security controls proportional to risk
- Business impact drives security investment
- Continuous risk assessment and adjustment

### 5. **Security as Enabler**
- Security enables business functionality
- Usable security is more effective
- Security integrated into development process

---

## 🚀 What You Can Do Now

You've mastered security thinking:

1. **Assess** threats using systematic threat modeling
2. **Design** layered security controls and defenses
3. **Implement** secure authentication and authorization
4. **Monitor** for security events and respond to incidents
5. **Integrate** security into the development lifecycle

**❓ Final Challenge**:
Design a comprehensive security strategy for a healthcare application.

**Consider**:
- What are the key assets to protect?
- What compliance requirements apply (HIPAA)?
- How would you implement patient data access controls?
- What monitoring would you implement?
- How would you handle a data breach?

**Think through**:
- Patient privacy requirements
- Medical device integration security
- Provider authentication and authorization
- Audit trails and compliance reporting
- Emergency access procedures

If you can design this security strategy with clear reasoning for each control, you're thinking like a security architect! 🛡️✨