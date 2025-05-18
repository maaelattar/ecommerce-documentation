from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EKS, EC2
from diagrams.aws.network import ELB, VPC, PrivateSubnet, PublicSubnet, InternetGateway, NATGateway
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.storage import S3
from diagrams.aws.security import IAM, SecretsManager
from diagrams.k8s.compute import Deployment, Pod, StatefulSet
from diagrams.k8s.network import Service
from diagrams.k8s.storage import PV
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.tracing import Jaeger
from diagrams.onprem.logging import FluentBit
from diagrams.onprem.queue import RabbitMQ
from diagrams.onprem.ci import GithubActions
from diagrams.programming.language import Nodejs
from diagrams.onprem.client import Client, User

# Graph attributes
graph_attr = {
    "fontsize": "45",
    "bgcolor": "transparent"
}

with Diagram("Multi-Environment Deployment - E-commerce Platform", show=False, direction="TB", 
             outformat="jpg", filename="multi_environment_deployment_diagram", graph_attr=graph_attr):
    
    # External Users
    developers = User("Developers")
    qa_team = User("QA Team")
    business = User("Business Users")
    customers = Client("Customers")
    
    # Common CI/CD Pipeline
    with Cluster("CI/CD Pipeline"):
        cicd = GithubActions("GitHub Actions")
    
    # Development Environment
    with Cluster("Development Environment"):
        with Cluster("AWS Dev Account"):
            dev_vpc = VPC("Dev VPC")
            
            with Cluster("Dev EKS Cluster (Small)"):
                dev_eks = EKS("Dev EKS")
                
                with Cluster("Dev Namespace: Core"):
                    # Smaller replicas, resource limits
                    dev_user_svc = Deployment("User Service (1 replica)")
                    dev_order_svc = Deployment("Order Service (1 replica)")
                    dev_product_svc = Deployment("Product Service (1 replica)")
                
                with Cluster("Dev Namespace: Infrastructure"):
                    dev_rabbitmq = StatefulSet("RabbitMQ (1 node)")
                    dev_monitoring = Prometheus("Prometheus (minimal)")
                
            # Dev Databases
            dev_dbs = RDS("Shared Dev DB (Small)")
            dev_cache = ElastiCache("Dev Cache (t3.small)")
            
            # Dev Load Balancer
            dev_elb = ELB("Dev Internal ALB")
    
    # Staging Environment
    with Cluster("Staging Environment"):
        with Cluster("AWS Staging Account"):
            stage_vpc = VPC("Staging VPC")
            
            with Cluster("Staging EKS Cluster (Medium)"):
                stage_eks = EKS("Staging EKS")
                
                with Cluster("Staging Namespace: Core"):
                    # Mid-sized deployment
                    stage_user_svc = Deployment("User Service (2 replicas)")
                    stage_order_svc = Deployment("Order Service (2 replicas)")
                    stage_product_svc = Deployment("Product Service (2 replicas)")
                
                with Cluster("Staging Namespace: Infrastructure"):
                    stage_rabbitmq = StatefulSet("RabbitMQ (3 nodes)")
                    stage_monitoring = Prometheus("Full Monitoring Stack")
                    stage_tracing = Jaeger("Jaeger Tracing")
                
            # Staging Databases (Closer to prod)
            stage_dbs = RDS("Staging DB (Medium)")
            stage_cache = ElastiCache("Staging Cache (m5.large)")
            
            # Staging Load Balancer
            stage_elb = ELB("Staging ALB")
    
    # Production Environment
    with Cluster("Production Environment"):
        with Cluster("AWS Production Account"):
            prod_vpc = VPC("Production VPC")
            
            with Cluster("Production EKS Cluster (Large)"):
                prod_eks = EKS("Production EKS")
                
                with Cluster("Production Namespace: Core"):
                    # Production-sized deployment with HPA
                    prod_user_svc = Deployment("User Service (3+ replicas, HPA)")
                    prod_order_svc = Deployment("Order Service (3+ replicas, HPA)")
                    prod_product_svc = Deployment("Product Service (3+ replicas, HPA)")
                
                with Cluster("Production Namespace: Infrastructure"):
                    prod_rabbitmq = StatefulSet("RabbitMQ (3+ nodes)")
                    prod_monitoring = Prometheus("Full Monitoring + Alerting")
                    prod_tracing = Jaeger("Distributed Tracing")
                    prod_logging = FluentBit("Centralized Logging")
                
            # Production Databases
            prod_dbs = RDS("Production DB Cluster (m5.xlarge)")
            prod_cache = ElastiCache("Production Cache Cluster")
            
            # Production Load Balancer with WAF
            prod_elb = ELB("Production ALB with WAF")
            
            # Backup and Compliance
            prod_backup = S3("Backup Bucket")
            prod_secrets = SecretsManager("Enhanced Secrets")
    
    # Environment Connections and Access Rights
    developers >> dev_elb
    developers >> stage_elb
    
    qa_team >> stage_elb
    business >> stage_elb
    
    customers >> prod_elb
    
    # CI/CD Deployment Flow
    cicd >> Edge(color="blue", label="continuous deployment") >> dev_eks
    cicd >> Edge(color="green", label="on approved PR") >> stage_eks
    cicd >> Edge(color="red", label="manual release") >> prod_eks
    
    # Environment Data Flow
    dev_user_svc >> dev_dbs
    dev_user_svc >> dev_cache
    dev_order_svc >> dev_rabbitmq
    
    stage_user_svc >> stage_dbs
    stage_user_svc >> stage_cache
    stage_order_svc >> stage_rabbitmq
    
    prod_user_svc >> prod_dbs
    prod_user_svc >> prod_cache
    prod_order_svc >> prod_rabbitmq
    prod_dbs >> prod_backup
    
    # Environment Isolation
    dev_vpc - Edge(style="dotted", color="red", label="isolated") - stage_vpc
    stage_vpc - Edge(style="dotted", color="red", label="isolated") - prod_vpc
