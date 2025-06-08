"""Utility helpers for creating QR codes as images."""

import qrcode
from PIL import Image


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
