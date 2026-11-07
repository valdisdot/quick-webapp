import streamlit as st
from quick_webapp.webapp import menu_page
from quick_webapp import session_bean
from quick_webapp.ui.page_context import PageContext
from quick_webapp.ui.security.basic.page import render_current_users_management_page
from context import webapp, current_user_service, user_service


@session_bean(key="user_management_current_users_page_context")
def __page_context() -> PageContext:
    return PageContext("user_management_current_users")

menu_page("9_User Management", "1_Current")
current_user_service = current_user_service()
current_user_service.only_permitted("admin")

with webapp().as_context("User Management | Current", page_title_render=lambda title: st.subheader(title)):
    render_current_users_management_page(
        user_service(),
        __page_context().get_context(),
        10,
        current_user_service.get_user().user_name,
        roles_column_x=1.5,
        width=900
    )