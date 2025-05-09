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
    st.session_state.authenticated = True  # For demo purposes, set to True

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "dashboard"

# Helper functions
def save_data():
    """Save data to a file (in a real app, this would be a database)"""
    try:
        # Convert datetime objects to strings for JSON serialization
        data = {
            "clients": st.session_state.clients
        }
        
        # In a real app, you would save to a database
        # For demo, we'll just print a success message
        st.success("Data saved successfully!")
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def load_data():
    """Load data from a file (in a real app, this would be a database)"""
    try:
        # In a real app, you would load from a database
        # For demo, we'll use the session state data
        return True
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return False

def get_csv_download_link(df, filename="videmi_data.csv"):
    """Generate a download link for a CSV file"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-button">Download CSV File</a>'
    return href

def format_currency(amount):
    """Format a number as currency"""
    return f"${amount:.2f}"

# Authentication (simplified for demo)
def login_page():
    st.title("Videmi Services Management System")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username == "admin" and password == "password":  # Demo credentials
                st.session_state.authenticated = True
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

# Main application
def main_app():
    # Sidebar for navigation
    with st.sidebar:
        st.title("Videmi Services")
        st.image("https://via.placeholder.com/150x150.png?text=Videmi+Logo", width=150)
        
        # Navigation
        st.subheader("Navigation")
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.active_tab = "dashboard"
            st.session_state.current_client = None
        
        if st.button("👥 Clients", use_container_width=True):
            st.session_state.active_tab = "clients"
            st.session_state.current_client = None
            
        if st.button("🗓️ Reservations", use_container_width=True):
            st.session_state.active_tab = "reservations"
            st.session_state.current_client = None
            
        if st.button("📈 Reports", use_container_width=True):
            st.session_state.active_tab = "reports"
            st.session_state.current_client = None
            
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.active_tab = "settings"
            st.session_state.current_client = None
        
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
        
        # Logout button
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.experimental_rerun()
    
    # Main content area
    if st.session_state.active_tab == "dashboard":
        show_dashboard()
    elif st.session_state.active_tab == "clients":
        show_clients()
    elif st.session_state.active_tab == "reservations":
        show_reservations()
    elif st.session_state.active_tab == "reports":
        show_reports()
    elif st.session_state.active_tab == "settings":
        show_settings()

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
    
    # In a real app, this would be actual activity data
    activity_data = [
        {"time": "Today, 10:23 AM", "description": "New reservation added for Dajo Curacao"},
        {"time": "Yesterday, 3:45 PM", "description": "Client profile updated: Beach Resort Rentals"},
        {"time": "May 8, 2:15 PM", "description": "Exported monthly report for all clients"},
        {"time": "May 7, 11:30 AM", "description": "Added new client: Sunset Villas"}
    ]
    
    for activity in activity_data:
        st.markdown(f"**{activity['time']}**: {activity['description']}")

# Clients page
def show_clients():
    st.title("Client Management")
    
    # Create tabs for viewing and adding clients
    tab1, tab2 = st.tabs(["View Clients", "Add New Client"])
    
    with tab1:
        if not st.session_state.clients:
            st.info("No clients added yet. Use the 'Add New Client' tab to add your first client.")
        else:
            # Display clients in a grid
            for i in range(0, len(st.session_state.clients), 3):
                cols = st.columns(3)
                
                for j in range(3):
                    if i + j < len(st.session_state.clients):
                        client_id = list(st.session_state.clients.keys())[i + j]
                        client = st.session_state.clients[client_id]
                        
                        with cols[j]:
                            with st.container(border=True):
                                st.subheader(client["name"])
                                st.write(f"**Contact:** {client['contact_person']}")
                                st.write(f"**Email:** {client['email']}")
                                st.write(f"**Service:** {client['service_type']}")
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
                    
                    st.success(f"Client '{client_name}' added successfully!")
                    st.session_state.current_client = client_id
                    st.session_state.active_tab = "client_details"
                    st.experimental_rerun()

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
                all_reservations.append(reservation_with_client)
        else:
            # Show reservations for all clients
            for client_id, client in st.session_state.clients.items():
                for reservation in client.get("reservations", []):
                    reservation_with_client = reservation.copy()
                    reservation_with_client["client_name"] = client["name"]
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
                        
                        if st.button("Cancel", key=f"cancel_res_{reservation.get('id', '')}"):
                            # In a real app, this would mark the reservation as cancelled
                            st.info("Reservation would be cancelled here")
    
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
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Add to the client's reservations
                    if "reservations" not in st.session_state.clients[selected_client_id]:
                        st.session_state.clients[selected_client_id]["reservations"] = []
                    
                    st.session_state.clients[selected_client_id]["reservations"].append(new_reservation)
                    save_data()
                    
                    st.success(f"Reservation for '{property_name}' added successfully!")
                    st.experimental_rerun()

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
    tab1, tab2, tab3 = st.tabs(["General Settings", "User Management", "Data Management"])
    
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
                st.success("Display settings saved successfully!")
    
    with tab2:
        st.subheader("User Management")
        
        # Sample users for demo
        users = [
            {"name": "Admin User", "email": "admin@videmiservices.com", "role": "Administrator"},
            {"name": "Manager", "email": "manager@videmiservices.com", "role": "Manager"},
            {"name": "Staff Member", "email": "staff@videmiservices.com", "role": "Staff"}
        ]
        
        # Display users
        for user in users:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{user['name']}**")
                    st.write(f"Email: {user['email']}")
                
                with col2:
                    st.write(f"Role: {user['role']}")
                    st.write("Last login: Today, 10:23 AM")
                
                with col3:
                    st.button("Edit", key=f"edit_user_{user['email']}")
                    st.button("Delete", key=f"delete_user_{user['email']}")
        
        # Add new user
        with st.container(border=True):
            st.write("Add New User")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_user_name = st.text_input("Name")
                new_user_email = st.text_input("Email")
            
            with col2:
                new_user_role = st.selectbox(
                    "Role",
                    options=["Administrator", "Manager", "Staff"]
                )
                new_user_password = st.text_input("Password", type="password")
            
            if st.button("Add User"):
                st.success(f"User '{new_user_name}' added successfully!")
    
    with tab3:
        st.subheader("Data Management")
        
        # Backup and restore
        with st.container(border=True):
            st.write("Backup and Restore")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Create Backup", use_container_width=True):
                    st.success("Backup created successfully!")
            
            with col2:
                st.file_uploader("Restore from Backup", type=["json"])
        
        # Export data
        with st.container(border=True):
            st.write("Export Data")
            
            export_type = st.selectbox(
                "Export Type",
                options=["All Data", "Clients Only", "Reservations Only"]
            )
            
            if st.button("Export Data"):
                st.success("Data exported successfully!")
        
        # Clear data
        with st.container(border=True):
            st.write("Clear Data")
            
            clear_type = st.selectbox(
                "Clear Type",
                options=["All Data", "Clients Only", "Reservations Only"]
            )
            
            confirm_clear = st.text_input("Type 'CONFIRM' to clear data")
            
            if st.button("Clear Data"):
                if confirm_clear == "CONFIRM":
                    st.success("Data cleared successfully!")
                else:
                    st.error("Please type 'CONFIRM' to clear data")

# Run the app
if not st.session_state.authenticated:
    login_page()
else:
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
</style>
""", unsafe_allow_html=True)
