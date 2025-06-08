import importlib
import sys
import types

# Stub PIL modules
class DummyImage:
    def __init__(self, size=(0, 0), color="white"):
        self.size = size
        self.color = color
        self.pasted = []
        self.drawn_text = []

    def paste(self, img, position):
        self.pasted.append((img, position))


def new(mode, size, color="white"):
    return DummyImage(size=size, color=color)


class DummyDraw:
    def __init__(self, img):
        self.img = img

    def text(self, position, text, font=None, fill=None):
        self.img.drawn_text.append((position, text))


class DummyFont:
    pass

pil_mod = types.ModuleType("PIL")
image_mod = types.ModuleType("PIL.Image")
image_mod.Image = DummyImage
image_mod.new = new
image_draw_mod = types.ModuleType("PIL.ImageDraw")
image_draw_mod.Draw = DummyDraw
image_font_mod = types.ModuleType("PIL.ImageFont")
image_font_mod.load_default = lambda: DummyFont()

pil_mod.Image = image_mod
pil_mod.ImageDraw = image_draw_mod
pil_mod.ImageFont = image_font_mod

sys.modules["PIL"] = pil_mod
sys.modules["PIL.Image"] = image_mod
sys.modules["PIL.ImageDraw"] = image_draw_mod
sys.modules["PIL.ImageFont"] = image_font_mod

# Stub qrcode_utils
qr_mod = types.ModuleType("app.qrcode_utils")

class DummyQR(DummyImage):
    def __init__(self, data, size):
        super().__init__(size=(size, size))
        self.data = data

def generate_qr_code(data, size=200):
    return DummyQR(data, size)

qr_mod.generate_qr_code = generate_qr_code
sys.modules["app.qrcode_utils"] = qr_mod

label_templates = importlib.import_module("app.label_templates")


def test_device_label_contents():
    img = label_templates.device_label("Device", "123")

    assert img.pasted, "QR code not pasted"
    qr, pos = img.pasted[0]
    assert isinstance(qr, DummyQR)
    assert qr.data == "123"
    assert pos == (280, 10)

    texts = [t for _, t in img.drawn_text]
    assert "Device" in texts[0]
    assert "ID: 123" in texts[1]


def test_calibration_label_contents():
    img = label_templates.calibration_label("2023-01-01", "OK", "C123", "QRDATA")

    qr, pos = img.pasted[0]
    assert qr.data == "QRDATA"
    assert pos == (280, 10)

    texts = [t for _, t in img.drawn_text]
    assert "Date: 2023-01-01" in texts[0]
    assert "Status: OK" in texts[1]
    assert "Cert: C123" in texts[2]
