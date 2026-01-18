import streamlit as st
import json
import time

def render_chat_page():
    """Render the complete chat interface"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access the chat.")
        return
    
    user = st.session_state.get("current_user", {})
    role = user.get('role', 'user').lower()
    
    st.markdown("## 🤖 Chat with PDFs")
    st.caption("Ask questions about your documents. The AI will answer strictly from the document content.")
    
    # Get API client
    api_client = st.session_state.get("api_client")
    if not api_client:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    # Fetch documents
    with st.spinner("Loading available documents..."):
        documents = api_client.get_chatable_documents()
    
    if not documents:
        st.warning("""
        No documents available for chatting. 
        
        **For Admins/Superadmins:** Upload and process documents first.
        **For Users:** Wait for admins to upload public documents.
        """)
        
        if role in ["admin", "superadmin"]:
            if st.button("📤 Upload Documents", type="primary"):
                st.session_state.page = "upload"
                st.rerun()
        return
    
    # Create two columns: document selection and chat
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown("### 📚 Select Document")
        
        # Filter and sort documents
        available_docs = []
        for doc in documents:
            available_docs.append(doc)
        
        # Sort by title
        available_docs.sort(key=lambda x: x.get('title', '').lower())
        
        if not available_docs:
            st.warning("No documents available for your role.")
            return
        
        # Document selector with better UI
        doc_options = []
        for doc in available_docs:
            icon = "🌐" if doc.get('is_public', True) else "🔒"
            status = "✅" if doc.get('processed_at') else "⏳"
            doc_options.append({
                "label": f"{icon} {doc['title']} {status}",
                "value": doc['id'],
                "doc": doc
            })
        
        # Create radio buttons for document selection
        selected_option = st.radio(
            "Choose a document:",
            options=[opt["label"] for opt in doc_options],
            key="doc_selector"
        )
        
        # Get selected document
        selected_opt = next((opt for opt in doc_options if opt["label"] == selected_option), None)
        
        if selected_opt:
            selected_doc = selected_opt["doc"]
            selected_doc_id = selected_opt["value"]
            
            # Display document info
            st.markdown("---")
            st.markdown("#### 📋 Document Info")
            st.markdown(f"**Title:** {selected_doc.get('title', 'Untitled')}")
            st.markdown(f"**File:** {selected_doc.get('filename', 'Unknown')}")
            st.markdown(f"**Visibility:** {'🌐 Public' if selected_doc.get('is_public') else '🔒 Private'}")
            st.markdown(f"**Uploaded by:** {selected_doc.get('uploaded_by', 'Unknown')}")
            
            if selected_doc.get('uploaded_at'):
                st.markdown(f"**Uploaded:** {selected_doc['uploaded_at'][:10]}")
            
            if selected_doc.get('processed_at'):
                st.markdown(f"**Processed:** ✅ Ready for chat")
            else:
                st.markdown(f"**Status:** ⏳ Needs processing")
                if role in ["admin", "superadmin"]:
                    if st.button("🔄 Process Document", key=f"process_{selected_doc_id}", use_container_width=True):
                        with st.spinner("Processing document..."):
                            result = api_client.process_document(selected_doc_id)
                            if result and result.get("success"):
                                st.success("Document processed! Creating embeddings...")
                                embed_result = api_client.create_embeddings(selected_doc_id)
                                if embed_result and embed_result.get("success"):
                                    st.success("✅ Ready for chat!")
                                    st.rerun()
                            else:
                                st.error("Processing failed")
    
    with col_right:
        if not selected_opt:
            st.info("Please select a document to start chatting.")
            return
        
        selected_doc = selected_opt["doc"]
        selected_doc_id = selected_opt["value"]
        
        # Check if document is processed
        if not selected_doc.get('processed_at'):
            st.warning("""
            ⚠️ This document needs to be processed before chatting.
            
            **Processing includes:**
            1. Text extraction from PDF
            2. Chunking into smaller pieces
            3. Creating embeddings for semantic search
            
            Please ask an admin to process this document.
            """)
            return
        
        st.markdown(f"### 💬 Chat with: **{selected_doc.get('title', 'Document')}**")
        
        # Initialize chat history for this document
        chat_key = f"chat_doc_{selected_doc_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        
        # Display chat messages
        chat_container = st.container()
        
        with chat_container:
            # Show chat history
            chat_history = st.session_state[chat_key]
            
            if chat_history:
                st.markdown("#### 📝 Conversation")
                for i, message in enumerate(chat_history):
                    if message["role"] == "user":
                        with st.chat_message("user"):
                            st.markdown(message["content"])
                            if message.get("timestamp"):
                                st.caption(message["timestamp"])
                    else:
                        with st.chat_message("assistant"):
                            st.markdown(message["content"])
                            if message.get("metadata"):
                                with st.expander("📊 Response Details"):
                                    st.json(message["metadata"])
                            if message.get("timestamp"):
                                st.caption(message["timestamp"])
            
            # Current conversation area
            st.markdown("---")
        
        # Input for new question - placed outside the container
        question = st.chat_input(
            f"Ask a question about {selected_doc.get('title', 'the document')}...",
            key=f"chat_input_{selected_doc_id}"
        )
        
        # Handle new question
        if question:
            # Add user message to history and display immediately
            user_message = {
                "role": "user",
                "content": question,
                "timestamp": time.strftime("%H:%M:%S")
            }
            st.session_state[chat_key].append(user_message)
            
            # Display user message
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(question)
                    st.caption(user_message["timestamp"])
            
            # Get AI response with streaming
            with st.spinner("🤔 Thinking..."):
                try:
                    # Get streaming response
                    stream = api_client.chat_stream(selected_doc_id, question)
                    
                    if stream:
                        # Create a placeholder for the streaming response
                        response_placeholder = st.empty()
                        full_response = ""
                        metadata = {}
                        
                        # Parse the SSE stream
                        def parse_sse_stream(stream):
                            """Parse Server-Sent Events stream"""
                            for line in stream:
                                if line:
                                    try:
                                        line = line.decode('utf-8').strip()
                                        if line.startswith('data: '):
                                            try:
                                                event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                                                yield event_data
                                            except json.JSONDecodeError:
                                                continue
                                    except:
                                        continue
                        
                        for event_data in parse_sse_stream(stream):
                            if event_data["type"] == "metadata":
                                metadata = event_data["data"]
                            elif event_data["type"] == "text":
                                chunk = event_data["data"]
                                full_response += chunk
                                # Update the placeholder with the current response
                                with response_placeholder.chat_message("assistant"):
                                    st.markdown(full_response + "▌")
                            elif event_data["type"] == "complete":
                                # Finalize the response
                                with response_placeholder.chat_message("assistant"):
                                    st.markdown(full_response)
                                    if metadata:
                                        with st.expander("📊 Response Details"):
                                            st.write(f"**Relevant:** {metadata.get('is_relevant', 'Unknown')}")
                                            st.write(f"**Context chunks used:** {metadata.get('context_chunks_retrieved', 0)}")
                                            st.write(f"**Similarity score:** {metadata.get('top_similarity_score', 0):.3f}")
                                    st.caption(time.strftime("%H:%M:%S"))
                                break
                            elif event_data["type"] == "error":
                                st.error(f"Error: {event_data['data'].get('message', 'Unknown error')}")
                                break
                        
                        # Add AI response to history
                        ai_message = {
                            "role": "assistant",
                            "content": full_response,
                            "metadata": metadata,
                            "timestamp": time.strftime("%H:%M:%S")
                        }
                        st.session_state[chat_key].append(ai_message)
                        
                    else:
                        st.error("Failed to get response from AI. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error during chat: {str(e)}")
        
        # Chat controls
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Chat", use_container_width=True, help="Clear and start fresh"):
                st.session_state[chat_key] = []
                st.rerun()
        
        with col2:
            if st.button("📋 Export Chat", use_container_width=True, help="Export conversation to text file"):
                if chat_history:
                    export_text = f"Chat with: {selected_doc.get('title', 'Document')}\n"
                    export_text += f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    export_text += "=" * 50 + "\n\n"
                    
                    for message in chat_history:
                        role = "User" if message["role"] == "user" else "AI"
                        export_text += f"{role} ({message.get('timestamp', '')}):\n"
                        export_text += f"{message['content']}\n\n"
                    
                    st.download_button(
                        label="Download Chat",
                        data=export_text,
                        file_name=f"chat_{selected_doc_id}_{time.strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.warning("No chat history to export")
        
        with col3:
            if st.button("ℹ️ Chat Instructions", use_container_width=True, help="How to use the chat"):
                with st.expander("Chat Instructions", expanded=True):
                    st.markdown("""
                    **How to get the best results:**
                    
                    1. **Ask specific questions** - Instead of "Tell me about this document", ask "What are the main points in section 3?"
                    2. **Reference page numbers** - If you know the page, mention it: "On page 5, what does it say about..."
                    3. **Ask one question at a time** - The AI works best with focused questions
                    4. **Use keywords** - The AI searches for similar content in the document
                    
                    **What to expect:**
                    - ✅ Answers based ONLY on the document content
                    - ❌ "The question is irrelevant" when answer isn't in the document
                    - 📊 Response details show how relevant the answer is
                    
                    **Note:** The AI cannot use external knowledge or make assumptions.
                    """)