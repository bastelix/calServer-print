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
    from .label_templates import device_label, device_label_svg
    from .qrcode_utils import generate_qr_code
    from .print_utils import print_label
except ImportError:  # pragma: no cover - running as script
    from calserver_api import fetch_calibration_data
    from label_templates import device_label, device_label_svg
    from qrcode_utils import generate_qr_code
    from print_utils import print_label


def _pil_to_data_url(image: Image.Image) -> str:
    """Return a data URL for the given PIL image."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{data}"


def _build_table_kwargs(table_func, rows: List[Dict[str, Any]], on_select) -> Dict[str, Any]:
    """Return kwargs for ``ui.table`` with optional parameters."""

    kwargs = dict(
        columns=[
            {"name": "I4201", "label": "Gerätename", "field": "I4201"},
            {"name": "I4202", "label": "Hersteller", "field": "I4202"},
            {"name": "I4203", "label": "Typ", "field": "I4203"},
            {"name": "I4204", "label": "Beschreibung", "field": "I4204"},
            {"name": "I4206", "label": "Seriennummer", "field": "I4206"},
            {"name": "C2301", "label": "Kalibrierdatum", "field": "C2301"},
            {"name": "C2303", "label": "Ablaufdatum", "field": "C2303"},
            {
                "name": "qrcode",
                "label": "QR-Code",
                "field": "qrcode",
                "html": True,
            },
            {
                "name": "preview",
                "label": "Vorschau",
                "field": "preview",
                "html": True,
            },
        ],
        rows=rows,
        row_key="I4201",
        on_select=on_select,
    )

    params = inspect.signature(table_func).parameters
    if "pagination" in params:
        kwargs["pagination"] = {"rowsPerPage": 10}
    elif "rows_per_page" in params:
        kwargs["rows_per_page"] = 10
    elif any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        kwargs["rows_per_page"] = 10
    if "search" in params:
        kwargs["search"] = True
    if (
        "rows_per_page" not in params
        and "pagination" not in params
        and not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    ):
        kwargs.pop("rows_per_page", None)
    if "selection" in params:
        kwargs["selection"] = "single"
    if "html_columns" in params:
        kwargs["html_columns"] = ["qrcode", "preview"]
    elif any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        kwargs["html_columns"] = ["qrcode", "preview"]
    return kwargs


def _navigate(path: str) -> None:
    """Open the given path using the available NiceGUI API."""
    if hasattr(ui, "open"):
        ui.open(path)  # type: ignore[attr-defined]
    elif hasattr(ui, "open_page"):
        ui.open_page(path)  # pragma: no cover - legacy NiceGUI
    elif hasattr(ui, "navigate") and hasattr(ui.navigate, "to"):
        ui.navigate.to(path)  # pragma: no cover - future NiceGUI
    elif hasattr(ui, "navigate"):
        ui.navigate(path)  # pragma: no cover - future NiceGUI
    else:  # pragma: no cover - missing method
        raise AttributeError("No navigation method found in nicegui.ui")


def main() -> None:
    """Run the NiceGUI label tool."""

    stored_login: Dict[str, str] = {}
    table_rows: List[Dict[str, Any]] = []
    all_rows: List[Dict[str, Any]] = []
    selected_row: Dict[str, Any] | None = None
    current_image: Image.Image | None = None

    status_log: ui.log | None = None
    label_svg: ui.html | None = None
    print_button: ui.button | None = None
    label_card: ui.card | None = None
    placeholder_label: ui.label | None = None
    row_info_label: ui.label | None = None
    device_table: ui.table | None = None
    empty_table_label: ui.label | None = None
    main_layout: ui.column | None = None
    filter_slider: ui.slider | None = None
    filter_value: int = 1

    # login form elements (initialized on the login page)
    base_url: ui.input | None = None
    username: ui.input | None = None
    password: ui.input | None = None
    api_key: ui.input | None = None

    def push_status(msg: str) -> None:
        nonlocal status_log
        if status_log:
            try:
                status_log.push(msg)
            except Exception:
                status_log = None
        ui.notify(msg)

    def handle_login() -> None:
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
            _navigate("/app")
            push_status("Login successful")
        except Exception as e:  # pragma: no cover - UI only
            push_status(f"Login failed: {e}")

    def logout() -> None:
        nonlocal selected_row, current_image
        nonlocal status_log, label_svg, print_button, label_card, device_table
        nonlocal placeholder_label, empty_table_label, main_layout, filter_slider, row_info_label
        push_status("Logged out")
        stored_login.clear()
        selected_row = None
        current_image = None
        status_log = None
        label_svg = None
        print_button = None
        label_card = None
        device_table = None
        placeholder_label = None
        row_info_label = None
        empty_table_label = None
        main_layout = None
        filter_slider = None
        _navigate("/")

    def apply_table_filter() -> None:
        table_rows.clear()
        if filter_value == 2:
            table_rows.extend(all_rows)
        else:
            table_rows.extend([r for r in all_rows if r.get("C2339") == filter_value])
        if device_table:
            device_table.update()
        if empty_table_label:
            empty_table_label.visible = len(table_rows) == 0

    def fetch_data() -> None:
        nonlocal selected_row, all_rows
        try:
            push_status("Fetching data...")
            if filter_value == 2:
                filter_payload = {}
            else:
                filter_payload = [
                    {"property": "C2339", "value": filter_value, "operator": "="}
                ]
            data = fetch_calibration_data(
                stored_login.get("base_url", base_url.value),
                stored_login.get("username", username.value),
                stored_login.get("password", password.value),
                stored_login.get("api_key", api_key.value),
                filter_payload,
            )
            if isinstance(data, dict) and isinstance(data.get("data"), dict):
                cal_list = data["data"].get("calibration", [])
            elif isinstance(data, list):
                cal_list = data
            else:
                cal_list = [data] if data else []
            all_rows = []
            for entry in cal_list:
                inv = entry.get("inventory") or {}
                mtag_value = (
                    entry.get("MTAG")
                    or entry.get("mtag")
                    or inv.get("MTAG")
                    or inv.get("mtag")
                    or "-"
                )
                qr_img = generate_qr_code(mtag_value, size=60)
                qr_data = _pil_to_data_url(qr_img)
                all_rows.append(
                    {
                        "I4201": inv.get("I4201") or "-",
                        "I4202": inv.get("I4202") or "-",
                        "I4203": inv.get("I4203") or "-",
                        "I4204": inv.get("I4204") or "-",
                        "I4206": inv.get("I4206") or "-",
                        "C2301": entry.get("C2301") or "-",
                        "C2303": entry.get("C2303") or "-",
                        "MTAG": mtag_value,
                        "C2339": entry.get("C2339"),
                        "qrcode": f"<img src='{qr_data}' width='60' height='60'>",
                        "preview": f"<a href='{qr_data}' target='_blank'>Vorschau</a>",
                    }
                )
            apply_table_filter()
            selected_row = None
            push_status("Data loaded")
        except Exception as e:  # pragma: no cover - UI only
            push_status(f"Error fetching data: {e}")
            table_rows.clear()
            if device_table:
                device_table.update()
            if empty_table_label:
                empty_table_label.visible = True

    def update_label(row: Dict[str, Any] | None) -> None:
        nonlocal current_image, row_info_label
        if not row:
            current_image = None
            if label_svg:
                label_svg.content = device_label_svg("", "", "")
                label_svg.visible = True
            if placeholder_label:
                placeholder_label.visible = False
            if print_button:
                print_button.disable()
            if row_info_label:
                row_info_label.set_text("Keine Zeile ausgewählt")
            return

        name = row.get("I4201", "")
        expiry = row.get("C2303", "")
        mtag = row.get("MTAG", "")
        if not mtag or mtag == "-":
            push_status("MTAG fehlt für ausgewähltes Gerät")
        if row_info_label:
            row_info_label.set_text(f"I4201: {name}, C2303: {expiry}")
        img = device_label(name, expiry, mtag)
        current_image = img
        if label_svg:
            label_svg.content = device_label_svg(name, expiry, mtag)
            label_svg.visible = True
        if placeholder_label:
            placeholder_label.visible = False
        if print_button:
            print_button.enable()

    def _find_row(data) -> Dict[str, Any] | None:
        key = None
        if isinstance(data, dict):
            key = data.get("I4201")
        else:
            key = data
        return next((r for r in table_rows if r.get("I4201") == key), None)

    def on_select(e) -> None:
        nonlocal selected_row
        key = getattr(e, "selection", None)
        if key is None:
            key = getattr(e, "args", None)
            if isinstance(key, list):
                key = key[0] if key else None
        selected_row = _find_row(key)
        update_label(selected_row)

    def handle_row_click(e) -> None:
        """Update label preview when a table row is clicked."""
        nonlocal selected_row
        row = getattr(e, "args", None)
        if isinstance(row, list):
            row = row[0] if row else None
        selected_row = _find_row(row)
        update_label(selected_row)

    def on_slider_change(e) -> None:
        nonlocal filter_value
        try:
            filter_value = int(getattr(e, "value", e))
        except Exception:
            filter_value = 1
        apply_table_filter()

    def do_print() -> None:
        if not current_image:
            return
        try:
            print_label(current_image, "")
            push_status("Printed")
        except Exception as e:  # pragma: no cover - UI only
            push_status(f"Print error: {e}")

    def show_main_ui() -> None:
        nonlocal status_log, label_svg, print_button, label_card, device_table, main_layout, empty_table_label, placeholder_label, filter_slider, row_info_label
        main_layout = ui.column()
        with main_layout:
            ui.button("Logout", on_click=logout).classes("absolute-top-right q-mt-sm q-mr-sm").props("icon=logout flat color=negative")
            filter_slider = ui.slider(min=0, max=2, step=1, value=1, on_change=on_slider_change).props("label-always").classes("q-mt-md")
            ui.button("Daten laden", on_click=fetch_data).props("color=primary").classes("q-mt-md")
            # table and label preview side by side below controls
            with ui.row().classes("justify-center q-gutter-xl items-start"):
                with ui.column().style("flex:3;min-width:600px;max-width:900px"):
                    empty_table_label = ui.label("Noch keine Daten geladen").classes("text-grey text-center q-mt-md")
                    table_kwargs = _build_table_kwargs(ui.table, table_rows, on_select)
                    device_table = ui.table(**table_kwargs).classes("q-mt-md")
                    device_table.on("row-click", handle_row_click)
                    empty_table_label.visible = len(table_rows) == 0
                with ui.column().classes("col-auto").style("min-width:320px"):
                    label_card = ui.card().style("padding:32px;min-height:260px;")
                    with label_card:
                        ui.label("Label-Vorschau").classes("text-h6")
                        row_info_label = ui.label("Bitte Gerät auswählen").classes("q-mb-md")
                        placeholder_label = ui.label("Keine Vorschau verfügbar").classes("text-grey q-mb-md")
                        placeholder_label.visible = False
                        label_svg = ui.html(device_label_svg("", "", "")).classes("q-mb-md").style("max-width:260px;")
                        label_svg.visible = True
                        print_button = ui.button("Drucken", on_click=do_print).props("color=primary")
                        print_button.disable()
        footer = ui.footer().classes("bg-grey-2 shadow-2")
        with footer:
            expansion = ui.expansion("Status anzeigen", value=False)
            with expansion:
                status_log = ui.log(max_lines=100).style(
                    "background-color:white;color:black;width:100%;"
                )

    @ui.page("/")
    def login_page() -> None:
        nonlocal base_url, username, password, api_key
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

    @ui.page("/app")
    def main_page() -> None:
        show_main_ui()
        fetch_data()

    ui.run(port=8080, show=False)


if __name__ in {"__main__", "__mp_main__"}:  # pragma: no cover - manual start
    main()
