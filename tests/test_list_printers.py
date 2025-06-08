import importlib
import sys
import types

# Prepare stub PIL modules since print_utils requires them
pil_mod = types.ModuleType('PIL')
pil_image_mod = types.ModuleType('PIL.Image')
class DummyImage:
    pass
pil_image_mod.Image = DummyImage
pil_mod.Image = pil_image_mod
sys.modules['PIL'] = pil_mod
sys.modules['PIL.Image'] = pil_image_mod
sys.modules['win32print'] = types.ModuleType('win32print')
sys.modules['cups'] = types.ModuleType('cups')

print_utils = importlib.import_module('app.print_utils')


def test_list_printers_unknown(monkeypatch):
    monkeypatch.setattr(print_utils.platform, 'system', lambda: 'Other')
    assert print_utils.list_printers() == []


