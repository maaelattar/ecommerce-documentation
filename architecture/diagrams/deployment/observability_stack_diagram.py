from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.logging import Loki, FluentBit
from diagrams.onprem.tracing import Jaeger, Tempo
# Analytics components not needed for this diagram
from diagrams.aws.management import Cloudwatch
from diagrams.k8s.compute import Deployment, Pod, StatefulSet, DaemonSet
from diagrams.k8s.network import Service
from diagrams.aws.storage import S3
from diagrams.onprem.queue import RabbitMQ
from diagrams.onprem.network import Internet
from diagrams.programming.language import Nodejs
from diagrams.onprem.client import User, Client

graph_attr = {
    "fontsize": "45",
    "bgcolor": "transparent"
}

with Diagram("Observability Stack - E-commerce Platform", show=False, direction="TB", outformat="jpg", filename="observability_stack_diagram", graph_attr=graph_attr):
    # Service consumers
    sre = User("SRE Team")
    developer = User("Developers")
    business = Client("Business Analysts")
    
    with Cluster("Microservice Instrumentation"):
        # Example microservices
        user_svc = Nodejs("User Service")
        order_svc = Nodejs("Order Service")
        product_svc = Nodejs("Product Service")
        payment_svc = Nodejs("Payment Service")
        
    with Cluster("Monitoring & Alerting (PGA Stack)"):
        # Core monitoring components
        with Cluster("Metrics Collection & Storage"):
            prometheus = Prometheus("Prometheus")
            prom_am = Prometheus("Alertmanager")
            prom_stateful = StatefulSet("Prometheus StatefulSet")
            prom_service = Service("Prometheus Service")
            
            # Connect Prometheus components
            prometheus - prom_stateful
            prometheus - prom_service
            prometheus - prom_am
            
        with Cluster("Visualization"):
            grafana = Grafana("Grafana")
            grafana_deploy = Deployment("Grafana Deployment")
            grafana_svc = Service("Grafana Service")
            
            # Connect Grafana components
            grafana - grafana_deploy
            grafana - grafana_svc
            
        # SLO dashboards in Grafana
        slo_dash = Grafana("SLO Dashboards")
        service_dash = Grafana("Service Dashboards")
        
        # Connect dashboards to Grafana
        grafana >> slo_dash
        grafana >> service_dash
    
    with Cluster("Distributed Tracing (OpenTelemetry)"):
        # OpenTelemetry components
        otel_collector = Deployment("OpenTelemetry Collector")
        
        with Cluster("Trace Storage & Visualization"):
            jaeger_collector = Jaeger("Jaeger Collector")
            jaeger_query = Jaeger("Jaeger Query")
            jaeger_svc = Service("Jaeger Service")
            
            # Connect Jaeger components
            jaeger_collector - jaeger_query
            jaeger_query - jaeger_svc
    
    with Cluster("Logging Infrastructure"):
        # Logging components
        fluentbit = FluentBit("FluentBit DaemonSet")
        loki = Loki("Loki")
        loki_svc = Service("Loki Service")
        
        # S3 for long-term storage
        logs_bucket = S3("Log Archives")
        
        # Connect logging components
        fluentbit >> loki
        loki - loki_svc
        loki >> logs_bucket
    
    # Cross-component connections
    prometheus >> Edge(color="darkgreen", label="scrapes metrics", style="dashed") >> otel_collector
    
    # Instrument services with the observability stack
    for service in [user_svc, order_svc, product_svc, payment_svc]:
        service >> Edge(color="darkgreen", label="metrics") >> prometheus
        service >> Edge(color="darkblue", label="traces") >> otel_collector
        service >> Edge(color="darkorange", label="logs") >> fluentbit
    
    # Data flow to OTel collector and Jaeger
    otel_collector >> jaeger_collector
    
    # Connections to consumers
    sre >> Edge(color="blue") >> grafana
    sre >> Edge(color="red") >> prom_am
    developer >> Edge(color="blue") >> jaeger_query
    
    # Grafana datasource connections
    prometheus << Edge(label="data source", style="dotted") << grafana
    loki << Edge(label="data source", style="dotted") << grafana
    jaeger_query << Edge(label="data source", style="dotted") << grafana
    
    # Business dashboards
    business >> Edge(color="green") >> service_dash
