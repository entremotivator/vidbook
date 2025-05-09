import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import json
import os
import uuid
import io
import requests
import time
import hashlib
import hmac
import re
import matplotlib.pyplot as plt
import seaborn as sns
from github import Github
from github import InputFileContent
import xlrd
import openpyxl
from PIL import Image
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="Videmi Services Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'clients' not in st.session_state:
    st.session_state.clients = {}
    
    # Add sample client - Dajo Curacao
    st.session_state.clients["dajo-curacao"] = {
        "id": "dajo-curacao",
        "name": "Dajo Curacao",
        "contact_person": "John Doe",
        "email": "contact@dajocuracao.com",
        "phone": "+123456789",
        "address": "Willemstad, Curacao",
        "service_type": "Property Management",
        "notes": "Vacation rental properties",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reservations": []
    }

if 'current_client' not in st.session_state:
    st.session_state.current_client = None

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "dashboard"

if 'users' not in st.session_state:
    # Create some default users (in a real app, this would be in a database)
    # Format: username: {password_hash, role, name, email}
    st.session_state.users = {
        "admin": {
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "admin",
            "name": "Admin User",
            "email": "admin@videmiservices.com"
        },
        "manager": {
            "password_hash": hashlib.sha256("manager123".encode()).hexdigest(),
            "role": "manager",
            "name": "Manager User",
            "email": "manager@videmiservices.com"
        },
        "staff": {
            "password_hash": hashlib.sha256("staff123".encode()).hexdigest(),
            "role": "staff",
            "name": "Staff User",
            "email": "staff@videmiservices.com"
        }
    }

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'github_token' not in st.session_state:
    st.session_state.github_token = None

if 'github_repo' not in st.session_state:
    st.session_state.github_repo = None

if 'imported_data' not in st.session_state:
    st.session_state.imported_data = None

if 'import_history' not in st.session_state:
    st.session_state.import_history = []

if 'export_history' not in st.session_state:
    st.session_state.export_history = []

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

if 'activity_log' not in st.session_state:
    st.session_state.activity_log = []

# Helper functions
def log_activity(activity_type, description, user=None):
    """Log user activity"""
    if user is None and st.session_state.current_user:
        user = st.session_state.current_user
    
    st.session_state.activity_log.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "type": activity_type,
        "description": description
    })

def add_notification(message, type="info"):
    """Add a notification to the session state"""
    st.session_state.notifications.append({
        "message": message,
        "type": type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    })

def save_data_to_github(data, filename, commit_message):
    """Save data to GitHub repository"""
    if not st.session_state.github_token or not st.session_state.github_repo:
        st.error("GitHub integration not configured. Please set up GitHub in Settings.")
        return False
    
    try:
        # Initialize GitHub client
        g = Github(st.session_state.github_token)
        repo = g.get_repo(st.session_state.github_repo)
        
        # Convert data to JSON
        json_data = json.dumps(data, indent=2, default=str)
        
        # Check if file exists
        try:
            contents = repo.get_contents(filename)
            # Update file
            repo.update_file(
                contents.path,
                commit_message,
                json_data,
                contents.sha
            )
        except:
            # Create file
            repo.create_file(
                filename,
                commit_message,
                json_data
            )
        
        log_activity("github", f"Saved data to GitHub: {filename}")
        add_notification(f"Successfully saved data to GitHub: {filename}", "success")
        return True
    
    except Exception as e:
        st.error(f"Error saving to GitHub: {e}")
        add_notification(f"Failed to save data to GitHub: {str(e)}", "error")
        return False

def load_data_from_github(filename):
    """Load data from GitHub repository"""
    if not st.session_state.github_token or not st.session_state.github_repo:
        st.error("GitHub integration not configured. Please set up GitHub in Settings.")
        return None
    
    try:
        # Initialize GitHub client
        g = Github(st.session_state.github_token)
        repo = g.get_repo(st.session_state.github_repo)
        
        # Get file contents
        contents = repo.get_contents(filename)
        data = json.loads(contents.decoded_content.decode())
        
        log_activity("github", f"Loaded data from GitHub: {filename}")
        add_notification(f"Successfully loaded data from GitHub: {filename}", "success")
        return data
    
    except Exception as e:
        st.error(f"Error loading from GitHub: {e}")
        add_notification(f"Failed to load data from GitHub: {str(e)}", "error")
        return None

def save_data():
    """Save data to a file or GitHub"""
    try:
        # Convert datetime objects to strings for JSON serialization
        data = {
            "clients": st.session_state.clients,
            "users": st.session_state.users,
            "activity_log": st.session_state.activity_log,
            "import_history": st.session_state.import_history,
            "export_history": st.session_state.export_history
        }
        
        # Save to GitHub if configured
        if st.session_state.github_token and st.session_state.github_repo:
            success = save_data_to_github(
                data,
                "videmi_services_data.json",
                f"Update data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if success:
                return True
        
        # Otherwise, just show success message (in a real app, save to database)
        st.success("Data saved successfully!")
        log_activity("data", "Saved application data")
        return True
    
    except Exception as e:
        st.error(f"Error saving data: {e}")
        add_notification(f"Failed to save data: {str(e)}", "error")
        return False

def load_data():
    """Load data from a file or GitHub"""
    try:
        # Load from GitHub if configured
        if st.session_state.github_token and st.session_state.github_repo:
            data = load_data_from_github("videmi_services_data.json")
            if data:
                st.session_state.clients = data.get("clients", {})
                st.session_state.users = data.get("users", st.session_state.users)
                st.session_state.activity_log = data.get("activity_log", [])
                st.session_state.import_history = data.get("import_history", [])
                st.session_state.export_history = data.get("export_history", [])
                return True
        
        # In a real app, you would load from a database
        # For demo, we'll use the session state data
        log_activity("data", "Loaded application data")
        return True
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        add_notification(f"Failed to load data: {str(e)}", "error")
        return False

def get_csv_download_link(df, filename="videmi_data.csv"):
    """Generate a download link for a CSV file"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-button">Download CSV File</a>'
    return href

def get_excel_download_link(df, filename="videmi_data.xlsx"):
    """Generate a download link for an Excel file"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    
    b64 = base64.b64encode(output.getvalue()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="download-button">Download Excel File</a>'
    return href

def format_currency(amount):
    """Format a number as currency"""
    return f"${amount:.2f}"

def verify_password(username, password):
    """Verify a user's password"""
    if username not in st.session_state.users:
        return False
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == st.session_state.users[username]["password_hash"]

def has_permission(required_role):
    """Check if the current user has the required role"""
    if not st.session_state.authenticated or not st.session_state.current_user:
        return False
    
    user_role = st.session_state.users[st.session_state.current_user]["role"]
    
    # Role hierarchy: admin > manager > staff
    if required_role == "admin":
        return user_role == "admin"
    elif required_role == "manager":
        return user_role in ["admin", "manager"]
    elif required_role == "staff":
        return user_role in ["admin", "manager", "staff"]
    
    return False

def parse_csv(file):
    """Parse a CSV file and return a DataFrame"""
    try:
        df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Error parsing CSV file: {e}")
        return None

def parse_excel(file):
    """Parse an Excel file and return a DataFrame"""
    try:
        df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Error parsing Excel file: {e}")
        return None

def import_reservations_from_df(df, client_id):
    """Import reservations from a DataFrame"""
    if client_id not in st.session_state.clients:
        st.error(f"Client with ID {client_id} not found.")
        return False
    
    try:
        # Check required columns
        required_columns = ["property_name", "check_in_date", "check_out_date"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            return False
        
        # Process each row
        imported_count = 0
        for _, row in df.iterrows():
            # Generate a unique ID for the reservation
            reservation_id = f"res-{uuid.uuid4()}"
            
            # Create reservation dictionary
            new_reservation = {
                "id": reservation_id,
                "property_name": row.get("property_name", ""),
                "guest_name": row.get("guest_name", ""),
                "guest_email": row.get("guest_email", ""),
                "guest_phone": row.get("guest_phone", ""),
                "check_in_date": row.get("check_in_date", ""),
                "check_out_date": row.get("check_out_date", ""),
                "num_guests": row.get("num_guests", 1),
                "client_profile": row.get("client_profile", "Regular Stay"),
                "notes": row.get("notes", ""),
                "status": row.get("status", "Active"),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "imported": True
            }
            
            # Add to the client's reservations
            if "reservations" not in st.session_state.clients[client_id]:
                st.session_state.clients[client_id]["reservations"] = []
            
            st.session_state.clients[client_id]["reservations"].append(new_reservation)
            imported_count += 1
        
        # Log the import
        st.session_state.import_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": st.session_state.current_user,
            "client_id": client_id,
            "client_name": st.session_state.clients[client_id]["name"],
            "count": imported_count,
            "file_type": "CSV/Excel"
        })
        
        log_activity("import", f"Imported {imported_count} reservations for client {st.session_state.clients[client_id]['name']}")
        add_notification(f"Successfully imported {imported_count} reservations", "success")
        
        return True
    
    except Exception as e:
        st.error(f"Error importing reservations: {e}")
        add_notification(f"Failed to import reservations: {str(e)}", "error")
        return False

def import_clients_from_df(df):
    """Import clients from a DataFrame"""
    try:
        # Check required columns
        required_columns = ["name", "contact_person", "email"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            return False
        
        # Process each row
        imported_count = 0
        for _, row in df.iterrows():
            # Generate a unique ID for the client
            client_name = row.get("name", "")
            client_id = client_name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
            
            # Create client dictionary
            new_client = {
                "id": client_id,
                "name": client_name,
                "contact_person": row.get("contact_person", ""),
                "email": row.get("email", ""),
                "phone": row.get("phone", ""),
                "address": row.get("address", ""),
                "service_type": row.get("service_type", ""),
                "notes": row.get("notes", ""),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reservations": [],
                "imported": True
            }
            
            # Add to clients
            st.session_state.clients[client_id] = new_client
            imported_count += 1
        
        # Log the import
        st.session_state.import_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": st.session_state.current_user,
            "count": imported_count,
            "file_type": "CSV/Excel",
            "type": "clients"
        })
        
        log_activity("import", f"Imported {imported_count} clients")
        add_notification(f"Successfully imported {imported_count} clients", "success")
        
        return True
    
    except Exception as e:
        st.error(f"Error importing clients: {e}")
        add_notification(f"Failed to import clients: {str(e)}", "error")
        return False

# Authentication in sidebar
def sidebar_auth():
    with st.sidebar:
        st.title("Videmi Services")
        
        # Logo
        st.image("https://via.placeholder.com/150x150.png?text=Videmi+Logo", width=150)
        
        # Authentication
        if not st.session_state.authenticated:
            st.subheader("Login")
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if verify_password(username, password):
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        log_activity("auth", f"User logged in: {username}", username)
                        add_notification(f"Welcome back, {st.session_state.users[username]['name']}!", "success")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            # Demo credentials
            with st.expander("Demo Credentials"):
                st.write("**Admin User**")
                st.write("Username: admin")
                st.write("Password: admin123")
                
                st.write("**Manager User**")
                st.write("Username: manager")
                st.write("Password: manager123")
                
                st.write("**Staff User**")
                st.write("Username: staff")
                st.write("Password: staff123")
        else:
            # Show user info
            user_info = st.session_state.users[st.session_state.current_user]
            st.write(f"**Logged in as:** {user_info['name']}")
            st.write(f"**Role:** {user_info['role'].capitalize()}")
            
            # Navigation
            st.subheader("Navigation")
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.active_tab = "dashboard"
                st.session_state.current_client = None
                st.rerun()
            
            if st.button("👥 Clients", use_container_width=True):
                st.session_state.active_tab = "clients"
                st.session_state.current_client = None
                st.rerun()
                
            if st.button("🗓️ Reservations", use_container_width=True):
                st.session_state.active_tab = "reservations"
                st.session_state.current_client = None
                st.rerun()
            
            if st.button("📤 Import/Export", use_container_width=True):
                st.session_state.active_tab = "import_export"
                st.session_state.current_client = None
                st.rerun()
                
            if st.button("📈 Reports", use_container_width=True):
                st.session_state.active_tab = "reports"
                st.session_state.current_client = None
                st.rerun()
                
            if has_permission("admin") and st.button("⚙️ Settings", use_container_width=True):
                st.session_state.active_tab = "settings"
                st.session_state.current_client = None
                st.rerun()
            
            # Client selector (if there are clients)
            if st.session_state.clients:
                st.divider()
                st.subheader("Select Client")
                
                client_options = ["All Clients"] + [client["name"] for client_id, client in st.session_state.clients.items()]
                selected_client = st.selectbox("", client_options)
                
                if selected_client != "All Clients":
                    # Find the client ID by name
                    for client_id, client in st.session_state.clients.items():
                        if client["name"] == selected_client:
                            st.session_state.current_client = client_id
                            break
                else:
                    st.session_state.current_client = None
                
                if st.button("View Selected Client", use_container_width=True):
                    if st.session_state.current_client:
                        st.session_state.active_tab = "client_details"
                        st.rerun()
            
            # Notifications
            unread_count = sum(1 for n in st.session_state.notifications if not n["read"])
            notification_label = f"🔔 Notifications ({unread_count})" if unread_count > 0 else "🔔 Notifications"
            
            with st.expander(notification_label):
                if not st.session_state.notifications:
                    st.write("No notifications")
                else:
                    for i, notification in enumerate(st.session_state.notifications):
                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                if notification["type"] == "success":
                                    st.success(notification["message"])
                                elif notification["type"] == "error":
                                    st.error(notification["message"])
                                elif notification["type"] == "warning":
                                    st.warning(notification["message"])
                                else:
                                    st.info(notification["message"])
                                
                                st.caption(f"Time: {notification['timestamp']}")
                            
                            with col2:
                                if not notification["read"]:
                                    if st.button("Mark Read", key=f"read_{i}"):
                                        st.session_state.notifications[i]["read"] = True
                                        st.experimental_rerun()
                    
                    if st.button("Clear All"):
                        st.session_state.notifications = []
                        st.experimental_rerun()
            
            # Logout button
            st.divider()
            if st.button("Logout", use_container_width=True):
                log_activity("auth", f"User logged out: {st.session_state.current_user}")
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.experimental_rerun()

# Main application
def main_app():
    # Show authentication in sidebar
    sidebar_auth()
    
    # Main content area
    if not st.session_state.authenticated:
        # Show welcome page for non-authenticated users
        st.title("Welcome to Videmi Services Management System")
        
        st.write("""
        This comprehensive management system helps Videmi Services manage all clients, 
        reservations, and business operations efficiently. Please log in using the sidebar 
        to access the system.
        """)
        
        # Features
        st.subheader("Key Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 👥 Client Management")
            st.write("Manage all your clients in one place with detailed profiles and history.")
        
        with col2:
            st.markdown("### 🗓️ Reservation System")
            st.write("Track all reservations across properties with comprehensive filtering and reporting.")
        
        with col3:
            st.markdown("### 📊 Business Analytics")
            st.write("Gain insights into your business performance with detailed reports and visualizations.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📤 Import/Export")
            st.write("Easily import and export data from CSV and Excel files with GitHub integration.")
        
        with col2:
            st.markdown("### 🔒 User Management")
            st.write("Control access with role-based permissions for administrators, managers, and staff.")
        
        with col3:
            st.markdown("### 📱 Mobile Friendly")
            st.write("Access your data from any device with a responsive, mobile-friendly interface.")
        
        # Demo image
        st.image("https://via.placeholder.com/1200x400.png?text=Videmi+Services+Management+System", use_column_width=True)
        
        return
    
    # For authenticated users, show the appropriate content
    if st.session_state.active_tab == "dashboard":
        show_dashboard()
    elif st.session_state.active_tab == "clients":
        show_clients()
    elif st.session_state.active_tab == "client_details":
        show_client_details()
    elif st.session_state.active_tab == "reservations":
        show_reservations()
    elif st.session_state.active_tab == "import_export":
        show_import_export()
    elif st.session_state.active_tab == "reports":
        show_reports()
    elif st.session_state.active_tab == "settings":
        if has_permission("admin"):
            show_settings()
        else:
            st.error("You don't have permission to access Settings. Please contact an administrator.")
            st.session_state.active_tab = "dashboard"
            st.experimental_rerun()

# Dashboard page
def show_dashboard():
    st.title("Dashboard")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clients", len(st.session_state.clients))
    
    # Count total reservations across all clients
    total_reservations = sum(len(client.get("reservations", [])) for client in st.session_state.clients.values())
    
    with col2:
        st.metric("Total Reservations", total_reservations)
    
    # Calculate upcoming reservations (next 7 days)
    today = datetime.now().date()
    upcoming_count = 0
    
    for client in st.session_state.clients.values():
        for reservation in client.get("reservations", []):
            try:
                check_in_date = datetime.strptime(reservation.get("check_in_date", ""), "%Y-%m-%d").date()
                if today <= check_in_date <= today + timedelta(days=7):
                    upcoming_count += 1
            except:
                pass
    
    with col3:
        st.metric("Upcoming (7 days)", upcoming_count)
    
    with col4:
        # This would be calculated from actual data in a real app
        st.metric("Monthly Revenue", "$5,240", delta="+12%")
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Reservations by Client")
        
        # Prepare data for the chart
        client_names = []
        reservation_counts = []
        
        for client_id, client in st.session_state.clients.items():
            client_names.append(client["name"])
            reservation_counts.append(len(client.get("reservations", [])))
        
        # Create a bar chart
        if client_names:
            fig = px.bar(
                x=client_names,
                y=reservation_counts,
                labels={"x": "Client", "y": "Reservations"},
                color=reservation_counts,
                color_continuous_scale="Viridis",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No client data available")
    
    with col2:
        st.subheader("Upcoming Reservations")
        
        # Create a calendar-like view for upcoming reservations
        upcoming_reservations = []
        
        for client_id, client in st.session_state.clients.items():
            for reservation in client.get("reservations", []):
                try:
                    check_in_date = datetime.strptime(reservation.get("check_in_date", ""), "%Y-%m-%d").date()
                    if today <= check_in_date <= today + timedelta(days=30):
                        upcoming_reservations.append({
                            "client": client["name"],
                            "property": reservation.get("property_name", ""),
                            "check_in": check_in_date,
                            "check_out": datetime.strptime(reservation.get("check_out_date", ""), "%Y-%m-%d").date(),
                            "guests": reservation.get("num_guests", 0)
                        })
                except:
                    pass
        
        # Sort by check-in date
        upcoming_reservations.sort(key=lambda x: x["check_in"])
        
        if upcoming_reservations:
            # Convert to DataFrame for display
            df = pd.DataFrame(upcoming_reservations)
            df["check_in"] = df["check_in"].astype(str)
            df["check_out"] = df["check_out"].astype(str)
            df.columns = ["Client", "Property", "Check-in", "Check-out", "Guests"]
            
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("No upcoming reservations in the next 30 days")
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Show actual activity log
    recent_activities = sorted(
        st.session_state.activity_log,
        key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"),
        reverse=True
    )[:10]  # Get the 10 most recent activities
    
    if recent_activities:
        for activity in recent_activities:
            st.markdown(f"**{activity['timestamp']}** ({activity['user']}): {activity['description']}")
    else:
        st.info("No recent activity")
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Add New Client", use_container_width=True):
            st.session_state.active_tab = "clients"
            st.experimental_rerun()
    
    with col2:
        if st.button("Add New Reservation", use_container_width=True):
            st.session_state.active_tab = "reservations"
            st.experimental_rerun()
    
    with col3:
        if st.button("Import Data", use_container_width=True):
            st.session_state.active_tab = "import_export"
            st.experimental_rerun()
    
    with col4:
        if st.button("Generate Reports", use_container_width=True):
            st.session_state.active_tab = "reports"
            st.experimental_rerun()

# Clients page
def show_clients():
    st.title("Client Management")
    
    # Create tabs for viewing and adding clients
    tab1, tab2 = st.tabs(["View Clients", "Add New Client"])
    
    with tab1:
        if not st.session_state.clients:
            st.info("No clients added yet. Use the 'Add New Client' tab to add your first client.")
        else:
            # Search and filter
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_term = st.text_input("Search Clients", "")
            
            with col2:
                filter_service = st.selectbox(
                    "Filter by Service Type",
                    options=["All"] + list(set(client["service_type"] for client in st.session_state.clients.values() if "service_type" in client))
                )
            
            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    options=["Name (A-Z)", "Name (Z-A)", "Newest First", "Oldest First", "Most Reservations"]
                )
            
            # Apply filters and search
            filtered_clients = {}
            
            for client_id, client in st.session_state.clients.items():
                # Apply search
                if search_term and search_term.lower() not in client["name"].lower() and search_term.lower() not in client.get("contact_person", "").lower():
                    continue
                
                # Apply service filter
                if filter_service != "All" and client.get("service_type", "") != filter_service:
                    continue
                
                filtered_clients[client_id] = client
            
            # Apply sorting
            sorted_client_ids = list(filtered_clients.keys())
            
            if sort_by == "Name (A-Z)":
                sorted_client_ids.sort(key=lambda x: filtered_clients[x]["name"])
            elif sort_by == "Name (Z-A)":
                sorted_client_ids.sort(key=lambda x: filtered_clients[x]["name"], reverse=True)
            elif sort_by == "Newest First":
                sorted_client_ids.sort(key=lambda x: filtered_clients[x].get("created_at", ""), reverse=True)
            elif sort_by == "Oldest First":
                sorted_client_ids.sort(key=lambda x: filtered_clients[x].get("created_at", ""))
            elif sort_by == "Most Reservations":
                sorted_client_ids.sort(key=lambda x: len(filtered_clients[x].get("reservations", [])), reverse=True)
            
            # Display clients in a grid
            if not filtered_clients:
                st.info("No clients match your search criteria.")
            else:
                st.write(f"Showing {len(filtered_clients)} clients")
                
                # Display in a grid
                for i in range(0, len(sorted_client_ids), 3):
                    cols = st.columns(3)
                    
                    for j in range(3):
                        if i + j < len(sorted_client_ids):
                            client_id = sorted_client_ids[i + j]
                            client = filtered_clients[client_id]
                            
                            with cols[j]:
                                with st.container(border=True):
                                    st.subheader(client["name"])
                                    st.write(f"**Contact:** {client.get('contact_person', 'N/A')}")
                                    st.write(f"**Email:** {client.get('email', 'N/A')}")
                                    st.write(f"**Service:** {client.get('service_type', 'N/A')}")
                                    st.write(f"**Reservations:** {len(client.get('reservations', []))}")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("View Details", key=f"view_{client_id}"):
                                            st.session_state.current_client = client_id
                                            st.session_state.active_tab = "client_details"
                                            st.experimental_rerun()
                                    
                                    with col2:
                                        if st.button("Manage", key=f"manage_{client_id}"):
                                            st.session_state.current_client = client_id
                                            st.session_state.active_tab = "reservations"
                                            st.experimental_rerun()
    
    with tab2:
        st.subheader("Add New Client")
        
        with st.form("add_client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                client_name = st.text_input("Client Name*")
                contact_person = st.text_input("Contact Person*")
                email = st.text_input("Email Address*")
                phone = st.text_input("Phone Number")
            
            with col2:
                address = st.text_area("Address")
                service_type = st.selectbox(
                    "Service Type*",
                    options=[
                        "Property Management",
                        "Cleaning Services",
                        "Maintenance",
                        "Vacation Rentals",
                        "Hotel Management",
                        "Other"
                    ]
                )
                
                if service_type == "Other":
                    service_type = st.text_input("Specify Service Type")
            
            notes = st.text_area("Additional Notes")
            
            submitted = st.form_submit_button("Add Client")
            
            if submitted:
                if not client_name or not contact_person or not email:
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    # Generate a unique ID for the client
                    client_id = client_name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
                    
                    # Create client dictionary
                    new_client = {
                        "id": client_id,
                        "name": client_name,
                        "contact_person": contact_person,
                        "email": email,
                        "phone": phone,
                        "address": address,
                        "service_type": service_type,
                        "notes": notes,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "reservations": []
                    }
                    
                    # Add to session state
                    st.session_state.clients[client_id] = new_client
                    save_data()
                    
                    log_activity("client", f"Added new client: {client_name}")
                    add_notification(f"Client '{client_name}' added successfully!", "success")
                    
                    st.success(f"Client '{client_name}' added successfully!")
                    st.session_state.current_client = client_id
                    st.session_state.active_tab = "client_details"
                    st.experimental_rerun()

# Client details page
def show_client_details():
    if not st.session_state.current_client or st.session_state.current_client not in st.session_state.clients:
        st.error("Client not found.")
        st.session_state.active_tab = "clients"
        st.experimental_rerun()
        return
    
    client = st.session_state.clients[st.session_state.current_client]
    
    # Header with client name and back button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title(f"Client: {client['name']}")
    
    with col2:
        if st.button("← Back to Clients", use_container_width=True):
            st.session_state.active_tab = "clients"
            st.experimental_rerun()
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Client Information", "Reservations", "Analytics", "History"])
    
    with tab1:
        # Client information with edit capability
        st.subheader("Client Information")
        
        edit_mode = st.checkbox("Edit Client Information")
        
        if edit_mode:
            # Edit form
            with st.form("edit_client_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    client_name = st.text_input("Client Name*", value=client["name"])
                    contact_person = st.text_input("Contact Person*", value=client.get("contact_person", ""))
                    email = st.text_input("Email Address*", value=client.get("email", ""))
                    phone = st.text_input("Phone Number", value=client.get("phone", ""))
                
                with col2:
                    address = st.text_area("Address", value=client.get("address", ""))
                    service_type = st.selectbox(
                        "Service Type*",
                        options=[
                            "Property Management",
                            "Cleaning Services",
                            "Maintenance",
                            "Vacation Rentals",
                            "Hotel Management",
                            "Other"
                        ],
                        index=["Property Management", "Cleaning Services", "Maintenance", "Vacation Rentals", "Hotel Management", "Other"].index(client.get("service_type", "Property Management")) if client.get("service_type", "") in ["Property Management", "Cleaning Services", "Maintenance", "Vacation Rentals", "Hotel Management", "Other"] else 0
                    )
                    
                    if service_type == "Other":
                        service_type = st.text_input("Specify Service Type", value=client.get("service_type", "") if client.get("service_type", "") not in ["Property Management", "Cleaning Services", "Maintenance", "Vacation Rentals", "Hotel Management"] else "")
                
                notes = st.text_area("Additional Notes", value=client.get("notes", ""))
                
                submitted = st.form_submit_button("Save Changes")
                
                if submitted:
                    if not client_name or not contact_person or not email:
                        st.error("Please fill in all required fields (marked with *)")
                    else:
                        # Update client information
                        client["name"] = client_name
                        client["contact_person"] = contact_person
                        client["email"] = email
                        client["phone"] = phone
                        client["address"] = address
                        client["service_type"] = service_type
                        client["notes"] = notes
                        client["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Save changes
                        st.session_state.clients[st.session_state.current_client] = client
                        save_data()
                        
                        log_activity("client", f"Updated client information: {client_name}")
                        add_notification(f"Client '{client_name}' updated successfully!", "success")
                        
                        st.success(f"Client '{client_name}' updated successfully!")
                        st.experimental_rerun()
        else:
            # Display client information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Client Name:** {client['name']}")
                st.write(f"**Contact Person:** {client.get('contact_person', 'N/A')}")
                st.write(f"**Email:** {client.get('email', 'N/A')}")
                st.write(f"**Phone:** {client.get('phone', 'N/A')}")
            
            with col2:
                st.write(f"**Service Type:** {client.get('service_type', 'N/A')}")
                st.write(f"**Created:** {client.get('created_at', 'N/A')}")
                st.write(f"**Last Updated:** {client.get('updated_at', 'N/A') if 'updated_at' in client else 'Never'}")
                st.write(f"**Total Reservations:** {len(client.get('reservations', []))}")
            
            st.subheader("Address")
            st.write(client.get("address", "No address provided"))
            
            st.subheader("Notes")
            st.write(client.get("notes", "No notes provided"))
        
        # Delete client button (with confirmation)
        st.divider()
        if has_permission("manager"):
            delete_col1, delete_col2 = st.columns([3, 1])
            
            with delete_col1:
                st.write("**Danger Zone**")
                st.write("Deleting a client will permanently remove all associated data, including reservations.")
            
            with delete_col2:
                if st.button("Delete Client", use_container_width=True):
                    st.warning("Are you sure you want to delete this client? This action cannot be undone.")
                    confirm_delete = st.text_input("Type the client name to confirm deletion")
                    
                    if confirm_delete == client["name"]:
                        # Delete the client
                        client_name = client["name"]
                        del st.session_state.clients[st.session_state.current_client]
                        save_data()
                        
                        log_activity("client", f"Deleted client: {client_name}")
                        add_notification(f"Client '{client_name}' deleted successfully!", "success")
                        
                        st.success(f"Client '{client_name}' deleted successfully!")
                        st.session_state.current_client = None
                        st.session_state.active_tab = "clients"
                        st.experimental_rerun()
    
    with tab2:
        # Reservations for this client
        st.subheader("Reservations")
        
        reservations = client.get("reservations", [])
        
        if not reservations:
            st.info("No reservations found for this client.")
            
            if st.button("Add New Reservation"):
                st.session_state.active_tab = "reservations"
                st.experimental_rerun()
        else:
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_status = st.selectbox(
                    "Filter by Status",
                    options=["All", "Upcoming", "Past", "Cancelled"]
                )
            
            with col2:
                # Get unique property names
                property_names = ["All"]
                for reservation in reservations:
                    if "property_name" in reservation and reservation["property_name"] not in property_names:
                        property_names.append(reservation["property_name"])
                
                filter_property = st.selectbox("Filter by Property", options=property_names)
            
            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    options=["Check-in Date (Newest)", "Check-in Date (Oldest)", "Property Name"]
                )
            
            # Apply filters
            filtered_reservations = reservations.copy()
            
            # Filter by status
            today = datetime.now().date()
            if filter_status == "Upcoming":
                filtered_reservations = [
                    r for r in filtered_reservations 
                    if datetime.strptime(r.get("check_in_date", "2099-01-01"), "%Y-%m-%d").date() >= today
                ]
            elif filter_status == "Past":
                filtered_reservations = [
                    r for r in filtered_reservations 
                    if datetime.strptime(r.get("check_out_date", "2000-01-01"), "%Y-%m-%d").date() < today
                ]
            elif filter_status == "Cancelled":
                filtered_reservations = [r for r in filtered_reservations if r.get("status") == "Cancelled"]
            
            # Filter by property
            if filter_property != "All":
                filtered_reservations = [r for r in filtered_reservations if r.get("property_name") == filter_property]
            
            # Sort reservations
            if sort_by == "Check-in Date (Newest)":
                filtered_reservations.sort(key=lambda x: x.get("check_in_date", ""), reverse=True)
            elif sort_by == "Check-in Date (Oldest)":
                filtered_reservations.sort(key=lambda x: x.get("check_in_date", ""))
            elif sort_by == "Property Name":
                filtered_reservations.sort(key=lambda x: x.get("property_name", ""))
            
            # Add new reservation button
            if st.button("Add New Reservation"):
                st.session_state.active_tab = "reservations"
                st.experimental_rerun()
            
            # Display reservations
            if not filtered_reservations:
                st.info("No reservations match your filter criteria.")
            else:
                st.write(f"Showing {len(filtered_reservations)} reservations")
                
                for reservation in filtered_reservations:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.subheader(f"{reservation.get('property_name', 'Unknown Property')}")
                            st.write(f"**Guest:** {reservation.get('guest_name', 'Unknown Guest')}")
                            st.write(f"**Contact:** {reservation.get('guest_email', '')} | {reservation.get('guest_phone', '')}")
                        
                        with col2:
                            st.write(f"**Check-in:** {reservation.get('check_in_date', 'Unknown')}")
                            st.write(f"**Check-out:** {reservation.get('check_out_date', 'Unknown')}")
                            st.write(f"**Guests:** {reservation.get('num_guests', '0')}")
                            st.write(f"**Status:** {reservation.get('status', 'Active')}")
                        
                        with col3:
                            # Action buttons
                            if st.button("View Details", key=f"view_res_{reservation.get('id', '')}"):
                                # In a real app, this would open a detailed view
                                st.info("Detailed view would open here")
                            
                            if st.button("Edit", key=f"edit_res_{reservation.get('id', '')}"):
                                # In a real app, this would open an edit form
                                st.info("Edit form would open here")
                            
                            if reservation.get("status") != "Cancelled" and st.button("Cancel", key=f"cancel_res_{reservation.get('id', '')}"):
                                # Mark the reservation as cancelled
                                for i, res in enumerate(client["reservations"]):
                                    if res.get("id") == reservation.get("id"):
                                        client["reservations"][i]["status"] = "Cancelled"
                                        client["reservations"][i]["cancelled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        client["reservations"][i]["cancelled_by"] = st.session_state.current_user
                                        
                                        save_data()
                                        
                                        log_activity("reservation", f"Cancelled reservation for {reservation.get('property_name', 'Unknown Property')}")
                                        add_notification(f"Reservation cancelled successfully!", "success")
                                        
                                        st.success("Reservation cancelled successfully!")
                                        st.experimental_rerun()
                                        break
    
    with tab3:
        # Analytics for this client
        st.subheader("Client Analytics")
        
        # Calculate metrics
        reservations = client.get("reservations", [])
        total_reservations = len(reservations)
        
        # Active reservations
        active_reservations = len([r for r in reservations if r.get("status") != "Cancelled"])
        
        # Calculate upcoming reservations
        today = datetime.now().date()
        upcoming_reservations = 0
        
        for reservation in reservations:
            try:
                check_in_date = datetime.strptime(reservation.get("check_in_date", ""), "%Y-%m-%d").date()
                if today <= check_in_date and reservation.get("status") != "Cancelled":
                    upcoming_reservations += 1
            except:
                pass
        
        # Calculate total nights
        total_nights = 0
        
        for reservation in reservations:
            try:
                check_in_date = datetime.strptime(reservation.get("check_in_date", ""), "%Y-%m-%d").date()
                check_out_date = datetime.strptime(reservation.get("check_out_date", ""), "%Y-%m-%d").date()
                nights = (check_out_date - check_in_date).days
                total_nights += nights
            except:
                pass
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Reservations", total_reservations)
        
        with col2:
            st.metric("Active Reservations", active_reservations)
        
        with col3:
            st.metric("Upcoming Reservations", upcoming_reservations)
        
        with col4:
            st.metric("Total Nights", total_nights)
        
        # Charts
        if total_reservations > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # Reservations by property
                property_counts = {}
                
                for reservation in reservations:
                    property_name = reservation.get("property_name", "Unknown")
                    if property_name in property_counts:
                        property_counts[property_name] += 1
                    else:
                        property_counts[property_name] = 1
                
                # Create DataFrame for chart
                property_df = pd.DataFrame({
                    "Property": list(property_counts.keys()),
                    "Reservations": list(property_counts.values())
                })
                
                fig = px.bar(
                    property_df,
                    x="Property",
                    y="Reservations",
                    title="Reservations by Property",
                    color="Reservations",
                    color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Reservation status breakdown
                status_counts = {}
                
                for reservation in reservations:
                    status = reservation.get("status", "Active")
                    if status in status_counts:
                        status_counts[status] += 1
                    else:
                        status_counts[status] = 1
                
                # Create DataFrame for chart
                status_df = pd.DataFrame({
                    "Status": list(status_counts.keys()),
                    "Count": list(status_counts.values())
                })
                
                fig = px.pie(
                    status_df,
                    values="Count",
                    names="Status",
                    title="Reservation Status Breakdown",
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Reservations over time
            st.subheader("Reservations Over Time")
            
            # Prepare data
            dates = []
            for reservation in reservations:
                try:
                    created_at = datetime.strptime(reservation.get("created_at", ""), "%Y-%m-%d %H:%M:%S").date()
                    dates.append(created_at)
                except:
                    pass
            
            if dates:
                # Create a date range
                min_date = min(dates)
                max_date = max(dates)
                date_range = pd.date_range(start=min_date, end=max_date)
                
                # Count reservations by date
                date_counts = {}
                for date in date_range:
                    date_str = date.strftime("%Y-%m-%d")
                    date_counts[date_str] = 0
                
                for date in dates:
                    date_str = date.strftime("%Y-%m-%d")
                    if date_str in date_counts:
                        date_counts[date_str] += 1
                
                # Create DataFrame for chart
                date_df = pd.DataFrame({
                    "Date": list(date_counts.keys()),
                    "Reservations": list(date_counts.values())
                })
                
                # Convert Date to datetime
                date_df["Date"] = pd.to_datetime(date_df["Date"])
                
                # Sort by date
                date_df = date_df.sort_values("Date")
                
                # Calculate cumulative sum
                date_df["Cumulative"] = date_df["Reservations"].cumsum()
                
                # Create chart
                fig = px.line(
                    date_df,
                    x="Date",
                    y=["Reservations", "Cumulative"],
                    title="Reservations Over Time",
                    labels={"value": "Count", "Date": "Date", "variable": "Metric"},
                    color_discrete_sequence=["#1f77b4", "#2ca02c"]
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No reservation data available for analytics.")
    
    with tab4:
        # History and activity log for this client
        st.subheader("Client History")
        
        # Filter activity log for this client
        client_activities = [
            activity for activity in st.session_state.activity_log
            if "client" in activity["type"] and client["name"] in activity["description"]
        ]
        
        if not client_activities:
            st.info("No activity history found for this client.")
        else:
            # Sort by timestamp (newest first)
            client_activities.sort(key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"), reverse=True)
            
            # Display activity log
            for activity in client_activities:
                st.write(f"**{activity['timestamp']}** ({activity['user']}): {activity['description']}")

# Reservations page
def show_reservations():
    st.title("Reservation Management")
    
    # Check if a specific client is selected
    client_name = "All Clients"
    if st.session_state.current_client:
        client_name = st.session_state.clients[st.session_state.current_client]["name"]
    
    st.subheader(f"Reservations for {client_name}")
    
    # Create tabs for viewing and adding reservations
    tab1, tab2 = st.tabs(["View Reservations", "Add New Reservation"])
    
    with tab1:
        # Collect all reservations
        all_reservations = []
        
        if st.session_state.current_client:
            # Only show reservations for the selected client
            client = st.session_state.clients[st.session_state.current_client]
            for reservation in client.get("reservations", []):
                reservation_with_client = reservation.copy()
                reservation_with_client["client_name"] = client["name"]
                reservation_with_client["client_id"] = st.session_state.current_client
                all_reservations.append(reservation_with_client)
        else:
            # Show reservations for all clients
            for client_id, client in st.session_state.clients.items():
                for reservation in client.get("reservations", []):
                    reservation_with_client = reservation.copy()
                    reservation_with_client["client_name"] = client["name"]
                    reservation_with_client["client_id"] = client_id
                    all_reservations.append(reservation_with_client)
        
        if not all_reservations:
            st.info("No reservations found. Use the 'Add New Reservation' tab to add your first reservation.")
        else:
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_status = st.selectbox(
                    "Filter by Status",
                    options=["All", "Upcoming", "Past", "Cancelled"]
                )
            
            with col2:
                # Get unique property names
                property_names = ["All"]
                for reservation in all_reservations:
                    if "property_name" in reservation and reservation["property_name"] not in property_names:
                        property_names.append(reservation["property_name"])
                
                filter_property = st.selectbox("Filter by Property", options=property_names)
            
            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    options=["Check-in Date (Newest)", "Check-in Date (Oldest)", "Client Name", "Property Name"]
                )
            
            # Apply filters
            filtered_reservations = all_reservations.copy()
            
            # Filter by status
            today = datetime.now().date()
            if filter_status == "Upcoming":
                filtered_reservations = [
                    r for r in filtered_reservations 
                    if datetime.strptime(r.get("check_in_date", "2099-01-01"), "%Y-%m-%d").date() >= today
                ]
            elif filter_status == "Past":
                filtered_reservations = [
                    r for r in filtered_reservations 
                    if datetime.strptime(r.get("check_out_date", "2000-01-01"), "%Y-%m-%d").date() < today
                ]
            elif filter_status == "Cancelled":
                filtered_reservations = [r for r in filtered_reservations if r.get("status") == "Cancelled"]
            
            # Filter by property
            if filter_property != "All":
                filtered_reservations = [r for r in filtered_reservations if r.get("property_name") == filter_property]
            
            # Sort reservations
            if sort_by == "Check-in Date (Newest)":
                filtered_reservations.sort(key=lambda x: x.get("check_in_date", ""), reverse=True)
            elif sort_by == "Check-in Date (Oldest)":
                filtered_reservations.sort(key=lambda x: x.get("check_in_date", ""))
            elif sort_by == "Client Name":
                filtered_reservations.sort(key=lambda x: x.get("client_name", ""))
            elif sort_by == "Property Name":
                filtered_reservations.sort(key=lambda x: x.get("property_name", ""))
            
            # Display reservations
            if not filtered_reservations:
                st.info("No reservations match your filter criteria.")
            else:
                st.write(f"Showing {len(filtered_reservations)} reservations")
                
                for reservation in filtered_reservations:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.subheader(f"{reservation.get('property_name', 'Unknown Property')}")
                            st.write(f"**Client:** {reservation.get('client_name', 'Unknown Client')}")
                            st.write(f"**Guest:** {reservation.get('guest_name', 'Unknown Guest')}")
                            st.write(f"**Contact:** {reservation.get('guest_email', '')} | {reservation.get('guest_phone', '')}")
                        
                        with col2:
                            st.write(f"**Check-in:** {reservation.get('check_in_date', 'Unknown')}")
                            st.write(f"**Check-out:** {reservation.get('check_out_date', 'Unknown')}")
                            st.write(f"**Guests:** {reservation.get('num_guests', '0')}")
                            st.write(f"**Status:** {reservation.get('status', 'Active')}")
                        
                        with col3:
                            # Action buttons
                            if st.button("View Details", key=f"view_res_{reservation.get('id', '')}"):
                                # In a real app, this would open a detailed view
                                st.info("Detailed view would open here")
                            
                            if st.button("Edit", key=f"edit_res_{reservation.get('id', '')}"):
                                # In a real app, this would open an edit form
                                st.info("Edit form would open here")
                            
                            if reservation.get("status") != "Cancelled" and st.button("Cancel", key=f"cancel_res_{reservation.get('id', '')}"):
                                # Mark the reservation as cancelled
                                client_id = reservation.get("client_id")
                                for i, res in enumerate(st.session_state.clients[client_id]["reservations"]):
                                    if res.get("id") == reservation.get("id"):
                                        st.session_state.clients[client_id]["reservations"][i]["status"] = "Cancelled"
                                        st.session_state.clients[client_id]["reservations"][i]["cancelled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        st.session_state.clients[client_id]["reservations"][i]["cancelled_by"] = st.session_state.current_user
                                        
                                        save_data()
                                        
                                        log_activity("reservation", f"Cancelled reservation for {reservation.get('property_name', 'Unknown Property')}")
                                        add_notification(f"Reservation cancelled successfully!", "success")
                                        
                                        st.success("Reservation cancelled successfully!")
                                        st.experimental_rerun()
                                        break
    
    with tab2:
        st.subheader("Add New Reservation")
        
        # If no client is selected, show a client selector
        if not st.session_state.current_client:
            client_options = [client["name"] for client_id, client in st.session_state.clients.items()]
            selected_client_name = st.selectbox("Select Client", options=client_options)
            
            # Find the client ID by name
            for client_id, client in st.session_state.clients.items():
                if client["name"] == selected_client_name:
                    selected_client_id = client_id
                    break
        else:
            selected_client_id = st.session_state.current_client
        
        with st.form("add_reservation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                property_name = st.text_input("Property Name*")
                guest_name = st.text_input("Guest Name*")
                guest_email = st.text_input("Guest Email")
                guest_phone = st.text_input("Guest Phone")
            
            with col2:
                check_in_date = st.date_input("Check-in Date*")
                check_out_date = st.date_input("Check-out Date*")
                num_guests = st.number_input("Number of Guests*", min_value=1, value=2)
                
                client_profile = st.selectbox(
                    "Client Profile",
                    options=[
                        "Regular Stay",
                        "Long-term Rental",
                        "Business Trip",
                        "Vacation",
                        "Other"
                    ]
                )
            
            notes = st.text_area("Additional Notes")
            
            submitted = st.form_submit_button("Add Reservation")
            
            if submitted:
                if not property_name or not guest_name:
                    st.error("Please fill in all required fields (marked with *)")
                elif check_in_date >= check_out_date:
                    st.error("Check-out date must be after check-in date")
                else:
                    # Generate a unique ID for the reservation
                    reservation_id = f"res-{uuid.uuid4()}"
                    
                    # Create reservation dictionary
                    new_reservation = {
                        "id": reservation_id,
                        "property_name": property_name,
                        "guest_name": guest_name,
                        "guest_email": guest_email,
                        "guest_phone": guest_phone,
                        "check_in_date": check_in_date.strftime("%Y-%m-%d"),
                        "check_out_date": check_out_date.strftime("%Y-%m-%d"),
                        "num_guests": num_guests,
                        "client_profile": client_profile,
                        "notes": notes,
                        "status": "Active",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "created_by": st.session_state.current_user
                    }
                    
                    # Add to the client's reservations
                    if "reservations" not in st.session_state.clients[selected_client_id]:
                        st.session_state.clients[selected_client_id]["reservations"] = []
                    
                    st.session_state.clients[selected_client_id]["reservations"].append(new_reservation)
                    save_data()
                    
                    log_activity("reservation", f"Added new reservation for {property_name}")
                    add_notification(f"Reservation for '{property_name}' added successfully!", "success")
                    
                    st.success(f"Reservation for '{property_name}' added successfully!")
                    st.experimental_rerun()

# Import/Export page
def show_import_export():
    st.title("Import & Export Data")
    
    # Create tabs for different import/export options
    tab1, tab2, tab3, tab4 = st.tabs(["Import Data", "Export Data", "GitHub Integration", "Import History"])
    
    with tab1:
        st.subheader("Import Data")
        
        # Select import type
        import_type = st.selectbox(
            "Select Import Type",
            options=["Reservations", "Clients"]
        )
        
        # Select file type
        file_type = st.selectbox(
            "Select File Type",
            options=["CSV", "Excel"]
        )
        
        # Upload file
        uploaded_file = st.file_uploader(f"Upload {file_type} File", type=["csv", "xlsx", "xls"])
        
        if uploaded_file is not None:
            # Parse file
            if file_type == "CSV":
                df = parse_csv(uploaded_file)
            else:
                df = parse_excel(uploaded_file)
            
            if df is not None:
                st.session_state.imported_data = df
                st.write("Preview of imported data:")
                st.dataframe(df.head(10))
                
                # If importing reservations, select client
                if import_type == "Reservations":
                    client_options = [client["name"] for client_id, client in st.session_state.clients.items()]
                    selected_client_name = st.selectbox("Select Client for Reservations", options=client_options)
                    
                    # Find the client ID by name
                    for client_id, client in st.session_state.clients.items():
                        if client["name"] == selected_client_name:
                            selected_client_id = client_id
                            break
                    
                    if st.button("Import Reservations"):
                        success = import_reservations_from_df(df, selected_client_id)
                        if success:
                            st.success(f"Successfully imported reservations for {selected_client_name}!")
                            save_data()
                            st.session_state.imported_data = None
                            st.experimental_rerun()
                
                # If importing clients
                elif import_type == "Clients":
                    if st.button("Import Clients"):
                        success = import_clients_from_df(df)
                        if success:
                            st.success("Successfully imported clients!")
                            save_data()
                            st.session_state.imported_data = None
                            st.experimental_rerun()
    
    with tab2:
        st.subheader("Export Data")
        
        # Select export type
        export_type = st.selectbox(
            "Select Export Type",
            options=["All Clients", "All Reservations", "Single Client", "Single Client Reservations"]
        )
        
        # Select file format
        file_format = st.selectbox(
            "Select File Format",
            options=["CSV", "Excel"]
        )
        
        # If exporting a single client, select the client
        if export_type in ["Single Client", "Single Client Reservations"]:
            client_options = [client["name"] for client_id, client in st.session_state.clients.items()]
            selected_client_name = st.selectbox("Select Client", options=client_options)
            
            # Find the client ID by name
            for client_id, client in st.session_state.clients.items():
                if client["name"] == selected_client_name:
                    selected_client_id = client_id
                    break
        
        # Generate export
        if st.button("Generate Export"):
            # Prepare data for export
            if export_type == "All Clients":
                # Export all client data
                export_data = []
                for client_id, client in st.session_state.clients.items():
                    client_data = {k: v for k, v in client.items() if k != "reservations"}
                    export_data.append(client_data)
                
                export_df = pd.DataFrame(export_data)
                filename = "all_clients"
            
            elif export_type == "All Reservations":
                # Export all reservation data
                export_data = []
                for client_id, client in st.session_state.clients.items():
                    for reservation in client.get("reservations", []):
                        reservation_data = reservation.copy()
                        reservation_data["client_name"] = client["name"]
                        reservation_data["client_id"] = client_id
                        export_data.append(reservation_data)
                
                export_df = pd.DataFrame(export_data)
                filename = "all_reservations"
            
            elif export_type == "Single Client":
                # Export single client data
                client = st.session_state.clients[selected_client_id]
                client_data = {k: v for k, v in client.items() if k != "reservations"}
                export_df = pd.DataFrame([client_data])
                filename = f"client_{selected_client_name.lower().replace(' ', '_')}"
            
            elif export_type == "Single Client Reservations":
                # Export reservations for a single client
                client = st.session_state.clients[selected_client_id]
                export_data = []
                for reservation in client.get("reservations", []):
                    reservation_data = reservation.copy()
                    reservation_data["client_name"] = client["name"]
                    export_data.append(reservation_data)
                
                export_df = pd.DataFrame(export_data)
                filename = f"reservations_{selected_client_name.lower().replace(' ', '_')}"
            
            # Generate download link
            if file_format == "CSV":
                download_link = get_csv_download_link(export_df, f"{filename}.csv")
            else:
                download_link = get_excel_download_link(export_df, f"{filename}.xlsx")
            
            st.markdown(download_link, unsafe_allow_html=True)
            
            # Log export
            st.session_state.export_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": st.session_state.current_user,
                "type": export_type,
                "format": file_format,
                "filename": filename
            })
            
            log_activity("export", f"Exported {export_type} as {file_format}")
            add_notification(f"Successfully generated {export_type} export!", "success")
            
            save_data()
    
    with tab3:
        st.subheader("GitHub Integration")
        
        # GitHub configuration
        with st.form("github_config_form"):
            github_token = st.text_input("GitHub Personal Access Token", type="password", value=st.session_state.github_token if st.session_state.github_token else "")
            github_repo = st.text_input("GitHub Repository (format: username/repo)", value=st.session_state.github_repo if st.session_state.github_repo else "")
            
            submitted = st.form_submit_button("Save GitHub Configuration")
            
            if submitted:
                st.session_state.github_token = github_token
                st.session_state.github_repo = github_repo
                
                log_activity("settings", "Updated GitHub integration settings")
                add_notification("GitHub configuration updated successfully!", "success")
                
                st.success("GitHub configuration updated successfully!")
        
        # GitHub actions
        if st.session_state.github_token and st.session_state.github_repo:
            st.write("GitHub integration is configured. You can now save and load data from GitHub.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Save Data to GitHub", use_container_width=True):
                    success = save_data()
                    if success:
                        st.success("Data saved to GitHub successfully!")
            
            with col2:
                if st.button("Load Data from GitHub", use_container_width=True):
                    success = load_data()
                    if success:
                        st.success("Data loaded from GitHub successfully!")
                        st.experimental_rerun()
        else:
            st.info("Please configure GitHub integration to enable saving and loading data from GitHub.")
    
    with tab4:
        st.subheader("Import/Export History")
        
        # Create tabs for import and export history
        history_tab1, history_tab2 = st.tabs(["Import History", "Export History"])
        
        with history_tab1:
            if not st.session_state.import_history:
                st.info("No import history found.")
            else:
                # Sort by timestamp (newest first)
                sorted_history = sorted(
                    st.session_state.import_history,
                    key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"),
                    reverse=True
                )
                
                # Display import history
                for item in sorted_history:
                    with st.container(border=True):
                        st.write(f"**Time:** {item['timestamp']}")
                        st.write(f"**User:** {item['user']}")
                        
                        if "type" in item and item["type"] == "clients":
                            st.write(f"**Type:** Client Import")
                            st.write(f"**Count:** {item['count']} clients")
                        else:
                            st.write(f"**Client:** {item.get('client_name', 'Unknown')}")
                            st.write(f"**Count:** {item['count']} reservations")
                        
                        st.write(f"**File Type:** {item['file_type']}")
        
        with history_tab2:
            if not st.session_state.export_history:
                st.info("No export history found.")
            else:
                # Sort by timestamp (newest first)
                sorted_history = sorted(
                    st.session_state.export_history,
                    key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"),
                    reverse=True
                )
                
                # Display export history
                for item in sorted_history:
                    with st.container(border=True):
                        st.write(f"**Time:** {item['timestamp']}")
                        st.write(f"**User:** {item['user']}")
                        st.write(f"**Type:** {item['type']}")
                        st.write(f"**Format:** {item['format']}")
                        st.write(f"**Filename:** {item['filename']}")

# Reports page
def show_reports():
    st.title("Reports & Analytics")
    
    # Report type selector
    report_type = st.selectbox(
        "Select Report Type",
        options=[
            "Reservation Summary",
            "Client Performance",
            "Revenue Analysis",
            "Occupancy Rates",
            "Custom Report"
        ]
    )
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
    
    # Client selector
    client_options = ["All Clients"] + [client["name"] for client_id, client in st.session_state.clients.items()]
    selected_client = st.selectbox("Select Client", options=client_options)
    
    # Generate button
    if st.button("Generate Report"):
        st.divider()
        
        # Display report based on type
        if report_type == "Reservation Summary":
            show_reservation_summary_report(start_date, end_date, selected_client)
        elif report_type == "Client Performance":
            show_client_performance_report(start_date, end_date, selected_client)
        elif report_type == "Revenue Analysis":
            show_revenue_analysis_report(start_date, end_date, selected_client)
        elif report_type == "Occupancy Rates":
            show_occupancy_rates_report(start_date, end_date, selected_client)
        elif report_type == "Custom Report":
            show_custom_report(start_date, end_date, selected_client)

# Report generators
def show_reservation_summary_report(start_date, end_date, selected_client):
    st.subheader("Reservation Summary Report")
    st.write(f"Period: {start_date} to {end_date}")
    
    # Collect reservation data
    reservation_data = []
    
    for client_id, client in st.session_state.clients.items():
        if selected_client == "All Clients" or client["name"] == selected_client:
            for reservation in client.get("reservations", []):
                try:
                    check_in = datetime.strptime(reservation.get("check_in_date", ""), "%Y-%m-%d").date()
                    check_out = datetime.strptime(reservation.get("check_out_date", ""), "%Y-%m-%d").date()
                    
                    # Check if reservation is within the date range
                    if (check_in <= end_date and check_out >= start_date):
                        reservation_data.append({
                            "client": client["name"],
                            "property": reservation.get("property_name", ""),
                            "check_in": check_in,
                            "check_out": check_out,
                            "nights": (check_out - check_in).days,
                            "guests": reservation.get("num_guests", 0),
                            "status": reservation.get("status", "Active")
                        })
                except:
                    pass
    
    if not reservation_data:
        st.info("No reservation data available for the selected period and client.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(reservation_data)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reservations", len(df))
    
    with col2:
        st.metric("Total Nights", df["nights"].sum())
    
    with col3:
        st.metric("Avg. Length of Stay", f"{df['nights'].mean():.1f} nights")
    
    with col4:
        st.metric("Total Guests", df["guests"].sum())
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Reservations by client
        if selected_client == "All Clients":
            client_counts = df["client"].value_counts().reset_index()
            client_counts.columns = ["Client", "Reservations"]
            
            fig = px.bar(
                client_counts,
                x="Client",
                y="Reservations",
                title="Reservations by Client",
                color="Reservations",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Reservations by property
            property_counts = df["property"].value_counts().reset_index()
            property_counts.columns = ["Property", "Reservations"]
            
            fig = px.bar(
                property_counts,
                x="Property",
                y="Reservations",
                title="Reservations by Property",
                color="Reservations",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Reservation status breakdown
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        
        fig = px.pie(
            status_counts,
            values="Count",
            names="Status",
            title="Reservation Status Breakdown",
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed data
    st.subheader("Detailed Reservation Data")
    
    # Format dates for display
    df["check_in"] = df["check_in"].astype(str)
    df["check_out"] = df["check_out"].astype(str)
    
    # Rename columns for display
    display_df = df.copy()
    display_df.columns = ["Client", "Property", "Check-in", "Check-out", "Nights", "Guests", "Status"]
    
    st.dataframe(display_df, use_container_width=True)
    
    # Download link
    st.markdown(get_csv_download_link(display_df, "reservation_summary.csv"), unsafe_allow_html=True)

def show_client_performance_report(start_date, end_date, selected_client):
    st.subheader("Client Performance Report")
    st.write(f"Period: {start_date} to {end_date}")
    
    # In a real app, this would use actual data
    # For demo purposes, we'll generate some sample data
    
    # Generate sample client performance data
    client_data = []
    
    for client_id, client in st.session_state.clients.items():
        if selected_client == "All Clients" or client["name"] == selected_client:
            # Count reservations
            reservation_count = len(client.get("reservations", []))
            
            # Generate random metrics for demo
            revenue = np.random.randint(1000, 10000)
            growth = np.random.uniform(-0.2, 0.5)
            satisfaction = np.random.uniform(3.5, 5.0)
            
            client_data.append({
                "client": client["name"],
                "reservations": reservation_count,
                "revenue": revenue,
                "growth": growth,
                "satisfaction": satisfaction
            })
    
    if not client_data:
        st.info("No client data available for the selected period.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(client_data)
    
    # Performance metrics
    for client_row in client_data:
        with st.container(border=True):
            st.subheader(client_row["client"])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Reservations", client_row["reservations"])
            
            with col2:
                st.metric("Revenue", format_currency(client_row["revenue"]))
            
            with col3:
                st.metric("Growth", f"{client_row['growth']*100:.1f}%", delta=f"{client_row['growth']*100:.1f}%")
            
            with col4:
                st.metric("Satisfaction", f"{client_row['satisfaction']:.1f}/5.0")
    
    # Performance comparison chart
    if len(client_data) > 1:
        st.subheader("Client Performance Comparison")
        
        # Create a radar chart for comparison
        categories = ['Reservations', 'Revenue', 'Growth', 'Satisfaction']
        
        fig = go.Figure()
        
        for client_row in client_data:
            # Normalize values for radar chart
            reservations_norm = client_row["reservations"] / df["reservations"].max()
            revenue_norm = client_row["revenue"] / df["revenue"].max()
            growth_norm = (client_row["growth"] - df["growth"].min()) / (df["growth"].max() - df["growth"].min())
            satisfaction_norm = (client_row["satisfaction"] - 3.5) / 1.5  # Normalize between 3.5 and 5.0
            
            fig.add_trace(go.Scatterpolar(
                r=[reservations_norm, revenue_norm, growth_norm, satisfaction_norm],
                theta=categories,
                fill='toself',
                name=client_row["client"]
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_revenue_analysis_report(start_date, end_date, selected_client):
    st.subheader("Revenue Analysis Report")
    st.write(f"Period: {start_date} to {end_date}")
    
    # In a real app, this would use actual revenue data
    # For demo purposes, we'll generate some sample data
    
    # Generate dates between start and end date
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Generate sample revenue data
    revenue_data = []
    
    for client_id, client in st.session_state.clients.items():
        if selected_client == "All Clients" or client["name"] == selected_client:
            for date in date_range:
                # Generate random revenue for demo
                revenue = np.random.randint(100, 500)
                expenses = np.random.randint(50, 200)
                
                revenue_data.append({
                    "date": date,
                    "client": client["name"],
                    "revenue": revenue,
                    "expenses": expenses,
                    "profit": revenue - expenses
                })
    
    if not revenue_data:
        st.info("No revenue data available for the selected period and client.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(revenue_data)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = df["revenue"].sum()
        st.metric("Total Revenue", format_currency(total_revenue))
    
    with col2:
        total_expenses = df["expenses"].sum()
        st.metric("Total Expenses", format_currency(total_expenses))
    
    with col3:
        total_profit = df["profit"].sum()
        st.metric("Total Profit", format_currency(total_profit))
    
    with col4:
        profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0
        st.metric("Profit Margin", f"{profit_margin:.1f}%")
    
    # Revenue over time chart
    st.subheader("Revenue Over Time")
    
    # Group by date and sum revenue
    daily_revenue = df.groupby("date")[["revenue", "expenses", "profit"]].sum().reset_index()
    
    fig = px.line(
        daily_revenue,
        x="date",
        y=["revenue", "expenses", "profit"],
        title="Daily Revenue, Expenses, and Profit",
        labels={"value": "Amount", "date": "Date", "variable": "Category"},
        color_discrete_sequence=["#2ca02c", "#d62728", "#1f77b4"]
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Revenue by client
    if selected_client == "All Clients":
        st.subheader("Revenue by Client")
        
        # Group by client and sum revenue
        client_revenue = df.groupby("client")[["revenue", "expenses", "profit"]].sum().reset_index()
        
        fig = px.bar(
            client_revenue,
            x="client",
            y=["revenue", "expenses", "profit"],
            title="Revenue, Expenses, and Profit by Client",
            labels={"value": "Amount", "client": "Client", "variable": "Category"},
            barmode="group",
            color_discrete_sequence=["#2ca02c", "#d62728", "#1f77b4"]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed data
    st.subheader("Detailed Revenue Data")
    
    # Group by client and date
    if selected_client == "All Clients":
        grouped_df = df.groupby(["client", "date"])[["revenue", "expenses", "profit"]].sum().reset_index()
    else:
        grouped_df = df.groupby("date")[["revenue", "expenses", "profit"]].sum().reset_index()
    
    # Format dates for display
    grouped_df["date"] = grouped_df["date"].astype(str)
    
    # Format currency columns
    for col in ["revenue", "expenses", "profit"]:
        grouped_df[col] = grouped_df[col].apply(lambda x: format_currency(x))
    
    # Rename columns for display
    if selected_client == "All Clients":
        grouped_df.columns = ["Client", "Date", "Revenue", "Expenses", "Profit"]
    else:
        grouped_df.columns = ["Date", "Revenue", "Expenses", "Profit"]
    
    st.dataframe(grouped_df, use_container_width=True)
    
    # Download link
    st.markdown(get_csv_download_link(grouped_df, "revenue_analysis.csv"), unsafe_allow_html=True)

def show_occupancy_rates_report(start_date, end_date, selected_client):
    st.subheader("Occupancy Rates Report")
    st.write(f"Period: {start_date} to {end_date}")
    
    # In a real app, this would use actual occupancy data
    # For demo purposes, we'll generate some sample data
    
    # Generate sample property data
    property_data = []
    
    for client_id, client in st.session_state.clients.items():
        if selected_client == "All Clients" or client["name"] == selected_client:
            # Generate random properties for demo
            num_properties = max(1, len(client.get("reservations", [])) // 2)
            
            for i in range(num_properties):
                property_name = f"Property {i+1}"
                
                # Generate random occupancy data
                total_days = (end_date - start_date).days + 1
                occupied_days = np.random.randint(0, total_days + 1)
                occupancy_rate = (occupied_days / total_days) * 100
                
                # Generate random revenue
                avg_daily_rate = np.random.randint(80, 300)
                revenue = occupied_days * avg_daily_rate
                
                property_data.append({
                    "client": client["name"],
                    "property": property_name,
                    "total_days": total_days,
                    "occupied_days": occupied_days,
                    "occupancy_rate": occupancy_rate,
                    "avg_daily_rate": avg_daily_rate,
                    "revenue": revenue
                })
    
    if not property_data:
        st.info("No property data available for the selected period and client.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(property_data)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_occupancy = df["occupancy_rate"].mean()
        st.metric("Avg. Occupancy Rate", f"{avg_occupancy:.1f}%")
    
    with col2:
        total_occupied_days = df["occupied_days"].sum()
        total_days = df["total_days"].sum()
        st.metric("Total Occupied Days", f"{total_occupied_days} / {total_days}")
    
    with col3:
        avg_daily_rate = df["avg_daily_rate"].mean()
        st.metric("Avg. Daily Rate", format_currency(avg_daily_rate))
    
    with col4:
        total_revenue = df["revenue"].sum()
        st.metric("Total Revenue", format_currency(total_revenue))
    
    # Occupancy rate chart
    st.subheader("Occupancy Rates by Property")
    
    fig = px.bar(
        df,
        x="property",
        y="occupancy_rate",
        color="client" if selected_client == "All Clients" else None,
        title="Occupancy Rates by Property",
        labels={"property": "Property", "occupancy_rate": "Occupancy Rate (%)", "client": "Client"},
        color_continuous_scale="Viridis"
    )
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    
    # Revenue vs. Occupancy chart
    st.subheader("Revenue vs. Occupancy Rate")
    
    fig = px.scatter(
        df,
        x="occupancy_rate",
        y="revenue",
        size="avg_daily_rate",
        color="client" if selected_client == "All Clients" else None,
        hover_name="property",
        title="Revenue vs. Occupancy Rate",
        labels={"occupancy_rate": "Occupancy Rate (%)", "revenue": "Revenue", "avg_daily_rate": "Avg. Daily Rate", "client": "Client"},
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed data
    st.subheader("Detailed Occupancy Data")
    
    # Format currency columns
    display_df = df.copy()
    display_df["avg_daily_rate"] = display_df["avg_daily_rate"].apply(lambda x: format_currency(x))
    display_df["revenue"] = display_df["revenue"].apply(lambda x: format_currency(x))
    display_df["occupancy_rate"] = display_df["occupancy_rate"].apply(lambda x: f"{x:.1f}%")
    
    # Rename columns for display
    if selected_client == "All Clients":
        display_df.columns = ["Client", "Property", "Total Days", "Occupied Days", "Occupancy Rate", "Avg. Daily Rate", "Revenue"]
    else:
        display_df = display_df.drop(columns=["client"])
        display_df.columns = ["Property", "Total Days", "Occupied Days", "Occupancy Rate", "Avg. Daily Rate", "Revenue"]
    
    st.dataframe(display_df, use_container_width=True)
    
    # Download link
    st.markdown(get_csv_download_link(display_df, "occupancy_rates.csv"), unsafe_allow_html=True)

def show_custom_report(start_date, end_date, selected_client):
    st.subheader("Custom Report")
    st.write(f"Period: {start_date} to {end_date}")
    
    # Let the user select metrics to include
    st.write("Select metrics to include in your custom report:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_reservations = st.checkbox("Reservation Summary", value=True)
        include_revenue = st.checkbox("Revenue Analysis", value=True)
    
    with col2:
        include_occupancy = st.checkbox("Occupancy Rates", value=True)
        include_client_performance = st.checkbox("Client Performance", value=False)
    
    # Generate the custom report
    if include_reservations:
        st.divider()
        show_reservation_summary_report(start_date, end_date, selected_client)
    
    if include_revenue:
        st.divider()
        show_revenue_analysis_report(start_date, end_date, selected_client)
    
    if include_occupancy:
        st.divider()
        show_occupancy_rates_report(start_date, end_date, selected_client)
    
    if include_client_performance:
        st.divider()
        show_client_performance_report(start_date, end_date, selected_client)

# Settings page
def show_settings():
    st.title("Settings")
    
    # Create tabs for different settings
    tab1, tab2, tab3, tab4 = st.tabs(["General Settings", "User Management", "Data Management", "System Logs"])
    
    with tab1:
        st.subheader("General Settings")
        
        # Company information
        with st.container(border=True):
            st.write("Company Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name", value="Videmi Services")
                company_email = st.text_input("Company Email", value="contact@videmiservices.com")
            
            with col2:
                company_phone = st.text_input("Company Phone", value="+123456789")
                company_address = st.text_area("Company Address", value="123 Main Street\nWillemstad, Curacao")
            
            if st.button("Save Company Information"):
                log_activity("settings", "Updated company information")
                add_notification("Company information saved successfully!", "success")
                st.success("Company information saved successfully!")
        
        # Notification settings
        with st.container(border=True):
            st.write("Notification Settings")
            
            email_notifications = st.checkbox("Email Notifications", value=True)
            sms_notifications = st.checkbox("SMS Notifications", value=False)
            
            st.write("Notification Events:")
            new_reservation = st.checkbox("New Reservation", value=True)
            reservation_update = st.checkbox("Reservation Update", value=True)
            reservation_cancellation = st.checkbox("Reservation Cancellation", value=True)
            
            if st.button("Save Notification Settings"):
                log_activity("settings", "Updated notification settings")
                add_notification("Notification settings saved successfully!", "success")
                st.success("Notification settings saved successfully!")
        
        # Display settings
        with st.container(border=True):
            st.write("Display Settings")
            
            date_format = st.selectbox(
                "Date Format",
                options=["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"]
            )
            
            currency = st.selectbox(
                "Currency",
                options=["USD ($)", "EUR (€)", "ANG (ƒ)"]
            )
            
            if st.button("Save Display Settings"):
                log_activity("settings", "Updated display settings")
                add_notification("Display settings saved successfully!", "success")
                st.success("Display settings saved successfully!")
    
    with tab2:
        st.subheader("User Management")
        
        # Display users
        for username, user in st.session_state.users.items():
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{user['name']}**")
                    st.write(f"Username: {username}")
                    st.write(f"Email: {user['email']}")
                
                with col2:
                    st.write(f"Role: {user['role'].capitalize()}")
                    st.write("Last login: Today, 10:23 AM")  # In a real app, this would be actual data
                
                with col3:
                    if st.button("Edit", key=f"edit_user_{username}"):
                        st.session_state.edit_user = username
                    
                    if username != "admin" and st.button("Delete", key=f"delete_user_{username}"):
                        if st.session_state.current_user == username:
                            st.error("You cannot delete your own account.")
                        else:
                            st.warning(f"Are you sure you want to delete user '{username}'?")
                            confirm_delete = st.button(f"Confirm Delete {username}", key=f"confirm_delete_{username}")
                            
                            if confirm_delete:
                                del st.session_state.users[username]
                                log_activity("user", f"Deleted user: {username}")
                                add_notification(f"User '{username}' deleted successfully!", "success")
                                save_data()
                                st.experimental_rerun()
        
        # Edit user form
        if 'edit_user' in st.session_state and st.session_state.edit_user:
            username = st.session_state.edit_user
            user = st.session_state.users[username]
            
            st.subheader(f"Edit User: {username}")
            
            with st.form("edit_user_form"):
                name = st.text_input("Name", value=user['name'])
                email = st.text_input("Email", value=user['email'])
                
                role = st.selectbox(
                    "Role",
                    options=["admin", "manager", "staff"],
                    index=["admin", "manager", "staff"].index(user['role'])
                )
                
                change_password = st.checkbox("Change Password")
                
                if change_password:
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                
                submitted = st.form_submit_button("Save Changes")
                
                if submitted:
                    # Update user information
                    st.session_state.users[username]['name'] = name
                    st.session_state.users[username]['email'] = email
                    st.session_state.users[username]['role'] = role
                    
                    if change_password:
                        if not new_password:
                            st.error("Password cannot be empty.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match.")
                        else:
                            # Update password
                            st.session_state.users[username]['password_hash'] = hashlib.sha256(new_password.encode()).hexdigest()
                    
                    log_activity("user", f"Updated user information: {username}")
                    add_notification(f"User '{username}' updated successfully!", "success")
                    save_data()
                    
                    st.success(f"User '{username}' updated successfully!")
                    st.session_state.edit_user = None
                    st.experimental_rerun()
            
            if st.button("Cancel Edit"):
                st.session_state.edit_user = None
                st.experimental_rerun()
        
        # Add new user
        st.subheader("Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
            
            new_role = st.selectbox(
                "Role",
                options=["admin", "manager", "staff"]
            )
            
            new_password = st.text_input("Password", type="password")
            confirm_new_password = st.text_input("Confirm Password", type="password")
            
            submitted = st.form_submit_button("Add User")
            
            if submitted:
                if not new_username or not new_name or not new_email or not new_password:
                    st.error("All fields are required.")
                elif new_username in st.session_state.users:
                    st.error(f"Username '{new_username}' already exists.")
                elif new_password != confirm_new_password:
                    st.error("Passwords do not match.")
                else:
                    # Add new user
                    st.session_state.users[new_username] = {
                        "password_hash": hashlib.sha256(new_password.encode()).hexdigest(),
                        "role": new_role,
                        "name": new_name,
                        "email": new_email
                    }
                    
                    log_activity("user", f"Added new user: {new_username}")
                    add_notification(f"User '{new_username}' added successfully!", "success")
                    save_data()
                    
                    st.success(f"User '{new_username}' added successfully!")
                    st.experimental_rerun()
    
    with tab3:
        st.subheader("Data Management")
        
        # Backup and restore
        with st.container(border=True):
            st.write("Backup and Restore")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Create Backup", use_container_width=True):
                    # Create backup data
                    backup_data = {
                        "clients": st.session_state.clients,
                        "users": st.session_state.users,
                        "activity_log": st.session_state.activity_log,
                        "import_history": st.session_state.import_history,
                        "export_history": st.session_state.export_history,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Convert to JSON
                    backup_json = json.dumps(backup_data, indent=2, default=str)
                    
                    # Create download link
                    b64 = base64.b64encode(backup_json.encode()).decode()
                    filename = f"videmi_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    href = f'<a href="data:application/json;base64,{b64}" download="{filename}" class="download-button">Download Backup File</a>'
                    
                    st.markdown(href, unsafe_allow_html=True)
                    
                    log_activity("backup", "Created data backup")
                    add_notification("Backup created successfully!", "success")
            
            with col2:
                uploaded_file = st.file_uploader("Restore from Backup", type=["json"])
                
                if uploaded_file is not None:
                    try:
                        # Read and parse backup file
                        backup_data = json.loads(uploaded_file.getvalue().decode())
                        
                        # Validate backup data
                        if "clients" not in backup_data or "users" not in backup_data:
                            st.error("Invalid backup file. Missing required data.")
                        else:
                            if st.button("Restore Data"):
                                # Restore data
                                st.session_state.clients = backup_data.get("clients", {})
                                st.session_state.users = backup_data.get("users", st.session_state.users)
                                st.session_state.activity_log = backup_data.get("activity_log", [])
                                st.session_state.import_history = backup_data.get("import_history", [])
                                st.session_state.export_history = backup_data.get("export_history", [])
                                
                                log_activity("restore", "Restored data from backup")
                                add_notification("Data restored successfully!", "success")
                                save_data()
                                
                                st.success("Data restored successfully!")
                                st.experimental_rerun()
                    
                    except Exception as e:
                        st.error(f"Error restoring backup: {e}")
        
        # Export data
        with st.container(border=True):
            st.write("Export All Data")
            
            if st.button("Export All Data"):
                # Create export data
                export_data = {
                    "clients": st.session_state.clients,
                    "users": {k: {**v, "password_hash": "[REDACTED]"} for k, v in st.session_state.users.items()},  # Redact passwords
                    "activity_log": st.session_state.activity_log,
                    "import_history": st.session_state.import_history,
                    "export_history": st.session_state.export_history,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Convert to JSON
                export_json = json.dumps(export_data, indent=2, default=str)
                
                # Create download link
                b64 = base64.b64encode(export_json.encode()).decode()
                filename = f"videmi_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                href = f'<a href="data:application/json;base64,{b64}" download="{filename}" class="download-button">Download Export File</a>'
                
                st.markdown(href, unsafe_allow_html=True)
                
                log_activity("export", "Exported all data")
                add_notification("Data exported successfully!", "success")
        
        # Clear data
        with st.container(border=True):
            st.write("Clear Data")
            
            clear_type = st.selectbox(
                "Clear Type",
                options=["All Data", "Clients Only", "Reservations Only", "Activity Log"]
            )
            
            confirm_clear = st.text_input("Type 'CONFIRM' to clear data")
            
            if st.button("Clear Data"):
                if confirm_clear == "CONFIRM":
                    if clear_type == "All Data":
                        # Keep users but clear everything else
                        st.session_state.clients = {}
                        st.session_state.activity_log = []
                        st.session_state.import_history = []
                        st.session_state.export_history = []
                        
                        log_activity("clear", "Cleared all data")
                        add_notification("All data cleared successfully!", "success")
                    
                    elif clear_type == "Clients Only":
                        st.session_state.clients = {}
                        
                        log_activity("clear", "Cleared all clients")
                        add_notification("All clients cleared successfully!", "success")
                    
                    elif clear_type == "Reservations Only":
                        # Clear reservations for all clients
                        for client_id in st.session_state.clients:
                            st.session_state.clients[client_id]["reservations"] = []
                        
                        log_activity("clear", "Cleared all reservations")
                        add_notification("All reservations cleared successfully!", "success")
                    
                    elif clear_type == "Activity Log":
                        st.session_state.activity_log = []
                        
                        log_activity("clear", "Cleared activity log")
                        add_notification("Activity log cleared successfully!", "success")
                    
                    save_data()
                    st.success(f"{clear_type} cleared successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Please type 'CONFIRM' to clear data")
    
    with tab4:
        st.subheader("System Logs")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            log_type = st.selectbox(
                "Filter by Type",
                options=["All", "auth", "client", "reservation", "import", "export", "backup", "restore", "clear", "settings", "user", "github"]
            )
        
        with col2:
            log_user = st.selectbox(
                "Filter by User",
                options=["All"] + list(st.session_state.users.keys())
            )
        
        # Apply filters
        filtered_logs = st.session_state.activity_log.copy()
        
        if log_type != "All":
            filtered_logs = [log for log in filtered_logs if log["type"] == log_type]
        
        if log_user != "All":
            filtered_logs = [log for log in filtered_logs if log["user"] == log_user]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"), reverse=True)
        
        # Display logs
        if not filtered_logs:
            st.info("No logs found matching your filter criteria.")
        else:
            st.write(f"Showing {len(filtered_logs)} logs")
            
            for log in filtered_logs:
                st.write(f"**{log['timestamp']}** ({log['user']}): {log['description']} [Type: {log['type']}]")
            
            # Export logs
            if st.button("Export Logs"):
                # Convert to DataFrame
                log_df = pd.DataFrame(filtered_logs)
                
                # Create download link
                st.markdown(get_csv_download_link(log_df, "activity_logs.csv"), unsafe_allow_html=True)

# Run the app
def main():
    main_app()

# Add custom CSS
st.markdown("""
<style>
    .download-button {
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: #4CAF50;
        color: white;
        text-align: center;
        text-decoration: none;
        font-size: 16px;
        border-radius: 4px;
        margin-top: 10px;
    }
    
    .download-button:hover {
        background-color: #45a049;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4e8df5;
        color: white;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    /* Container styling */
    [data-testid="stContainer"] {
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        padding: 10px;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 4px;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Form styling */
    [data-testid="stForm"] {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        border: 1px solid #e9ecef;
    }
    
    /* Metric styling */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #e9ecef;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid #e9ecef;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
