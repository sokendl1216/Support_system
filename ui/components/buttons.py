# ui/components/buttons.py

import streamlit as st

def primary_button(label: str, key=None):
    return st.button(label, key=key)

def icon_button(label: str, icon: str, key=None):
    return st.button(f":{icon}: {label}", key=key)
