"""Utility helpers for creating QR codes as images."""

import qrcode
import qrcode.image.svg
from PIL import Image
import io
import base64


def generate_qr_code(data: str, size: int = 200) -> Image.Image:
    """Return a QR code image containing ``data``.

    Parameters
    ----------
    data:
        The text that should be encoded in the QR code.
    size:
        Width and height of the resulting image in pixels. Defaults to
        ``200``.

    Returns
    -------
    PIL.Image.Image
        An image object containing the QR code.
    """

    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img.resize((size, size))


def generate_qr_code_svg(data: str) -> str:
    """Return an SVG string for ``data`` encoded as QR code."""

    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
    buffer = io.BytesIO()
    img.save(buffer)
    svg = buffer.getvalue().decode()
    if svg.lstrip().startswith("<?xml"):
        svg = svg.split("?>", 1)[-1]
    return svg


def generate_qr_code_data_url(data: str, size: int = 200) -> str:
    """Return a PNG data URL for ``data`` encoded as QR code."""

    img = generate_qr_code(data, size=size)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"
