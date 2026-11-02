import streamlit as st
from quick_webapp.ui import restart_browser_window
from context import current_user_service
from context import webapp
from quick_webapp.webapp import menu_page

menu_page("0_Home")
current_user_service = current_user_service()
current_user_service.only_permitted()

if st.query_params.get("reload"):
    st.query_params.clear()
    restart_browser_window()

user = current_user_service.get_user()
with webapp().as_context(f"Welcome to Quick WebApp Example, **{user.user_name}**!", page_title_render=st.header):
    pass