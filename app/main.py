"""NiceGUI based label printing application with login and device table."""

from __future__ import annotations
import base64
import io
import os
import inspect
from typing import Any, Dict, List

from PIL import Image
from nicegui import ui

# Eigene Module importieren
try:
    from .calserver_api import fetch_calibration_data
    from .label_templates import device_label, device_label_svg
    from .qrcode_utils import generate_qr_code, generate_qr_code_svg
    from .print_utils import print_label
except ImportError:
    from calserver_api import fetch_calibration_data
    from label_templates import device_label, device_label_svg
    from qrcode_utils import generate_qr_code, generate_qr_code_svg
    from print_utils import print_label


def _pil_to_data_url(image: Image.Image) -> str:
    """Return a data URL for the given PIL image."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{data}"


def _build_table_kwargs(
    table_func: Any,
    rows: List[Dict[str, Any]],
    on_select: Any,
) -> Dict[str, Any]:
    """Return kwargs for `ui.table` with optional parameters."""
    kwargs: Dict[str, Any] = dict(
        columns=[
            {"name": "I4201", "label": "Gerätename", "field": "I4201"},
            {"name": "I4202", "label": "Hersteller", "field": "I4202"},
            {"name": "I4203", "label": "Typ", "field": "I4203"},
            {"name": "I4204", "label": "Beschreibung", "field": "I4204"},
            {"name": "I4206", "label": "Seriennummer", "field": "I4206"},
            {"name": "C2301", "label": "Kalibrierdatum", "field": "C2301"},
            {"name": "C2303", "label": "Ablaufdatum", "field": "C2303"},
            {"name": "MTAG",  "label": "MTAG",       "field": "MTAG"},
            {"name": "qrcode",  "label": "QR-Code",   "field": "qrcode"},
            {"name": "preview", "label": "Vorschau",  "field": "preview"},
        ],
        rows=rows,
        row_key="I4201",
        on_select=on_select,
    )
    params = inspect.signature(table_func).parameters
    # Pagination oder rows_per_page
    if "pagination" in params:
        kwargs["pagination"] = {"rowsPerPage": 10}
    elif "rows_per_page" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        kwargs["rows_per_page"] = 10
    # Suche aktivieren
    if "search" in params:
        kwargs["search"] = True
    # Einzel-Selektion
    if "selection" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        kwargs["selection"] = "single"
    return kwargs


def _navigate(path: str) -> None:
    """Open the given path using the available NiceGUI API."""
    if hasattr(ui, "open"):
        ui.open(path)  # type: ignore[attr-defined]
    elif hasattr(ui, "open_page"):
        ui.open_page(path)
    elif hasattr(ui, "navigate") and hasattr(ui.navigate, "to"):
        ui.navigate.to(path)
    elif hasattr(ui, "navigate"):
        ui.navigate(path)
    else:
        raise AttributeError("No navigation method found in nicegui.ui")


def main() -> None:
    """Run the NiceGUI label tool."""
    # States
    stored_login: Dict[str, str] = {}
    table_rows: List[Dict[str, Any]] = []
    all_rows: List[Dict[str, Any]] = []
    selected_row: Dict[str, Any] | None = None
    current_image: Image.Image | None = None

    # UI-Elemente
    status_log: ui.log | None = None
    label_svg: ui.html | None = None
    print_button: ui.button | None = None
    placeholder_label: ui.label | None = None
    row_info_label: ui.label | None = None
    device_table: ui.table | None = None
    empty_table_label: ui.label | None = None
    filter_switch: ui.switch | None = None
    search_input: ui.input | None = None
    label_dialog: ui.dialog | None = None
    dialog_label_svg: ui.html | None = None

    # Login-Felder
    base_url: ui.input | None = None
    username: ui.input | None = None
    password: ui.input | None = None
    api_key: ui.input | None = None

    # enable Tailwind CSS for the login dialog styling
    ui.add_head_html('<script src="https://cdn.tailwindcss.com"></script>')

    # Helper: Status-Log
    def push_status(msg: str) -> None:
        nonlocal status_log
        if status_log:
            try:
                status_log.push(msg)
            except Exception:
                status_log = None
        ui.notify(msg)

    # Login-Handler
    def handle_login() -> None:
        nonlocal stored_login
        try:
            push_status("Checking login...")
            fetch_calibration_data(
                base_url.value, username.value, password.value, api_key.value, {}
            )
            stored_login = {
                "base_url": base_url.value,
                "username": username.value,
                "password": password.value,
                "api_key": api_key.value,
            }
            _navigate("/app")
            push_status("Login successful")
        except Exception as e:
            push_status(f"Login failed: {e}")

    # Logout-Handler
    def logout() -> None:
        nonlocal selected_row, current_image, status_log, label_svg, print_button
        nonlocal device_table, placeholder_label, empty_table_label, row_info_label
        push_status("Logged out")
        stored_login.clear()
        selected_row = None
        current_image = None
        status_log = None
        label_svg = None
        print_button = None
        device_table = None
        placeholder_label = None
        empty_table_label = None
        row_info_label = None
        _navigate("/")

    # Filter-Logik
    def apply_table_filter() -> None:
        nonlocal table_rows
        table_rows.clear()
        filtered = all_rows
        if filter_switch.value is False:
            # Nur aktuelle
            filtered = [r for r in filtered if r.get("C2339") == 1]
        if search_value := search_input.value:
            sv = search_value.lower()
            filtered = [
                r for r in filtered
                if any(sv in str(r.get(f, "")).lower() for f in ["I4201","I4202","I4203","I4204","I4206","MTAG"])
            ]
        table_rows.extend(filtered)
        if device_table:
            device_table.update()
        if empty_table_label:
            empty_table_label.visible = len(table_rows) == 0

    # API-Daten laden
    def fetch_data() -> None:
        nonlocal all_rows, selected_row
        try:
            push_status("Fetching data...")
            payload = [] if filter_switch.value else [{"property":"C2339","value":1,"operator":"="}]
            data = fetch_calibration_data(
                stored_login["base_url"], stored_login["username"],
                stored_login["password"], stored_login["api_key"], payload
            )
            cal_list = (
                data.get("data", {}).get("calibration") if isinstance(data, dict) else data
            ) or []
            all_rows.clear()
            base = stored_login["base_url"].rstrip("/")
            for entry in cal_list:
                inv = entry.get("inventory") or {}
                mtag = entry.get("MTAG") or inv.get("MTAG") or "-"
                qr_url = f"{base}/qrcode/{mtag}"
                qr_img = generate_qr_code(qr_url, size=80)
                qr_svg = _pil_to_data_url(qr_img)
                all_rows.append({
                    "I4201": inv.get("I4201") or "-",
                    "I4202": inv.get("I4202") or "-",
                    "I4203": inv.get("I4203") or "-",
                    "I4204": inv.get("I4204") or "-",
                    "I4206": inv.get("I4206") or "-",
                    "C2301": entry.get("C2301") or "-",
                    "C2303": entry.get("C2303") or "-",
                    "MTAG":  mtag,
                    "qrcode": qr_svg,
                    "preview":"<span style='cursor:pointer;color:blue'>Vorschau</span>",
                })
            apply_table_filter()
            selected_row = None
            push_status("Data loaded")
        except Exception as e:
            push_status(f"Error fetching data: {e}")
            table_rows.clear()
            if device_table:
                device_table.update()
            if empty_table_label:
                empty_table_label.visible = True

    # Label aktualisieren
    def update_label(row: Dict[str, Any] | None) -> None:
        nonlocal current_image
        if not row:
            label_svg.content = device_label_svg("","","")
            placeholder_label.visible = False
            print_button.disable()
            row_info_label.set_text("Keine Zeile ausgewählt")
            return
        name = row["I4201"]
        expiry = row["C2303"]
        mtag = row["MTAG"]
        qr_url = f"{stored_login['base_url'].rstrip('/')}/qrcode/{mtag}"
        row_info_label.set_text(f"I4201: {name}, C2303: {expiry}")
        current_image = device_label(name, expiry, qr_url)
        label_svg.content = device_label_svg(name, expiry, qr_url)
        placeholder_label.visible = False
        print_button.enable()

    # Zeilen finden
    def _find_row(key: Any) -> Dict[str, Any] | None:
        if isinstance(key, dict): key = key.get("I4201")
        return next((r for r in table_rows if r["I4201"] == key), None)

    # Auswahl-Handler
    def on_select(e: Any) -> None:
        sel = getattr(e,"selection", None) or (getattr(e,"args", None) or [None])[0]
        row = _find_row(sel)
        update_label(row)

    # Klick auf Zeile
    def handle_row_click(e: Any) -> None:
        row_key = (getattr(e,"args",None) or [None])[0]
        row = _find_row(row_key)
        update_label(row)

    # Klick auf Vorschau-Zelle
    def handle_cell_click(e: Any) -> None:
        data = getattr(e,"args",None)
        col = data.get("column", {}).get("name") if isinstance(data,dict) else None
        if col == "preview":
            row = _find_row(data.get("row") if isinstance(data,dict) else None)
            dialog_label_svg.content = device_label_svg(row["I4201"], row["C2303"], f"{stored_login['base_url'].rstrip('/')}/qrcode/{row['MTAG']}")
            label_dialog.open()

    # Drucken
    def do_print() -> None:
        if current_image:
            try:
                print_label(current_image, "")
                push_status("Printed")
            except Exception as e:
                push_status(f"Print error: {e}")

    # Main UI aufbauen
    def show_main_ui() -> None:
        nonlocal status_log, label_svg, print_button, placeholder_label, row_info_label
        nonlocal device_table, empty_table_label, filter_switch, search_input, label_dialog, dialog_label_svg
        with ui.column():
            ui.button("Logout", on_click=logout).classes("absolute-top-right q-mt-sm q-mr-sm").props("icon=logout flat color=negative")
            search_input = ui.input("Gerätename suchen").props("outlined clearable").on("input", lambda e: apply_table_filter())
            ui.button("Daten laden", on_click=fetch_data).props("color=primary").classes("q-mt-md")
            # Dialog
            with ui.dialog() as label_dialog:
                with ui.card():
                    dialog_label_svg = ui.html(device_label_svg("","","")).style("max-width:260px;")
                    ui.button("Schließen", on_click=label_dialog.close)
            # Tabelle & Vorschau
            with ui.row().classes("justify-center q-gutter-xl items-start"):
                # Tabelle
                with ui.column().style("flex:3;min-width:600px;max-width:900px"):
                    filter_switch = ui.switch("Nur aktuelle", value=True, on_change=lambda e: apply_table_filter()).classes("q-mt-md")
                    ui.label("Nur Aktuelle!").bind_visibility_from(filter_switch, 'value')
                    empty_table_label = ui.label("Noch keine Daten geladen").classes("text-grey text-center q-mt-md")
                    device_table = ui.table(**_build_table_kwargs(ui.table, table_rows, on_select)).classes("q-mt-md")
                    device_table.on("row-click", handle_row_click)
                    device_table.on("cell-click", handle_cell_click)
                    device_table.add_slot("body-cell-qrcode", """
                        <q-td :props="props"><img :src="props.value" style="width:80px;height:80px" /></q-td>
                    """)
                    device_table.add_slot("body-cell-preview", """
                        <q-td :props="props"><div v-html="props.value" /></q-td>
                    """)
                    empty_table_label.visible = len(table_rows) == 0
                # Vorschau rechts
                with ui.column().style("min-width:320px;"):
                    with ui.card().classes("pa-4"):
                        ui.label("Label-Vorschau").classes("text-h6")
                        row_info_label = ui.label("Bitte Gerät auswählen").classes("q-mb-md")
                        placeholder_label = ui.label("Keine Vorschau verfügbar").classes("text-grey q-mb-md")
                        placeholder_label.visible = False
                        label_svg = ui.html(device_label_svg("","","")).style("max-width:260px;;;")
                        print_button = ui.button("Drucken", on_click=do_print).props("color=primary")
                        print_button.disable()
        # Footer
        with ui.footer().classes("bg-grey-2 shadow-2"):
            with ui.expansion("Status anzeigen", value=False):
                status_log = ui.log(max_lines=100).style("background-color:white;color:black;width:100%;")

    @ui.page("/")
    
    def login_page() -> None:
        nonlocal base_url, username, password, api_key
        is_dev = os.getenv("APP_ENV") == "development"
        domain = os.getenv("DOMAIN", "demo.net-cal.com" if is_dev else "calserver.example.com")
        default_url = f"https://{domain}" if not domain.startswith("http") else domain
    
        with ui.row().classes('min-h-screen flex items-center justify-center bg-[#f8f4f3]'):
            with ui.column().classes('w-full max-w-md bg-white rounded-2xl shadow-lg px-8 py-8 mx-2'):
                # Logo und Titel
                ui.html("""
                    <div class="flex items-center justify-center mb-6">
                        <h2 class="font-bold text-3xl tracking-tight">calServer <span class="bg-[#f84525] text-white px-2 rounded-md">Labeltool</span></h2>
                    </div>
                """)
                # Überschrift
                ui.label('Log In').classes('block text-2xl font-semibold text-center mb-8 text-gray-800')
                
                # API URL
                ui.label('API URL').classes('block font-medium text-sm text-gray-700 mb-1')
                base_url = ui.input(placeholder='API URL', value=default_url).classes(
                    'w-full rounded-md py-2.5 px-4 border border-gray-200 bg-gray-50 focus:border-[#f84525] text-sm outline-[#f84525] mb-4 transition')
                
                # Benutzername
                ui.label('Benutzername').classes('block font-medium text-sm text-gray-700 mb-1')
                username = ui.input(placeholder='E-Mail', value="api-demo@calhelp.de" if is_dev else "").classes(
                    'w-full rounded-md py-2.5 px-4 border border-gray-200 bg-gray-50 focus:border-[#f84525] text-sm outline-[#f84525] mb-4 transition')
                
                # Passwort
                ui.label('Passwort').classes('block font-medium text-sm text-gray-700 mb-1')
                with ui.row().classes('relative'):
                    password = ui.input(placeholder='Passwort', password=True).classes(
                        'w-full rounded-md py-2.5 px-4 border border-gray-200 bg-gray-50 focus:border-[#f84525] text-sm outline-[#f84525] transition')
                    ui.button('', icon='visibility', on_click=lambda: password.set_password(not password._props.get('password', True))).classes(
                        'absolute right-2 top-2 text-gray-400 bg-transparent shadow-none')
                # API Key
                ui.label('API Key').classes('block font-medium text-sm text-gray-700 mb-1 mt-4')
                api_key = ui.input(placeholder='API Key', password=True, value="53f1871505fa8190659aaae17845bd19" if is_dev else "").classes(
                    'w-full rounded-md py-2.5 px-4 border border-gray-200 bg-gray-50 focus:border-[#f84525] text-sm outline-[#f84525] mb-4 transition')
                
                # Login-Button
                ui.button("LOGIN", on_click=handle_login).classes(
                    'w-full mt-6 px-4 py-2 rounded-md bg-blue-400 hover:bg-blue-500 text-white font-bold shadow-sm transition uppercase tracking-widest'
                )


    @ui.page("/app")
    def main_page() -> None:
        show_main_ui()
        fetch_data()

    ui.run(port=8080, show=False)


if __name__ == "__main__":
    main()
