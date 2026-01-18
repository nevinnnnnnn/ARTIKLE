import streamlit as st
import time
from src.auth import logout_user

def render_profile_page():
    """Render the user profile page"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access your profile.")
        return
    
    user = st.session_state.get("current_user", {})
    user_id = user.get('user_id')
    current_username = user.get('username')
    current_role = user.get('role', 'user')
    
    st.markdown("## 👤 My Profile")
    
    # Get API client
    api_client = st.session_state.get("api_client")
    if not api_client:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    # Get current user details
    with st.spinner("Loading profile..."):
        user_details = api_client.get_current_user()
    
    if not user_details:
        st.error("Failed to load profile information.")
        return
    
    # Display current info
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Role badge
        role_badges = {
            "superadmin": {"icon": "👑", "color": "gold"},
            "admin": {"icon": "🛠️", "color": "blue"},
            "user": {"icon": "👤", "color": "green"}
        }
        
        badge = role_badges.get(current_role, {"icon": "👤", "color": "gray"})
        st.markdown(f"<h2 style='text-align: center; color: {badge['color']};'>{badge['icon']}</h2>", 
                   unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center;'>{current_role.title()}</h4>", 
                   unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**Username:** {current_username}")
        st.markdown(f"**Email:** {user_details.get('email', 'Not set')}")
        st.markdown(f"**Full Name:** {user_details.get('full_name', 'Not set')}")
        st.markdown(f"**Account Created:** {user_details.get('created_at', 'Unknown')}")
        st.markdown(f"**Status:** {'✅ Active' if user_details.get('is_active') else '❌ Inactive'}")
    
    st.markdown("---")
    
    # Update profile form
    st.markdown("### Update Profile")
    
    with st.form("update_profile_form"):
        st.markdown("#### Personal Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username", value=current_username)
            new_email = st.text_input("Email", value=user_details.get('email', ''))
        
        with col2:
            new_full_name = st.text_input("Full Name", value=user_details.get('full_name', ''))
        
        st.markdown("#### Change Password")
        col1, col2 = st.columns(2)
        
        with col1:
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
        
        with col2:
            confirm_password = st.text_input("Confirm New Password", type="password")
        
        # Validation
        if new_password and new_password != confirm_password:
            st.error("New passwords do not match!")
        
        update_profile = st.form_submit_button("Update Profile", type="primary", use_container_width=True)
        
        if update_profile:
            update_data = {}
            
            # Only include changed fields
            if new_username != current_username:
                update_data["username"] = new_username
            
            if new_email != user_details.get('email'):
                update_data["email"] = new_email
            
            if new_full_name != user_details.get('full_name'):
                update_data["full_name"] = new_full_name
            
            if new_password and new_password == confirm_password:
                if current_password:
                    update_data["password"] = new_password
                else:
                    st.error("Please enter current password to change password.")
            
            if update_data:
                with st.spinner("Updating profile..."):
                    result = api_client.make_request("PUT", f"/api/v1/users/{user_id}", json=update_data)
                
                if result:
                    st.success("✅ Profile updated successfully!")
                    # Update session state
                    st.session_state.current_user["username"] = new_username
                    st.rerun()
                else:
                    st.error("❌ Failed to update profile.")
            else:
                st.info("No changes made.")
    
    # Danger zone
    st.markdown("---")
    st.markdown("### ⚠️ Danger Zone")
    
    with st.expander("Account Actions"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
        
        with col2:
            if st.button("🗑️ Delete Account", type="secondary", use_container_width=True):
                st.warning("Are you sure you want to delete your account? This action cannot be undone.")
                confirm = st.checkbox("I understand this will permanently delete my account")
                
                if confirm:
                    if st.button("✅ Confirm Delete", type="primary"):
                        st.error("Account deletion not implemented yet.")