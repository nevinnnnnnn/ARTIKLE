import streamlit as st
import requests
from typing import Any, Dict, List
import json

def handle_api_error(response: requests.Response):
    """Handle API response errors"""
    try:
        error_data = response.json()
        if "detail" in error_data:
            if isinstance(error_data["detail"], str):
                st.error(f"❌ {error_data['detail']}")
            elif isinstance(error_data["detail"], list):
                for error in error_data["detail"]:
                    st.error(f"❌ {error.get('msg', str(error))}")
            else:
                st.error(f"❌ {str(error_data['detail'])}")
        elif "message" in error_data:
            st.error(f"❌ {error_data['message']}")
        else:
            st.error(f"❌ API Error {response.status_code}: {response.text}")
    except:
        st.error(f"❌ Error {response.status_code}: {response.text}")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def validate_pdf_file(file) -> bool:
    """Validate uploaded PDF file"""
    if file is None:
        return False
    
    # Check file type
    if not file.name.lower().endswith('.pdf'):
        st.error("❌ Only PDF files are allowed.")
        return False
    
    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB in bytes
    if len(file.getvalue()) > max_size:
        st.error(f"❌ File size exceeds 50MB limit.")
        return False
    
    return True

def parse_sse_stream(stream):
    """Parse Server-Sent Events stream"""
    for line in stream:
        if line:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                    yield event_data
                except json.JSONDecodeError:
                    continue

def get_role_icon(role: str) -> str:
    """Get icon for user role"""
    icons = {
        "superadmin": "👑",
        "admin": "🛠️",
        "user": "👤"
    }
    return icons.get(role.lower(), "👤")

def get_document_icon(is_public: bool) -> str:
    """Get icon for document visibility"""
    return "🌐" if is_public else "🔒"

def display_user_badge(user_data: Dict[str, Any]):
    """Display user badge with role"""
    role = user_data.get('role', 'user').lower()
    username = user_data.get('username', 'Unknown')
    is_active = user_data.get('is_active', True)
    
    icon = get_role_icon(role)
    status = "🟢" if is_active else "🔴"
    
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        st.write(icon)
    with col2:
        st.write(f"**{username}**")
        st.caption(f"{role.title()}")
    with col3:
        st.write(status)

def create_user_form(edit_mode: bool = False, user_data: Dict[str, Any] = None):
    """Create user form for create/edit"""
    if user_data is None:
        user_data = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        email = st.text_input("Email", value=user_data.get('email', ''))
        username = st.text_input("Username", value=user_data.get('username', ''))
        full_name = st.text_input("Full Name", value=user_data.get('full_name', ''))
    
    with col2:
        password = st.text_input("Password", type="password") if not edit_mode else None
        
        role_options = ["user", "admin", "superadmin"]
        default_role = user_data.get('role', 'user')
        if default_role not in role_options:
            default_role = 'user'
        
        role = st.selectbox("Role", role_options, index=role_options.index(default_role))
        
        if edit_mode:
            is_active = st.checkbox("Active", value=user_data.get('is_active', True))
    
    return {
        "email": email,
        "username": username,
        "full_name": full_name,
        "password": password if not edit_mode else None,
        "role": role,
        "is_active": is_active if edit_mode else True
    }