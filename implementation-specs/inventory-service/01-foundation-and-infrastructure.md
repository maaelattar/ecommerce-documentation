# Phase 1: Foundation and Infrastructure

## Overview

The Foundation and Infrastructure phase establishes the technical foundation for the Inventory Service. This phase focuses on setting up the development environment, creating the project structure, and configuring the necessary tools and pipelines for efficient development and deployment.

**Duration**: Weeks 1-2

## Tasks and Implementation Details

### 1. Repository Setup

#### 1.1 Create GitHub Repository
- Create repository named `inventory-service` in the organization GitHub account
- Set appropriate visibility (private)
- Configure README with service overview and setup instructions
- Add `.gitignore` for Node.js/TypeScript projects

#### 1.2 Branch Protection
- Configure branch protection rules for `main` branch:
  - Require pull request reviews before merging
  - Require status checks to pass before merging
  - Restrict who can push to matching branches
  - Require linear history

#### 1.3 Issue and PR Templates
- Create issue templates for:
  - Feature requests
  - Bug reports
  - Technical debt/refactoring
- Create PR template with:
  - Description field
  - Related issue field
  - Testing checklist
  - Documentation checklist
  - Quality requirements

### 2. Project Scaffolding

#### 2.1 Initialize Project
```bash
# Initialize project
mkdir inventory-service
cd inventory-service
npm init -y

# Install TypeScript
npm install typescript @types/node ts-node --save-dev

# Initialize TypeScript configuration
npx tsc --init

# Install Express and required types
npm install express
npm install @types/express --save-dev
```

#### 2.2 Configure Code Quality Tools
```bash
# Install ESLint and Prettier
npm install eslint prettier eslint-config-prettier eslint-plugin-prettier --save-dev

# Install Husky for pre-commit hooks
npm install husky lint-staged --save-dev
```

Create configuration files:
- `.eslintrc.js`
- `.prettierrc`
- `husky.config.js`

#### 2.3 Testing Framework Setup
```bash
# Install Jest for testing
npm install jest ts-jest @types/jest --save-dev

# Create Jest configuration
npx ts-jest config:init
```

#### 2.4 Project Structure
Create the following folder structure:
```
/src
  /domain
    /entities         # Domain entities
    /events           # Domain events
    /valueObjects     # Value objects
    /repositories     # Repository interfaces
  /application
    /services         # Application services
    /commands         # Command handlers
    /queries          # Query handlers
    /dtos             # Data transfer objects
  /infrastructure
    /database         # Database implementations
    /messaging        # Message broker implementations
    /repositories     # Repository implementations
    /external         # External service clients
  /interfaces
    /api              # REST API controllers
    /events           # Event handlers
    /jobs             # Scheduled jobs
  /config             # Application configuration
  /utils              # Utility functions
/test
  /unit               # Unit tests
  /integration        # Integration tests
  /e2e                # End-to-end tests
/scripts              # Build and deployment scripts
/docs                 # Documentation
```

### 3. CI/CD Pipeline Configuration

#### 3.1 GitHub Actions Workflow
Create `.github/workflows/ci.yml`:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Use Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18.x'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build
      
  deploy-dev:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Development
        run: ./scripts/deploy.sh development
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          
  deploy-prod:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Production
        run: ./scripts/deploy.sh production
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

#### 3.2 Environment Configuration
- Create `config` directory with environment-specific configuration files:
  - `default.ts`
  - `development.ts`
  - `test.ts`
  - `production.ts`

- Implement configuration management using `config` npm package:
```bash
npm install config @types/config --save
```

#### 3.3 Secrets Management
- Configure GitHub repository secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `DATABASE_URL`
  - `RABBITMQ_URL`
  - `JWT_SECRET`

### 4. Development Environment Setup

#### 4.1 Docker Compose Configuration
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  # PostgreSQL database
  postgres:
    image: postgres:14-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: inventory_user
      POSTGRES_PASSWORD: inventory_password
      POSTGRES_DB: inventory_service
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # DynamoDB Local
  dynamodb-local:
    image: amazon/dynamodb-local:latest
    ports:
      - "8000:8000"
    command: "-jar DynamoDBLocal.jar -sharedDb -dbPath /home/dynamodblocal/data"
    volumes:
      - dynamodb_data:/home/dynamodblocal/data

  # RabbitMQ
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: inventory_user
      RABBITMQ_DEFAULT_PASS: inventory_password

  # Redis for caching
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  dynamodb_data:
```

#### 4.2 Local Development Configuration
- Create npm scripts in `package.json`:
```json
"scripts": {
  "start": "ts-node src/index.ts",
  "dev": "nodemon --watch src --ext ts --exec ts-node src/index.ts",
  "build": "tsc",
  "lint": "eslint . --ext .ts",
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage",
  "docker:up": "docker-compose up -d",
  "docker:down": "docker-compose down"
}
```

- Install nodemon for hot-reloading:
```bash
npm install nodemon --save-dev
```

#### 4.3 Database Initialization and Seeding
- Create database migration scripts using TypeORM:
```bash
npm install typeorm pg --save
```

- Create seed data scripts in `scripts/seed.ts`

#### 4.4 Documentation Setup
- Set up Swagger for API documentation:
```bash
npm install swagger-ui-express @types/swagger-ui-express --save
```

## Deliverables

1. Fully configured GitHub repository with appropriate protections and templates
2. Initialized TypeScript project with proper folder structure
3. Configured code quality tools (ESLint, Prettier, Husky)
4. Set up testing framework with sample tests
5. Implemented CI/CD pipeline with GitHub Actions
6. Environment-specific configuration
7. Development environment with Docker Compose
8. Database migration and seed scripts
9. Hot-reloading development server
10. Initial API documentation setup

## Definition of Done

- Repository is created and accessible to the team
- All code quality tools are operational
- CI pipeline successfully runs on PR creation
- Local development environment can be started with a single command
- Database migrations run successfully
- Sample API endpoint is documented and testable
- Development team can clone and run the project without manual configuration