# CI/CD Pipeline Architecture

This diagram visualizes the Continuous Integration and Continuous Deployment (CI/CD) pipeline using GitHub Actions for the e-commerce platform.

![CI/CD Pipeline Diagram](./cicd_pipeline_diagram.png)

## Pipeline Stages:

- **Source Control**: Developers push code changes to a GitHub repository.
- **GitHub Actions Workflow**: Triggered on push or pull request events.
  - **Build**: Code is compiled, and Docker images are built.
  - **Test**: Unit, integration, and end-to-end tests are executed.
  - **Security Scan**: Tools like Snyk or Trivy scan dependencies and images for vulnerabilities.
  - **Push to ECR**: Built Docker images are tagged and pushed to AWS Elastic Container Registry (ECR).
  - **Deploy**: Kubernetes manifests are applied to the target EKS environment (e.g., Development, Staging, Production) using tools like `kubectl` or Helm.
