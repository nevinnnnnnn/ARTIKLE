import streamlit as st

def render_documents_page():
    """Render the documents management page"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access documents.")
        return
    
    user = st.session_state.get("current_user", {})
    role = user.get('role', 'user').lower()
    user_id = user.get('user_id')
    
    st.markdown("## 📚 All Documents")
    
    # Get API client
    api_client = st.session_state.get("api_client")
    if not api_client:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    # Fetch all documents
    with st.spinner("Loading documents..."):
        documents = api_client.get_documents()
    
    if not documents:
        st.info("No documents found.")
        return
    
    # Display documents in a table
    st.markdown(f"### Found {len(documents)} documents")
    
    for doc in documents:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                # Document info
                visibility = "🌐 Public" if doc.get('is_public') else "🔒 Private"
                status = "✅ Ready" if doc.get('embeddings_created_at') else ("⏳ Processed" if doc.get('is_processed') else "📤 Uploaded")
                
                st.markdown(f"**{doc.get('title', 'Untitled')}**")
                st.caption(f"File: {doc.get('original_filename', 'Unknown')} | {visibility} | {status}")
                st.caption(f"Uploaded by: {doc.get('uploaded_by_username', 'Unknown')}")
            
            with col2:
                # Status button
                if st.button("📊 Status", key=f"status_{doc['id']}", use_container_width=True):
                    status_info = api_client.get_document_status(doc['id'])
                    if status_info and 'data' in status_info:
                        st.info(f"Status: {status_info['data'].get('status', 'unknown')}")
            
            with col3:
                # Edit button (if owner)
                is_owner = doc.get('uploaded_by_id') == user_id
                
                if (role in ["superadmin", "admin"]) and is_owner:
                    if st.button("✏️ Edit", key=f"edit_{doc['id']}", use_container_width=True):
                        st.session_state.editing_doc = doc['id']
                    
                    # Show edit options if selected
                    if st.session_state.get('editing_doc') == doc['id']:
                        st.markdown("---")
                        st.markdown(f"**Edit Options for {doc.get('title')}**")
                        col_opt1, col_opt2 = st.columns(2)
                        with col_opt1:
                            if st.button("🔄 Process Document", key=f"process_{doc['id']}", use_container_width=True):
                                with st.spinner("Processing document..."):
                                    result = api_client.make_request("POST", f"/api/v1/documents/{doc['id']}/process")
                                    if result and result.get('success'):
                                        st.success("✅ Processing started")
                                        st.session_state.editing_doc = None
                                        st.rerun()
                                    else:
                                        st.error("Failed to process")
                        with col_opt2:
                            if st.button("🧠 Create Embeddings", key=f"embed_{doc['id']}", use_container_width=True):
                                with st.spinner("Creating embeddings..."):
                                    result = api_client.make_request("POST", f"/api/v1/documents/{doc['id']}/embed")
                                    if result and result.get('success'):
                                        st.success("✅ Embeddings created")
                                        st.session_state.editing_doc = None
                                        st.rerun()
                                    else:
                                        st.error("Failed to create embeddings")
            
            with col4:
                # Delete button (if owner)
                if (role in ["superadmin", "admin"]) and is_owner:
                    if st.button("🗑️ Delete", key=f"delete_{doc['id']}", type="secondary", use_container_width=True):
                        # Confirmation dialog
                        if st.session_state.get(f"confirm_delete_{doc['id']}", False):
                            result = api_client.make_request("DELETE", f"/api/v1/documents/{doc['id']}")
                            if result and result.get('success'):
                                st.success("✅ Document deleted!")
                                st.session_state[f"confirm_delete_{doc['id']}"] = False
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete document")
                        else:
                            st.warning("Click again to confirm deletion")
                            st.session_state[f"confirm_delete_{doc['id']}"] = True
            
            st.markdown("---")
    
    # Document actions based on role
    if role in ["superadmin", "admin"]:
        st.markdown("### 📊 Document Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Upload New Document", use_container_width=True):
                st.session_state.page = "upload"
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh List", use_container_width=True):
                st.rerun()
    else:
        if st.button("🔄 Refresh List", use_container_width=True):
            st.rerun()