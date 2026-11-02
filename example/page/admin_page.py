import streamlit as st
from quick_webapp.webapp import menu_page
from context import webapp
from context import current_user_service


menu_page("9_Admin", "1_Welcome, Admin")
current_user_service = current_user_service()
current_user_service.only_permitted("admin")

with webapp().as_context("This is an admin page title"):
    st.write("**You are an admin**")
    if st.button("Exit", type="primary"):
        current_user_service.logout()
