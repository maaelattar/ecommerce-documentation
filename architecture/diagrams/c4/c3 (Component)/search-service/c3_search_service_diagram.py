# ecommerce-documentation/architecture/diagrams/c4/c3/search-service/c3_search_service_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import MongoDB
from diagrams.onprem.queue import Kafka
from diagrams.elastic.elasticsearch import Elasticsearch
from diagrams.onprem.client import Users

# --- Configuration ---
diagram_name = "C3 Search Service Component Diagram"
output_filename = "c3_search_service_diagram"
graph_attr = {
    "fontsize": "20",
    "bgcolor": "transparent",
    "splines": "ortho",
    "nodesep": "1.2",
    "ranksep": "1.8",
    "concentrate": "true",
    "compound": "true"
}
# --- End Configuration ---

with Diagram(diagram_name, show=False, filename=output_filename, graph_attr=graph_attr, direction="LR", outformat="jpg"):

    # --- External Systems/Users ---
    frontend = Users("Frontend Applications")
    product_service = Server("Product Service")
    inventory_service = Server("Inventory Service")
    
    # --- External Dependencies ---
    search_config_db = MongoDB("Search Configuration DB\n(MongoDB)")
    msg_broker = Kafka("Message Broker\n(e.g., Kafka, RabbitMQ)")
    elasticsearch_cluster = Elasticsearch("Elasticsearch Cluster")

    # --- Search Service Components ---
    with Cluster("Search Service Container\n(Provides search capabilities across catalog)"):
        
        # API Layer
        api_interface = Server("Search API Interface\n[Component: NestJS Controller]\nExposes search endpoints")
        
        # Service Layer
        search_orchestrator = Server("Search Orchestrator\n[Component: NestJS Service]\nCoordinates search operations")
        query_builder = Server("Query Builder\n[Component: Query Service]\nBuilds Elasticsearch queries")
        facet_manager = Server("Facet Manager\n[Component: Filter Service]\nHandles filtering and faceted search")
        result_processor = Server("Result Processor\n[Component: Processor Service]\nTransforms and enriches results")
        
        # Domain Layer
        search_configuration = Server("Search Configuration\n[Component: Domain Entities]\nDefines searchable attributes, boosts, etc.")
        
        # Data Access Layer
        search_repository = Server("Search Repository\n[Component: Repository]\nManages configuration storage")
        
        # Integration Layer
        index_manager = Server("Index Manager\n[Component: Integration Service]\nManages Elasticsearch indexes")
        event_consumer = Server("Event Consumer\n[Component: Message Client]\nConsumes product/inventory events")

        # Internal component interactions
        api_interface >> Edge(label="Uses") >> search_orchestrator
        event_consumer >> Edge(label="Updates via") >> index_manager
        
        search_orchestrator >> Edge(label="Uses") >> query_builder
        search_orchestrator >> Edge(label="Uses") >> facet_manager
        search_orchestrator >> Edge(label="Uses") >> result_processor
        
        query_builder >> Edge(label="Configures using") >> search_configuration
        facet_manager >> Edge(label="Configures using") >> search_configuration
        
        index_manager >> Edge(label="Manages") >> search_configuration
        search_repository >> Edge(label="Persists") >> search_configuration

    # --- External interactions ---
    # From external systems to Search Service
    frontend >> Edge(label="Search requests") >> api_interface
    product_service >> Edge(label="Direct index requests") >> api_interface
    msg_broker >> Edge(label="Product/Inventory events") >> event_consumer
    
    # From Search Service to external dependencies
    search_repository >> Edge(label="Reads/Writes") >> search_config_db
    query_builder >> Edge(label="Queries") >> elasticsearch_cluster
    facet_manager >> Edge(label="Queries") >> elasticsearch_cluster
    index_manager >> Edge(label="Manages indexes") >> elasticsearch_cluster

print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
