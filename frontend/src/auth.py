import streamlit as st
from typing import Optional, Dict, Any

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user with backend"""
    try:
        # Get API client from session state
        api_client = st.session_state.api_client
        
        if api_client is None:
            st.error("API client not initialized")
            return False
        
        # Try login
        response = api_client.login(username, password)
        
        if response and "access_token" in response:
            # Store user info in session state
            st.session_state.authenticated = True
            st.session_state.current_user = {
                "user_id": response.get("user_id"),
                "username": username,
                "role": response.get("role", "user")
            }
            st.session_state.token = response.get("access_token")
            return True
        
        return False
        
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False

def logout_user():
    """Logout user"""
    try:
        api_client = st.session_state.api_client
        if api_client:
            api_client.logout()
        
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.token = None
        st.session_state.page = "chat"
        
        st.success("Logged out successfully!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Logout error: {str(e)}")

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user from session state"""
    return st.session_state.get("current_user")

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)

def require_auth():
    """Require authentication - redirect to login if not authenticated"""
    if not is_authenticated():
        st.warning("Please log in to access this page.")
        st.session_state.page = "chat"
        st.rerun()
        return False
    return True