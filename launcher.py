import streamlit.web.bootstrap
import os
import sys

script_path = os.path.join(os.path.dirname(__file__), "app", "main.py")

streamlit.web.bootstrap.run(
    script_path,
    [],
    {"flag_options": ["--server.headless=true"]}
)
