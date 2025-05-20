# AWS EKS Cluster Specification

## 1. Introduction

This document specifies the Amazon Elastic Kubernetes Service (EKS) infrastructure setup for the e-commerce platform's production, staging, and testing environments. It defines the cluster architecture, networking, security, and management practices in alignment with our AWS-centric architecture decisions.

## 2. Cluster Architecture

### 2.1. Cluster Configuration

| Component               | Specification                                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------- |
| EKS Version             | 1.28                                                                                                                |
| Control Plane           | AWS-managed EKS control plane                                                                                       |
| Region                  | Primary: us-east-1, DR: us-west-2                                                                                   |
| Availability Zones      | Minimum 3 AZs per region                                                                                            |
| Cluster Endpoint Access | Private with limited public access via CIDR restrictions                                                            |
| Add-ons                 | Amazon VPC CNI, CoreDNS, kube-proxy, AWS Load Balancer Controller, Cluster Autoscaler, AWS Node Termination Handler |

### 2.2. Node Groups Configuration

#### 2.2.1. Production Environment

| Node Group        | Instance Types                 | Min Nodes | Max Nodes | Purpose                                     |
| ----------------- | ------------------------------ | --------- | --------- | ------------------------------------------- |
| system-services   | c6i.large                      | 2         | 4         | System services (monitoring, ingress, etc.) |
| general-workloads | m6i.xlarge                     | 3         | 10        | Standard application workloads              |
| memory-optimized  | r6i.xlarge                     | 2         | 6         | Data-intensive workloads (caches, search)   |
| spot-workloads    | m6i.large, m5.large, m5a.large | 0         | 10        | Fault-tolerant services, batch jobs         |

#### 2.2.2. Staging Environment

| Node Group        | Instance Types        | Min Nodes | Max Nodes | Purpose               |
| ----------------- | --------------------- | --------- | --------- | --------------------- |
| system-services   | c6i.medium            | 1         | 2         | System services       |
| general-workloads | m6i.large             | 2         | 6         | Standard workloads    |
| spot-workloads    | m6i.medium, m5.medium | 0         | 4         | Non-critical services |

#### 2.2.3. Testing Environment

| Node Group         | Instance Types | Min Nodes | Max Nodes | Purpose       |
| ------------------ | -------------- | --------- | --------- | ------------- |
| combined-workloads | m6i.large      | 1         | 4         | All workloads |

### 2.3. Fargate Profiles (Serverless Compute)

| Profile Name      | Namespace/Label Selectors | Purpose                           |
| ----------------- | ------------------------- | --------------------------------- |
| utility-workloads | namespace: utility        | Jobs, cron jobs, batch processing |
| dev-environments  | namespace: dev-\*         | Development environments          |

## 3. Networking Configuration

### 3.1. VPC Setup

- **CIDR Block**: 10.0.0.0/16
- **Subnets**:
  - **Public Subnets**: 3x /24 (one per AZ)
  - **Private Subnets (for nodes)**: 3x /19 (one per AZ)
  - **Database Subnets**: 3x /24 (one per AZ)

### 3.2. Security Groups

- **EKS Cluster Security Group**:
  - Inbound: HTTPS (443) from VPC CIDR
  - Outbound: All to 0.0.0.0/0
- **Node Groups Security Group**:
  - Inbound: All from Cluster SG, All from Node Groups SG
  - Outbound: All to 0.0.0.0/0
- **Database Security Group**:
  - Inbound: DB port from Node Groups SG
  - Outbound: None

### 3.3. Network Policies

- **Default Deny**:
  - Block all ingress and egress by default
- **Namespace Isolation**:
  - Allow traffic within namespace
  - Explicit policies for cross-namespace communication
- **Service Communication**:
  - Explicit allow rules between specific services

## 4. IAM and Authorization

### 4.1. IAM Roles

- **EKS Cluster Role**:
  - Permissions: AmazonEKSClusterPolicy
- **EKS Node Role**:
  - Permissions: AmazonEKSWorkerNodePolicy, AmazonEKS_CNI_Policy, AmazonEC2ContainerRegistryReadOnly
- **Fargate Pod Execution Role**:
  - Permissions: AmazonEKSFargatePodExecutionRolePolicy

### 4.2. Kubernetes RBAC

- **Admin Role**:
  - Full cluster administration
  - Assigned to DevOps team
- **Developer Role**:
  - Create/update deployments, services, pods in designated namespaces
  - View-only access to logs, events
- **Monitoring Role**:
  - Read-only access to all resources for monitoring systems

### 4.3. AWS IAM Integration with Kubernetes RBAC

- **Authentication**: AWS IAM Authenticator for Kubernetes
- **Mapping**:
  - IAM roles mapped to Kubernetes RBAC groups
  - Example:
    ```yaml
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: aws-auth
      namespace: kube-system
    data:
      mapRoles: |
        - rolearn: arn:aws:iam::${AWS_ACCOUNT_ID}:role/EKSDevOpsAdmin
          username: devops-admin
          groups:
            - system:masters
        - rolearn: arn:aws:iam::${AWS_ACCOUNT_ID}:role/EKSDeveloper
          username: developer
          groups:
            - developers
    ```

## 5. Storage Configuration

### 5.1. Storage Classes

| Name          | Provisioner     | Parameters                | Use Case                          |
| ------------- | --------------- | ------------------------- | --------------------------------- |
| gp3 (default) | ebs.csi.aws.com | type: gp3, iopsPerGB: "3" | General purpose storage           |
| io1-high-perf | ebs.csi.aws.com | type: io1, iops: "5000"   | High-performance database storage |
| standard-efs  | efs.csi.aws.com | fileSystemId: ${EFS_ID}   | Shared read-write storage         |

### 5.2. Persistent Volume Claims Strategy

- **Service-Specific PVCs**:
  - Each stateful service defines its own PVC
  - Naming convention: `<service-name>-data`
- **Backup Policies**:
  - Use AWS Backup for EBS volumes
  - Snapshot schedule: Daily
  - Retention: 7 days

### 5.3. Ephemeral Storage

- **EmptyDir**:
  - Used for temporary storage, cache
  - Size limit: 1GB per pod
- **Memory Storage**:
  - EmptyDir with memory medium for high-performance temporary storage

## 6. Monitoring and Observability Setup

### 6.1. Monitoring Stack

- **Prometheus & Grafana**:
  - Deployment: Helm chart via `prometheus-community/kube-prometheus-stack`
  - Persistent storage: 50GB gp3 EBS for Prometheus
  - Retention: 15 days

### 6.2. Logging Solution

- **AWS OpenSearch (ELK) Integration**:
  - Components: Fluent Bit DaemonSet, OpenSearch service, OpenSearch Dashboards
  - Log forwarder: Fluent Bit to collect container logs
  - Log storage: AWS OpenSearch Service (2 m5.large.search instances)
  - Retention: 30 days

### 6.3. Distributed Tracing

- **AWS X-Ray**:
  - Deployment: AWS X-Ray daemon as DaemonSet
  - Integration: AWS Distro for OpenTelemetry (ADOT)
  - Sampling rate: 5% of requests

## 7. Service Mesh and Ingress

### 7.1. Service Mesh (Optional)

- **AWS App Mesh**:
  - Components: App Mesh Controller, Envoy proxies as sidecars
  - Features: Traffic routing, retry/timeout policies, circuit breaking

### 7.2. Ingress Configuration

- **AWS Load Balancer Controller**:
  - Deployment: Helm chart
  - Annotations for NLB/ALB configuration
- **Application Load Balancer (ALB)**:
  - SSL termination
  - WAF integration
  - Path-based routing

### 7.3. Example Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ecommerce-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: ${ACM_CERT_ARN}
    alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS-1-2-2017-01
spec:
  rules:
    - host: api.ecommerce-example.com
      http:
        paths:
          - path: /products
            pathType: Prefix
            backend:
              service:
                name: product-service
                port:
                  number: 80
          - path: /orders
            pathType: Prefix
            backend:
              service:
                name: order-service
                port:
                  number: 80
```

## 8. Security Measures

### 8.1. Pod Security Standards

- **Baseline Policy**:
  - Restrict host namespace sharing
  - Prevent privileged containers
  - Restrict volume types

### 8.2. Network Security

- **Network Policies**:
  - Default deny all ingress/egress
  - Explicit allow rules for required communication
- **AWS Security Groups**:
  - Restrict traffic between node groups and external services

### 8.3. Secret Management

- **AWS Secrets Manager Integration**:
  - External Secrets Operator for Kubernetes
  - Secret rotation policies (30-day rotation)

### 8.4. Image Security

- **ECR Image Scanning**:
  - Automatic scanning on push
  - Block deployments of images with high severity vulnerabilities
- **Image Pull Policies**:
  - Always pull from private ECR
  - Image tag immutability enabled

## 9. Resource Management

### 9.1. Resource Quotas

- **Namespace Limits**:
  - CPU, memory, pods, services, etc., per namespace
  - Example:
    ```yaml
    apiVersion: v1
    kind: ResourceQuota
    metadata:
      name: compute-resources
      namespace: production
    spec:
      hard:
        requests.cpu: "20"
        requests.memory: 40Gi
        limits.cpu: "40"
        limits.memory: 80Gi
        pods: "100"
    ```

### 9.2. Limit Ranges

- **Default Container Limits**:
  - Default CPU and memory requests/limits
  - Example:
    ```yaml
    apiVersion: v1
    kind: LimitRange
    metadata:
      name: default-limits
      namespace: production
    spec:
      limits:
        - default:
            cpu: "500m"
            memory: "512Mi"
          defaultRequest:
            cpu: "100m"
            memory: "256Mi"
          type: Container
    ```

### 9.3. Horizontal Pod Autoscaler

- **Autoscaling Configuration**:
  - Based on CPU utilization (target 70%)
  - Custom metrics from Prometheus
  - Min/Max pods specified per deployment

## 10. Disaster Recovery

### 10.1. Backup Strategy

- **Velero for Kubernetes Resources**:
  - Schedule: Daily
  - Retention: 30 days
  - Storage: S3 bucket in DR region
- **Persistent Volume Backups**:
  - EBS snapshots via AWS Backup
  - Cross-region replication

### 10.2. Multi-Region Strategy

- **Active-Passive Setup**:
  - Primary region: us-east-1
  - DR region: us-west-2
  - Route 53 failover routing

### 10.3. Recovery Time Objective (RTO)

- **Target RTO**: < 4 hours
- **Recovery Plan**:
  - Documented failover procedures
  - Regular DR drills (quarterly)

## 11. Cost Optimization

### 11.1. Right-sizing

- **Node Optimization**:
  - Regular analysis of resource usage
  - Adjust requests/limits based on actual usage
- **Spot Instances**:
  - Use for stateless, fault-tolerant services
  - Diversify instance types for availability

### 11.2. Autoscaling

- **Cluster Autoscaler**:
  - Scale down delay: 10 minutes
  - Scale down utilization threshold: 50%
- **Scheduled Scaling**:
  - Reduce capacity during off-hours for non-production environments

### 11.3. Cost Allocation

- **Tagging Strategy**:
  - Environment: prod, staging, testing
  - Department: engineering, marketing, etc.
  - Application: product-service, order-service, etc.
  - Cost center: finance tag for billing

## 12. Implementation Plan

### 12.1. Terraform Modules

- **VPC Module**:
  - Creates VPC, subnets, route tables, etc.
- **EKS Module**:
  - Creates EKS cluster, node groups, etc.
- **Security Module**:
  - Creates IAM roles, security groups, etc.

### 12.2. Deployment Sequence

1. Infrastructure provisioning (Terraform)
2. Cluster configuration (kubectl, Helm)
3. Core services deployment (monitoring, logging, etc.)
4. Application deployment (CI/CD pipeline)

### 12.3. Example Terraform Configuration

```hcl
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"

  name = "eks-vpc"
  cidr = "10.0.0.0/16"

  azs = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.0.0/19", "10.0.32.0/19", "10.0.64.0/19"]
  public_subnets = ["10.0.96.0/24", "10.0.97.0/24", "10.0.98.0/24"]
  database_subnets = ["10.0.99.0/24", "10.0.100.0/24", "10.0.101.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false

  tags = {
    Environment = "production"
    Application = "ecommerce"
  }
}

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 18.0"

  cluster_name = "ecommerce-production"
  cluster_version = "1.28"

  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_private_access = true
  cluster_endpoint_public_access = true
  cluster_endpoint_public_access_cidrs = ["11.22.33.44/32"] # Admin IPs

  node_security_group_additional_rules = {
    ingress_self_all = {
      description = "Node to node all ports/protocols"
      protocol = "-1"
      from_port = 0
      to_port = 0
      type = "ingress"
      self = true
    }
  }

  eks_managed_node_groups = {
    system_services = {
      name = "system-services"
      instance_types = ["c6i.large"]
      min_size = 2
      max_size = 4
      desired_size = 2

      labels = {
        role = "system"
      }

      taints = [{
        key = "dedicated"
        value = "system"
        effect = "NO_SCHEDULE"
      }]
    }

    general_workloads = {
      name = "general-workloads"
      instance_types = ["m6i.xlarge"]
      min_size = 3
      max_size = 10
      desired_size = 3

      labels = {
        role = "application"
      }
    }
  }

  tags = {
    Environment = "production"
    Application = "ecommerce"
  }
}
```

## 13. References

- [Amazon EKS Documentation](https://docs.aws.amazon.com/eks/)
- [EKS Workshop](https://www.eksworkshop.com/)
- [Terraform AWS EKS Module](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [ADR-006-cloud-native-deployment-strategy](../../architecture/adr/ADR-006-cloud-native-deployment-strategy.md)
