"""Streamlit based user interface for printing calibration labels."""

import json
import streamlit as st
from PIL import Image

from .calserver_api import fetch_calibration_data
from .label_templates import device_label, calibration_label
from .print_utils import list_printers, print_label


def main():
    """Run the interactive Streamlit application."""

    st.title("calServer Labeltool")

    base_url = st.text_input("API Base URL", "https://calserver.example.com")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    api_key = st.text_input("API Key", type="password")
    filter_json = st.text_area("Filter JSON", "{}")

    label_type = st.radio("Label Type", ["Device", "Calibration"])

    if st.button("Fetch Data"):
        try:
            data = fetch_calibration_data(
                base_url,
                username,
                password,
                api_key,
                json.loads(filter_json or "{}"),
            )
            st.session_state["cal_data"] = data
            st.success("Data loaded")
        except Exception as e:
            st.error(str(e))

    data = st.session_state.get("cal_data")
    if data:
        if label_type == "Device":
            name = data.get("device_name", "Device")
            device_id = str(data.get("device_id", ""))
            img = device_label(name, device_id)
        else:
            date = data.get("date", "")
            status = data.get("status", "")
            cert = data.get("certificate", "")
            img = calibration_label(date, status, cert, str(data))
        st.image(img)

        printers = list_printers()
        printer = st.selectbox("Printer", printers)
        if st.button("Print"):
            try:
                print_label(img, printer)
                st.success("Printed")
            except Exception as e:
                st.error(str(e))


if __name__ == "__main__":
    main()
