# ecommerce-documentation/architecture/diagrams/c4/c3/product-service/c3_product_service_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL, MongoDB
from diagrams.onprem.queue import Kafka
from diagrams.elastic.elasticsearch import Elasticsearch
from diagrams.onprem.client import User, Users

# --- Configuration ---
diagram_name = "C3 Product Service Component Diagram"
output_filename = "c3_product_service_diagram"
graph_attr = {
    "fontsize": "20",
    "bgcolor": "transparent",
    "splines": "ortho",
    "nodesep": "1.0",
    "ranksep": "1.5",
    "concentrate": "true",
    "compound": "true"
}
# --- End Configuration ---

with Diagram(diagram_name, show=False, filename=output_filename, graph_attr=graph_attr, direction="LR", outformat="jpg"):

    # --- External Systems/Users ---
    frontend = Users("Frontend Applications")
    admin_portal = User("Admin Portal")
    order_service = Server("Order Service")
    recommendation_service = Server("Recommendation Service")

    # --- External Dependencies ---
    product_db = PostgreSQL("Product Database\n(e.g., PostgreSQL, MongoDB)")
    search_index = Elasticsearch("Search Index\n(e.g., Elasticsearch)")
    msg_broker = Kafka("Message Broker\n(e.g., Kafka, RabbitMQ)")

    # --- Product Service Components ---
    with Cluster("Product Service Container\n(Manages product info, inventory, pricing, search)"):
        
        # Define components
        api_interface = Server("API Interface\n(REST/GraphQL)\nExposes product functionalities")
        catalog = Server("Product Catalog Component\nCore logic for product details, categories, attributes")
        inventory = Server("Inventory Component\nTracks stock levels, availability")
        pricing = Server("Pricing Component\nCalculates prices, handles promotions")
        search = Server("Search Integration Component\nManages product indexing, interfaces with Search Index")
        review = Server("Review Management Component\nHandles product reviews")
        persistence = Server("Data Persistence Component\nDB interactions for product, inventory, reviews")
        event_publishing = Server("Event Publishing Component\nPublishes domain events")

        # Internal component interactions
        api_interface >> Edge(label="Delegates to") >> catalog
        api_interface >> Edge(label="Delegates to") >> inventory
        api_interface >> Edge(label="Delegates to") >> pricing
        api_interface >> Edge(label="Queries") >> search
        api_interface >> Edge(label="Delegates to") >> review

        catalog >> Edge(label="Uses for product data") >> persistence
        inventory >> Edge(label="Uses for inventory data") >> persistence
        review >> Edge(label="Uses for review data") >> persistence
        pricing >> Edge(label="Uses for pricing rules (optional)") >> persistence

        catalog >> Edge(label="Notifies for indexing") >> search
        inventory >> Edge(label="Notifies stock for indexing") >> search

        catalog >> Edge(label="Publishes changes") >> event_publishing
        inventory >> Edge(label="Publishes stock updates") >> event_publishing
        pricing >> Edge(label="Publishes price changes") >> event_publishing
        review >> Edge(label="Publishes new reviews") >> event_publishing

    # --- External interactions ---
    # From external systems to Product Service
    frontend >> Edge(label="Gets product info, search") >> api_interface
    admin_portal >> Edge(label="Manages product catalog") >> api_interface
    order_service >> Edge(label="Gets product details, prices") >> api_interface
    recommendation_service >> Edge(label="Gets product metadata") >> api_interface
    
    # From Product Service to external dependencies
    persistence >> Edge(label="Reads/Writes") >> product_db
    search >> Edge(label="Indexes/Queries") >> search_index
    event_publishing >> Edge(label="Sends events to") >> msg_broker

print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
