from typing import Any
from collections.abc import Callable, Iterable
import streamlit as st
import quick_webapp.ui as ui
from quick_webapp.ui.editor import data_editor, Node
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.user_service import UserService, InvalidUserSessionException, UserLockedException, UserNotActiveException, UserNotFoundException, UserLayerException

def login_form(
        user_service: UserService,
        session_id_key: str,
        registration_key: str | None,
        title: str,
        user_name_label: str,
        password_label: str,
        login_button_label: str,
        registration_button_label: str,
        help_text: str | None,
        help_badge: str,
        exception_text_mapper: Callable[[Exception], str]
    ):
    """
    Displays login dialog.
    User session ID will be stored in browser cache with key 'session_id_key' key from this method params and then the gets refreshed.
    If user clicked on register button, browser cache will contain a cookie with 'registration_key' key from this method params set to 1, and then the gets also refreshed.
    """

    @st.dialog(title, width="small", dismissible=False)
    def dialog():
        user_name = st.text_input(user_name_label)
        password = st.text_input(password_label, type="password")

        error = None

        session_id = None
        with st.container(width="stretch", horizontal=True):
            with st.container(width="stretch", horizontal=True, horizontal_alignment="left", vertical_alignment="center"):
                if help_text and len(help_text):
                    st.badge(label=help_badge, help=help_text)

                if registration_key and len(registration_key):
                    if st.button(registration_button_label, type="secondary"):
                        ui.write_cookie(registration_key, "true", user_service.session_lifespan_seconds)
                        ui.restart_browser_window()

            with st.container(width="content", horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
                if st.button(login_button_label, type="primary", shortcut="Enter"):
                    if user_name and password:
                        user_name = user_name.strip()
                        password = password.strip()

                        if len(user_name) and len(password):
                            try:
                                session_id = user_service.login(user_name, password, ui.get_browser_locate(), ui.get_browser_timezone(), ui.get_browser_user_agent(), ui.get_ip_address())
        
                            except Exception as e:
                                error = e

        if session_id:
            ui.write_cookie(session_id_key, session_id, user_service.session_lifespan_seconds)
            ui.delete_cookie(registration_key)
            ui.restart_browser_window()
        
        if error:
            st.error(exception_text_mapper(error))

    dialog()

def registration_form(
        user_service: UserService,
        default_roles: str | Iterable[str] | None,
        default_active_status: bool,
        registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None,
        registration_key: str,
        title: str,
        user_name_label: str,
        full_name_label: str | None,
        password_label: str,
        confirm_password_label: str,
        register_button_label: str,
        login_button_label: str,
        help_badge: str,
        help_text: str | None,
        exception_text_mapper: Callable[[Exception], str],
        passwords_do_not_match_text: str
    ):
    """
    Displays registration dialog. User only provide username, full name and password, role and active status must be specified withing parameters of this method.
    The method only registers a user, then the user must login.
    If user clicked on login button or got successfully registered, browser cache will remove a cookie with 'registration_key' key from this method params, and then the gets refreshed.
    """

    roles = []
    if default_roles:
        if isinstance(default_roles, str):
            roles.append(default_roles)
        elif isinstance(default_roles, Iterable):
            for role in default_roles:
                roles.append(str(role))

    @st.dialog(title, width="small", dismissible=False)
    def dialog():
        user_name = st.text_input(user_name_label)
        full_name = st.text_input(full_name_label) if full_name_label is not None else None
        password = st.text_input(password_label, type="password")
        confirm_password = st.text_input(confirm_password_label, type="password")

        error = None

        with st.container(width="stretch", horizontal=True):
            with st.container(width="stretch", horizontal=True, horizontal_alignment="left", vertical_alignment="center"):
                if help_text and len(help_text):
                    st.badge(label=help_badge, help=help_text)

                if st.button(login_button_label, type="secondary", shortcut="Esc"):
                    ui.delete_cookie(registration_key)
                    ui.restart_browser_window()

            with st.container(width="content", horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
                if st.button(register_button_label, type="primary", shortcut="Enter"):
                    if user_name and password and confirm_password:
                        user_name = user_name.strip()
                        full_name = full_name.strip() if full_name is not None else None
                        password = password.strip()

                        if password != confirm_password.strip():
                            error = passwords_do_not_match_text
                        elif len(user_name) and len(password):
                            try:
                                user_service.register_user(
                                    User(user_name, True, False, roles, full_name, False, default_active_status, False),
                                    password,
                                    None if registration_default_user_details_supplier is None else registration_default_user_details_supplier() 
                                )
                                ui.delete_cookie(registration_key)
                                ui.restart_browser_window()
        
                            except Exception as e:
                                error = exception_text_mapper(e)
        
        if error:
            st.error(error)

    dialog()

def set_password_form(
        user_service: UserService,
        session_id_key: str,
        title: str,
        password_label: str,
        new_password_label: str,
        confirm_new_password_label: str,
        set_button_label: str,
        exception_text_mapper: Callable[[Exception], str],
        passwords_do_not_match_text: str
    ):
    """
    Displays set password dialog for a user from the current session.
    After setting up is successfull, user will be automatically relogged with a new password, all session (including initial one) will be deleted. 
    """

    @st.dialog(title, width="small", dismissible=False)
    def dialog():
        session_id = ui.read_cookie(session_id_key)
        password = st.text_input(password_label, type="password")
        new_password = st.text_input(new_password_label, type="password")
        confirm_new_password = st.text_input(confirm_new_password_label, type="password")

        error = None

        with st.container(width="stretch", horizontal=True, horizontal_alignment="right"):
                if st.button(set_button_label, type="primary", shortcut="Enter"):
                    if password and new_password and confirm_new_password:
                        password = password.strip()
                        new_password = new_password.strip()

                        if new_password != confirm_new_password.strip():
                            error = passwords_do_not_match_text
                        elif len(password) and len(new_password):
                            try:
                                new_session_id = user_service.set_password(session_id, password, new_password, ui.get_browser_locate(), ui.get_browser_timezone(), ui.get_browser_user_agent(), ui.get_ip_address())
                                ui.write_cookie(session_id_key, new_session_id, user_service.session_lifespan_seconds)
                                ui.restart_browser_window()
                            except (InvalidUserSessionException, UserLockedException, UserNotActiveException, UserNotFoundException):
                                ui.delete_cookie(session_id_key)
                                ui.restart_browser_window()
                            except Exception as e:
                                error = exception_text_mapper(e)
                                raise e
        
        if error:
            st.error(error)

    dialog()

def create_user_form(
    user_service: UserService,
    registration_default_user_details_supplier: Callable[[], dict[str, Any]] | None,
    context: dict[str, Any],
    title: str,
    user_name_label: str,
    full_name_label: str | None,
    password_label: str,
    confirm_password_label: str,
    roles_label: str,
    is_ui_user_label: str,
    is_service_user_label: str,
    is_active_label: str,
    is_locked_label: str,
    is_password_set_required_label: str,
    details_label: str,
    create_button_label: str,
    exception_text_mapper: Callable[[Exception], str],
    passwords_do_not_match_text: str,
    key_suffix: str | None
):
    """
    Displays a form to create a user.
    Reruns Streamlit script if registration is successful.
    """

    details = None if registration_default_user_details_supplier is None else registration_default_user_details_supplier()
    details = Node.create(details) if details else None

    @st.dialog(title, width="small", dismissible=True)
    def dialog():
        key = f"{key_suffix}_create_user_form" if key_suffix else "create_user_form"
        user_name = st.text_input(user_name_label, key=f"{key}_user_name")
        name = st.text_input(full_name_label, key=f"{key}_name") if full_name_label is not None else None

        with st.container(
            width="stretch",
            horizontal=True,
            horizontal_alignment="left",
            vertical_alignment="center"
        ):
            is_ui_user = st.toggle(is_ui_user_label, True, key=f"{key}_is_ui_user")
            is_service_user = st.toggle(is_service_user_label, key=f"{key}_is_service_user")
        
        password = st.text_input(password_label, type="password", key=f"{key}_password")
        confirm_password = st.text_input(confirm_password_label, type="password", key=f"{key}_confirm_password")
        roles = st.multiselect(roles_label, user_service.fetch_roles(), key=f"{key}_roles")
        is_active = st.toggle(is_active_label, True, key=f"{key}_is_active")
        is_locked = st.toggle(is_locked_label, key=f"{key}_is_locked")
        is_password_set_required = st.toggle(is_password_set_required_label, True, key=f"{key}_password_set_required")

        if details:
            st.write(f"**{details_label}**")
            data_editor(details, key, context, True, is_one_based_array_index=True)

        error = None

        with st.container(
            width="stretch",
            horizontal=True,
            horizontal_alignment="right",
            vertical_alignment="center",
        ):
            if st.button(create_button_label, type="primary", key=f"{key}_create", shortcut="Enter"):
                if user_name and password and confirm_password:
                    user_name = user_name.strip()
                    name = name.strip() if name is not None else None
                    password = password.strip()

                    if password != confirm_password.strip():
                        error = passwords_do_not_match_text
                    elif len(user_name) and len(password):
                        try:
                            user_service.register_user(
                                User(
                                    user_name,
                                    is_ui_user,
                                    is_service_user,
                                    roles,
                                    name,
                                    is_locked,
                                    is_active,
                                    is_password_set_required,
                                ),
                                password,
                                details.data() if details else None
                            )
                            st.session_state.clear()
                            st.rerun()

                        except Exception as e:
                            error = exception_text_mapper(e)

        if error:
            st.error(error)

    dialog()

def __fetch_user(user_name: str, user_service: UserService) -> User | None:
    try:
        return user_service.fetch_user(user_name)
    except UserLayerException as e:
        ui.console_error(f"{e}")
        st.rerun()

def __fetch_user_details(user_name: str, user_service: UserService) -> dict[str, Any]:
    try:
        return user_service.fetch_user_details(user_name)
    except UserLayerException as e:
        ui.console_error(f"{e}")
        st.rerun()

def edit_user_form(
    user_name: str,
    user_service: UserService,
    context: dict[str, Any],
    title: str,
    full_name_label: str | None,
    password_label: str,
    confirm_password_label: str,
    roles_label: str,
    is_ui_user_label: str,
    is_service_user_label: str,
    is_active_label: str,
    is_locked_label: str,
    is_password_set_required_label: str,
    details_label: str,
    save_button_label: str,
    exception_text_mapper: Callable[[Exception], str],
    passwords_do_not_match_text: str,
    key_suffix: str | None
):
    """
    Displays a form to edit a user.
    Reruns Streamlit script if update is successful.
    """

    user = __fetch_user(user_name, user_service)
    details = __fetch_user_details(user_name, user_service)
    details_node = Node.create(details) if details else None
    key = f"{key_suffix}_edit_user_form" if key_suffix else "edit_user_form"

    @st.dialog(title, width="small", dismissible=True)
    def dialog():
        st.text_input(user_name, user_name, label_visibility="hidden", disabled=True, key=f"{key}_user_name")
        name = (st.text_input(full_name_label, user.name, key=f"{key}_name") if full_name_label is not None else None)

        with st.container(
            width="stretch",
            horizontal=True,
            horizontal_alignment="left",
            vertical_alignment="center"
        ):
            is_ui_user = st.toggle(is_ui_user_label, user.is_ui_user, key=f"{key}_is_ui_user")
            is_service_user = st.toggle(is_service_user_label, user.is_service_user, key=f"{key}_is_service_user")

        password = st.text_input(password_label, type="password", key=f"{key}_password")
        confirm_password = st.text_input(confirm_password_label, type="password", key=f"{key}_confirm_password")
        roles = st.multiselect(roles_label, user_service.fetch_roles(), user.roles, key=f"{key}_roles")
        is_active = st.toggle(is_active_label, user.active, key=f"{key}_is_active")
        is_locked = st.toggle(is_locked_label, user.locked, key=f"{key}_is_locked")
        is_password_set_required = st.toggle(is_password_set_required_label, user.requires_password_update, key=f"{key}_password_set_required")

        if details_node:
            st.write(f"**{details_label}**")
            data_editor(details_node, key, context, True, is_one_based_array_index=True)

        error = None

        with st.container(
            width="stretch",
            horizontal=True,
            horizontal_alignment="right",
            vertical_alignment="center"
        ):
            if st.button(save_button_label, type="primary", key=f"{key}_save", shortcut="Enter"):
                do_pass = True

                if password and password.strip():
                    if password != confirm_password.strip():
                        do_pass = False
                        error = passwords_do_not_match_text

                else:
                    password = None

                if do_pass:
                    try:
                        user_service.update_user(
                            User(
                                user_name,
                                is_ui_user,
                                is_service_user,
                                roles,
                                name,
                                is_locked,
                                is_active,
                                is_password_set_required,
                            ),
                            password,
                            details_node.data() if details_node else details
                        )

                        st.session_state.clear()
                        st.rerun()

                    except Exception as e:
                        error = exception_text_mapper(e)

        if error:
            st.error(error)

    dialog()