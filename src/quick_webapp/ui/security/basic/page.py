from typing import Any, Literal
from collections.abc import Callable, Iterable
from pathlib import Path
import streamlit as st
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.curent_user_service import UserService
from quick_webapp.ui import read_cookie, get_browser_locate, get_browser_timezone, get_browser_user_agent, get_ip_address
from quick_webapp.ui.action_table import action_table
from quick_webapp.ui.security.basic.form import login_form, registration_form, set_password_form, edit_user_form, create_user_form


class SecurityUIConfig:
    """
    A record class to store security related UI compifuration like button labels, texts etc.
    """

    def __init__(
        self,
        # Login form
        login_title: str = "Login",
        user_name_label: str = "Username",
        password_label: str = "Password",
        login_button_label: str = "Login",
        registration_button_label: str = "Registration",
        login_help_text: str | None = None,

        # Registration form
        registration_title: str = "Registration",
        full_name_label: str | None = "Full name",
        confirm_password_label: str = "Confirm password",
        register_button_label: str = "Register",
        registration_login_button_label: str = "Login",
        registration_help_text: str | None = None,

        # Set password form
        set_password_title: str = "Set a password",
        new_password_label: str = "New password",
        confirm_new_password_label: str = "Confirm new password",
        set_password_button_label: str = "Set",

        # Create user form
        create_user_title: str = "Create a user",
        is_ui_user_label: str = "UI user",
        is_service_user_label: str = "Service user",
        roles_label: str = "Roles",
        is_active_label: str = "Active",
        is_locked_label: str = "Locked",
        is_password_set_required_label: str = "Require password set",
        create_user_button_label: str = "Create",

        # Edit user form
        edit_user_title: str = "Edit a user",
        save_button_label: str = "Save",

        # Manage users pages
        clear_all_expired_sessions_label: str = "Clear expired",
        create_new_user_button_label: str = "New user",
        search_by_user_name_text_field_label: str = "User name:",
        search_by_user_name_button: str = "Search",
        user_name_column_label: str = "username",
        name_column_label: str = "Name",
        is_ui_user_column_label: str = "Regular user?",
        is_service_user_column_label: str = "Service user?",
        roles_column_label: str = "Roles",
        locked_column_label: str = "Is locked?",
        active_column_label: str = "Is active?",
        requires_password_update_column_label: str = "Must set password?",
        sessions_column_label: str = "Sessions",
        token_sessions_column_label: str = "Token sessions",
        logout_user_button_label: str = "Logout",
        edit_user_button_label: str = "Edit",
        no_users_found: str = "No users were found...",
        next_page_button_label: str = "Next >",
        back_page_button_label: str = "< Back",

        # Shared texts
        details_label: str = "Details",
        help_badge: str = "🛟",
        exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception),
        passwords_do_not_match_text: str = "Passwords do not match!",
        true_label: str = "✅",
        false_label: str = "⬜",
        null_text: str = "Not set",
        badge_background_color: str = "#6569C3",
        badge_foreground_color: str = "#ffffff"
    ):
        # Login form
        self.__login_title = login_title
        self.__user_name_label = user_name_label
        self.__password_label = password_label
        self.__login_button_label = login_button_label
        self.__registration_button_label = registration_button_label
        self.__login_help_text = login_help_text

        # Registration form
        self.__registration_title = registration_title
        self.__full_name_label = full_name_label
        self.__confirm_password_label = confirm_password_label
        self.__register_button_label = register_button_label
        self.__registration_login_button_label = registration_login_button_label
        self.__registration_help_text = registration_help_text

        # Set password form
        self.__set_password_title = set_password_title
        self.__new_password_label = new_password_label
        self.__confirm_new_password_label = confirm_new_password_label
        self.__set_password_button_label = set_password_button_label

        # Create user form
        self.__create_user_title = create_user_title
        self.__is_ui_user_label = is_ui_user_label
        self.__is_service_user_label = is_service_user_label
        self.__roles_label = roles_label
        self.__is_active_label = is_active_label
        self.__is_locked_label = is_locked_label
        self.__is_password_set_required_label = is_password_set_required_label
        self.__create_user_button_label = create_user_button_label

        # Edit user form
        self.__edit_user_title = edit_user_title
        self.__save_button_label = save_button_label

        # Manage users pages
        self.__clear_all_expired_sessions_label = clear_all_expired_sessions_label
        self.__create_new_user_button_label = create_new_user_button_label
        self.__search_by_user_name_text_field_label = search_by_user_name_text_field_label
        self.__search_by_user_name_button = search_by_user_name_button
        self.__user_name_column_label = user_name_column_label
        self.__name_column_label = name_column_label
        self.__ui_user_column_label = is_ui_user_column_label
        self.__service_user_column_label = is_service_user_column_label
        self.__roles_column_label = roles_column_label
        self.__locked_column_label = locked_column_label
        self.__active_column_label = active_column_label
        self.__requires_password_update_column_label = requires_password_update_column_label
        self.__sessions_column_label = sessions_column_label
        self.__token_sessions_column_label = token_sessions_column_label
        self.__edit_user_button_label = edit_user_button_label
        self.__logout_user_button_label = logout_user_button_label
        self.__no_users_found = no_users_found
        self.__next_page_button_label = next_page_button_label
        self.__back_page_button_label = back_page_button_label

        # Shared texts
        self.__details_label = details_label
        self.__help_badge = help_badge
        self.__exception_text_mapper = exception_text_mapper
        self.__passwords_do_not_match_text = passwords_do_not_match_text
        self.__true_label = true_label
        self.__false_label = false_label
        self.__null_text = null_text
        self.__badge_background_color = badge_background_color
        self.__badge_foreground_color = badge_foreground_color

    # Login form

    @property
    def login_title(self) -> str:
        return self.__login_title

    @property
    def user_name_label(self) -> str:
        return self.__user_name_label

    @property
    def password_label(self) -> str:
        return self.__password_label

    @property
    def login_button_label(self) -> str:
        return self.__login_button_label

    @property
    def registration_button_label(self) -> str:
        return self.__registration_button_label

    @property
    def login_help_text(self) -> str | None:
        return self.__login_help_text

    # Registration form

    @property
    def registration_title(self) -> str:
        return self.__registration_title

    @property
    def full_name_label(self) -> str | None:
        return self.__full_name_label

    @property
    def confirm_password_label(self) -> str:
        return self.__confirm_password_label

    @property
    def register_button_label(self) -> str:
        return self.__register_button_label

    @property
    def registration_login_button_label(self) -> str:
        return self.__registration_login_button_label

    @property
    def registration_help_text(self) -> str | None:
        return self.__registration_help_text

    # Set password form

    @property
    def set_password_title(self) -> str:
        return self.__set_password_title

    @property
    def new_password_label(self) -> str:
        return self.__new_password_label

    @property
    def confirm_new_password_label(self) -> str:
        return self.__confirm_new_password_label

    @property
    def set_password_button_label(self) -> str:
        return self.__set_password_button_label

    # Create user form

    @property
    def create_user_title(self) -> str:
        return self.__create_user_title

    @property
    def is_ui_user_label(self) -> str:
        return self.__is_ui_user_label

    @property
    def is_service_user_label(self) -> str:
        return self.__is_service_user_label

    @property
    def roles_label(self) -> str:
        return self.__roles_label

    @property
    def is_active_label(self) -> str:
        return self.__is_active_label

    @property
    def is_locked_label(self) -> str:
        return self.__is_locked_label

    @property
    def is_password_set_required_label(self) -> str:
        return self.__is_password_set_required_label

    @property
    def create_user_button_label(self) -> str:
        return self.__create_user_button_label

    # Edit user form

    @property
    def edit_user_title(self) -> str:
        return self.__edit_user_title

    @property
    def save_button_label(self) -> str:
        return self.__save_button_label

    # Manage users pages

    @property
    def clear_all_expired_sessions_label(self) -> str:
        return self.__clear_all_expired_sessions_label

    @property
    def create_new_user_button_label(self) -> str:
        return self.__create_new_user_button_label

    @property
    def search_by_user_name_text_field_label(self) -> str:
        return self.__search_by_user_name_text_field_label

    @property
    def search_by_user_name_button(self) -> str:
        return self.__search_by_user_name_button

    @property
    def user_name_column_label(self) -> str:
        return self.__user_name_column_label

    @property
    def name_column_label(self) -> str:
        return self.__name_column_label

    @property
    def ui_user_column_label(self) -> str:
        return self.__ui_user_column_label

    @property
    def service_user_column_label(self) -> str:
        return self.__service_user_column_label

    @property
    def roles_column_label(self) -> str:
        return self.__roles_column_label

    @property
    def locked_column_label(self) -> str:
        return self.__locked_column_label

    @property
    def active_column_label(self) -> str:
        return self.__active_column_label

    @property
    def requires_password_update_column_label(self) -> str:
        return self.__requires_password_update_column_label

    @property
    def sessions_column_label(self) -> str:
        return self.__sessions_column_label

    @property
    def token_sessions_column_label(self) -> str:
        return self.__token_sessions_column_label

    @property
    def edit_user_button_label(self) -> str:
        return self.__edit_user_button_label

    @property
    def logout_user_button_label(self) -> str:
        return self.__logout_user_button_label

    @property
    def no_users_found(self) -> str:
        return self.__no_users_found

    @property
    def next_page_button_label(self) -> str:
        return self.__next_page_button_label
    
    @property
    def back_page_button_label(self) -> str:
        return self.__back_page_button_label

    # Shared texts

    @property
    def details_label(self) -> str:
        return self.__details_label

    @property
    def help_badge(self) -> str:
        return self.__help_badge

    @property
    def exception_text_mapper(self) -> Callable[[Exception], str]:
        return self.__exception_text_mapper

    @property
    def passwords_do_not_match_text(self) -> str:
        return self.__passwords_do_not_match_text

    @property
    def true_label(self) -> str:
        return self.__true_label

    @property
    def false_label(self) -> str:
        return self.__false_label

    @property
    def null_text(self) -> str:
        return self.__null_text
    
    @property
    def badge_background_color(self) -> str:
        return self.__badge_background_color

    @property
    def badge_foreground_color(self) -> str:
        return self.__badge_foreground_color


@st.fragment
def render_login_page(
    user_service: UserService,
    session_id_key: str,
    logged_in_page_path: str | Path | st.Page,
    registration_key: str | None = None,
    registration_default_roles: str | Iterable[str] | None = None,
    registration_default_active_status: bool | None = None,
    registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None = None,
    security_ui_config: SecurityUIConfig = SecurityUIConfig()
):
    """
    Renders a default login page with login_form, registration_form, set_password_form from ui.security.basic.form package.

    Rules applied from the forms too - if registration_key is empty or blank then registration won't be accesible.

    After login completed the user will be redirected to logged_in_page_path.

    Texts and error render could be set up with security_ui_config.
    """

    session_id = read_cookie(session_id_key)

    if session_id is None or not user_service.is_logged_in(session_id, get_browser_locate(), get_browser_timezone(), get_browser_user_agent(), get_ip_address()):
        if registration_key and read_cookie(registration_key) == "true":
            registration_form(
                user_service,
                registration_default_roles,
                registration_default_active_status,
                registration_default_user_details_supplier,
                registration_key,
                security_ui_config.registration_title,
                security_ui_config.user_name_label,
                security_ui_config.full_name_label,
                security_ui_config.password_label,
                security_ui_config.confirm_password_label,
                security_ui_config.register_button_label,
                security_ui_config.login_button_label,
                security_ui_config.help_badge,
                security_ui_config.registration_help_text,
                security_ui_config.exception_text_mapper,
                security_ui_config.passwords_do_not_match_text
            )
        else:
            login_form(
                user_service, 
                session_id_key, 
                registration_key, 
                security_ui_config.login_title,
                security_ui_config.user_name_label,
                security_ui_config.password_label,
                security_ui_config.login_button_label,
                security_ui_config.register_button_label,
                security_ui_config.login_help_text,
                security_ui_config.help_badge,
                security_ui_config.exception_text_mapper
            )
    else:
        if user_service.is_new_password_update_required(session_id):
            set_password_form(
                user_service,
                session_id_key,
                security_ui_config.set_password_title,
                security_ui_config.password_label,
                security_ui_config.new_password_label,
                security_ui_config.confirm_new_password_label,
                security_ui_config.save_button_label,
                security_ui_config.exception_text_mapper,
                security_ui_config.passwords_do_not_match_text
            )
        else:
            st.switch_page(logged_in_page_path)

def __call_edit_user_form(user: User, user_service: UserService, page_context: dict[str, Any], security_ui_config: SecurityUIConfig, key_suffix: str):
    edit_user_form(
        user.user_name, 
        user_service,
        page_context,
        security_ui_config.edit_user_title,
        security_ui_config.full_name_label,
        security_ui_config.password_label,
        security_ui_config.confirm_password_label,
        security_ui_config.roles_label,
        security_ui_config.is_ui_user_label,
        security_ui_config.is_service_user_label,
        security_ui_config.is_active_label,
        security_ui_config.is_locked_label,
        security_ui_config.is_password_set_required_label,
        security_ui_config.details_label,
        security_ui_config.save_button_label,
        security_ui_config.exception_text_mapper,
        security_ui_config.passwords_do_not_match_text,
        key_suffix
    )

    page_context["do_search"] = True

def __call_create_user_form(user_service: UserService, registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None, page_context: dict[str, Any], security_ui_config: SecurityUIConfig, key_suffix: str):
    create_user_form(
        user_service,
        registration_default_user_details_supplier,
        page_context,
        security_ui_config.create_user_title,
        security_ui_config.user_name_label,
        security_ui_config.full_name_label,
        security_ui_config.password_label,
        security_ui_config.confirm_password_label,
        security_ui_config.roles_label,
        security_ui_config.is_ui_user_label,
        security_ui_config.is_service_user_label,
        security_ui_config.is_active_label,
        security_ui_config.is_locked_label,
        security_ui_config.is_password_set_required_label,
        security_ui_config.details_label,
        security_ui_config.create_user_button_label,
        security_ui_config.exception_text_mapper,
        security_ui_config.passwords_do_not_match_text,
        key_suffix
    )

    page_context["do_search"] = True

def __render_user_roles(user: User, background: str, foreground: str):
    with st.container(horizontal=True, gap="xxsmall"):
        for role in user.roles:
            st.write(f':color[{role}]{{background="{background}" foreground="{foreground}"}}')

def __setup_render_all_users_management_page(security_ui_config: SecurityUIConfig, user_service: UserService, page_context: dict[str, Any], column_ratio_spec: list[int], key_suffix: str):
    page_context["data_mappers"] = {
        security_ui_config.user_name_column_label: lambda user: st.write(f"{user.user_name}"),
        security_ui_config.name_column_label: lambda user: st.write(f"**{user.name}**" if user.name else f':color[{security_ui_config.null_text}]{{foreground="#6b6b6b" background="#e3e3e3"}}'),
        security_ui_config.ui_user_column_label: lambda user: st.write(security_ui_config.true_label if user.is_ui_user else security_ui_config.false_label),
        security_ui_config.service_user_column_label: lambda user: st.write(security_ui_config.true_label if user.is_service_user else security_ui_config.false_label),
        security_ui_config.roles_column_label: lambda user: __render_user_roles(user, security_ui_config.badge_background_color, security_ui_config.badge_foreground_color),
        security_ui_config.active_column_label: lambda user: st.write(security_ui_config.true_label if user.active else security_ui_config.false_label),
        security_ui_config.locked_column_label: lambda user: st.write(security_ui_config.true_label if user.locked else security_ui_config.false_label),
        security_ui_config.requires_password_update_column_label: lambda user: st.write(security_ui_config.true_label if user.requires_password_update else security_ui_config.false_label)
    }

    page_context["action_mappers"] = {
        security_ui_config.edit_user_button_label: lambda user: __call_edit_user_form(user, user_service, page_context, security_ui_config, key_suffix)
    }

    page_context["column_ratio_spec"] = column_ratio_spec
    page_context["q_user_name"] = None
    page_context["users"] = None
    page_context["do_search"] = None
    page_context["offset"] = 0
    page_context["has_more"] = None

@st.fragment
def render_all_users_management_page(
    user_service: UserService,
    registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None,
    context: dict[str, Any],
    users_per_page = 10,
    excluding_user_names: list[str] | str | None = None,
    security_ui_config: SecurityUIConfig = SecurityUIConfig(),
    width: int | Literal["stretch", "content"] = "stretch",
    key: str | None = None,
    user_name_column_x = 1,
    name_column_x = 1.5,
    is_ui_user_column_x = 0.5,
    is_service_user_column_x = 0.5,
    roles_column_x = 2.5,
    active_column_x = 0.5,
    locked_column_x = 0.5,
    password_set_required_column_x = 0.5,
    edit_button_column_x = 0.5
):
    """
    Renders a basic user management page.
    
    Do not use this method inside the st.dialog since the method calls user editor that is st.dialig itself, and calling dialog from a dialog is not supported in Streamlit. 
    """
    
    key = f"render_all_users_management_page_{key}" if key else "render_all_users_management_page"
    if not key in context:
        page_context = {}
        __setup_render_all_users_management_page(security_ui_config, user_service, page_context, [user_name_column_x, name_column_x, is_ui_user_column_x, is_service_user_column_x, roles_column_x, active_column_x, locked_column_x, password_set_required_column_x, edit_button_column_x], key)
        context[key] = page_context
    else:
        page_context = context[key]

    if not f"{key}_search_by_user_name_text_field" in st.session_state:
        st.session_state[f"{key}_search_by_user_name_text_field"] = page_context["q_user_name"]

    users = page_context.get("users")
    if page_context["do_search"] or users is None:
        page_context["do_search"] = None
        users = user_service.fetch_users(page_context["q_user_name"], page_context["offset"], users_per_page + 1, excluding_user_names)
        page_context["has_more"] = len(users) > users_per_page
        users = users[:users_per_page]
        page_context["users"] = users

    with st.container(width=width):
        if st.button(security_ui_config.create_new_user_button_label, type="primary", key=f"{key}_create_new_user"):
            __call_create_user_form(user_service, registration_default_user_details_supplier, page_context, security_ui_config, key)

        with st.container(horizontal=True, vertical_alignment="bottom", width="content", key=f"{key}_search"):
            q_user_name = st.text_input(security_ui_config.search_by_user_name_text_field_label, "", width=350, key=f"{key}_search_by_user_name_text_field")
            page_context["q_user_name"] = q_user_name if q_user_name else ""
            if st.button("Search", type="primary", key=f"{key}_search_by_user_name_button"):
                page_context["offset"] = 0
                page_context["do_search"] = True
                st.rerun(scope="fragment")

        if users:
            action_table(
                users,
                security_ui_config.no_users_found,
                page_context["data_mappers"],
                page_context["action_mappers"],
                container_width="stretch",
                column_ratio_spec=page_context["column_ratio_spec"],
                key_suffix=f"{key}_users"
            )

            with st.container(horizontal=True, gap="xxsmall"):
                offset = page_context["offset"]
                if offset > 0 and st.button(security_ui_config.back_page_button_label, key=f"{key}_back_page"):
                    offset = offset - users_per_page
                    page_context["offset"] = 0 if offset < 0 else offset
                    page_context["do_search"] = True
                    st.rerun(scope="fragment")

                if page_context["has_more"] and st.button(security_ui_config.next_page_button_label, key=f"{key}_next_page"):
                    page_context["offset"] = offset + users_per_page
                    page_context["do_search"] = True
                    st.rerun(scope="fragment")

        else:
            st.write(security_ui_config.no_users_found)

def __call_logout_user(user: User, user_service: UserService, page_context: dict[str, Any]):
    user_service.close_all_sessions(user.user_name)
    page_context["do_search"] = True
    st.rerun(scope="fragment")

def __setup_render_current_users_management_page(security_ui_config: SecurityUIConfig, user_service: UserService, page_context: dict[str, Any], column_ratio_spec: list[int], key_suffix: str):
    page_context["data_mappers"] = {
        security_ui_config.user_name_column_label: lambda session_info: st.write(f"{session_info.user.user_name}"),
        security_ui_config.name_column_label: lambda session_info: st.write(f"**{session_info.user.name}**" if session_info.user.name else ':color[Not set]{foreground="#6b6b6b" background="#e3e3e3"}'),
        security_ui_config.ui_user_column_label: lambda session_info: st.write(security_ui_config.true_label if session_info.user.is_ui_user else security_ui_config.false_label),
        security_ui_config.service_user_column_label: lambda session_info: st.write(security_ui_config.true_label if session_info.user.is_service_user else security_ui_config.false_label),
        security_ui_config.roles_column_label: lambda session_info: __render_user_roles(session_info.user, security_ui_config.badge_background_color, security_ui_config.badge_foreground_color),
        security_ui_config.sessions_column_label: lambda session_info: st.write(session_info.user_sessions_count),
        security_ui_config.token_sessions_column_label: lambda session_info: st.write(session_info.token_sessions_count)
    }

    page_context["action_mappers"] = {
        security_ui_config.edit_user_button_label: lambda session_info: __call_edit_user_form(session_info.user, user_service, page_context, security_ui_config, key_suffix),
        security_ui_config.logout_user_button_label: lambda session_info: __call_logout_user(session_info.user, user_service, page_context)
    }

    page_context["column_ratio_spec"] = column_ratio_spec
    page_context["q_user_name"] = None
    page_context["session_infos"] = None
    page_context["do_search"] = None
    page_context["offset"] = 0
    page_context["has_more"] = None

@st.fragment
def render_current_users_management_page(
    user_service: UserService,
    context: dict[str, Any],
    users_per_page = 10,
    excluding_user_names: list[str] | str | None = None,
    security_ui_config: SecurityUIConfig = SecurityUIConfig(),
    width: int | Literal["stretch", "content"] = "stretch",
    key: str | None = None,
    user_name_column_x = 1,
    name_column_x = 1.5,
    is_ui_user_column_x = 0.5,
    is_service_user_column_x = 0.5,
    roles_column_x = 2.5,
    sessions_column_x = 0.7,
    token_sessions_column_x = 0.7,
    buttons_column_x = 1
):
    """
    Renders a basic current user management page.

    Do not use this method inside the st.dialog since the method calls user editor that is st.dialig itself, and calling dialog from a dialog is not supported in Streamlit. 
    """
    
    key = f"render_current_users_management_page_{key}" if key else "render_current_users_management_page"
    if not key in context:
        page_context = {}
        __setup_render_current_users_management_page(security_ui_config, user_service, page_context, [user_name_column_x, name_column_x, is_ui_user_column_x, is_service_user_column_x, roles_column_x, sessions_column_x, token_sessions_column_x, buttons_column_x], key)
        context[key] = page_context
    else:
        page_context = context[key]

    if not f"{key}_search_by_user_name_text_field" in st.session_state:
        st.session_state[f"{key}_search_by_user_name_text_field"] = page_context["q_user_name"]

    with st.container(width=width):
        if st.button(security_ui_config.clear_all_expired_sessions_label, type="primary", key=f"{key}_clear_all_expired_sessions"):
            user_service.clear_all_expired_sessions()

        with st.container(horizontal=True, vertical_alignment="bottom", width="content", key=f"{key}_search"):
            q_user_name = st.text_input(security_ui_config.search_by_user_name_text_field_label, "", width=350, key=f"{key}_search_by_user_name_text_field")
            page_context["q_user_name"] = q_user_name if q_user_name else ""
            if st.button("Search", type="primary", key=f"{key}_search_by_user_name_button"):
                page_context["offset"] = 0
                page_context["do_search"] = True
                st.rerun(scope="fragment")

        session_infos = page_context.get("session_infos")
        if page_context["do_search"] or session_infos is None:
            page_context["do_search"] = None
            session_infos = user_service.get_all_sessions_info(page_context["q_user_name"], page_context["offset"], users_per_page + 1, excluding_user_names)
            page_context["has_more"] = len(session_infos) > users_per_page
            session_infos = session_infos[:users_per_page]
            page_context["session_infos"] = session_infos

        if session_infos:
            action_table(
                session_infos,
                security_ui_config.no_users_found,
                page_context["data_mappers"],
                page_context["action_mappers"],
                container_width="stretch",
                column_ratio_spec=page_context["column_ratio_spec"],
                key_suffix=f"{key}_users"
            )

            with st.container(horizontal=True, gap="xxsmall"):
                offset = page_context["offset"]
                if offset > 0 and st.button(security_ui_config.back_page_button_label, key=f"{key}_back_page"):
                    offset = offset - users_per_page
                    page_context["offset"] = 0 if offset < 0 else offset
                    page_context["do_search"] = True
                    st.rerun(scope="fragment")

                if page_context["has_more"] and st.button(security_ui_config.next_page_button_label, key=f"{key}_next_page"):
                    page_context["offset"] = offset + users_per_page
                    page_context["do_search"] = True
                    st.rerun(scope="fragment")

        else:
            st.write(security_ui_config.no_users_found)
