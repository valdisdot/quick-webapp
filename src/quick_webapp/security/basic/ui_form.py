from collections.abc import Callable
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

        with st.container(width="stretch", horizontal=True):
            with st.container(width="stretch", horizontal=True, horizontal_alignment="left", vertical_alignment="center"):
                if help_text and len(help_text):
                    st.badge(label=help_badge, help=help_text)

                if registration_key and len(registration_key):
                    if st.button(registration_button_label, type="secondary"):
                        ui.write_cookie(registration_key, 1, user_service.session_lifespan_seconds)
                        ui.restart_browser_window()
                else:
                    st.write("")

            with st.container(width="content", horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
                if st.button(login_button_label, type="primary"):
                    if user_name and password:
                        user_name = user_name.strip()
                        password = password.strip()

                        if len(user_name) and len(password):
                            try:
                                session_id = user_service.login(user_name, password, ui.get_browser_locate(), ui.get_browser_timezone())
                                ui.write_cookie(session_id_key, session_id, user_service.session_lifespan_seconds)
                                ui.delete_cookie(registration_key)
                                ui.restart_browser_window()
        
                            except Exception as e:
                                error = e
        
        if error:
            st.error(exception_text_mapper(error))

    dialog()

def registration_form(
        user_service: UserService,
        default_role: str,
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
        user_name = st.text_input(user_name_label)
        full_name = st.text_input(full_name_label) if full_name_label is not None else None
        password = st.text_input(password_label, type="password")
        confirm_password = st.text_input(confirm_password_label, type="password")

        error = None

        with st.container(width="stretch", horizontal=True):
            with st.container(width="stretch", horizontal=True, horizontal_alignment="left", vertical_alignment="center"):
                if help_text and len(help_text):
                    st.badge(label=help_badge, help=help_text)

                if st.button(login_button_label, type="secondary"):
                    ui.delete_cookie(registration_key)
                    ui.restart_browser_window()

            with st.container(width="content", horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
                if st.button(register_button_label, type="primary"):
                    if user_name and password and confirm_password:
                        user_name = user_name.strip()
                        full_name = full_name.strip() if full_name is not None else None
                        password = password.strip()

                        if password != confirm_password.strip():
                            error = passwords_do_not_match_text
                        elif len(user_name) and len(password):
                            try:
                                user_service.register_user(
                                    User(user_name, [default_role], full_name, False, default_active_status, False),
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
                if st.button(set_button_label, type="primary"):
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
    is_active_label: str = "Active",
    is_locked_label: str = "Locked",
    is_password_set_required_label: str = "Require password set",
    create_button_label: str = "Create",
    exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception),
    passwords_do_not_match_text: str = "Passwords do not match!",
):
    """
    Displays a form to create a user.
    Reruns Streamlit script if registration is successful.
    """

    @st.dialog(title, width="small", dismissible=True)
    def dialog():
        user_name = st.text_input(user_name_label)
        full_name = (
            st.text_input(full_name_label) if full_name_label is not None else None
        )
        password = st.text_input(password_label, type="password")
        confirm_password = st.text_input(confirm_password_label, type="password")
        roles = st.multiselect(roles_label, user_service.fetch_roles())
        is_active = st.toggle(is_active_label, True)
        is_locked = st.toggle(is_locked_label)
        is_password_set_required = st.toggle(is_password_set_required_label, True)

        error = None

        with st.container(
            width="stretch",
            horizontal=True,
            horizontal_alignment="right",
            vertical_alignment="center",
        ):
            if st.button(create_button_label, type="primary"):
                if user_name and password and confirm_password:
                    user_name = user_name.strip()
                    full_name = full_name.strip() if full_name is not None else None
                    password = password.strip()

                    if password != confirm_password.strip():
                        error = passwords_do_not_match_text
                    elif len(user_name) and len(password):
                        try:
                            user_service.register_user(
                                User(
                                    user_name,
                                    roles,
                                    full_name,
                                    is_locked,
                                    is_active,
                                    is_password_set_required,
                                ),
                                password,
                            )
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
    is_active_label: str = "Active",
    is_locked_label: str = "Locked",
    is_password_set_required_label: str = "Require password set",
    save_button_label: str = "Save",
    exception_text_mapper: Callable[[Exception], str] = lambda exception: str(exception),
    passwords_do_not_match_text: str = "Passwords do not match!",
):
    """
    Displays a form to edit a user.
    Reruns Streamlit script if update is successful.
    """

    @st.dialog(title, width="small", dismissible=True)
    def dialog(user: User):
        st.text_input(
            user_name, user_name, label_visibility="hidden", disabled=True
        )
        full_name = (
            st.text_input(full_name_label, user.name)
            if full_name_label is not None
            else None
        )
        password = st.text_input(password_label, type="password")
        confirm_password = st.text_input(confirm_password_label, type="password")
        roles = st.multiselect(roles_label, user_service.fetch_roles(), user.roles)
        is_active = st.toggle(is_active_label, user.active)
        is_locked = st.toggle(is_locked_label, user.locked)
        is_password_set_required = st.toggle(
            is_password_set_required_label, user.requires_password_update
        )

        error = None

        with st.container(
            width="stretch",
            horizontal=True,
            horizontal_alignment="right",
            vertical_alignment="center",
        ):
            if st.button(save_button_label, type="primary"):
                full_name = (
                    None
                    if (full_name is None or len(full_name.strip()) == 0)
                    else full_name
                )
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
                                roles,
                                full_name if full_name else user.name,
                                is_locked,
                                is_active,
                                is_password_set_required,
                            ),
                            password,
                        )
                        st.rerun()

                    except Exception as e:
                        error = exception_text_mapper(e)

        if error:
            st.error(error)

    dialog(__fetch_user(user_name, user_service))

def manage_user_form(
    user_name: str,
    user_service: UserService,
    title: str = "Manage a user",
    active_label: str = "Active",
    not_active_label: str = "Not active",
    sessions_label: str = "Sessions",
    lock_label: str = "Lock",
    unlock_label: str = "Unlock",
    logout_label: str = "Logout"
):
    """
    Displays a form to manage a user (lock and close sessions).
    Reruns Streamlit script if saving is successful.
    """

    @st.dialog(title, width="small", dismissible=True)
    def dialog(user: User):
        with st.container(horizontal=True):
            st.write(f"**{user.user_name}**")
            if user.name:
                st.write(f"({user.name})")
        
        st.badge(active_label if user.active else not_active_label, color="green" if user.active else "gray")
        st.write(f"{sessions_label}: {len(user_service.get_user_sessions(user_name))}")

        with st.container(horizontal=True):
            if st.button(unlock_label if user.locked else lock_label, type="secondary" if user.locked else "primary"):
                user_service.update_user_lock(user_name, not user.locked)
                user = __fetch_user(user_name, user_service)
            
            if st.button(logout_label, type="primary"):
                user_service.close_user_sessions(user.user_name)
                user = __fetch_user(user_name, user_service)

    dialog(__fetch_user(user_name, user_service))

