import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# API Base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Session state for authentication
if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# Utility functions
def api_request(method, endpoint, data=None, params=None, auth=True):
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {}
    
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        if method.lower() == "get":
            response = requests.get(url, params=params, headers=headers)
        elif method.lower() == "post":
            response = requests.post(url, json=data, headers=headers)
        elif method.lower() == "put":
            response = requests.put(url, json=data, headers=headers)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers)
        else:
            st.error(f"Invalid method: {method}")
            return None
        
        if response.status_code in [200, 201, 204]:
            if response.status_code == 204:  # No content
                return True
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def login():
    st.subheader("Login")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if email and password:
            data = {"email": email, "password": password}
            response = api_request("post", "auth/login", data=data, auth=False)
            
            if response:
                st.session_state.token = response["access_token"]
                st.session_state.user_id = response["user_id"]
                st.session_state.user_role = response["user_role"]
                st.success("Login successful!")
                st.rerun()
        else:
            st.warning("Please enter email and password")

def logout():
    st.session_state.token = None
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.success("Logged out successfully!")
    st.rerun()

# Page components
def dashboard_page():
    st.title("Smart Beauty Salon Dashboard")
    
    # Get user profile
    user = api_request("get", "users/me")
    
    if not user:
        st.warning("Failed to load user data")
        return
    
    st.write(f"Welcome, {user['full_name']}!")
    
    # Display different content based on user role
    if st.session_state.user_role == "client":
        client_dashboard()
    elif st.session_state.user_role == "salon_owner":
        salon_owner_dashboard()
    elif st.session_state.user_role == "stylist":
        stylist_dashboard()
    elif st.session_state.user_role == "admin":
        admin_dashboard()

def client_dashboard():
    st.header("Client Dashboard")
    
    # Show tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Upcoming Appointments", "Search Services", "Chat Assistant", "My Ratings"])
    
    with tab1:
        st.subheader("Your Upcoming Appointments")
        appointments = api_request("get", "appointments/my-appointments", params={"status": "pending"})
        
        if appointments:
            if len(appointments) > 0:
                for appt in appointments:
                    with st.expander(f"{appt['service']['name']} on {appt['start_time']}"):
                        st.write(f"**Service:** {appt['service']['name']}")
                        st.write(f"**Stylist:** {appt['stylist']['full_name']}")
                        st.write(f"**Date/Time:** {appt['start_time']}")
                        st.write(f"**Status:** {appt['status']}")
                        st.write(f"**Price:** ${appt['price']}")
                        
                        if appt['status'] == "pending":
                            if st.button(f"Cancel Appointment #{appt['id']}"):
                                cancel_data = {
                                    "status": "cancelled",
                                    "cancellation_reason": "Cancelled by client"
                                }
                                result = api_request("put", f"appointments/{appt['id']}/status", data=cancel_data)
                                if result:
                                    st.success("Appointment cancelled!")
                                    st.rerun()
            else:
                st.info("You have no upcoming appointments")
        else:
            st.warning("Failed to load appointments")
    
    with tab2:
        st.subheader("Search for Services")
        query = st.text_input("What service are you looking for?")
        
        if query:
            if st.button("Search"):
                services = api_request("get", f"services/search", params={"query": query})
                
                if services and len(services) > 0:
                    for service in services:
                        with st.expander(f"{service['name']} at {service['salon_name']} - ${service['price']}"):
                            st.write(f"**Service:** {service['name']}")
                            st.write(f"**Category:** {service['category']}")
                            st.write(f"**Salon:** {service['salon_name']}")
                            st.write(f"**Location:** {service['salon_city']}")
                            st.write(f"**Price:** ${service['price']}")
                            st.write(f"**Duration:** {service['duration_minutes']} minutes")
                            
                            if st.button(f"Book {service['name']} #{service['id']}"):
                                st.session_state.selected_service = service
                                st.rerun()
                else:
                    st.info("No services found matching your query")
    
    with tab3:
        st.subheader("Beauty Assistant Chat")
        
        user_message = st.text_input("Ask Beauty Assistant for recommendations", key="chat_input")
        
        if st.button("Send"):
            if user_message:
                chat_data = {"message": user_message}
                response = api_request("post", "chatbot/message", data=chat_data)
                
                if response:
                    st.write("**Beauty Assistant:**")
                    st.write(response["message"])
                    
                    if response.get("recommended_services"):
                        st.write("**Recommended Services:**")
                        for service in response["recommended_services"]:
                            st.write(f"- {service['name']} at {service['salon_name']} - ${service['price']}")
                else:
                    st.warning("Failed to get a response from Beauty Assistant")
    
    with tab4:
        st.subheader("My Ratings and Reviews")
        ratings = api_request("get", "ratings/my-ratings")
        
        if ratings:
            if len(ratings) > 0:
                for rating in ratings:
                    with st.expander(f"{rating['target_type'].capitalize()}: {rating['overall_score']} stars"):
                        st.write(f"**Rating:** {rating['overall_score']} / 5")
                        st.write(f"**Type:** {rating['target_type']}")
                        if rating.get("comment"):
                            st.write(f"**Comment:** {rating['comment']}")
                        st.write(f"**Date:** {rating['created_at']}")
            else:
                st.info("You haven't submitted any ratings yet")
        else:
            st.warning("Failed to load ratings")

def salon_owner_dashboard():
    st.header("Salon Owner Dashboard")
    
    # Show tabs
    tab1, tab2, tab3, tab4 = st.tabs(["My Salons", "Appointments", "Services", "Stylists"])
    
    with tab1:
        st.subheader("Your Salons")
        salons = api_request("get", "salons/my-salons")
        
        if salons:
            if len(salons) > 0:
                for salon in salons:
                    with st.expander(f"{salon['name']} - {salon['city']}"):
                        st.write(f"**Name:** {salon['name']}")
                        st.write(f"**Location:** {salon['city']}")
                        st.write(f"**Status:** {'Active' if salon['is_active'] else 'Inactive'}")
                        
                        if st.button(f"Manage Salon #{salon['id']}"):
                            st.session_state.selected_salon = salon
                            st.rerun()
            else:
                st.info("You don't have any salons yet")
                
                if st.button("Create New Salon"):
                    st.session_state.create_salon = True
                    st.rerun()
        else:
            st.warning("Failed to load salons")
    
    with tab2:
        st.subheader("Today's Appointments")
        # In a real implementation, we would need to get the salon IDs first
        # For simplicity, we'll just show a placeholder
        st.info("Please select a salon to view its appointments")
    
    with tab3:
        st.subheader("Services Management")
        st.info("Please select a salon to manage its services")
    
    with tab4:
        st.subheader("Stylists Management")
        st.info("Please select a salon to manage its stylists")

def stylist_dashboard():
    st.header("Stylist Dashboard")
    
    # Show tabs
    tab1, tab2, tab3 = st.tabs(["Today's Appointments", "My Schedule", "My Services"])
    
    with tab1:
        st.subheader("Today's Appointments")
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        appointments = api_request("get", "appointments/my-appointments", 
                                   params={"from_date": today.isoformat(), 
                                           "to_date": tomorrow.isoformat()})
        
        if appointments:
            if len(appointments) > 0:
                for appt in appointments:
                    with st.expander(f"{appt['service']['name']} at {appt['start_time']}"):
                        st.write(f"**Client:** {appt['client']['full_name']}")
                        st.write(f"**Service:** {appt['service']['name']}")
                        st.write(f"**Time:** {appt['start_time']}")
                        st.write(f"**Status:** {appt['status']}")
                        st.write(f"**Price:** ${appt['price']}")
                        
                        if appt['status'] == "pending":
                            if st.button(f"Confirm Appointment #{appt['id']}"):
                                update_data = {"status": "confirmed"}
                                result = api_request("put", f"appointments/{appt['id']}/status", data=update_data)
                                if result:
                                    st.success("Appointment confirmed!")
                                    st.rerun()
                        
                        if appt['status'] == "confirmed":
                            if st.button(f"Complete Appointment #{appt['id']}"):
                                update_data = {"status": "completed"}
                                result = api_request("put", f"appointments/{appt['id']}/status", data=update_data)
                                if result:
                                    st.success("Appointment marked as completed!")
                                    st.rerun()
            else:
                st.info("You have no appointments scheduled for today")
        else:
            st.warning("Failed to load appointments")
    
    with tab2:
        st.subheader("My Schedule")
        st.info("Please use the calendar to view and manage your schedule")
        # In a real app, we would implement a proper calendar view
    
    with tab3:
        st.subheader("My Services")
        st.info("Services you can provide would be listed here")
        # In a real app, we would list the stylist's services

def admin_dashboard():
    st.header("Admin Dashboard")
    
    # Show tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Users", "Salons", "Services", "System Stats"])
    
    with tab1:
        st.subheader("User Management")
        
        # Filter options
        role_filter = st.selectbox("Filter by role", 
                                   ["All", "Client", "Salon Owner", "Stylist", "Admin"], 
                                   index=0)
        
        # Convert role filter to API parameter
        role_param = None
        if role_filter != "All":
            role_param = role_filter.lower().replace(" ", "_")
        
        users = api_request("get", "users", params={"role": role_param})
        
        if users:
            if len(users) > 0:
                # Convert to dataframe for better display
                users_df = pd.DataFrame(users)
                st.dataframe(users_df[['id', 'email', 'full_name', 'role', 'is_active']])
            else:
                st.info("No users found with the selected filter")
        else:
            st.warning("Failed to load users")
    
    with tab2:
        st.subheader("Salon Management")
        salons = api_request("get", "salons", params={"is_active": True})
        
        if salons:
            if len(salons) > 0:
                # Convert to dataframe for better display
                salons_df = pd.DataFrame(salons)
                st.dataframe(salons_df[['id', 'name', 'city', 'is_active']])
            else:
                st.info("No active salons found")
        else:
            st.warning("Failed to load salons")
    
    with tab3:
        st.subheader("Service Management")
        st.info("Services would be listed here")
        # In a real app, we would list all services
    
    with tab4:
        st.subheader("System Statistics")
        st.info("System statistics would be displayed here")
        # In a real app, we would show various statistics

# Main App
def main():
    st.set_page_config(
        page_title="Smart Beauty Salon",
        page_icon="💇‍♀️",
        layout="wide"
    )
    
    # Sidebar
    with st.sidebar:
        st.title("Smart Beauty Salon")
        
        if st.session_state.token:
            st.write(f"Logged in as: **{st.session_state.user_role}**")
            if st.button("Logout"):
                logout()
        else:
            login()
    
    # Main content
    if st.session_state.token:
        dashboard_page()
    else:
        st.title("Welcome to Smart Beauty Salon")
        st.write("Please login to access the dashboard")
        
        # Feature highlights
        st.header("Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Find the Perfect Salon")
            st.write("Search for salons and services based on your preferences")
        
        with col2:
            st.subheader("AI Beauty Assistant")
            st.write("Get personalized beauty recommendations from our AI assistant")
        
        with col3:
            st.subheader("Easy Booking")
            st.write("Book appointments with your favorite stylists in just a few clicks")

if __name__ == "__main__":
    main()