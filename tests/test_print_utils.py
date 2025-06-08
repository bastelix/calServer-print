import importlib
import sys
import types
import pytest

# Stub PIL module for import
class DummyImage:
    def save(self, path):
        pass

pil_mod = types.ModuleType('PIL')
pil_image_mod = types.ModuleType('PIL.Image')
pil_image_mod.Image = DummyImage
pil_mod.Image = pil_image_mod
sys.modules['PIL'] = pil_mod
sys.modules['PIL.Image'] = pil_image_mod

# Stub cups and win32print modules
sys.modules['cups'] = types.ModuleType('cups')
sys.modules['win32print'] = types.ModuleType('win32print')

print_utils = importlib.import_module('app.print_utils')


def test_print_label_unsupported(monkeypatch):
    monkeypatch.setattr(print_utils.platform, 'system', lambda: 'Other')
    with pytest.raises(RuntimeError):
        print_utils.print_label(DummyImage(), 'dummy')

