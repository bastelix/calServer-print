"""NiceGUI based user interface for printing calibration labels."""

import json
import io
import base64
from PIL import Image
from nicegui import ui

# dictionary to keep login information during runtime
stored_login: dict[str, str] = {}

try:
    from .calserver_api import fetch_calibration_data
    from .label_templates import device_label, calibration_label
    from .print_utils import list_printers, print_label
except ImportError:  # pragma: no cover - allow running as script
    from calserver_api import fetch_calibration_data
    from label_templates import device_label, calibration_label
    from print_utils import list_printers, print_label


def _pil_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{data}"


def main() -> None:
    """Run the interactive NiceGUI application."""

    cal_data = {}
    current_image: Image.Image | None = None

    base_url = ui.input(
        "API Base URL",
        value=stored_login.get("base_url", "https://calserver.example.com"),
    )
    username = ui.input("Username", value=stored_login.get("username", ""))
    password = ui.input(
        "Password", password=True, value=stored_login.get("password", "")
    )
    api_key = ui.input("API Key", password=True, value=stored_login.get("api_key", ""))
    filter_json = ui.textarea(
        "Filter JSON", value=stored_login.get("filter_json", "{}")
    )

    for ctrl in (base_url, username, password, api_key, filter_json):
        if hasattr(ctrl, "classes"):
            ctrl.classes("w-96")
        else:  # pragma: no cover - compatibility fallback
            ctrl.style("width: 24rem")

    label_type = ui.radio(["Device", "Calibration"], value="Device")

    label_img = ui.image("")
    # Older NiceGUI versions do not support the ``classes`` argument on
    # ``ui.image``.  We therefore add the tailwind class after creation if the
    # helper is available.
    if hasattr(label_img, "classes"):
        label_img.classes("w-96")
    else:  # pragma: no cover - compatibility fallback
        label_img.style("width: 24rem")
    printer_select = ui.select(options=list_printers())

    # log window for detailed application messages
    log_window = ui.log(max_lines=100)

    def fetch() -> None:
        nonlocal cal_data, current_image
        try:
            log_window.push("Fetching data...")
            stored_login.update({
                "base_url": base_url.value,
                "username": username.value,
                "password": password.value,
                "api_key": api_key.value,
                "filter_json": filter_json.value,
            })
            data = fetch_calibration_data(
                base_url.value,
                username.value,
                password.value,
                api_key.value,
                json.loads(filter_json.value or "{}"),
            )
            cal_data = data
            ui.notify("Data loaded", type="positive")
            log_window.push("Data loaded successfully")
            update_label()
        except Exception as e:  # pragma: no cover - UI only
            log_window.push(f"Error: {e}")
            ui.notify(str(e), type="negative")

    def update_label() -> None:
        nonlocal current_image
        if not cal_data:
            return
        log_window.push(f"Render label: {label_type.value}")
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
            log_window.push(f"Printing on {printer_select.value}")
            print_label(current_image, printer_select.value)
            ui.notify("Printed", type="positive")
        except Exception as e:  # pragma: no cover - UI only
            log_window.push(f"Print error: {e}")
            ui.notify(str(e), type="negative")

    ui.button("Fetch Data", on_click=fetch)
    ui.button("Print", on_click=do_print)

    ui.run(port=8080, show=False)


if __name__ == "__main__":  # pragma: no cover - manual start
    main()
