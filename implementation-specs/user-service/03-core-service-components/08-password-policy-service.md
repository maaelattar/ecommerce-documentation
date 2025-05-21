# 08 - PasswordPolicyService

The `PasswordPolicyService` is responsible for defining, enforcing, and validating password policies within the User Service. It ensures that user-chosen passwords meet the security requirements of the application, such as complexity, length, and uniqueness (non-breached).

This service is primarily consumed by the `AuthService` during registration and password change/reset operations.

## 1. Responsibilities

*   **Define Password Policies**: Centralize the definition of password rules, which might include:
    *   Minimum and maximum length.
    *   Required character types (e.g., uppercase, lowercase, numbers, special characters).
    *   Prohibition of common or easily guessable passwords.
    *   Password history (preventing reuse of recent passwords).
    *   Password expiration (though this is sometimes debated for usability vs. security).
*   **Validate Passwords**: Provide methods to check a given password string against the defined policies.
*   **Provide Policy Details**: Offer a way to retrieve the current password policy rules (e.g., for display on a registration or password change form).
*   **Breached Password Detection (Pwned Passwords)**: Integrate with services like Have I Been Pwned (HIBP) to check if a password has appeared in known data breaches.

## 2. Key Methods (Conceptual NestJS Example)

```typescript
import { Injectable, BadRequestException } from '@nestjs/common';
import * as zxcvbn from 'zxcvbn'; // A popular password strength estimator
// In a real application, you might use a dedicated library for HIBP or an internal service.
// For this example, we'll mock the HIBP check.
import { HttpService } from '@nestjs/axios'; // For making HTTP requests to HIBP (if used)
import { firstValueFrom } from 'rxjs';
import * as crypto from 'crypto';

export interface PasswordPolicy {
  minLength: number;
  maxLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  disallowedCommonWords?: string[]; // Example, could be more sophisticated
  zxcvbnMinScore?: number; // Minimum score from zxcvbn (0-4)
  checkPwnedPasswords?: boolean;
  passwordHistoryCount?: number; // How many past passwords to check against
}

@Injectable()
export class PasswordPolicyService {
  private currentPolicy: PasswordPolicy;

  constructor(private readonly httpService: HttpService) {
    // Policies can be loaded from configuration
    this.currentPolicy = {
      minLength: 10,
      maxLength: 128,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
      zxcvbnMinScore: 2, // A reasonable minimum, higher is stronger
      checkPwnedPasswords: true,
      passwordHistoryCount: 5,
      disallowedCommonWords: ['password', '123456', 'qwerty', 'admin'],
    };
  }

  getCurrentPolicy(): PasswordPolicy {
    return this.currentPolicy;
  }

  async validatePassword(
    password: string,
    userId?: string, // Optional, for checking password history
    oldHashedPasswords: string[] = [] // Hashes of user's previous passwords
  ): Promise<{ isValid: boolean; messages: string[] }> {
    const messages: string[] = [];

    if (password.length < this.currentPolicy.minLength) {
      messages.push(`Password must be at least ${this.currentPolicy.minLength} characters long.`);
    }
    if (password.length > this.currentPolicy.maxLength) {
      messages.push(`Password must be no more than ${this.currentPolicy.maxLength} characters long.`);
    }
    if (this.currentPolicy.requireUppercase && !/[A-Z]/.test(password)) {
      messages.push('Password must contain at least one uppercase letter.');
    }
    if (this.currentPolicy.requireLowercase && !/[a-z]/.test(password)) {
      messages.push('Password must contain at least one lowercase letter.');
    }
    if (this.currentPolicy.requireNumbers && !/[0-9]/.test(password)) {
      messages.push('Password must contain at least one number.');
    }
    if (this.currentPolicy.requireSpecialChars && !/[^A-Za-z0-9]/.test(password)) {
      messages.push('Password must contain at least one special character.');
    }
    if (this.currentPolicy.disallowedCommonWords?.some(word => password.toLowerCase().includes(word))) {
      messages.push('Password contains a common or disallowed word.');
    }

    // ZXCVBN score check
    if (this.currentPolicy.zxcvbnMinScore !== undefined) {
      const strength = zxcvbn(password);
      if (strength.score < this.currentPolicy.zxcvbnMinScore) {
        messages.push(`Password is too weak. Score: ${strength.score}/${this.currentPolicy.zxcvbnMinScore}. Suggestions: ${strength.feedback.suggestions?.join(' ')}`);
      }
    }

    // Pwned passwords check
    if (this.currentPolicy.checkPwnedPasswords) {
      try {
        const isPwned = await this.isPasswordPwned(password);
        if (isPwned) {
          messages.push('This password has appeared in a data breach and should not be used.');
        }
      } catch (error) {
        console.error('Error checking pwned password:', error);
        // Decide if this should be a hard fail or a soft fail (e.g., allow if service is down)
        // messages.push('Could not verify if password was breached. Please try a different password.');
      }
    }
    
    // Password history check
    // This requires access to the user's previous hashed passwords and a way to compare the new plain password against them.
    // This is a conceptual example; actual implementation needs secure handling of password comparison.
    if (userId && this.currentPolicy.passwordHistoryCount && this.currentPolicy.passwordHistoryCount > 0) {
        // This part is tricky. We don't want to re-hash the new password with every old salt.
        // Instead, the AuthService, when changing a password, should hash the NEW password with the user's CURRENT salt
        // and then compare this NEW hash against a list of PREVIOUSLY STORED HASHES for that user.
        // The PasswordPolicyService itself might not do the hashing for history checks, but flags the requirement.
        // For simplicity, if `oldHashedPasswords` (bcrypt hashes) were passed, AuthService would try to match `password` against them.
        // This is a placeholder for a more robust check, typically done in AuthService.
    }

    return { isValid: messages.length === 0, messages };
  }

  // K-Anonymity model for checking Pwned Passwords API
  // See: https://haveibeenpwned.com/API/v3#PwnedPasswords
  private async isPasswordPwned(password: string): Promise<boolean> {
    const sha1Hash = crypto.createHash('sha1').update(password).digest('hex').toUpperCase();
    const prefix = sha1Hash.substring(0, 5);
    const suffix = sha1Hash.substring(5);

    try {
      const response = await firstValueFrom(
        this.httpService.get(`https://api.pwnedpasswords.com/range/${prefix}`, {
          headers: { 'Add-Padding': 'true' } // Optional: helps obfuscate the exact hash length
        })
      );
      const hashes = response.data.split('\r\n');
      for (const line of hashes) {
        const [hashSuffix, count] = line.split(':');
        if (hashSuffix === suffix) {
          console.warn(`Password pwned ${count} times.`);
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Failed to query Pwned Passwords API:', error.message);
      // Depending on policy, either fail open (assume not pwned if API fails) or fail closed.
      // For security, failing closed (or asking user to try different password) is often better if API is critical.
      throw new Error('Pwned Passwords API check failed.'); 
    }
  }
}
```

## 3. Interactions

*   **`AuthService`**: The primary consumer. `AuthService` calls `PasswordPolicyService.validatePassword()` during:
    *   User registration.
    *   Password change process.
    *   Password reset process.
*   **Configuration Source**: Password policies (length, complexity rules) are often configurable and might be loaded from environment variables, a configuration file, or a database at startup.
*   **External Services (e.g., Have I Been Pwned)**: For checking if a password has been compromised in known data breaches.
*   **`UserService` (or User Entity/Repository)**: Indirectly, if password history is enforced, the `PasswordPolicyService` (or `AuthService` using its rules) would need access to a user's previous password hashes to prevent reuse.

## 4. Policy Configuration

*   **Flexibility**: Policies should be configurable without requiring code changes.
*   **Clarity**: The policy rules should be easily understandable by developers and potentially presentable to end-users.

## 5. Security Considerations

*   **Strength of Policies**: The chosen policies should reflect current best practices for password security (e.g., NIST guidelines often recommend length and breach checks over frequent forced changes or complex arbitrary rules).
*   **Protection of Policy Configuration**: If policies are dynamically configurable, ensure that the mechanism for changing them is secure and restricted.
*   **Rate Limiting on Validation**: While validation is internal, if an endpoint directly exposes policy validation, it should be rate-limited.
*   **Handling Breached Password Check Failures**: Decide on a strategy if the external breached password service is unavailable (fail open, fail closed, or degrade gracefully).
*   **Password History Implementation**: If implementing password history, ensure it's done securely. Do not store old passwords in a less secure way than the current password. Comparing a new plaintext password against old hashes requires care (typically, hash the new password with each of the old salts and compare hashes, or hash new password with current salt and compare with list of previous hashes if salts were consistent or stored per hash).

## 6. Future Enhancements

*   **Dynamic Policy Updates**: Ability to update password policies in real-time without service restart (if stored in a dynamic configuration source).
*   **User-Specific Policies**: Potentially allowing different policies for different user groups (e.g., administrators vs. regular users), though this adds complexity.
*   **Adaptive Policies**: Policies that adjust based on risk signals (e.g., requiring stronger passwords after suspicious login attempts).
*   **UI Feedback**: Providing more granular feedback to the UI about which specific policy rules are not being met.

`PasswordPolicyService` is a crucial component for maintaining a baseline of password hygiene and protecting user accounts from common password-related attacks.
