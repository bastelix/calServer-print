"""Functions for rendering device and calibration label images."""

from PIL import Image, ImageDraw, ImageFont
from .qrcode_utils import generate_qr_code

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
