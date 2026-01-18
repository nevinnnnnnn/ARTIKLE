import streamlit as st

def render_users_page():
    """Render the user management page (superadmin only)"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access user management.")
        return
    
    user = st.session_state.get("current_user", {})
    role = user.get('role', 'user').lower()
    
    # Only superadmin can manage users
    if role != "superadmin":
        st.error("⚠️ You need superadmin privileges to manage users.")
        return
    
    st.markdown("## 👥 User Management")
    
    # Get API client
    api_client = st.session_state.get("api_client")
    if not api_client:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    # Tabs for different functions
    tab1, tab2 = st.tabs(["📋 User List", "➕ Create User"])
    
    with tab1:
        st.markdown("### Existing Users")
        
        # Fetch users
        with st.spinner("Loading users..."):
            users = api_client.get_users()
        
        if not users:
            st.info("No users found.")
        else:
            # Display users in a table
            for user_data in users:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        # User info
                        status_icon = "✅" if user_data.get('is_active') else "❌"
                        role_icon = {
                            "superadmin": "👑",
                            "admin": "🛠️",
                            "user": "👤"
                        }.get(user_data.get('role', 'user'), "👤")
                        
                        st.markdown(f"**{user_data.get('username', 'Unknown')}**")
                        st.caption(f"{user_data.get('email', 'No email')}")
                        st.caption(f"{role_icon} {user_data.get('role', 'user').title()} | {status_icon} {'Active' if user_data.get('is_active') else 'Inactive'}")
                    
                    with col2:
                        # Edit button (disabled for now)
                        st.button("Edit", key=f"edit_user_{user_data['id']}", 
                                 disabled=True, use_container_width=True)
                    
                    with col3:
                        # Toggle active status
                        current_status = "Deactivate" if user_data.get('is_active') else "Activate"
                        if st.button(current_status, key=f"toggle_{user_data['id']}", use_container_width=True):
                            # Toggle user status
                            result = api_client.toggle_user_active(user_data['id'])
                            if result and result.get("success"):
                                st.success(f"User {current_status.lower()}d!")
                                st.rerun()
                    
                    with col4:
                        # Delete button (only for non-superadmin users)
                        if user_data.get('role') != "superadmin" and user_data.get('id') != st.session_state.current_user.get('user_id'):
                            if st.button("Delete", key=f"delete_{user_data['id']}", 
                                        type="secondary", use_container_width=True):
                                st.warning(f"Delete user {user_data.get('username')}?")
                    st.markdown("---")
    
    with tab2:
        st.markdown("### Create New User")
        
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("Email", placeholder="user@example.com")
                username = st.text_input("Username", placeholder="username")
                full_name = st.text_input("Full Name", placeholder="Optional")
            
            with col2:
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                role_options = ["user", "admin", "superadmin"]
                role = st.selectbox("Role", role_options)
                
                is_active = st.checkbox("Active", value=True)
            
            # Validation
            if password != confirm_password:
                st.error("Passwords do not match!")
            
            submit = st.form_submit_button("Create User", type="primary", use_container_width=True)
            
            if submit:
                if not all([email, username, password]):
                    st.error("Please fill in all required fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    user_data = {
                        "email": email,
                        "username": username,
                        "password": password,
                        "full_name": full_name if full_name else None,
                        "role": role,
                        "is_active": is_active
                    }
                    
                    with st.spinner("Creating user..."):
                        result = api_client.create_user(user_data)
                    
                    if result:
                        st.success(f"✅ User {username} created successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create user.")