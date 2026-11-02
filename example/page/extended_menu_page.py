import streamlit as st
from quick_webapp import bean
from quick_webapp.webapp import menu_page
from context import webapp, ui_package, login_page

@bean(key="go_to_simple_page_switch")
def __go_to_simple_page():
    return lambda: st.switch_page(ui_package() / "simple_page.py")

@bean(key="go_login_switch")
def __go_login():
    return lambda: st.switch_page(login_page())

menu_page("1_UIs", "2_Extended menu")
with webapp().as_context("This is an extended page title", {"To simple page": __go_to_simple_page(), "Go login": __go_login()}):
    st.write("Click on addition button in the menu: **To simple page**")
    st.write("Or click **Go login**")