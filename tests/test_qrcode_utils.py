import importlib
import sys
import types

# Create stub qrcode and PIL modules
class DummyImage:
    def __init__(self, size=(210, 210)):
        self.size = size
    def resize(self, size):
        self.size = size
        return self
    def save(self, buffer, format=None):
        buffer.write(b'PNG')

def _stub_modules():
    qrcode_mod = types.ModuleType('qrcode')
    class DummyQRCode:
        def __init__(self, box_size=10, border=2):
            pass
        def add_data(self, data):
            self.data = data
        def make(self, fit=True):
            pass
        def make_image(self, fill_color='black', back_color='white', image_factory=None):
            if image_factory:
                return image_factory()
            return DummyImage()
    qrcode_mod.QRCode = DummyQRCode

    # Stub qrcode.image.svg.SvgImage
    qrcode_image_mod = types.ModuleType('qrcode.image')
    qrcode_svg_mod = types.ModuleType('qrcode.image.svg')
    class DummySvgImage:
        def save(self, buffer):
            buffer.write(b'<svg></svg>')
    qrcode_svg_mod.SvgImage = DummySvgImage
    qrcode_image_mod.svg = qrcode_svg_mod
    qrcode_mod.image = qrcode_image_mod

    pil_mod = types.ModuleType('PIL')
    pil_image_mod = types.ModuleType('PIL.Image')
    pil_image_mod.Image = DummyImage
    pil_mod.Image = pil_image_mod

    sys.modules['qrcode'] = qrcode_mod
    sys.modules['PIL'] = pil_mod
    sys.modules['PIL.Image'] = pil_image_mod

_stub_modules()

qrcode_utils = importlib.import_module('app.qrcode_utils')


def test_generate_qr_code_size():
    img = qrcode_utils.generate_qr_code('hello', size=100)
    assert img.size == (100, 100)


def test_generate_qr_code_svg_string():
    svg = qrcode_utils.generate_qr_code_svg('hello')
    assert '<svg' in svg and '</svg>' in svg
    assert not svg.strip().startswith('<?xml'), 'XML header not removed'


def test_generate_qr_code_data_url_prefix():
    url = qrcode_utils.generate_qr_code_data_url('hello', size=100)
    assert url.startswith('data:image/png;base64,')
