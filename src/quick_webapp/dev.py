import logging
import time
import json
from functools import wraps
import streamlit as st

def deprecated(note: str = "deprecated call..."):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logging.warning(f"{func.__name__}: {note}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def note(note: str = "a warning note!"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logging.warning(f"{func.__name__}: {note}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def mark_ui(text: str | None = None):
    st.error(f"🔴 {text}" if text else "🔴")

def mock_json(name: str, trottle_s: float = 0):
    delay = time.time_ns()
    with open(f"examples/{name}.json", encoding="utf-8") as json_file:
        json_obj = json.load(json_file)
    delay = trottle_s - (delay - time.time_ns())/1000000000
    if (delay > 0): 
        time.sleep(delay)
    return json_obj