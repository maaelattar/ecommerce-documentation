# Environment Setup

## 🎯 Objective

Set up development tools for the ecommerce platform infrastructure.

## 📋 Required Tools

- **Docker 24.x+** - Container runtime
- **AWS CLI 2.15+** - AWS service interaction  
- **Node.js 20.x LTS** - Runtime for CDK
- **pnpm 8.x+** - Package manager
- **AWS CDK 2.x** - Infrastructure as Code
- **LocalStack CLI** - Local AWS simulation

## 🔧 Quick Installation

### macOS
```bash
brew install docker awscli node pnpm
brew install localstack/tap/localstack-cli
pnpm install -g aws-cdk aws-cdk-local
```

### Linux
```bash
# Install Docker & Node.js
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc && nvm install --lts

# Install tools
npm install -g pnpm aws-cdk aws-cdk-local
pip install localstack[core]
```

### Windows
1. Install Docker Desktop + Node.js LTS
2. Run: `npm install -g pnpm aws-cdk aws-cdk-local`
3. Install AWS CLI from AWS docs

## ✅ Verify
```bash
docker --version && aws --version && cdk --version
```

Continue to **[02-localstack-setup.md](./02-localstack-setup.md)**