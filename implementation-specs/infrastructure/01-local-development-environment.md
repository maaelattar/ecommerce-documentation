# Local Development Environment Setup

## 1. Introduction

This document specifies the local development environment setup for the e-commerce platform. A consistent, reproducible development environment is crucial for developer productivity and ensures that code behaves consistently across different environments. This specification builds upon [ADR-046-local-development-environment-orchestration](../../architecture/adr/ADR-046-local-development-environment-orchestration.md) and outlines the practical implementation details.

## 2. Development Tools Overview

### 2.1. Core Tools

| Tool       | Version  | Purpose                                                        |
| ---------- | -------- | -------------------------------------------------------------- |
| Docker     | 24.x+    | Container runtime for local service deployment                 |
| Kubernetes | 1.28+    | Container orchestration (via minikube, k3d, or Docker Desktop) |
| Helm       | 3.14+    | Package manager for Kubernetes resources                       |
| kubectl    | 1.28+    | Kubernetes command-line tool                                   |
| AWS CLI    | 2.15+    | Interaction with AWS services                                  |
| Node.js    | 20.x LTS | Runtime for microservices development                          |
| npm        | 10.x+    | Node.js package manager                                        |
| Git        | 2.40+    | Version control                                                |

### 2.2. Kubernetes Development Tools

#### 2.2.1. Tilt

- **Version**: 0.33.5+
- **Purpose**: Automates the build-push-deploy workflow for Kubernetes
- **Installation**:

  ```bash
  # MacOS
  brew install tilt-dev/tap/tilt

  # Linux
  curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash

  # Windows
  iex ((new-object net.webclient).DownloadString('https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.ps1'))
  ```

- **Configuration**:
  - Each service will have a `Tiltfile` defining how it should be built and deployed
  - Root level `Tiltfile` for orchestrating the entire platform

#### 2.2.2. Telepresence

- **Version**: 2.16+
- **Purpose**: Provides local development with seamless remote cluster integration
- **Installation**:

  ```bash
  # MacOS
  brew install datawire/blackbird/telepresence

  # Linux
  curl -fL https://app.getambassador.io/download/tel2/linux/amd64/latest/telepresence -o telepresence
  sudo mv telepresence /usr/local/bin/
  sudo chmod +x /usr/local/bin/telepresence

  # Windows
  curl -fL https://app.getambassador.io/download/tel2/windows/amd64/latest/telepresence.zip -o telepresence.zip
  ```

- **Configuration**:
  - Traffic interception configuration for each service
  - Volume mounting for local code changes
  - Environment variable mapping

#### 2.2.3. OpenLens (formerly K8sLens)

- **Version**: 6.5+
- **Purpose**: GUI for visualizing and managing Kubernetes clusters
- **Installation**:

  ```bash
  # MacOS
  brew install --cask openlens

  # Linux/Windows
  # Download from https://github.com/MuhammedKalkan/OpenLens/releases
  ```

- **Configuration**:
  - Cluster access configuration
  - Prometheus integration for monitoring
  - Extensions for additional functionality

## 3. Local Environment Setup

### 3.1. Local Kubernetes Cluster

We recommend using **k3d** for the local Kubernetes cluster due to its lightweight nature and fast startup time. Minikube or Docker Desktop Kubernetes are acceptable alternatives based on developer preference.

#### 3.1.1. k3d Setup

```bash
# Install k3d
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Create a cluster with port mappings for services
k3d cluster create ecommerce-local \
  --api-port 6550 \
  --port "8080:80@loadbalancer" \
  --port "8443:443@loadbalancer" \
  --agents 2 \
  --registry-create ecommerce-registry:0.0.0.0:5000
```

### 3.2. Development Namespace Setup

Each developer should create their own namespace to avoid conflicts:

```bash
kubectl create namespace dev-${USER}
kubectl config set-context --current --namespace=dev-${USER}
```

### 3.3. Service Dependencies Setup

#### 3.3.1. Database (PostgreSQL)

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgresql bitnami/postgresql \
  --set auth.postgresPassword=postgres \
  --set auth.database=ecommerce \
  --namespace dev-${USER}
```

#### 3.3.2. Message Broker (RabbitMQ)

```bash
helm install rabbitmq bitnami/rabbitmq \
  --set auth.username=admin \
  --set auth.password=admin123 \
  --namespace dev-${USER}
```

## 4. Project Setup

### 4.1. Repository Structure

```
ecommerce-platform/
├── services/
│   ├── product-service/
│   ├── inventory-service/
│   ├── order-service/
│   └── ...
├── infrastructure/
│   ├── kubernetes/
│   ├── terraform/
│   └── helm/
├── Tiltfile
└── docker-compose.yml (alternative to k8s for simple setups)
```

### 4.2. Service-level Tiltfile Example (Product Service)

```python
# Tiltfile for product-service

# Build the Docker image
docker_build(
  'ecommerce/product-service',
  '.',
  dockerfile='./Dockerfile',
  live_update=[
    sync('./src', '/app/src'),
    run('cd /app && npm install', trigger=['./package.json', './package-lock.json']),
    restart_container()
  ]
)

# Deploy to Kubernetes
k8s_yaml(helm(
  'helm',
  namespace='dev-' + local('whoami').strip(),
  values=['./helm/values-dev.yaml']
))

# Port forward the service
k8s_resource(
  'product-service',
  port_forwards='3000:3000',
  resource_deps=['postgresql', 'rabbitmq']
)
```

### 4.3. Root Tiltfile

```python
# Root Tiltfile for ecommerce platform

# Load individual service Tiltfiles
include('./services/product-service/Tiltfile')
include('./services/inventory-service/Tiltfile')
include('./services/order-service/Tiltfile')
# ... other services

# Define resource dependencies
k8s_resource('rabbitmq', labels=['infrastructure'])
k8s_resource('postgresql', labels=['infrastructure'])

# Group resources for easier management
k8s_resource_group('backend', ['product-service', 'inventory-service', 'order-service'])
k8s_resource_group('frontend', ['web-ui'])
```

## 5. Telepresence Workflow

### 5.1. Connecting to Remote Cluster

For integration testing with services running in a dev/staging cluster:

```bash
# Start a Telepresence session
telepresence connect

# Intercept a specific service
telepresence intercept product-service --port 3000:http --env-file=.env.remote
```

### 5.2. Local Development with Remote Dependencies

Example development workflow:

1. Connect to the remote cluster with Telepresence
2. Intercept the service you're working on
3. Run the service locally (outside of Kubernetes)
4. Changes made locally will be accessible through the cluster's ingress

## 6. Workflow Examples

### 6.1. New Service Development

1. Create a new directory in the `services` folder
2. Implement the service following the standard project structure
3. Create a Dockerfile and Helm chart
4. Add a Tiltfile for the service
5. Include the service in the root Tiltfile
6. Run `tilt up` to deploy the entire platform with your new service

### 6.2. Existing Service Modification

1. Navigate to the service directory
2. Make code changes
3. Tilt will automatically rebuild and redeploy the service
4. Use OpenLens to monitor the deployment and logs
5. Test the changes via port-forwarded endpoints

## 7. Troubleshooting Guide

### 7.1. Common Issues and Solutions

| Issue                            | Solution                                                           |
| -------------------------------- | ------------------------------------------------------------------ |
| Service not starting             | Check logs with `kubectl logs <pod>` or via OpenLens               |
| Database connection failure      | Verify PostgreSQL is running and credentials are correct           |
| Changes not reflecting           | Check Tilt logs for build issues                                   |
| Telepresence connectivity issues | Run `telepresence quit` and reconnect                              |
| Resource constraints             | Adjust k3d cluster resources or Docker Desktop resource allocation |

### 7.2. Logging and Debugging

- Use OpenLens to view logs and resource usage
- Enable debug mode in Tilt with `tilt up --debug`
- Access service logs through Tilt UI or with `tilt logs <service-name>`

## 8. References

- [Tilt Documentation](https://docs.tilt.dev/)
- [Telepresence Documentation](https://www.telepresence.io/docs/latest/quick-start/)
- [OpenLens GitHub](https://github.com/MuhammedKalkan/OpenLens)
- [k3d Documentation](https://k3d.io/)
- [ADR-046-local-development-environment-orchestration](../../architecture/adr/ADR-046-local-development-environment-orchestration.md)
- [ADR-003-nodejs-nestjs-for-initial-services](../../architecture/adr/ADR-003-nodejs-nestjs-for-initial-services.md)
