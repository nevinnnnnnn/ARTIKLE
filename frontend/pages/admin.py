import streamlit as st
import time

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
            render_dashboard(api_client)
        
        with tab2:
            render_user_management(api_client)
        
        with tab3:
            st.markdown("#### 📚 Document Management")
            render_document_management(api_client)
        
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
            render_document_management(api_client)
        
        with tab2:
            st.markdown("#### 👥 View Users")
            render_user_list(api_client)


def render_dashboard(api_client):
    """Render system dashboard"""
    st.markdown("#### 📊 System Dashboard")
    
    # Fetch stats
    with st.spinner("Loading statistics..."):
        users_response = api_client.get_users(limit=1000)
        documents_response = api_client.get_documents(limit=1000)
    
    # Extract data
    users_list = users_response if isinstance(users_response, list) else []
    documents_list = documents_response if isinstance(documents_response, list) else []
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Users", len(users_list), help="Total registered users")
    
    with col2:
        st.metric("Total Documents", len(documents_list), help="Total documents in system")
    
    with col3:
        active_users = len([u for u in users_list if u.get('is_active', False)])
        st.metric("Active Users", active_users, help="Currently active users")
    
    st.markdown("---")
    
    # User stats
    col1, col2, col3 = st.columns(3)
    with col1:
        superadmins = len([u for u in users_list if u.get('role', '').lower() == 'superadmin'])
        st.metric("Superadmins", superadmins)
    
    with col2:
        admins = len([u for u in users_list if u.get('role', '').lower() == 'admin'])
        st.metric("Admins", admins)
    
    with col3:
        regular_users = len([u for u in users_list if u.get('role', '').lower() == 'user'])
        st.metric("Regular Users", regular_users)


def render_user_list(api_client):
    """Render user list"""
    st.markdown("##### All Users")
    
    # Fetch users
    with st.spinner("Loading users..."):
        users_response = api_client.get_users()
    
    users_list = users_response if isinstance(users_response, list) else []
    
    if not users_list:
        st.info("No users in the system yet.")
        return
    
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


def render_document_management(api_client):
    """Render document management interface"""
    
    st.markdown("##### 📚 Document Management")
    
    # Fetch documents
    with st.spinner("Loading documents..."):
        documents_response = api_client.get_documents()
    
    documents_list = documents_response if isinstance(documents_response, list) else []
    
    if not documents_list:
        st.info("No documents in the system yet.")
        return
    
    # Display documents
    for doc in documents_list:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                visibility = "🌐 Public" if doc.get('is_public') else "🔒 Private"
                status = "✅ Ready" if doc.get('embeddings_created_at') else ("⏳ Processed" if doc.get('is_processed') else "📤 Uploaded")
                
                st.markdown(f"**{doc.get('title', 'Untitled')}**")
                st.caption(f"{visibility} | {status}")
            
            with col2:
                st.caption(doc.get('original_filename', 'Unknown'))
            
            with col3:
                if st.button("📊 Status", key=f"status_{doc['id']}", use_container_width=True):
                    status_info = api_client.get_document_status(doc['id'])
                    if status_info and 'data' in status_info:
                        st.json(status_info['data'])
            
            with col4:
                if st.button("🗑️ Delete", key=f"delete_doc_{doc['id']}", use_container_width=True):
                    # Delete confirmation
                    col_del1, col_del2 = st.columns(2)
                    with col_del1:
                        if st.button("✅ Confirm Delete", key=f"confirm_del_{doc['id']}"):
                            result = api_client.make_request("DELETE", f"/api/v1/documents/{doc['id']}")
                            if result and result.get('success'):
                                st.success("Document deleted!")
                                st.rerun()
                    with col_del2:
                        if st.button("❌ Cancel", key=f"cancel_del_{doc['id']}"):
                            st.rerun()
            
            st.markdown("---")


def render_user_management(api_client):
    """Render user management interface"""
    
    st.markdown("#### 👥 Manage Users")
    
    # Tabs for user management
    user_tab1, user_tab2 = st.tabs(["📋 User List", "➕ Create User"])
    
    with user_tab1:
        render_user_list(api_client)
    
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
                    
                    if result:
                        if result.get("error"):
                            st.error(f"❌ Error: {result.get('detail', 'Unknown error')}")
                        elif "id" in result:
                            st.success(f"✅ User created successfully! ID: {result['id']}")
                            st.balloons()
                            # Clear form by rerunning
                            st.session_state.create_user_form_submitted = True
                            time.sleep(1)
                            st.rerun()
                        elif result.get("success"):
                            st.success("✅ User created successfully!")
                            st.balloons()
                        else:
                            st.error(f"❌ Failed to create user")
                    else:
                        st.error("❌ Failed to create user: No response from server")