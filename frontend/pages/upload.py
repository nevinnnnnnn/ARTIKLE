import streamlit as st
import time

def render_upload_page():
    """Render the document upload page with auto-processing"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access upload.")
        return
    
    user = st.session_state.get("current_user", {})
    role = user.get('role', 'user').lower()
    
    # Only admin and superadmin can upload
    if role not in ["admin", "superadmin"]:
        st.error("⚠️ You need admin privileges to upload documents.")
        return
    
    st.markdown("## 📤 Upload Document")
    st.info("Documents are automatically processed and embeddings created after upload.")
    
    # Get API client
    api_client = st.session_state.get("api_client")
    if not api_client:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    # Upload form
    with st.form("upload_form", clear_on_submit=False):
        st.markdown("### Document Details")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf",
            help="Maximum file size: 50MB. Processing starts automatically after upload."
        )
        
        # Document metadata
        title = st.text_input("Document Title", placeholder="Enter a title for the document")
        description = st.text_area("Description", placeholder="Enter a description (optional)")
        
        # Visibility settings
        is_public = st.checkbox("Make document public", value=True, 
                               help="Public documents are visible to all users")
        
        # Submit button
        submit = st.form_submit_button("Upload & Process Document", type="primary", use_container_width=True)
    
    if submit:
        if not uploaded_file:
            st.error("Please select a PDF file to upload.")
        elif not title:
            st.error("Please enter a title for the document.")
        else:
            # Upload document
            with st.spinner("Uploading document..."):
                result = api_client.upload_document(
                    file=uploaded_file,
                    title=title,
                    description=description if description else None,
                    is_public=is_public
                )
            
            if result and result.get("success"):
                document_id = result.get("document_id")
                st.success(f"✅ Document uploaded successfully! ID: {document_id}")
                
                # Show processing status with real-time updates
                st.markdown("---")
                st.markdown("### ⚙️ Processing Status")
                
                # Auto-refresh status every 2 seconds
                status_placeholder = st.empty()
                
                max_attempts = 60  # 2 minutes max
                for attempt in range(max_attempts):
                    status_info = api_client.get_document_status(document_id)
                    
                    if status_info and 'data' in status_info:
                        doc_status = status_info['data']
                        status_val = doc_status.get('status', 'uploaded')
                        
                        with status_placeholder.container():
                            # Step 1: Upload complete
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                st.success("✅")
                            with col2:
                                st.markdown("**Upload Complete**")
                                st.caption("File saved to server")
                            
                            # Step 2: Processing
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                if status_val in ['processing', 'ready']:
                                    st.success("✅")
                                else:
                                    st.info("⏳")
                            with col2:
                                st.markdown("**Processing Document**")
                                chunk_count = doc_status.get('chunk_count', 0)
                                if chunk_count > 0:
                                    st.caption(f"✅ Created {chunk_count} chunks")
                                else:
                                    st.caption("Extracting text and creating chunks...")
                            
                            # Step 3: Creating embeddings
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                if status_val == 'ready':
                                    st.success("✅")
                                else:
                                    st.info("⏳")
                            with col2:
                                st.markdown("**Creating Embeddings**")
                                if status_val == 'ready':
                                    st.caption("✅ Embeddings complete!")
                                else:
                                    st.caption("Building vector search index...")
                        
                        # Exit loop if processing complete
                        if status_val == 'ready':
                            st.balloons()
                            st.success("🎉 Document ready for chatting!")
                            break
                    
                    # Wait before next check
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                
            else:
                st.error("❌ Failed to upload document.")
    
    # Quick actions (outside form)
    if submit and result and result.get("success"):
        st.markdown("---")
        st.markdown("### 🚀 What's Next?")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🤖 Start Chatting", key="btn_chat", use_container_width=True):
                st.session_state.page = "chat"
                st.rerun()
        with col2:
            if st.button("📚 View Documents", key="btn_docs", use_container_width=True):
                st.session_state.page = "documents"
                st.rerun()
        with col3:
            if st.button("📤 Upload Another", key="btn_upload", use_container_width=True):
                st.rerun()
    
    # Back to documents button (always available)
    st.markdown("---")
    if st.button("← Back to Documents", key="btn_back", use_container_width=True):
        st.session_state.page = "documents"
        st.rerun()