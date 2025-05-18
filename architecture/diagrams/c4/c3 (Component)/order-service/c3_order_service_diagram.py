# ecommerce-documentation/architecture/diagrams/c4/c3/order-service/c3_order_service_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.queue import Kafka
from diagrams.custom import Custom

# --- Configuration ---
diagram_name = "C3 Order Service Component Diagram"
output_filename = "c3_order_service_diagram"
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

    # --- External Systems/Containers ---
    api_gateway = Server("API Gateway\n[External Container]")
    payment_service = Server("Payment Service\n[External Container]")
    message_broker = Kafka("Message Broker (RabbitMQ)\n[External Container]")
    order_db = PostgreSQL("Order DB (PostgreSQL)\n[External Container]")

    # --- Order Service Components ---
    with Cluster("Order Service Container"):
        # Define components in logical layers
        
        # API Layer
        api_controller = Server("Order API Controller\n[Component: NestJS Controller]\nHandles incoming HTTP requests for orders and carts")
        
        # Service Layer
        app_service = Server("Order Application Service\n[Component: NestJS Service]\nCore business logic for order creation, updates, and management")
        cart_component = Server("Cart Management Component\n[Component: NestJS Service/Module]\nManages shopping cart logic")
        
        # Domain Layer
        domain_entities = Server("Order Domain Entities\n[Component: TypeORM Entities/Classes]\nRepresents Order, OrderItem, etc.")
        
        # Data Access Layer
        order_repo = Server("Order Repository\n[Component: TypeORM Repository]\nData access for order entities")
        
        # Integration Layer
        payment_client = Server("Payment Service Client\n[Component: HTTP Client Wrapper]\nCommunicates with the Payment Service")
        event_publisher = Server("Event Publisher\n[Component: RabbitMQ Client Wrapper]\nPublishes domain events")

        # Internal component interactions
        api_controller >> Edge(label="Routes to") >> app_service
        api_controller >> Edge(label="Routes to") >> cart_component
        
        app_service >> Edge(label="Uses") >> domain_entities
        app_service >> Edge(label="Persists via") >> order_repo
        app_service >> Edge(label="Requests payment") >> payment_client
        app_service >> Edge(label="Publishes events") >> event_publisher
        
        cart_component >> Edge(label="Uses") >> domain_entities
        cart_component >> Edge(label="Persists via") >> order_repo

    # --- External interactions ---
    api_gateway >> Edge(label="Routes HTTP requests to") >> api_controller
    order_repo >> Edge(label="Reads/Writes [SQL]") >> order_db
    payment_client >> Edge(label="Requests payment processing [HTTPS/JSON]") >> payment_service
    event_publisher >> Edge(label="Publishes 'OrderCreated' etc. [AMQP]") >> message_broker

print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
