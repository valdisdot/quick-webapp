import streamlit as st

from quick_webapp.ui.security.basic.page import render_login_page
from quick_webapp.webapp import service_page
from context import webapp, user_service, session_id_key, home_page

def __registration_default_user_details() -> dict:
    return {
        "self_registered": True
    }

service_page()
render_login_page(
    user_service(),
    session_id_key(),
    home_page(),
    "registraction",
    "user",
    registration_default_user_details_supplier=__registration_default_user_details
)