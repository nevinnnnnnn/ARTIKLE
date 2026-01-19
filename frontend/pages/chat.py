import streamlit as st
import json
import time
import logging

logger = logging.getLogger(__name__)


def render_chat_page():
    """Render the complete professional chat interface"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access the chat.")
        return
    
    user = st.session_state.get("current_user", {})
    role = user.get('role', 'user').lower()
    
    # Professional page header
    st.set_page_config(page_title="Chat with Documents", layout="wide")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("## 💬")
    with col2:
        st.markdown("# Chat with Documents")
    
    st.divider()
    
    # Get API client
    api_client = st.session_state.get("api_client")
    if not api_client:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    # Add refresh button
    if st.button("🔄 Refresh Documents", key="refresh_docs"):
        st.rerun()
    
    # Fetch chatable documents (processed only)
    with st.spinner("Loading available documents..."):
        response = api_client.get_chatable_documents()
        documents = response if isinstance(response, list) else response.get('data', []) if isinstance(response, dict) else []
    
    if not documents:
        if role in ["admin", "superadmin"]:
            st.info("""
            **No documents available yet.**
            
            To get started:
            1. Go to the Upload section
            2. Upload a PDF document
            3. Wait for processing to complete
            4. Return here to chat
            """)
            
            if st.button("📤 Upload Documents", type="primary", use_container_width=True):
                st.session_state.page = "upload"
                st.rerun()
        else:
            st.info("No documents available for chatting. Please ask an admin to upload documents.")
        return
    
    # Create two-column layout: document selector + chat
    col_left, col_right = st.columns([1.2, 3], gap="large")
    
    # LEFT COLUMN: Document Selection
    with col_left:
        st.markdown("### 📚 Available Documents")
        
        # Filter and sort documents
        available_docs = sorted(documents, key=lambda x: x.get('title', '').lower())
        
        # Create document selector
        doc_options = []
        for doc in available_docs:
            icon = "🌐" if doc.get('is_public', True) else "🔒"
            status = "✅" if doc.get('processed_at') else "⏳"
            doc_options.append({
                "label": f"{icon} {doc['title']} {status}",
                "value": doc['id'],
                "doc": doc
            })
        
        # Document selection
        selected_option = st.selectbox(
            "Select document:",
            options=[opt["label"] for opt in doc_options],
            key="doc_selector",
            label_visibility="collapsed"
        )
        
        # Get selected document
        selected_opt = next((opt for opt in doc_options if opt["label"] == selected_option), None)
        
        if selected_opt:
            selected_doc = selected_opt["doc"]
            selected_doc_id = selected_opt["value"]
            
            # Display document info in professional card
            st.markdown("---")
            with st.container(border=True):
                st.markdown(f"**📄 {selected_doc.get('title', 'Untitled')}**")
                st.caption(f"File: `{selected_doc.get('filename', 'Unknown')}`")
                
                # Visibility & Status
                col_vis, col_stat = st.columns(2)
                with col_vis:
                    if selected_doc.get('is_public'):
                        st.write("**Access:** 🌐 Public")
                    else:
                        st.write("**Access:** 🔒 Private")
                        
                with col_stat:
                    if selected_doc.get('processed_at'):
                        st.write("**Status:** ✅ Ready")
                    else:
                        st.write("**Status:** ⏳ Processing")
                
                # Metadata
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.caption(f"**By:** {selected_doc.get('uploaded_by', 'Unknown')}")
                with col_m2:
                    if selected_doc.get('uploaded_at'):
                        st.caption(f"**Date:** {selected_doc['uploaded_at'][:10]}")
                
                st.divider()
                
                # Process button if not ready
                if not selected_doc.get('processed_at') and role in ["admin", "superadmin"]:
                    if st.button("🔄 Process Now", key=f"process_{selected_doc_id}", use_container_width=True):
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
    
    # RIGHT COLUMN: Chat Interface
    with col_right:
        if not selected_opt:
            st.info("👈 **Select a document to start chatting**")
            return
        
        selected_doc = selected_opt["doc"]
        selected_doc_id = selected_opt["value"]
        
        # Check if document is processed
        if not selected_doc.get('processed_at'):
            st.warning("""
            ⚠️ **This document needs to be processed first**
            
            Processing includes:
            - Text extraction from PDF
            - Content chunking  
            - Creating search embeddings
            
            Please ask an admin to process this document.
            """)
            return
        
        # Chat header
        st.markdown(f"### 💬 Chat: **{selected_doc.get('title')}**")
        st.caption("Ask questions about this document - the AI will answer based on its content")
        st.divider()
        
        # Initialize chat history for this document
        chat_key = f"chat_doc_{selected_doc_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
            # Load persistent chat history from backend
            try:
                history_response = api_client.make_request(
                    method="GET",
                    endpoint=f"/api/v1/chat/history/{selected_doc_id}"
                )
                if history_response and not history_response.get("error"):
                    for chat_msg in history_response.get("data", []):
                        # Load from DB format to session state format
                        st.session_state[chat_key].append({
                            "role": "user",
                            "content": chat_msg["question"],
                            "timestamp": chat_msg.get("timestamp", "")
                        })
                        st.session_state[chat_key].append({
                            "role": "assistant",
                            "content": chat_msg["response"],
                            "metadata": {
                                "top_similarity_score": chat_msg.get("relevance_score", 0),
                                "context_chunks_retrieved": chat_msg.get("context_chunks", 0)
                            },
                            "timestamp": chat_msg.get("timestamp", "")
                        })
            except Exception as e:
                st.warning(f"Could not load chat history: {str(e)}")
        
        chat_history = st.session_state[chat_key]
        
        # Display chat messages
        if chat_history:
            for message in chat_history:
                if message["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(message["content"])
                        st.caption(f"*{message.get('timestamp', '')}*")
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(message["content"])
                        if message.get("metadata"):
                            with st.expander("📊 Response Details"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    score = message['metadata'].get('top_similarity_score', 0)
                                    st.metric("Relevance", f"{score:.1%}")
                                with col2:
                                    chunks = message['metadata'].get('context_chunks_retrieved', 0)
                                    st.metric("Sources Used", chunks)
                                with col3:
                                    status = "✅ Relevant" if message['metadata'].get('is_relevant') else "⚠️ Low Match"
                                    st.write(f"**Quality:** {status}")
                        st.caption(f"*{message.get('timestamp', '')}*")
        else:
            st.info("👋 **Start your conversation below**")
        
        st.divider()
        
        # Input area
        question = st.chat_input(
            f"Ask about {selected_doc.get('title')}...",
            key=f"chat_input_{selected_doc_id}"
        )
        
        # Handle new question
        if question:
            # Add user message to history immediately
            user_message = {
                "role": "user",
                "content": question,
                "timestamp": time.strftime("%H:%M:%S")
            }
            st.session_state[chat_key].append(user_message)
            
            # Display user message
            with st.chat_message("user", avatar="👤"):
                st.markdown(question)
                st.caption(f"*{user_message['timestamp']}*")
            
            # Get AI response
            with st.spinner("🤖 AI is thinking..."):
                try:
                    stream = api_client.chat_stream(selected_doc_id, question)
                    
                    if stream:
                        response_placeholder = st.empty()
                        full_response = ""
                        metadata = {}
                        stream_complete = False
                        
                        def parse_sse_stream(stream):
                            """Parse SSE stream with robust error handling"""
                            try:
                                for line in stream:
                                    if line:
                                        try:
                                            line_str = line.decode('utf-8').strip() if isinstance(line, bytes) else str(line).strip()
                                            if line_str.startswith('data: '):
                                                try:
                                                    event_data = json.loads(line_str[6:])
                                                    yield event_data
                                                except json.JSONDecodeError:
                                                    continue
                                        except Exception as e:
                                            continue
                            except Exception as e:
                                st.error(f"Stream error: {str(e)}")
                        
                        for event_data in parse_sse_stream(stream):
                            try:
                                if event_data.get("type") == "metadata":
                                    metadata = event_data.get("data", {})
                                elif event_data.get("type") == "text":
                                    chunk = event_data.get("data", "")
                                    if chunk:
                                        full_response += chunk
                                        # Display streaming response
                                        with response_placeholder.container():
                                            with st.chat_message("assistant", avatar="🤖"):
                                                st.markdown(full_response + " ▌")
                                elif event_data.get("type") == "complete":
                                    stream_complete = True
                                    # Final response display
                                    with response_placeholder.container():
                                        with st.chat_message("assistant", avatar="🤖"):
                                            if full_response:
                                                st.markdown(full_response)
                                            else:
                                                st.write("*(No response generated)*")
                                            
                                            if metadata:
                                                with st.expander("📊 Response Details"):
                                                    col1, col2, col3 = st.columns(3)
                                                    with col1:
                                                        score = metadata.get('top_similarity_score', 0)
                                                        st.metric("Relevance", f"{score:.1%}")
                                                    with col2:
                                                        chunks = metadata.get('context_chunks_retrieved', 0)
                                                        st.metric("Sources", chunks)
                                                    with col3:
                                                        status = "✅" if metadata.get('is_relevant') else "ℹ️"
                                                        st.write(f"**Quality:** {status}")
                                            st.caption(f"*{time.strftime('%H:%M:%S')}*")
                                    break
                                elif event_data.get("type") == "error":
                                    error_msg = event_data.get("data", {}).get("message", "Unknown error")
                                    with response_placeholder.container():
                                        st.error(f"⚠️ {error_msg}")
                                    stream_complete = True
                                    break
                            except KeyError:
                                # Malformed event, skip it
                                continue
                        
                        # If stream ended without complete event, show what we have
                        if not stream_complete and full_response and full_response not in ["Error", ""]:
                            with response_placeholder.container():
                                with st.chat_message("assistant", avatar="🤖"):
                                    st.markdown(full_response)
                                    if metadata:
                                        with st.expander("📊 Response Details"):
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                score = metadata.get('top_similarity_score', 0)
                                                st.metric("Relevance", f"{score:.1%}")
                                            with col2:
                                                chunks = metadata.get('context_chunks_retrieved', 0)
                                                st.metric("Sources", chunks)
                                            with col3:
                                                status = "✅" if metadata.get('is_relevant') else "ℹ️"
                                                st.write(f"**Quality:** {status}")
                                    st.caption(f"*{time.strftime('%H:%M:%S')}*")
                        
                        # Add response to history - CRITICAL FIX
                        if full_response:
                            ai_message = {
                                "role": "assistant",
                                "content": full_response,
                                "metadata": metadata,
                                "timestamp": time.strftime("%H:%M:%S")
                            }
                            st.session_state[chat_key].append(ai_message)
                        else:
                            # No response generated, add error message
                            ai_message = {
                                "role": "assistant",
                                "content": "❌ No response was generated. Please try again.",
                                "metadata": metadata,
                                "timestamp": time.strftime("%H:%M:%S")
                            }
                            st.session_state[chat_key].append(ai_message)
                    else:
                        st.error("❌ Failed to get response. Please try again.")
                        error_message = {
                            "role": "assistant",
                            "content": "❌ Failed to get response from the server.",
                            "metadata": {},
                            "timestamp": time.strftime("%H:%M:%S")
                        }
                        st.session_state[chat_key].append(error_message)
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    error_message = {
                        "role": "assistant",
                        "content": f"❌ Error occurred: {str(e)}",
                        "metadata": {},
                        "timestamp": time.strftime("%H:%M:%S")
                    }
                    st.session_state[chat_key].append(error_message)
        
        # Controls
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state[chat_key] = []
                st.rerun()
        
        with col2:
            if st.button("💾 Export Chat", use_container_width=True):
                if chat_history:
                    export_text = f"Chat: {selected_doc.get('title', 'Document')}\n"
                    export_text += f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    export_text += "=" * 60 + "\n\n"
                    
                    for message in chat_history:
                        role = "👤 User" if message["role"] == "user" else "🤖 AI"
                        export_text += f"{role} ({message.get('timestamp', '')}):\n"
                        export_text += f"{message['content']}\n\n"
                    
                    st.download_button(
                        label="Download",
                        data=export_text,
                        file_name=f"chat_{selected_doc_id}_{time.strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.warning("No chat history to export")
        
        with col3:
            if st.button("💡 Tips", use_container_width=True):
                with st.expander("How to Get Better Answers"):
                    st.markdown("""
                    **✅ Best Practices:**
                    - Ask specific, focused questions
                    - Reference page numbers when available
                    - Use keywords from the document
                    - Ask one question at a time
                    
                    **❌ Avoid:**
                    - Questions unrelated to the document
                    - Vague or unclear phrasing
                    - Multiple questions at once
                    - Expecting external knowledge
                    
                    **Examples:**
                    - "What are the key findings in section 3?"
                    - "On page 5, what does it say about..."
                    - "Summarize the main conclusion"
                    """)