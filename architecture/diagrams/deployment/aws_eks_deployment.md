# AWS EKS Deployment Architecture

This diagram illustrates the deployment architecture of the e-commerce platform on AWS Elastic Kubernetes Service (EKS).

![AWS EKS Deployment Diagram](./aws_eks_deployment_diagram.png)

## Key Components:

- **VPC**: Configured with public and private subnets across multiple Availability Zones (AZs).
- **Application Load Balancer (ALB)**: Distributes incoming traffic across microservices in the private subnets.
- **NAT Gateway**: Allows instances in private subnets to access the internet (e.g., for pulling images, updates).
- **EKS Cluster**: Hosts the microservices (User, Product, Order) as Kubernetes Deployments and Services.
- **Managed Databases**: RDS PostgreSQL for relational data and ElastiCache Redis for caching.
- **Messaging Queue**: RabbitMQ for asynchronous communication between services.
- **Observability**: Prometheus for metrics, Grafana for visualization, Jaeger for tracing, and FluentBit for logging.
- **CI/CD**: Integrated with GitHub Actions for automated builds and deployments, using ECR for container image storage.
- **Security**: AWS Secrets Manager used for managing sensitive credentials.
