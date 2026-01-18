import streamlit as st
from pages import admin

def render_superadmin_page():
    """Render the superadmin page - delegates to admin panel"""
    admin.render_admin_page()