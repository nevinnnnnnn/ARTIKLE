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
if 'show_sidebar' not in st.session_state:
    st.session_state.show_sidebar = False

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
    
    # Show sidebar only if authenticated
    if st.session_state.authenticated:
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
    """Display login page - NO SIDEBAR"""
    st.markdown("## Welcome to PDF AI Chatbot")
    st.markdown("Please log in to continue.")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Use a unique key for the form and inputs
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username or Email", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submit:
                if authenticate_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
    
    # Info box - bottom of page
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
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
        # Don't show welcome message for all pages, just on chat/home
        if st.session_state.page == "chat":
            st.markdown(f"### Welcome back, {user.get('username', 'User')}! 👋")
        
        # Display page content
        if st.session_state.page == "chat":
            # Import and render chat page
            try:
                from pages import chat
                chat.render_chat_page()
            except ImportError as e:
                st.error(f"Error loading chat page: {e}")
                
        elif st.session_state.page == "documents":
            # Import and render documents page
            try:
                from pages import documents
                documents.render_documents_page()
            except ImportError as e:
                st.error(f"Error loading documents page: {e}")
                
        elif st.session_state.page == "upload":
            # Import and render upload page (admin/superadmin only)
            try:
                from pages import upload
                upload.render_upload_page()
            except ImportError as e:
                st.error(f"Error loading upload page: {e}")
                
        elif st.session_state.page == "users":
            # Import and render users management page (superadmin only)
            try:
                from pages import users
                users.render_users_page()
            except ImportError as e:
                st.error(f"Error loading users page: {e}")
        
        elif st.session_state.page == "admin":
            # Import and render admin panel (admin only)
            try:
                from pages import superadmin
                superadmin.render_superadmin_page()
            except ImportError as e:
                st.error(f"Error loading admin panel: {e}")
                
        elif st.session_state.page == "profile":
            # Import and render profile page
            try:
                from pages import profile
                profile.render_profile_page()
            except ImportError as e:
                st.error(f"Error loading profile page: {e}")
        else:
            # Default to chat if page not found
            st.session_state.page = "chat"
            st.rerun()

if __name__ == "__main__":
    main()