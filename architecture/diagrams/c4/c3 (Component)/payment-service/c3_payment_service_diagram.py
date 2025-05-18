# ecommerce-documentation/architecture/diagrams/c4/c3/payment-service/c3_payment_service_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.queue import Kafka
from diagrams.onprem.client import User
from diagrams.aws.general import General
from diagrams.azure.security import KeyVaults

# --- Configuration ---
diagram_name = "C3 Payment Service Component Diagram"
output_filename = "c3_payment_service_diagram"
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
    order_service = Server("Order Service")
    admin_user = User("Admin User/System\n(for refunds, configuration)")

    # --- External Dependencies ---
    payment_gateway_stripe = General("External Payment Gateway\n(e.g., Stripe)")
    payment_gateway_paypal = General("External Payment Gateway\n(e.g., PayPal)")
    fraud_service = KeyVaults("External Fraud Detection Service\n(Optional)")
    payment_db = PostgreSQL("Payment Database\n(e.g., PostgreSQL, MySQL)")
    msg_broker = Kafka("Message Broker\n(e.g., Kafka, RabbitMQ)")

    # --- Payment Service Components ---
    with Cluster("Payment Service Container\n(Handles payment processing, gateway integrations)"):
        
        # Define components
        api_interface = Server("API Interface\n(REST/gRPC)\nExposes payment operations")
        processor = Server("Payment Processing Component\nOrchestrates payment authorization, capture, refunds")
        gateway_integration = Server("Payment Gateway Integration Component\nAdapters for external payment gateways")
        transaction_mgr = Server("Transaction Management Component\nManages payment transaction lifecycle and history")
        fraud_integration = Server("Fraud Detection Integration Component\n(Optional) Connects to fraud screening services")
        persistence = Server("Data Persistence Component\nStores transaction data, gateway configs")
        event_publishing = Server("Event Publishing Component\nPublishes payment status events")

        # Internal component interactions
        api_interface >> Edge(label="Requests") >> processor
        processor >> Edge(label="Uses") >> gateway_integration
        processor >> Edge(label="Updates/Reads") >> transaction_mgr
        processor >> Edge(label="Consults (optional)") >> fraud_integration
        transaction_mgr >> Edge(label="Uses") >> persistence
        processor >> Edge(label="Publishes via") >> event_publishing
        gateway_integration >> Edge(label="Stores config/logs via") >> persistence

    # --- External interactions ---
    # From external systems to Payment Service
    order_service >> Edge(label="Initiates Payment, Receives Status") >> api_interface
    admin_user >> Edge(label="Manages Refunds, Configuration") >> api_interface
    
    # From Payment Service to external dependencies
    gateway_integration >> Edge(label="Processes via") >> payment_gateway_stripe
    gateway_integration >> Edge(label="Processes via") >> payment_gateway_paypal
    fraud_integration >> Edge(label="Checks transaction with") >> fraud_service
    persistence >> Edge(label="Reads/Writes") >> payment_db
    event_publishing >> Edge(label="Sends events to") >> msg_broker

print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
