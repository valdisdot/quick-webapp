from collections.abc import Callable, Iterable
import streamlit as st
import quick_webapp.ui as ui
from quick_webapp.security.basic.user import User
from quick_webapp.security.basic.user_service import UserService, InvalidUserSessionException, UserLockedException, UserNotActiveException, UserNotFoundException, UserLayerException

def login_form(
        user_service: UserService,
        session_id_key: str,
        registration_key: str | None = None,
        title: str = "Login",
        user_name_label: str = "Username",
        password_label: str = "Password",
        login_button_label: str = "Login",
        registration_button_label: str = "Registration",
        help_text: str | None = None,
        help_badge: str = "🛟",
        exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception)
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
                                session_id = user_service.login(user_name, password, ui.get_browser_locate(), ui.get_browser_timezone())
        
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
        registration_key: str,
        title: str = "Registration",
        user_name_label: str = "Username",
        full_name_label: str | None = "Full name",
        password_label: str = "Password",
        confirm_password_label: str = "Confirm password",
        register_button_label: str = "Register",
        login_button_label: str = "Login",
        help_badge: str = "🛟",
        help_text: str | None = None,
        exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception),
        passwords_do_not_match_text: str = "Passwords do not match!"
    ):
    """
    Displays registration dialog. User only provide username, full name and password, role and active status must be specified withing parameters of this method.
    The method only registers a user, then the user must login.
    If user clicked on login button or got successfully registered, browser cache will remove a cookie with 'registration_key' key from this method params, and then the gets refreshed.
    """

    @st.dialog(title, width="small", dismissible=False)
    def dialog():
        roles = [] if not default_roles else ([str(default_role) for default_role in default_roles] if isinstance(default_roles, Iterable) else [str(default_roles)])
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
                                    password
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
        title: str = "Set a password",
        password_label: str = "Password",
        new_password_label: str = "New password",
        confirm_new_password_label: str = "Confirm new password",
        set_button_label: str = "Set",
        exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception),
        passwords_do_not_match_text: str = "Passwords do not match!"
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
                                new_session_id = user_service.set_password(session_id, password, new_password, ui.get_browser_locate(), ui.get_browser_timezone())
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

def __fetch_user(user_name: str, user_service: UserService) -> User | None:
    try:
        return user_service.fetch_user(user_name)
    except UserLayerException as e:
        ui.console_error(f"{e}")
        st.rerun()

def create_user_form(
    user_service: UserService,
    title: str = "Create a user",
    user_name_label: str = "Username",
    full_name_label: str | None = "Full name",
    password_label: str = "Password",
    confirm_password_label: str = "Confirm password",
    roles_label: str = "Roles",
    is_ui_user_label: str = "UI user",
    is_service_user_label: str = "Service user",
    is_active_label: str = "Active",
    is_locked_label: str = "Locked",
    is_password_set_required_label: str = "Require password set",
    create_button_label: str = "Create",
    exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception),
    passwords_do_not_match_text: str = "Passwords do not match!",
    key_suffix: str | None = None
):
    """
    Displays a form to create a user.
    Reruns Streamlit script if registration is successful.
    """

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
                                password
                            )
                            st.session_state.clear()
                            st.rerun()

                        except Exception as e:
                            error = exception_text_mapper(e)

        if error:
            st.error(error)

    dialog()

def edit_user_form(
    user_name: str,
    user_service: UserService,
    title: str = "Edit a user",
    full_name_label: str | None = "Full name",
    password_label: str = "Password",
    confirm_password_label: str = "Confirm password",
    roles_label: str = "Roles",
    is_ui_user_label: str = "UI user",
    is_service_user_label: str = "Service user",
    is_active_label: str = "Active",
    is_locked_label: str = "Locked",
    is_password_set_required_label: str = "Require password set",
    save_button_label: str = "Save",
    exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception),
    passwords_do_not_match_text: str = "Passwords do not match!",
    key_suffix: str | None = None
):
    """
    Displays a form to edit a user.
    Reruns Streamlit script if update is successful.
    """

    @st.dialog(title, width="small", dismissible=True)
    def dialog(user: User):
        key = f"{key_suffix}_edit_user_form" if key_suffix else "edit_user_form"

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
                            password
                        )

                        st.session_state.clear()
                        st.rerun()

                    except Exception as e:
                        error = exception_text_mapper(e)

        if error:
            st.error(error)

    dialog(__fetch_user(user_name, user_service))