import streamlit as st
from quick_webapp.ui.security.basic.page import render_login_page
from quick_webapp.webapp import service_page
from context import webapp, user_service, session_id_key, home_page

service_page()
render_login_page(
    user_service(),
    session_id_key(),
    home_page(),
    "registraction",
    "user"
)