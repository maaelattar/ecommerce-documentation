# CI/CD Pipeline Specification

## 1. Introduction

This document specifies the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the e-commerce platform. It defines how code changes will be built, tested, and deployed to various environments in an automated, consistent, and secure manner. The pipeline leverages AWS services and integrates with our development tools to ensure a smooth development-to-production workflow.

## 2. Pipeline Architecture

### 2.1. High-Level Overview

The CI/CD pipeline follows this high-level workflow:

1. Code committed to GitHub repository
2. Automated testing triggered (linting, unit tests, security scans)
3. Build process creates container images
4. Container images pushed to Amazon ECR
5. Deployment to appropriate environment based on branch/tag
6. Post-deployment validation and notifications

### 2.2. Environments

| Environment | Purpose                         | Deployment Trigger          | Approval Required |
| ----------- | ------------------------------- | --------------------------- | ----------------- |
| Development | Development and feature testing | Push to feature branches    | No                |
| Testing     | Integration testing             | Merge to `develop` branch   | No                |
| Staging     | Pre-production validation       | Merge to `release/*` branch | Yes               |
| Production  | Live system                     | Merge to `main` branch      | Yes               |

## 3. Tools and Services

### 3.1. Source Control

- **System**: GitHub
- **Branching Strategy**: GitFlow
  - `main`: Production code
  - `develop`: Integration branch
  - `feature/*`: Feature development
  - `release/*`: Release preparation
  - `hotfix/*`: Production fixes

### 3.2. CI/CD Orchestration

#### 3.2.1. Primary: AWS CodePipeline

- **Purpose**: Orchestrate the overall CI/CD workflow
- **Configuration**: Infrastructure-as-Code via AWS CDK
- **Integration Points**:
  - GitHub (source)
  - AWS CodeBuild (build and test)
  - AWS ECR (container registry)
  - AWS EKS (deployment target)

#### 3.2.2. Alternative: GitHub Actions

- **Purpose**: Provide additional CI capabilities and developer-friendly workflows
- **Configuration**: YAML files in `.github/workflows/`
- **Integration Points**:
  - AWS credentials via GitHub Secrets
  - Direct EKS deployment via GitHub Action

### 3.3. Build and Test

- **AWS CodeBuild**:
  - Compute: 8 vCPU, 16GB RAM
  - Timeout: 30 minutes
  - Caching: Source and dependencies in S3
- **Security Scanning**:
  - Amazon ECR image scanning
  - SonarQube code quality analysis
  - OWASP dependency checks

### 3.4. Deployment Tools

- **ArgoCD**:
  - GitOps controller for Kubernetes deployments
  - Application configuration stored in Git
  - Automated sync with target environments
- **Helm**:
  - Package microservices as Helm charts
  - Versioning and release management
  - Environment-specific value overrides

### 3.5. Local Development Integration

- **Tilt**:
  - Local Kubernetes development
  - Fast feedback loops during development
  - Integration with pipeline for consistent build process
- **Telepresence**:
  - Local-to-cluster development
  - Intercept traffic for local debugging
  - Test local changes against remote dependencies
- **OpenLens**:
  - Kubernetes dashboard for visualization
  - Monitor local and remote cluster state
  - Debug deployments and services

## 4. Pipeline Stages

### 4.1. Continuous Integration

#### 4.1.1. Code Validation

```yaml
# Example GitHub Action for code validation
name: Code Validation
on:
  push:
    branches: ["**"]
  pull_request:
    branches: [develop, main, release/*]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: "20"
          cache: "npm"
      - name: Install dependencies
        run: npm ci
      - name: Lint code
        run: npm run lint
      - name: Run unit tests
        run: npm run test
      - name: SonarQube scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

#### 4.1.2. Build Process

```yaml
# Example CodeBuild buildspec.yml
version: 0.2

phases:
  install:
    runtime-versions:
      nodejs: 20
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $REPOSITORY_URI:latest .
      - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $REPOSITORY_URI:latest
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - echo Writing image definition file...
      - aws ecr describe-images --repository-name $IMAGE_REPO_NAME --image-ids imageTag=latest --query 'imageDetails[].imageTags[0]' --output text
      - echo "{\"ImageURI\":\"$REPOSITORY_URI:$IMAGE_TAG\"}" > imageDefinition.json

artifacts:
  files:
    - imageDefinition.json
    - appspec.yaml
    - taskdef.json
```

### 4.2. Continuous Deployment

#### 4.2.1. ArgoCD Application Configuration

```yaml
# Example ArgoCD Application manifest
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: product-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: git@github.com:example/ecommerce-infra.git
    targetRevision: HEAD
    path: kubernetes/apps/product-service
    helm:
      valueFiles:
        - values-${ENV}.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: ecommerce
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

#### 4.2.2. AWS CodePipeline Configuration

```hcl
# Example Terraform for AWS CodePipeline
resource "aws_codepipeline" "ecommerce_pipeline" {
  name     = "ecommerce-${var.service_name}-pipeline"
  role_arn = aws_iam_role.codepipeline_role.arn

  artifact_store {
    location = aws_s3_bucket.codepipeline_bucket.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.github.arn
        FullRepositoryId = "example/ecommerce-${var.service_name}"
        BranchName       = var.branch_name
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "BuildAndTest"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"

      configuration = {
        ProjectName = aws_codebuild_project.service_build.name
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "CodeBuildDeploy"
      input_artifacts = ["build_output"]
      version         = "1"

      configuration = {
        ProjectName = aws_codebuild_project.service_deploy.name
        EnvironmentVariables = jsonencode([
          {
            name  = "ENVIRONMENT"
            value = var.environment
            type  = "PLAINTEXT"
          }
        ])
      }
    }
  }
}
```

### 4.3. Deployment Strategies

#### 4.3.1. Blue/Green Deployment

- **Implementation**: AWS CodeDeploy with EKS
- **Process**:
  1. New version deployed alongside existing version
  2. Traffic gradually shifted to new version
  3. Old version terminated after successful validation
- **Rollback**: Immediate traffic shift back to blue environment

#### 4.3.2. Canary Deployment

- **Implementation**: AWS App Mesh + ArgoCD
- **Process**:
  1. Deploy new version to small percentage of traffic (5%)
  2. Monitor metrics, logs, and errors
  3. Gradually increase traffic percentage (5% → 20% → 50% → 100%)
  4. Abort if any issues detected
- **Configuration**:
  ```yaml
  canary:
    steps:
      - setWeight: 5
      - pause: { duration: 10m }
      - setWeight: 20
      - pause: { duration: 10m }
      - setWeight: 50
      - pause: { duration: 10m }
      - setWeight: 100
  ```

## 5. Security Measures

### 5.1. Secrets Management

- **AWS Secrets Manager**:
  - Store sensitive configuration
  - Automatic rotation
  - Integration with EKS via External Secrets Operator
- **GitHub Secrets**:
  - Store CI/CD credentials
  - Limited to specific workflows and repos

### 5.2. Pipeline Security

- **IAM Roles**:
  - Least privilege principle
  - Service-specific roles
  - Temporary credentials
- **Artifact Signing**:
  - Sign container images with AWS Signer
  - Verify signatures before deployment

### 5.3. Security Scans

- **Static Application Security Testing (SAST)**:
  - SonarQube integration
  - Fail pipeline on high-severity issues
- **Dynamic Application Security Testing (DAST)**:
  - OWASP ZAP scans against staging
  - Run weekly against production

## 6. Developer Experience

### 6.1. Local Development Workflow

1. **Setup Local Environment**:

   ```bash
   git clone https://github.com/example/ecommerce-product-service.git
   cd ecommerce-product-service
   npm install
   tilt up # Start local Kubernetes dev environment
   ```

2. **Feature Development**:

   ```bash
   git checkout -b feature/new-feature
   # Make changes
   npm test # Run tests locally
   git commit -am "Add new feature"
   git push origin feature/new-feature
   ```

3. **Pull Request Workflow**:
   - Create PR against `develop` branch
   - CI pipeline runs automatically
   - Review feedback and make changes
   - Merge when approved

### 6.2. Telepresence Integration

For testing local changes against a development cluster:

```bash
# Start telepresence
telepresence connect

# Intercept specific service
telepresence intercept product-service \
  --port 3000:80 \
  --env-file=.env.remote \
  --namespace ecommerce

# Run service locally
npm run start:dev

# Stop intercept when done
telepresence leave product-service
```

### 6.3. Developer Tools

- **Tilt Dashboard**: `http://localhost:10350/`
- **OpenLens**: Connect to local or remote clusters
- **ArgoCD UI**: `https://argocd.dev.example.com`
- **Pipeline Status**: AWS CodePipeline console or GitHub Actions tab

## 7. Monitoring and Notifications

### 7.1. Pipeline Monitoring

- **AWS CloudWatch**:
  - Pipeline execution metrics
  - Success/failure rates
  - Stage duration
- **GitHub Status Checks**:
  - PR status integration
  - Required checks for merging

### 7.2. Notifications

- **AWS SNS Integration**:
  - Notifications for pipeline states
  - Filter by environment and status
- **Slack Integration**:
  - Channel notifications
  - Direct developer alerts for failures
  - Daily deployment summary

### 7.3. Deployment Tracking

- **Deployment Metadata**:
  - Store deployment info in DynamoDB
  - Track versions, times, and approvers
  - Link to relevant commits and issues
- **Rollback History**:
  - Track rollback events
  - Document reasons and resolution

## 8. Rollback Procedures

### 8.1. Automated Rollback

Triggered by:

- Failed health checks
- Error rate threshold exceeded
- P90 latency above threshold

### 8.2. Manual Rollback

```bash
# Using ArgoCD
argocd app rollback product-service

# Using kubectl
kubectl rollout undo deployment/product-service

# Using AWS CodeDeploy
aws deploy stop-deployment \
  --deployment-id d-ABCDEF123 \
  --auto-rollback-enabled
```

## 9. Compliance and Auditing

### 9.1. Audit Trail

- **AWS CloudTrail**:
  - Track all API calls and changes
  - Retention: 90 days
- **Deployment Logs**:
  - Store in CloudWatch Logs
  - Retention: 1 year

### 9.2. Compliance Checks

- **Pipeline Gates**:
  - Security scan approval
  - Configuration validation
  - Infrastructure drift detection
- **Scheduled Audits**:
  - Monthly security review
  - Pipeline configuration review

## 10. Implementation and Onboarding

### 10.1. Pipeline Setup

1. **Infrastructure Provisioning**:

   ```bash
   cd infrastructure/terraform/cicd
   terraform init
   terraform apply -var-file=dev.tfvars
   ```

2. **Repository Setup**:

   - Add workflow files
   - Configure branch protection
   - Set up required secrets

3. **Developer Onboarding**:
   - Documentation
   - Team training session
   - Pipeline workshop

### 10.2. Rollout Plan

1. **Phase 1**: Development environment pipeline
2. **Phase 2**: Testing environment pipeline
3. **Phase 3**: Staging environment pipeline
4. **Phase 4**: Production environment pipeline

## 11. References

- [AWS CodePipeline Documentation](https://docs.aws.amazon.com/codepipeline/latest/userguide/welcome.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/en/stable/)
- [Tilt Documentation](https://docs.tilt.dev/)
- [Telepresence Documentation](https://www.telepresence.io/docs/)
- [OpenLens GitHub](https://github.com/MuhammedKalkan/OpenLens)
- [GitFlow Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
- [ADR-006-cloud-native-deployment-strategy](../../architecture/adr/ADR-006-cloud-native-deployment-strategy.md)
- [ADR-046-local-development-environment-orchestration](../../architecture/adr/ADR-046-local-development-environment-orchestration.md)
