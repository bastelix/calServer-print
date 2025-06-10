from nicegui import ui
import qrcode
import qrcode.image.svg
import io
import jinja2

# Beispiel-Daten
rows = [
    {"I4201": "Gerät 1", "C2303": "2025-01-01", "MTAG": "MT100"},
    {"I4201": "Gerät 2", "C2303": "2025-06-30", "MTAG": "MT200"},
]

selected_row = rows[0]
selected_template = "Standard"

# SVG-Templates mit Jinja2-Platzhaltern
TEMPLATES = {
    "Standard": """
<svg width='350' height='200' xmlns='http://www.w3.org/2000/svg'>
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

def generate_qr_svg(data: str) -> str:
    factory = qrcode.image.svg.SvgImage
    qr = qrcode.make(data, image_factory=factory)
    buf = io.BytesIO()
    qr.save(buf)
    return buf.getvalue().decode()

def update_preview():
    if not selected_row:
        preview.content = '<i>Keine Zeile ausgewählt</i>'
        return
    qr_svg = generate_qr_svg(selected_row['MTAG'])
    tpl = jinja2.Template(TEMPLATES[selected_template])
    svg = tpl.render(
        I4201=selected_row['I4201'],
        C2303=selected_row['C2303'],
        MTAG=selected_row['MTAG'],
        QRCODE=qr_svg,
    )
    preview.content = svg

# UI Elemente
with ui.row():
    table = ui.table(
        columns=[{'name': 'I4201', 'label': 'I4201', 'field': 'I4201'},
                 {'name': 'C2303', 'label': 'C2303', 'field': 'C2303'},
                 {'name': 'MTAG', 'label': 'MTAG', 'field': 'MTAG'}],
        rows=rows, row_key='I4201', selection='single',
        on_select=lambda e: on_select(e)
    )
    with ui.column():
        template_select = ui.select(list(TEMPLATES.keys()), value=selected_template,
                                    on_change=lambda e: on_template_change(e))
        preview = ui.html('')


def on_select(e):
    global selected_row
    selected_row = e.selection[0] if e.selection else None
    update_preview()


def on_template_change(e):
    global selected_template
    selected_template = e.value
    update_preview()

update_preview()

ui.run()
