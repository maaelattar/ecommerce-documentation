from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EKS, EC2, ECR
from diagrams.aws.network import ELB, VPC, PrivateSubnet, PublicSubnet, InternetGateway, NATGateway
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.storage import S3, EFS
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import IAM
from diagrams.aws.devtools import Codebuild, Codecommit, Codedeploy, Codepipeline
from diagrams.k8s.clusterconfig import HPA
from diagrams.k8s.compute import Deployment, Pod, ReplicaSet, StatefulSet
from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.storage import PV, PVC, StorageClass
from diagrams.k8s.controlplane import APIServer, Scheduler, ControllerManager
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.tracing import Jaeger
from diagrams.onprem.logging import FluentBit
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import RabbitMQ, Kafka
from diagrams.onprem.ci import Jenkins, GitlabCI, GithubActions
from diagrams.onprem.vcs import Git, Github
# NestJS not available in diagrams library
from diagrams.programming.language import Nodejs
from diagrams.generic.compute import Rack
from diagrams.generic.device import Mobile, Tablet
from diagrams.generic.network import Switch
from diagrams.generic.os import Android, IOS
from diagrams.generic.place import Datacenter
from diagrams.generic.storage import Storage
from diagrams.onprem.client import User

with Diagram("AWS EKS Deployment - E-commerce Platform", show=False, direction="TB", outformat="jpg", filename="aws_eks_deployment_diagram") as diag:
    user = User("End User (Web/Mobile)")

    with Cluster("AWS Cloud"):
        with Cluster("Region (e.g., us-east-1)"):
            ecr = ECR("Elastic Container Registry")
            s3_config_backups = S3("Config/Backups")

            github_actions = GithubActions("GitHub Actions CI/CD")

            with Cluster("VPC"):
                igw = InternetGateway("Internet Gateway")
                nat_gw = NATGateway("NAT Gateway")

                with Cluster("Public Subnets"):
                    alb = ELB("Application Load Balancer")

                with Cluster("Private Subnets"):
                    with Cluster("EKS Cluster (Managed Kubernetes)"):
                        eks_control_plane = EKS("EKS Control Plane")
                        
                        with Cluster("Kubernetes Worker Nodes (EC2 Instances)"):
                            nodes_group = Cluster("Nodes Group", graph_attr={"bgcolor": "transparent"})
                            with nodes_group:
                                nodes = [
                                    EC2("Worker Node 1"),
                                    EC2("Worker Node 2"),
                                    EC2("Worker Node 3")
                                ]

                            with Cluster("Observability Stack"):
                                prometheus = Prometheus("Prometheus")
                                grafana = Grafana("Grafana")
                                alertmanager = Prometheus("Alertmanager") # Using Prometheus icon for Alertmanager
                                jaeger_collector = Jaeger("Jaeger Collector")
                                jaeger_query = Jaeger("Jaeger Query")
                                fluentd_ds = Deployment("FluentBit DaemonSet") # Represent as a DaemonSet
                                
                                for node_instance in nodes:
                                    node_instance >> Edge(style="dotted", label="logs") >> fluentd_ds
                                
                                eks_control_plane >> Edge(color="grey", style="dashed") >> [prometheus, grafana, jaeger_query]

                            with Cluster("Core Services Namespace"):
                                # User Service
                                with Cluster("User Service"):
                                    user_svc_deploy = Deployment("Deployment")
                                    user_svc_pods = [Pod("Pod 1"), Pod("Pod 2")]
                                    user_svc_service = Service("Service (ClusterIP)")
                                    user_svc_hpa = HPA("HPA")
                                    user_svc_deploy >> user_svc_pods
                                    user_svc_service >> user_svc_deploy 
                                    user_svc_deploy >> user_svc_hpa
                                    for pod_instance in user_svc_pods:
                                        with Cluster(pod_instance.label, graph_attr={"bgcolor": "transparent", "style": "dotted", "labeljust": "l", "labelloc": "b"}):
                                            nestjs_app = Nodejs("NestJS App")
                                            pod_instance - nestjs_app

                                # Product Service
                                with Cluster("Product Service"):
                                    product_svc_deploy = Deployment("Deployment")
                                    product_svc_pods = [Pod("Pod 1"), Pod("Pod 2")]
                                    product_svc_service = Service("Service (ClusterIP)")
                                    product_svc_hpa = HPA("HPA")
                                    product_svc_deploy >> product_svc_pods
                                    product_svc_service >> product_svc_deploy
                                    product_svc_deploy >> product_svc_hpa
                                    for pod_instance in product_svc_pods:
                                        with Cluster(pod_instance.label, graph_attr={"bgcolor": "transparent", "style": "dotted", "labeljust": "l", "labelloc": "b"}):
                                            nestjs_app = Nodejs("NestJS App")
                                            pod_instance - nestjs_app

                                # Order Service
                                with Cluster("Order Service"):
                                    order_svc_deploy = Deployment("Deployment")
                                    order_svc_pods = [Pod("Pod 1"), Pod("Pod 2")]
                                    order_svc_service = Service("Service (ClusterIP)")
                                    order_svc_hpa = HPA("HPA")
                                    order_svc_deploy >> order_svc_pods
                                    order_svc_service >> order_svc_deploy # Connection for order service
                                    order_svc_deploy >> order_svc_hpa
                                    for pod_instance in order_svc_pods:
                                        with Cluster(pod_instance.label, graph_attr={"bgcolor": "transparent", "style": "dotted", "labeljust": "l", "labelloc": "b"}):
                                            nestjs_app = Nodejs("NestJS App")
                                            pod_instance - nestjs_app

                            with Cluster("Messaging Namespace"):
                                with Cluster("RabbitMQ Cluster"):
                                    rabbitmq_sts = StatefulSet("StatefulSet")
                                    rabbitmq_pods = [Pod("Pod 1"), Pod("Pod 2")]
                                    rabbitmq_service = Service("Service (Headless)")
                                    rabbitmq_sts >> rabbitmq_pods
                                    rabbitmq_service >> rabbitmq_sts

                            with Cluster("Kubernetes System & Config"):
                                kube_api = APIServer("Kube API Server (Control Plane)") # Part of EKS managed plane
                                config_maps = StorageClass("ConfigMaps")
                                secrets = StorageClass("Sealed Secrets")
                                eks_control_plane - kube_api
                                
                    # Databases outside EKS but in private subnets
                    with Cluster("Databases (Managed AWS Services)"):
                        user_db = RDS("User DB (Postgres)")
                        product_db = RDS("Product DB (Postgres)")
                        order_db = RDS("Order DB (Postgres)")
                        cache_redis = ElastiCache("Cache (Redis)")

                    # Network Flow
                    user >> alb >> [user_svc_service, product_svc_service, order_svc_service]
                    igw >> alb
                    
                    for node_instance in nodes:
                        nat_gw << Edge(label="egress") << node_instance

                    # Service Dependencies
                    user_svc_deploy >> Edge(label="reads/writes") >> user_db
                    user_svc_deploy >> Edge(label="reads/writes") >> cache_redis
                    product_svc_deploy >> Edge(label="reads/writes") >> product_db
                    order_svc_deploy >> Edge(label="reads/writes") >> order_db

                    order_svc_deploy >> Edge(label="K8s DNS", style="dashed") >> user_svc_service
                    order_svc_deploy >> Edge(label="K8s DNS", style="dashed") >> product_svc_service
                    
                    for svc_deploy in [user_svc_deploy, product_svc_deploy, order_svc_deploy]:
                        svc_deploy >> Edge(label="AMQP", style="dashed") >> rabbitmq_service
                        svc_deploy >> Edge(color="darkgreen", style="dashed", label="metrics") >> prometheus
                        svc_deploy >> Edge(color="blue", style="dashed", label="traces") >> jaeger_collector
                        svc_deploy >> Edge(color="orange", style="dotted", label="uses") >> config_maps
                        svc_deploy >> Edge(color="red", style="dotted", label="uses") >> secrets

    # CI/CD Flow
    github_actions >> Edge(label="docker push") >> ecr
    github_actions >> Edge(label="kubectl apply/helm upgrade") >> eks_control_plane
    
    for node_instance in nodes:
        ecr >> Edge(label="docker pull") >> node_instance

diag
