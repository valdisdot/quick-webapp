from typing import Any
import streamlit as st
from quick_webapp.webapp import menu_page
from quick_webapp import bean, session_bean
from quick_webapp.ui.action_table import action_table
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.user_service import UserService
from quick_webapp.ui.security.basic.page import render_all_users_management_page
from quick_webapp.ui.page_context import PageContext
from context import webapp, current_user_service, user_service


@session_bean(key="user_management_all_users_page_context")
def __page_context() -> PageContext:
    return PageContext("user_management_all_users")

menu_page("9_User Management", "1_All")
current_user_service = current_user_service()
current_user_service.only_permitted("admin")

with webapp().as_context("User Management | All", page_title_render=lambda title: st.subheader(title)):
    render_all_users_management_page(
        user_service(),
        __page_context().get_context(),
        10,
        current_user_service.get_user().user_name
    )