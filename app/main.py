"""NiceGUI based user interface for printing calibration labels."""

import json
import io
import base64
from PIL import Image
from nicegui import ui

from .calserver_api import fetch_calibration_data
from .label_templates import device_label, calibration_label
from .print_utils import list_printers, print_label


def _pil_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{data}"


def main() -> None:
    """Run the interactive NiceGUI application."""

    cal_data = {}
    current_image: Image.Image | None = None

    base_url = ui.input("API Base URL", value="https://calserver.example.com")
    username = ui.input("Username")
    password = ui.input("Password", password=True)
    api_key = ui.input("API Key", password=True)
    filter_json = ui.textarea("Filter JSON", value="{}")

    label_type = ui.radio(["Device", "Calibration"], value="Device")

    label_img = ui.image("", classes="w-96")
    printer_select = ui.select(options=list_printers())

    def fetch() -> None:
        nonlocal cal_data, current_image
        try:
            data = fetch_calibration_data(
                base_url.value,
                username.value,
                password.value,
                api_key.value,
                json.loads(filter_json.value or "{}"),
            )
            cal_data = data
            ui.notify("Data loaded", type="positive")
            update_label()
        except Exception as e:  # pragma: no cover - UI only
            ui.notify(str(e), type="negative")

    def update_label() -> None:
        nonlocal current_image
        if not cal_data:
            return
        if label_type.value == "Device":
            name = cal_data.get("device_name", "Device")
            device_id = str(cal_data.get("device_id", ""))
            img = device_label(name, device_id)
        else:
            date = cal_data.get("date", "")
            status = cal_data.get("status", "")
            cert = cal_data.get("certificate", "")
            img = calibration_label(date, status, cert, str(cal_data))
        current_image = img
        label_img.set_source(_pil_to_data_url(img))

    def do_print() -> None:
        if not current_image:
            return
        try:
            print_label(current_image, printer_select.value)
            ui.notify("Printed", type="positive")
        except Exception as e:  # pragma: no cover - UI only
            ui.notify(str(e), type="negative")

    ui.button("Fetch Data", on_click=fetch)
    ui.button("Print", on_click=do_print)

    ui.run()


if __name__ == "__main__":  # pragma: no cover - manual start
    main()
