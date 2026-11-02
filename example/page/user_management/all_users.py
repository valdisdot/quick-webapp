from typing import Any
import streamlit as st
from quick_webapp.webapp import menu_page
from quick_webapp import bean, session_bean
from quick_webapp.ui.action_table import action_table
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.user_service import UserService
from quick_webapp.ui.security.basic.form import edit_user_form
from quick_webapp.ui.page_context import PageContext
from context import webapp, current_user_service, user_service

def __switch_user_lock(user: User, context: dict[str, Any]):
    user_service.update_user_lock(user.user_name, not user.locked)
    context["modified"] = True
    st.rerun()

def __edit_user(user: User, context: dict[str, Any]):
    edit_user_form(user.user_name, user_service)
    context["modified"] = True

@bean(key="user_management_all_users_data_mappers")
def __data_mappers() -> dict[str, callable]:
    return {
        "Username": lambda user: st.write(f"**{user.user_name}**"),
        "Name": lambda user: st.write(user.name if user.name else ':color[Not set]{foreground="#6b6b6b" background="#e3e3e3"}'),
        "Roles": lambda user: st.write(" ".join(f':color[{role}]{{foreground="#f5fffa" background="#464bb4"}}' for role in user.roles)),
        "Locked": lambda user: st.write("🔴" if user.locked else "⚪")
    }

@bean(key="user_management_all_users_action_mappers")
def __action_mappers() -> dict[str, callable]:
    return {
        "🔒": lambda user: __switch_user_lock(user, __page_context().get_context()),
        "📝": lambda user: __edit_user(user, __page_context().get_context())
    }

@session_bean(key="user_management_all_users_page_context")
def __page_context() -> PageContext:
    return PageContext("user_management_all_users")


menu_page("9_User Management", "1_All")
current_user_service = current_user_service()
user_service: UserService = user_service()
current_user_service.only_permitted("admin")

with webapp().as_context("User Management | All", page_title_render=lambda title: st.subheader(title)):
    current_user_name = current_user_service.get_user().user_name
    page_context = __page_context().get_context()
    users_per_page = 10

    with st.container(horizontal=True, vertical_alignment="bottom"):
        q_user_name = st.text_input("User name:", "", width=350)
        if st.button("Search", type="primary") or "q_user_name" not in page_context:
            page_context["q_user_name"] = q_user_name
            page_context["offset"] = 0
            page_context["page"] = user_service.fetch_users(q_user_name, 0, users_per_page, current_user_name)
            page_context["has_next"] = len(page_context["page"]) == users_per_page and len(user_service.fetch_users(q_user_name, users_per_page, 1, current_user_name)) > 0

    if "page" in page_context:
        page = page_context["page"]
        offset = page_context.get("offset", 0)

        if page_context.get("modified"):
            page = user_service.fetch_users(q_user_name, offset, users_per_page, current_user_name)
            page_context["modified"] = False
            page_context["page"] = page

        if page:
            st.write("**Users:**")
            action_table(
                page,
                "No users...",
                __data_mappers(),
                __action_mappers(),
                container_width=800,
                column_ratio_spec=[1, 1.2, 1, 0.4, 0.2, 0.2]
            )

            has_next = page_context.get("has_next")
            has_previous = offset > 0

            if has_next or has_previous:
                clicked = False
                with st.container(horizontal=True):
                    if has_previous:
                        if st.button("<"):
                            clicked = True
                            offset = offset - users_per_page
                            page_context["offset"] = 0 if offset < 0 else offset

                    if has_next:
                        if st.button(">"):
                            clicked = True
                            offset = offset + users_per_page
                            page_context["offset"] = offset
                
                if clicked:
                    page_context["page"] = user_service.fetch_users(q_user_name, offset, users_per_page, current_user_name)
                    page_context["has_next"] = len(page_context["page"]) == users_per_page and len(user_service.fetch_users(q_user_name, offset + users_per_page, 1, current_user_name)) > 0
                    st.rerun()
        else:
            st.write(f"*No users like '{q_user_name}', honey!*")