# ecommerce-documentation/architecture/diagrams/c4/c3/inventory-service/c3_inventory_service_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import Kafka
from diagrams.onprem.client import User, Users

# --- Configuration ---
diagram_name = "C3 Inventory Service Component Diagram"
output_filename = "c3_inventory_service_diagram"
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
    admin = User("Admin/Warehouse Users")
    product_service = Server("Product Service")
    order_service = Server("Order Service")
    frontend = Users("Frontend Applications")
    
    # --- External Dependencies ---
    inventory_db = PostgreSQL("Inventory Database\n(PostgreSQL)")
    inventory_cache = Redis("Inventory Cache\n(Redis)")
    msg_broker = Kafka("Message Broker\n(e.g., Kafka, RabbitMQ)")

    # --- Inventory Service Components ---
    with Cluster("Inventory Service Container\n(Manages stock levels and inventory operations)"):
        
        # API Layer
        api_interface = Server("Inventory API Interface\n[Component: NestJS Controller]\nExposes inventory endpoints")
        
        # Service Layer
        inventory_manager = Server("Inventory Manager\n[Component: NestJS Service]\nCore inventory operations logic")
        reservation_service = Server("Reservation Service\n[Component: NestJS Service]\nReserves inventory during checkout")
        allocation_service = Server("Allocation Service\n[Component: NestJS Service]\nAllocates inventory for fulfilled orders")
        reporting_service = Server("Reporting Service\n[Component: NestJS Service]\nInventory analytics and reporting")
        
        # Domain Layer
        domain_entities = Server("Inventory Domain Entities\n[Component: TypeORM Entities]\nStockItem, Warehouse, etc.")
        
        # Data Access Layer
        inventory_repository = Server("Inventory Repository\n[Component: TypeORM Repository]\nData access for inventory entities")
        cache_manager = Server("Cache Manager\n[Component: Cache Client]\nManages fast access to inventory levels")
        
        # Integration Layer
        event_publisher = Server("Event Publisher\n[Component: Message Client]\nPublishes inventory events")
        event_consumer = Server("Event Consumer\n[Component: Message Client]\nConsumes order and product events")

        # Internal component interactions
        api_interface >> Edge(label="Uses") >> inventory_manager
        api_interface >> Edge(label="Uses") >> reservation_service
        api_interface >> Edge(label="Uses") >> allocation_service
        api_interface >> Edge(label="Uses") >> reporting_service
        
        event_consumer >> Edge(label="Triggers") >> reservation_service
        event_consumer >> Edge(label="Triggers") >> allocation_service
        
        inventory_manager >> Edge(label="Uses") >> domain_entities
        reservation_service >> Edge(label="Uses") >> domain_entities
        allocation_service >> Edge(label="Uses") >> domain_entities
        reporting_service >> Edge(label="Uses") >> domain_entities
        
        inventory_manager >> Edge(label="Persists via") >> inventory_repository
        reservation_service >> Edge(label="Persists via") >> inventory_repository
        allocation_service >> Edge(label="Persists via") >> inventory_repository
        reporting_service >> Edge(label="Reads data via") >> inventory_repository
        
        inventory_manager >> Edge(label="Uses") >> cache_manager
        reservation_service >> Edge(label="Uses") >> cache_manager
        
        inventory_manager >> Edge(label="Publishes via") >> event_publisher
        reservation_service >> Edge(label="Publishes via") >> event_publisher
        allocation_service >> Edge(label="Publishes via") >> event_publisher

    # --- External interactions ---
    # From external systems to Inventory Service
    admin >> Edge(label="Manages inventory") >> api_interface
    product_service >> Edge(label="Gets inventory levels") >> api_interface
    order_service >> Edge(label="Reserves/allocates items") >> api_interface
    frontend >> Edge(label="Views availability") >> api_interface
    msg_broker >> Edge(label="Order/Product events") >> event_consumer
    
    # From Inventory Service to external dependencies
    inventory_repository >> Edge(label="Reads/Writes") >> inventory_db
    cache_manager >> Edge(label="Reads/Writes") >> inventory_cache
    event_publisher >> Edge(label="Publishes events") >> msg_broker

print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
