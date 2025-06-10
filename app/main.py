"""NiceGUI based label printing application with login and device table."""

from __future__ import annotations
import base64
import io
import os
import inspect
from typing import Any, Dict, List

import jinja2

from PIL import Image
from nicegui import ui

# Eigene Module importieren
try:
    from .calserver_api import fetch_calibration_data
    from .label_templates import (
        device_label,
        device_label_svg,
        available_label_templates,
        render_label_template,
        svg_header,
    )
    from .qrcode_utils import generate_qr_code, generate_qr_code_svg
    from .print_utils import print_label, list_printers, print_file
except ImportError:
    from calserver_api import fetch_calibration_data
    from label_templates import (
        device_label,
        device_label_svg,
        available_label_templates,
        render_label_template,
        svg_header,
    )
    from qrcode_utils import generate_qr_code, generate_qr_code_svg
    from print_utils import print_label, list_printers, print_file


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
    current_svg: str | None = None

    # Printer selection
    available_printers: List[str] = []
    selected_printer: str | None = None
    printer_select: ui.select | None = None
    pdf_option: ui.checkbox | None = None
    png_option: ui.checkbox | None = None

    # UI-Elemente
    status_log: ui.log | None = None
    label_svg: ui.html | None = None
    template_select: ui.select | None = None
    selected_template: str = "Standard"
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

    # Simple Jinja2 templates for the preview
    jinja_templates = {
        "Standard": """
<svg width='400' height='200' xmlns='http://www.w3.org/2000/svg'>
  <rect width='100%' height='100%' fill='white'/>
  <text x='10' y='40' font-size='16'>I4201: {{ I4201 }}</text>
  <text x='10' y='80' font-size='16'>C2303: {{ C2303 }}</text>
  <g transform='translate(200,40) scale(0.5)'>
    {{ QRCODE }}
  </g>
</svg>
""",
        "Modern": """
<svg width='350' height='200' xmlns='http://www.w3.org/2000/svg'>
  <rect width='100%' height='100%' fill='white'/>
  <text x='175' y='40' font-size='20' text-anchor='middle'>{{ I4201 }}</text>
  <text x='175' y='70' font-size='14' text-anchor='middle'>Ablauf: {{ C2303 }}</text>
  <g transform='translate(125,90) scale(0.5)'>
    {{ QRCODE }}
  </g>
</svg>
""",
    }

    def render_preview(template: str, name: str, expiry: str, qr_data: str) -> str:
        qr_svg = generate_qr_code_svg(qr_data)
        if template in jinja_templates:
            tpl = jinja2.Template(jinja_templates[template])
            body = tpl.render(I4201=name, C2303=expiry, MTAG=qr_data, QRCODE=qr_svg)
            return svg_header() + body
        return render_label_template(template, name, expiry, qr_data)

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
        nonlocal selected_row, current_image, current_svg, status_log, label_svg, print_button
        nonlocal device_table, placeholder_label, empty_table_label, row_info_label, pdf_option, png_option
        push_status("Logged out")
        stored_login.clear()
        selected_row = None
        current_image = None
        current_svg = None
        status_log = None
        label_svg = None
        print_button = None
        device_table = None
        placeholder_label = None
        empty_table_label = None
        row_info_label = None
        pdf_option = None
        png_option = None
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
        nonlocal current_image, current_svg, selected_printer
        if not row:
            label_svg.content = render_preview(selected_template, "", "", "")
            placeholder_label.visible = True
            print_button.disable()
            row_info_label.set_text("Keine Zeile ausgewählt")
            current_image = None
            current_svg = None
            return
        name = row["I4201"]
        expiry = row["C2303"]
        mtag = row["MTAG"]
        qr_url = f"{stored_login['base_url'].rstrip('/')}/qrcode/{mtag}"
        row_info_label.set_text(f"I4201: {name}, C2303: {expiry}")
        current_image = device_label(name, expiry, qr_url)
        current_svg = render_preview(selected_template, name, expiry, qr_url)
        label_svg.content = current_svg
        placeholder_label.visible = False
        if selected_printer:
            print_button.enable()
        else:
            print_button.disable()


    # Auswahl-Handler
    def on_select(e: Any) -> None:
        nonlocal selected_row
        sel = getattr(e, "selection", None)
        if sel and isinstance(sel, list) and len(sel) > 0:
            selected_row = sel[0]
            update_label(selected_row)
        else:
            selected_row = None
            update_label(None)

    # Klick auf Zeile
    def handle_row_click(e: Any) -> None:
        data = getattr(e, "args", None)
        row = None
        if isinstance(data, dict):
            row = data.get("row")
        elif isinstance(data, list) and data:
            row = data[-1]
        update_label(row)

    # Klick auf Vorschau-Zelle
    def handle_cell_click(e: Any) -> None:
        data = getattr(e, "args", None)
        col = data.get("column", {}).get("name") if isinstance(data, dict) else None
        if col == "preview":
            row = data.get("row") if isinstance(data, dict) else None
            if row:
                mtag = row.get("MTAG", "")
                qr_url = f"{stored_login['base_url'].rstrip('/')}/qrcode/{mtag}"
                dialog_label_svg.content = render_preview(
                    selected_template,
                    row["I4201"],
                    row["C2303"],
                    qr_url,
                )
                label_dialog.open()

    def change_template(e: Any) -> None:
        nonlocal selected_template
        if template_select:
            selected_template = template_select.value
        if device_table and device_table.selection:
            update_label(device_table.selection[0])
        else:
            update_label(None)

    def on_printer_change(e: Any) -> None:
        nonlocal selected_printer, selected_row, print_button
        if printer_select:
            selected_printer = printer_select.value
        if selected_row and selected_printer:
            print_button.enable()
        elif print_button:
            print_button.disable()

    # Drucken
    def do_print() -> None:
        nonlocal selected_printer, current_svg, pdf_option, png_option
        if (not current_image and not current_svg) or not selected_printer:
            push_status("Bitte zuerst Datensatz und Drucker wählen")
            return
        try:
            if pdf_option and pdf_option.value:
                import tempfile
                import cairosvg
                from .print_utils import print_file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp_path = tmp.name
                cairosvg.svg2pdf(bytestring=current_svg.encode('utf-8'), write_to=tmp_path)
                try:
                    print_file(tmp_path, selected_printer)
                finally:
                    os.unlink(tmp_path)
            elif png_option and png_option.value:
                import tempfile
                import cairosvg
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    tmp_path = tmp.name
                cairosvg.svg2png(bytestring=current_svg.encode('utf-8'), write_to=tmp_path)
                img = Image.open(tmp_path)
                try:
                    print_label(img, selected_printer)
                finally:
                    os.unlink(tmp_path)
            else:
                print_label(current_image, selected_printer)
            push_status(f"Printed on: {selected_printer}")
        except Exception as e:
            push_status(f"Print error: {e}")

    # Main UI aufbauen
    def show_main_ui() -> None:
        nonlocal status_log, label_svg, print_button, placeholder_label, row_info_label
        nonlocal device_table, empty_table_label, filter_switch, search_input, label_dialog, dialog_label_svg
        nonlocal template_select, printer_select, available_printers, selected_printer
        nonlocal pdf_option, png_option

        try:
            available_printers = list_printers()
        except Exception as e:
            push_status(f"Error listing printers: {e}")
            available_printers = []
        selected_printer = available_printers[0] if available_printers else None
        with ui.column():
            ui.button("Logout", on_click=logout).classes("absolute-top-right q-mt-sm q-mr-sm").props("icon=logout flat color=negative")
            search_input = ui.input("Gerätename suchen").props("outlined clearable").on("input", lambda e: apply_table_filter())
            ui.button("Daten laden", on_click=fetch_data).props("color=primary").classes("q-mt-md")
            # Dialog
            with ui.dialog() as label_dialog:
                with ui.card():
                    dialog_label_svg = ui.html(
                        render_preview(selected_template, "", "", "")
                    ).style("max-width:420px;border:1px solid #ccc;padding:4px;")
                    ui.button("Schließen", on_click=label_dialog.close)
            # Tabelle & Vorschau
            # Tabelle & Vorschau im Grid-Layout nebeneinander
            with ui.row().classes('grid grid-cols-3 w-full gap-4'):
                # Tabelle links (nimmt 2/3 ein)
                with ui.column().classes('col-span-2 border p-1'):
                    filter_switch = ui.switch("Nur aktuelle", value=True, on_change=lambda e: apply_table_filter()).classes("q-mt-md")
                    ui.label("Nur Aktuelle!").bind_visibility_from(filter_switch, 'value')
                    empty_table_label = ui.label("Noch keine Daten geladen").classes("text-grey text-center q-mt-md")
                    device_table = ui.table(**_build_table_kwargs(ui.table, table_rows, on_select)).classes("q-mt-md")
                    device_table.on("row-click", handle_row_click)
                    device_table.on("cell-click", handle_cell_click)
                    device_table.add_slot("body-cell-qrcode", """
                        <q-td :props="props"><img :src="props.value" class="w-20 h-20 object-contain" /></q-td>
                    """)
                    device_table.add_slot("body-cell-preview", """
                        <q-td :props="props"><div v-html="props.value" /></q-td>
                    """)
                    empty_table_label.visible = len(table_rows) == 0
                # Vorschau rechts
                with ui.column().classes('col-span-1 border p-1'):
                    with ui.card().classes("pa-4"):
                        ui.label("Label-Vorschau").classes("text-h6")
                        row_info_label = ui.label("Bitte Gerät auswählen").classes("q-mb-md")
                        all_templates = list(dict.fromkeys(
                            list(jinja_templates.keys()) + available_label_templates()
                        ))
                        template_select = ui.select(
                            options=all_templates,
                            value=selected_template,
                            on_change=change_template,
                        ).classes("q-mb-md")
                        placeholder_label = ui.label("Keine Vorschau verfügbar").classes("text-grey q-mb-md")
                        placeholder_label.visible = False
                        label_svg = ui.html(
                            render_preview(selected_template, "", "", "")
                        ).style("max-width:420px;border:1px solid #ccc;padding:4px;")
                        printer_select = ui.select(
                            options=available_printers,
                            value=selected_printer,
                            on_change=on_printer_change,
                        ).classes("q-mb-md")
                        pdf_option = ui.checkbox("SVG → PDF").classes("q-mb-sm")
                        png_option = ui.checkbox("SVG → PNG").classes("q-mb-sm")
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
    
        with ui.row().classes('min-h-screen w-screen flex items-center justify-center bg-[#f8f4f3]'):
            with ui.column().classes('w-full max-w-lg bg-white rounded-2xl shadow-lg px-8 py-6 mx-2 items-center'):
                # Logo und Titel
                ui.html("""
                    <div class="flex items-center justify-center mb-6">
                        <h2 class="font-bold text-3xl tracking-tight">calServer <span class="bg-[#f84525] text-white px-2 rounded-md">Labeltool</span></h2>
                    </div>
                """)
                # Überschrift
                ui.label('Log In').classes('block text-2xl font-semibold text-center mb-8 text-gray-800')
                
                # API URL
                base_url = ui.input('API URL', value=default_url).classes(
                    'w-full rounded-md py-2.5 px-4 border border-gray-200 bg-gray-50 focus:border-[#f84525] text-sm outline-[#f84525] mb-4 transition')
                
                # Benutzername
                username = ui.input('Benutzername', value="api-demo@calhelp.de" if is_dev else "").classes(
                    'w-full rounded-md py-2.5 px-4 border border-gray-200 bg-gray-50 focus:border-[#f84525] text-sm outline-[#f84525] mb-4 transition')
                
                # Passwort
                password = ui.input('Passwort', password=True).classes(
                    'w-full rounded-md py-2.5 px-4 border border-gray-200 bg-gray-50 focus:border-[#f84525] text-sm outline-[#f84525] mb-4 transition')
                # API Key
                api_key = ui.input('API Key', password=True, value="53f1871505fa8190659aaae17845bd19" if is_dev else "").classes(
                    'w-full rounded-md py-2.5 px-4 mt-4 border border-gray-200 bg-gray-50 focus:border-[#f84525] text-sm outline-[#f84525] mb-4 transition')
                
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
