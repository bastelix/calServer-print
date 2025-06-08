import qrcode
from PIL import Image


def generate_qr_code(data: str, size: int = 200) -> Image.Image:
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img.resize((size, size))
