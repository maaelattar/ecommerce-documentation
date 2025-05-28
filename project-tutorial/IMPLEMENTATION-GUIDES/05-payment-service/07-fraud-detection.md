# 07. Fraud Detection & Risk Management

## Overview

Implement basic fraud detection patterns and risk management to protect against fraudulent transactions while maintaining a smooth user experience for legitimate customers.

## 🎯 Learning Objectives

- Build fraud detection rule engine
- Implement velocity checking
- Create risk scoring algorithms
- Add blacklist/whitelist management
- Design manual review workflows

---

## Step 1: Risk Assessment Service

```typescript
// src/modules/fraud/services/risk-assessment.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { RiskAssessment } from '../entities/risk-assessment.entity';

@Injectable()
export class RiskAssessmentService {
  private readonly logger = new Logger(RiskAssessmentService.name);

  constructor(
    @InjectRepository(RiskAssessment)
    private riskRepository: Repository<RiskAssessment>,
  ) {}

  async assessPaymentRisk(paymentData: any): Promise<RiskScore> {
    const riskFactors = await this.calculateRiskFactors(paymentData);
    const riskScore = this.calculateOverallRisk(riskFactors);
    
    await this.saveRiskAssessment(paymentData.paymentId, riskFactors, riskScore);
    
    return {
      score: riskScore,
      level: this.getRiskLevel(riskScore),
      factors: riskFactors,
      recommendation: this.getRecommendation(riskScore),
    };
  }

  private async calculateRiskFactors(paymentData: any): Promise<RiskFactors> {
    return {
      velocityRisk: await this.checkVelocity(paymentData.customerId),
      amountRisk: this.checkAmountRisk(paymentData.amount),
      locationRisk: await this.checkLocationRisk(paymentData.ipAddress),
      deviceRisk: await this.checkDeviceRisk(paymentData.deviceFingerprint),
      blacklistRisk: await this.checkBlacklist(paymentData.customerId),
    };
  }
}
```