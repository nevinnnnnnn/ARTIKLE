import streamlit as st
import json
import time
import logging

logger = logging.getLogger(__name__)


def render_chat_page():
    """
    Delta-safe, production-ready chat page.
    
    KEY SAFETY MEASURES:
    1. Streaming lock prevents page render while response is streaming
    2. Chat container is created ONCE (outside history loop) for stable delta
    3. Only the placeholder inside gets updated during streaming
    4. No st.rerun() calls - only st.stop() after state changes
    5. UI element order is preserved across all reruns
    """

    # ---- STREAMING LOCK (CRITICAL) ----
    # This flag prevents page render while streaming to avoid delta corruption
    if "chat_streaming" not in st.session_state:
        st.session_state.chat_streaming = False

    if st.session_state.chat_streaming:
        st.warning("⏳ Response is streaming... please wait")
        st.stop()  # Block all further rendering during streaming

    # ---- AUTH CHECK ----
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access the chat.")
        return

    user = st.session_state.get("current_user", {})
    role = user.get("role", "user").lower()

    # ---- HEADER ----
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("## 💬")
    with col2:
        st.markdown("# Chat with Documents")

    st.divider()

    # ---- API CLIENT ----
    api_client = st.session_state.get("api_client")
    if not api_client:
        st.error("API client not initialized.")
        return

    # ---- LOAD DOCUMENTS ----
    with st.spinner("Loading documents..."):
        response = api_client.get_chatable_documents()
        documents = response if isinstance(response, list) else response.get("data", []) if isinstance(response, dict) else []

    if not documents:
        st.info("No documents available.")
        return

    # ---- LAYOUT ----
    col_left, col_right = st.columns([1.2, 3], gap="large")

    # ================= LEFT COLUMN =================
    with col_left:
        st.markdown("### 📚 Documents")

        docs = sorted(documents, key=lambda x: x.get("title", "").lower())
        labels = []
        doc_map = {}

        for d in docs:
            icon = "🌐" if d.get("is_public", True) else "🔒"
            status = "✅" if d.get("processed_at") else "⏳"
            label = f"{icon} {d['title']} {status}"
            labels.append(label)
            doc_map[label] = d

        selected_label = st.selectbox(
            "Select document",
            labels,
            label_visibility="collapsed",
            key="doc_selector"
        )

        selected_doc = doc_map.get(selected_label)
        if not selected_doc:
            return

        if not selected_doc.get("processed_at"):
            st.warning("Document not processed yet.")
            return

    # ================= RIGHT COLUMN =================
    with col_right:
        doc_id = selected_doc["id"]
        chat_key = f"chat_{doc_id}"

        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        st.markdown(f"### 💬 {selected_doc.get('title')}")
        st.caption("AI answers strictly from this document")
        st.divider()

        # ---- DISPLAY CHAT HISTORY ----
        # CRITICAL: Chat message containers are created only for display
        # The order and structure must remain stable across all reruns
        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("timestamp"):
                    st.caption(msg["timestamp"])

        # ---- INPUT (MUST be after history for stable order) ----
        question = st.chat_input(
            f"Ask about {selected_doc.get('title')}..."
        )

        if question:
            # STEP 1: Add user message to session state FIRST
            user_msg = {
                "role": "user",
                "content": question,
                "timestamp": time.strftime("%H:%M:%S")
            }
            st.session_state[chat_key].append(user_msg)

            # STEP 2: Display user message immediately
            with st.chat_message("user"):
                st.markdown(question)
                st.caption(user_msg["timestamp"])

            # STEP 3: Set streaming lock BEFORE creating assistant container
            # This ensures the next rerun will stop before rendering anything
            st.session_state.chat_streaming = True

            # STEP 4: Create assistant container ONCE and get placeholder ONCE
            # CRITICAL: Do NOT recreate this container during streaming
            with st.chat_message("assistant"):
                stream_placeholder = st.empty()

            # STEP 5: Stream response into the SAME placeholder
            full_response = ""
            metadata = {}

            try:
                stream = api_client.chat_stream(doc_id, question)
                
                if not stream:
                    stream_placeholder.markdown("❌ Failed to get response stream")
                    full_response = "❌ No response stream returned"
                    logger.error("chat_stream returned None")
                else:
                    logger.info(f"Starting to read from stream for question: {question[:50]}")

                    for line in stream:
                        if not line:
                            continue

                        try:
                            # Handle SSE format: "data: {json}"
                            line_str = line.decode() if isinstance(line, bytes) else line
                            
                            # Remove "data: " prefix if present
                            if line_str.startswith("data:"):
                                line_str = line_str[5:].strip()
                            
                            data = json.loads(line_str)
                            logger.debug(f"Received event type: {data.get('type')}")
                        except (json.JSONDecodeError, ValueError):
                            # Skip lines that aren't valid JSON
                            logger.debug(f"Skipped non-JSON line: {line_str[:50] if line_str else 'empty'}")
                            continue

                        # Only update the placeholder, never recreate the container
                        if data.get("type") == "text":
                            chunk = data.get("data", "")
                            if chunk:
                                full_response += chunk
                                # Update placeholder with cursor animation
                                stream_placeholder.markdown(full_response + " ▌")

                        elif data.get("type") == "metadata":
                            metadata = data.get("data", {})
                            logger.info(f"Metadata received: {len(metadata)} items")

                        elif data.get("type") == "complete":
                            logger.info("Stream completion received")
                            break

                    logger.info(f"Stream finished. Total response length: {len(full_response)}")
                    # Final update: remove cursor
                    stream_placeholder.markdown(full_response)

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                stream_placeholder.markdown("❌ Error generating response")
                full_response = "❌ Error occurred."

            # STEP 6: Save AI response to session state
            ai_msg = {
                "role": "assistant",
                "content": full_response,
                "metadata": metadata,
                "timestamp": time.strftime("%H:%M:%S")
            }
            st.session_state[chat_key].append(ai_msg)
            logger.info(f"Chat message saved to session state. Response: {full_response[:100]}")

            # STEP 7: Release streaming lock
            # After response is complete and saved, unlock for next interaction
            # Do NOT call st.stop() here - allow page to continue rendering
            # This ensures the controls below are visible
            st.session_state.chat_streaming = False

        # ---- CONTROLS (Appears after chat input for stable order) ----
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True, key=f"clear_{doc_id}"):
                st.session_state[chat_key] = []
                # Update state first, then stop (not rerun) to avoid delta issues
                st.stop()

        with col2:
            if st.button("💾 Export Chat", use_container_width=True, key=f"export_{doc_id}"):
                text = ""
                for m in st.session_state[chat_key]:
                    text += f"{m['role'].upper()}: {m['content']}\n\n"

                st.download_button(
                    "Download",
                    text,
                    file_name=f"chat_{doc_id}.txt",
                    mime="text/plain",
                    key=f"dl_{doc_id}"
                )
