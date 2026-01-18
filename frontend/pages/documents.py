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
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Document info
                visibility = "🌐 Public" if doc.get('is_public') else "🔒 Private"
                status = "✅ Processed" if doc.get('is_processed') else "⏳ Not Processed"
                
                st.markdown(f"**{doc.get('title', 'Untitled')}**")
                st.caption(f"File: {doc.get('original_filename', 'Unknown')} | {visibility} | {status}")
                st.caption(f"Uploaded by: {doc.get('uploaded_by_username', 'Unknown')}")
            
            with col2:
                # Action buttons based on role and ownership
                is_owner = doc.get('uploaded_by_id') == user_id
                
                if role == "superadmin" or (role == "admin" and is_owner):
                    if st.button("Edit", key=f"edit_{doc['id']}", use_container_width=True):
                        st.session_state.editing_doc = doc['id']
                        st.rerun()
            
            with col3:
                if role == "superadmin" or (role == "admin" and is_owner):
                    if st.button("Delete", key=f"delete_{doc['id']}", type="secondary", use_container_width=True):
                        # Delete document logic here
                        st.warning(f"Delete document {doc['id']}?")
            
            st.markdown("---")
    
    # Document actions based on role
    st.markdown("### 📊 Document Actions")
    
    if role in ["superadmin", "admin"]:
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