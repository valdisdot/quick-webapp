from typing import Any, Literal
from collections.abc import Callable, Iterable
from pathlib import Path
import streamlit as st
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.curent_user_service import UserService
from quick_webapp.ui import read_cookie, get_browser_locate, get_browser_timezone
from quick_webapp.ui.action_table import action_table
from quick_webapp.ui.security.basic.form import login_form, registration_form, set_password_form, edit_user_form


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

        # Manage user form
        manage_user_title: str = "Manage a user",
        active_label: str = "Active",
        not_active_label: str = "Not active",
        sessions_label: str = "Sessions",
        lock_label: str = "Lock",
        unlock_label: str = "Unlock",
        logout_label: str = "Logout",

        # Manage users pages
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
        edit_user_button_label: str = "Edit",
        logout_user_button_label: str = "Logout",
        no_users_found: str = "No users were found...",

        # Shared texts
        help_badge: str = "🛟",
        help_text: str | None = None,
        exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception),
        passwords_do_not_match_text: str = "Passwords do not match!",
        true_label: str = "✅",
        false_label: str = "⬜",
        null_text: str = "Not set"
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

        # Manage user form
        self.__manage_user_title = manage_user_title
        self.__active_label = active_label
        self.__not_active_label = not_active_label
        self.__sessions_label = sessions_label
        self.__lock_label = lock_label
        self.__unlock_label = unlock_label
        self.__logout_label = logout_label
        self.__no_users_found = no_users_found

        # Manage users pages
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
        self.__edit_user_button_label = edit_user_button_label
        self.__logout_user_button_label = logout_user_button_label

        # Shared texts
        self.__help_badge = help_badge
        self.__help_text = help_text
        self.__exception_text_mapper = exception_text_mapper
        self.__passwords_do_not_match_text = passwords_do_not_match_text
        self.__true_label = true_label
        self.__false_label = false_label
        self.__null_text = null_text

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

    # Manage user form

    @property
    def manage_user_title(self) -> str:
        return self.__manage_user_title

    @property
    def active_label(self) -> str:
        return self.__active_label

    @property
    def not_active_label(self) -> str:
        return self.__not_active_label

    @property
    def sessions_label(self) -> str:
        return self.__sessions_label

    @property
    def lock_label(self) -> str:
        return self.__lock_label

    @property
    def unlock_label(self) -> str:
        return self.__unlock_label

    @property
    def logout_label(self) -> str:
        return self.__logout_label

    # Manage users pages

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
    def edit_user_button_label(self) -> str:
        return self.__edit_user_button_label

    @property
    def logout_user_button_label(self) -> str:
        return self.__logout_user_button_label

    @property
    def no_users_found(self) -> str:
        return self.__no_users_found

    # Shared texts

    @property
    def help_badge(self) -> str:
        return self.__help_badge

    @property
    def help_text(self) -> str | None:
        return self.__help_text

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


@st.fragment
def render_login_page(
    user_service: UserService,
    session_id_key: str,
    logged_in_page_path: str | Path | st.Page,
    registration_key: str | None,
    registration_default_roles: str | Iterable[str] | None = None,
    registration_default_active_status: bool | None = None,
    security_ui_config: SecurityUIConfig = SecurityUIConfig(),
):
    """
    Renders a default login page with login_form, registration_form, set_password_form from ui.security.basic.form package.

    Rules applied from the forms too - if registration_key is empty or blank then registration won't be accesible.

    After login completed the user will be redirected to logged_in_page_path.

    Texts and error render could be set up with security_ui_config.
    """

    session_id = read_cookie(session_id_key)
    user_locale = get_browser_locate()
    user_timezone = get_browser_timezone()

    if session_id is None or not user_service.is_logged_in(session_id, user_locale, user_timezone):
        if registration_key and read_cookie(registration_key) == "true":
            registration_form(
                user_service,
                registration_default_roles,
                registration_default_active_status,
                registration_key,
                security_ui_config.registration_title,
                security_ui_config.user_name_label,
                security_ui_config.full_name_label,
                security_ui_config.password_label,
                security_ui_config.confirm_password_label,
                security_ui_config.register_button_label,
                security_ui_config.login_button_label,
                security_ui_config.help_badge,
                security_ui_config.help_text,
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
                security_ui_config.help_text,
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
        security_ui_config.save_button_label,
        security_ui_config.exception_text_mapper,
        security_ui_config.passwords_do_not_match_text,
        key_suffix
    )
    page_context["do_search"] = True

def __render_user_roles(user: User):
    with st.container(horizontal=True, gap="xxsmall"):
        for role in user.roles:
            st.write(f':color[{role}]{{foreground="#f5fffa" background="#464bb4"}}')

def __setup_render_all_users_management_page(security_ui_config: SecurityUIConfig, user_service: UserService, page_context: dict[str, Any], key_suffix: str):
    page_context["data_mappers"] = {
        security_ui_config.user_name_column_label: lambda user: st.write(f"`{user.user_name}`"),
        security_ui_config.name_column_label: lambda user: st.write(f"**{user.name}**" if user.name else ':color[Not set]{foreground="#6b6b6b" background="#e3e3e3"}'),
        security_ui_config.ui_user_column_label: lambda user: st.write(security_ui_config.true_label if user.is_ui_user else security_ui_config.false_label),
        security_ui_config.service_user_column_label: lambda user: st.write(security_ui_config.true_label if user.is_service_user else security_ui_config.false_label),
        security_ui_config.roles_column_label: __render_user_roles,
        security_ui_config.active_column_label: lambda user: st.write(security_ui_config.true_label if user.active else security_ui_config.false_label),
        security_ui_config.locked_column_label: lambda user: st.write(security_ui_config.true_label if user.locked else security_ui_config.false_label),
        security_ui_config.requires_password_update_column_label: lambda user: st.write(security_ui_config.true_label if user.requires_password_update else security_ui_config.false_label)
    }

    page_context["action_mappers"] = {
        security_ui_config.edit_user_button_label: lambda user: __call_edit_user_form(user, user_service, page_context, security_ui_config, key_suffix)
    }

    page_context["q_user_name"] = ""
    page_context["users"] = None
    page_context["do_search"] = None
    page_context["offset"] = 0
    page_context["has_more"] = None

@st.fragment
def render_all_users_management_page(
    user_service: UserService,
    context: dict[str, Any],
    users_per_page = 10,
    excluding_user_names: list[str] | str | None = None,
    security_ui_config: SecurityUIConfig = SecurityUIConfig(),
    width: int | Literal["stretch", "content"] = "stretch",
    key: str | None = None,
):
    key = f"render_all_users_management_page_{key}" if key else "render_all_users_management_page"
    if not key in context:
        page_context = {}
        __setup_render_all_users_management_page(security_ui_config, user_service, page_context, key)
        context[key] = page_context
    else:
        page_context = context[key]

    if not f"{key}_search_by_user_name_text_field" in st.session_state:
        st.session_state[f"{key}_search_by_user_name_text_field"] = page_context["q_user_name"]
    with st.container(width=width):
        with st.container(horizontal=True, vertical_alignment="bottom", width="content", key=f"{key}_search"):
            q_user_name = st.text_input(security_ui_config.search_by_user_name_text_field_label, "", width=350, key=f"{key}_search_by_user_name_text_field")
            page_context["q_user_name"] = q_user_name if q_user_name else ""
            if st.button("Search", type="primary", key=f"{key}_search_by_user_name_button"):
                page_context["offset"] = 0
                page_context["do_search"] = True

        users = page_context.get("users")
        if page_context["do_search"] or users is None:
            page_context["do_search"] = None
            users = user_service.fetch_users(page_context["q_user_name"], page_context["offset"], users_per_page + 1, excluding_user_names)
            page_context["has_more"] = len(users) > users_per_page
            users = users[:users_per_page]
            page_context["users"] = users

        if users:
            action_table(
                users,
                security_ui_config.no_users_found,
                page_context["data_mappers"],
                page_context["action_mappers"],
                container_width="stretch",
                column_ratio_spec=[1, 2, 0.5, 0.5, 2, 0.5, 0.5, 0.5, 0.5],
                key_suffix=f"{key}_users"
            )

            with st.container(horizontal=True, gap="xxsmall"):
                offset = page_context["offset"]
                if offset > 0 and st.button("<"):
                    offset = offset - users_per_page
                    page_context["offset"] = 0 if offset < 0 else offset
                    page_context["do_search"] = True
                    st.rerun(scope="fragment")

                if page_context["has_more"] and st.button(">"):
                    page_context["offset"] = offset + users_per_page
                    page_context["do_search"] = True
                    st.rerun(scope="fragment")

        else:
            st.write(security_ui_config.no_users_found)
