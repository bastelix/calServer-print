"""Functions for rendering device and calibration label images."""

from PIL import Image, ImageDraw, ImageFont
from .qrcode_utils import generate_qr_code, generate_qr_code_svg

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

    qr_svg = generate_qr_code_svg(mtag)

    svg = f"""
<svg width='400' height='200' xmlns='http://www.w3.org/2000/svg'>
  <rect width='100%' height='100%' fill='white'/>
  <text x='10' y='30' font-size='16'>Gerät: {name}</text>
  <text x='10' y='70' font-size='16'>Ablauf: {expiry}</text>
  <g transform='translate(280,10)'>
    {qr_svg}
  </g>
</svg>
"""
    return svg


def simple_device_label_svg(name: str, expiry: str, mtag: str) -> str:
    """Return a simplified SVG representation of a device label."""

    qr_svg = generate_qr_code_svg(mtag)

    svg = f"""
<svg width='400' height='200' xmlns='http://www.w3.org/2000/svg'>
  <rect width='100%' height='100%' fill='white'/>
  <text x='200' y='40' font-size='20' text-anchor='middle'>{name}</text>
  <text x='200' y='80' font-size='14' text-anchor='middle'>Bis: {expiry}</text>
  <g transform='translate(150,90)'>
    {qr_svg}
  </g>
</svg>
"""
    return svg


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


# Mapping of template names to functions returning SVG strings
LABEL_TEMPLATE_FUNCTIONS = {
    "Standard": device_label_svg,
    "Einfach": simple_device_label_svg,
}


def available_label_templates() -> list[str]:
    """Return the list of available label template names."""
    return list(LABEL_TEMPLATE_FUNCTIONS.keys())


def render_label_template(template: str, name: str, expiry: str, mtag: str) -> str:
    """Render the given template name using the provided parameters."""
    func = LABEL_TEMPLATE_FUNCTIONS.get(template, device_label_svg)
    return func(name, expiry, mtag)
