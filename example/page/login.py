import streamlit as st
from quick_webapp.ui.security.basic.form import login_form, registration_form, set_password_form
from quick_webapp.ui import read_cookie, get_browser_locate, get_browser_timezone
from quick_webapp.webapp import service_page
from context import webapp, user_service, session_id_key, home_page

service_page()
user_service = user_service()

with webapp().as_context("Login"):
    session_id_key = session_id_key()
    session_id = read_cookie(session_id_key)
    user_locale = get_browser_locate()
    user_timezone = get_browser_timezone()

    if session_id is None or not user_service.is_logged_in(session_id, user_locale, user_timezone):
        registration_clicked = bool(read_cookie("user_wanna_reg", False))
        if registration_clicked:
            registration_form(
                user_service,
                "user",
                True,
                "user_wanna_reg"
            )
        else:
            login_form(
                user_service, 
                session_id_key=session_id_key, 
                registration_key="user_wanna_reg", 
                help_text="This is a help text and lorem ipsum!"
                )
    else:
        if user_service.is_new_password_update_required(session_id):
            set_password_form(
                user_service,
                session_id_key
            )
        else:
            st.switch_page(home_page())
    