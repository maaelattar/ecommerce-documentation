# ecommerce-documentation/architecture/diagrams_python/c1_system_context_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User
from diagrams.onprem.compute import Server # Generic server for external systems
from diagrams.generic.blank import Blank # For the main system box
from diagrams.onprem.network import Internet
from diagrams.onprem.security import Vault # Placeholder for Identity Provider

# --- Configuration ---
diagram_name = "C1 E-Commerce Platform System Context Diagram"
output_filename = "c1_system_context_diagram"
graph_attr = {
    "fontsize": "20", # Slightly larger for C1
    "bgcolor": "transparent",
    "splines": "spline",
    "nodesep": "1.2",
    "ranksep": "1.8",
}
# --- End Configuration ---

with Diagram(diagram_name, show=False, filename=output_filename, graph_attr=graph_attr, direction="LR", outformat="jpg"):

    # --- Actors ---
    customer = User("Customer\n(Uses the platform to browse and purchase products)")
    admin_user = User("Admin User\n(Manages platform content, users, and orders)")

    # --- External Systems ---
    payment_gateway = Server("External Payment Gateway\n(e.g., Stripe, PayPal)\nProcesses payments")
    shipping_provider = Server("External Shipping Provider\n(e.g., FedEx, DHL)\nHandles order fulfillment logistics")
    identity_provider = Vault("External Identity Provider\n(e.g., Auth0, Okta)\nManages user authentication") # Using Vault as a placeholder

    # --- The System Itself (as a single box) ---
    # Using a Cluster to visually group the system, even if it's just one node for C1
    with Cluster("Our E-Commerce Ecosystem"):
        ecommerce_system = Server("E-Commerce Platform\n(The software system being built)")

    # --- Relationships ---
    customer >> Edge(label="Uses (HTTPS)") >> ecommerce_system
    admin_user >> Edge(label="Manages (HTTPS)") >> ecommerce_system

    ecommerce_system >> Edge(label="Processes Payments Via (API/HTTPS)") >> payment_gateway
    ecommerce_system >> Edge(label="Arranges Shipping Via (API)") >> shipping_provider
    ecommerce_system >> Edge(label="Authenticates Users Via (OAuth/SAML)") >> identity_provider


print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
