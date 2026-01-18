import streamlit as st
from src.auth import get_current_user, logout_user

def render_sidebar():
    """Render role-specific sidebar navigation - NO SIDEBAR on login page"""
    
    user = get_current_user()
    if not user:
        return
    
    role = user.get('role', 'user').lower()
    username = user.get('username', 'User')
    
    # Sidebar header with user info
    st.sidebar.markdown("# 🤖 PDF AI Chatbot")
    st.sidebar.markdown("---")
    
    # Role badges
    role_badges = {
        "superadmin": "👑 Superadmin",
        "admin": "🛠️ Admin", 
        "user": "👤 User"
    }
    
    st.sidebar.markdown(f"### {role_badges.get(role, '👤 User')}")
    st.sidebar.caption(f"📧 {username}")
    st.sidebar.markdown("---")
    
    # Navigation based on role - Primary Section
    st.sidebar.markdown("## 📍 Navigation")
    
    # Common navigation items for all roles
    if role in ["superadmin", "admin", "user"]:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🤖 Chat", key="nav_chat", use_container_width=True):
                st.session_state.page = "chat"
                st.rerun()
        with col2:
            if st.button("📚 Docs", key="nav_documents", use_container_width=True):
                st.session_state.page = "documents"
                st.rerun()
    
    # Admin-only navigation
    if role in ["superadmin", "admin"]:
        if st.sidebar.button("📤 Upload Document", key="nav_upload", use_container_width=True):
            st.session_state.page = "upload"
            st.rerun()
    
    # Admin navigation (not superadmin)
    if role == "admin":
        if st.sidebar.button("⚙️ Admin Panel", key="nav_admin", use_container_width=True):
            st.session_state.page = "admin"
            st.rerun()
    
    # Superadmin-only navigation
    if role == "superadmin":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("👥 Users", key="nav_users", use_container_width=True):
                st.session_state.page = "users"
                st.rerun()
        with col2:
            if st.button("⚙️ Admin", key="nav_admin", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()
    
    # Profile section for all roles
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 👤 Account")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("👤 Profile", key="nav_profile", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="nav_logout", use_container_width=True, type="secondary"):
            logout_user()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0.0 • Built with Streamlit 🚀")