from quick_webapp.webapp import streamlit_page
from context import user_menu_pages, user_service_pages

streamlit_page = streamlit_page(
    user_menu_pages(),
    user_service_pages(),
    "Welcome to example!"
)
streamlit_page.run()
 