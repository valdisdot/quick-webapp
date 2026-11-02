from typing import Any
import streamlit as st
from quick_webapp import session_bean
from quick_webapp.webapp import menu_page
from context import webapp

@session_bean(key="simple_page_page_context_dict")
def __context() -> dict[str, any]:
    return {}

menu_page("1_UIs", "1_Simple page")

with webapp().as_context(
    page_title="A simple page", 
    page_title_render=lambda t: st.subheader(t),
    java_scripts=["console.log('print to browser!');"]
):
    page_session_obj = __context()
    
    text_input = st.text_area("Type the text:")

    if text_input and len(text_input):
        page_session_obj["last_text"] = text_input

    text_input = page_session_obj.get("last_text")
    if text_input:
        st.write("**You typed:**")
        st.write(text_input)