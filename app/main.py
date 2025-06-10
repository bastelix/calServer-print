"""NiceGUI based label printing application with login and device table."""

from __future__ import annotations

import base64
import io
import json
import os
import inspect
from typing import Any, Dict, List

from PIL import Image
from nicegui import ui

try:
    from .calserver_api import fetch_calibration_data
    from .label_templates import device_label
    from .print_utils import print_label
except ImportError:  # pragma: no cover - running as script
    from calserver_api import fetch_calibration_data
    from label_templates import device_label
    from print_utils import print_label


def _pil_to_data_url(image: Image.Image) -> str:
    """Return a data URL for the given PIL image."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{data}"


def main() -> None:
    """Run the NiceGUI label tool."""

    stored_login: Dict[str, str] = {}
    table_rows: List[Dict[str, Any]] = []
    selected_row: Dict[str, Any] | None = None
    current_image: Image.Image | None = None

    status_log: ui.log | None = None
    label_img: ui.image | None = None
    print_button: ui.button | None = None
    label_card: ui.card | None = None
    device_table: ui.table | None = None
    main_layout: ui.column | None = None
    login_card: ui.card | None = None

    def push_status(msg: str) -> None:
        if status_log:
            status_log.push(msg)
        ui.notify(msg)

    def handle_login() -> None:
        nonlocal login_card, main_layout
        try:
            push_status("Checking login...")
            fetch_calibration_data(
                base_url.value,
                username.value,
                password.value,
                api_key.value,
                {},
            )
            stored_login.update(
                {
                    "base_url": base_url.value,
                    "username": username.value,
                    "password": password.value,
                    "api_key": api_key.value,
                }
            )
            login_card.visible = False
            show_main_ui()
            push_status("Login successful")
        except Exception as e:  # pragma: no cover - UI only
            push_status(f"Login failed: {e}")

    def logout() -> None:
        nonlocal selected_row, current_image
        push_status("Logged out")
        stored_login.clear()
        selected_row = None
        current_image = None
        if main_layout:
            main_layout.clear()
        login_card.visible = True

    def fetch_data() -> None:
        nonlocal selected_row
        try:
            push_status("Fetching data...")
            data = fetch_calibration_data(
                stored_login.get("base_url", base_url.value),
                stored_login.get("username", username.value),
                stored_login.get("password", password.value),
                stored_login.get("api_key", api_key.value),
                {},
            )
            if isinstance(data, dict) and isinstance(data.get("data"), dict):
                cal_list = data["data"].get("calibration", [])
            elif isinstance(data, list):
                cal_list = data
            else:
                cal_list = [data] if data else []
            rows = []
            for entry in cal_list:
                inv = entry.get("inventory") or {}
                rows.append(
                    {
                        "I4201": inv.get("I4201") or "-",
                        "I4202": inv.get("I4202") or "-",
                        "I4203": inv.get("I4203") or "-",
                        "I4204": inv.get("I4204") or "-",
                        "I4206": inv.get("I4206") or "-",
                        "C2301": entry.get("C2301") or "-",
                        "C2303": entry.get("C2303") or "-",
                    }
                )
            table_rows.clear()
            table_rows.extend(rows)
            selected_row = None
            if device_table:
                device_table.update()
            push_status("Data loaded")
        except Exception as e:  # pragma: no cover - UI only
            push_status(f"Error fetching data: {e}")
            table_rows.clear()
            if device_table:
                device_table.update()

    def update_label(row: Dict[str, Any] | None) -> None:
        nonlocal current_image
        if not row:
            if label_card:
                label_card.visible = False
            if print_button:
                print_button.disable()
            return
        img = device_label(row.get("I4201", ""), row.get("I4206", ""))
        current_image = img
        if label_img:
            label_img.set_source(_pil_to_data_url(img))
        if label_card:
            label_card.visible = True
        if print_button:
            print_button.enable()

    def on_select(e) -> None:
        nonlocal selected_row
        selected_row = e.args
        update_label(selected_row)

    def do_print() -> None:
        if not current_image:
            return
        try:
            print_label(current_image, "")
            push_status("Printed")
        except Exception as e:  # pragma: no cover - UI only
            push_status(f"Print error: {e}")

    def show_main_ui() -> None:
        nonlocal status_log, label_img, print_button, label_card, device_table, main_layout
        main_layout = ui.column()
        with main_layout:
            ui.button("Logout", on_click=logout).classes("absolute-top-right q-mt-sm q-mr-sm").props("icon=logout flat color=negative")
            with ui.row().classes("justify-center q-gutter-xl flex-wrap"):
                with ui.column().style("flex:3;min-width:600px;max-width:900px"):
                    table_kwargs = dict(
                        columns=[
                            {"name": "I4201", "label": "Gerätename", "field": "I4201"},
                            {"name": "I4202", "label": "Hersteller", "field": "I4202"},
                            {"name": "I4203", "label": "Typ", "field": "I4203"},
                            {"name": "I4204", "label": "Beschreibung", "field": "I4204"},
                            {"name": "I4206", "label": "Seriennummer", "field": "I4206"},
                            {"name": "C2301", "label": "Kalibrierdatum", "field": "C2301"},
                            {"name": "C2303", "label": "Ablaufdatum", "field": "C2303"},
                        ],
                        rows=table_rows,
                        row_key="I4201",
                        pagination=True,
                        on_select=on_select,
                    )
                    if "search" in inspect.signature(ui.table).parameters:
                        table_kwargs["search"] = True
                    if "rows_per_page" in inspect.signature(ui.table).parameters:
                        table_kwargs["rows_per_page"] = 10
                    device_table = ui.table(**table_kwargs).classes("q-mt-md")
                    ui.button("Daten laden", on_click=fetch_data).props("color=primary").classes("q-mt-md")
                with ui.column().style("flex:2;min-width:320px"):
                    label_card = ui.card().style("margin-left:32px;padding:32px;")
                    label_card.visible = False
                    with label_card:
                        ui.label("Label-Vorschau").classes("text-h6")
                        label_img = ui.image("").classes("q-mb-md").style("max-width:260px;")
                        print_button = ui.button("Drucken", on_click=do_print).props("color=primary")
                        print_button.disable()
            with ui.footer().classes("bg-grey-2 shadow-2"):
                expansion = ui.expansion("Status anzeigen", value=False)
                with expansion:
                    status_log = ui.log(max_lines=100)

    # ----- Login card -----
    login_card = ui.card().style("max-width:420px;margin:80px auto;")
    with login_card:
        ui.label("calServer Labeltool").classes("text-h5 text-center q-mb-md")

        # Prefill login fields in development mode. The DOMAIN environment
        # variable determines the default URL. If APP_ENV is set to
        # ``development`` additional credentials are populated as well.
        is_dev = os.getenv("APP_ENV") == "development"
        if is_dev:
            domain = os.getenv("DOMAIN", "demo.net-cal.com")
        else:
            domain = os.getenv("DOMAIN", "calserver.example.com")
        default_url = domain if domain.startswith("http") else f"https://{domain}"
        base_url = ui.input("API URL", value=default_url).props("outlined")
        username = ui.input(
            "Benutzername",
            value="api-demo@calhelp.de" if is_dev else "",
        ).props("outlined")
        password = ui.input("Passwort", password=True).props("outlined")
        api_key = ui.input(
            "API Key",
            password=True,
            value="53f1871505fa8190659aaae17845bd19" if is_dev else "",
        ).props("outlined")
        ui.button("Login", on_click=handle_login).props("color=primary")

    ui.run(port=8080, show=False)


if __name__ == "__main__":  # pragma: no cover - manual start
    main()
