import requests
import json
import streamlit as st
from typing import Optional, Dict, Any, List

class APIClient:
    """HTTP client for backend API communication"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.headers["Authorization"] = f"Bearer {token}"
        st.session_state.token = token
    
    def clear_token(self):
        """Clear authentication token"""
        if "Authorization" in self.headers:
            del self.headers["Authorization"]
        if "token" in st.session_state:
            st.session_state.token = None
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to backend"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Add headers
            kwargs['headers'] = {**self.headers, **kwargs.get('headers', {})}
            
            # Make request
            response = requests.request(method, url, **kwargs)
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                # Handle API error
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        st.error(f"❌ {error_data['detail']}")
                    elif "message" in error_data:
                        st.error(f"❌ {error_data['message']}")
                except:
                    st.error(f"❌ API Error {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to the backend server. Please ensure the backend is running.")
            return None
        except Exception as e:
            st.error(f"❌ Request failed: {str(e)}")
            return None
    
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Login and get JWT token"""
        # Use OAuth2 password flow format
        form_data = {
            "username": username,
            "password": password
        }
        
        response = self.make_request(
            "POST",
            "/api/v1/auth/login",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response and "access_token" in response:
            self.set_token(response["access_token"])
            return response
        return None
    
    def logout(self):
        """Logout user"""
        response = self.make_request("POST", "/api/v1/auth/logout")
        self.clear_token()
        return response
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        return self.make_request("GET", "/api/v1/users/me")
    
    def get_documents(self, skip: int = 0, limit: int = 100, is_public: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get list of documents"""
        params = {"skip": skip, "limit": limit}
        if is_public is not None:
            params["is_public"] = is_public
        
        response = self.make_request("GET", "/api/v1/documents", params=params)
        return response or []
    
    def get_chatable_documents(self) -> List[Dict[str, Any]]:
        """Get documents ready for chatting"""
        response = self.make_request("GET", "/api/v1/chat/documents")
        if response and "data" in response:
            return response["data"]
        return []
    
    def chat_stream(self, document_id: int, query: str):
        """Stream chat response"""
        url = f"{self.base_url}/api/v1/chat/stream"
        headers = {**self.headers, "Accept": "text/event-stream"}
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"document_id": document_id, "query": query},
                stream=True
            )
            
            if response.status_code == 200:
                return response.iter_lines()
            else:
                # Handle error
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        st.error(f"❌ {error_data['detail']}")
                except:
                    st.error(f"❌ API Error {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"❌ Streaming request failed: {str(e)}")
            return None
    
    def upload_document(self, file, title: str = None, description: str = None, is_public: bool = True) -> Optional[Dict[str, Any]]:
        """Upload a PDF document"""
        url = f"{self.base_url}/api/v1/documents/upload"
        
        files = {
            "file": (file.name, file, "application/pdf")
        }
        
        data = {
            "is_public": str(is_public).lower()
        }
        
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        
        try:
            response = requests.post(
                url,
                headers={"Authorization": self.headers.get("Authorization", "")},
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Handle error
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        st.error(f"❌ {error_data['detail']}")
                except:
                    st.error(f"❌ Upload Error {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
            return None
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of users"""
        params = {"skip": skip, "limit": limit}
        response = self.make_request("GET", "/api/v1/users", params=params)
        return response or []
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        return self.make_request("POST", "/api/v1/users", json=user_data)
    
    def toggle_user_active(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Toggle user active status"""
        return self.make_request("POST", f"/api/v1/users/{user_id}/toggle-active")
    
    def process_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Process document for embeddings"""
        return self.make_request("POST", f"/api/v1/documents/{document_id}/process")
    
    def create_embeddings(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Create embeddings for document"""
        return self.make_request("POST", f"/api/v1/documents/{document_id}/create-embeddings")

# Global API client instance - initialized with hardcoded URL
api_client = APIClient("http://localhost:8000")

def get_api_client() -> APIClient:
    """Get the global API client instance"""
    global api_client
    
    # Restore token from session state if exists
    if st.session_state.get('token'):
        api_client.set_token(st.session_state.token)
    
    return api_client