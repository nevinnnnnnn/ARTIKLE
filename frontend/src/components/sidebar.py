import streamlit as st
from src.auth import get_current_user, logout_user

def render_sidebar():
    """Render the sidebar navigation"""
    st.sidebar.markdown("# 🤖 PDF AI Chatbot")
    
    user = get_current_user()
    
    if user:
        # User info section
        st.sidebar.markdown("---")
        role = user.get('role', 'user').lower()
        
        # Role icons
        role_icons = {
            "superadmin": "👑",
            "admin": "🛠️",
            "user": "👤"
        }
        icon = role_icons.get(role, "👤")
        
        st.sidebar.markdown(f"### {icon} {user.get('username', 'User')}")
        st.sidebar.caption(f"{role.title()}")
        
        # Navigation section
        st.sidebar.markdown("---")
        st.sidebar.markdown("## 📍 Navigation")
        
        # Determine available pages based on role
        pages = []
        if role in ["superadmin", "admin", "user"]:
            pages.append(("🤖 Chat", "chat"))
            pages.append(("📚 Documents", "documents"))
        
        if role in ["superadmin", "admin"]:
            pages.append(("🛠️ Admin", "admin"))
        
        if role == "superadmin":
            pages.append(("👑 Superadmin", "superadmin"))
        
        # Create navigation buttons
        for page_name, page_id in pages:
            if st.sidebar.button(page_name, key=f"nav_{page_id}", use_container_width=True):
                st.session_state.page = page_id
                st.rerun()
        
        # Logout button
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", use_container_width=True, type="primary"):
            logout_user()
    
    else:
        # Login prompt
        st.sidebar.markdown("---")
        st.sidebar.info("Please log in to access the chatbot features.")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0.0 • Built with Streamlit")