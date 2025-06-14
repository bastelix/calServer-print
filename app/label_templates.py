"""Functions for rendering device and calibration label images."""

from PIL import Image, ImageDraw, ImageFont
from .qrcode_utils import (
    generate_qr_code,
    generate_qr_code_data_url,
)


def svg_header() -> str:
    """Return a standard SVG header."""

    # ``svglib`` sometimes tries to load the external DTD referenced by the
    # standard SVG doctype which can fail in restricted environments.  A minimal
    # XML header is sufficient and avoids that network request.
    return "<?xml version='1.0' encoding='UTF-8' standalone='no'?>\n"

FONT = ImageFont.load_default()


def device_label(name: str, expiry: str, mtag: str) -> Image.Image:
    """Create a label image for a device.

    Parameters
    ----------
    name:
        Device name to show on the label.
    expiry:
        Expiry date of the calibration/approval.
    mtag:
        Value to encode in the QR code.

    The label contains the device name, the expiry date and a QR code
    encoding the provided ``mtag`` value.
    """

    img = Image.new("RGB", (400, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"Gerät: {name}", font=FONT, fill="black")
    draw.text((10, 50), f"Ablauf: {expiry}", font=FONT, fill="black")
    qr = generate_qr_code(mtag, size=100)
    img.paste(qr, (280, 10))
    return img


def device_label_svg(name: str, expiry: str, mtag: str) -> str:
    """Return an SVG representation of a device label."""

    qr_png = generate_qr_code_data_url(mtag, size=100)
    qr_elem = f"<image href='{qr_png}' width='100' height='100' />"
    svg_body = f"""
<svg width='400' height='200' xmlns='http://www.w3.org/2000/svg'>
  <rect width='100%' height='100%' fill='white'/>
  <text x='10' y='30' font-size='16'>Gerät: {name}</text>
  <text x='10' y='70' font-size='16'>Ablauf: {expiry}</text>
  <g transform='translate(280,10)'>
    {qr_elem}
  </g>
</svg>
"""
    return svg_header() + svg_body


def simple_device_label_svg(name: str, expiry: str, mtag: str) -> str:
    """Return a simplified SVG representation of a device label."""

    qr_png = generate_qr_code_data_url(mtag, size=100)
    qr_elem = f"<image href='{qr_png}' width='100' height='100' />"
    svg_body = f"""
<svg width='400' height='200' xmlns='http://www.w3.org/2000/svg'>
  <rect width='100%' height='100%' fill='white'/>
  <text x='200' y='40' font-size='20' text-anchor='middle'>{name}</text>
  <text x='200' y='80' font-size='14' text-anchor='middle'>Bis: {expiry}</text>
  <g transform='translate(150,90)'>
    {qr_elem}
  </g>
</svg>
"""
    return svg_header() + svg_body


def calibration_label(date: str, status: str, cert: str, qr_data: str) -> Image.Image:
    """Create a calibration label image.

    The label shows calibration date, status and certificate number. The
    provided ``qr_data`` is encoded into a QR code and placed on the right
    side of the label.
    """

    img = Image.new("RGB", (400, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"Date: {date}", font=FONT, fill="black")
    draw.text((10, 50), f"Status: {status}", font=FONT, fill="black")
    draw.text((10, 90), f"Cert: {cert}", font=FONT, fill="black")
    qr = generate_qr_code(qr_data, size=100)
    img.paste(qr, (280, 10))
    return img


# Mapping of template names to functions returning SVG strings. Additional
# functions following the ``*_label_svg`` naming scheme will be picked up
# automatically.
LABEL_TEMPLATE_FUNCTIONS = {
    "Standard": device_label_svg,
    "Einfach": simple_device_label_svg,
}


def _discover_template_functions() -> dict[str, callable]:
    """Return mapping of template names to template functions."""
    mapping = dict(LABEL_TEMPLATE_FUNCTIONS)
    for name, func in globals().items():
        if callable(func) and name.endswith("_label_svg") and func not in mapping.values():
            label = name.replace("_label_svg", "").replace("_", " ").title()
            mapping[label] = func
    return mapping


def available_label_templates() -> list[str]:
    """Return the list of available label template names."""
    return list(_discover_template_functions().keys())


def render_label_template(template: str, name: str, expiry: str, mtag: str) -> str:
    """Render the given template name using the provided parameters."""
    mapping = _discover_template_functions()
    func = mapping.get(template, mapping.get("Standard"))
    return func(name, expiry, mtag)
