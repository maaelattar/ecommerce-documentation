# ecommerce-documentation/architecture/diagrams/c4/c3/user-service/c3_user_service_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.queue import Kafka
from diagrams.onprem.client import User, Users
from diagrams.onprem.security import Vault

# --- Configuration ---
diagram_name = "C3 User Service Component Diagram"
output_filename = "c3_user_service_diagram"
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
    customer = Users("Customers")
    admin = User("Admin Users")
    frontend = Server("Frontend Applications")
    other_services = Server("Other Microservices\n(Order, Product, etc.)")
    identity_provider = Vault("External Identity Provider\n(e.g., Auth0, Okta)")

    # --- External Dependencies ---
    user_db = PostgreSQL("User Database\n(PostgreSQL)")
    msg_broker = Kafka("Message Broker\n(e.g., Kafka, RabbitMQ)")

    # --- User Service Components ---
    with Cluster("User Service Container\n(Manages user accounts, profiles, and authentication)"):
        
        # API Layer
        api_interface = Server("API Interface\n[Component: NestJS Controller]\nExposes user management endpoints")
        
        # Service Layer
        auth_service = Server("Authentication Service\n[Component: NestJS Service]\nHandles login, registration, token verification")
        profile_service = Server("Profile Management Service\n[Component: NestJS Service]\nManages user profile data")
        preferences_service = Server("User Preferences Service\n[Component: NestJS Service]\nManages user settings and preferences")
        
        # Domain Layer
        domain_entities = Server("User Domain Entities\n[Component: TypeORM Entities]\nUser, Profile, Preferences classes")
        
        # Data Access Layer
        user_repository = Server("User Repository\n[Component: TypeORM Repository]\nData access for user entities")
        
        # Integration Layer
        auth_provider_client = Server("Identity Provider Client\n[Component: OAuth/OIDC Client]\nIntegrates with external IdP")
        event_publisher = Server("Event Publisher\n[Component: Message Client]\nPublishes user-related events")

        # Internal component interactions
        api_interface >> Edge(label="Delegates auth") >> auth_service
        api_interface >> Edge(label="Delegates profile ops") >> profile_service
        api_interface >> Edge(label="Delegates preferences") >> preferences_service
        
        auth_service >> Edge(label="Uses") >> domain_entities
        auth_service >> Edge(label="Authenticates via") >> auth_provider_client
        
        profile_service >> Edge(label="Uses") >> domain_entities
        profile_service >> Edge(label="Persists via") >> user_repository
        profile_service >> Edge(label="Publishes events via") >> event_publisher
        
        preferences_service >> Edge(label="Uses") >> domain_entities
        preferences_service >> Edge(label="Persists via") >> user_repository

    # --- External interactions ---
    # From external systems to User Service
    frontend >> Edge(label="User operations (register, login, profile)") >> api_interface
    other_services >> Edge(label="User validation, profile data") >> api_interface
    
    # From User Service to external dependencies
    user_repository >> Edge(label="Reads/Writes") >> user_db
    auth_provider_client >> Edge(label="Authenticates via") >> identity_provider
    event_publisher >> Edge(label="Publishes events") >> msg_broker
    
    # User interactions
    customer >> Edge(label="Uses via frontend") >> frontend
    admin >> Edge(label="Manages users via") >> frontend

print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
