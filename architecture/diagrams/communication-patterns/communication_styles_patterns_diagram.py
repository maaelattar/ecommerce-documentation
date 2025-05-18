# /Users/mh/Documents/Wave/demo/ecommerce-repos-gemi/ecommerce-documentation/architecture/diagrams/communication-patterns/communication_styles_patterns_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.network import Nginx as APIGateway # Using Nginx as a generic API Gateway icon
from diagrams.onprem.queue import Kafka # Using Kafka as a generic message broker icon
from diagrams.onprem.security import Vault # For IdP
from diagrams.generic.blank import Blank # For generic external services if no specific icon fits

# --- Configuration ---
diagram_name = "Communication Styles and Patterns"
output_filename = "communication_styles_patterns_diagram" # Output will be .jpg
graph_attr = {
    "fontsize": "18",
    "bgcolor": "transparent",
    "splines": "ortho", # Using ortho for cleaner lines
    "nodesep": "0.8",
    "ranksep": "1.5",
    "compound": "true" # Allows edges between clusters
}
edge_attr = {
    "fontsize": "10",
    "fontname": "Sans-Serif"
}
node_attr = {
    "fontsize": "12",
    "fontname": "Sans-Serif",
    "height": "1.0", # Slightly smaller nodes
    "width": "2.0"
}

# Edge styles based on Mermaid classDef
sync_color = "#0078d7"
async_color = "#ff8c00"
sync_edge_attrs = {"color": sync_color, "style": "solid", "penwidth": "2.0"}
async_edge_attrs = {"color": async_color, "style": "dashed", "penwidth": "2.0"}
# --- End Configuration ---

with Diagram(diagram_name, show=False, filename=output_filename, graph_attr=graph_attr, edge_attr=edge_attr, node_attr=node_attr, direction="TB", outformat="jpg"):

    # --- Infrastructure Nodes ---
    gateway = APIGateway("API Gateway")
    broker = Kafka("Message Broker")

    # --- Service Nodes ---
    with Cluster("Internal Microservices"):
        user_service = Server("User Service")
        product_service = Server("Product Service")
        order_service = Server("Order Service")
        payment_service = Server("Payment Service")
        notification_service = Server("Notification Service")
        
        # Grouping for layout
        services_group1 = [user_service, product_service]
        services_group2 = [order_service, payment_service, notification_service]


    # --- External System Nodes ---
    with Cluster("External Systems"):
        idp = Vault("Identity Provider (IdP)")
        payment_gw = Server("Payment Gateway (Ext.)")
        email_svc = Blank("Email Service (Ext.)") # Using Blank for generic external
        shipping_api = Blank("Shipping API (Ext.)") # Using Blank for generic external
        
        external_group1 = [idp, payment_gw]
        external_group2 = [email_svc, shipping_api]

    # --- Define Connections ---

    # Gateway to Services (Synchronous REST)
    gateway >> Edge(label="REST API Calls", **sync_edge_attrs) >> user_service
    gateway >> Edge(label="REST API Calls", **sync_edge_attrs) >> product_service
    gateway >> Edge(label="REST API Calls", **sync_edge_attrs) >> order_service
    gateway >> Edge(label="REST API Calls", **sync_edge_attrs) >> payment_service
    
    # Gateway to IdP (Synchronous Auth Validation)
    gateway >> Edge(label="Auth Validation", **sync_edge_attrs) >> idp

    # Service to External System (Synchronous)
    payment_service >> Edge(label="Process Payment (HTTPS)", **sync_edge_attrs) >> payment_gw
    order_service >> Edge(label="Get Shipping Rates (HTTPS)", **sync_edge_attrs) >> shipping_api

    # Service to Broker (Asynchronous Event Publishing)
    user_service >> Edge(label="Publishes UserRegistered", **async_edge_attrs) >> broker
    product_service >> Edge(label="Publishes ProductUpdated", **async_edge_attrs) >> broker
    order_service >> Edge(label="Publishes OrderCreated,\nOrderShipped", **async_edge_attrs) >> broker
    payment_service >> Edge(label="Publishes PaymentProcessed", **async_edge_attrs) >> broker

    # Broker to Service (Asynchronous Event Consumption)
    broker >> Edge(label="Consumes All Events\n(for notifications)", **async_edge_attrs) >> notification_service
    broker >> Edge(label="Consumes OrderCreated\n(e.g., for inventory/analytics)", **async_edge_attrs) >> product_service # As per existing Mermaid
    broker >> Edge(label="Consumes PaymentProcessed\n(to update order status)", **async_edge_attrs) >> order_service

    # Notification Service to External Email Service (Asynchronous)
    notification_service >> Edge(label="Sends Email (via API)", **async_edge_attrs) >> email_svc

print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
