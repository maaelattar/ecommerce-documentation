from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.vcs import Github, Git
from diagrams.aws.devtools import Codebuild, Codepipeline
from diagrams.aws.management import CloudwatchEventEventBased, SystemsManagerParameterStore
from diagrams.aws.compute import ECR
from diagrams.aws.storage import S3
from diagrams.aws.security import IAM, SecretsManager
from diagrams.k8s.compute import Deployment
from diagrams.k8s.ecosystem import Helm
from diagrams.onprem.container import Docker
from diagrams.programming.language import Nodejs
from diagrams.onprem.client import User, Client
from diagrams.onprem.network import Internet
from diagrams.aws.compute import EKS

graph_attr = {
    "fontsize": "45",
    "bgcolor": "transparent"
}

with Diagram("CI/CD Pipeline - E-commerce Platform", show=False, direction="LR", outformat="jpg", filename="cicd_pipeline_diagram", graph_attr=graph_attr):
    # Developers and source code
    developer = User("Developer")
    
    with Cluster("Source Code Management"):
        repo = Github("GitHub Repository")
        pr = Github("Pull Request")
        code = Git("Feature Branch")
        main = Git("Main Branch")
        
        developer >> code
        code >> pr
        pr >> main
        main >> repo
    
    # CI/CD Pipeline
    with Cluster("CI/CD Pipeline (GitHub Actions)"):
        with Cluster("Continuous Integration"):
            ci_workflow = GithubActions("CI Workflow")
            
            with Cluster("Build & Test"):
                unit_tests = GithubActions("Unit Tests")
                integration_tests = GithubActions("Integration Tests")
                static_analysis = GithubActions("Static Analysis")
                linter = GithubActions("Linter")
                build = Docker("Build Container")
            
            with Cluster("Security Checks"):
                sast = GithubActions("SAST Scan")
                dependency_check = GithubActions("Dependency Scan")
                secrets_scan = GithubActions("Secrets Scan")
                
            # CI Flow
            ci_workflow >> unit_tests
            ci_workflow >> integration_tests
            ci_workflow >> static_analysis
            ci_workflow >> linter
            ci_workflow >> build
            ci_workflow >> dependency_check
            ci_workflow >> sast
            ci_workflow >> secrets_scan
        
        with Cluster("Continuous Delivery"):
            cd_workflow = GithubActions("CD Workflow")
            
            with Cluster("Artifact Creation & Storage"):
                ecr = ECR("Container Registry")
                version = GithubActions("Semantic Versioning")
                
            with Cluster("Deployment"):
                helm = Helm("Helm Charts")
                deploy_dev = GithubActions("Deploy to Dev")
                deploy_stage = GithubActions("Deploy to Staging")
                deploy_prod = GithubActions("Deploy to Production")
                
            # CD Flow
            cd_workflow >> version
            build >> ecr
            cd_workflow >> helm
            cd_workflow >> deploy_dev
            deploy_dev >> deploy_stage
            deploy_stage >> deploy_prod
    
    # Environments
    with Cluster("Kubernetes Environments"):
        dev = EKS("Development")
        staging = EKS("Staging")
        prod = EKS("Production")
        
        deploy_dev >> dev
        deploy_stage >> staging
        deploy_prod >> prod
    
    # Triggers and Connections
    pr >> Edge(color="green", style="dashed", label="triggers") >> ci_workflow
    main >> Edge(color="blue", style="dashed", label="triggers") >> cd_workflow
    
    # Approval Flow
    approver = Client("Release Manager")
    approver >> Edge(color="red", label="approves") >> deploy_prod
