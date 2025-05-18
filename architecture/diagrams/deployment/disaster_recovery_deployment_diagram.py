from diagrams import Diagram, Cluster, Edge, Node
from diagrams.aws.compute import EKS, EC2, Lambda
from diagrams.aws.network import ELB, VPC, Route53, CloudFront, DirectConnect
from diagrams.aws.database import RDS, ElastiCache, Aurora, Database
from diagrams.aws.storage import S3
from diagrams.aws.management import CloudwatchEventEventBased, Cloudwatch, AutoScaling
from diagrams.aws.integration import SQS, SNS, MQ
from diagrams.aws.security import WAF, SecretsManager
from diagrams.aws.general import General
from diagrams.k8s.compute import Deployment
from diagrams.k8s.network import Service
from diagrams.onprem.client import Client, Users
from diagrams.onprem.network import Internet

# Graph attributes
graph_attr = {
    "fontsize": "45",
    "bgcolor": "transparent"
}

with Diagram("Disaster Recovery Deployment - E-commerce Platform", show=False, direction="TB", 
             outformat="jpg", filename="disaster_recovery_deployment_diagram", graph_attr=graph_attr):
    
    # Users and Internet
    users = Users("Global Users")
    internet = Internet("Internet")
    
    # Global Resources
    with Cluster("Global AWS Resources"):
        dns = Route53("Route53 with Health Checks")
        cdn = CloudFront("CloudFront CDN")
        static_content = S3("S3 - Static Content")
        waf = WAF("WAF")
        
    # Primary Region
    with Cluster("Primary Region (us-east-1)"):
        with Cluster("Primary Infrastructure"):
            # Network components
            primary_vpc = VPC("Primary VPC")
            primary_alb = ELB("Primary ALB")
            
            # Kubernetes
            with Cluster("Primary EKS Cluster"):
                primary_eks = EKS("Primary EKS")
                
                with Cluster("Primary Microservices"):
                    primary_services = [
                        Deployment("User Service (Active)"),
                        Deployment("Order Service (Active)"),
                        Deployment("Product Service (Active)"),
                        Deployment("Payment Service (Active)")
                    ]
                    
                    primary_service_mesh = Service("Service Mesh")
                    
                    for svc in primary_services:
                        svc >> primary_service_mesh
            
            # Data Infrastructure
            with Cluster("Primary Data Storage"):
                primary_db = Aurora("Aurora Primary Cluster")
                primary_db_replica = Aurora("Aurora Read Replica")
                primary_cache = ElastiCache("ElastiCache (Redis Cluster)")
                primary_rabbit = MQ("RabbitMQ - Primary")
                
                primary_db >> Edge(label="sync replication") >> primary_db_replica
                
            # Monitoring
            primary_monitor = Cloudwatch("CloudWatch Primary")
            primary_scaling = AutoScaling("AutoScaling")
            
    # Secondary/DR Region
    with Cluster("DR Region (us-west-2)"):
        with Cluster("DR Infrastructure"):
            # Network components
            dr_vpc = VPC("DR VPC")
            dr_alb = ELB("DR ALB (Standby)")
            
            # Kubernetes
            with Cluster("DR EKS Cluster"):
                dr_eks = EKS("DR EKS")
                
                with Cluster("DR Microservices"):
                    dr_services = [
                        Deployment("User Service (Standby)"),
                        Deployment("Order Service (Standby)"),
                        Deployment("Product Service (Standby)"),
                        Deployment("Payment Service (Standby)")
                    ]
                    
                    dr_service_mesh = Service("Service Mesh")
                    
                    for svc in dr_services:
                        svc >> dr_service_mesh
            
            # Data Infrastructure
            with Cluster("DR Data Storage"):
                dr_db = Aurora("Aurora DR Cluster")
                dr_cache = ElastiCache("ElastiCache (Redis Cluster)")
                dr_rabbit = MQ("RabbitMQ - DR")
                
            # Monitoring
            dr_monitor = Cloudwatch("CloudWatch DR")
            dr_scaling = AutoScaling("AutoScaling")
    
    # Cross-Region Components
    with Cluster("Cross-Region Resources"):
        # Cross-region replication
        s3_backup = S3("Cross-Region Backup Bucket")
        events = SNS("SNS for Cross-Region Events")
        
        # Health check and failover mechanisms
        failover = Route53("R53 Failover")
        
        # Replication connections
        db_replication = Edge(label="async replication", style="dashed", color="blue")
        primary_db >> db_replication >> dr_db
        
        # Message queue replication
        primary_rabbit >> Edge(label="mirror queue", style="dashed", color="orange") >> dr_rabbit
        
        # Backup flow
        primary_db >> Edge(label="backup", style="dotted") >> s3_backup
        s3_backup >> Edge(label="restore if needed", style="dotted") >> dr_db
    
    # User Flow and Failover Mechanism
    users >> internet
    internet >> dns
    
    dns >> cdn
    cdn >> static_content
    
    # Normal operations flow
    dns >> Edge(color="green", label="active") >> waf >> primary_alb >> primary_eks
    dns >> Edge(color="red", style="dashed", label="standby") >> dr_alb
    
    # Monitoring and event flow
    primary_monitor >> events
    dr_monitor >> events
    events >> failover
    
    # Failover mechanism
    failover >> Edge(color="red", style="bold", label="failover trigger") >> dns
    
    # Health checks
    primary_monitor >> Edge(style="dotted", label="health check") >> primary_services[0]
    dr_monitor >> Edge(style="dotted", label="health check") >> dr_services[0]
