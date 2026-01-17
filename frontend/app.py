import streamlit as st

# MUST be the first Streamlit command
st.set_page_config(
    page_title="PDF AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize ALL session state variables at the TOP level
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'token' not in st.session_state:
    st.session_state.token = None
if 'page' not in st.session_state:
    st.session_state.page = "chat"
if 'api_client' not in st.session_state:
    st.session_state.api_client = None

# Now import other modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.api_client import APIClient
from src.auth import authenticate_user, logout_user, get_current_user
from src.components.sidebar import render_sidebar

def main():
    """Main Streamlit application"""
    
    # Initialize API client if not already
    if st.session_state.api_client is None:
        st.session_state.api_client = APIClient("http://localhost:8000")
    
    # Render sidebar
    with st.sidebar:
        render_sidebar()
    
    # Main content area
    st.title("🤖 PDF AI Chatbot")
    
    # Check authentication
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_content()

def show_login_page():
    """Display login page"""
    st.markdown("## Welcome to PDF AI Chatbot")
    st.markdown("Please log in to continue.")
    
    # Create two columns for login form
    col1, col2 = st.columns([1, 2])
    
    with col2:
        # Use a unique key for the form and inputs
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username or Email", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if authenticate_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
    
    # Info box
    with col1:
        st.info("""
        **Demo Credentials:**
        
        👑 **Superadmin**
        - Username: `superadmin`
        - Password: `admin123`
        
        🛠️ **Admin**
        - Username: `admin`
        - Password: `admin123`
        
        👤 **User**
        - Username: `user`
        - Password: `user123`
        """)

def show_main_content():
    """Display main content based on user role"""
    user = get_current_user()
    
    if user:
        st.markdown(f"### Welcome back, {user.get('username', 'User')}! 👋")
        st.markdown(f"**Role:** {user.get('role', 'User').title()}")
        
        # Display page content
        if st.session_state.page == "chat":
            # Import and render chat page
            try:
                from pages import chat
                chat.render_chat_page()
            except ImportError:
                st.warning("Chat page not implemented yet")
                
        elif st.session_state.page == "documents":
            # Import and render documents page
            try:
                from pages import documents
                documents.render_documents_page()
            except ImportError:
                st.warning("Documents page not implemented yet")
                
        elif st.session_state.page == "admin":
            # Import and render admin page
            try:
                from pages import admin
                admin.render_admin_page()
            except ImportError:
                st.warning("Admin page not implemented yet")
                
        elif st.session_state.page == "superadmin":
            # Import and render superadmin page
            try:
                from pages import superadmin
                superadmin.render_superadmin_page()
            except ImportError:
                st.warning("Superadmin page not implemented yet")

if __name__ == "__main__":
    main()