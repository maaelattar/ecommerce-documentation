# ecommerce-documentation/architecture/diagrams_python/c2_container_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.generic.device import Mobile, Tablet
from diagrams.generic.blank import Blank
from diagrams.onprem.client import User, Users
from diagrams.onprem.network import Internet
from diagrams.onprem.compute import Server # Generic server, can be used for custom services
from diagrams.onprem.database import PostgreSQL, MongoDB, Cassandra # Example databases
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import Kafka # Or RabbitMQ
from diagrams.elastic.elasticsearch import Elasticsearch
from diagrams.onprem.security import Vault # For Identity Provider (conceptual)
from diagrams.aws.compute import EC2 # Generic compute for services if deploying to AWS
from diagrams.aws.database import RDS, DocumentDB # Example AWS databases
from diagrams.aws.integration import SQS, SNS # Example AWS messaging
from diagrams.aws.network import APIGateway

# --- Configuration ---
diagram_name = "C2 E-Commerce Platform Container Diagram"
output_filename = "c2_container_diagram" # Output will be c2_container_diagram.jpg
graph_attr = {
    "fontsize": "18",
    "bgcolor": "transparent",
    "splines": "ortho", # Changed from "spline" to "ortho" for cleaner right-angle lines
    "nodesep": "1.0",  # Reduced slightly from 1.2
    "ranksep": "1.8",  # Slightly reduced from 2.0
    "concentrate": "true",  # Helps merge edges going in the same direction
    "compound": "true"  # Allows edges between clusters
}
# --- End Configuration ---

with Diagram(diagram_name, show=False, filename=output_filename, graph_attr=graph_attr, direction="LR", outformat="jpg"):

    # --- External Users & Systems ---
    customer = User("Customer\n(Web/Mobile User)")
    admin_user = User("Admin User\n(Manages platform)")
    external_payment_gateway = Server("External Payment Gateway\n(e.g., Stripe, PayPal)") # Using generic server
    external_shipping_provider = Server("External Shipping Provider\n(e.g., FedEx, DHL)") # Using generic server
    external_identity_provider = Vault("External Identity Provider\n(e.g., Auth0, Okta)") # Using Vault as a placeholder

    # --- E-Commerce Platform Boundary ---
    with Cluster("E-Commerce Platform (Software System)"):

        with Cluster("Frontend Applications"):
            web_app = Server("Web Application\n(React/Vue/Angular)") # Generic Server for WebApp
            mobile_app = Mobile("Mobile Application\n(iOS/Android)")

        with Cluster("API Layer"):
            api_gateway = APIGateway("API Gateway\n(Handles external requests, routes to services)")

        with Cluster("Microservices (Backend Systems)"):
            product_service = Server("Product Service\n(Manages product catalog, pricing)") # Updated description
            order_service = Server("Order Service\n(Manages orders, cart, checkout)")
            payment_service = Server("Payment Service\n(Processes payments)")
            user_service = Server("User Service\n(Manages user accounts, profiles)")
            inventory_service = Server("Inventory Service\n(Manages stock levels - if separate)") # Assuming it might be separate
            notification_service = Server("Notification Service\n(Handles emails, SMS, push notifications)")
            search_service_container = Server("Search Service\n(Provides search capabilities - distinct from index)")

        with Cluster("Data Stores"):
            product_db = PostgreSQL("Product DB\n(PostgreSQL)")
            order_db = MongoDB("Order DB\n(MongoDB)")
            user_db = PostgreSQL("User DB\n(PostgreSQL - for user profiles)")
            inventory_db = Redis("Inventory DB\n(Redis - for fast stock checks)") # Example
            payment_db = Cassandra("Payment DB\n(Cassandra - for transaction logs)") # Example

        with Cluster("Search & Caching"):
            search_index = Elasticsearch("Search Index\n(Elasticsearch)")
            cache = Redis("Distributed Cache\n(Redis)")

        with Cluster("Messaging Infrastructure"):
            message_broker = Kafka("Message Broker\n(Kafka/RabbitMQ)\nEvent-driven communication")

        # --- Internal Connections ---
        # Frontend to API Gateway
        web_app >> Edge(label="Makes API calls (HTTPS)") >> api_gateway
        mobile_app >> Edge(label="Makes API calls (HTTPS)") >> api_gateway

        # API Gateway to Microservices
        api_gateway >> Edge(label="Routes to") >> product_service
        api_gateway >> Edge(label="Routes to") >> order_service
        api_gateway >> Edge(label="Routes to") >> payment_service
        api_gateway >> Edge(label="Routes to") >> user_service
        api_gateway >> Edge(label="Routes to") >> search_service_container
        api_gateway >> Edge(label="Routes to (async trigger)") >> notification_service # e.g., for password reset initiate

        # Microservice to Microservice (Direct or via Message Broker)
        order_service >> Edge(label="Requests product info") >> product_service
        order_service >> Edge(label="Requests inventory check") >> inventory_service # Assuming direct or via API
        order_service >> Edge(label="Initiates payment") >> payment_service
        order_service >> Edge(label="Publishes OrderCreated event") >> message_broker
        
        inventory_service >> Edge(label="Reads/Writes stock levels") >> inventory_db # Added connection

        payment_service >> Edge(label="Publishes PaymentProcessed event") >> message_broker
        product_service >> Edge(label="Publishes ProductUpdated event") >> message_broker
        inventory_service >> Edge(label="Publishes StockUpdated event") >> message_broker # Assuming it's a source of truth
        user_service >> Edge(label="Publishes UserRegistered event") >> message_broker

        search_service_container >> Edge(label="Queries/Manages") >> search_index # Added connection

        # Microservices consuming events
        message_broker >> Edge(label="OrderCreated event") >> notification_service # For order confirmation
        message_broker >> Edge(label="PaymentProcessed event") >> order_service # To update order status
        message_broker >> Edge(label="ProductUpdated event") >> search_service_container # Search service consumes product updates
        message_broker >> Edge(label="PaymentProcessed event") >> notification_service # For payment confirmation
        message_broker >> Edge(label="StockUpdated event") >> product_service # To update availability display (if needed)
        message_broker >> Edge(label="UserRegistered event") >> notification_service # For welcome email

        # Microservices to Data Stores
        product_service >> Edge(label="Reads/Writes") >> product_db
        product_service >> Edge(label="Updates") >> search_index # For indexing
        product_service >> Edge(label="Uses") >> cache

        order_service >> Edge(label="Reads/Writes") >> order_db
        order_service >> Edge(label="Uses") >> cache # e.g., for cart

        payment_service >> Edge(label="Reads/Writes") >> payment_db

        user_service >> Edge(label="Reads/Writes") >> user_db

        inventory_service >> Edge(label="Reads/Writes") >> inventory_db
        
        search_service_container >> Edge(label="Queries") >> search_index


        # Microservices to other internal systems
        notification_service # Standalone, but triggered by events or API calls

    # --- Connections to External Systems ---
    customer >> Edge(label="Uses") >> web_app
    customer >> Edge(label="Uses") >> mobile_app
    admin_user >> Edge(label="Accesses Admin Panel via") >> web_app # Assuming admin panel is part of main web app

    payment_service >> Edge(label="Processes payments via (HTTPS)") >> external_payment_gateway
    order_service >> Edge(label="Gets shipping rates/labels from (API)") >> external_shipping_provider # Via Order Service for fulfillment
    user_service >> Edge(label="Authenticates via (OAuth/SAML)") >> external_identity_provider
    api_gateway >> Edge(label="Delegates authentication (sometimes)") >> external_identity_provider # For user-facing apps


print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
