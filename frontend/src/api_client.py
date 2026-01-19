import requests
import streamlit as st
from typing import Optional, Dict, Any, List, Iterator


class APIClient:
    """HTTP client for backend API communication"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json"
        }

    # -------------------------
    # Auth helpers
    # -------------------------

    def set_token(self, token: str):
        self.headers["Authorization"] = f"Bearer {token}"

    def clear_token(self):
        self.headers.pop("Authorization", None)

    # -------------------------
    # Core request handler
    # -------------------------

    def make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"

        try:
            kwargs["headers"] = {
                **self.headers,
                **kwargs.get("headers", {})
            }

            response = requests.request(
                method=method,
                url=url,
                timeout=15,
                **kwargs
            )

            # Success responses
            if response.status_code in [200, 201]:
                return response.json()

            # Error handling - return error data for caller to handle
            try:
                error_data = response.json()
                if "detail" in error_data:
                    return {"error": True, "detail": error_data["detail"]}
                elif "message" in error_data:
                    return {"error": True, "detail": error_data["message"]}
                else:
                    return {"error": True, "detail": f"API Error {response.status_code}"}
            except Exception:
                return {"error": True, "detail": f"API Error {response.status_code}"}

        except requests.exceptions.ConnectionError:
            return {"error": True, "detail": "Cannot connect to backend. Is the server running?"}
        except requests.exceptions.Timeout:
            return {"error": True, "detail": "Request timed out."}
        except Exception as e:
            return {"error": True, "detail": f"Request failed: {str(e)}"}

    # -------------------------
    # Authentication
    # -------------------------

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Login using JSON body - FastAPI expects JSON, not form data"""

        payload = {
            "username": username,
            "password": password
        }

        response = self.make_request(
            "POST",
            "/api/v1/auth/login",
            json=payload
        )

        if response and "access_token" in response:
            self.set_token(response["access_token"])
            return response

        return None

    def logout(self) -> Optional[Dict[str, Any]]:
        response = self.make_request("POST", "/api/v1/auth/logout")
        self.clear_token()
        return response

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return self.make_request("GET", "/api/v1/users/me")

    # -------------------------
    # Documents
    # -------------------------

    def get_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        is_public: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        params = {"skip": skip, "limit": limit}
        if is_public is not None:
            params["is_public"] = is_public

        return self.make_request("GET", "/api/v1/documents", params=params) or []

    def get_chatable_documents(self) -> List[Dict[str, Any]]:
        response = self.make_request("GET", "/api/v1/chat/documents")
        return response.get("data", []) if response else []

    def upload_document(
        self,
        file,
        title: Optional[str] = None,
        description: Optional[str] = None,
        is_public: bool = True
    ) -> Optional[Dict[str, Any]]:

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
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

            try:
                error_data = response.json()
                st.error(f"❌ {error_data.get('detail', 'Upload failed')}")
            except Exception:
                st.error(f"❌ Upload Error {response.status_code}")

            return None

        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
            return None

    def process_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        return self.make_request(
            "POST",
            f"/api/v1/documents/{document_id}/process"
        )

    def create_embeddings(self, document_id: int) -> Optional[Dict[str, Any]]:
        return self.make_request(
            "POST",
            f"/api/v1/documents/{document_id}/create-embeddings"
        )
    
    def get_document_status(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document processing status"""
        return self.make_request("GET", f"/api/v1/documents/{document_id}/status")

    # -------------------------
    # Users (Admin / Superadmin)
    # -------------------------

    def get_users(self, skip: int = 0, limit: int = 100) -> Optional[Dict[str, Any]]:
        """Get list of users"""
        params = {"skip": skip, "limit": limit}
        response = self.make_request("GET", "/api/v1/users", params=params)
        return response if response else {"data": []}

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = "",
        role: str = "user"
    ) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        user_data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role
        }
        return self.make_request("POST", "/api/v1/users", json=user_data)

    def update_user(
        self,
        user_id: int,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update user information"""
        return self.make_request("PUT", f"/api/v1/users/{user_id}", json=kwargs)

    def delete_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Delete a user"""
        return self.make_request("DELETE", f"/api/v1/users/{user_id}")

    def toggle_user_active(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Toggle user active status"""
        return self.make_request(
            "POST",
            f"/api/v1/users/{user_id}/toggle-active"
        )


    # -------------------------
    # Chat streaming
    # -------------------------

    def chat_stream(
        self,
        document_id: int,
        query: str
    ) -> Optional[Iterator[bytes]]:

        url = f"{self.base_url}/api/v1/chat/stream"
        headers = {
            **self.headers,
            "Accept": "text/event-stream"
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    "document_id": document_id,
                    "query": query
                },
                stream=True,
                timeout=180  # Increased to 180s for long-running responses
            )

            if response.status_code == 200:
                return response.iter_lines()

            try:
                error_data = response.json()
                st.error(f"❌ {error_data.get('detail', 'Chat failed')}")
            except Exception:
                st.error(f"❌ Chat Error {response.status_code}")

            return None

        except requests.exceptions.Timeout:
            st.error("⚠️ Chat response timed out.")
            return None
        except Exception as e:
            st.error(f"❌ Streaming failed: {str(e)}")
            return None
