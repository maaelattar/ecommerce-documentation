from diagrams import Diagram, Cluster, Edge
# Using verified flowchart components
from diagrams.programming.flowchart import PredefinedProcess, Database, Document, StartEnd

# Enhanced Diagram Configuration
diagram_name = "E-Commerce Platform Data Flow Diagram"
output_filename = "data_flow_diagram"

# Overall graph attributes for better layout
graph_attr = {
    "splines": "ortho",         # Orthogonal lines for cleaner appearance
    "nodesep": "0.6",          # Spacing between nodes horizontally
    "ranksep": "0.8",          # Spacing vertically
    "fontsize": "18",          # Large title font
    "fontname": "Arial",        # Clean font
    "bgcolor": "white",         # White background for better contrast
    "concentrate": "false",     # Don't merge edges - keep data flows distinct
    "compound": "true",         # Allow edges between clusters
    "pad": "0.75",             # Padding around the diagram
    "rankdir": "LR",           # Left to right layout (instead of top-bottom)
    "newrank": "true",         # Use new rank algorithm to help with alignment
    "overlap": "false",        # Prevent node overlap
    "outputorder": "edgesfirst" # Draw edges first for cleaner appearance
}

# Edge attributes for better readability
edge_attr = {
    "fontsize": "9",          # Smaller edge label font
    "fontname": "Arial",       
    "fontcolor": "#444444",
    "penwidth": "1.2",         # Slightly thicker lines
    "constraint": "true",      # Maintain hierarchical constraints
    "tailclip": "true",       # Clip tail of edge at node
    "headclip": "true"        # Clip head of edge at node
}

# Default attributes for all nodes
node_attr = {
    "fontsize": "11",
    "fontname": "Arial",
    "margin": "0.2,0.1"
}

# Node styling
entity_attrs = {"shape": "oval", "style": "filled", "fillcolor": "#e6f2ff", 
              "color": "#1168bd", "penwidth": "2.0"}
              
process_attrs = {"shape": "box", "style": "filled", "fillcolor": "#fff8dc", 
               "color": "#ff8c00", "penwidth": "2.0"}
               
datastore_attrs = {"shape": "cylinder", "style": "filled", "fillcolor": "#e6ffe6", 
                 "color": "#2d882d", "penwidth": "2.0"}
                 
external_attrs = {"shape": "component", "style": "filled", "fillcolor": "#f2f2f2", 
                "color": "#333333", "penwidth": "2.0"}

# Edge styling by type
normal_edge = {"color": "#555555", "penwidth": "1.0"}
data_store_edge = {"color": "#2d882d", "penwidth": "1.2"}
external_edge = {"color": "#1168bd", "penwidth": "1.2"}
event_edge = {"color": "#ff8c00", "style": "dashed", "penwidth": "1.2"}



# Add invisible edges to enforce proper hierarchy and prevent floating labels
def add_invisible_edge(node1, node2):
    return node1 >> Edge(style="invis", constraint="true") >> node2

# Add invisible rank nodes to help with layout
def create_rank_node():
    return StartEnd("", shape="point", width="0.01", height="0.01", style="invis")

with Diagram(diagram_name, show=False, filename=output_filename, graph_attr=graph_attr, 
             edge_attr=edge_attr, node_attr=node_attr, direction="LR", outformat="jpg"):

    # Group related components using clusters for better organization
    with Cluster("External\nEntities", graph_attr={"style": "dashed", "color": "#1168bd", 
                                         "bgcolor": "#f0f5ff40", "penwidth": "1.5"}):
        user_entity = StartEnd("Customer", **entity_attrs)
        admin_entity = StartEnd("Administrator", **entity_attrs)
    
    # Group processes by functional area for better organization
    with Cluster("Core Processes", graph_attr={"style": "dashed", "color": "#ff8c00", 
                                              "bgcolor": "#fff8f040", "penwidth": "1.5"}):
        # User-related processes
        with Cluster("User Management", graph_attr={"style": "dotted", "color": "#ff8c00", 
                                                "bgcolor": "transparent"}):
            auth_process = PredefinedProcess("Authentication\nProcess", **process_attrs)
            user_process = PredefinedProcess("User Management\nProcess", **process_attrs)
        
        # Product-related processes
        with Cluster("Product & Cart", graph_attr={"style": "dotted", "color": "#ff8c00", 
                                              "bgcolor": "transparent"}):
            catalog_process = PredefinedProcess("Catalog Management\nProcess", **process_attrs)
            cart_process = PredefinedProcess("Cart Management\nProcess", **process_attrs)
        
        # Order-related processes
        with Cluster("Order Processing", graph_attr={"style": "dotted", "color": "#ff8c00", 
                                               "bgcolor": "transparent"}):
            order_process = PredefinedProcess("Order Management\nProcess", **process_attrs)
            payment_process = PredefinedProcess("Payment\nProcessing", **process_attrs)
            fulfill_process = PredefinedProcess("Order Fulfillment\nProcess", **process_attrs)
        
        # Notification process
        notify_process = PredefinedProcess("Notification\nProcess", **process_attrs)
    
    with Cluster("Data\nStores", graph_attr={"style": "dashed", "color": "#2d882d", 
                                         "bgcolor": "#f0fff040", "penwidth": "1.5"}):
        user_db = Database("User DB", **datastore_attrs)
        product_db = Database("Product DB", **datastore_attrs)
        order_db = Database("Order DB", **datastore_attrs)
        payment_db = Database("Payment DB", **datastore_attrs)
    
    with Cluster("External\nSystems", graph_attr={"style": "dashed", "color": "#333333", 
                                            "bgcolor": "#f8f8f840", "penwidth": "1.5"}):
        idp = Document("Identity\nProvider", **external_attrs)
        payment_gw = Document("Payment\nGateway", **external_attrs)
        shipping_api = Document("Shipping\nProvider API", **external_attrs)
        email_service = Document("Email\nService", **external_attrs)

    # Create a few invisible anchor points to help with layout
    anchor1 = create_rank_node()
    anchor2 = create_rank_node()
    
    # Data flows - User authentication & profile (styled edges by category)
    user_entity >> Edge(label="Login", **normal_edge) >> auth_process
    auth_process >> Edge(label="Auth token", **normal_edge) >> user_entity
    auth_process >> Edge(label="Verify", **external_edge) >> idp
    user_entity >> Edge(label="Register", **normal_edge) >> user_process
    user_process >> Edge(label="Store profile", **data_store_edge) >> user_db
    
    # Data flows - Product browsing with simplified labels
    user_entity >> Edge(label="Browse", **normal_edge) >> catalog_process
    catalog_process >> Edge(label="Products", **normal_edge) >> user_entity
    catalog_process >> Edge(label="Query", **data_store_edge) >> product_db
    admin_entity >> Edge(label="Manage", **normal_edge) >> catalog_process
    
    # Data flows - Cart management with simplified labels
    user_entity >> Edge(label="Add item", **normal_edge) >> cart_process
    cart_process >> Edge(label="Show cart", **normal_edge) >> user_entity
    cart_process >> Edge(label="Check stock", **data_store_edge) >> product_db
    cart_process >> Edge(label="Save cart", **data_store_edge) >> order_db
    
    # Data flows - Order creation with simpler labels
    user_entity >> Edge(label="Place order", **normal_edge, minlen="2") >> order_process
    cart_process >> Edge(label="Cart data", **normal_edge, minlen="1") >> order_process
    order_process >> Edge(label="Save order", **data_store_edge, minlen="1") >> order_db
    order_process >> Edge(label="Confirm", **normal_edge, minlen="1") >> user_entity
    order_process >> Edge(label="Process payment", **normal_edge, minlen="1") >> payment_process
    
    # Data flows - Payment with highlighted external interaction
    payment_process >> Edge(label="Auth request", **external_edge, minlen="1") >> payment_gw
    payment_gw >> Edge(label="Authorize", **external_edge, minlen="1") >> payment_process
    payment_process >> Edge(label="Record", **data_store_edge, minlen="1") >> payment_db
    payment_process >> Edge(label="Status", **normal_edge, minlen="1") >> order_process
    
    # Data flows - Order events using event edges
    order_process >> Edge(label="Order created", **event_edge, minlen="1") >> notify_process
    payment_process >> Edge(label="Payment complete", **event_edge, minlen="1") >> notify_process
    
    # Data flows - Fulfillment with cleaner organization
    admin_entity >> Edge(label="Manage", **normal_edge, minlen="1") >> fulfill_process
    fulfill_process >> Edge(label="Order info", **data_store_edge, minlen="1") >> order_db
    fulfill_process >> Edge(label="Update status", **data_store_edge, minlen="1") >> order_db
    fulfill_process >> Edge(label="Ship request", **external_edge, minlen="1") >> shipping_api
    shipping_api >> Edge(label="Ship label", **external_edge, minlen="1") >> fulfill_process
    
    # Data flows - Inventory update
    order_process >> Edge(label="Update inventory", **data_store_edge, minlen="1") >> product_db
    
    # Data flows - Notifications with clear external system interaction
    fulfill_process >> Edge(label="Ship event", **event_edge, minlen="1") >> notify_process
    notify_process >> Edge(label="Send email", **external_edge, minlen="1") >> email_service
    email_service >> Edge(label="Deliver", **external_edge, minlen="1") >> user_entity
    
    # Add some invisible edges to help with layout and prevent floating labels
    add_invisible_edge(anchor1, order_process)
    add_invisible_edge(anchor1, cart_process)
    add_invisible_edge(anchor2, payment_db)
    add_invisible_edge(anchor2, product_db)

print(f"Enhanced diagram '{diagram_name}' generation initiated. Output: '{output_filename}.jpg'")
print("\nKey enhancements:")
print("- Left-to-right layout for better flow visualization")
print("- Functional clustering of related processes")
print("- Styled nodes with distinctive shapes and colors")
print("- Simplified, more readable connection labels")
print("- Added event flow as a distinct connection type")
print("- Improved background colors and contrast")
print("- Better spacing and organization of components")
