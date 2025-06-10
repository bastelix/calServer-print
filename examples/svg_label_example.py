from nicegui import ui
import requests
import qrcode
import io
import qrcode.image.svg

# 1) API abfragen
response = requests.get('https://api.example.com/auswertung')
data = response.json()
value_i4201 = data.get('I4201', '—')
value_c2303 = data.get('C2303', '—')

# 2) QR-Code als SVG generieren
factory = qrcode.image.svg.SvgImage
qr = qrcode.make('MTAG', image_factory=factory)
buf = io.BytesIO()
qr.save(buf)
qr_svg = buf.getvalue().decode()

# 3) SVG-Template zusammenbauen
svg_template = f'''
<svg viewBox="0 0 350 200" width="350" height="200" xmlns="http://www.w3.org/2000/svg">
  <g transform="translate(10,10) scale(0.8)">
    {qr_svg}
  </g>
  <text x="200" y="60" font-family="Arial" font-size="16">I4201: {value_i4201}</text>
  <text x="200" y="100" font-family="Arial" font-size="16">C2303: {value_c2303}</text>
</svg>'''

# 4) in NiceGUI einbetten
ui.html(svg_template)

ui.run()
