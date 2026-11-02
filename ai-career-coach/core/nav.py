"""Registry of pages so any page can jump to another with a button (keeps the session, unlike a link)."""
import streamlit as st

PAGES: dict = {}


def go(name: str):
    st.switch_page(PAGES[name])
