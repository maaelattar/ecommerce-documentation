# ecommerce-documentation/architecture/diagrams/c4/c3/notification-service/c3_notification_service_diagram.py

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import MongoDB
from diagrams.onprem.queue import Kafka
from diagrams.onprem.client import User, Users
from diagrams.aws.integration import SNS

# --- Configuration ---
diagram_name = "C3 Notification Service Component Diagram"
output_filename = "c3_notification_service_diagram"
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
    other_services = Server("Other Microservices\n(Order, User, Product, etc.)")
    admin = User("Admin Users\n(Manages notification templates)")
    
    # --- External Dependencies ---
    notification_db = MongoDB("Notification Database\n(MongoDB)")
    msg_broker = Kafka("Message Broker\n(e.g., Kafka, RabbitMQ)")
    email_provider = SNS("Email Service Provider\n(e.g., SendGrid, Mailchimp)")
    sms_provider = SNS("SMS Service Provider\n(e.g., Twilio)")
    push_provider = SNS("Push Notification Provider\n(e.g., Firebase FCM)")

    # --- Notification Service Components ---
    with Cluster("Notification Service Container\n(Handles emails, SMS, push notifications)"):
        
        # API Layer
        api_interface = Server("API Interface\n[Component: NestJS Controller]\nExposes notification endpoints")
        
        # Service Layer
        notification_manager = Server("Notification Manager\n[Component: NestJS Service]\nOrchestrates notification delivery")
        template_engine = Server("Template Engine\n[Component: Template Service]\nRenders notification content")
        delivery_scheduler = Server("Delivery Scheduler\n[Component: Queue Service]\nHandles timing and retries")
        
        # Domain Layer
        notification_templates = Server("Notification Templates\n[Component: Domain Entities]\nEmail/SMS/Push templates")
        notification_preferences = Server("User Notification Preferences\n[Component: Domain Entities]\nUser channel/frequency settings")
        
        # Data Access Layer
        notification_repository = Server("Notification Repository\n[Component: Repository]\nStores notification records and templates")
        
        # Integration Layer
        event_consumer = Server("Event Consumer\n[Component: Message Client]\nConsumes events from other services")
        email_gateway = Server("Email Gateway\n[Component: Integration Client]\nSends emails")
        sms_gateway = Server("SMS Gateway\n[Component: Integration Client]\nSends SMS messages")
        push_gateway = Server("Push Gateway\n[Component: Integration Client]\nSends push notifications")

        # Internal component interactions
        api_interface >> Edge(label="Uses") >> notification_manager
        event_consumer >> Edge(label="Triggers") >> notification_manager
        
        notification_manager >> Edge(label="Renders with") >> template_engine
        notification_manager >> Edge(label="Schedules via") >> delivery_scheduler
        notification_manager >> Edge(label="Uses") >> notification_preferences
        
        template_engine >> Edge(label="Uses") >> notification_templates
        
        delivery_scheduler >> Edge(label="Sends via") >> email_gateway
        delivery_scheduler >> Edge(label="Sends via") >> sms_gateway
        delivery_scheduler >> Edge(label="Sends via") >> push_gateway
        
        notification_repository >> Edge(label="Persists") >> notification_templates
        notification_repository >> Edge(label="Persists") >> notification_preferences

    # --- External interactions ---
    # From external systems to Notification Service
    other_services >> Edge(label="Direct API calls") >> api_interface
    msg_broker >> Edge(label="Events (OrderCreated, etc.)") >> event_consumer
    admin >> Edge(label="Manages templates") >> api_interface
    
    # From Notification Service to external dependencies
    notification_repository >> Edge(label="Reads/Writes") >> notification_db
    email_gateway >> Edge(label="Sends via") >> email_provider
    sms_gateway >> Edge(label="Sends via") >> sms_provider
    push_gateway >> Edge(label="Sends via") >> push_provider

print(f"Diagram '{diagram_name}' was generated as '{output_filename}.jpg'")
