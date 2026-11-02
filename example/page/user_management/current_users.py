from typing import Any
import streamlit as st
from quick_webapp.webapp import menu_page
from quick_webapp import bean, session_bean
from quick_webapp.ui.page_context import PageContext
from quick_webapp.ui.action_table import action_table
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.user_service import UserService
from quick_webapp.ui.security.basic.form import manage_user_form, edit_user_form
from context import webapp, current_user_service, user_service


def __manage_user(user: User, context: dict[str, Any]):
    context["modified"] = True
    manage_user_form(user.user_name, user_service)

def __edit_user(user: User, context: dict[str, Any]):
    context["modified"] = True
    edit_user_form(user.user_name, user_service)

@bean(key="user_management_current_users_data_mappers")
def __data_mappers() -> dict[str, callable]:
    return {
        "Username": lambda user_session: st.write(f"**{user_session[0].user_name}**"),
        "Name": lambda user_session: st.write(user_session[0].name if user_session[0].name else ':color[Not set]{foreground="#6b6b6b" background="#e3e3e3"}'),
        "Roles": lambda user_session: st.write(" ".join(f':color[{role}]{{foreground="#f5fffa" background="#464bb4"}}' for role in user_session[0].roles)),
        "Sessions": lambda user_session: st.write(len(user_session[1]))
    }

@bean(key="user_management_current_users_action_mappers")
def __action_mappers() -> dict[str, callable]:
    return {
        "🧑‍💼": lambda dict_view: __manage_user(dict_view[0], __page_context().get_context()),
        "📝": lambda dict_view: __edit_user(dict_view[0], __page_context().get_context())
    }

@session_bean(key="user_management_current_users_page_context")
def __page_context() -> PageContext:
    return PageContext("user_management_all_users")

menu_page("9_User Management", "1_Current")
current_user_service = current_user_service()
current_user_service.only_permitted("admin")
user_service: UserService = user_service()

with webapp().as_context("User Management | Current", page_title_render=lambda title: st.subheader(title)):
    current_user_name = current_user_service.get_user().user_name
    current_users = user_service.get_all_user_sessions(current_user_name)

    if current_users:
        st.write("**Active users:**")
        action_table(
            current_users.items(),
            "No current users...",
            __data_mappers(),
            __action_mappers(),
            container_width=800,
            column_ratio_spec=[1, 1.2, 1, 0.4, 0.2, 0.2]
        )
    else:
        st.write("*No active users to manage...*")


