import streamlit as st

def render_admin_page():
    """Render the admin panel (for both admin and superadmin roles)"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access the admin panel.")
        return
    
    user = st.session_state.get("current_user", {})
    role = user.get('role', 'user').lower()
    
    # Only admin and superadmin can access
    if role not in ["admin", "superadmin"]:
        st.error("⚠️ You need admin privileges to access this panel.")
        return
    
    st.markdown("## 🛠️ Admin Panel")
    
    # Get API client
    api_client = st.session_state.get("api_client")
    if not api_client:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    if role == "superadmin":
        # Superadmin gets full admin page with user management
        st.markdown("### Welcome, Superadmin! 👑")
        
        # Tabs for different admin functions
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "👥 Manage Users", "📚 Documents", "⚙️ Settings"])
        
        with tab1:
            st.markdown("#### 📊 System Dashboard")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", "🔄 Loading...", help="Total registered users")
            with col2:
                st.metric("Total Documents", "🔄 Loading...", help="Total documents in system")
            with col3:
                st.metric("Active Sessions", "🔄 Loading...", help="Currently active users")
            st.markdown("---")
            st.info("Dashboard statistics coming soon...")
        
        with tab2:
            render_user_management(api_client)
        
        with tab3:
            st.markdown("#### 📚 Document Management")
            st.info("Document management tools coming soon...")
        
        with tab4:
            st.markdown("#### ⚙️ System Settings")
            st.info("System settings coming soon...")
    
    else:
        # Regular admin gets limited admin page
        st.markdown("### Admin Panel 🛠️")
        st.markdown("Welcome, Admin! You have document management and basic user viewing permissions.")
        
        tab1, tab2 = st.tabs(["📚 Documents", "👥 Users"])
        
        with tab1:
            st.markdown("#### 📚 Your Documents")
            st.info("Document management tools coming soon...")
        
        with tab2:
            st.markdown("#### 👥 View Users")
            st.info("User viewing tools coming soon...")


def render_user_management(api_client):
    """Render user management interface"""
    
    st.markdown("#### 👥 Manage Users")
    
    # Tabs for user management
    user_tab1, user_tab2 = st.tabs(["📋 User List", "➕ Create User"])
    
    with user_tab1:
        st.markdown("##### Existing Users")
        
        # Fetch users
        with st.spinner("Loading users..."):
            users_response = api_client.get_users()
        
        if not users_response:
            st.info("No users found or unable to fetch users.")
        else:
            # Display users
            if isinstance(users_response, dict) and "data" in users_response:
                users_list = users_response["data"]
            else:
                users_list = users_response if isinstance(users_response, list) else []
            
            if not users_list:
                st.info("No users in the system yet.")
            else:
                # Create dataframe for display
                user_data = []
                for u in users_list:
                    user_data.append({
                        "ID": u.get("id"),
                        "Username": u.get("username"),
                        "Email": u.get("email"),
                        "Role": u.get("role", "").upper(),
                        "Status": "✅ Active" if u.get("is_active", False) else "❌ Inactive",
                        "Full Name": u.get("full_name", "")
                    })
                
                st.dataframe(user_data, use_container_width=True)
    
    with user_tab2:
        st.markdown("##### Create New User")
        
        with st.form("create_user_form"):
            username = st.text_input("Username", help="Unique username for login")
            email = st.text_input("Email", help="User's email address")
            password = st.text_input("Password", type="password", help="Initial password")
            confirm_password = st.text_input("Confirm Password", type="password")
            full_name = st.text_input("Full Name", help="User's full name (optional)")
            
            role = st.selectbox(
                "Role",
                options=["user", "admin"],
                help="Select user role (superadmin can only be created via direct DB access)"
            )
            
            submit = st.form_submit_button("Create User", type="primary", use_container_width=True)
            
            if submit:
                # Validation
                if not all([username, email, password]):
                    st.error("Please fill in all required fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    # Create user via API
                    with st.spinner("Creating user..."):
                        result = api_client.create_user(
                            username=username,
                            email=email,
                            password=password,
                            full_name=full_name,
                            role=role
                        )
                    
                    if result and result.get("success"):
                        st.success(f"✅ User '{username}' created successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create user: {result.get('message', 'Unknown error')}")