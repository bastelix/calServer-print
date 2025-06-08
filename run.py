import streamlit.web.bootstrap

STREAMLIT_ARGS = {
    "flag_options": ["--server.headless=true"],
    "script_path": "app/main.py",
}

streamlit.web.bootstrap.run(
    STREAMLIT_ARGS["script_path"],
    flag_options=STREAMLIT_ARGS["flag_options"],
)
